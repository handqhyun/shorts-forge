"""shorts_forge — 로컬 실행 전용 YouTube Shorts 자동 생성 (게이트 비의존 구현).

정본 입력: ../PRD.md v0.2 · ../workflow.md v0.2 · ../prd-research/final-research.md.
본 패키지는 그 하위 산출물이며 단정하지 않는다. INVARIANT #1(로컬 불변)은
import 시 전역 monkeypatch 하지 않는다 — 테스트 러너/패키징 안정성 때문 —
대신 실행 경로(cli.run)가 netguard.guarded() 로 명시 설치한다(workflow §6).
"""

__version__ = "0.1.0"

TRACE = {
    "prd": "§0",
    "workflow": "§0",
    "ax": [],
    "f": [],
    "gate": [],
}
