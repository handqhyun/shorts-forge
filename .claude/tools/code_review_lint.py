"""N-1: code-reviewer lint wrapper CLI.

Reference: prompt/workflow-coding.md sections 4.3.2 (N-1).

Deterministic subprocess wrapper for ruff + mypy, emitting a single JSON report.
The LLM design review runs only on lint pass (prefilter). When ruff/mypy are
unavailable (this environment), the tool degrades gracefully and reports
tools_available=false rather than failing the build; the orchestrator decides
whether a lint-unavailable environment blocks the gate.

Standard library only: argparse, json, shutil, subprocess, sys, pathlib.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from . import errors, result

TRACE = {
    "module": "tools.code_review_lint",
    "imports": ["argparse", "json", "re", "shutil", "subprocess", "sys", "pathlib", "tools.errors", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-code_review_lint",
}

HELP_JSON = {
    "tool": "code_review_lint",
    "args": {
        "--target": "str path to lint (required)",
    },
}


def _run(cmd: list) -> dict:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {"returncode": proc.returncode, "stdout_tail": proc.stdout.strip().splitlines()[-5:]}


def cmd(ns: argparse.Namespace) -> result.ToolResult:
    if not ns.target:
        raise errors.UsageError("--target is required")
    if not Path(ns.target).exists():
        raise errors.NotFoundError(f"--target not found: {ns.target}")

    ruff_ok = shutil.which("ruff") is not None
    mypy_ok = shutil.which("mypy") is not None

    ruff_report = _run(["ruff", "check", ns.target]) if ruff_ok else {"skipped": "ruff not installed"}
    mypy_report = _run(["mypy", ns.target]) if mypy_ok else {"skipped": "mypy not installed"}

    return result.ok(
        {
            "target": ns.target,
            "tools_available": {"ruff": ruff_ok, "mypy": mypy_ok},
            "ruff": ruff_report,
            "mypy": mypy_report,
            "ratchet_delta": {},
            "lint_clean": (not ruff_ok or ruff_report.get("returncode") == 0)
            and (not mypy_ok or mypy_report.get("returncode") == 0),
        }
    )


def _target_from_stdin() -> str | None:
    import re
    raw = sys.stdin.read()
    m = re.search(r'"file_path"\s*:\s*"([^"]+)"', raw or "")
    return m.group(1) if m else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="code_review_lint", description="ruff+mypy wrapper")
    parser.add_argument("--help-json", action="store_true")
    parser.add_argument("--target", default=None)
    parser.add_argument("--stdin", action="store_true", help="read target from stdin hook JSON")
    parser.set_defaults(fn=cmd)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    if ns.stdin and not ns.target:
        ns.target = _target_from_stdin()
    if not ns.target:
        return result.emit(result.ok({"skipped": "no file_path in event", "lint_clean": True}))
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
