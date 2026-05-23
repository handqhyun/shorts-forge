"""A-3 Dry-Run simulation — exercises the storyboard-only decision path
(selection/ordering/EDL/gates) without rendering, plus selfcheck.

Reference: PRD §6 J-3 (dry-run storyboard) · workflow.md §9 ·
[[project-impl-reinspection]] F-7 (dry_run makes G2/G3 trivially pass at
s7_validate.py:94) — these tests assert dry-run as a DECISION-PATH check and
explicitly guard against reading a passing dry-run as render proof.
"""
from __future__ import annotations

import json

from shorts_forge import cli


def _latest_manifest(ascii_root):
    run_dir = sorted((ascii_root / "runs").iterdir())[-1]
    return run_dir, json.loads(
        (run_dir / "S7" / "manifest.json").read_text(encoding="utf-8"))


def _run_dirs(ascii_root):
    base = ascii_root / "runs"
    return {p.name for p in base.iterdir()} if base.exists() else set()


def test_dry_run_emits_storyboard_not_mp4(synthetic_inbox, ascii_root):
    rc = cli.cmd_run(str(synthetic_inbox), root=str(ascii_root),
                     dry_run=True, seed=1234567)
    assert rc == 0
    run_dir, _ = _latest_manifest(ascii_root)

    storyboard = run_dir / "S6" / "storyboard.txt"
    assert storyboard.exists(), "dry-run must emit a storyboard"
    assert "TOTAL=" in storyboard.read_text(encoding="utf-8")

    # FALSE-GREEN GUARD (F-7): a passing dry-run must NOT have produced a render.
    assert not list((ascii_root / "out").glob("*.mp4")), \
        "dry-run produced an mp4 — render was not actually skipped"


def test_dry_run_structural_gates_are_not_render_verified(synthetic_inbox, ascii_root):
    cli.cmd_run(str(synthetic_inbox), root=str(ascii_root),
                dry_run=True, seed=1234567)
    _, man = _latest_manifest(ascii_root)
    gates, notes = man["gates"], man["gate_notes"]

    # EDL-structure gates are genuinely evaluated even in dry-run.
    for g in ("G4", "G5", "G6", "G7"):
        assert g in gates, f"{g} missing from dry-run manifest"

    # G1 is EDL-duration based and labelled dry-run (not a measured render).
    assert "dry-run" in notes.get("G1", "")
    # G2/G3 pass structurally with NO rendered media behind them: this is the
    # documented F-7 weakness, asserted here so it cannot masquerade as proof.
    assert gates["G2"] is True and gates["G3"] is True
    assert man["output"] and man["output"].endswith("storyboard.txt")


def test_dry_run_deterministic_same_seed(synthetic_inbox, ascii_root):
    # run_id is a random uuid4 (runstate.new_run), so identify each run by the
    # newly-created dir rather than lexicographic order.
    before = _run_dirs(ascii_root)
    cli.cmd_run(str(synthetic_inbox), root=str(ascii_root), dry_run=True, seed=42)
    run_a = ((ascii_root / "runs") / (_run_dirs(ascii_root) - before).pop())
    sb_a = (run_a / "S6" / "storyboard.txt").read_text(encoding="utf-8")

    before = _run_dirs(ascii_root)
    cli.cmd_run(str(synthetic_inbox), root=str(ascii_root), dry_run=True, seed=42)
    run_b = ((ascii_root / "runs") / (_run_dirs(ascii_root) - before).pop())
    sb_b = (run_b / "S6" / "storyboard.txt").read_text(encoding="utf-8")

    assert run_a.name != run_b.name    # distinct runs (random run_id)
    # The storyboard embeds run-id-keyed absolute slide paths; the deterministic
    # invariant is the DECISION content (cut order, durations, motion), so
    # normalise the per-run id out before comparing.
    norm_a = sb_a.replace(run_a.name, "RUNID")
    norm_b = sb_b.replace(run_b.name, "RUNID")
    assert norm_a == norm_b            # identical decisions (deterministic)


def test_selfcheck_passes_invariant_harness():
    assert cli.cmd_selfcheck() == 0
