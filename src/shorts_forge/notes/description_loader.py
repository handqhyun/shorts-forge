"""Owner-supplied description seed — PRD §3.1 v1.1 currency 2026-05-25 (option A).

Reads owner-edited optional text file at ``<inbox>/description.txt``.
Returns NFC-normalized text (trimmed) or ``None`` when absent, empty, too
large, or corrupt UTF-8 — graceful degradation to the neutral KR description
fallback in ``llm.template_fallback.draft_metadata``.

INVARIANT #1: code is read-only and never reaches the network.
Reference: PRD §3.1 v1.1 currency · workflow.md §S1/§5 v1.1 currency.
Schema details (seed application mode — verbatim vs first-N vs summary) are
``[DESIGN]`` 잔존 per PRD §3.1 v1.1 currency.
"""
from __future__ import annotations

import unicodedata
from pathlib import Path

TRACE = {
    "prd": "§3.1 v1.1",
    "workflow": "§S1 v1.1·§5",
    "ax": ["AX-I18N", "AX-CRAFT"],
    "f": ["§3.11"],
    "gate": [],
}

DESCRIPTION_FILENAME = "description.txt"
MAX_CHARS = 1000
MAX_BYTES = 16 * 1024  # 16 KiB safety bound on file size before read


def description_path(inbox: Path) -> Path:
    return Path(inbox) / DESCRIPTION_FILENAME


def load_description(inbox: Path) -> str | None:
    p = description_path(inbox)
    if not p.is_file():
        return None
    try:
        if p.stat().st_size > MAX_BYTES:
            return None
        raw = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    text = unicodedata.normalize("NFC", raw).strip()
    if not text:
        return None
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]
    return text
