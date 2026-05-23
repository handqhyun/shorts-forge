"""Contract tests for N-1 tools.code_review_lint."""

import argparse
import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401
from tools import code_review_lint


class CodeReviewLintContract(unittest.TestCase):
    def test_graceful_when_tools_absent(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "x.py")
            p.write_text("import json\n", encoding="utf-8")
            r = code_review_lint.cmd(argparse.Namespace(target=str(p)))
            # tools_available reports presence; lint_clean is True when a tool is absent
            self.assertIn("ruff", r.data["tools_available"])
            self.assertIn("mypy", r.data["tools_available"])
            self.assertIsInstance(r.data["lint_clean"], bool)

    def test_missing_target_raises(self):
        from tools import errors
        with self.assertRaises(errors.NotFoundError):
            code_review_lint.cmd(argparse.Namespace(target="/no/such/x.py"))

    def test_trace_help(self):
        self.assertEqual(code_review_lint.TRACE["adapter_boundary_id"], "ADAPT-TOOL-code_review_lint")
        self.assertEqual(code_review_lint.HELP_JSON["tool"], "code_review_lint")


if __name__ == "__main__":
    unittest.main()
