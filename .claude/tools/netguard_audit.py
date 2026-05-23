"""P-4: network-ledger-audit CLI (INVARIANT #1 enforcement).

Reference: prompt/workflow-coding.md section 5.3.2 (P-4).

Scans a Python source tree (AST) for forbidden network imports
(requests/urllib/httpx/aiohttp) outside the netguard carveout, and scans the
runtime network ledger JSON for non-carveout egress events. INVARIANT #1 is
non-negotiable; a single missed import is an RLM breach, so this is deterministic
AST, never an LLM read.

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
    "module": "tools.netguard_audit",
    "imports": ["argparse", "ast", "json", "sys", "pathlib", "tools.errors", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-netguard_audit",
}

FORBIDDEN = ("requests", "urllib", "httpx", "aiohttp", "socket", "http")
# Carveout: only this module is allowed to reference network primitives.
CARVEOUT_SUFFIXES = ("invariants/netguard.py",)

HELP_JSON = {
    "tool": "netguard_audit",
    "args": {
        "--src": "str source tree to scan (default: impl/src/)",
        "--ledger": "str runtime network ledger JSON path (optional)",
    },
}


def _is_carveout(path: Path) -> bool:
    s = path.as_posix()
    return any(s.endswith(suf) for suf in CARVEOUT_SUFFIXES)


def _top_module(name: str) -> str:
    return name.split(".", 1)[0]


def scan_imports(src: Path) -> list:
    findings = []
    for py in sorted(src.rglob("*.py")):
        if _is_carveout(py):
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        except SyntaxError as exc:
            findings.append({"path": py.as_posix(), "import": "<syntax-error>", "detail": str(exc)})
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _top_module(alias.name) in FORBIDDEN:
                        findings.append({"path": py.as_posix(), "import": alias.name, "lineno": node.lineno})
            elif isinstance(node, ast.ImportFrom):
                if node.module and _top_module(node.module) in FORBIDDEN:
                    findings.append({"path": py.as_posix(), "import": node.module, "lineno": node.lineno})
    return findings


def scan_ledger(ledger_path: Path) -> list:
    if not ledger_path.is_file():
        return []
    try:
        data = json.loads(ledger_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise errors.ValidationError(f"ledger not valid JSON: {exc}") from exc
    violations = []
    for event in data.get("egress_events", []):
        if not event.get("carveout", False):
            violations.append(event)
    return violations


def cmd_audit(ns: argparse.Namespace) -> result.ToolResult:
    src = Path(ns.src)
    if not src.exists():
        raise errors.NotFoundError(f"--src not found: {ns.src}")
    forbidden_imports = scan_imports(src)
    ledger_violations = scan_ledger(Path(ns.ledger)) if ns.ledger else []
    data = {
        "src": src.as_posix(),
        "forbidden_imports": forbidden_imports,
        "ledger_violations": ledger_violations,
        "invariant1_ok": not forbidden_imports and not ledger_violations,
    }
    return result.ok(data)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="netguard_audit", description="INVARIANT #1 network audit")
    parser.add_argument("--help-json", action="store_true")
    parser.add_argument("--src", default="impl/src/")
    parser.add_argument("--ledger", default=None)
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
