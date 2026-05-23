"""Contract tests for P-4 tools.netguard_audit."""

import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401
from tools import netguard_audit


class NetguardContract(unittest.TestCase):
    def test_clean_tree_passes(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "ok.py").write_text("import json\nimport ast\n", encoding="utf-8")
            findings = netguard_audit.scan_imports(Path(d))
            self.assertEqual(findings, [])

    def test_forbidden_import_detected(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "bad.py").write_text("import requests\n", encoding="utf-8")
            findings = netguard_audit.scan_imports(Path(d))
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["import"], "requests")

    def test_from_import_detected(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "bad.py").write_text("from urllib import request\n", encoding="utf-8")
            findings = netguard_audit.scan_imports(Path(d))
            self.assertEqual(len(findings), 1)

    def test_tools_tree_is_clean(self):
        findings = netguard_audit.scan_imports(Path(_toolpath._CLAUDE_DIR) / "tools")
        self.assertEqual(findings, [])

    def test_trace_and_help(self):
        self.assertEqual(netguard_audit.TRACE["adapter_boundary_id"], "ADAPT-TOOL-netguard_audit")
        self.assertEqual(netguard_audit.HELP_JSON["tool"], "netguard_audit")


if __name__ == "__main__":
    unittest.main()
