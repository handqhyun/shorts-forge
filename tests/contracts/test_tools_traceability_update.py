"""Contract tests for P-9 tools.traceability_update."""

import argparse
import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401
from tools import traceability_update, errors


GOOD = '''
TRACE = {
    "module": "x", "imports": [], "imported_by": [],
    "writes_state_keys": [], "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-x",
}
'''


class TraceabilityUpdateContract(unittest.TestCase):
    def test_valid_module_preview_only(self):
        with tempfile.TemporaryDirectory() as d:
            m = Path(d, "m.py")
            m.write_text(GOOD, encoding="utf-8")
            r = traceability_update.cmd(argparse.Namespace(module=str(m), currency="c"))
            self.assertTrue(r.data["trace_ok"])
            self.assertFalse(r.data["wrote"])  # never writes SOT axis directly

    def test_missing_trace_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            m = Path(d, "m.py")
            m.write_text("x = 1\n", encoding="utf-8")
            with self.assertRaises(errors.ValidationError):
                traceability_update.cmd(argparse.Namespace(module=str(m), currency="c"))

    def test_target_is_sot_axis(self):
        self.assertEqual(traceability_update.SOT_TRACEABILITY, "prompt/impl/docs/TRACEABILITY.md")

    def test_trace_help(self):
        self.assertEqual(traceability_update.TRACE["adapter_boundary_id"], "ADAPT-TOOL-traceability_update")
        self.assertEqual(traceability_update.HELP_JSON["tool"], "traceability_update")


if __name__ == "__main__":
    unittest.main()
