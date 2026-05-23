"""hook backing: PreToolUse Bash network-egress guard (§6.4).

Reference: prompt/workflow-coding.md sections 6.4, 6.7 (P-10 mapping).

Inspects a Bash command string for network egress patterns
(curl/wget/pip install/npm/http(s)://) and denies unless the command matches the
carveout whitelist. Deterministic substring/regex match. INVARIANT #1 PreToolUse
enforcement.

Standard library only: argparse, json, re, sys, pathlib.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from . import errors, result

TRACE = {
    "module": "tools.netguard_pretool",
    "imports": ["argparse", "json", "re", "sys", "pathlib", "tools.errors", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-netguard_pretool",
}

EGRESS_RE = re.compile(r"\b(curl|wget|pip\s+install|npm\s+install|npm\s+i)\b|https?://", re.IGNORECASE)
DEFAULT_CARVEOUTS = "impl/.claude/state/network-carveouts.json"

HELP_JSON = {
    "tool": "netguard_pretool",
    "args": {
        "--command": "str the Bash command to inspect (required)",
        "--carveouts": f"str carveout whitelist JSON (default: {DEFAULT_CARVEOUTS})",
    },
}


def _carveouts(path: str) -> list:
    p = Path(path)
    if not p.is_file():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data.get("allow_substrings", [])


def cmd(ns: argparse.Namespace) -> result.ToolResult:
    if ns.command is None:
        raise errors.UsageError("--command is required")
    match = EGRESS_RE.search(ns.command)
    if not match:
        return result.ok({"decision": "allow", "reason": "no egress pattern", "command": ns.command})
    for allowed in _carveouts(ns.carveouts):
        if allowed in ns.command:
            return result.ok({"decision": "allow", "reason": f"carveout: {allowed}", "command": ns.command})
    return result.ok(
        {
            "decision": "deny",
            "reason": f"network egress blocked: {match.group(0)!r}",
            "command": ns.command,
        }
    )


def _command_from_stdin() -> str | None:
    raw = sys.stdin.read()
    m = re.search(r'"command"\s*:\s*"((?:[^"\\]|\\.)*)"', raw or "")
    if not m:
        return None
    return m.group(1).encode().decode("unicode_escape")


def build_parser():
    p = argparse.ArgumentParser(prog="netguard_pretool", description="Bash egress guard")
    p.add_argument("--help-json", action="store_true")
    p.add_argument("--command", default=None)
    p.add_argument("--carveouts", default=DEFAULT_CARVEOUTS)
    p.add_argument("--stdin", action="store_true", help="read command from stdin hook JSON")
    p.set_defaults(fn=cmd)
    return p


def main(argv=None) -> int:
    ns = build_parser().parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    if ns.stdin and ns.command is None:
        ns.command = _command_from_stdin()
    if ns.command is None:
        # No command in event: allow.
        return result.emit(result.ok({"decision": "allow", "reason": "no command in event"}))
    res = ns.fn(ns)
    code = result.emit(res)
    if res.status == "ok" and res.data.get("decision") == "deny":
        return 2
    return code


if __name__ == "__main__":
    raise SystemExit(main())
