"""S6 RENDER — 결정론 단일 인코드(x264 CPU). NVENC/CUDA 금지.

추적: PRD §4 C-OUT/C-HW/C-LEN·§7 NEVER · workflow.md §2 S6 [DESIGN] · 【AX-HW】 [F §3.7]
[DESIGN] D-ENC: x264 `veryfast` CRF20 베이스라인(MP4/H.264 High/AAC-LC/30fps).
슬라이드(1080×1920) → zoompan Ken Burns(무모션 금지) → concat → 무음 AAC(anullsrc)
→ 단일 인코드. ffmpeg 어댑터가 NVENC/CUDA 토큰 구조적 차단(C-HW·INVARIANT #1).
주: dev=imageio-ffmpeg(libx264). 제품 배포 인코더 라이선스는 패키징/법적 소관(NOTICE·C-LIC).
"""
from __future__ import annotations

from ..media import ffmpeg_cli
from ..spine import edl as edlmod
from ..spine.contracts import StageContract, StageResult
from ..spine.runstate import RunState

TRACE = {
    "prd": "§4 C-OUT",
    "workflow": "§2 S6",
    "ax": ["AX-HW", "AX-I18N"],
    "f": ["§3.7", "§3.11"],
    "gate": [],
}

FPS = 30


class S6Render(StageContract):
    stage_id = "S6"
    TRACE = TRACE

    def run(self, rs: RunState) -> StageResult:
        assert rs.edl is not None
        tl = rs.edl["timeline"]
        total = round(edlmod.total_seconds(rs.edl), 3)
        out = rs.stage_dir("S6") / "render.mp4"

        if rs.dry_run:
            # 스토리보드만(렌더 없음) — J-3 dry-run
            sb = rs.stage_dir("S6") / "storyboard.txt"
            sb.write_text(
                "\n".join(f"#{e['idx']:03d} {e['kind']} {e['out']}s "
                          f"motion={e['motion']['type']} src={e.get('slide_src','')}"
                          for e in tl) + f"\nTOTAL={total}s\n",
                encoding="utf-8",
            )
            rs.output_path = str(sb)
            return StageResult(ok=True, stage_id=self.stage_id,
                               artifact_ref=str(sb),
                               detail=f"dry-run 스토리보드({len(tl)} 컷, {total}s)")

        args: list[str] = []
        for e in tl:
            args += ["-loop", "1", "-t", f"{e['out']:.3f}",
                     "-i", e["slide_src"]]
        args += ["-f", "lavfi", "-t", f"{total:.3f}",
                 "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]

        # 엔트리별 zoompan(미묘 Ken Burns·결정론) → concat
        fc = []
        for i, e in enumerate(tl):
            frames = max(1, round(e["out"] * FPS))
            zt = float(e["motion"].get("zoom_to", 1.08))
            inc = round((zt - 1.0) / max(1, frames - 1), 6)
            fc.append(
                f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=disable,"
                f"setsar=1,fps={FPS},"
                f"zoompan=z='min(zoom+{inc},{zt})':d={frames}:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"s=1080x1920:fps={FPS}[v{i}]"
            )
        concat_in = "".join(f"[v{i}]" for i in range(len(tl)))
        fc.append(f"{concat_in}concat=n={len(tl)}:v=1:a=0[vout]")
        audio_idx = len(tl)

        args += [
            "-filter_complex", ";".join(fc),
            "-map", "[vout]", "-map", f"{audio_idx}:a",
            "-t", f"{total:.3f}",
            *ffmpeg_cli.x264_baseline_args(),
            str(out),
        ]
        ffmpeg_cli.run(args, timeout=900)
        rs.output_path = str(out)
        rs.artifacts["S6"] = str(out)
        return StageResult(ok=True, stage_id=self.stage_id,
                           artifact_ref=str(out),
                           detail=f"렌더 {len(tl)} 컷 → {total}s mp4 (x264 CPU)")
