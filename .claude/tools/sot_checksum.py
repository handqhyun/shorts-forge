"""hook backing: SOT four-axis checksum store/check (§6.1 SessionStart).

Reference: prompt/workflow-coding.md sections 6.1, 6.7 (P-10 mapping).

Computes SHA-256 over each SOT axis and compares against a stored baseline.
On mismatch, the SessionStart hook surfaces a corruption warning. Deterministic.

Standard library only: argparse, hashlib, json, sys, pathlib.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from . import errors, result

TRACE = {
    "module": "tools.sot_checksum",
    "imports": ["argparse", "hashlib", "json", "sys", "pathlib", "tools.errors", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-sot_checksum",
}

SOT_AXES = (
    "PRD.md",
    "workflow.md",
    "prd-research/final-research.md",
    "impl/docs/TRACEABILITY.md",
)
DEFAULT_STORE = "impl/.claude/state/sot-checksums.json"

HELP_JSON = {
    "tool": "sot_checksum",
    "args": {
        "--mode": "enum('store','check') (required)",
        "--root": "str SOT root (auto-detect if omitted)",
        "--store": f"str checksum store path (default: {DEFAULT_STORE})",
    },
}


def _find_root(override):
    if override:
        return Path(override)
    for parent in Path(__file__).resolve().parents:
        if (parent / "PRD.md").is_file() and (parent / "workflow.md").is_file():
            return parent
    raise errors.NotFoundError("SOT root not found")


def _digests(root: Path) -> dict:
    out = {}
    for axis in SOT_AXES:
        p = root / axis
        out[axis] = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    return out


def cmd(ns: argparse.Namespace) -> result.ToolResult:
    if ns.mode not in ("store", "check"):
        raise errors.ValidationError("--mode must be store|check")
    root = _find_root(ns.root)
    current = _digests(root)
    store_path = Path(ns.store)

    if ns.mode == "store":
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store_path.write_text(json.dumps(current, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return result.ok({"stored": True, "axes": list(current)})

    if not store_path.is_file():
        return result.ok({"baseline_present": False, "mismatches": [], "note": "no baseline; run store first"})
    baseline = json.loads(store_path.read_text(encoding="utf-8"))
    mismatches = [a for a in SOT_AXES if baseline.get(a) != current.get(a)]
    return result.ok({"baseline_present": True, "mismatches": mismatches, "integrity_ok": not mismatches})


def build_parser():
    p = argparse.ArgumentParser(prog="sot_checksum", description="SOT checksum store/check")
    p.add_argument("--help-json", action="store_true")
    p.add_argument("--mode")
    p.add_argument("--root", default=None)
    p.add_argument("--store", default=DEFAULT_STORE)
    p.set_defaults(fn=cmd)
    return p


def main(argv=None) -> int:
    ns = build_parser().parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    if not ns.mode:
        build_parser().print_help(sys.stderr)
        return 2
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
