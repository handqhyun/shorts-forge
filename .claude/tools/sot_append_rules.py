"""Shared SOT append-only rule definitions — single source of truth.

Reference: prompt/workflow-coding.md §4.4.1 (N-4) / §5.2.2 (P-7) / §11.2 / IQ-27.

Both sot_guardian (N-4 PreToolUse guard) and append_only (P-7 currency validator)
import the canonical currency marker and the append-only verifier from HERE, so
that "what is a valid append" has exactly ONE definition (ANCHOR II SOT integrity:
no divergent rules across tools).

LIMITATION — a deterministic guard cannot enforce *semantics*. verify_append_only
proves a *structural* append-only change (no line removed, no body rewritten) plus
§11.2 version/status token-only corrections. It CANNOT detect a semantically
reversing clause phrased as an append (e.g. appending "...정정: 실은 반대 채택").
Decision-reversal prevention (§11.2 "결정 번복 불허") therefore remains the
responsibility of the append-only skill flow + owner confirmation, NOT this gate.

Standard library only: difflib, re.
"""
from __future__ import annotations

import difflib
import re

TRACE = {
    "module": "tools.sot_append_rules",
    "imports": ["difflib", "re"],
    "imported_by": ["tools.sot_guardian", "tools.append_only"],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-sot_append_rules",
}

# Canonical currency marker (workflow-coding.md §4.4.1 N-4 / §5.2.2 P-7 / IQ-27).
CANONICAL_MARKER = re.compile(
    r"\(v\d+\.\d+(?:\.\d+)? currency \d{4}-\d{2}-\d{2}·번복 아님·X3 안정성 클래스"
)

# §11.2 exception class: version/status identifier tokens that may be corrected
# in-place (e.g. "DRAFT v0.6" -> "DRAFT v0.9"). Body bytes outside the token must
# stay identical; decision reversions are NOT a token correction.
STATUS_TOKEN_RE = re.compile(r"(?:DRAFT\s+)?v\d+\.\d+(?:\.\d+)?")


def _is_subsequence(old: str, new: str) -> bool:
    """True if `old` is a subsequence of `new` — i.e. `new` only ADDS characters
    to `old` (no original character removed or changed). Pure-addition check."""
    it = iter(new)
    return all(ch in it for ch in old)


def _is_token_only_change(old: str, new: str) -> bool:
    """True if old and new differ ONLY inside §11.2 version/status tokens."""
    skel_old = STATUS_TOKEN_RE.sub("\x00V\x00", old)
    skel_new = STATUS_TOKEN_RE.sub("\x00V\x00", new)
    return skel_old == skel_new and old != new


def _line_change_allowed(old: str, new: str) -> bool:
    """A replaced line is allowed iff it is a pure intra-line addition
    (end-of-line / end-of-cell append) or a §11.2 token-only correction."""
    if old == new:
        return True
    return _is_subsequence(old, new) or _is_token_only_change(old, new)


def verify_append_only(before: str, after: str) -> tuple:
    """Model (나): allow equal / inserted lines / pure intra-line additions /
    §11.2 token corrections. Deny line deletions and body rewrites.

    See module LIMITATION note: structural enforcement only, not semantic.

    Returns (allowed: bool, reason: str)."""
    if before == after:
        return True, "no-op (identical)"

    a = before.splitlines(keepends=True)
    b = after.splitlines(keepends=True)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if tag == "insert":
            continue  # new lines (currency / new rows) are append-only by nature
        if tag == "delete":
            return False, f"line(s) removed at {i1}-{i2} (reversion/corruption)"
        if tag == "replace":
            old_block = a[i1:i2]
            new_block = b[j1:j2]
            if len(new_block) < len(old_block):
                return False, f"line(s) removed in replace at {i1}-{i2}"
            # Pair existing lines 1:1; surplus new lines are treated as inserts.
            for k in range(len(old_block)):
                if not _line_change_allowed(old_block[k], new_block[k]):
                    return False, (
                        f"body modified at line {i1 + k} "
                        "(not a tail-append nor a §11.2 token correction)"
                    )
            continue
    return True, "append-only (+ §11.2 token corrections)"
