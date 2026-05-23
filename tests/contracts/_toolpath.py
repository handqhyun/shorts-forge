"""Shared sys.path bootstrap for test_tools_* contract tests.

The deterministic tools live in impl/.claude/tools/. This helper puts impl/.claude/
on sys.path so the tests can `from tools import <name>`. Importing this module
(import _toolpath) has the side effect of extending sys.path.
"""

import pathlib
import sys

_CLAUDE_DIR = pathlib.Path(__file__).resolve().parents[2] / ".claude"
if str(_CLAUDE_DIR) not in sys.path:
    sys.path.insert(0, str(_CLAUDE_DIR))
