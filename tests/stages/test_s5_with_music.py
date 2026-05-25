"""S5 with owner music — PRD §12-D2/D14 v1.2 (option 2 owner manual music folder).

Reference: PRD §12-D2/D14 v1.2 currency · workflow.md §10 D2/D14 v1.2 ·
src/shorts_forge/stages/s5_audio.py.
"""
from __future__ import annotations

from types import SimpleNamespace

from shorts_forge.music import loader as ML
from shorts_forge.stages import s5_audio as S5


def _rs(root, seed=1):
    edl = {"audio": {}}
    return SimpleNamespace(root=root, seed=seed, edl=edl)


def _put_music(root, *names):
    d = root / ML.MUSIC_DIRNAME
    d.mkdir(parents=True, exist_ok=True)
    for n in names:
        (d / n).write_bytes(b"fake_audio_bytes")


def test_empty_music_folder_silent_fallback(tmp_path):
    rs = _rs(tmp_path)
    res = S5.S5Audio().run(rs)
    assert res.ok
    assert rs.edl["audio"]["track_ref"] is None
    assert rs.edl["audio"]["mode"] == "silent_inc1"
    assert any(ev[0] == "D2" and ev[1] == "fallback"
               for ev in res.gate_events)


def test_owner_track_picked_when_present(tmp_path):
    _put_music(tmp_path, "track.mp3")
    rs = _rs(tmp_path)
    res = S5.S5Audio().run(rs)
    assert res.ok
    assert rs.edl["audio"]["track_ref"].endswith("track.mp3")
    assert rs.edl["audio"]["mode"] == "owner_track"
    assert "license=owner_responsibility" in rs.edl["audio"]["source"]


def test_owner_pick_deterministic_same_seed(tmp_path):
    _put_music(tmp_path, "a.mp3", "b.mp3", "c.mp3", "d.mp3")
    rs1 = _rs(tmp_path, seed=7)
    rs2 = _rs(tmp_path, seed=7)
    S5.S5Audio().run(rs1)
    S5.S5Audio().run(rs2)
    assert rs1.edl["audio"]["track_ref"] == rs2.edl["audio"]["track_ref"]


def test_contentid_placeholder_always_present(tmp_path):
    rs = _rs(tmp_path)
    S5.S5Audio().run(rs)
    cid = rs.edl["audio"]["contentid"]
    assert cid["gate"] == "D8"
    assert cid["status"] == "placeholder"


def test_load_library_with_root_returns_tracks(tmp_path):
    _put_music(tmp_path, "x.mp3", "y.wav")
    assert len(S5.load_library(tmp_path)) == 2


def test_load_library_no_root_returns_empty():
    assert S5.load_library() == []


def test_owner_track_d14_event_emitted(tmp_path):
    _put_music(tmp_path, "song.mp3")
    rs = _rs(tmp_path)
    res = S5.S5Audio().run(rs)
    d14_events = [ev for ev in res.gate_events if ev[0] == "D14"]
    assert d14_events
    assert "소유자 선택" in d14_events[0][2]


def test_only_audio_extensions_picked_up_via_s5(tmp_path):
    # README.txt next to music files must not be picked as a track.
    _put_music(tmp_path, "song.mp3")
    (tmp_path / ML.MUSIC_DIRNAME / "README.txt").write_text(
        "license: CC0", encoding="utf-8"
    )
    rs = _rs(tmp_path)
    S5.S5Audio().run(rs)
    assert rs.edl["audio"]["track_ref"].endswith("song.mp3")
