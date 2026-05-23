#!/usr/bin/env bash
# Hook: PreToolUse Edit|Write. Reference: workflow-coding.md §6.3 / §6.7 (P-10).
# Reads file_path/tool_name from the hook-input JSON on stdin; deny => exit 2.
set -euo pipefail
CLAUDE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec env PYTHONPATH="$CLAUDE_DIR" python3 -m tools.sot_guardian --pre-tool-use --stdin
