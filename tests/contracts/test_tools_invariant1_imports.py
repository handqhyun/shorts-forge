"""INVARIANT #1 enforcement on the build tooling itself.

Reference: prompt/workflow-coding.md §4.2.6 Exit contract (d), §5.3.2 (P-4),
§15.1.8 종료 조건 (d). The deterministic tools that build the project must
themselves contain zero forbidden network imports — a single network import in
the tool layer would be an RLM (INVARIANT #1) breach. This runs the same
AST scan (tools.netguard_audit) the gate uses, pointed at tools/.
"""

import unittest
from pathlib import Path

import _toolpath  # noqa: F401  (sys.path bootstrap side effect)
from tools import netguard_audit

TOOLS_DIR = Path(_toolpath._CLAUDE_DIR) / "tools"


class Invariant1ImportsContract(unittest.TestCase):
    def test_tools_tree_has_no_forbidden_imports(self):
        findings = netguard_audit.scan_imports(TOOLS_DIR)
        self.assertEqual(findings, [], f"forbidden imports in tool layer: {findings}")

    def test_scan_is_deterministic(self):
        a = netguard_audit.scan_imports(TOOLS_DIR)
        b = netguard_audit.scan_imports(TOOLS_DIR)
        self.assertEqual(a, b)

    def test_scan_detects_a_forbidden_import(self):
        # Negative control: an injected forbidden import must be caught, proving
        # the empty result above is a real pass and not a silent no-op.
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "leak.py"
            p.write_text("import requests\n", encoding="utf-8")
            findings = netguard_audit.scan_imports(Path(d))
            self.assertTrue(any(f["import"] == "requests" for f in findings))


if __name__ == "__main__":
    unittest.main()
