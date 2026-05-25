"""Owner-supplied prose notes — PRD §3.1 v1.1 currency 2026-05-25 (option A).

Optional text seeds in the Inbox folder (e.g. ``description.txt``) flow into
the metadata draft. Strictly read-only; no external fetch (INVARIANT #1).
Missing / empty / corrupt files degrade silently to the neutral fallback.
"""

TRACE = {
    "prd": "§3.1 v1.1",
    "workflow": "§S1 v1.1·§5",
    "ax": ["AX-I18N", "AX-CRAFT"],
    "f": ["§3.11"],
    "gate": [],
}
