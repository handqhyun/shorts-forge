"""상태 DB — SQLite 스키마(run 상태·체크포인트·콘텐츠주소 캐시·네트워크 원장).

추적: PRD §10 OPS-3(멱등 상태·체크포인트)·§4(network ledger) · workflow.md §4 · [F §3.2/§3.4]
손수제작 상태머신 1순위([F §3.2]): SQLite+파일, 클라우드 위험 0·최소 풋프린트.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

TRACE = {
    "prd": "§10 OPS-3",
    "workflow": "§4",
    "ax": ["AX-OPS", "AX-ORCH"],
    "f": ["§3.2", "§3.4"],
    "gate": [],
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    seed INTEGER NOT NULL,
    status TEXT NOT NULL,                 -- pending|running|done|failed
    current_stage TEXT,
    input_manifest_hash TEXT,
    output_manifest_path TEXT,
    code_version TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inputs (
    run_id TEXT NOT NULL,
    src_path_nfc TEXT NOT NULL,          -- NFC 정규화 경로(C-I18N)
    content_hash TEXT NOT NULL,
    kind TEXT,                            -- still|clip|unknown
    quality_json TEXT,
    confidence_tier INTEGER,              -- 1=EXIF .. 5=unknown (C-SPINE 5단계)
    orientation INTEGER,
    isolated INTEGER DEFAULT 0,           -- 1=불량 격리(배치 비중단, C-INPUT)
    isolate_reason TEXT,
    PRIMARY KEY (run_id, content_hash)
);
CREATE TABLE IF NOT EXISTS stage_checkpoints (
    run_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,                 -- ok|failed
    started_at REAL, ended_at REAL,
    output_ref TEXT,
    retry_count INTEGER DEFAULT 0,
    error_class TEXT,
    PRIMARY KEY (run_id, stage)
);
CREATE TABLE IF NOT EXISTS cache (
    content_hash TEXT PRIMARY KEY,        -- 콘텐츠주소(리롤 결정론 재사용)
    stage TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS network_ledger (
    run_id TEXT NOT NULL,
    ts REAL NOT NULL,
    target TEXT NOT NULL,
    carveout_id TEXT                      -- NULL = INVARIANT #1 위반(SM-3 실패)
);
CREATE TABLE IF NOT EXISTS gate_log (
    run_id TEXT NOT NULL,
    ts REAL NOT NULL,
    gate_id TEXT NOT NULL,
    result TEXT NOT NULL,                 -- pass|fail|blocked
    detail TEXT
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    """DB 연결(스키마 보장). 부모 디렉터리 생성."""
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def flush_network_ledger(conn: sqlite3.Connection, run_id: str, ledger) -> None:
    """netguard.NetworkLedger 를 DB 로 영속화(실행당 원장 — INVARIANT #1 감사)."""
    conn.executemany(
        "INSERT INTO network_ledger (run_id, ts, target, carveout_id) VALUES (?,?,?,?)",
        [(run_id, e.ts, e.target, e.carveout_id) for e in ledger.entries],
    )
    conn.commit()


def log_gate(conn: sqlite3.Connection, run_id: str, gate_id: str,
             result: str, detail: str = "") -> None:
    import time

    conn.execute(
        "INSERT INTO gate_log (run_id, ts, gate_id, result, detail) VALUES (?,?,?,?,?)",
        (run_id, time.time(), gate_id, result, detail),
    )
    conn.commit()
