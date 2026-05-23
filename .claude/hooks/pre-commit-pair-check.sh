#!/usr/bin/env bash
# Hook: PreToolUse Bash (git commit). Reference: workflow-coding.md §6.9 / §6.7 (P-10).
# Strict mode (IQ-23 default): pair violation => exit 2 blocks the commit.
set -euo pipefail
CLAUDE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec env PYTHONPATH="$CLAUDE_DIR" python3 -m tools.pre_commit_pair_check
