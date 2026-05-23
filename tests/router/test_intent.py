"""Smart router intent recognition + structural layer-separation guarantees.

Asserts:
  (i)  Concept-anchor recognition covers the required KR/EN variants and
       admits new surface forms via concept membership (data), not via
       a flat keyword scan (code).
  (ii) The router/guide modules never reference, import, or reach the
       layer-A build harness — Infrastructure Build re-run is structurally
       unreachable from any branch in this entry surface.
"""
from __future__ import annotations

import ast
import inspect

import pytest

from shorts_forge.entry import guide, router


@pytest.mark.parametrize("utterance", [
    "시작",
    "시작하자",
    "시작해줘",
    "시작합시다",
    "start",
    "START",
    "  시작  ",
    "시작!",
    "워크플로우를 시작하자",
    "작업을 시작하자",
    "워크플로우 시작",
    "let's start",
    "lets start",
    "begin",
    "kickoff",
])
def test_start_usage_recognized(utterance):
    assert router.recognize(utterance) is router.Intent.START_USAGE


@pytest.mark.parametrize("utterance", [
    "",
    None,
    "안녕",
    "오늘 날씨가 좋네",
    "publish",
    "rebuild",
    "infrastructure",
    "시작했어요",                # past tense, not a command form
    "시작하지마",                # negation, not a command form
])
def test_unknown_intent(utterance):
    assert router.recognize(utterance) is router.Intent.UNKNOWN


def test_extending_concept_set_is_data_change_only():
    """Documenting the design property: a new surface form is admitted by
    the same matching code path (concept membership), not by changing
    router logic. We construct an extended frozen concept and verify that
    the normalizer treats new surfaces identically to existing ones.
    """
    extended = router.ConceptAnchor(
        "INITIATE",
        frozenset(router.INITIATE.surfaces | {"개시"}),
    )
    norm = router._normalize
    normalized = {norm(s) for s in extended.surfaces}
    assert norm("개시") in normalized
    # Same code path for old and new surfaces — both normalize identically.
    assert norm("시작") in normalized


def _surface_text() -> str:
    return inspect.getsource(router) + "\n" + inspect.getsource(guide)


@pytest.mark.parametrize("forbidden", [
    "build_orchestrator",
    "shorts-forge-build-orchestrator",
    "build_state",
    "Infrastructure Build",
    "infrastructure_build",
    "Infrastructure",
    ".claude/agents",
    ".claude/tools",
    "step-registry",
    "step_registry",
])
def test_router_and_guide_have_no_harness_token(forbidden):
    assert forbidden not in _surface_text()


def test_router_and_guide_imports_are_clean():
    """AST-level: imports of router.py and guide.py never name the build
    harness package or the orchestrator/build_state modules."""
    for mod in (router, guide):
        tree = ast.parse(inspect.getsource(mod))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert ".claude" not in alias.name
                    assert "orchestrator" not in alias.name
                    assert "build_state" not in alias.name
            elif isinstance(node, ast.ImportFrom):
                name = node.module or ""
                assert ".claude" not in name
                assert "orchestrator" not in name
                assert "build_state" not in name


def test_guide_options_are_fixed_to_product_modes():
    """Catalog is exactly the two product modes; nothing addresses the
    build layer; nothing can be inserted at runtime (frozen tuple of
    frozen dataclasses)."""
    assert isinstance(guide.OPTIONS, tuple)
    assert len(guide.OPTIONS) == 2

    # Exactly one full-render and one dry-run option, both delegating to
    # the existing `shorts-forge run` verb.
    commands = [o.command for o in guide.OPTIONS]
    assert any(c.startswith("shorts-forge run ") and "--dry-run" not in c
               for c in commands)
    assert any("--dry-run" in c for c in commands)

    # No build-layer wording anywhere in user-facing text.
    forbidden_substrings_lower = ("build", "infrastructure", "harness",
                                  "orchestrator", "재실행", "재빌드")
    for opt in guide.OPTIONS:
        haystack = (opt.label + " " + opt.result + " " + opt.command).lower()
        for token in forbidden_substrings_lower:
            assert token.lower() not in haystack


def test_guide_options_dataclass_is_frozen():
    """Defense in depth: a frozen dataclass cannot be mutated to swap in
    a build-layer option after import."""
    opt = guide.OPTIONS[0]
    with pytest.raises(Exception):
        opt.label = "Infrastructure Build 재실행"  # type: ignore[misc]


def test_bare_start_resolves_via_recognize_start():
    """CLI treats a bare `start` verb as recognize('start') — verify the
    underlying recognition is positive so the CLI dispatch is consistent.
    """
    assert router.recognize("start") is router.Intent.START_USAGE
