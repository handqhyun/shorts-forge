#!/usr/bin/env bash
# Hook: Stop. Reference: workflow-coding.md §6.6 / §6.7 (P-10).
set -euo pipefail
CLAUDE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec env PYTHONPATH="$CLAUDE_DIR" python3 -m tools.persist_pending_decisions
