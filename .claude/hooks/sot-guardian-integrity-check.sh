#!/usr/bin/env bash
# Hook: SessionStart. Reference: workflow-coding.md §6.1 / §6.7 (P-10 2-line wrapper).
# Body delegates to deterministic tools; no inline grep/awk/sed.
set -euo pipefail
CLAUDE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env PYTHONPATH="$CLAUDE_DIR" python3 -m tools.sot_checksum --mode check || true
exec env PYTHONPATH="$CLAUDE_DIR" python3 -m tools.translation_queue --mode check
