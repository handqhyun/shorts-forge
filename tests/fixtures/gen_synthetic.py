"""합성 입력 생성 — 개인 미디어 절대 미사용(PRD §7 NEVER, [F §3.12]).

추적: PRD §7 NEVER·§4 C-INPUT/C-I18N · workflow.md §2 S1 · [F §3.10/§3.11/§3.12]
회전-EXIF·NFD 한글명·0바이트·디코드불가·근중복·파노·스크린샷명 등 S1 정규화
경계를 결정론적으로 망라. 모두 절차 생성(저작권·프라이버시 무관).
"""
from __future__ import annotations

import datetime as _dt
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw


def _structured(idx: int, size=(1200, 800)) -> Image.Image:
    """idx 별로 pHash 가 충분히 다른 구조 이미지(근중복 오탐 방지)."""
    w, h = size
    hue = (idx * 37) % 360
    r = (hue * 7) % 256
    g = (hue * 13) % 256
    b = (hue * 19) % 256
    im = Image.new("RGB", size, (r, g, b))
    d = ImageDraw.Draw(im)
    # idx 의존 위치/모양 → 저주파 DCT 분포 상이
    d.rectangle([50 + idx * 9 % 400, 40, 50 + idx * 9 % 400 + 300, 360],
                fill=((r + 90) % 256, (g + 60) % 256, (b + 120) % 256))
    d.ellipse([300, 250 + idx * 7 % 300, 760, 700],
              fill=((b + 40) % 256, (r + 80) % 256, (g + 20) % 256))
    d.text((60, 60), f"SF-{idx:02d}", fill=(255, 255, 255))
    return im


def _exif_with(dt: _dt.datetime, orientation: int | None = None) -> Image.Exif:
    ex = Image.Exif()
    ex[36867] = dt.strftime("%Y:%m:%d %H:%M:%S")   # DateTimeOriginal
    if orientation is not None:
        ex[274] = orientation                       # Orientation
    return ex


def make_inbox(root: str | Path, n_good: int = 14) -> Path:
    """합성 inbox 생성. 반환=inbox 경로. 결정론(동일 인자→동일 산출)."""
    inbox = Path(root)
    inbox.mkdir(parents=True, exist_ok=True)
    base = _dt.datetime(2026, 5, 1, 9, 0, 0)

    for i in range(n_good):
        im = _structured(i)
        dt = base + _dt.timedelta(minutes=i * 3)
        orient = 6 if i == 2 else (8 if i == 5 else None)  # 회전 EXIF 2건
        im.save(inbox / f"IMG_{i:04d}.jpg", format="JPEG",
                exif=_exif_with(dt, orient), quality=92)

    # NFD 분해 한글 파일명(유효 이미지 — S1 NFC 정규화로 보존돼야 함)
    nfd_name = unicodedata.normalize("NFD", "여행사진.jpg")
    _structured(101).save(inbox / nfd_name, format="JPEG",
                          exif=_exif_with(base + _dt.timedelta(minutes=60)),
                          quality=92)

    # 근중복(IMG_0000 의 1px 변형) → 격리 기대
    dup = _structured(0)
    dup.putpixel((0, 0), (1, 2, 3))
    dup.save(inbox / "IMG_DUP.jpg", format="JPEG",
             exif=_exif_with(base + _dt.timedelta(minutes=2)), quality=92)

    # 파노라마 종횡비 → 격리 기대
    Image.new("RGB", (3000, 800), (20, 120, 200)).save(
        inbox / "PANO_0001.jpg", format="JPEG", quality=85)

    # 스크린샷 파일명 프록시 → 격리 기대(잠정 [F §3.10])
    _structured(77).save(inbox / "Screenshot_2026-05-01.png", format="PNG")

    # 0바이트 → 격리 기대
    (inbox / "broken.jpg").write_bytes(b"")

    # 디코드 불가(가짜 heic) → 격리 기대(가용 디코더 없음·[GATE:D9] 조달 안 함)
    (inbox / "weird.heic").write_bytes(b"\x00\x01\x02not-an-image\xff" * 8)

    return inbox


if __name__ == "__main__":
    import sys

    print(make_inbox(sys.argv[1] if len(sys.argv) > 1 else "./_synthetic_inbox"))
