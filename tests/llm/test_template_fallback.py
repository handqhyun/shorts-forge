"""A-2 pipeline integration — the single LLM meta node (Inc1 demoted form).
draft_metadata is the zero-model floor: deterministic neutral KR draft, no
free-form slang, hashtags <= 15, text-only, ai_disclosure False.

Reference: PRD §2 SM-1/§6 J-3/§9 R-CAP3/§12-D5 v1.0 · workflow.md §5/§10 D5
v1.0 · [GATE:D5] option 2 (owner manual lexicon).
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from shorts_forge.llm import template_fallback as TF  # noqa: F401  (kept for module-level fixture clarity)

# Baseline tests assume an empty lex (no owner keywords) AND no owner
# description seed. Using paths that do not exist on disk makes both loaders
# return their empty/None fallback — the graceful-degradation path identical
# to pre-v1.0 / pre-v1.1 behavior.
_NOEXIST_LEX_ROOT = Path("/sf_test_root_no_lex_baseline")
_NOEXIST_INBOX = Path("/sf_test_inbox_no_description_baseline")


def _fake_rs(n_assets=3):
    edl = {"timeline": [{"in": 0.0, "out": 4.0}, {"in": 0.0, "out": 4.0}]}
    assets = [SimpleNamespace(isolated=False) for _ in range(n_assets)]
    return SimpleNamespace(edl=edl, assets=assets,
                           root=_NOEXIST_LEX_ROOT, inbox=_NOEXIST_INBOX)


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


def test_empty_lex_baseline_records_zero_lex_size():
    # D5 v1.0 (option 2): missing lex file → lex_size 0, neutral fallback.
    assert TF.draft_metadata(_fake_rs())["lex_size"] == 0
