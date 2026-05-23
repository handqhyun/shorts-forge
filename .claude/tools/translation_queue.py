"""hook backing: translation queue check/summary (§6.1, §6.2).

Reference: prompt/workflow-coding.md sections 6.1, 6.2, 6.7 (P-10 mapping).

Queries pair_outputs for rows whose ko_status is not 'ok' (i.e. pending/produced/
failed) and returns the count plus the oldest/most-recent step ids. Deterministic
sqlite read.

Standard library only: argparse, json, sqlite3, sys, pathlib.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from . import errors, result

TRACE = {
    "module": "tools.translation_queue",
    "imports": ["argparse", "json", "sqlite3", "sys", "pathlib", "tools.errors", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": ["pair_outputs"],
    "adapter_boundary_id": "ADAPT-TOOL-translation_queue",
}

DEFAULT_DB = "impl/.claude/state/build_state.sqlite"
PENDING_STATES = ("pending", "produced", "failed")

HELP_JSON = {
    "tool": "translation_queue",
    "args": {
        "--mode": "enum('check','summary') (required)",
        "--db": f"str build_state db (default: {DEFAULT_DB})",
        "--limit": "int max step ids in summary (default 5)",
    },
}


def cmd(ns: argparse.Namespace) -> result.ToolResult:
    if ns.mode not in ("check", "summary"):
        raise errors.ValidationError("--mode must be check|summary")
    if not Path(ns.db).is_file():
        return result.ok({"db_present": False, "pending_count": 0, "step_ids": []})
    conn = sqlite3.connect(ns.db)
    conn.row_factory = sqlite3.Row
    try:
        placeholders = ",".join("?" for _ in PENDING_STATES)
        rows = conn.execute(
            f"SELECT step_id, ko_status, ts_en FROM pair_outputs "
            f"WHERE ko_status IN ({placeholders}) ORDER BY ts_en ASC;",
            PENDING_STATES,
        ).fetchall()
    except sqlite3.Error as exc:
        raise errors.StateError(f"query failed: {exc}") from exc
    finally:
        conn.close()
    count = len(rows)
    step_ids = [r["step_id"] for r in rows[: ns.limit]]
    data = {"db_present": True, "pending_count": count, "step_ids": step_ids}
    if ns.mode == "summary" and rows:
        data["oldest_step_id"] = rows[0]["step_id"]
    return result.ok(data)


def build_parser():
    p = argparse.ArgumentParser(prog="translation_queue", description="translation queue check/summary")
    p.add_argument("--help-json", action="store_true")
    p.add_argument("--mode")
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(fn=cmd)
    return p


def main(argv=None) -> int:
    ns = build_parser().parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    if not ns.mode:
        build_parser().print_help(sys.stderr)
        return 2
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
