"""P-9: traceability-update CLI (TRACE validate + append-only preview).

Reference: prompt/workflow-coding.md sections 5.3.3 (P-9), 11.2.

Validates the TRACE dict of a changed module and prepares an append-only currency
line for impl/docs/TRACEABILITY.md. Because TRACEABILITY.md is a SOT axis, this tool
NEVER writes it directly: it validates and emits the would-append preview; the
actual append must pass the sot_guardian (N-4) + append_only (P-7) gate.
Deterministic: ast + regex, LLM 0.

Standard library only: argparse, ast, json, re, sys, pathlib.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

from . import errors, result

TRACE = {
    "module": "tools.traceability_update",
    "imports": ["argparse", "ast", "json", "sys", "pathlib", "tools.errors", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-traceability_update",
}

REQUIRED_KEYS = (
    "module", "imports", "imported_by",
    "writes_state_keys", "reads_state_keys", "adapter_boundary_id",
)
SOT_TRACEABILITY = "prompt/impl/docs/TRACEABILITY.md"

HELP_JSON = {
    "tool": "traceability_update",
    "args": {
        "--module": "str path to changed .py module (required)",
        "--currency": "str currency line to be appended (preview only)",
    },
}


def _trace_keys(tree: ast.AST):
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "TRACE" and isinstance(node.value, ast.Dict):
                    return {
                        k.value for k in node.value.keys
                        if isinstance(k, ast.Constant) and isinstance(k.value, str)
                    }
    return None


def cmd(ns: argparse.Namespace) -> result.ToolResult:
    mod = Path(ns.module)
    if not mod.is_file():
        raise errors.NotFoundError(f"--module not found: {ns.module}")
    try:
        tree = ast.parse(mod.read_text(encoding="utf-8"), filename=str(mod))
    except SyntaxError as exc:
        raise errors.ValidationError(f"module has syntax error: {exc}") from exc
    keys = _trace_keys(tree)
    if keys is None:
        raise errors.ValidationError(f"module has no TRACE dict: {ns.module}")
    missing = [k for k in REQUIRED_KEYS if k not in keys]
    if missing:
        raise errors.ValidationError(f"TRACE dict missing keys: {missing}")

    return result.ok(
        {
            "module": mod.as_posix(),
            "trace_ok": True,
            "target": SOT_TRACEABILITY,
            "would_append": ns.currency,
            "note": "preview only; actual append must pass sot_guardian (N-4) + append_only (P-7) gate (SOT axis)",
            "wrote": False,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="traceability_update", description="TRACE validate + append preview")
    parser.add_argument("--help-json", action="store_true")
    parser.add_argument("--module", default=None)
    parser.add_argument("--currency", default="")
    parser.set_defaults(fn=cmd)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    if not ns.module:
        parser.print_help(sys.stderr)
        return 2
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
