"""CLI E2E for `shorts-forge start` — natural-language entry into the
user guidance mode. Crosses the real process boundary via subprocess
(argparse, UTF-8 forcing, entry module discovery).

Reference: PRD §10 OPS-1 trigger, §1.2 non-coder user · workflow.md §1.
Isolation: tmp cwd; the entry surface does not touch the real SOT or
build_state because the `start` verb has no pipeline side effects.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_SRC = str(Path(__file__).resolve().parents[2] / "src")


def _env():
    e = dict(os.environ)
    e["PYTHONPATH"] = _SRC + os.pathsep + e.get("PYTHONPATH", "")
    e["PYTHONIOENCODING"] = "utf-8"
    return e


def _cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "shorts_forge.cli", *args],
        cwd=cwd, env=_env(), capture_output=True, text=True,
        encoding="utf-8",
    )


@pytest.mark.parametrize("utterance", [
    "시작",
    "시작하자",
    "start",
    "워크플로우를 시작하자",
    "작업을 시작하자",
])
def test_start_recognizes_and_shows_guide(utterance, tmp_path):
    r = _cli("start", utterance, cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert "ready" in r.stdout
    assert "풀 렌더" in r.stdout
    assert "스토리보드" in r.stdout
    assert "shorts-forge run" in r.stdout


def test_bare_start_treated_as_start_intent(tmp_path):
    r = _cli("start", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert "풀 렌더" in r.stdout
    assert "shorts-forge run" in r.stdout


def test_unknown_utterance_returns_friendly_error(tmp_path):
    r = _cli("start", "오늘 날씨가 좋네", cwd=tmp_path)
    assert r.returncode == 1
    assert "인식" in (r.stdout + r.stderr)


def test_guide_output_never_lists_build_harness(tmp_path):
    """Structural absence verified at the actual output surface."""
    r = _cli("start", "시작", cwd=tmp_path)
    assert r.returncode == 0
    out_lower = r.stdout.lower()
    for forbidden in ("infrastructure", "build harness", "orchestrator"):
        assert forbidden not in out_lower
    for kr_forbidden in ("재빌드", "재실행", "인프라"):
        assert kr_forbidden not in r.stdout
