"""S3 SELECT/ORDER — 결정론 휴리스틱(연대순 척추 + 히어로 앵커).

추적: PRD §8 C-THUMB·§7·§8 D-차원 입력상대 · workflow.md §2 S3 · 【AX-CRAFT】【AX-INPUT】 [F §3.9/§3.10]
[GATE:D5] v1.0 currency 2026-05-25 (option 2): 소유자 수동 로컬 렉시콘.
빈 lex = 연대순 폴백 (현 동작 동형). lex 채워짐 = 추후 [DESIGN] 재배열 확장.
선별=품질·중복·입력바닥 규칙(고전, 모델 0). 첫 프레임=가용 최강(연대순-첫 아님,
C-THUMB). 샷수 대역·페이스 적용. 수치 문턱은 [GATE:D1] 잠정.
"""
from __future__ import annotations

from ..spine import edl as edlmod
from ..spine.contracts import StageContract, StageResult
from ..spine.runstate import RunState

TRACE = {
    "prd": "§8 C-THUMB·§12-D5 v1.0",
    "workflow": "§2 S3·§10 D5 v1.0",
    "ax": ["AX-CRAFT", "AX-INPUT"],
    "f": ["§3.9", "§3.10"],
    "gate": ["D5", "D1"],
}

# 파생 샷수 대역(~12–50, 40–59초) [F §3.9]. 하한은 [GATE:D1] 잠정(상수 채택 금지).
SHOT_BAND_MAX = 50
PROVISIONAL_D1_SHOT_BAND_MIN = 1   # 잠정(Fowler ratchet) — Phase-0 골든 보정 전 미정의
PER_SHOT_MIN_S, PER_SHOT_MAX_S = 1.0, 4.0   # ~2–4초/컷, 정지 >5초 금지
TARGET_TOTAL_S = 55.0


def energy_arc_reorder(assets, lex=None):
    """[GATE:D5] v1.0 currency 2026-05-25 (option 2): owner manual lexicon.

    Empty / None lex → identity (preserve chronological order — current
    baseline behavior). Non-empty lex → identity for now; topic-driven
    re-order is `[DESIGN]` 잔존 (PRD §12-D5 v1.0). Asset-side keyword meta
    is not yet wired through S2 — schema extension is a separate turn.
    """
    return list(assets)


class S3SelectOrder(StageContract):
    stage_id = "S3"
    TRACE = TRACE

    def run(self, rs: RunState) -> StageResult:
        usable = [a for a in rs.assets if not a.isolated]
        if not usable:
            return StageResult(False, self.stage_id,
                               detail="유효 자산 0 — SM-1 바닥 불성립(빈 실효 입력)")

        # 선별: 샷수 상한 적용(연대순 유지 — D5 잠정). 결정론.
        selected = usable[:SHOT_BAND_MAX]

        # 히어로 = 가용 최강(선명도 최대), 입력상대. C-THUMB: 첫 프레임=훅.
        hero = max(selected, key=lambda a: (a.quality.get("sharpness", 0.0),
                                            -a.confidence_tier, a.content_hash))
        ordered = [hero] + [a for a in selected if a is not hero]

        n = len(ordered)
        per = max(PER_SHOT_MIN_S, min(PER_SHOT_MAX_S, TARGET_TOTAL_S / n))
        # C-LEN 보호: 총합 ≤59s
        if n * per > edlmod.MAX_SECONDS:
            per = max(PER_SHOT_MIN_S, edlmod.MAX_SECONDS / n - 0.01)

        edl = edlmod.new_edl(rs.run_id, rs.seed)
        edl["spine_kind"] = "chronological"   # D5 잠정
        edl["hero_ref"] = hero.content_hash
        for a in ordered:
            edlmod.add_entry(
                edl, source_ref=a.content_hash, kind=a.kind,
                t_in=0.0, t_out=round(per, 3),
                transform_916={"mode": "cover_crop", "target": [1080, 1920]},
                motion={"type": "pending"},   # S4가 Ken Burns 채움
                transition_in="cut",
                caption_tokens=[],
            )
        rs.edl = edl
        return StageResult(
            ok=True, stage_id=self.stage_id,
            detail=f"선별 {n}/{len(usable)}, 히어로={hero.content_hash[:8]}, "
                   f"샷당 {per:.2f}s (연대순·D5 잠정)",
        )

    def validate_output(self, rs: RunState, result: StageResult) -> None:
        super().validate_output(rs, result)
        assert rs.edl is not None
        if rs.edl["hero_ref"] != rs.edl["timeline"][0]["source_ref"]:
            raise RuntimeError("C-THUMB 위반: 히어로가 첫 엔트리 아님")
        n = len(rs.edl["timeline"])
        if not (PROVISIONAL_D1_SHOT_BAND_MIN <= n <= SHOT_BAND_MAX):
            raise RuntimeError(f"G5 샷수 대역 벗어남: {n}")
