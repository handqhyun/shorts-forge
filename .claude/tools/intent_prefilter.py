"""N-2: intent-classifier prefilter CLI.

Reference: prompt/workflow-coding.md sections 5.2.3 (N-2), 16 IQ-17.

Deterministic substring/keyword prefilter over owner input. Emits candidate intent
categories plus an ambiguity signal. The LLM category classifier runs ONLY on
prefilter-pass input (multi-match); zero matches route straight to blocking-surfacer
without an LLM call. This tool is the deterministic prefilter, not the classifier.

Standard library only: argparse, json, re, sys.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from . import errors, result

TRACE = {
    "module": "tools.intent_prefilter",
    "imports": ["argparse", "json", "re", "sys", "tools.errors", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-intent_prefilter",
}

# Deterministic keyword signals per category.
GATE_RE = re.compile(r"(?<![0-9A-Za-z])D(?:[1-9]|1[0-7])(?![0-9A-Za-z])")
IQ_RE = re.compile(r"(?<![0-9A-Za-z])IQ-\d+(?![0-9A-Za-z])")
DESIGN_RE = re.compile(r"\[DESIGN\]|ADR|fork|어댑터|adapter")
PROGRESS_KW = ("build", "next", "run", "진행", "다음", "실행", "이어", "착수", "진입")
META_KW = ("?", "상태", "status", "뭐", "무엇", "확인", "어떻게", "왜")
# "왜" is shared with the 4-option decision-surface structure (핵심·왜·트레이드오프·다음
# 결과). When the input echoes a full decision surface, "왜" is a structural token, not
# an interrogative — so it must not, on its own, drive a meta-question classification.
FOUR_OPTION_TOKENS = ("핵심", "왜", "트레이드오프", "다음 결과")

HELP_JSON = {
    "tool": "intent_prefilter",
    "args": {
        "--raw-input": "str owner input verbatim (required)",
    },
}


def prefilter(text: str) -> dict:
    candidates = []
    if GATE_RE.search(text):
        candidates.append("BLOCKING")
    if IQ_RE.search(text):
        candidates.append("[INFRA-DESIGN]")
    if DESIGN_RE.search(text):
        candidates.append("[DESIGN]")
    if any(kw in text for kw in PROGRESS_KW):
        candidates.append("build-progress")
    meta_hits = [kw for kw in META_KW if kw in text]
    if all(t in text for t in FOUR_OPTION_TOKENS):
        meta_hits = [kw for kw in meta_hits if kw != "왜"]
    if meta_hits:
        candidates.append("meta-question")

    # de-duplicate, preserve order
    seen = []
    for c in candidates:
        if c not in seen:
            seen.append(c)

    if not seen:
        ambiguity = "undecidable"
    elif len(seen) == 1:
        ambiguity = "clear"
    else:
        ambiguity = "multi-intent"

    return {
        "candidate_categories": seen,
        "ambiguity_level": ambiguity,
        "needs_llm": ambiguity == "multi-intent",
        "route_to_blocking_surfacer": ambiguity in ("undecidable", "multi-intent"),
    }


def cmd(ns: argparse.Namespace) -> result.ToolResult:
    if ns.raw_input is None:
        raise errors.UsageError("--raw-input is required")
    return result.ok(prefilter(ns.raw_input))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="intent_prefilter", description="intent prefilter")
    parser.add_argument("--help-json", action="store_true")
    parser.add_argument("--raw-input", default=None)
    parser.set_defaults(fn=cmd)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    if ns.raw_input is None:
        parser.print_help(sys.stderr)
        return 2
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
