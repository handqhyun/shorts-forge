"""Trending lexicon loader — PRD §12-D5/D16 v1.0 currency 2026-05-25 (option 2).

Reads owner-edited local text file at `<sf_root>/lex/trending.txt`.
Returns a frozenset of NFC-normalized keywords. File absent, parse failure,
empty file, or any I/O error → empty frozenset (graceful degradation to
chronological order + neutral hashtag fallback; spine_kind stays
"chronological").

INVARIANT #1: code is read-only and never reaches the network.

Reference: PRD §12-D5/D16 v1.0 · workflow.md §10 D5/D16 v1.0 currency · §5
LLM node · S3 SELECT/ORDER. Schema details (richer JSON, per-keyword
confidence, separate slang vs topic pools, edit UI) remain `[DESIGN]` —
deferred to a separate turn per PRD §12-D5 v1.0 currency.
"""
from __future__ import annotations

import unicodedata
from pathlib import Path

TRACE = {
    "prd": "§12-D5/D16 v1.0",
    "workflow": "§10 D5/D16 v1.0",
    "ax": ["AX-CRAFT", "AX-I18N"],
    "f": ["§3.9", "§3.11"],
    "gate": ["D5", "D16"],
}

LEX_DIRNAME = "lex"
LEX_FILENAME = "trending.txt"
COMMENT_PREFIX = "#"
MAX_KEYWORDS = 200
MAX_KEYWORD_LEN = 40


def lex_path(sf_root: Path) -> Path:
    return Path(sf_root) / LEX_DIRNAME / LEX_FILENAME


def load_lex(sf_root: Path) -> frozenset[str]:
    p = lex_path(sf_root)
    if not p.is_file():
        return frozenset()
    try:
        raw = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return frozenset()
    out: set[str] = set()
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith(COMMENT_PREFIX):
            continue
        if len(s) > MAX_KEYWORD_LEN:
            continue
        out.add(unicodedata.normalize("NFC", s))
        if len(out) >= MAX_KEYWORDS:
            break
    return frozenset(out)
