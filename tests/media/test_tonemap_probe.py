"""A-2 residual — direct unit coverage of tonemap (D-CS working colorspace /
HDR->SDR filter) and probe (classification + C-SPINE confidence tiers), the
deterministic media helpers previously uncovered directly.

Reference: PRD §4 C-INPUT/C-SPINE · workflow.md §2 S1 [DESIGN] D-CS · [F §3.10].
"""
from __future__ import annotations

import datetime as dt

from PIL import Image

from shorts_forge.media import probe as P
from shorts_forge.media import tonemap as T


# ---- tonemap (pure) ---------------------------------------------------------

def test_tonemap_none_for_sdr():
    assert T.video_tonemap_filter(False) is None


def test_tonemap_hlg_uses_hlg_peak():
    f = T.video_tonemap_filter(True, hlg=True)
    assert f and f"npl={T.HLG_NOMINAL_PEAK_LUM}" in f
    assert "tonemap=hable" in f and "format=yuv420p" in f


def test_tonemap_dovi_uses_dovi_peak():
    f = T.video_tonemap_filter(True, hlg=False)
    assert f and f"npl={T.DOVI_NOMINAL_PEAK_LUM}" in f


def test_working_colorspace_is_bt709_8bit_limited():
    cs = T.working_colorspace()
    assert cs == {"primaries": "bt709", "transfer": "bt709",
                  "range": "limited", "depth": 8}


# ---- probe (classification + tiers) -----------------------------------------

def test_probe_zero_byte_not_decodable(tmp_path):
    f = tmp_path / "empty.jpg"
    f.write_bytes(b"")
    info = P.probe(f)
    assert info["decodable"] is False
    assert "0바이트 또는 부재" in info["reason"]


def test_probe_valid_still(tmp_path):
    f = tmp_path / "ok.png"
    Image.new("RGB", (640, 480), (10, 20, 30)).save(f)
    info = P.probe(f)
    assert info["kind"] == "still" and info["decodable"] is True
    assert (info["width"], info["height"]) == (640, 480)


def test_probe_undecodable_garbage(tmp_path):
    f = tmp_path / "weird.heic"
    f.write_bytes(b"\x00\x01not-an-image\xff" * 8)
    info = P.probe(f)
    assert info["decodable"] is False


def test_probe_extension_not_in_allowlist(tmp_path):
    f = tmp_path / "note.txt"
    f.write_text("hello")
    info = P.probe(f)
    assert info["decodable"] is False
    assert "allow-list" in info["reason"]


def test_confidence_tier_exif_is_tier_one(tmp_path):
    tier, ts = P.confidence_tier(tmp_path / "IMG_0001.jpg", exif_dt=123456.0)
    assert tier == 1 and ts == 123456.0


def test_confidence_tier_name_date_is_tier_three(tmp_path):
    tier, ts = P.confidence_tier(tmp_path / "IMG_20260501_120000.jpg",
                                 exif_dt=None)
    assert tier == 3
    assert ts == dt.datetime(2026, 5, 1, 12, 0, 0).timestamp()


def test_confidence_tier_mtime_is_tier_four(tmp_path):
    f = tmp_path / "random_name.jpg"
    f.write_bytes(b"x")
    tier, ts = P.confidence_tier(f, exif_dt=None)
    assert tier == 4 and ts is not None


def test_datetime_from_name_returns_none_without_date():
    assert P._datetime_from_name("vacation.jpg") is None
