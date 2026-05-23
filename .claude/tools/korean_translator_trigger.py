"""hook backing: PostToolUse *.en.md -> korean-translator enqueue (§6.8).

Reference: prompt/workflow-coding.md sections 6.8, 6.7 (P-10 mapping). F-5 resolution:
this is the deterministic body the §6.8 hook wrapper calls (no inline heredoc).

Reads the PostToolUse hook input JSON from stdin, extracts file_path, matches
*.en.md in the allowed zones, checks pair_outputs idempotency on en_sha, and emits
an enqueue signal for the orchestrator. Deterministic.

Standard library only: argparse, hashlib, json, os, re, sqlite3, sys.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys

from . import result

TRACE = {
    "module": "tools.korean_translator_trigger",
    "imports": ["argparse", "hashlib", "json", "os", "re", "sqlite3", "sys", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": ["pair_outputs"],
    "adapter_boundary_id": "ADAPT-TOOL-korean_translator_trigger",
}

ALLOWED_ZONES = ("impl/.claude/runs/", "impl/docs/", "prompt/decisions/")
DEFAULT_DB = "impl/.claude/state/build_state.sqlite"

HELP_JSON = {
    "tool": "korean_translator_trigger",
    "args": {
        "--db": f"str build_state db (default: {DEFAULT_DB})",
        "--input": "str hook input JSON (default: read stdin)",
    },
}


def _decide(raw: str, db: str) -> dict:
    m = re.search(r'"file_path"\s*:\s*"([^"]+)"', raw)
    if not m:
        return {"action": "noop", "reason": "no file_path"}
    fp = m.group(1)
    if not fp.endswith(".en.md"):
        return {"action": "noop", "reason": "not .en.md"}
    if not any(fp.startswith(z) or ("/" + z) in fp for z in ALLOWED_ZONES):
        return {"action": "noop", "reason": "outside allowed zones"}
    if not os.path.isfile(db):
        return {"action": "defer", "reason": "build_state.sqlite not initialized"}
    if not os.path.isfile(fp):
        return {"action": "defer", "reason": "file not on disk yet"}
    en_sha = hashlib.sha256(open(fp, "rb").read()).hexdigest()
    try:
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT ko_status FROM pair_outputs WHERE en_path=? AND en_sha=? LIMIT 1;",
            (fp, en_sha),
        ).fetchone()
        conn.close()
    except sqlite3.Error as exc:
        return {"action": "defer", "reason": f"sqlite error: {exc}"}
    if row is not None and row["ko_status"] == "ok":
        return {"action": "skip", "reason": "idempotent: ko_status=ok", "en_path": fp}
    return {"action": "enqueue", "subagent": "korean-translator", "en_path": fp, "en_sha": en_sha}


def cmd(ns: argparse.Namespace) -> result.ToolResult:
    raw = ns.input if ns.input is not None else sys.stdin.read()
    return result.ok(_decide(raw or "", ns.db))


def build_parser():
    p = argparse.ArgumentParser(prog="korean_translator_trigger", description="en.md translation enqueue")
    p.add_argument("--help-json", action="store_true")
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--input", default=None)
    p.set_defaults(fn=cmd)
    return p


def main(argv=None) -> int:
    ns = build_parser().parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
