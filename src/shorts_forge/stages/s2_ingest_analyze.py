"""S2 INGEST/ANALYZE — 고전 CV 결정론 특징(SM-1 바닥, 모델 0).

추적: PRD §9 R-CAP4(자산별 대형 VLM 금지)·§7 NEVER(픽셀 불출)·§2 SM-1
 · workflow.md §2 S2 · 【AX-INTEL】【AX-CRAFT】 [F §3.3/§3.9]
증분 1 = 고전 CV만(선명도/밝기). 소형 비전 캡션은 옵트인·기본 OFF(미구현).
픽셀은 어떤 모드에서도 외부 불출 — 본 단계는 로컬 결정론 특징만 산출.
"""
from __future__ import annotations

from ..spine.contracts import StageContract, StageResult
from ..spine.runstate import RunState

TRACE = {
    "prd": "§9 R-CAP4",
    "workflow": "§2 S2",
    "ax": ["AX-INTEL", "AX-CRAFT"],
    "f": ["§3.3", "§3.9"],
    "gate": [],
}


def _features(png_path: str) -> dict:
    """결정론 고전 특징: 밝기 평균 + 선명도 프록시(인접차 분산). numpy 비의존."""
    from PIL import Image

    with Image.open(png_path) as im:
        g = im.convert("L").resize((64, 64), Image.BILINEAR)
        px = list(g.getdata())
    n = len(px)
    mean = sum(px) / n
    # 선명도 프록시: 수평 인접 절대차 평균(고전 Laplacian 대체·결정론)
    diffs = [abs(px[i] - px[i - 1]) for i in range(1, n) if i % 64 != 0]
    sharp = sum(diffs) / max(1, len(diffs))
    return {"brightness": round(mean, 4), "sharpness": round(sharp, 4)}


class S2IngestAnalyze(StageContract):
    stage_id = "S2"
    TRACE = TRACE

    def run(self, rs: RunState) -> StageResult:
        analyzed = 0
        for a in rs.assets:
            if a.kind == "still" and a.work_path:
                try:
                    a.quality.update(_features(a.work_path))
                    analyzed += 1
                except Exception:  # noqa: BLE001 — 특징 실패는 SM-1 비차단
                    a.quality.setdefault("brightness", 0.0)
                    a.quality.setdefault("sharpness", 0.0)
            else:
                a.quality.setdefault("brightness", 0.0)
                a.quality.setdefault("sharpness", 0.0)
        return StageResult(
            ok=True, stage_id=self.stage_id,
            detail=f"고전 CV 특징 {analyzed}/{len(rs.assets)}건(모델 0)",
        )
