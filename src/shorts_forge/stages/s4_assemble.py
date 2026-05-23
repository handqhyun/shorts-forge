"""S4 ASSEMBLE — 9:16 슬라이드 머티리얼라이즈 + 미묘 Ken Burns + 번인 캡션.

추적: PRD §8 C-OUT/C-THUMB·§7 NEVER(정지샷 무모션 금지·금지전환) · workflow.md §2 S4 [DESIGN]
 · 【AX-MEDIA】 [F §3.1]
[DESIGN] D-FG: 엔트리별 결정론 변환. 정지=Pillow cover-크롭 1080×1920(프레임
채움·레터박스 제거·사전 업스케일) → S6 zoompan 모션(무모션 금지). 캡션: 증분1=ASCII 플레이스홀더 바
(한글 libass keep-all 는 Inc4 — OFL 폰트=카브아웃 #1 자산). 클립=대표 프레임 1장.
"""
from __future__ import annotations

from pathlib import Path

from ..media import ffmpeg_cli
from ..spine import edl as edlmod
from ..spine.contracts import StageContract, StageResult
from ..spine.runstate import RunState

TRACE = {
    "prd": "§8 C-OUT",
    "workflow": "§2 S4",
    "ax": ["AX-MEDIA"],
    "f": ["§3.1"],
    "gate": [],
}

CANVAS = (1080, 1920)
# Ken Burns 미묘 줌(무모션 금지 — PRD §7 NEVER). 결정론·가역(D-FG).
KENBURNS = {"type": "kenburns", "zoom_from": 1.0, "zoom_to": 1.08,
            "upscaled": True}


def _asset_by_hash(rs: RunState, h: str):
    for a in rs.assets:
        if a.content_hash == h:
            return a
    return None


def _extract_clip_frame(rs: RunState, src: str, dst: Path) -> None:
    # 클립 대표 프레임 1장(t=0, 결정론). 트랜스코드는 Inc4.
    ffmpeg_cli.run(["-i", src, "-frames:v", "1", "-f", "image2", str(dst)])


def _make_slide(src_png: str, dst: Path, idx: int, hero: bool) -> None:
    """cover-크롭 1080×1920(프레임 채움) + ASCII 플레이스홀더 캡션 바.

    랜드스케이프/혼합방향 원본을 9:16에 *채워* 풀블리드 훅 보장(레터박스 제거 —
    PRD C-THUMB 첫프레임 강프레임·S7 G2 '비풀레터박스'). 사전 업스케일 허용
    (D-FG: zoompan 지터 방지). 결정론(중앙 크롭·동일 입력→동일 산출).
    """
    from PIL import Image, ImageDraw, ImageFont

    cw, ch = CANVAS
    with Image.open(src_png) as im:
        im = im.convert("RGB")
        iw, ih = im.size
        scale = max(cw / iw, ch / ih)            # COVER: 9:16 채움(min→max)
        nw, nh = max(cw, round(iw * scale)), max(ch, round(ih * scale))
        im = im.resize((nw, nh), Image.LANCZOS)
        left, top = (nw - cw) // 2, (nh - ch) // 2
        canvas = im.crop((left, top, left + cw, top + ch))   # 중앙 크롭→정확히 캔버스

    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.load_default(size=44)
    except TypeError:
        font = ImageFont.load_default()
    # 타이틀-세이프 하단 바 + 대비(증분1 ASCII 플레이스홀더 — 한글=Inc4 libass)
    bar_h = 150
    draw.rectangle([0, ch - bar_h, cw, ch], fill=(0, 0, 0))
    label = "shorts-forge" + ("  [HERO]" if hero else f"  #{idx}")
    draw.text((48, ch - bar_h + 48), label, fill=(255, 255, 255), font=font)
    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst, format="PNG")


class S4Assemble(StageContract):
    stage_id = "S4"
    TRACE = TRACE

    def run(self, rs: RunState) -> StageResult:
        assert rs.edl is not None
        sd = rs.stage_dir("S4")
        made = 0
        for e in rs.edl["timeline"]:
            a = _asset_by_hash(rs, e["source_ref"])
            if a is None or not a.work_path:
                return StageResult(False, self.stage_id,
                                   detail=f"엔트리 자산 미해석: {e['source_ref'][:8]}")
            slide = sd / f"slide_{e['idx']:03d}.png"
            if a.kind == "clip":
                frame = sd / f"clipframe_{e['idx']:03d}.png"
                _extract_clip_frame(rs, a.work_path, frame)
                _make_slide(str(frame), slide, e["idx"],
                            hero=(e["idx"] == 0))
            else:
                _make_slide(a.work_path, slide, e["idx"], hero=(e["idx"] == 0))
            e["motion"] = dict(KENBURNS)
            e["slide_src"] = str(slide)
            e["caption_tokens"] = [{"text": "shorts-forge",
                                    "t_in": 0.0, "t_out": e["out"]}]
            made += 1

        edlmod.validate(rs.edl)   # C-OUT/C-LEN/C-THUMB/G6 결정론 검증(R-CAP2)
        edl_path = edlmod.dump(rs.edl, sd / "edl.json")   # 결정론 영속(추적·재현)
        rs.artifacts["S4"] = str(sd)
        return StageResult(ok=True, stage_id=self.stage_id,
                           artifact_ref=str(edl_path),
                           detail=f"슬라이드 {made}장 (9:16·Ken Burns·캡션 바)")
