"""N-4: sot-guardian CLI (PreToolUse SOT write guard).

Reference: prompt/workflow-coding.md sections 4.4.1 (N-4), 6.3, 16 IQ-27 RESOLVED.

Decides whether an Edit/Write on a given path is allowed. The SOT four axes are
deny-by-path. The currency exception is recognized ONLY by the single canonical
regex (LLM-assist removed per IQ-27). Deterministic: path match + regex, LLM 0.

Standard library only: argparse, json, re, sys, pathlib.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import errors, result
from .sot_append_rules import CANONICAL_MARKER, verify_append_only

TRACE = {
    "module": "tools.sot_guardian",
    "imports": ["argparse", "json", "sys", "pathlib", "tools.errors", "tools.result", "tools.sot_append_rules"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-sot_guardian",
}

# SOT four axes (deny on Edit/Write unless currency-append validated upstream).
SOT_AXES = (
    "prompt/PRD.md",
    "prompt/workflow.md",
    "prompt/prd-research/final-research.md",
    "prompt/impl/docs/TRACEABILITY.md",
)

HELP_JSON = {
    "tool": "sot_guardian",
    "args": {
        "--pre-tool-use": "flag PreToolUse mode",
        "--file": "str target file path (required)",
        "--tool": "enum('Edit','Write') (required)",
        "--currency-text": "str optional currency line (legacy marker fallback only)",
        "--baseline-file": "str path to current SOT content (diff baseline; default: --file on disk)",
        "--new-content-file": "str path holding the proposed new full content (enables diff verification)",
        "--new-content": "str proposed new full content inline (alternative to --new-content-file)",
    },
}


def _is_sot_axis(file_path: str) -> bool:
    norm = file_path.replace("\\", "/")
    return any(norm.endswith(axis) or norm == axis for axis in SOT_AXES)


def cmd_guard(ns: argparse.Namespace) -> result.ToolResult:
    if not ns.file:
        raise errors.UsageError("--file is required")
    if ns.tool not in ("Edit", "Write"):
        raise errors.ValidationError("--tool must be 'Edit' or 'Write'")

    if not _is_sot_axis(ns.file):
        return result.ok({"decision": "allow", "reason": "not a SOT axis", "file": ns.file})

    # SOT axis: verify the proposed change is append-only via real diff (F-1).
    after = _read_proposed(ns)
    if after is not None:
        before = _read_baseline(ns)
        allowed, reason = verify_append_only(before, after)
        return result.ok(
            {"decision": "allow" if allowed else "deny", "reason": reason, "file": ns.file}
        )

    # No proposed content available: fail-closed. A bare canonical marker is NOT
    # sufficient evidence of an append-only change (the F-1 hole). The append-only
    # skill is the sanctioned write path; this guard denies unverifiable SOT writes.
    return result.ok(
        {
            "decision": "deny",
            "reason": "SOT axis write unverifiable: proposed content not provided (fail-closed)",
            "file": ns.file,
        }
    )


def _read_proposed(ns: argparse.Namespace) -> str | None:
    if getattr(ns, "new_content", None) is not None:
        return ns.new_content
    ncf = getattr(ns, "new_content_file", None)
    if ncf:
        return Path(ncf).read_text(encoding="utf-8")
    return None


def _read_baseline(ns: argparse.Namespace) -> str:
    bf = getattr(ns, "baseline_file", None) or ns.file
    p = Path(bf)
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def _from_stdin() -> tuple:
    """Extract (file_path, tool, proposed_after) from a PreToolUse hook-input JSON
    on stdin. For Write, proposed_after is tool_input.content. For Edit, it is the
    current file with old_string -> new_string applied (so the guard can diff)."""
    raw = sys.stdin.read() or ""
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError):
        return (None, "Write", None)

    tool = payload.get("tool_name") or "Write"
    ti = payload.get("tool_input") or {}
    file_path = ti.get("file_path")
    if not file_path:
        return (None, tool, None)

    after = None
    if tool == "Write":
        after = ti.get("content")
    elif tool == "Edit":
        p = Path(file_path)
        before = p.read_text(encoding="utf-8") if p.is_file() else ""
        old_s, new_s = ti.get("old_string", ""), ti.get("new_string", "")
        if ti.get("replace_all"):
            after = before.replace(old_s, new_s)
        else:
            after = before.replace(old_s, new_s, 1)
    return (file_path, tool, after)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sot_guardian", description="SOT write guard")
    parser.add_argument("--help-json", action="store_true")
    parser.add_argument("--pre-tool-use", action="store_true")
    parser.add_argument("--file", default=None)
    parser.add_argument("--tool", default="Write")
    parser.add_argument("--currency-text", default="")
    parser.add_argument("--baseline-file", default=None)
    parser.add_argument("--new-content-file", default=None)
    parser.add_argument("--new-content", default=None)
    parser.add_argument("--stdin", action="store_true", help="read file_path/tool/content from stdin hook JSON")
    parser.set_defaults(fn=cmd_guard)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    if ns.stdin and not ns.file:
        ns.file, ns.tool, stdin_after = _from_stdin()
        if stdin_after is not None and ns.new_content is None:
            ns.new_content = stdin_after
    if not ns.file:
        # No file in a PreToolUse event that does not target a file: allow.
        return result.emit(result.ok({"decision": "allow", "reason": "no file_path in event"}))
    # Exit code: deny => 2 (PreToolUse block), allow => 0.
    res = ns.fn(ns)
    code = result.emit(res)
    if res.status == "ok" and res.data.get("decision") == "deny":
        return 2
    return code


if __name__ == "__main__":
    raise SystemExit(main())
