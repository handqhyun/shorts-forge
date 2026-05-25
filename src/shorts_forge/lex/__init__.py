"""Owner-managed local lexicon — D5/D16 v1.0 currency 2026-05-25 (option 2).

PRD §12-D5/D16 v1.0 currency: owner manually edits a local text file; code is
read-only; no external fetch (INVARIANT #1 preserved). Empty / missing file →
graceful degradation to chronological + neutral fallback.
"""

TRACE = {
    "prd": "§12-D5/D16 v1.0",
    "workflow": "§10 D5/D16 v1.0",
    "ax": ["AX-CRAFT", "AX-I18N"],
    "f": ["§3.9", "§3.11"],
    "gate": ["D5", "D16"],
}
