"""톤맵 — HDR/P3 → SDR Rec.709 (캡슐화된 [DESIGN] D-CS 결정점, 가역).

추적: PRD §4 C-INPUT · workflow.md §2 S1 [DESIGN] · [F §3.10]
【AX-INPUT】 iPhone 12+ 영상 HDR 기본 → 무시 시 워시아웃/크러시. 정규화서 명시
SDR Rec.709 8-bit 톤맵(HLG npl≈400 / DoVi npl≈100, npl 튜너블). CPU 톤맵 비용 큼.

설계: 본 모듈이 작업 색공간 결정(D-CS)을 캡슐화 → 10-bit 경로/연산자 교체 가역.
정지=Pillow RGB(sRGB 가정, image_ops). 영상=ffmpeg 필터(가용 시), 미가용 시
plain scale 강등(SM-1: 그래도 산출). 실제 HDR 영상 경로는 Inc4 S6에서 확장.
"""
from __future__ import annotations

TRACE = {
    "prd": "§4 C-INPUT",
    "workflow": "§2 S1",
    "ax": ["AX-INPUT"],
    "f": ["§3.10"],
    "gate": [],
}

# npl 튜너블 기본값(가역 — config 주입 가능)
HLG_NOMINAL_PEAK_LUM = 400
DOVI_NOMINAL_PEAK_LUM = 100


def video_tonemap_filter(is_hdr: bool, *, hlg: bool = True) -> str | None:
    """HDR 영상 → SDR Rec.709 ffmpeg 필터(가용 시). 미가용 환경은 None 강등.

    zscale/tonemap 미빌드 ffmpeg 에서는 호출자가 plain scale 로 강등(SM-1).
    """
    if not is_hdr:
        return None
    npl = HLG_NOMINAL_PEAK_LUM if hlg else DOVI_NOMINAL_PEAK_LUM
    return (
        f"zscale=t=linear:npl={npl},tonemap=hable,"
        f"zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
    )


def working_colorspace() -> dict:
    """[DESIGN] D-CS 확정값(가역). 작업표현 = BT.709·8-bit·limited."""
    return {"primaries": "bt709", "transfer": "bt709", "range": "limited",
            "depth": 8}
