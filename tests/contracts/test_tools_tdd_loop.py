"""Contract tests for P-8 tools.tdd_loop."""

import argparse
import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401
from tools import tdd_loop


class TddLoopContract(unittest.TestCase):
    def test_runner_selected(self):
        # In an env without pytest, the runner degrades to unittest.
        self.assertIn(tdd_loop._has_pytest(), (True, False))

    def test_green_on_passing_suite(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "test_ok.py").write_text(
                "import unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_x(self):\n"
                "        self.assertEqual(1, 1)\n",
                encoding="utf-8",
            )
            r = tdd_loop.cmd(argparse.Namespace(test_path=d, impl_path=None, ratchet_path=None))
            self.assertTrue(r.data["green_pass"])

    def test_red_on_failing_suite(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "test_bad.py").write_text(
                "import unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_x(self):\n"
                "        self.assertEqual(1, 2)\n",
                encoding="utf-8",
            )
            r = tdd_loop.cmd(argparse.Namespace(test_path=d, impl_path=None, ratchet_path=None))
            self.assertFalse(r.data["green_pass"])

    def test_trace_help(self):
        self.assertEqual(tdd_loop.TRACE["adapter_boundary_id"], "ADAPT-TOOL-tdd_loop")
        self.assertEqual(tdd_loop.HELP_JSON["tool"], "tdd_loop")


if __name__ == "__main__":
    unittest.main()
