"""Smart router: natural-language start command -> product usage intent.

Design (not a flat keyword list):
  - Each semantic concept (INITIATE, WORK_OBJECT) owns an extensible set
    of normalized surface forms.
  - An intent fires when its required concepts are present.
  - Recognition runs on normalized tokens (NFC + casefold + outer whitespace
    strip + small trailing-punctuation strip), with single-token, full-string,
    and 2-gram candidates to admit multi-word forms like "let's start".
  - Adding a new surface form is data, not code: the matching logic is
    unchanged because it operates on concept membership and intent composition.

Invariants:
  - INVARIANT #1: pure-local; no network, no LLM, no embeddings.
  - Layer separation: this module does not import the build harness layer.
    The guidance options surface (guide.py) is fixed to product CLI verbs,
    so the layer-A rebuild path is structurally unreachable from any branch
    reachable here — there is no symbol, no import, no string that addresses
    the harness.

Honest limit: without embeddings/LLM (INVARIANT #1), purely semantic
recognition is bounded by lexicon coverage. New variants extend a concept
set; matching itself does not change.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import Enum

TRACE = {
    "prd": "§10 OPS-1, §1.2",
    "workflow": "§1",
    "ax": ["AX-ONBOARD"],
    "f": [],
    "gate": [],
}


class Intent(str, Enum):
    START_USAGE = "START_USAGE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ConceptAnchor:
    """A semantic concept and its normalized surface forms.

    Surface forms are stored case-folded; matching re-normalizes both sides
    to stay robust against editor input variation.
    """
    name: str
    surfaces: frozenset[str]


INITIATE = ConceptAnchor(
    "INITIATE",
    frozenset({
        # Korean
        "시작", "시작하자", "시작하기", "시작해", "시작해줘", "시작합시다",
        "스타트",
        # English
        "start", "begin", "kickoff", "kick off", "go",
        "let's start", "lets start", "let us start",
    }),
)

WORK_OBJECT = ConceptAnchor(
    "WORK_OBJECT",
    frozenset({
        # Korean (bare + topic/object particles)
        "워크플로우", "워크플로우를", "워크플로", "워크플로를",
        "작업", "작업을", "프로세스", "파이프라인",
        # English
        "workflow", "work", "task", "process", "pipeline",
    }),
)

_CONCEPTS: tuple[ConceptAnchor, ...] = (INITIATE, WORK_OBJECT)


@dataclass(frozen=True)
class IntentSpec:
    intent: Intent
    required: tuple[str, ...]


# START_USAGE requires INITIATE. WORK_OBJECT is contextual (boosts intent
# strength when paired) but not strictly required — "시작" / "start" alone
# is an explicit start command per task spec.
_INTENTS: tuple[IntentSpec, ...] = (
    IntentSpec(Intent.START_USAGE, required=("INITIATE",)),
)


_TRAILING_PUNCT = ".,!?:;~"


def _normalize(s: str | None) -> str:
    """NFC + casefold + strip outer whitespace + drop trailing punctuation."""
    if not s:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = s.casefold().strip()
    while s and s[-1] in _TRAILING_PUNCT:
        s = s[:-1]
    return s


def _candidates(utterance: str | None) -> set[str]:
    """Generate surface candidates: full string, single tokens, and 2-grams.

    This admits multi-word concept forms ("let's start", "워크플로우를 시작하자")
    without requiring the user to match a specific surface exactly.
    """
    s = _normalize(utterance)
    if not s:
        return set()
    parts = s.split()
    cands: set[str] = {s}
    cands.update(parts)
    for i in range(len(parts) - 1):
        cands.add(parts[i] + " " + parts[i + 1])
    return cands


def _concepts_present(utterance: str | None) -> set[str]:
    candidates = _candidates(utterance)
    if not candidates:
        return set()
    hits: set[str] = set()
    for concept in _CONCEPTS:
        normalized = {_normalize(x) for x in concept.surfaces}
        if candidates & normalized:
            hits.add(concept.name)
    return hits


def recognize(utterance: str | None) -> Intent:
    """Classify an utterance into a product usage intent.

    Empty / None / unrecognized -> Intent.UNKNOWN. Callers (cli.cmd_start)
    treat a bare `start` verb as recognize("start").
    """
    hits = _concepts_present(utterance)
    for spec in _INTENTS:
        if all(req in hits for req in spec.required):
            return spec.intent
    return Intent.UNKNOWN
