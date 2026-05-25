"""메타 노드 강등형 — KR 템플릿 메타초안(모델 0). 단일 LLM 터치의 SM-1 바닥.

추적: PRD §9 R-CAP3·§2 SM-1·§6 J-3·§7 ASK(침묵 자동게시 Never)·§12-D5 v1.0
 · workflow.md §5·§10 D5 v1.0 · 【AX-I18N】 [F §3.11]
한글 1음절=1자(불이익 없음)·모바일 truncation → 첫 ~20–25 음절 훅. 해시태그
`#쇼츠 #shorts`+토픽(≤15). 텍스트만(픽셀 NEVER).
[GATE:D5] v1.0 currency 2026-05-25 (option 2): 소유자 수동 로컬 렉시콘.
빈 lex = 비-슬랭 중립 폴백(현 동작 동형). lex 채워짐 = 키워드를 해시태그에 어펜드
(15 한도·dedup). 슬랭 자유생성은 여전히 금지(소유자 명시 lex만 신뢰).
"""
from __future__ import annotations

import json
import unicodedata

from ..invariants import encoding
from ..lex import loader as lex_loader
from ..notes import description_loader
from ..spine.contracts import StageContract, StageResult
from ..spine.runstate import RunState

TRACE = {
    "prd": "§9 R-CAP3·§12-D5 v1.0",
    "workflow": "§5·§10 D5 v1.0",
    "ax": ["AX-I18N"],
    "f": ["§3.11"],
    "gate": ["D5", "D16"],
}

# 비-슬랭 중립-친근 존댓말 안전 템플릿(D5 폴백·결정론). 자유 생성 금지.
_TITLE_TMPL = "오늘의 기록 | 사진과 영상으로 만든 쇼츠"
_DESC_TMPL = ("직접 찍은 사진과 영상을 모아 만든 약 {sec}초 세로 영상입니다. "
              "편하게 봐 주세요.")
_BASE_TAGS = ["#쇼츠", "#shorts", "#일상", "#영상기록"]


def resolve_slang(text: str, lex=None) -> str:
    """[GATE:D5] v1.0 currency 2026-05-25 (option 2): owner manual lexicon.

    Returns NFC-normalized text. Slang substitution is not performed — owner
    keywords are injected at the hashtag layer (see draft_metadata), not by
    rewriting user-facing prose. Empty/None lex is the baseline path.
    Free-form slang generation remains forbidden (only owner-declared
    keywords are trusted).
    """
    return unicodedata.normalize("NFC", text)


_MAX_HASHTAGS = 15


def _lex_hashtags(lex) -> list[str]:
    """Owner lex → sorted unique `#`-prefixed hashtags (NFC, deterministic)."""
    tags: list[str] = []
    for kw in sorted(lex):
        kw = unicodedata.normalize("NFC", kw).strip()
        if not kw:
            continue
        tag = kw if kw.startswith("#") else f"#{kw}"
        tags.append(tag)
    return tags


def draft_metadata(rs: RunState) -> dict:
    """결정론 KR 메타초안(모델 0). 첫 ~25 음절 훅·해시태그≤15·텍스트만."""
    assert rs.edl is not None
    sec = int(round(sum(e["out"] - e["in"] for e in rs.edl["timeline"])))
    n = len([a for a in rs.assets if not a.isolated])
    title = encoding.nfc(_TITLE_TMPL)[:90]          # 제목 100자 한도 여유

    # PRD §3.1 v1.1 (option A): inbox/description.txt prose seed.
    # Seed present → user prose + auto info appendix.
    # Seed absent  → neutral KR template fallback (pre-v1.1 behavior).
    seed = description_loader.load_description(rs.inbox)
    if seed is not None:
        description = (f"{seed}\n\n"
                       f"(자동 정보: 약 {max(1, sec)}초·총 {n}개 컷.)")
    else:
        desc = encoding.nfc(_DESC_TMPL.format(sec=max(1, sec)))
        description = f"{desc}\n\n총 {n}개 컷."

    # D5 v1.0 (option 2): owner-managed local lex → hashtag append; empty → no-op.
    lex = lex_loader.load_lex(rs.root)
    base = list(_BASE_TAGS)
    seen: set[str] = set()
    tags: list[str] = []
    for t in base + _lex_hashtags(lex):
        if t in seen:
            continue
        seen.add(t)
        tags.append(t)
        if len(tags) >= _MAX_HASHTAGS:
            break

    meta = {
        "title": title,
        "description": description,
        "hashtags": tags,
        "ai_disclosure": False,   # 증분1=실사 조합·무음(AI 음악/보이스 없음)
        "source": ("template_fallback(model=0, D5 v1.0 option2 owner-lex; "
                   f"lex_size={len(lex)}; "
                   f"description_seed={'owner' if seed is not None else 'fallback'})"),
        "lex_size": len(lex),
        "description_seed_used": seed is not None,
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
