"""결정론 고정 seed 레지스트리.

추적: PRD §7 ALWAYS("산출 결정론 기본, 고정 seed") · workflow.md §0 #5 · [F §3.2]

규칙: 모든 결정론 단계는 동일 입력+동일 seed → 동일 산출. 리롤은 창의 노드만
무효화(spine/cache.py CREATIVE_NODES). 미디어 연산에 비결정 난수 금지.
"""
from __future__ import annotations

import hashlib
import random

TRACE = {
    "prd": "§7 ALWAYS",
    "workflow": "§0 #5",
    "ax": ["AX-ORCH"],
    "f": ["§3.2"],
    "gate": [],
}

DEFAULT_SEED = 1234567


def derive_seed(*parts: object, base: int = DEFAULT_SEED) -> int:
    """입력 부분들로부터 안정·결정론 seed 파생(플랫폼 무관, 해시 기반)."""
    h = hashlib.sha256(repr((base, *parts)).encode("utf-8")).hexdigest()
    return int(h[:12], 16)


def rng(*parts: object, base: int = DEFAULT_SEED) -> random.Random:
    """파생 seed 로 고정된 결정론 RNG(stdlib만; numpy 비의존)."""
    return random.Random(derive_seed(*parts, base=base))
