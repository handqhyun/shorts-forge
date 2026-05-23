"""P-2: traceability-auditor CLI (TRACE dict enforcement).

Reference: prompt/workflow-coding.md sections 4.3.4 (P-2), 14.1.2 #9.

For each Python module in the target tree, parse the AST and verify the module
defines a module-level TRACE dict carrying the v0.3 five fields plus module name,
AND that the declared TRACE["imports"] set matches the imports the AST actually
contains (§14.1.2 #9: "grep/AST 결과와 대조하여 불일치 시 RED"). Relative imports
resolve to "<package>.<name>" using the file's parent-directory name; __future__ is
ignored. Deterministic: ast.parse, no LLM re-reading of the dict.

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
    "module": "tools.trace_audit",
    "imports": ["argparse", "ast", "json", "sys", "pathlib", "tools.errors", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-trace_audit",
}

REQUIRED_KEYS = (
    "module",
    "imports",
    "imported_by",
    "writes_state_keys",
    "reads_state_keys",
    "adapter_boundary_id",
)

HELP_JSON = {
    "tool": "trace_audit",
    "args": {
        "--target": "str source tree to audit (default: impl/.claude/tools/)",
        "--skip": "str comma-separated basenames to skip (default: __init__.py)",
    },
}


def _trace_dict(tree: ast.AST):
    """Return the module-level `TRACE = {...}` ast.Dict node, or None."""

    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "TRACE":
                    if isinstance(node.value, ast.Dict):
                        return node.value
    return None


def _trace_keys(tree: ast.AST):
    """Return the set of string keys of a module-level `TRACE = {...}` dict, or None."""

    d = _trace_dict(tree)
    if d is None:
        return None
    keys = set()
    for k in d.keys:
        if isinstance(k, ast.Constant) and isinstance(k.value, str):
            keys.add(k.value)
    return keys


def _declared_imports(tree: ast.AST):
    """Return the declared TRACE['imports'] as a set, or None if absent/non-list."""

    d = _trace_dict(tree)
    if d is None:
        return None
    for k, v in zip(d.keys, d.values):
        if isinstance(k, ast.Constant) and k.value == "imports":
            if isinstance(v, (ast.List, ast.Tuple)):
                out = {e.value for e in v.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)}
                out.discard("__future__")
                return out
            return None
    return None


def _actual_imports(tree: ast.AST, pkg_name: str) -> set:
    """Top-level module names actually imported (relative -> '<pkg>.<name>')."""

    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                if node.module:
                    out.add(f"{pkg_name}.{node.module.split('.', 1)[0]}")
                else:
                    for alias in node.names:
                        out.add(f"{pkg_name}.{alias.name}")
            elif node.module:
                out.add(node.module.split(".", 1)[0])
    out.discard("__future__")
    return out


def cmd_audit(ns: argparse.Namespace) -> result.ToolResult:
    target = Path(ns.target)
    if not target.exists():
        raise errors.NotFoundError(f"--target not found: {ns.target}")
    skip = {s.strip() for s in ns.skip.split(",") if s.strip()}

    missing_trace = []
    incomplete_trace = []
    inaccurate_imports = []
    audited = []
    for py in sorted(target.rglob("*.py")):
        if py.name in skip:
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        except SyntaxError as exc:
            missing_trace.append({"path": py.as_posix(), "detail": f"syntax error: {exc}"})
            continue
        keys = _trace_keys(tree)
        if keys is None:
            missing_trace.append({"path": py.as_posix()})
            continue
        missing_keys = [k for k in REQUIRED_KEYS if k not in keys]
        if missing_keys:
            incomplete_trace.append({"path": py.as_posix(), "missing_keys": missing_keys})
        # §14.1.2 #9: declared TRACE['imports'] must match the AST's actual imports.
        declared = _declared_imports(tree)
        if declared is not None:
            actual = _actual_imports(tree, py.parent.name)
            if declared != actual:
                inaccurate_imports.append({
                    "path": py.as_posix(),
                    "declared_only": sorted(declared - actual),
                    "actual_only": sorted(actual - declared),
                })
        audited.append(py.as_posix())

    data = {
        "target": target.as_posix(),
        "audited_count": len(audited),
        "missing_trace": missing_trace,
        "incomplete_trace": incomplete_trace,
        "inaccurate_imports": inaccurate_imports,
        "trace_ok": not missing_trace and not incomplete_trace and not inaccurate_imports,
    }
    return result.ok(data)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trace_audit", description="TRACE dict auditor")
    parser.add_argument("--help-json", action="store_true")
    parser.add_argument("--target", default="impl/.claude/tools/")
    parser.add_argument("--skip", default="__init__.py")
    parser.set_defaults(fn=cmd_audit)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
