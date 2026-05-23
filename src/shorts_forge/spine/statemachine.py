"""손수제작 결정론 상태머신 — 멱등 선형 DAG S1..S7.

추적: PRD §6 J-2·§10 OPS-3·§11(단계 게이트) · workflow.md §1/§4 · [F §3.2]
흐름은 **고정·선형**(LLM 흐름결정 불가 — R-CAP2). 단계당
precheck→run→validate_output→checkpoint→next. 체크포인트 센티넬로 멱등 재진입.
INVARIANT #1 강제(netguard.guarded)·run 락·우선순위는 호출자(cli)가 감싼다.
"""
from __future__ import annotations

import time

from .contracts import StageContract, StageResult
from . import db as dbmod
from .runstate import RunState

TRACE = {
    "prd": "§6 J-2",
    "workflow": "§1",
    "ax": ["AX-ORCH", "AX-OPS"],
    "f": ["§3.2"],
    "gate": [],
}


def _checkpoint_ok(rs: RunState, stage: str) -> bool:
    """센티넬 + DB 체크포인트 ok → 멱등 스킵(OPS-3)."""
    sentinel = rs.stage_dir(stage) / "stage.done"
    if not sentinel.exists():
        return False
    row = rs.conn.execute(
        "SELECT status FROM stage_checkpoints WHERE run_id=? AND stage=?",
        (rs.run_id, stage),
    ).fetchone()
    return bool(row and row["status"] == "ok")


def _write_checkpoint(rs: RunState, stage: str, status: str,
                      started: float, ended: float, output_ref: str | None,
                      error_class: str = "") -> None:
    rs.conn.execute(
        "INSERT OR REPLACE INTO stage_checkpoints "
        "(run_id, stage, status, started_at, ended_at, output_ref, error_class) "
        "VALUES (?,?,?,?,?,?,?)",
        (rs.run_id, stage, status, started, ended, output_ref, error_class),
    )
    rs.conn.execute(
        "UPDATE runs SET current_stage=? WHERE run_id=?", (stage, rs.run_id)
    )
    rs.conn.commit()
    if status == "ok":
        (rs.stage_dir(stage) / "stage.done").write_text(
            str(ended), encoding="utf-8"
        )


def run_pipeline(rs: RunState, stages: list[StageContract]) -> RunState:
    """S1..S7 결정론 실행. 실패 시 체크포인트 기록 후 re-raise."""
    rs.conn.execute(
        "UPDATE runs SET status='running' WHERE run_id=?", (rs.run_id,)
    )
    rs.conn.commit()
    try:
        for stage in stages:
            sid = stage.stage_id
            if _checkpoint_ok(rs, sid):
                continue  # 멱등 재진입 — 결정론 산출 재사용(D-RR: S1/S2 항상)
            started = time.time()
            try:
                stage.precheck(rs)
                result: StageResult = stage.run(rs)
                stage.validate_output(rs, result)
            except Exception as exc:  # noqa: BLE001 — 단계 실패 격리·체크포인트
                _write_checkpoint(rs, sid, "failed", started, time.time(),
                                  None, type(exc).__name__)
                rs.conn.execute(
                    "UPDATE runs SET status='failed' WHERE run_id=?", (rs.run_id,)
                )
                rs.conn.commit()
                raise
            for gate_id, gres, detail in result.gate_events:
                dbmod.log_gate(rs.conn, rs.run_id, gate_id, gres, detail)
            _write_checkpoint(rs, sid, "ok", started, time.time(),
                              result.artifact_ref)
        rs.conn.execute(
            "UPDATE runs SET status='done', output_manifest_path=? WHERE run_id=?",
            (rs.output_path, rs.run_id),
        )
        rs.conn.commit()
        return rs
    finally:
        # 실행당 네트워크 원장 영속화 — INVARIANT #1 감사(SM-3)
        dbmod.flush_network_ledger(rs.conn, rs.run_id, rs.ledger)
