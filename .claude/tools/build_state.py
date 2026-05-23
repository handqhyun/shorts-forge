"""P-11: build_state.sqlite CRUD CLI (single write path).

Reference: prompt/workflow-coding.md section 3.4 (P-11), 16 IQ-28 RESOLVED.

The orchestrator and every subagent route build_state.sqlite writes for the four
core tables (build_runs, build_tasks, build_decisions, build_forks) through this
CLI; no component writes raw SQL to them. The pair_outputs table is co-owned: row
creation is performed atomically by tools.pair_write (file + DB in one transaction,
so it cannot be split into a separate process without breaking the en/ko atomicity
guarantee), while ko_status transitions go through set-pair-status here. Both
writers share the KO_STATUS enum defined in this module (single source). Column
names and enum values are validated here so that hallucinated values
(e.g. ko_status='okay') are rejected deterministically.

Subcommands:
    init                 apply schema.sql to create/initialize the database
    create-run           insert a build_runs row
    update-task          upsert a build_tasks row
    set-task-completed   mark a build_tasks row completed
    set-pair-status      upsert a pair_outputs row's ko_status
    insert-decision      insert a build_decisions row
    update-fork-status   update a build_forks row's status
    --help-json          print the machine-readable argument schema

All output uses the {"status","data","errors"} envelope (tools.result).
Standard library only: argparse, sqlite3, json, pathlib, datetime.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from . import errors, result

TRACE = {
    "module": "tools.build_state",
    "imports": ["argparse", "json", "sqlite3", "sys", "pathlib", "tools.errors", "tools.result"],
    "imported_by": ["tools.pair_write"],
    "writes_state_keys": [
        "build_runs", "build_tasks", "build_decisions", "build_forks", "pair_outputs",
    ],
    "reads_state_keys": [
        "build_runs", "build_tasks", "build_decisions", "build_forks", "pair_outputs",
    ],
    "adapter_boundary_id": "ADAPT-TOOL-build_state",
}

DEFAULT_DB = "impl/.claude/state/build_state.sqlite"
DEFAULT_SCHEMA = "impl/.claude/state/schema.sql"

PHASE_VALUES = ("-1", "-0.75", "-0.5", "0", "1", "2+")
RUN_STATUS = ("running", "halted_on_gate", "completed", "failed")
TASK_STATUS = ("pending", "in_progress", "completed", "failed", "timeout")
KO_STATUS = ("pending", "produced", "ok", "failed")
DECISION_TYPE = ("BLOCKING", "DESIGN", "INFRA-DESIGN")
FORK_STATUS = ("running", "merged", "discarded")

# Machine-readable schema for --help-json (mirrors the SKILL.md argument table).
HELP_JSON = {
    "tool": "build_state",
    "subcommands": {
        "init": {"args": {"--db": "str", "--schema": "str"}},
        "create-run": {
            "args": {
                "--db": "str",
                "--build-run-id": "str (required)",
                "--phase": f"enum{PHASE_VALUES}",
                "--started-at": "str ISO-8601 (required)",
                "--status": f"enum{RUN_STATUS}",
            }
        },
        "update-task": {
            "args": {
                "--db": "str",
                "--task-id": "str (required)",
                "--build-run-id": "str (required)",
                "--subagent-name": "str (required)",
                "--status": f"enum{TASK_STATUS}",
                "--stage": "str|null",
                "--last-heartbeat-at": "str ISO-8601|null (optional liveness stamp)",
                "--created-at": "str ISO-8601 (required)",
            }
        },
        "set-task-completed": {
            "args": {"--db": "str", "--task-id": "str (required)", "--completed-at": "str (required)"}
        },
        "set-pair-status": {
            "args": {
                "--db": "str",
                "--build-run-id": "str (required)",
                "--step-id": "str (required)",
                "--en-path": "str (required)",
                "--ko-status": f"enum{KO_STATUS}",
            }
        },
        "insert-decision": {
            "args": {
                "--db": "str",
                "--decision-id": "str (required)",
                "--build-run-id": "str (required)",
                "--decision-type": f"enum{DECISION_TYPE}",
                "--gate-id": "str|null",
            }
        },
        "update-fork-status": {
            "args": {
                "--db": "str",
                "--fork-id": "str (required)",
                "--status": f"enum{FORK_STATUS}",
            }
        },
    },
}


def _connect(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    if not path.is_file():
        raise errors.StateError(f"build_state database not initialized: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    # Parallel builders share one DB — without busy_timeout a concurrent writer fails immediately with SQLITE_BUSY.
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn


def _check_enum(name: str, value: str, allowed: tuple) -> None:
    if value not in allowed:
        raise errors.ValidationError(
            f"{name} must be one of {allowed}, got {value!r}"
        )


def cmd_init(ns: argparse.Namespace) -> result.ToolResult:
    schema_path = Path(ns.schema)
    if not schema_path.is_file():
        raise errors.NotFoundError(f"schema file not found: {ns.schema}")
    Path(ns.db).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(ns.db)
    try:
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        conn.commit()
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            ).fetchall()
        ]
    finally:
        conn.close()
    return result.ok({"db": ns.db, "tables": tables})


def cmd_create_run(ns: argparse.Namespace) -> result.ToolResult:
    _check_enum("phase", ns.phase, PHASE_VALUES)
    _check_enum("status", ns.status, RUN_STATUS)
    conn = _connect(ns.db)
    try:
        conn.execute(
            "INSERT INTO build_runs (build_run_id, phase, started_at, status, halted_gate) "
            "VALUES (?, ?, ?, ?, NULL);",
            (ns.build_run_id, ns.phase, ns.started_at, ns.status),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise errors.IntegrityError(f"create-run failed: {exc}") from exc
    finally:
        conn.close()
    return result.ok({"build_run_id": ns.build_run_id, "phase": ns.phase})


def cmd_update_task(ns: argparse.Namespace) -> result.ToolResult:
    _check_enum("status", ns.status, TASK_STATUS)
    conn = _connect(ns.db)
    try:
        conn.execute(
            "INSERT INTO build_tasks "
            "(task_id, build_run_id, subagent_name, stage, status, last_heartbeat_at, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(task_id) DO UPDATE SET "
            "subagent_name=excluded.subagent_name, stage=excluded.stage, "
            "status=excluded.status, "
            # On status-only update, preserve the existing heartbeat (update only when a new value is given).
            "last_heartbeat_at=COALESCE(excluded.last_heartbeat_at, build_tasks.last_heartbeat_at);",
            (ns.task_id, ns.build_run_id, ns.subagent_name, ns.stage, ns.status,
             ns.last_heartbeat_at, ns.created_at),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise errors.IntegrityError(f"update-task failed: {exc}") from exc
    finally:
        conn.close()
    return result.ok({"task_id": ns.task_id, "status": ns.status})


def cmd_set_task_completed(ns: argparse.Namespace) -> result.ToolResult:
    conn = _connect(ns.db)
    try:
        # §8 task-verification gate 5 (Korean pair) deterministic backstop: a task
        # that produced English artifacts may only complete once every one of its
        # pair_outputs rows reached ko_status='ok'. A task with no pair_outputs rows
        # is gate-5-exempt (§8.1: tasks with no English output skip this gate). The
        # invariant "어느 하나라도 실패 = task incomplete" is enforced here at the
        # write point rather than relying on the orchestrator's prose alone (B-4).
        blocking = conn.execute(
            "SELECT step_id, ko_status FROM pair_outputs "
            "WHERE task_id=? AND ko_status != 'ok' ORDER BY step_id;",
            (ns.task_id,),
        ).fetchall()
        if blocking:
            offenders = ", ".join(f"{r['step_id']}={r['ko_status']}" for r in blocking)
            raise errors.IntegrityError(
                f"task {ns.task_id} cannot complete: §8 gate 5 (Korean pair) "
                f"requires ko_status='ok' for all pair_outputs; non-ok: [{offenders}]",
                task_id=ns.task_id,
                gate="korean_pair",
            )
        cur = conn.execute(
            "UPDATE build_tasks SET status='completed', completed_at=? WHERE task_id=?;",
            (ns.completed_at, ns.task_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise errors.NotFoundError(f"task not found: {ns.task_id}")
    finally:
        conn.close()
    return result.ok({"task_id": ns.task_id, "status": "completed"})


def cmd_set_pair_status(ns: argparse.Namespace) -> result.ToolResult:
    _check_enum("ko_status", ns.ko_status, KO_STATUS)
    conn = _connect(ns.db)
    try:
        cur = conn.execute(
            "UPDATE pair_outputs SET ko_status=? "
            "WHERE build_run_id=? AND step_id=? AND en_path=?;",
            (ns.ko_status, ns.build_run_id, ns.step_id, ns.en_path),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise errors.NotFoundError(
                f"pair_outputs row not found for ({ns.build_run_id}, {ns.step_id}, {ns.en_path})"
            )
    finally:
        conn.close()
    return result.ok({"step_id": ns.step_id, "ko_status": ns.ko_status})


def cmd_insert_decision(ns: argparse.Namespace) -> result.ToolResult:
    _check_enum("decision_type", ns.decision_type, DECISION_TYPE)
    conn = _connect(ns.db)
    try:
        conn.execute(
            "INSERT INTO build_decisions "
            "(decision_id, build_run_id, decision_type, gate_id) VALUES (?, ?, ?, ?);",
            (ns.decision_id, ns.build_run_id, ns.decision_type, ns.gate_id),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise errors.IntegrityError(f"insert-decision failed: {exc}") from exc
    finally:
        conn.close()
    return result.ok({"decision_id": ns.decision_id, "decision_type": ns.decision_type})


def cmd_update_fork_status(ns: argparse.Namespace) -> result.ToolResult:
    _check_enum("status", ns.status, FORK_STATUS)
    conn = _connect(ns.db)
    try:
        cur = conn.execute(
            "UPDATE build_forks SET status=? WHERE fork_id=?;",
            (ns.status, ns.fork_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise errors.NotFoundError(f"fork not found: {ns.fork_id}")
    finally:
        conn.close()
    return result.ok({"fork_id": ns.fork_id, "status": ns.status})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="build_state", description="build_state.sqlite CRUD CLI")
    parser.add_argument("--help-json", action="store_true", help="print machine-readable schema")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("init")
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--schema", default=DEFAULT_SCHEMA)
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("create-run")
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--build-run-id", required=True)
    p.add_argument("--phase", required=True)
    p.add_argument("--started-at", required=True)
    p.add_argument("--status", default="running")
    p.set_defaults(fn=cmd_create_run)

    p = sub.add_parser("update-task")
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--task-id", required=True)
    p.add_argument("--build-run-id", required=True)
    p.add_argument("--subagent-name", required=True)
    p.add_argument("--stage", default=None)
    p.add_argument("--status", default="pending")
    p.add_argument("--last-heartbeat-at", default=None)
    p.add_argument("--created-at", required=True)
    p.set_defaults(fn=cmd_update_task)

    p = sub.add_parser("set-task-completed")
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--task-id", required=True)
    p.add_argument("--completed-at", required=True)
    p.set_defaults(fn=cmd_set_task_completed)

    p = sub.add_parser("set-pair-status")
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--build-run-id", required=True)
    p.add_argument("--step-id", required=True)
    p.add_argument("--en-path", required=True)
    p.add_argument("--ko-status", required=True)
    p.set_defaults(fn=cmd_set_pair_status)

    p = sub.add_parser("insert-decision")
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--decision-id", required=True)
    p.add_argument("--build-run-id", required=True)
    p.add_argument("--decision-type", required=True)
    p.add_argument("--gate-id", default=None)
    p.set_defaults(fn=cmd_insert_decision)

    p = sub.add_parser("update-fork-status")
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--fork-id", required=True)
    p.add_argument("--status", required=True)
    p.set_defaults(fn=cmd_update_fork_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    if not getattr(ns, "cmd", None):
        parser.print_help(sys.stderr)
        return 2
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
