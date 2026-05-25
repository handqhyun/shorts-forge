"""template_fallback lex injection — D5 v1.0 currency (option 2 owner-lex).

Reference: PRD §12-D5 v1.0 · workflow.md §5/§10 D5 v1.0 ·
src/shorts_forge/llm/template_fallback.py.
"""
from __future__ import annotations

from types import SimpleNamespace

from shorts_forge.lex import loader
from shorts_forge.llm import template_fallback as TF


def _rs(root, n_assets=3):
    edl = {"timeline": [{"in": 0.0, "out": 4.0}, {"in": 0.0, "out": 4.0}]}
    assets = [SimpleNamespace(isolated=False) for _ in range(n_assets)]
    # inbox path is set under the same tmp_path tree but to a sub-directory
    # that doesn't contain description.txt — keeps these lex-focused tests
    # independent of the v1.1 description seed.
    return SimpleNamespace(edl=edl, assets=assets, root=root,
                           inbox=root / "_no_inbox_for_lex_tests")


def _write_lex(root, *keywords):
    d = root / loader.LEX_DIRNAME
    d.mkdir(parents=True, exist_ok=True)
    (d / loader.LEX_FILENAME).write_text("\n".join(keywords), encoding="utf-8")


def test_empty_lex_uses_base_hashtags_only(tmp_path):
    meta = TF.draft_metadata(_rs(tmp_path))
    assert meta["lex_size"] == 0
    assert "#쇼츠" in meta["hashtags"]
    assert "#shorts" in meta["hashtags"]


def test_lex_keywords_appear_as_hashtags(tmp_path):
    _write_lex(tmp_path, "운동", "다이어트")
    meta = TF.draft_metadata(_rs(tmp_path))
    assert meta["lex_size"] == 2
    assert "#운동" in meta["hashtags"]
    assert "#다이어트" in meta["hashtags"]
    # Base tags preserved.
    assert "#쇼츠" in meta["hashtags"]


def test_hashtags_capped_at_15_with_overflow_lex(tmp_path):
    _write_lex(tmp_path, *[f"kw{i}" for i in range(30)])
    meta = TF.draft_metadata(_rs(tmp_path))
    assert len(meta["hashtags"]) == 15


def test_lex_dedups_against_base(tmp_path):
    _write_lex(tmp_path, "쇼츠")  # collides with base "#쇼츠"
    meta = TF.draft_metadata(_rs(tmp_path))
    assert meta["hashtags"].count("#쇼츠") == 1


def test_keyword_with_hash_prefix_is_treated_as_comment(tmp_path):
    # Single-character `#` at line start marks a comment (loader contract).
    # Owners write plain words; the loader prepends `#` automatically when
    # building hashtags. A line starting with `#` is intentionally skipped.
    _write_lex(tmp_path, "#트렌딩")
    meta = TF.draft_metadata(_rs(tmp_path))
    assert "#트렌딩" not in meta["hashtags"]
    assert meta["lex_size"] == 0


def test_source_records_lex_size(tmp_path):
    _write_lex(tmp_path, "운동", "다이어트", "챌린지")
    meta = TF.draft_metadata(_rs(tmp_path))
    assert "lex_size=3" in meta["source"]


def test_deterministic_with_lex(tmp_path):
    _write_lex(tmp_path, "운동", "다이어트")
    m1 = TF.draft_metadata(_rs(tmp_path))
    m2 = TF.draft_metadata(_rs(tmp_path))
    assert m1 == m2


def test_resolve_slang_returns_input_unchanged_no_lex():
    assert TF.resolve_slang("아무 텍스트") == "아무 텍스트"


def test_resolve_slang_returns_input_unchanged_with_lex():
    # 안 2 v1.0: lex availability does not substitute prose — owner keywords
    # are surfaced via the hashtag layer (see draft_metadata), not by
    # rewriting user-facing text.
    lex = frozenset({"운동", "다이어트"})
    assert TF.resolve_slang("아무 텍스트", lex=lex) == "아무 텍스트"


def test_resolve_slang_normalizes_nfd_to_nfc():
    import unicodedata
    nfd = unicodedata.normalize("NFD", "한국")
    assert nfd != "한국"
    assert TF.resolve_slang(nfd) == "한국"
