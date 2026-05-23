"""N-3: translatability-precheck CLI (deterministic part).

Reference: prompt/workflow-coding.md sections 5.3.6 (N-3).

Deterministic checks (a)~(d) on an English original before pair-write:
  (a) identifier integrity: malformed-pattern detection for section refs (§ without a
      number), gate ids ([GATE:D] without a digit), IQ ids (IQ- without a digit), and
      ADAPT ids (ADAPT- without a slug). Detects broken identifiers only — well-formed
      refs never trip it.
  (b) code-block / fence pairing (even number of ``` fences)
  (c) currency-marker format (when category='currency-marker')
  (d) 4-option decision-surface structure (when category='4-option-decision-surface')
The LLM checks (e)~(g) run only on (a)~(d) pass; this tool emits the deterministic
verdict and the prefilter-pass payload.

Standard library only: argparse, json, re, sys.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from . import errors, result

TRACE = {
    "module": "tools.translatability_precheck",
    "imports": ["argparse", "json", "re", "sys", "tools.errors", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-translatability_precheck",
}

CATEGORIES = (
    "4-option-decision-surface",
    "adr-body",
    "owner-guide",
    "subagent-output",
    "currency-marker",
)

CURRENCY_RE = re.compile(
    r"\(v\d+\.\d+(?:\.\d+)? currency \d{4}-\d{2}-\d{2}·번복 아님·X3 안정성 클래스"
)
# Malformed-identifier detection (a): each fires only on a broken pattern, so
# well-formed identifiers (§4.3.5, [GATE:D14], IQ-17, ADAPT-S1-IN) never trip them.
BAD_GATE_RE = re.compile(r"\[GATE:D\](?![0-9])|\[GATE:D\b(?!\d)")
BAD_SECTION_RE = re.compile(r"§(?!\s*\d)")
BAD_IQ_RE = re.compile(r"IQ-(?!\d)")
BAD_ADAPT_RE = re.compile(r"ADAPT-(?![A-Za-z0-9])")
IDENTIFIER_FAILURES = frozenset({
    "malformed_gate_ref", "malformed_section_ref", "malformed_iq_ref", "malformed_adapter_ref",
})
FOUR_OPTION_TOKENS = ("핵심", "왜", "트레이드오프", "다음 결과")

HELP_JSON = {
    "tool": "translatability_precheck",
    "args": {
        "--en-content": "str English original (required)",
        "--category": f"enum{CATEGORIES} (required)",
    },
}


def precheck(content: str, category: str) -> dict:
    failed = []

    # (b) fenced code-block pairing
    if content.count("```") % 2 != 0:
        failed.append("code_block_unbalanced")

    # (a) identifier integrity: malformed gate / section / IQ / ADAPT refs
    if BAD_GATE_RE.search(content):
        failed.append("malformed_gate_ref")
    if BAD_SECTION_RE.search(content):
        failed.append("malformed_section_ref")
    if BAD_IQ_RE.search(content):
        failed.append("malformed_iq_ref")
    if BAD_ADAPT_RE.search(content):
        failed.append("malformed_adapter_ref")

    # (c) currency-marker format
    if category == "currency-marker" and not CURRENCY_RE.search(content):
        failed.append("currency_marker_malformed")

    # (d) 4-option decision-surface structure
    if category == "4-option-decision-surface":
        missing = [t for t in FOUR_OPTION_TOKENS if t not in content]
        if missing:
            failed.append("four_option_structure_missing:" + ",".join(missing))

    return {
        "category": category,
        "verdict": "pass" if not failed else "fail",
        "failed_axes": failed,
        "identifier_integrity_ok": not (IDENTIFIER_FAILURES & set(failed)),
        "structure_ok": not any(f.startswith("four_option") for f in failed),
        "markers_ok": "currency_marker_malformed" not in failed,
    }


def cmd(ns: argparse.Namespace) -> result.ToolResult:
    if ns.en_content is None:
        raise errors.UsageError("--en-content is required")
    if ns.category not in CATEGORIES:
        raise errors.ValidationError(f"--category must be one of {CATEGORIES}")
    return result.ok(precheck(ns.en_content, ns.category))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="translatability_precheck", description="translatability precheck")
    parser.add_argument("--help-json", action="store_true")
    parser.add_argument("--en-content", default=None)
    parser.add_argument("--category", default="subagent-output")
    parser.set_defaults(fn=cmd)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    if ns.en_content is None:
        parser.print_help(sys.stderr)
        return 2
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
