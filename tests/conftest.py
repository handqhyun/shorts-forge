"""pytest 공통 — 합성 inbox 픽스처(개인 미디어 절대 미사용, PRD §7 NEVER)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_FIX = Path(__file__).parent / "fixtures" / "gen_synthetic.py"
_spec = importlib.util.spec_from_file_location("gen_synthetic", _FIX)
gen_synthetic = importlib.util.module_from_spec(_spec)
sys.modules["gen_synthetic"] = gen_synthetic
_spec.loader.exec_module(gen_synthetic)


@pytest.fixture()
def synthetic_inbox(tmp_path) -> Path:
    return gen_synthetic.make_inbox(tmp_path / "inbox")


@pytest.fixture()
def ascii_root(tmp_path) -> Path:
    r = tmp_path / "sfroot"
    r.mkdir()
    return r
