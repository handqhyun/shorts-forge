"""Owner music loader — PRD §12-D2/D14 v1.2 currency 2026-05-25 (option 2).

Reads owner-placed audio files under ``<sf_root>/music/`` (whitelist of
``.mp3`` / ``.m4a`` / ``.wav`` only). Pick is deterministic (seed-based).
Missing / empty / unreadable folder → empty list / ``None`` — graceful
degradation to silent_inc1, identical to pre-v1.2 behavior.

INVARIANT #1: read-only; no external fetch.

Reference: PRD §12-D2/D14 v1.2 currency · workflow.md §10 D2/D14 v1.2 ·
``src/shorts_forge/stages/s5_audio.py``. Schema extensions (per-track mood
tags, BPM hints, license manifest, multi-track mixing) are ``[DESIGN]``
잔존 per PRD §12-D2 v1.2 currency.
"""
from __future__ import annotations

import hashlib
import unicodedata
from pathlib import Path

TRACE = {
    "prd": "§12-D2/D14 v1.2",
    "workflow": "§10 D2/D14 v1.2·§2 S5",
    "ax": ["AX-LICENSE", "AX-MEDIA"],
    "f": ["§3.8", "§3.1"],
    "gate": ["D2", "D14"],
}

MUSIC_DIRNAME = "music"
ALLOWED_EXTS = frozenset({".mp3", ".m4a", ".wav"})
MAX_TRACK_BYTES = 200 * 1024 * 1024  # 200 MiB safety bound per track


def music_dir(sf_root: Path) -> Path:
    return Path(sf_root) / MUSIC_DIRNAME


def discover_tracks(sf_root: Path) -> list[Path]:
    """Sorted (NFC) list of allowed-extension music files. Empty on absence."""
    d = music_dir(sf_root)
    if not d.is_dir():
        return []
    try:
        entries = list(d.iterdir())
    except OSError:
        return []
    out: list[Path] = []
    for p in entries:
        if not p.is_file():
            continue
        if p.suffix.lower() not in ALLOWED_EXTS:
            continue
        try:
            if p.stat().st_size > MAX_TRACK_BYTES:
                continue
        except OSError:
            continue
        out.append(p)
    out.sort(key=lambda p: unicodedata.normalize("NFC", p.name))
    return out


def pick_track(tracks: list[Path], seed: int) -> Path | None:
    """Deterministic seed-based pick; empty list → None."""
    if not tracks:
        return None
    h = hashlib.sha256(str(seed).encode("utf-8")).digest()
    idx = int.from_bytes(h[:8], "big") % len(tracks)
    return tracks[idx]


def load_for_run(sf_root: Path, seed: int) -> Path | None:
    """Composite helper: discover + pick."""
    return pick_track(discover_tracks(sf_root), seed)
