"""추적성 강제 — 모든 src 모듈이 TRACE 포인터 보유(ANCHOR ① 추적 불가=품질 실패).

추적: PRD header ANCHOR ① · workflow.md header · final-research.md §0
"""
from __future__ import annotations

import importlib
import pkgutil

import shorts_forge

REQUIRED_KEYS = {"prd", "workflow", "ax", "f", "gate"}


def _all_modules():
    yield shorts_forge
    for m in pkgutil.walk_packages(shorts_forge.__path__,
                                   prefix="shorts_forge."):
        yield importlib.import_module(m.name)


def test_every_module_has_trace_pointers():
    missing = []
    for mod in _all_modules():
        trace = getattr(mod, "TRACE", None)
        if not isinstance(trace, dict):
            missing.append(f"{mod.__name__}: TRACE 부재")
            continue
        if not REQUIRED_KEYS.issubset(trace):
            missing.append(f"{mod.__name__}: 키 누락 {REQUIRED_KEYS - set(trace)}")
            continue
        if not str(trace.get("prd")).strip() or not str(trace.get("workflow")).strip():
            missing.append(f"{mod.__name__}: prd/workflow 포인터 공백")
    assert not missing, "추적성 실패(=품질 실패):\n" + "\n".join(missing)
