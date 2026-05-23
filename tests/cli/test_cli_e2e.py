"""A-1 CLI E2E (substitutes the proposal's "Playwright E2E" — there is no UI
surface; the product's only entry point is the `shorts-forge` CLI). Drives the
real process boundary via subprocess (argparse, UTF-8 forcing, run lock,
netguard) rather than calling cli.cmd_run in-process.

Reference: PRD §6 J-1..J-5 · workflow.md §1/§9 · [GATE:D3] (no publish verb).
Isolation: synthetic inbox + tmp root only; never touches the real SOT.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import pytest

_SRC = str(Path(__file__).resolve().parents[2] / "src")


def _env():
    e = dict(os.environ)
    e["PYTHONPATH"] = _SRC + os.pathsep + e.get("PYTHONPATH", "")
    e["SHORTS_FORGE_FFMPEG"] = imageio_ffmpeg.get_ffmpeg_exe()
    e["PYTHONIOENCODING"] = "utf-8"
    return e


def _cli(*args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "shorts_forge.cli", *args],
        capture_output=True, text=True, encoding="utf-8",
        env=_env(), cwd=str(cwd), timeout=300,
    )


def test_selfcheck_exit_zero(tmp_path):
    r = _cli("selfcheck", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert "selfcheck: PASS" in r.stdout


def test_no_subcommand_is_usage_error(tmp_path):
    r = _cli(cwd=tmp_path)
    assert r.returncode == 2          # argparse: required subcommand missing


def test_publish_verb_absent_d3(tmp_path):
    # [GATE:D3] no auto-publish path: `publish` is not a valid CLI verb.
    r = _cli("publish", cwd=tmp_path)
    assert r.returncode != 0
    assert "publish" in (r.stderr + r.stdout)   # invalid choice diagnostic


def test_dry_run_e2e_storyboard_no_mp4(synthetic_inbox, tmp_path):
    root = tmp_path / "root"
    r = _cli("run", str(synthetic_inbox), "--root", str(root),
             "--dry-run", "--seed", "1234567", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert "DRY-RUN" in r.stdout
    assert list(root.glob("runs/*/S6/storyboard.txt"))
    assert not list(root.glob("out/*.mp4"))     # render skipped


def test_full_run_e2e_produces_vertical_short(synthetic_inbox, tmp_path):
    root = tmp_path / "root"
    r = _cli("run", str(synthetic_inbox), "--root", str(root),
             "--seed", "1234567", cwd=tmp_path)
    assert r.returncode == 0, f"rc={r.returncode}\nout={r.stdout}\nerr={r.stderr}"

    mp4s = list(root.glob("out/*.mp4"))
    assert mp4s, "full run produced no mp4"
    assert mp4s[0].stat().st_size > 0

    # geometry via the product's own probe (no external dependency added)
    sys.path.insert(0, _SRC)
    from shorts_forge.stages.s7_validate import _media_info   # noqa: E402
    os.environ.setdefault("SHORTS_FORGE_FFMPEG", imageio_ffmpeg.get_ffmpeg_exe())
    mi = _media_info(str(mp4s[0]))
    assert (mi["width"], mi["height"]) == (1080, 1920)
    assert 0 < mi["duration"] <= 59.5

    meta = list(root.glob("out/*.metadata.json"))
    assert meta
    m = json.loads(meta[0].read_text(encoding="utf-8"))
    assert any(ord(c) > 0x3000 for c in m["title"])      # Korean draft
