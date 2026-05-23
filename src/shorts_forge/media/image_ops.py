"""이미지 연산 — 회전 1회 베이크·정규화 저장·pHash(순수 Python DCT).

추적: PRD §4 C-INPUT · workflow.md §2 S1 · [F §3.10]
【AX-INPUT】 EXIF Orientation Pillow 자동 미적용 → ImageOps.exif_transpose() 필수,
HEIF 이중-회전 함정(transpose 후 Orientation=1). pHash=근중복 디덥(numpy 비의존).
"""
from __future__ import annotations

import math
from pathlib import Path

TRACE = {
    "prd": "§4 C-INPUT",
    "workflow": "§2 S1",
    "ax": ["AX-INPUT"],
    "f": ["§3.10"],
    "gate": [],
}

_HASH_N = 32   # DCT 입력 그리드
_HASH_K = 8    # 저주파 8x8 사용


def bake_rotation_and_normalize(src: str | Path, dst: str | Path) -> Path:
    """EXIF 회전 1회 베이크 + RGB(sRGB 가정)·작업표현 저장(이중회전 금지).

    [DESIGN] D-CS: 작업 색공간 = sRGB/RGB 8-bit(HDR/P3 톤맵은 tonemap.py).
    """
    from PIL import Image, ImageOps

    dst_p = Path(dst)
    dst_p.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)        # 회전 베이크(Orientation 소거)
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        elif im.mode == "L":
            im = im.convert("RGB")
        # 저장 시 EXIF 미동봉 → Orientation=1 효과(이중 회전 방지)
        im.save(dst_p, format="PNG", optimize=False)
    return dst_p


def _dct_1d(vec: list[float]) -> list[float]:
    n = len(vec)
    out = []
    factor = math.pi / (2.0 * n)
    for k in range(n):
        s = 0.0
        for i, v in enumerate(vec):
            s += v * math.cos((2 * i + 1) * k * factor)
        out.append(s)
    return out


def _channel_hash(px: list) -> int:
    """단일 채널 64-bit DCT pHash(저주파 8x8·DC 제외 median 임계)."""
    rows = [px[r * _HASH_N:(r + 1) * _HASH_N] for r in range(_HASH_N)]
    rows = [_dct_1d([float(v) for v in row]) for row in rows]
    cols = [_dct_1d([rows[r][c] for r in range(_HASH_N)])
            for c in range(_HASH_N)]
    coeffs = [cols[c][r] for r in range(_HASH_K) for c in range(_HASH_K)]
    body = coeffs[1:]
    med = sorted(body)[len(body) // 2]
    bits = 0
    for i, c in enumerate(coeffs):
        if c > med:
            bits |= 1 << i
    return bits


def phash(path: str | Path) -> int:
    """192-bit 색상 인지 지각 해시(RGB 3x64 채널 연결·결정론·numpy 비의존).

    luma-only pHash 는 색상만 다른 프레임을 동일 구조로 접어 distinct 콘텐츠를
    근중복 과격리한다(C1). 채널별 64-bit DCT pHash 를 연결하면 근중복 임계(=6)
    의미를 보존하면서 색상 변별을 복원한다 — 1px 변형은 ~0, 색상-distinct 는
    임계를 크게 상회. [F §3.10]
    """
    from PIL import Image

    with Image.open(path) as im:
        im = im.convert("RGB").resize((_HASH_N, _HASH_N), Image.BILINEAR)
        r, g, b = im.split()
    hr = _channel_hash(list(r.getdata()))
    hg = _channel_hash(list(g.getdata()))
    hb = _channel_hash(list(b.getdata()))
    return (hr << 128) | (hg << 64) | hb


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def is_near_duplicate(a: int, b: int, threshold: int = 6) -> bool:
    """pHash 해밍거리 ≤ 임계 → 근중복(인접 노출 금지·디덥)."""
    return hamming(a, b) <= threshold
