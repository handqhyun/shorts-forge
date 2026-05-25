"""A-2 residual — direct per-stage verification for S2/S3/S4/S5/S6, previously
covered only transitively by full E2E. Each test drives the real prior stages
on a shared RunState, then asserts that stage's output contract (ANCHOR (1):
no sampling — every spine stage gets a direct check).

Reference: PRD §2 SM-1/§4/§8 · workflow.md §2 S2-S6 · [GATE:D2/D5].
"""
from __future__ import annotations

from pathlib import Path

import pytest

from shorts_forge.spine import edl as edlmod
from shorts_forge.spine.gates import GateBlocked
from shorts_forge.spine.runstate import new_run
from shorts_forge.stages.s1_normalize import S1Normalize
from shorts_forge.stages.s2_ingest_analyze import S2IngestAnalyze, _features
from shorts_forge.stages.s3_select_order import S3SelectOrder, energy_arc_reorder
from shorts_forge.stages.s4_assemble import S4Assemble
from shorts_forge.stages.s5_audio import S5Audio
from shorts_forge.stages.s6_render import S6Render


def _drive(rs, stages):
    for st in stages:
        res = st.run(rs)
        st.validate_output(rs, res)
        assert res.ok, (st.stage_id, res.detail)
    return rs


def _rs(inbox, root):
    return new_run(root, inbox, code_version="test", seed=1)


def test_s2_classic_features_deterministic(synthetic_inbox, ascii_root):
    rs = _rs(synthetic_inbox, ascii_root)
    _drive(rs, [S1Normalize(), S2IngestAnalyze()])
    stills = [a for a in rs.assets if a.kind == "still"]
    assert stills
    for a in stills:
        assert "brightness" in a.quality and "sharpness" in a.quality
        assert isinstance(a.quality["sharpness"], (int, float))
    assert _features(stills[0].work_path) == _features(stills[0].work_path)


def test_s3_hero_first_chronological_edl(synthetic_inbox, ascii_root):
    rs = _rs(synthetic_inbox, ascii_root)
    _drive(rs, [S1Normalize(), S2IngestAnalyze(), S3SelectOrder()])
    edl = rs.edl
    assert edl is not None
    assert edl["spine_kind"] == "chronological"          # D5 provisional
    assert edl["hero_ref"] == edl["timeline"][0]["source_ref"]   # C-THUMB
    n = len(edl["timeline"])
    assert 1 <= n <= edlmod.TARGET_FPS * 2               # within shot band
    assert edlmod.total_seconds(edl) <= edlmod.MAX_SECONDS
    for e in edl["timeline"]:
        assert e["transition_in"] == "cut"               # Inc1 clean cut only
        assert e["motion"]["type"] == "pending"          # S4 fills Ken Burns


def test_s3_energy_arc_reorder_empty_lex_preserves_order():
    # D5 v1.0 (option 2): owner manual lexicon. Empty/None lex → identity
    # (chronological order preserved). Topic-driven re-order is [DESIGN] 잔존.
    items = [("a", 1), ("b", 2), ("c", 3)]
    assert energy_arc_reorder(items) == items
    assert energy_arc_reorder(items, lex=None) == items
    assert energy_arc_reorder(items, lex=frozenset()) == items


def test_s3_energy_arc_reorder_with_lex_currently_identity():
    items = [1, 2, 3]
    assert energy_arc_reorder(items, lex=frozenset({"운동"})) == [1, 2, 3]


def test_s4_slides_materialized_vertical(synthetic_inbox, ascii_root):
    rs = _rs(synthetic_inbox, ascii_root)
    _drive(rs, [S1Normalize(), S2IngestAnalyze(), S3SelectOrder(), S4Assemble()])
    from PIL import Image
    for e in rs.edl["timeline"]:
        assert e["motion"]["type"] == "kenburns"         # no-motion forbidden
        assert e["slide_src"]
        with Image.open(e["slide_src"]) as im:
            assert im.size == (1080, 1920)               # C-OUT cover-crop
        assert e["caption_tokens"]
    assert (Path(rs.artifacts["S4"]) / "edl.json").exists()


def test_s5_silent_when_no_owner_music(synthetic_inbox, ascii_root):
    # D2 v1.2 (option 2): empty <sf_root>/music/ → silent_inc1 fallback,
    # identical to pre-v1.2 behavior (graceful degradation).
    rs = _rs(synthetic_inbox, ascii_root)
    _drive(rs, [S1Normalize(), S2IngestAnalyze(), S3SelectOrder(),
                S4Assemble(), S5Audio()])
    assert rs.edl["audio"]["track_ref"] is None
    assert rs.edl["audio"]["mode"] == "silent_inc1"


def test_s6_renders_nonblack_vertical_short(synthetic_inbox, ascii_root):
    rs = _rs(synthetic_inbox, ascii_root)
    _drive(rs, [S1Normalize(), S2IngestAnalyze(), S3SelectOrder(),
                S4Assemble(), S5Audio(), S6Render()])
    out = rs.output_path
    assert out and out.endswith("render.mp4")
    from shorts_forge.stages.s7_validate import _media_info, _first_frame_nonblack
    mi = _media_info(out)
    assert (mi["width"], mi["height"]) == (1080, 1920)
    assert _first_frame_nonblack(rs, out)                # G2/C3 hook: not black
