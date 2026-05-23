#!/usr/bin/env bash
# Hook: PostToolUse Edit|Write (*.en.md). Reference: workflow-coding.md §6.8 / §6.7 (P-10).
# F-5 resolution: 2-line wrapper delegating to tools.korean_translator_trigger;
# no inline heredoc/grep/sed (previous v0.6 inline body removed).
set -euo pipefail
CLAUDE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec env PYTHONPATH="$CLAUDE_DIR" python3 -m tools.korean_translator_trigger
