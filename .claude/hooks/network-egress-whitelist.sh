#!/usr/bin/env bash
# Hook: PreToolUse Bash. Reference: workflow-coding.md §6.4 / §6.7 (P-10).
# Reads command from the hook-input JSON on stdin; deny => exit 2 (INVARIANT #1).
set -euo pipefail
CLAUDE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec env PYTHONPATH="$CLAUDE_DIR" python3 -m tools.netguard_pretool --stdin
