"""A-2 pipeline integration — the single LLM meta node (Inc1 demoted form).
draft_metadata is the zero-model floor: deterministic neutral KR draft, no
free-form slang ([GATE:D5]), hashtags <= 15, text-only, ai_disclosure False.

Reference: PRD §2 SM-1/§6 J-3/§9 R-CAP3 · workflow.md §5 · [GATE:D5].
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from shorts_forge.llm import template_fallback as TF
from shorts_forge.spine.gates import GateBlocked


def _fake_rs(n_assets=3):
    edl = {"timeline": [{"in": 0.0, "out": 4.0}, {"in": 0.0, "out": 4.0}]}
    assets = [SimpleNamespace(isolated=False) for _ in range(n_assets)]
    return SimpleNamespace(edl=edl, assets=assets)


def test_draft_metadata_neutral_korean_title():
    meta = TF.draft_metadata(_fake_rs())
    assert meta["title"] == TF._TITLE_TMPL
    assert any(ord(c) > 0x3000 for c in meta["title"])   # contains Hangul
    assert len(meta["title"]) <= 90


def test_hashtags_capped_at_15():
    meta = TF.draft_metadata(_fake_rs())
    assert len(meta["hashtags"]) <= 15


def test_ai_disclosure_false_for_silent_real_footage():
    assert TF.draft_metadata(_fake_rs())["ai_disclosure"] is False


def test_deterministic_same_input():
    assert TF.draft_metadata(_fake_rs(5)) == TF.draft_metadata(_fake_rs(5))


def test_cut_count_reflects_non_isolated_assets():
    meta = TF.draft_metadata(_fake_rs(n_assets=4))
    assert "총 4개 컷" in meta["description"]


def test_resolve_slang_is_gate_blocked_d5():
    with pytest.raises(GateBlocked):
        TF.resolve_slang("아무 슬랭")
