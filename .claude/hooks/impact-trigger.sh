#!/usr/bin/env bash
# Hook: PostToolUse Edit|Write (impl/src/**/*.py). Reference: workflow-coding.md §6.9 / §6.7 (P-10).
# F-5 resolution: 2-line wrapper delegating to tools.impact_trigger;
# no inline heredoc/grep/sed (previous v0.6 inline body removed).
set -euo pipefail
CLAUDE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec env PYTHONPATH="$CLAUDE_DIR" python3 -m tools.impact_trigger
