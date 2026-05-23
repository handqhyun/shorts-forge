"""StageContract — 단계 계약(precheck→run→validate_output, 결정론).

추적: PRD §9 R-CAP2(LLM 흐름결정 금지·결정론 코드가 C-* 검증 후 미디어 연산)
 · workflow.md §0 #6·§2 · [F §2]
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field

TRACE = {
    "prd": "§9 R-CAP2",
    "workflow": "§2",
    "ax": ["AX-ORCH"],
    "f": ["§2"],
    "gate": [],
}


@dataclass
class StageResult:
    ok: bool
    stage_id: str
    artifact_ref: str | None = None
    gate_events: list[tuple[str, str, str]] = field(default_factory=list)  # (gate,result,detail)
    isolated_inputs: list[str] = field(default_factory=list)
    detail: str = ""


class StageContract(abc.ABC):
    """모든 S1–S7 단계의 계약. 흐름은 고정·선형(LLM 흐름결정 금지 — R-CAP2)."""

    stage_id: str = ""
    TRACE: dict = {}

    def precheck(self, rs) -> None:
        """상류 불변식/C-* 전제 확인. 미충족 시 raise(다음 단계 진입 차단)."""

    @abc.abstractmethod
    def run(self, rs) -> StageResult:
        """결정론 실행(동일 입력+seed → 동일 산출). 부작용=체크포인트/아티팩트."""
        raise NotImplementedError

    def validate_output(self, rs, result: StageResult) -> None:
        """C-* + 체크포인트 무결성 검증. 다음 단계 호출 *전* 반드시 통과.

        기본: ok=False 면 RuntimeError. 단계별 오버라이드로 C-* 강화.
        """
        if not result.ok:
            raise RuntimeError(
                f"{self.stage_id} 산출 검증 실패: {result.detail}"
            )
