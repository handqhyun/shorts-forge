"""hook backing: Stop -> persist pending decisions (§6.6).

Reference: prompt/workflow-coding.md sections 6.6, 6.7 (P-10 mapping).

Queries build_decisions for rows with no owner_resolved_at (still open) and writes
an append-only summary to prompt/decisions/pending.md. Deterministic sqlite read +
append. Note: prompt/decisions/ is NOT a SOT axis, so the append is permitted.

Standard library only: argparse, json, sqlite3, sys, datetime, pathlib.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import errors, result

TRACE = {
    "module": "tools.persist_pending_decisions",
    "imports": ["argparse", "json", "sqlite3", "sys", "datetime", "pathlib", "tools.errors", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": ["build_decisions"],
    "adapter_boundary_id": "ADAPT-TOOL-persist_pending_decisions",
}

DEFAULT_DB = "impl/.claude/state/build_state.sqlite"
DEFAULT_OUT = "prompt/decisions/pending.md"

HELP_JSON = {
    "tool": "persist_pending_decisions",
    "args": {
        "--db": f"str build_state db (default: {DEFAULT_DB})",
        "--out": f"str pending md path (default: {DEFAULT_OUT})",
        "--now": "str ISO-8601 timestamp override (determinism)",
        "--dry-run": "flag do not write, only report",
    },
}


def cmd(ns: argparse.Namespace) -> result.ToolResult:
    if not Path(ns.db).is_file():
        return result.ok({"db_present": False, "open_count": 0, "wrote": False})
    conn = sqlite3.connect(ns.db)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT decision_id, decision_type, gate_id FROM build_decisions "
            "WHERE owner_resolved_at IS NULL ORDER BY decision_id;"
        ).fetchall()
    except sqlite3.Error as exc:
        raise errors.StateError(f"query failed: {exc}") from exc
    finally:
        conn.close()

    open_decisions = [
        {"decision_id": r["decision_id"], "decision_type": r["decision_type"], "gate_id": r["gate_id"]}
        for r in rows
    ]
    if ns.dry_run:
        return result.ok({"db_present": True, "open_count": len(open_decisions), "wrote": False, "open": open_decisions})

    now = ns.now or datetime.now(timezone.utc).isoformat()
    out = Path(ns.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"\n## pending decisions snapshot {now}\n"]
    for d in open_decisions:
        lines.append(f"- {d['decision_id']} [{d['decision_type']}] gate={d['gate_id']}\n")
    with out.open("a", encoding="utf-8") as f:
        f.writelines(lines)
    return result.ok({"db_present": True, "open_count": len(open_decisions), "wrote": True, "out": str(out)})


def build_parser():
    p = argparse.ArgumentParser(prog="persist_pending_decisions", description="persist open decisions")
    p.add_argument("--help-json", action="store_true")
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--out", default=DEFAULT_OUT)
    p.add_argument("--now", default=None)
    p.add_argument("--dry-run", action="store_true")
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
