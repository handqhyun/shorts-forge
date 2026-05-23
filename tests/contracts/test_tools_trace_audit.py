"""Contract tests for P-2 tools.trace_audit."""

import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401
from tools import trace_audit


GOOD = '''
TRACE = {
    "module": "x", "imports": [], "imported_by": [],
    "writes_state_keys": [], "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-x",
}
'''

INCOMPLETE = 'TRACE = {"module": "y"}\n'
NONE = 'x = 1\n'

# Imports os but does not declare it -> §14.1.2 #9 cross-check must flag it.
BAD_IMPORTS = '''
import os
TRACE = {
    "module": "z", "imports": [], "imported_by": [],
    "writes_state_keys": [], "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-z",
}
'''

# Declares exactly what it imports -> accurate.
GOOD_IMPORTS = '''
import os
import json
TRACE = {
    "module": "g", "imports": ["os", "json"], "imported_by": [],
    "writes_state_keys": [], "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-g",
}
'''


class TraceAuditContract(unittest.TestCase):
    def test_complete_trace_ok(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "a.py").write_text(GOOD, encoding="utf-8")
            r = trace_audit.cmd_audit(_ns(d))
            self.assertTrue(r.data["trace_ok"])

    def test_incomplete_trace_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "a.py").write_text(INCOMPLETE, encoding="utf-8")
            r = trace_audit.cmd_audit(_ns(d))
            self.assertFalse(r.data["trace_ok"])
            self.assertEqual(len(r.data["incomplete_trace"]), 1)

    def test_missing_trace_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "a.py").write_text(NONE, encoding="utf-8")
            r = trace_audit.cmd_audit(_ns(d))
            self.assertEqual(len(r.data["missing_trace"]), 1)

    def test_inaccurate_imports_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "a.py").write_text(BAD_IMPORTS, encoding="utf-8")
            r = trace_audit.cmd_audit(_ns(d))
            self.assertFalse(r.data["trace_ok"])
            self.assertEqual(len(r.data["inaccurate_imports"]), 1)
            self.assertIn("os", r.data["inaccurate_imports"][0]["actual_only"])

    def test_accurate_imports_pass(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "a.py").write_text(GOOD_IMPORTS, encoding="utf-8")
            r = trace_audit.cmd_audit(_ns(d))
            self.assertTrue(r.data["trace_ok"])
            self.assertEqual(r.data["inaccurate_imports"], [])

    def test_tools_tree_all_complete(self):
        r = trace_audit.cmd_audit(_ns(str(Path(_toolpath._CLAUDE_DIR) / "tools")))
        self.assertTrue(r.data["trace_ok"])
        self.assertGreaterEqual(r.data["audited_count"], 15)
        self.assertEqual(r.data["inaccurate_imports"], [])


def _ns(target):
    import argparse
    return argparse.Namespace(target=target, skip="__init__.py")


if __name__ == "__main__":
    unittest.main()
