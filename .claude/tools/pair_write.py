"""P-5: pair-write CLI (atomic English+Korean sibling commit).

Reference: prompt/workflow-coding.md sections 5.3.5 (P-5), 3.4, 13.5.4.

The single permitted write path for *.en.md + *.ko.md sibling pairs. Validates the
sibling convention and the write-zone whitelist, computes SHA-256 anchors, performs
the idempotency check against pair_outputs, commits atomically (English first, then
Korean; rollback English on Korean failure when ko_status='ok'), and upserts the
pair_outputs row. Deterministic: hashlib + sqlite3, LLM 0.

A non-'ok' write requires --task-id: such a pair is subject to §8 gate 5 (build_state
set-task-completed blocks until every pair_outputs row of the task reaches
ko_status='ok'), and gate 5 keys on task_id, so an unlinked row would be invisible.

Standard library only: argparse, hashlib, json, sqlite3, sys, datetime, pathlib.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import build_state, errors, result

TRACE = {
    "module": "tools.pair_write",
    "imports": [
        "argparse", "hashlib", "json", "sqlite3", "sys", "datetime", "pathlib",
        "tools.errors", "tools.result", "tools.build_state",
    ],
    "imported_by": [],
    "writes_state_keys": ["pair_outputs"],
    "reads_state_keys": ["pair_outputs"],
    "adapter_boundary_id": "ADAPT-TOOL-pair_write",
}

DEFAULT_DB = "impl/.claude/state/build_state.sqlite"
ALLOWED_ZONES = ("impl/.claude/runs/", "impl/docs/", "prompt/decisions/")
SOT_AXES = (
    "prompt/PRD.md",
    "prompt/workflow.md",
    "prompt/prd-research/final-research.md",
    "prompt/impl/docs/TRACEABILITY.md",
)
# Single source for the ko_status enum (build_state owns the canonical tuple).
KO_STATUS = build_state.KO_STATUS

HELP_JSON = {
    "tool": "pair_write",
    "args": {
        "--db": "str build_state db path",
        "--en-path": "str path ending .en.md (required)",
        "--en-content-file": "str file holding English original (required)",
        "--ko-path": "str sibling path ending .ko.md (required)",
        "--ko-content-file": "str file holding Korean translation (required for ok)",
        "--step-id": "str artifact id (required)",
        "--build-run-id": "str (required)",
        "--task-id": "str (required when --ko-status != 'ok'; else str|null)",
        "--ko-status": f"enum{KO_STATUS} (default ok)",
        "--now": "str ISO-8601 timestamp override (determinism)",
    },
}


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _norm(p: str) -> str:
    return p.replace("\\", "/")


def _check_sibling(en_path: str, ko_path: str) -> None:
    en, ko = _norm(en_path), _norm(ko_path)
    if not en.endswith(".en.md"):
        raise errors.ValidationError(f"en_path must end with .en.md: {en_path}")
    if not ko.endswith(".ko.md"):
        raise errors.ValidationError(f"ko_path must end with .ko.md: {ko_path}")
    if en[: -len(".en.md")] != ko[: -len(".ko.md")]:
        raise errors.ValidationError("en_path and ko_path must share basename+dir")


def _check_zone(path: str) -> None:
    n = _norm(path)
    if any(n.endswith(axis) or n == axis for axis in SOT_AXES):
        raise errors.IntegrityError(f"SOT axis path rejected: {path}")
    if not any(n.startswith(z) or ("/" + z) in n for z in ALLOWED_ZONES):
        raise errors.ValidationError(f"path outside allowed write zones: {path}")


def cmd_write(ns: argparse.Namespace) -> result.ToolResult:
    if ns.ko_status not in KO_STATUS:
        raise errors.ValidationError(f"--ko-status must be one of {KO_STATUS}")
    # A non-'ok' pair must be linked to its task: §8 gate 5 (set-task-completed) keys on
    # task_id, so an unlinked non-ok row is invisible to the backstop and would let a task
    # complete with an unverified translation. Enforce the link at the single write path.
    if ns.ko_status != "ok" and not ns.task_id:
        raise errors.ValidationError(
            "--task-id is required when --ko-status != 'ok' "
            "(unlinked non-ok pair is invisible to §8 gate 5 in set-task-completed)"
        )
    _check_sibling(ns.en_path, ns.ko_path)
    _check_zone(ns.en_path)
    _check_zone(ns.ko_path)

    en_file = Path(ns.en_content_file)
    if not en_file.is_file():
        raise errors.NotFoundError(f"--en-content-file not found: {ns.en_content_file}")
    en_content = en_file.read_text(encoding="utf-8")
    en_sha = _sha256_text(en_content)

    db = Path(ns.db)
    if not db.is_file():
        raise errors.StateError(f"build_state db not initialized: {ns.db}")

    now = ns.now or datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(ns.db)
    conn.row_factory = sqlite3.Row
    try:
        # Idempotency: same (build_run_id, step_id, en_path) with same en_sha and ok.
        row = conn.execute(
            "SELECT en_sha, ko_status FROM pair_outputs "
            "WHERE build_run_id=? AND step_id=? AND en_path=?;",
            (ns.build_run_id, ns.step_id, ns.en_path),
        ).fetchone()
        if row is not None and row["en_sha"] == en_sha and row["ko_status"] == "ok":
            return result.ok({"idempotent": True, "en_sha": en_sha, "atomicity_ok": True})

        ko_sha = None
        ts_ko = None
        # Atomic commit: English first.
        Path(ns.en_path).parent.mkdir(parents=True, exist_ok=True)
        Path(ns.en_path).write_text(en_content, encoding="utf-8")

        if ns.ko_status == "ok":
            if not ns.ko_content_file or not Path(ns.ko_content_file).is_file():
                # rollback English
                Path(ns.en_path).unlink(missing_ok=True)
                raise errors.IntegrityError("ko_status=ok requires --ko-content-file; rolled back English")
            ko_content = Path(ns.ko_content_file).read_text(encoding="utf-8")
            try:
                Path(ns.ko_path).parent.mkdir(parents=True, exist_ok=True)
                Path(ns.ko_path).write_text(ko_content, encoding="utf-8")
            except OSError as exc:
                Path(ns.en_path).unlink(missing_ok=True)
                raise errors.IntegrityError(f"Korean write failed; rolled back English: {exc}") from exc
            ko_sha = _sha256_text(ko_content)
            ts_ko = now

        conn.execute(
            "INSERT INTO pair_outputs "
            "(build_run_id, task_id, step_id, en_path, ko_path, en_sha, ko_sha, "
            " ko_status, ko_attempts, ts_en, ts_ko) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?) "
            "ON CONFLICT(build_run_id, step_id, en_path) DO UPDATE SET "
            "  en_sha=excluded.en_sha, ko_sha=COALESCE(excluded.ko_sha, pair_outputs.ko_sha), "
            "  ko_status=excluded.ko_status, ts_en=excluded.ts_en, "
            "  ts_ko=COALESCE(excluded.ts_ko, pair_outputs.ts_ko);",
            (
                ns.build_run_id, ns.task_id, ns.step_id, ns.en_path, ns.ko_path,
                en_sha, ko_sha, ns.ko_status, now, ts_ko,
            ),
        )
        conn.commit()
    except sqlite3.Error as exc:
        raise errors.IntegrityError(f"pair_outputs upsert failed: {exc}") from exc
    finally:
        conn.close()

    return result.ok(
        {
            "idempotent": False,
            "en_sha": en_sha,
            "ko_sha": ko_sha,
            "ko_status": ns.ko_status,
            "atomicity_ok": True,
            "ts_en": now,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pair_write", description="atomic en+ko pair write")
    parser.add_argument("--help-json", action="store_true")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--en-path")
    parser.add_argument("--en-content-file")
    parser.add_argument("--ko-path")
    parser.add_argument("--ko-content-file", default=None)
    parser.add_argument("--step-id")
    parser.add_argument("--build-run-id")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--ko-status", default="ok")
    parser.add_argument("--now", default=None)
    parser.set_defaults(fn=cmd_write)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    required = (ns.en_path, ns.ko_path, ns.en_content_file, ns.step_id, ns.build_run_id)
    if any(v is None for v in required):
        parser.print_help(sys.stderr)
        return 2
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
