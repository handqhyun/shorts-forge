"""hook backing: PreToolUse Bash git commit -> pair check (§6.9).

Reference: prompt/workflow-coding.md sections 6.9, 6.7 (P-10 mapping), 13.5.6 (c)(d)(e).

Inspects the staged file set (git diff --cached --name-only) and enforces the
en/ko pair invariant: every staged *.en.md must have a sibling *.ko.md (staged or
on disk), and every staged *.ko.md must have a sibling *.en.md. Deterministic git
plumbing + filesystem check. strict mode -> exit 2 on violation (IQ-23 default).

Standard library only: argparse, json, subprocess, sys, pathlib.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import result

TRACE = {
    "module": "tools.pre_commit_pair_check",
    "imports": ["argparse", "json", "subprocess", "sys", "pathlib", "tools.result"],
    "imported_by": [],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-pre_commit_pair_check",
}

HELP_JSON = {
    "tool": "pre_commit_pair_check",
    "args": {
        "--staged": "str newline/comma list of staged files (default: git diff --cached)",
        "--repo": "str repo root for sibling existence checks (default: .)",
    },
}


def _staged_files(explicit, repo) -> list:
    if explicit:
        sep = "\n" if "\n" in explicit else ","
        return [s.strip() for s in explicit.split(sep) if s.strip()]
    try:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, cwd=repo,
        )
        return [s for s in out.stdout.splitlines() if s.strip()]
    except (OSError, subprocess.SubprocessError):
        return []


def _sibling(path: str, frm: str, to: str) -> str:
    return path[: -len(frm)] + to


def cmd(ns: argparse.Namespace) -> result.ToolResult:
    staged = _staged_files(ns.staged, ns.repo)
    staged_set = set(staged)
    repo = Path(ns.repo)
    violations = []
    for f in staged:
        if f.endswith(".en.md"):
            sib = _sibling(f, ".en.md", ".ko.md")
            if sib not in staged_set and not (repo / sib).is_file():
                violations.append({"path": f, "reason": "missing Korean sibling"})
        elif f.endswith(".ko.md"):
            sib = _sibling(f, ".ko.md", ".en.md")
            if sib not in staged_set and not (repo / sib).is_file():
                violations.append({"path": f, "reason": "korean translation orphan (no English original)"})
    return result.ok({"staged_count": len(staged), "violations": violations, "pair_ok": not violations})


def build_parser():
    p = argparse.ArgumentParser(prog="pre_commit_pair_check", description="en/ko pair commit guard")
    p.add_argument("--help-json", action="store_true")
    p.add_argument("--staged", default=None)
    p.add_argument("--repo", default=".")
    p.set_defaults(fn=cmd)
    return p


def main(argv=None) -> int:
    ns = build_parser().parse_args(argv)
    if getattr(ns, "help_json", False):
        sys.stdout.write(json.dumps(HELP_JSON, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    res = ns.fn(ns)
    code = result.emit(res)
    if res.status == "ok" and res.data.get("violations"):
        return 2  # strict mode (IQ-23 default)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
