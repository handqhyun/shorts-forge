"""콘텐츠주소 캐시 + 리롤 경계.

추적: PRD §7 ALWAYS(리롤=창의 노드만 무효화·결정론 분석 재사용) · workflow.md §4 [DESIGN] · [F §3.2]
[DESIGN] D-RR: 무효화 경계 = 창의 노드만 {S3 정렬, S5 매칭, LLM 메타}.
S1/S2 콘텐츠주소 산출물은 리롤 시 항상 재사용. creative_epoch 는 창의 키만 포함.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

TRACE = {
    "prd": "§7 ALWAYS",
    "workflow": "§4",
    "ax": ["AX-ORCH"],
    "f": ["§3.2"],
    "gate": [],
}

# 창의 노드(리롤 시 무효화 대상). 결정론 노드(S1/S2)는 불포함 → 항상 재사용.
CREATIVE_NODES = frozenset({"S3", "S5", "LLM_META"})


def file_hash(path: str | Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def cache_key(stage: str, content_hash: str, params: str, creative_epoch: int) -> str:
    """캐시 키. 창의 노드만 creative_epoch 포함(D-RR 리롤 경계)."""
    parts = [stage, content_hash, params]
    if stage in CREATIVE_NODES:
        parts.append(f"epoch={creative_epoch}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def get(conn, content_hash: str) -> str | None:
    row = conn.execute(
        "SELECT artifact_path FROM cache WHERE content_hash=?", (content_hash,)
    ).fetchone()
    return row["artifact_path"] if row else None


def put(conn, content_hash: str, stage: str, artifact_path: str) -> None:
    import time

    conn.execute(
        "INSERT OR REPLACE INTO cache (content_hash, stage, artifact_path, created_at) "
        "VALUES (?,?,?,?)",
        (content_hash, stage, str(artifact_path), time.time()),
    )
    conn.commit()
