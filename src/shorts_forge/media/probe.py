"""probe-first 분류 — still/clip allow-list·디코드 가능성·EXIF 신뢰도 신호.

추적: PRD §4 C-INPUT/C-SPINE · workflow.md §2 S1/S7 · [F §3.10]
【AX-INPUT】 디코드 불가/exotic(ProRAW·MV-HEVC) → 스킵+로그(파일별 격리, 배치
비중단). HEIC/HDR 실디코드는 환경 probe된 디코더에만 의존([GATE:D9] 조달 결정은
차단 — 우리는 *조달*하지 않고 *가용*만 사용).
"""
from __future__ import annotations

import datetime as _dt
import os
import subprocess
from pathlib import Path

TRACE = {
    "prd": "§4 C-INPUT",
    "workflow": "§2 S1",
    "ax": ["AX-INPUT"],
    "f": ["§3.10"],
    "gate": ["D9"],
}

STILL_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff",
             ".heic", ".heif"}
CLIP_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}

# EXIF 태그(Pillow 정수 키)
_ORIENTATION, _DATETIME_ORIG = 274, 36867


def probe(path: str | Path) -> dict:
    """파일 1건 분류. 반환 dict: kind/width/height/orientation/exif_dt/decodable/reason."""
    p = Path(path)
    ext = p.suffix.lower()
    info = {"kind": "unknown", "width": 0, "height": 0, "orientation": 1,
            "exif_dt": None, "decodable": False, "reason": ""}

    if not p.exists() or p.stat().st_size == 0:
        info["reason"] = "0바이트 또는 부재"
        return info

    if ext in STILL_EXT:
        info["kind"] = "still"
        try:
            from PIL import Image, ExifTags  # noqa: F401

            with Image.open(p) as im:
                im.verify()
            with Image.open(p) as im:
                info["width"], info["height"] = im.size
                exif = getattr(im, "getexif", lambda: {})()
                if exif:
                    info["orientation"] = int(exif.get(_ORIENTATION, 1) or 1)
                    raw_dt = exif.get(_DATETIME_ORIG)
                    if raw_dt:
                        info["exif_dt"] = _parse_exif_dt(str(raw_dt))
            info["decodable"] = True
        except Exception as exc:  # noqa: BLE001 — 디코드 불가 → 격리(비중단)
            info["reason"] = f"디코드 불가: {type(exc).__name__}"
        return info

    if ext in CLIP_EXT:
        info["kind"] = "clip"
        info.update(_probe_clip(p))
        return info

    info["reason"] = f"allow-list 외 확장자: {ext}"
    return info


def _parse_exif_dt(raw: str) -> float | None:
    # EXIF 표준: "YYYY:MM:DD HH:MM:SS" (타임존 무시 = best-effort, C-SPINE)
    try:
        return _dt.datetime.strptime(
            raw.strip(), "%Y:%m:%d %H:%M:%S"
        ).timestamp()
    except (ValueError, OSError):
        return None


def _probe_clip(p: Path) -> dict:
    """ffmpeg -i stderr 파싱(imageio-ffmpeg 번들엔 ffprobe 없음)."""
    from . import ffmpeg_cli

    out = {"decodable": False, "width": 0, "height": 0, "reason": ""}
    try:
        proc = subprocess.run(
            [ffmpeg_cli.resolve_ffmpeg(), "-hide_banner", "-i", str(p)],
            capture_output=True, text=True, timeout=60,
        )
        err = proc.stderr or ""
        if "Video:" in err:
            out["decodable"] = True
            for tok in err.split("Video:")[1].split(","):
                tok = tok.strip()
                if "x" in tok and tok.split("x")[0].strip().isdigit():
                    w, _, rest = tok.partition("x")
                    h = "".join(ch for ch in rest if ch.isdigit())
                    if h:
                        out["width"], out["height"] = int(w), int(h)
                        break
        else:
            out["reason"] = "비디오 스트림 없음"
    except (subprocess.SubprocessError, OSError) as exc:
        out["reason"] = f"probe 실패: {type(exc).__name__}"
    return out


def confidence_tier(p: Path, exif_dt: float | None) -> tuple[int, float | None]:
    """C-SPINE 5단계 신뢰도 태깅: 1=EXIF 2=컨테이너 3=파일명 4=mtime 5=unknown.

    카메라 원본만 신뢰. 스크린샷/전달본/복사 오염 → 하위 티어.
    """
    if exif_dt is not None:
        return 1, exif_dt
    name_dt = _datetime_from_name(p.name)
    if name_dt is not None:
        return 3, name_dt
    try:
        return 4, os.path.getmtime(p)
    except OSError:
        return 5, None


def _datetime_from_name(name: str) -> float | None:
    import re

    m = re.search(r"(20\d{2})[-_]?(\d{2})[-_]?(\d{2})[-_]?(\d{2})(\d{2})(\d{2})",
                  name)
    if not m:
        return None
    try:
        return _dt.datetime(*(int(g) for g in m.groups())).timestamp()
    except (ValueError, OSError):
        return None
