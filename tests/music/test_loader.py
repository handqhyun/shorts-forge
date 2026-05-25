"""music loader — PRD §12-D2/D14 v1.2 (option 2 owner manual local music folder).

Reference: PRD §12-D2/D14 v1.2 currency · workflow.md §10 D2/D14 v1.2 ·
src/shorts_forge/music/loader.py.
"""
from __future__ import annotations

import unicodedata

from shorts_forge.music import loader as ML


def _music_dir(root):
    d = root / ML.MUSIC_DIRNAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def _make_track(d, name, content_bytes=b"fake_audio_bytes"):
    p = d / name
    p.write_bytes(content_bytes)
    return p


def test_missing_root_returns_empty(tmp_path):
    assert ML.discover_tracks(tmp_path / "no_root") == []


def test_missing_dir_returns_empty(tmp_path):
    assert ML.discover_tracks(tmp_path) == []


def test_empty_dir_returns_empty(tmp_path):
    _music_dir(tmp_path)
    assert ML.discover_tracks(tmp_path) == []


def test_basic_tracks_discovered_sorted(tmp_path):
    d = _music_dir(tmp_path)
    _make_track(d, "gamma.m4a")
    _make_track(d, "alpha.mp3")
    _make_track(d, "beta.wav")
    names = [p.name for p in ML.discover_tracks(tmp_path)]
    assert names == ["alpha.mp3", "beta.wav", "gamma.m4a"]


def test_non_audio_extensions_ignored(tmp_path):
    d = _music_dir(tmp_path)
    _make_track(d, "song.mp3")
    _make_track(d, "readme.txt")
    _make_track(d, "cover.jpg")
    _make_track(d, "playlist.m3u")
    assert [p.name for p in ML.discover_tracks(tmp_path)] == ["song.mp3"]


def test_case_insensitive_extension(tmp_path):
    d = _music_dir(tmp_path)
    _make_track(d, "SONG.MP3")
    _make_track(d, "Other.Wav")
    assert len(ML.discover_tracks(tmp_path)) == 2


def test_oversize_track_rejected(tmp_path):
    d = _music_dir(tmp_path)
    over = d / "huge.mp3"
    with open(over, "wb") as f:
        f.seek(ML.MAX_TRACK_BYTES + 1)
        f.write(b"\x00")
    _make_track(d, "small.mp3")
    assert [p.name for p in ML.discover_tracks(tmp_path)] == ["small.mp3"]


def test_subdirectories_ignored(tmp_path):
    d = _music_dir(tmp_path)
    (d / "subdir").mkdir()
    _make_track(d, "top.mp3")
    assert [p.name for p in ML.discover_tracks(tmp_path)] == ["top.mp3"]


def test_pick_track_deterministic_same_seed(tmp_path):
    d = _music_dir(tmp_path)
    for name in ["a.mp3", "b.mp3", "c.mp3"]:
        _make_track(d, name)
    tracks = ML.discover_tracks(tmp_path)
    assert ML.pick_track(tracks, seed=42) == ML.pick_track(tracks, seed=42)


def test_pick_track_seed_distribution_covers_multiple(tmp_path):
    d = _music_dir(tmp_path)
    for name in ["a.mp3", "b.mp3", "c.mp3", "d.mp3", "e.mp3"]:
        _make_track(d, name)
    tracks = ML.discover_tracks(tmp_path)
    picks = {ML.pick_track(tracks, seed=s) for s in range(100)}
    assert len(picks) >= 2


def test_pick_track_empty_returns_none():
    assert ML.pick_track([], seed=1) is None


def test_load_for_run_empty_returns_none(tmp_path):
    assert ML.load_for_run(tmp_path, seed=1) is None


def test_load_for_run_picks_one(tmp_path):
    d = _music_dir(tmp_path)
    _make_track(d, "only.mp3")
    p = ML.load_for_run(tmp_path, seed=1)
    assert p is not None
    assert p.name == "only.mp3"


def test_read_only_does_not_modify(tmp_path):
    d = _music_dir(tmp_path)
    _make_track(d, "x.mp3")
    before = sorted(p.name for p in d.iterdir())
    ML.discover_tracks(tmp_path)
    ML.load_for_run(tmp_path, seed=1)
    after = sorted(p.name for p in d.iterdir())
    assert before == after


def test_nfc_name_normalized_for_sort(tmp_path):
    d = _music_dir(tmp_path)
    # NFD-named file should still be discoverable and sorted via NFC name.
    nfd = unicodedata.normalize("NFD", "한국노래.mp3")
    _make_track(d, nfd)
    _make_track(d, "alpha.mp3")
    tracks = ML.discover_tracks(tmp_path)
    assert len(tracks) == 2
