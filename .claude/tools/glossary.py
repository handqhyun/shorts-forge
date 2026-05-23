"""P-6: glossary-lookup CLI (English->Korean term consistency).

Reference: prompt/workflow-coding.md sections 5.3.7 (P-6), 13.5.8.1 (Stage C freeze).

Read-write single path to impl/.claude/state/glossary.json. Append-only after the
Stage C freeze (frozen=true). Computes glossary_drift by comparing en->ko pairings
against the accepted history. Deterministic: JSON + exact-match hashing, LLM 0.

Standard library only: argparse, json, sys, pathlib.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import errors, result

TRACE = {
    "module": "tools.glossary",
    "imports": ["argparse", "json", "sys", "pathlib", "tools.errors", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-glossary",
}

DEFAULT_STORE = "impl/.claude/state/glossary.json"

HELP_JSON = {
    "tool": "glossary",
    "args": {
        "--mode": "enum('lookup','append','check-drift') (required)",
        "--term-pairs": "str JSON list of {en_term,ko_term,source_pair_row_id}",
        "--store": f"str glossary store path (default: {DEFAULT_STORE})",
    },
}


def _load_store(path: Path) -> dict:
    if not path.is_file():
        return {"frozen": False, "entries": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise errors.ValidationError(f"glossary store not valid JSON: {exc}") from exc
    data.setdefault("frozen", False)
    data.setdefault("entries", [])
    return data


def _save_store(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _parse_pairs(raw: str) -> list:
    if not raw:
        return []
    try:
        pairs = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise errors.ValidationError(f"--term-pairs not valid JSON: {exc}") from exc
    if not isinstance(pairs, list):
        raise errors.ValidationError("--term-pairs must be a JSON list")
    return pairs


def _index(entries: list) -> dict:
    """en_term -> set of ko_terms seen historically."""

    idx = {}
    for e in entries:
        idx.setdefault(e["en_term"], set()).add(e["ko_term"])
    return idx


def cmd(ns: argparse.Namespace) -> result.ToolResult:
    if ns.mode not in ("lookup", "append", "check-drift"):
        raise errors.ValidationError("--mode must be lookup|append|check-drift")
    store_path = Path(ns.store)
    store = _load_store(store_path)
    pairs = _parse_pairs(ns.term_pairs)
    idx = _index(store["entries"])

    if ns.mode == "lookup":
        matched, missing = [], []
        for p in pairs:
            (matched if p["en_term"] in idx else missing).append(p["en_term"])
        return result.ok({"matched": matched, "missing": missing})

    if ns.mode == "check-drift":
        drift_pairs = []
        for p in pairs:
            history = idx.get(p["en_term"], set())
            if history and p["ko_term"] not in history:
                drift_pairs.append(
                    {
                        "en_term": p["en_term"],
                        "ko_terms_history": sorted(history),
                        "ko_term_now": p["ko_term"],
                    }
                )
        return result.ok({"drift_count": len(drift_pairs), "drift_pairs": drift_pairs})

    # append
    if store["frozen"]:
        return result.ok(
            {
                "appended": [],
                "rejected_post_freeze": [p["en_term"] for p in pairs],
                "note": "glossary frozen (Stage C); ADR append required for new terms",
            }
        )
    appended = []
    for p in pairs:
        store["entries"].append(
            {
                "en_term": p["en_term"],
                "ko_term": p["ko_term"],
                "source_pair_row_id": p.get("source_pair_row_id"),
            }
        )
        appended.append(p["en_term"])
    _save_store(store_path, store)
    return result.ok({"appended": appended, "rejected_post_freeze": []})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="glossary", description="glossary lookup/append/drift")
    parser.add_argument("--help-json", action="store_true")
    parser.add_argument("--mode")
    parser.add_argument("--term-pairs", default="")
    parser.add_argument("--store", default=DEFAULT_STORE)
    parser.set_defaults(fn=cmd)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    if not ns.mode:
        parser.print_help(sys.stderr)
        return 2
    return result.run_guarded(lambda: ns.fn(ns))


if __name__ == "__main__":
    raise SystemExit(main())
