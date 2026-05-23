"""INVARIANT #1 — 아웃바운드 기본거부 + 네트워크 차단 E2E(SM-3, PRD §4 검증법)."""
from __future__ import annotations

import json
import socket

import pytest

from shorts_forge import cli
from shorts_forge.invariants import netguard


def test_non_carveout_outbound_blocked():
    led = netguard.NetworkLedger()
    with netguard.guarded(led):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with pytest.raises(netguard.InvariantViolation):
            s.connect(("127.0.0.1", 9))   # 비-카브아웃 → 즉시 차단
        s.close()
    assert not led.is_clean()             # 비-카브아웃 시도 기록됨
    assert led.non_carveout()


def test_carveout_outbound_recorded_as_carveout():
    led = netguard.NetworkLedger()
    with netguard.guarded(led):
        with netguard.carveout(netguard.CARVEOUT_SETUP_FETCH):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.2)
            with pytest.raises(OSError):  # 실연결 실패하나 차단은 아님
                s.connect(("127.0.0.1", 9))
            s.close()
    # 카브아웃으로 기록 → INVARIANT #1 위반 아님
    assert led.is_clean()
    assert led.entries and led.entries[-1].carveout_id == netguard.CARVEOUT_SETUP_FETCH


def test_network_blocked_full_pipeline_clean(synthetic_inbox, ascii_root):
    rc = cli.cmd_run(str(synthetic_inbox), root=str(ascii_root),
                     dry_run=False, seed=1234567)
    assert rc == 0                        # clean 이면 0
    runs = sorted((ascii_root / "runs").iterdir())
    assert runs
    manifest = json.loads(
        (runs[-1] / "S7" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["network_ledger"]["invariant1_clean"] is True
    assert manifest["network_ledger"]["non_carveout"] == []
