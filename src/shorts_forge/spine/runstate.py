"""RunState — 단계 간 공유 blackboard(멱등·결정론).

추적: PRD §10 OPS-3 · workflow.md §4 · [F §3.2]
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from ..invariants import encoding, seed as seedmod
from . import db as dbmod

TRACE = {
    "prd": "§10 OPS-3",
    "workflow": "§4",
    "ax": ["AX-ORCH", "AX-OPS"],
    "f": ["§3.2"],
    "gate": [],
}

STAGES = ("S1", "S2", "S3", "S4", "S5", "S6", "S7")


@dataclass
class Asset:
    """정규화 자산 1건(S1 산출)."""

    src_path_nfc: str
    content_hash: str
    kind: str = "unknown"               # still|clip|unknown
    confidence_tier: int = 5            # 1=EXIF .. 5=unknown (C-SPINE)
    timestamp: float | None = None
    orientation: int = 1
    quality: dict = field(default_factory=dict)
    work_path: str | None = None        # 정규화 작업표현 경로
    isolated: bool = False
    isolate_reason: str = ""


@dataclass
class RunState:
    run_id: str
    seed: int
    root: Path                          # ASCII 작업루트(런타임 모사)
    inbox: Path
    conn: object                        # sqlite3.Connection
    ledger: object                      # netguard.NetworkLedger
    code_version: str
    dry_run: bool = False
    creative_epoch: int = 0             # 리롤 시 증가(창의 노드만 무효화 — D-RR)
    assets: list[Asset] = field(default_factory=list)
    edl: dict | None = None
    artifacts: dict[str, str] = field(default_factory=dict)  # stage -> ref
    output_path: str | None = None
    metadata: dict | None = None        # 한국어 메타초안(제목/설명/해시태그)

    @property
    def run_dir(self) -> Path:
        return self.root / "runs" / self.run_id

    def stage_dir(self, stage: str) -> Path:
        d = self.run_dir / stage
        d.mkdir(parents=True, exist_ok=True)
        return d


def new_run(root: str | Path, inbox: str | Path, code_version: str,
            *, dry_run: bool = False, seed: int | None = None) -> RunState:
    """새 run 생성 — ASCII 작업루트 강제·고정 seed·DB 등록."""
    root_p = encoding.assert_ascii_workroot(root)
    inbox_p = encoding.nfc_path(inbox)
    run_id = uuid.uuid4().hex[:16]
    s = seed if seed is not None else seedmod.derive_seed(run_id)

    from ..invariants.netguard import NetworkLedger

    conn = dbmod.connect(root_p / "state.sqlite")
    conn.execute(
        "INSERT INTO runs (run_id, created_at, seed, status, code_version) "
        "VALUES (?,?,?,?,?)",
        (run_id, time.time(), s, "pending", code_version),
    )
    conn.commit()
    (root_p / "runs" / run_id).mkdir(parents=True, exist_ok=True)
    return RunState(
        run_id=run_id, seed=s, root=root_p, inbox=inbox_p, conn=conn,
        ledger=NetworkLedger(), code_version=code_version, dry_run=dry_run,
    )
