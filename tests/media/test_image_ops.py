"""A-2 pipeline integration — perceptual hash + near-duplicate dedup, the
deterministic core behind S2 ingest dedup. The over-isolation bug C1
([[project-impl-reinspection]]) lives in the THRESHOLD applied to these, so the
deterministic/monotonic properties are pinned here directly.

Reference: PRD §7 · workflow.md §4 · [F §3.10] · ANCHOR (1) no sampling.
"""
from __future__ import annotations

from PIL import Image

from shorts_forge.media import image_ops as IO


def _img(path, color, size=(64, 64)):
    Image.new("RGB", size, color).save(path)
    return path


def test_phash_deterministic(tmp_path):
    p = _img(tmp_path / "a.png", (10, 120, 200))
    assert IO.phash(p) == IO.phash(p)        # byte-stable across calls


def test_phash_spans_color_channels(tmp_path):
    # C1 fix: the 192-bit RGB-concatenated hash occupies bits above the low 64
    # (luma-only fit in 64), so per-channel colour structure contributes.
    from PIL import ImageDraw

    im = Image.new("RGB", (64, 64), (250, 250, 250))
    ImageDraw.Draw(im).rectangle([0, 0, 31, 63], fill=(220, 20, 20))  # left half
    p = tmp_path / "split.png"
    im.save(p)
    assert IO.phash(p).bit_length() > 64


def test_hamming_counts_differing_bits():
    assert IO.hamming(0b1010, 0b0000) == 2
    assert IO.hamming(0b1111, 0b0000) == 4
    assert IO.hamming(123, 123) == 0


def test_near_duplicate_threshold_boundary():
    base = 0
    six = (1 << 6) - 1          # exactly 6 bits set -> hamming 6
    seven = (1 << 7) - 1        # 7 bits set -> hamming 7
    assert IO.is_near_duplicate(base, base) is True
    assert IO.is_near_duplicate(base, six) is True       # <= 6 (default)
    assert IO.is_near_duplicate(base, seven) is False    # > 6


def test_identical_image_is_near_duplicate(tmp_path):
    a = _img(tmp_path / "x.png", (200, 30, 30))
    b = _img(tmp_path / "y.png", (200, 30, 30))
    assert IO.is_near_duplicate(IO.phash(a), IO.phash(b)) is True
