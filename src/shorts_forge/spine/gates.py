"""게이트 강제 — PRD §12 BLOCKING 미결정 의존 경로의 구조적 차단.

추적: PRD §12 D1–D16·§4 ALIGNMENT #1 · workflow.md §10 게이트 맵 · [F §8]
ANCHOR ③: 본 코드는 소유자 미결정을 단정하지 않는다. 차단 경로는 호출 시
GateBlocked 만 raise → 우발적 구현이 import-time + 테스트로 구조적 불가.

상태(2026-05-18 소유자 세션, PRD v0.2): D4 해소(소유권=소유자, 본 증분은
하니스 구조만·코퍼스 미제작) · D6 부분해제(베이스라인=OV sideload) · D3=B3 보류.
2026-05-19 PRD v0.5/workflow v0.3 정합: D10–D16·§4 ALIGNMENT #1을 GATES 레지스트리에
표면화 등록 — 코드 결정 안 함(ANCHOR ③ 동일·@gate_blocked 데코경로 미생성).
"""
from __future__ import annotations

import functools
from dataclasses import dataclass

TRACE = {
    "prd": "§12 D1–D16·§4 ALIGNMENT #1",
    "workflow": "§10",
    "ax": ["AX-PUBLISH", "AX-LICENSE", "AX-EVAL", "AX-ONBOARD"],
    "f": ["§8"],
    "gate": ["D1", "D2", "D3", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12", "D13", "D14", "D15", "D16"],
}


@dataclass(frozen=True)
class GateInfo:
    gate_id: str
    prd_ref: str
    workflow_ref: str
    classification: str  # HARD-BLOCKED | PROVISIONAL | PARTIAL
    note: str


# workflow.md §10 게이트 맵 ↔ 코드 정본
GATES: dict[str, GateInfo] = {
    "D1": GateInfo("D1", "§8.3", "§7", "PROVISIONAL",
                   "수치 문턱 = Phase-0 골든 보정 전 미정의. 상수 채택 금지·Fowler ratchet."),
    "D2": GateInfo("D2", "§12-D2", "S5", "HARD-BLOCKED",
                   "CC0 음악 라이브러리 콘텐츠 소싱·번들 미해소. 매칭 엔진만, 콘텐츠 절대 미번들. "
                   "(v1.2 currency 2026-05-25 option2: 소유자 수동 로컬 음악 폴더 "
                   "`<sf_root>/music/`·소유자 배치·라이선스=소유자·외부 fetch 0·"
                   "결정론 선택·빈 폴더=무음 폴백 동형·정밀 라우드니스는 [DESIGN] 잔존.)"),
    "D3": GateInfo("D3", "§12-D3", "§3", "HARD-BLOCKED",
                   "자동게시 = 2026-05-18 소유자 세션 B3 명시 보류. publish 자동화 금지·v1=파일만."),
    "D5": GateInfo("D5", "§12-D5", "S3/§5", "PROVISIONAL",
                   "트렌드/슬랭 팩 메커니즘 미결정. 잠정=연대순·비-슬랭 안전 카피. "
                   "(v1.0 currency 2026-05-25 option2: 소유자 수동 로컬 렉시콘 "
                   "`<sf_root>/lex/trending.txt`·외부 fetch 0·빈 lex=폴백 동형·"
                   "스키마/UI는 [DESIGN] 잔존.)"),
    "D6": GateInfo("D6", "§6 J-0", "§8", "PARTIAL",
                   "D6a: 베이스라인=OV sideload 확정. MS Store/Azure 무경고 채널=적격성 스파이크 잔존."),
    "D7": GateInfo("D7", "§12-D7", "§8", "PROVISIONAL",
                   "디바이스 실측치 미측정. 보수 기본 티어, 자동 티어선택 임계 미확정."),
    "D8": GateInfo("D8", "§12-D8", "S5", "PROVISIONAL",
                   "Content-ID 오클레임 관리 메커니즘 미결정. placeholder 인터페이스만."),
    "D9": GateInfo("D9", "§13", "S1", "HARD-BLOCKED",
                   "HEVC 디코더 번들 vs OS-제공 = 법적 미해결. 조달 결정 금지·probe된 디코더만."),
    "D10": GateInfo("D10", "§12-D10", "§11", "HARD-BLOCKED",
                    "빌드/구현 실현성(X1)=K-class 미측정. 전 구현 논리적 선결·코드 결정 안 함(표면화)."),
    "D11": GateInfo("D11", "§12-D11", "§9", "HARD-BLOCKED",
                    "unrecoverable-failure taxonomy(X2)=부분-상태 손상 복구 매트릭스 미명세(제3 BLOCKING 후보)."),
    "D12": GateInfo("D12", "§12-D12", "§10", "PROVISIONAL",
                    "위임-결정자 정합(L2·메타). 코드 표현 없음 — 표면화만, 본 코드 결정 안 함."),
    "D13": GateInfo("D13", "§12-D13", "§7", "HARD-BLOCKED",
                    "빌드정확성 수용객체(G2)=§8 출력품질과 범주 별개·D4/D11과 병합금지(제2 BLOCKING 후보)."),
    "D14": GateInfo("D14", "§12-D14", "S5/S7", "HARD-BLOCKED",
                    "무드음악 매칭 수용 차원 부재. ★제1목적 '적절한 음악' 직격·s5 휴리스틱만·s7 무드게이트 부재. "
                    "(v1.2 currency 2026-05-25: D2와 단일 결정 수렴 — 매칭 차원='소유자 선택'·"
                    "코드 명시 매칭 엔진 부재·★제1 충족 객체=소유자 큐레이션 한정으로 명시 재정의.)"),
    "D15": GateInfo("D15", "§12-D15", "§7/S7", "HARD-BLOCKED",
                    "실사용자 수용루프 부재. 판정자=소유자/머신만, 1차 비전문가 만족·재조정 권한 미명명."),
    "D16": GateInfo("D16", "§12-D16", "S3/§5", "PROVISIONAL",
                    "트렌드 갱신운영·부패수용 미명세. D5 메커니즘과 별개 운영축(주 단위 TIME-DECAY). "
                    "(v1.0 currency 2026-05-25: D5와 단일 결정 수렴 — 갱신=소유자 수동 편집·"
                    "cadence 강제 0·묵은 lex=정상 강등 수용판정.)"),
}


class GateBlocked(RuntimeError):
    """PRD §12 BLOCKING 게이트 의존 경로 호출 — 미해소 전 구현 착수 불가."""

    def __init__(self, gate_id: str):
        self.gate_id = gate_id
        info = GATES.get(gate_id)
        if info is None:
            super().__init__(f"[GATE:{gate_id}] 미정의 게이트")
            return
        super().__init__(
            f"[GATE:{gate_id}] {info.classification} — {info.note} "
            f"(PRD {info.prd_ref} / workflow {info.workflow_ref}). "
            f"소유자 미결정 해소 전 구현 착수 불가."
        )


def gate_blocked(gate_id: str):
    """차단 경로 데코레이터. 호출 시 GateBlocked 만 raise(구현 구조적 불가)."""
    if gate_id not in GATES:
        raise KeyError(f"미등록 게이트: {gate_id}")

    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            raise GateBlocked(gate_id)

        wrapper.__gate_blocked__ = gate_id  # type: ignore[attr-defined]
        return wrapper

    return deco
