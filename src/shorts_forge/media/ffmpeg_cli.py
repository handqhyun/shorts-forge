"""ffmpeg CLI 어댑터 — 결정론 인코드(x264 CPU 베이스라인). NVENC/CUDA 절대 금지.

추적: PRD §4 C-OUT/C-HW/C-LEN/C-LIC·§7 NEVER · workflow.md §2 S6·§0 #7 · [F §3.7/§3.1]
[DESIGN] D-ENC: x264 `veryfast` CRF~20 상시 베이스라인(예측가능·드라이버 취약성 0).
h264_qsv=옵트인만, v1 자동선택 금지. **NVENC/CUDA = INVARIANT #1 위반정의(C-HW)** →
명령 빌더가 구조적으로 차단. 바이너리 경로 해석은 어댑터가 추상화(가역):
  ① 환경 SHORTS_FORGE_FFMPEG  ② PATH  ③ imageio-ffmpeg 번들(개발용)
제품 런타임은 자체 LGPL ffmpeg 번들(설치기 소관, LAYOUT.md).
"""
from __future__ import annotations

import os
import shutil
import subprocess

from ..invariants import encoding, resource_guard

TRACE = {
    "prd": "§4 C-OUT",
    "workflow": "§2 S6",
    "ax": ["AX-HW", "AX-MEDIA"],
    "f": ["§3.7", "§3.1"],
    "gate": [],
}

# INVARIANT #1 위반정의(C-HW): 하드웨어 초과 가정. 명령에 등장 시 차단.
_FORBIDDEN_TOKENS = ("nvenc", "h264_nvenc", "hevc_nvenc", "cuda", "cuvid",
                      "-hwaccel cuda", "scale_npp", "cuda_npp")


class FFmpegUnavailable(RuntimeError):
    """ffmpeg 바이너리 미해석 — 제품은 설치기가 번들 보장(카브아웃 #1)."""


class HardwareInvariantViolation(RuntimeError):
    """NVENC/CUDA 토큰 = INVARIANT #1 위반정의(C-HW). 채택 불가."""


def resolve_ffmpeg() -> str:
    """① env ② PATH ③ imageio-ffmpeg 번들(개발). 미해석 시 예외."""
    env = os.environ.get("SHORTS_FORGE_FFMPEG")
    if env and os.path.isfile(env):
        return env
    on_path = shutil.which("ffmpeg")
    if on_path:
        return on_path
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # noqa: BLE001
        raise FFmpegUnavailable(
            "ffmpeg 미해석(env/PATH/imageio-ffmpeg). 제품은 설치기 번들 보장."
        ) from exc


def _assert_no_forbidden(args: list[str]) -> None:
    joined = " ".join(args).lower()
    for tok in _FORBIDDEN_TOKENS:
        if tok in joined:
            raise HardwareInvariantViolation(
                f"금지 토큰 {tok!r}(NVENC/CUDA). C-HW·INVARIANT #1 위반정의. "
                f"CPU 경로(x264)만 허용."
            )


def run(args: list[str], *, timeout: int = 600) -> subprocess.CompletedProcess:
    """ffmpeg 실행 — list-args(NFC)·금지 토큰 차단·encode heavy-section 강제."""
    _assert_no_forbidden(args)
    cmd = [resolve_ffmpeg(), "-hide_banner", "-nostdin", "-y",
           *[encoding.nfc(a) for a in args]]
    with resource_guard.heavy_section("encode"):
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=True
        )


def x264_baseline_args() -> list[str]:
    """[DESIGN] D-ENC 베이스라인: MP4/H.264 High/AAC-LC/30fps/CRF20 (C-OUT)."""
    return [
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart",
    ]
