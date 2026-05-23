"""hook backing: PostToolUse impl/src/**/*.py -> impact-analyzer enqueue (§6.9).

Reference: prompt/workflow-coding.md sections 6.9, 6.7 (P-10 mapping). F-5 resolution:
deterministic body the §6.9 hook wrapper calls (no inline heredoc).

Reads PostToolUse hook input JSON from stdin, extracts file_path, matches
impl/src/**/*.py, resolves the running build_run and in_progress task, checks the
impact-JSON cache for idempotency on changed_files_sha, and emits an enqueue signal.

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
    "module": "tools.impact_trigger",
    "imports": ["argparse", "hashlib", "json", "os", "re", "sqlite3", "sys", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": ["build_runs", "build_tasks"],
    "adapter_boundary_id": "ADAPT-TOOL-impact_trigger",
}

DEFAULT_DB = "impl/.claude/state/build_state.sqlite"

HELP_JSON = {
    "tool": "impact_trigger",
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
    if not (fp.startswith("impl/src/") and fp.endswith(".py")):
        return {"action": "noop", "reason": "not impl/src/**/*.py"}
    if not os.path.isfile(db):
        return {"action": "defer", "reason": "build_state.sqlite not initialized"}
    if not os.path.isfile(fp):
        return {"action": "defer", "reason": "file not on disk yet"}
    try:
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        run = conn.execute(
            "SELECT build_run_id FROM build_runs WHERE status='running' "
            "ORDER BY started_at DESC LIMIT 1;"
        ).fetchone()
        if run is None:
            conn.close()
            return {"action": "defer", "reason": "no running build_run"}
        brid = run["build_run_id"]
        task = conn.execute(
            "SELECT task_id FROM build_tasks WHERE build_run_id=? AND status='in_progress' "
            "ORDER BY created_at DESC LIMIT 1;",
            (brid,),
        ).fetchone()
        conn.close()
    except sqlite3.Error as exc:
        return {"action": "defer", "reason": f"sqlite error: {exc}"}
    if task is None:
        return {"action": "defer", "reason": "no in_progress task"}
    sha = hashlib.sha256(open(fp, "rb").read()).hexdigest()
    impact_path = os.path.join("impl/.claude/runs", brid, "impact", f"{task['task_id']}.json")
    if os.path.isfile(impact_path):
        try:
            cached = json.load(open(impact_path, encoding="utf-8"))
            if cached.get("changed_files_sha") == sha:
                return {"action": "skip", "reason": "idempotent: cached impact"}
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "action": "enqueue",
        "subagent": "impact-analyzer",
        "task_id": task["task_id"],
        "build_run_id": brid,
        "changed_files_sha": sha,
        "changed_file": fp,
    }


def cmd(ns: argparse.Namespace) -> result.ToolResult:
    raw = ns.input if ns.input is not None else sys.stdin.read()
    return result.ok(_decide(raw or "", ns.db))


def build_parser():
    p = argparse.ArgumentParser(prog="impact_trigger", description="src py impact enqueue")
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
