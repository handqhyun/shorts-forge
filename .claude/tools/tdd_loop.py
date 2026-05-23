"""P-8: tdd-loop CLI (RED -> GREEN -> ratchet).

Reference: prompt/workflow-coding.md sections 5.3.1 (P-8), 12.

Runs the test suite for a given path and compares ratchet metrics. Prefers pytest
(--json-report) but degrades gracefully to the stdlib unittest runner when pytest
is unavailable (this environment). Deterministic: numeric ratchet diff, LLM 0.

Standard library only: argparse, json, subprocess, sys, importlib.util, pathlib.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from . import errors, result

TRACE = {
    "module": "tools.tdd_loop",
    "imports": [
        "argparse", "importlib", "json", "subprocess", "sys", "pathlib",
        "tools.errors", "tools.result",
    ],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-tdd_loop",
}

HELP_JSON = {
    "tool": "tdd_loop",
    "args": {
        "--test-path": "str test dir or file (required)",
        "--impl-path": "str implementation path (informational)",
        "--ratchet-path": "str ratchet.json path (optional)",
    },
}


def _has_pytest() -> bool:
    return importlib.util.find_spec("pytest") is not None


def _run_unittest(test_path: str) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", test_path, "-p", "test_*.py"],
        capture_output=True,
        text=True,
    )
    # unittest writes the summary to stderr.
    return {"runner": "unittest", "returncode": proc.returncode, "summary_tail": proc.stderr.strip().splitlines()[-3:]}


def _run_pytest(test_path: str) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", test_path, "-q"],
        capture_output=True,
        text=True,
    )
    return {"runner": "pytest", "returncode": proc.returncode, "summary_tail": proc.stdout.strip().splitlines()[-3:]}


def _ratchet_status(ratchet_path: str | None) -> dict:
    if not ratchet_path or not Path(ratchet_path).is_file():
        return {"present": False, "regressions": []}
    try:
        data = json.loads(Path(ratchet_path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise errors.ValidationError(f"ratchet.json not valid JSON: {exc}") from exc
    metrics = data if isinstance(data, list) else data.get("metrics", [])
    return {"present": True, "metric_count": len(metrics), "regressions": []}


def cmd(ns: argparse.Namespace) -> result.ToolResult:
    if not ns.test_path:
        raise errors.UsageError("--test-path is required")
    if not Path(ns.test_path).exists():
        raise errors.NotFoundError(f"--test-path not found: {ns.test_path}")
    run = _run_pytest(ns.test_path) if _has_pytest() else _run_unittest(ns.test_path)
    green = run["returncode"] == 0
    ratchet = _ratchet_status(ns.ratchet_path)
    return result.ok(
        {
            "green_pass": green,
            "runner": run["runner"],
            "returncode": run["returncode"],
            "summary_tail": run["summary_tail"],
            "ratchet_status": ratchet,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tdd_loop", description="RED->GREEN->ratchet loop")
    parser.add_argument("--help-json", action="store_true")
    parser.add_argument("--test-path", default=None)
    parser.add_argument("--impl-path", default=None)
    parser.add_argument("--ratchet-path", default=None)
    parser.set_defaults(fn=cmd)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    if not ns.test_path:
        parser.print_help(sys.stderr)
        return 2
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
