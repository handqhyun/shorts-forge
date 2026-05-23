"""run 락·자원 가드 — 동시 다중 run 금지·encode/model 동시금지(OPS-6, [F §3.7])."""
from __future__ import annotations

import pytest

from shorts_forge.invariants import resource_guard, runlock


def test_run_lock_is_exclusive(tmp_path):
    lp = tmp_path / ".run.lock"
    with runlock.run_lock(lp):
        with pytest.raises(runlock.RunLockBusy):
            with runlock.run_lock(lp):
                pass
    # 해제 후 재획득 가능(직렬 FIFO)
    with runlock.run_lock(lp):
        pass


def test_encode_model_concurrency_rejected():
    with resource_guard.heavy_section("encode"):
        with pytest.raises(resource_guard.ResourceViolation):
            with resource_guard.heavy_section("model"):
                pass
    # 순차는 허용
    with resource_guard.heavy_section("model"):
        pass


def test_below_normal_priority_best_effort():
    # Windows 면 True, 기타 환경은 우아 강등(False) — 둘 다 불변식 비위반
    assert resource_guard.set_below_normal_priority() in (True, False)
