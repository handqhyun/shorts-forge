"""인코딩 불변 — NFC·UTF-8·ASCII 작업루트(PRD §4 C-I18N, [F §3.11])."""
from __future__ import annotations

import json
import unicodedata

import pytest

from shorts_forge.invariants import encoding


def test_nfc_composes_decomposed_hangul():
    decomposed = unicodedata.normalize("NFD", "여행사진")
    assert decomposed != "여행사진"            # NFD ≠ 원형
    assert encoding.nfc(decomposed) == "여행사진"
    # 멱등
    assert encoding.nfc(encoding.nfc(decomposed)) == "여행사진"


def test_ascii_workroot_rejects_non_ascii():
    with pytest.raises(encoding.EncodingViolation):
        encoding.assert_ascii_workroot(r"C:\Users\우리\sfroot")
    # ASCII 는 통과
    assert encoding.assert_ascii_workroot(r"C:\ProgramData\ShortsForge")


def test_json_dump_kwargs_preserve_hangul():
    s = json.dumps({"제목": "오늘의 기록"}, **encoding.json_dump_kwargs())
    assert "오늘의 기록" in s            # ensure_ascii=False → 한글 보존
    assert "\\u" not in s
