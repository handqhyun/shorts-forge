"""N-5: swarm-coordinator-fallback CLI (deterministic timeout detection).

Reference: prompt/workflow-coding.md sections 4.4.3 (N-5), 10.

Deterministic part: read build_tasks.last_heartbeat_at, compare against a 10-minute
threshold relative to --now, count stalled tasks, and emit the routing action. The
LLM routing judgment runs only after this deterministic timeout confirmation. Clock
input is injected via --now for determinism (no implicit wall-clock branching).

Standard library only: argparse, json, sqlite3, sys, datetime.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

from . import errors, result

TRACE = {
    "module": "tools.swarm_fallback",
    "imports": ["argparse", "json", "sqlite3", "sys", "datetime", "pathlib", "tools.errors", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": ["build_tasks"],
    "adapter_boundary_id": "ADAPT-TOOL-swarm_fallback",
}

DEFAULT_DB = "impl/.claude/state/build_state.sqlite"
TIMEOUT_MINUTES = 10
STALL_TASK_THRESHOLD = 3  # 3+ stalled tasks => solo mode

HELP_JSON = {
    "tool": "swarm_fallback",
    "args": {
        "--db": "str build_state db path",
        "--build-run-id": "str (required)",
        "--now": "str ISO-8601 current time (required for determinism)",
    },
}


def _parse_iso(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def cmd(ns: argparse.Namespace) -> result.ToolResult:
    if not ns.build_run_id:
        raise errors.UsageError("--build-run-id is required")
    if not ns.now:
        raise errors.UsageError("--now is required (determinism)")
    now = _parse_iso(ns.now)
    threshold = now - timedelta(minutes=TIMEOUT_MINUTES)

    from pathlib import Path

    if not Path(ns.db).is_file():
        raise errors.StateError(f"build_state db not initialized: {ns.db}")

    conn = sqlite3.connect(ns.db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000;")
    try:
        rows = conn.execute(
            "SELECT task_id, status, last_heartbeat_at, created_at FROM build_tasks "
            "WHERE build_run_id=? AND status='in_progress';",
            (ns.build_run_id,),
        ).fetchall()
    except sqlite3.Error as exc:
        raise errors.StateError(f"query failed: {exc}") from exc
    finally:
        conn.close()

    stalled = []
    for r in rows:
        # Tasks with no heartbeat yet (NULL) use created_at as the liveness basis —
        # prevents a freshly dispatched task from being misjudged as stalled before its first heartbeat.
        liveness = r["last_heartbeat_at"] or r["created_at"]
        if _parse_iso(liveness) < threshold:
            stalled.append(r["task_id"])

    if not stalled:
        action = "none"
    elif len(stalled) >= STALL_TASK_THRESHOLD:
        action = "solo-mode"
    else:
        action = "retry-then-reroute-then-blocking-surfacer"

    return result.ok(
        {
            "build_run_id": ns.build_run_id,
            "timeout_minutes": TIMEOUT_MINUTES,
            "stalled_tasks": stalled,
            "stalled_count": len(stalled),
            "action": action,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="swarm_fallback", description="deterministic timeout detection")
    parser.add_argument("--help-json", action="store_true")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--build-run-id", default=None)
    parser.add_argument("--now", default=None)
    parser.set_defaults(fn=cmd)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    if not ns.build_run_id or not ns.now:
        parser.print_help(sys.stderr)
        return 2
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
