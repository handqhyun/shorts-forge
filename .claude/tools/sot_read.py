"""P-1: SOT single parser CLI (PRD / workflow / final-research).

Reference: prompt/workflow-coding.md sections 5.1.1, 5.1.2, 5.1.3 (P-1).

The single source of truth for reading the SOT four axes. No subagent reads the
SOT markdown directly; they all call this CLI, which extracts a section verbatim
by header regex. Deterministic: same file bytes + same section ref -> same output.

Subcommands are expressed via --source:
    --source PRD            read prompt/PRD.md
    --source workflow       read prompt/workflow.md
    --source final-research read prompt/prd-research/final-research.md

Selection:
    --section "§12-D17"     extract the section whose header contains this token
    --axis "AX-CRAFT"       (final-research only) extract a 【AX-*】 axis block

Standard library only: argparse, json, re, sys, pathlib.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from . import errors, result

TRACE = {
    "module": "tools.sot_read",
    "imports": ["argparse", "json", "re", "sys", "pathlib", "tools.errors", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-sot_read",
}

SOURCE_FILES = {
    "PRD": "PRD.md",
    "workflow": "workflow.md",
    "final-research": "prd-research/final-research.md",
}

HELP_JSON = {
    "tool": "sot_read",
    "args": {
        "--source": f"enum{tuple(SOURCE_FILES)}",
        "--section": "str header token (e.g. '§12-D17')",
        "--axis": "str axis token, final-research only (e.g. 'AX-CRAFT')",
        "--root": "str SOT root dir override (default: auto-detect)",
    },
}

# Markdown ATX header line, level 1-6.
_HEADER_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def find_sot_root(override: str | None) -> Path:
    if override:
        root = Path(override)
        if not (root / "PRD.md").is_file():
            raise errors.NotFoundError(f"PRD.md not found under --root {override}")
        return root
    # Auto-detect: walk up from this module until a dir holds both PRD.md and workflow.md.
    for parent in Path(__file__).resolve().parents:
        if (parent / "PRD.md").is_file() and (parent / "workflow.md").is_file():
            return parent
    raise errors.NotFoundError("SOT root not found (no dir with PRD.md + workflow.md)")


def extract_section(text: str, token: str) -> str:
    """Return the section identified by `token`.

    Two modes, tried in order:
    1. ATX-header mode: a `#`-level header line containing `token`; the slice runs
       to the next header of the same or higher level (verbatim).
    2. Table-row / line mode: if no header matches, the token's last dash segment
       (e.g. 'D17' from '§12-D17') is matched as a whole word against non-header
       lines; the first matching line is returned verbatim (covers PRD §12 gate
       rows and other table-cell sections per §5.1.1)."""

    lines = text.splitlines()
    start = None
    start_level = None
    for i, line in enumerate(lines):
        m = _HEADER_RE.match(line)
        if m and token in line:
            start = i
            start_level = len(m.group(1))
            break
    if start is not None:
        end = len(lines)
        for j in range(start + 1, len(lines)):
            m = _HEADER_RE.match(lines[j])
            if m and len(m.group(1)) <= start_level:
                end = j
                break
        return "\n".join(lines[start:end])

    # Fallback: table-row / line mode.
    sub = token.split("-")[-1] if "-" in token else token
    # (a) Prefer a markdown table row whose first cell is exactly `sub`
    #     (e.g. '| D17 | ...'), which uniquely identifies a gate/registry row.
    row_re = re.compile(r"^\s*\|\s*" + re.escape(sub) + r"\s*\|")
    for line in lines:
        if row_re.match(line):
            return line
    # (b) Otherwise, the first non-header line containing `sub` as a whole word.
    word_re = re.compile(r"(?<![0-9A-Za-z])" + re.escape(sub) + r"(?![0-9A-Za-z])")
    for line in lines:
        if _HEADER_RE.match(line):
            continue
        if word_re.search(line):
            return line
    raise errors.NotFoundError(
        f"no header or table row matching {token!r} (tried header, table-row, word {sub!r})"
    )


def extract_axis(text: str, axis_token: str) -> str:
    """Extract a 【AX-*】 axis block from final-research (verbatim until next 【)."""

    marker = f"【{axis_token}】" if not axis_token.startswith("【") else axis_token
    idx = text.find(marker)
    if idx == -1:
        # Allow passing the bare token that appears inside the brackets.
        m = re.search(r"【\s*" + re.escape(axis_token) + r"[^】]*】", text)
        if not m:
            raise errors.NotFoundError(f"axis marker for {axis_token!r} not found")
        idx = m.start()
    nxt = text.find("【", idx + 1)
    end = nxt if nxt != -1 else len(text)
    return text[idx:end].rstrip()


def cmd_read(ns: argparse.Namespace) -> result.ToolResult:
    if ns.source not in SOURCE_FILES:
        raise errors.ValidationError(
            f"--source must be one of {tuple(SOURCE_FILES)}, got {ns.source!r}"
        )
    if not ns.section and not ns.axis:
        raise errors.UsageError("one of --section or --axis is required")
    if ns.axis and ns.source != "final-research":
        raise errors.UsageError("--axis is only valid for --source final-research")

    root = find_sot_root(ns.root)
    path = root / SOURCE_FILES[ns.source]
    if not path.is_file():
        raise errors.NotFoundError(f"SOT file not found: {path}")
    text = path.read_text(encoding="utf-8")

    if ns.axis:
        body = extract_axis(text, ns.axis)
        selector = {"axis": ns.axis}
    else:
        body = extract_section(text, ns.section)
        selector = {"section": ns.section}

    return result.ok(
        {
            "source": ns.source,
            "path": str(path),
            "selector": selector,
            "body": body,
            "byte_len": len(body.encode("utf-8")),
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sot_read", description="SOT single parser CLI")
    parser.add_argument("--help-json", action="store_true", help="print machine-readable schema")
    parser.add_argument("--source")
    parser.add_argument("--section", default=None)
    parser.add_argument("--axis", default=None)
    parser.add_argument("--root", default=None)
    parser.set_defaults(fn=cmd_read)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    if not ns.source:
        parser.print_help(sys.stderr)
        return 2
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
