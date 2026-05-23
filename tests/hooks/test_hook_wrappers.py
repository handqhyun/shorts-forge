"""A-4 Hook integration — drives the actual .claude/hooks/*.sh wrappers via
subprocess (stdin JSON -> exit code), covering the bash->python boundary that
the pure-Python tool contract tests never exercise.

Reference: workflow-coding.md sections 6.1-6.9 (P-10 wrappers) ;
[[project-build-execution]] B-5 (sot-guardian stdin->diff path had 0 automated
coverage, manual E2E only) ; ANCHOR (1) no sampling.

Isolation (ANCHOR (2)): every invocation runs with cwd set to a throwaway
sandbox and passes only tmp file paths. The real SOT (prompt/PRD.md,
prompt/workflow.md) and the real build_state.sqlite are never read or written --
the DB tools resolve a relative default that does not exist under the sandbox,
and the SOT-axis deny test builds a decoy <tmp>/prompt/PRD.md.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

_HOOKS = Path(__file__).resolve().parents[2] / ".claude" / "hooks"


def _run(hook_name: str, stdin_obj, cwd: Path):
    hook = _HOOKS / hook_name
    assert hook.exists(), f"hook missing: {hook}"
    payload = "" if stdin_obj is None else json.dumps(stdin_obj)
    return subprocess.run(
        ["bash", str(hook)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        timeout=30,
    )


# ---- sot-guardian-block.sh (PreToolUse Edit|Write -> deny == exit 2) --------

def _sot_decoy(tmp_path: Path) -> Path:
    """A throwaway file whose path ENDS WITH prompt/PRD.md so _is_sot_axis()
    matches, while pointing at tmp (never the real SOT)."""
    d = tmp_path / "prompt"
    d.mkdir()
    f = d / "PRD.md"
    f.write_text("line one\nline two\nline three\n", encoding="utf-8")
    return f


def test_sot_guardian_denies_body_modification(tmp_path):
    f = _sot_decoy(tmp_path)
    stdin = {"tool_name": "Write",
             "tool_input": {"file_path": str(f),
                            "content": "line one\nMUTATED\nline three\n"}}
    r = _run("sot-guardian-block.sh", stdin, cwd=tmp_path)
    assert r.returncode == 2, r.stderr


def test_sot_guardian_allows_pure_append(tmp_path):
    f = _sot_decoy(tmp_path)
    appended = f.read_text(encoding="utf-8") + "line four appended\n"
    stdin = {"tool_name": "Write",
             "tool_input": {"file_path": str(f), "content": appended}}
    r = _run("sot-guardian-block.sh", stdin, cwd=tmp_path)
    assert r.returncode == 0, r.stderr


def test_sot_guardian_allows_non_sot_file(tmp_path):
    f = tmp_path / "scratch.py"
    f.write_text("x = 1\n", encoding="utf-8")
    stdin = {"tool_name": "Write",
             "tool_input": {"file_path": str(f), "content": "x = 2\n"}}
    r = _run("sot-guardian-block.sh", stdin, cwd=tmp_path)
    assert r.returncode == 0, r.stderr


def test_sot_guardian_fail_closed_when_no_content(tmp_path):
    f = _sot_decoy(tmp_path)
    stdin = {"tool_name": "Write", "tool_input": {"file_path": str(f)}}
    r = _run("sot-guardian-block.sh", stdin, cwd=tmp_path)
    assert r.returncode == 2, r.stderr


# ---- network-egress-whitelist.sh (PreToolUse Bash -> deny == exit 2) --------

@pytest.mark.parametrize("cmd", ["curl http://example.com",
                                 "pip install requests",
                                 "wget https://x/y"])
def test_netguard_denies_egress(tmp_path, cmd):
    stdin = {"tool_name": "Bash", "tool_input": {"command": cmd}}
    r = _run("network-egress-whitelist.sh", stdin, cwd=tmp_path)
    assert r.returncode == 2, f"expected deny for {cmd!r}: {r.stderr}"


@pytest.mark.parametrize("cmd", ["ls -la", "python3 -m pytest tests/"])
def test_netguard_allows_non_egress(tmp_path, cmd):
    stdin = {"tool_name": "Bash", "tool_input": {"command": cmd}}
    r = _run("network-egress-whitelist.sh", stdin, cwd=tmp_path)
    assert r.returncode == 0, f"expected allow for {cmd!r}: {r.stderr}"


# ---- trigger / lifecycle hooks: graceful exit 0 in an empty sandbox ---------
# DB-absent path (relative DEFAULT_DB does not exist under the sandbox cwd) ->
# every trigger must defer/no-op without error.

@pytest.mark.parametrize("hook", [
    "korean-translator-trigger.sh",
    "impact-trigger.sh",
    "persist-pending-decisions.sh",
    "load-context-from-sot.sh",
    "sot-guardian-integrity-check.sh",
])
def test_trigger_hooks_graceful_in_sandbox(tmp_path, hook):
    stdin = {"tool_name": "Write", "tool_input": {"file_path": str(tmp_path / "x.en.md")}}
    r = _run(hook, stdin, cwd=tmp_path)
    assert r.returncode == 0, f"{hook} non-zero in sandbox: {r.stderr}"
