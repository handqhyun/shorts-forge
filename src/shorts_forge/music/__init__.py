"""Owner-supplied local music — PRD §12-D2/D14 v1.2 currency 2026-05-25 (option 2).

Owner places `.mp3` / `.m4a` / `.wav` files under `<sf_root>/music/`; the
pipeline picks one deterministically per run (seed-based). License is the
owner's responsibility (CC0 / owned / commissioned / cleared). Strictly
read-only; no external fetch (INVARIANT #1). Empty folder → silent fallback.
"""

TRACE = {
    "prd": "§12-D2/D14 v1.2",
    "workflow": "§10 D2/D14 v1.2·§2 S5",
    "ax": ["AX-LICENSE", "AX-MEDIA"],
    "f": ["§3.8", "§3.1"],
    "gate": ["D2", "D14"],
}
