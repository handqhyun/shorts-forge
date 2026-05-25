"""description_loader — PRD §3.1 v1.1 (option A owner description.txt seed).

Reference: PRD §3.1 v1.1 currency · workflow.md §S1 v1.1 ·
src/shorts_forge/notes/description_loader.py.
"""
from __future__ import annotations

import unicodedata

from shorts_forge.notes import description_loader as DL


def _write(inbox, text):
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / DL.DESCRIPTION_FILENAME).write_text(text, encoding="utf-8")


def test_missing_inbox_returns_none(tmp_path):
    assert DL.load_description(tmp_path / "no_inbox") is None


def test_missing_file_returns_none(tmp_path):
    (tmp_path / "inbox").mkdir()
    assert DL.load_description(tmp_path / "inbox") is None


def test_empty_file_returns_none(tmp_path):
    inbox = tmp_path / "inbox"
    _write(inbox, "")
    assert DL.load_description(inbox) is None


def test_whitespace_only_returns_none(tmp_path):
    inbox = tmp_path / "inbox"
    _write(inbox, "   \n\t\n  ")
    assert DL.load_description(inbox) is None


def test_basic_korean_text(tmp_path):
    inbox = tmp_path / "inbox"
    _write(inbox, "오늘 운동한 기록입니다.")
    assert DL.load_description(inbox) == "오늘 운동한 기록입니다."


def test_strips_leading_trailing_whitespace(tmp_path):
    inbox = tmp_path / "inbox"
    _write(inbox, "\n\n  본문 내용  \n\n")
    assert DL.load_description(inbox) == "본문 내용"


def test_nfd_input_normalized_to_nfc(tmp_path):
    inbox = tmp_path / "inbox"
    nfd = unicodedata.normalize("NFD", "한국 여행")
    assert nfd != "한국 여행"
    _write(inbox, nfd)
    assert DL.load_description(inbox) == "한국 여행"


def test_max_chars_truncation(tmp_path):
    inbox = tmp_path / "inbox"
    long_text = "가" * (DL.MAX_CHARS + 100)
    _write(inbox, long_text)
    out = DL.load_description(inbox)
    assert out is not None
    assert len(out) == DL.MAX_CHARS


def test_max_bytes_rejected_returns_none(tmp_path):
    inbox = tmp_path / "inbox"
    # 16 KiB + 1 — exceeds MAX_BYTES; loader refuses to read.
    huge = "x" * (DL.MAX_BYTES + 1)
    _write(inbox, huge)
    assert DL.load_description(inbox) is None


def test_corrupt_utf8_returns_none(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / DL.DESCRIPTION_FILENAME).write_bytes(b"\xff\xfe invalid utf-8 \x80")
    assert DL.load_description(inbox) is None


def test_multiline_preserved_inside_limit(tmp_path):
    inbox = tmp_path / "inbox"
    _write(inbox, "첫 줄.\n둘째 줄.\n셋째 줄.")
    assert DL.load_description(inbox) == "첫 줄.\n둘째 줄.\n셋째 줄."


def test_read_only_does_not_modify_inbox(tmp_path):
    inbox = tmp_path / "inbox"
    _write(inbox, "메모")
    before = sorted(p.name for p in inbox.iterdir())
    DL.load_description(inbox)
    after = sorted(p.name for p in inbox.iterdir())
    assert before == after
