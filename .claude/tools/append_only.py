"""P-7: append-only currency validator CLI.

Reference: prompt/workflow-coding.md sections 5.2.2 (P-7), 11.2, 16 IQ-27 RESOLVED.

Validates that a proposed currency line conforms to the single canonical marker
format. The LLM-assist branch ("naturalness of currency text") is REMOVED per
N-4/IQ-27: a currency marker is recognized ONLY by the canonical regex. This tool
validates; it does NOT apply the edit (the actual append is owner-confirmed and
performed through the SOT write path; this tool is the deterministic gate).

Standard library only: argparse, json, re, sys, pathlib.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from . import errors, result
from .sot_append_rules import CANONICAL_MARKER

TRACE = {
    "module": "tools.append_only",
    "imports": ["argparse", "json", "re", "sys", "pathlib", "tools.errors", "tools.result", "tools.sot_append_rules"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-append_only",
}

# CANONICAL_MARKER is imported from tools.sot_append_rules (single source of truth).
VERSION_RE = re.compile(r"^v\d+\.\d+(?:\.\d+)?$")

HELP_JSON = {
    "tool": "append_only",
    "args": {
        "--target": "str path to SOT/derived file (existence checked)",
        "--anchor": "str section/cell anchor id",
        "--version": "str version token (e.g. 'v0.9.6')",
        "--currency-text": "str the full proposed currency line",
    },
}


def cmd_validate(ns: argparse.Namespace) -> result.ToolResult:
    if not VERSION_RE.match(ns.version):
        raise errors.ValidationError(
            f"--version must match vN.N or vN.N.N, got {ns.version!r}"
        )
    target = Path(ns.target)
    if not target.is_file():
        raise errors.NotFoundError(f"--target file not found: {ns.target}")

    text = ns.currency_text
    marker_ok = bool(CANONICAL_MARKER.search(text))
    version_in_text = ns.version in text

    failures = []
    if not marker_ok:
        failures.append("canonical currency marker not found in --currency-text")
    if not version_in_text:
        failures.append(f"--version {ns.version!r} token not present in --currency-text")

    if failures:
        raise errors.ValidationError("; ".join(failures))

    return result.ok(
        {
            "target": str(target),
            "anchor": ns.anchor,
            "version": ns.version,
            "marker_ok": True,
            "append_mode": "end-of-cell-or-new-line",
            "note": "validation only; actual append is owner-confirmed (no edit applied)",
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="append_only", description="append-only currency validator")
    parser.add_argument("--help-json", action="store_true", help="print machine-readable schema")
    parser.add_argument("--target")
    parser.add_argument("--anchor", default="")
    parser.add_argument("--version")
    parser.add_argument("--currency-text", default="")
    parser.set_defaults(fn=cmd_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    if not ns.target or not ns.version:
        parser.print_help(sys.stderr)
        return 2
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
