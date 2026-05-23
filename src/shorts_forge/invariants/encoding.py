"""인코딩 불변 — NFC 정규화·UTF-8·ASCII 작업루트 강제.

추적: PRD §4 C-I18N(비협상)·INVARIANT #1 인코딩 위반정의 · workflow.md §6 · [F §3.11/§3.13]
【AX-I18N】 macOS/iOS NFD 분해 한글 파일명 → Python open()/glob 가 NFC 문자열로
FileNotFoundError → **사용자 미디어 무성 손실**(최고 확신·최고 임팩트). 모든 ingest
경로/문자열 NFC 강제, JSON/EDL ensure_ascii=False, 내부 작업루트 ASCII-only.
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

TRACE = {
    "prd": "§4 C-I18N",
    "workflow": "§6",
    "ax": ["AX-I18N", "AX-ONBOARD"],
    "f": ["§3.11", "§3.13"],
    "gate": [],
}


class EncodingViolation(RuntimeError):
    """INVARIANT #1 인코딩 위반정의 해당(비-ASCII 작업루트·미정규화 경로 처리)."""


def nfc(text: str) -> str:
    """문자열을 NFC 로 정규화(비협상). 모든 ingest 문자열/경로에 적용."""
    return unicodedata.normalize("NFC", text)


def nfc_path(p: str | Path) -> Path:
    """경로 문자열을 NFC 정규화하여 Path 로(한글 NFD 무성 손실 방지)."""
    return Path(nfc(str(p)))


def is_ascii(text: str) -> bool:
    return text.isascii()


def assert_ascii_workroot(root: str | Path) -> Path:
    """작업루트가 ASCII-only 임을 강제. 비-ASCII = 인코딩 위반정의([F §3.13]).

    한글 사용자명 경로(C:\\Users\\<한글이름>)+CP949+subprocess = 보장된 실패.
    """
    r = nfc_path(root)
    if not is_ascii(str(r)):
        raise EncodingViolation(
            f"작업루트는 ASCII-only 여야 함(INVARIANT #1 인코딩 위반정의): {r!r}"
        )
    return r


def force_utf8_io() -> None:
    """stdout/stderr 를 UTF-8 로 강제(콘솔 코드페이지 cp949 비의존).

    [F §3.11/§3.13] 한국 Windows 기본 콘솔=cp949 → 비-cp949 출력 시
    UnicodeEncodeError. 앱은 콘솔 인코딩에 의존하지 않고 UTF-8 을 강제한다
    (INVARIANT #1 인코딩 불변의 출력측 강제).
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="backslashreplace")
            except (ValueError, OSError):
                pass


def assert_utf8_runtime() -> None:
    """런타임 UTF-8 강제 확인(PYTHONUTF8 / utf-8 mode). 미충족 시 위반."""
    enc = (sys.getfilesystemencoding() or "").lower()
    if enc not in ("utf-8", "utf8"):
        raise EncodingViolation(
            f"파일시스템 인코딩 UTF-8 필요(PYTHONUTF8=1), 실측={enc!r}"
        )


def json_dump_kwargs() -> dict:
    """JSON/EDL 직렬화 표준 kwargs — 한글 보존(ensure_ascii=False)·UTF-8."""
    return {"ensure_ascii": False, "indent": 2, "sort_keys": True}
