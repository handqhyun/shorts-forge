"""lex loader — D5 v1.0 currency (option 2 owner manual local lexicon).

Reference: PRD §12-D5/D16 v1.0 · workflow.md §10 D5/D16 v1.0 ·
src/shorts_forge/lex/loader.py.
"""
from __future__ import annotations

import unicodedata

from shorts_forge.lex import loader


def _lex_dir(root):
    d = root / loader.LEX_DIRNAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def test_missing_root_returns_empty(tmp_path):
    assert loader.load_lex(tmp_path / "no_root") == frozenset()


def test_missing_file_returns_empty(tmp_path):
    _lex_dir(tmp_path)  # dir present but no file
    assert loader.load_lex(tmp_path) == frozenset()


def test_empty_file_returns_empty(tmp_path):
    d = _lex_dir(tmp_path)
    (d / loader.LEX_FILENAME).write_text("", encoding="utf-8")
    assert loader.load_lex(tmp_path) == frozenset()


def test_basic_keywords(tmp_path):
    d = _lex_dir(tmp_path)
    (d / loader.LEX_FILENAME).write_text("운동\n다이어트\n챌린지\n", encoding="utf-8")
    assert loader.load_lex(tmp_path) == frozenset({"운동", "다이어트", "챌린지"})


def test_skips_comments_and_blank_lines(tmp_path):
    d = _lex_dir(tmp_path)
    (d / loader.LEX_FILENAME).write_text(
        "# 주석 한 줄\n\n  \n운동\n# 다른 주석\n",
        encoding="utf-8",
    )
    assert loader.load_lex(tmp_path) == frozenset({"운동"})


def test_dedups(tmp_path):
    d = _lex_dir(tmp_path)
    (d / loader.LEX_FILENAME).write_text("운동\n운동\n운동\n", encoding="utf-8")
    assert loader.load_lex(tmp_path) == frozenset({"운동"})


def test_skips_too_long(tmp_path):
    d = _lex_dir(tmp_path)
    too_long = "x" * (loader.MAX_KEYWORD_LEN + 1)
    (d / loader.LEX_FILENAME).write_text(f"{too_long}\n운동\n", encoding="utf-8")
    assert loader.load_lex(tmp_path) == frozenset({"운동"})


def test_max_keywords_bound(tmp_path):
    d = _lex_dir(tmp_path)
    lines = "\n".join(f"kw{i}" for i in range(loader.MAX_KEYWORDS + 50))
    (d / loader.LEX_FILENAME).write_text(lines, encoding="utf-8")
    out = loader.load_lex(tmp_path)
    assert len(out) == loader.MAX_KEYWORDS


def test_nfc_normalizes_nfd_input(tmp_path):
    d = _lex_dir(tmp_path)
    nfd = unicodedata.normalize("NFD", "한국")
    assert nfd != "한국"  # decomposed
    (d / loader.LEX_FILENAME).write_text(nfd, encoding="utf-8")
    assert "한국" in loader.load_lex(tmp_path)


def test_corrupt_bytes_returns_empty(tmp_path):
    d = _lex_dir(tmp_path)
    (d / loader.LEX_FILENAME).write_bytes(b"\xff\xfe invalid utf-8 \x80")
    assert loader.load_lex(tmp_path) == frozenset()


def test_trims_surrounding_whitespace(tmp_path):
    d = _lex_dir(tmp_path)
    (d / loader.LEX_FILENAME).write_text("  운동  \n\t다이어트\t\n", encoding="utf-8")
    assert loader.load_lex(tmp_path) == frozenset({"운동", "다이어트"})


def test_read_only_does_not_create_files(tmp_path):
    # load_lex on a clean tmp_path must not write anything.
    before = set(tmp_path.iterdir())
    loader.load_lex(tmp_path)
    after = set(tmp_path.iterdir())
    assert before == after
