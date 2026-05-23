"""P-3: impact-analyzer CLI (deterministic dependency/ripple graph).

Reference: prompt/workflow-coding.md sections 4.3.5 (P-3), 14.1.2 #9, 14.1.3, 16 IQ-18.

For a changed-file set, build a deterministic import/dependency graph and emit the
impact JSON to impl/.claude/runs/<run-id>/impact/<task-id>.json. Idempotent on
(task_id, changed_files_sha). Deterministic: ast over the source tree, LLM 0.

Fields computed deterministically here:
  - downstream_modules: reverse-import scan over src_root.
  - shotgun_warnings: (a) §14.1.2 #9 TRACE.imports vs AST drift (undeclared absolute
    imports) and (b) build_state write-key ripple (TRACE.writes_state_keys of a changed
    module vs TRACE.reads_state_keys of every src_root module).
  - adapter_boundary_violations: §14.1.3 adapter_boundary_id referential integrity
    (a changed module declaring an id absent from the §14.1.3.2 table and not matching
    the ADAPT-TOOL-* tool convention).

Fields explicitly deferred (input artifact absent). Each is still emitted as an empty
list (schema stability) AND simultaneously named, with its reason, in the deferred_checks
array — so the empty list is never read as a silent clean pass (an unflagged empty list
would be the false-GREEN this tool's completion exists to remove):
  - ratchet_remeasure_required: needs impl/tests/ratchet.json (Phase-1 artifact).
  - red_regen_required: needs the D-3 RED test files (Phase-1 artifact).
  - adapter DTO/exception signature validation: needs the product DTO classes named in
    §14.1.3.2 (Phase-1 src/ artifacts); only adapter_boundary_id integrity is computed.

Standard library only: argparse, ast, json, sys, pathlib.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

from . import errors, result

TRACE = {
    "module": "tools.impact_analyze",
    "imports": ["argparse", "ast", "json", "sys", "pathlib", "tools.errors", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": ["build_tasks"],
    "adapter_boundary_id": "ADAPT-TOOL-impact_analyze",
}

HELP_JSON = {
    "tool": "impact_analyze",
    "args": {
        "--task-id": "str (required)",
        "--build-run-id": "str (required)",
        "--changed-files-sha": "str cache key (required)",
        "--changed-files": "str comma-separated changed .py paths (required)",
        "--src-root": "str source tree to scan for reverse deps (default: impl/src/)",
        "--out-root": "str run output root (default: impl/.claude/runs/)",
    },
}

# §14.1.3.2 adapter boundary table (11 stage/spine/meta boundaries). The
# ADAPT-TOOL-<name> convention (§14.1.2 #10 (g)) covers tool modules and is matched
# by prefix rather than enumerated here.
KNOWN_ADAPTER_BOUNDARIES = frozenset({
    "ADAPT-S1-IN", "ADAPT-S1-TONEMAP", "ADAPT-S2-INGEST", "ADAPT-S3-SELECT",
    "ADAPT-S4-ASSEMBLE", "ADAPT-S5-AUDIO", "ADAPT-S6-RENDER", "ADAPT-S7-VALIDATE",
    "ADAPT-SPINE-RR", "ADAPT-SPINE-DB", "ADAPT-META-LLM",
})

# __future__ is a compiler directive, not a dependency, and is conventionally absent
# from TRACE.imports; excluding it prevents a false "undeclared import" warning.
_NON_DEP_IMPORTS = frozenset({"__future__"})

# Checks whose deterministic input does not exist yet. Surfaced explicitly so an empty
# result field is never mistaken for a clean pass (the false-GREEN this tool's
# completion exists to remove).
DEFERRED_CHECKS = (
    {"check": "ratchet_remeasure_required",
     "reason": "input absent: impl/tests/ratchet.json not present (Phase-1 artifact)"},
    {"check": "red_regen_required",
     "reason": "input absent: D-3 RED test files are Phase-1 artifacts"},
    {"check": "adapter_dto_signature",
     "reason": "input absent: product DTO classes (§14.1.3.2) are Phase-1 src/ artifacts; "
               "only adapter_boundary_id referential integrity is computed"},
)


def _module_name(path: Path, src_root: Path) -> str:
    try:
        rel = path.resolve().relative_to(src_root.resolve())
    except ValueError:
        return path.stem
    return ".".join(rel.with_suffix("").parts)


def _imports_of(path: Path) -> set:
    if not path.is_file():
        return set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return set()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.name.split(".", 1)[0])
    return names


def _abs_imports_of(path: Path) -> set:
    """Top-level absolute import names. Relative (`from .`) imports are skipped because
    the TRACE convention records them dotted (e.g. `tools.errors`), so they cannot be
    reconciled by top-level name without false positives."""
    if not path.is_file():
        return set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return set()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if node.module:
                names.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.name.split(".", 1)[0])
    return names - _NON_DEP_IMPORTS


def _trace_of(path: Path) -> dict:
    """Extract the module-level `TRACE` dict literal via AST (no import execution)."""
    if not path.is_file():
        return {}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "TRACE":
                    try:
                        value = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return {}
                    return value if isinstance(value, dict) else {}
    return {}


def _resolve_changed(entry: str, src_root: Path) -> Path | None:
    """Resolve a changed-file entry to an existing path: try it as given, then by
    basename under src_root (handles run-relative paths and test fixtures alike)."""
    p = Path(entry)
    if p.is_file():
        return p
    candidate = src_root / p.name
    if candidate.is_file():
        return candidate
    return None


def cmd(ns: argparse.Namespace) -> result.ToolResult:
    changed = [c.strip() for c in ns.changed_files.split(",") if c.strip()]
    src_root = Path(ns.src_root)

    changed_stems = {Path(c).stem for c in changed}
    downstream = []
    if src_root.exists():
        for py in sorted(src_root.rglob("*.py")):
            imps = _imports_of(py)
            if imps & changed_stems:
                downstream.append(py.as_posix())

    # Resolve each changed entry once and read its TRACE dict.
    resolved = {c: _resolve_changed(c, src_root) for c in changed}
    traces = {c: (_trace_of(p) if p is not None else {}) for c, p in resolved.items()}

    shotgun_warnings = []
    adapter_violations = []

    for c in changed:
        trace = traces[c]
        if not trace:
            continue
        path = resolved[c]

        # (a) §14.1.2 #9 TRACE.imports vs AST: undeclared absolute imports.
        declared = {str(m).split(".", 1)[0] for m in trace.get("imports", [])}
        undeclared = sorted(_abs_imports_of(path) - declared)
        if undeclared:
            shotgun_warnings.append({
                "reason": f"undeclared imports in {c} (present in AST, absent from TRACE.imports)",
                "affected": undeclared,
            })

        # (c) §14.1.3 adapter_boundary_id referential integrity.
        aid = trace.get("adapter_boundary_id")
        if aid and aid not in KNOWN_ADAPTER_BOUNDARIES and not str(aid).startswith("ADAPT-TOOL-"):
            adapter_violations.append({
                "boundary_id": aid,
                "violation": "unknown adapter_boundary_id (not in §14.1.3.2 table nor ADAPT-TOOL-* convention)",
                "module": c,
            })

    # (b) build_state write-key ripple: readers of any key a changed module writes.
    write_keys = {k for c in changed for k in traces[c].get("writes_state_keys", [])}
    if write_keys and src_root.exists():
        for py in sorted(src_root.rglob("*.py")):
            reads = set(_trace_of(py).get("reads_state_keys", []))
            hit = sorted(reads & write_keys)
            if hit:
                shotgun_warnings.append({
                    "reason": f"build_state read of write-key(s) {hit} in {py.as_posix()}",
                    "affected": [py.as_posix()],
                })

    impact = {
        "task_id": ns.task_id,
        "build_run_id": ns.build_run_id,
        "changed_files_sha": ns.changed_files_sha,
        "changed_files": changed,
        "downstream_modules": downstream,
        "shotgun_warnings": shotgun_warnings,
        "ratchet_remeasure_required": [],
        "red_regen_required": [],
        "adapter_boundary_violations": adapter_violations,
        "deferred_checks": [dict(d) for d in DEFERRED_CHECKS],
    }

    out_dir = Path(ns.out_root) / ns.build_run_id / "impact"
    out_path = out_dir / f"{ns.task_id}.json"

    # Idempotency: identical changed_files_sha => cached no-op.
    if out_path.is_file():
        try:
            cached = json.loads(out_path.read_text(encoding="utf-8"))
            if cached.get("changed_files_sha") == ns.changed_files_sha:
                return result.ok({"cached": True, "out_path": out_path.as_posix()})
        except json.JSONDecodeError:
            pass

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(impact, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return result.ok({"cached": False, "out_path": out_path.as_posix(), "downstream_count": len(downstream)})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="impact_analyze", description="dependency/ripple analyzer")
    parser.add_argument("--help-json", action="store_true")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--build-run-id", default=None)
    parser.add_argument("--changed-files-sha", default=None)
    parser.add_argument("--changed-files", default="")
    parser.add_argument("--src-root", default="impl/src/")
    parser.add_argument("--out-root", default="impl/.claude/runs/")
    parser.set_defaults(fn=cmd)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    if not ns.task_id or not ns.build_run_id or not ns.changed_files_sha:
        parser.print_help(sys.stderr)
        return 2
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
