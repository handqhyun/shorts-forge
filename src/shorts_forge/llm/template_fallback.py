"""메타 노드 강등형 — KR 템플릿 메타초안(모델 0). 단일 LLM 터치의 SM-1 바닥.

추적: PRD §9 R-CAP3·§2 SM-1·§6 J-3·§7 ASK(침묵 자동게시 Never) · workflow.md §5
 · 【AX-I18N】 [F §3.11]
한글 1음절=1자(불이익 없음)·모바일 truncation → 첫 ~20–25 음절 훅. 해시태그
`#쇼츠 #shorts`+토픽(≤15). 텍스트만(픽셀 NEVER). [GATE:D5] 슬랭 자유생성 금지.
"""
from __future__ import annotations

import json

from ..invariants import encoding
from ..spine.contracts import StageContract, StageResult
from ..spine.gates import gate_blocked
from ..spine.runstate import RunState

TRACE = {
    "prd": "§9 R-CAP3",
    "workflow": "§5",
    "ax": ["AX-I18N"],
    "f": ["§3.11"],
    "gate": ["D5"],
}

# 비-슬랭 중립-친근 존댓말 안전 템플릿(D5 폴백·결정론). 자유 생성 금지.
_TITLE_TMPL = "오늘의 기록 | 사진과 영상으로 만든 쇼츠"
_DESC_TMPL = ("직접 찍은 사진과 영상을 모아 만든 약 {sec}초 세로 영상입니다. "
              "편하게 봐 주세요.")
_BASE_TAGS = ["#쇼츠", "#shorts", "#일상", "#영상기록"]


@gate_blocked("D5")
def resolve_slang(_text: str):
    """[GATE:D5] 트렌드/슬랭 렉시콘 = 미결정. 자유 생성 금지·중립 폴백만."""


def draft_metadata(rs: RunState) -> dict:
    """결정론 KR 메타초안(모델 0). 첫 ~25 음절 훅·해시태그≤15·텍스트만."""
    assert rs.edl is not None
    sec = int(round(sum(e["out"] - e["in"] for e in rs.edl["timeline"])))
    n = len([a for a in rs.assets if not a.isolated])
    title = encoding.nfc(_TITLE_TMPL)[:90]          # 제목 100자 한도 여유
    desc = encoding.nfc(_DESC_TMPL.format(sec=max(1, sec)))
    tags = _BASE_TAGS[:15]                            # >15 면 전부 무시 → 절대 초과 금지
    meta = {
        "title": title,
        "description": f"{desc}\n\n총 {n}개 컷.",
        "hashtags": tags,
        "ai_disclosure": False,   # 증분1=실사 조합·무음(AI 음악/보이스 없음)
        "source": "template_fallback(model=0, D5 비-슬랭 중립)",
    }
    return meta


class MetaDraftNode(StageContract):
    """단일 LLM 메타 노드(증분1 강등형). S5 뒤·S6 앞에 위치."""

    stage_id = "META"
    TRACE = TRACE

    def run(self, rs: RunState) -> StageResult:
        meta = draft_metadata(rs)
        rs.metadata = meta
        out_dir = rs.root / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        draft = out_dir / f"{rs.run_id}.metadata.json"
        draft.write_text(json.dumps(meta, **encoding.json_dump_kwargs()),
                         encoding="utf-8")
        rs.artifacts["META"] = str(draft)
        return StageResult(
            ok=True, stage_id=self.stage_id, artifact_ref=str(draft),
            gate_events=[("D5", "blocked", "슬랭 자유생성 금지·중립 존댓말 폴백")],
            detail="KR 메타초안(모델 0·침묵 자동게시 없음 — J-3 1탭 편집)",
        )
