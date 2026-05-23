"""Contract tests for N-3 tools.translatability_precheck."""

import unittest

import _toolpath  # noqa: F401
from tools import translatability_precheck as tp


class PrecheckContract(unittest.TestCase):
    def test_normal_passes(self):
        r = tp.precheck("Normal English with §4.2 ref and [GATE:D14].", "subagent-output")
        self.assertEqual(r["verdict"], "pass")

    def test_unbalanced_fence_fails(self):
        r = tp.precheck("```python\ncode without closing fence", "subagent-output")
        self.assertEqual(r["verdict"], "fail")
        self.assertIn("code_block_unbalanced", r["failed_axes"])

    def test_balanced_fence_passes(self):
        r = tp.precheck("```python\ncode\n```\n", "subagent-output")
        self.assertEqual(r["verdict"], "pass")

    def test_currency_marker_required(self):
        r = tp.precheck("no marker here", "currency-marker")
        self.assertEqual(r["verdict"], "fail")
        self.assertIn("currency_marker_malformed", r["failed_axes"])

    def test_currency_marker_present(self):
        r = tp.precheck("(v0.9.6 currency 2026-05-21·번복 아님·X3 안정성 클래스)", "currency-marker")
        self.assertEqual(r["verdict"], "pass")

    def test_four_option_incomplete_fails(self):
        r = tp.precheck("핵심: x 왜: y", "4-option-decision-surface")
        self.assertEqual(r["verdict"], "fail")

    def test_four_option_complete_passes(self):
        r = tp.precheck("핵심 왜 트레이드오프 다음 결과", "4-option-decision-surface")
        self.assertEqual(r["verdict"], "pass")

    def test_trace_help(self):
        self.assertEqual(tp.TRACE["adapter_boundary_id"], "ADAPT-TOOL-translatability_precheck")
        self.assertEqual(tp.HELP_JSON["tool"], "translatability_precheck")

    def test_wellformed_identifiers_pass(self):
        r = tp.precheck("Refs §4.3.5, IQ-17, ADAPT-S1-IN, [GATE:D14].", "subagent-output")
        self.assertEqual(r["verdict"], "pass")
        self.assertTrue(r["identifier_integrity_ok"])

    def test_malformed_section_ref_fails(self):
        r = tp.precheck("see § with no number", "subagent-output")
        self.assertEqual(r["verdict"], "fail")
        self.assertIn("malformed_section_ref", r["failed_axes"])
        self.assertFalse(r["identifier_integrity_ok"])

    def test_malformed_iq_ref_fails(self):
        r = tp.precheck("resolved in IQ- soon", "subagent-output")
        self.assertEqual(r["verdict"], "fail")
        self.assertIn("malformed_iq_ref", r["failed_axes"])

    def test_malformed_adapter_ref_fails(self):
        r = tp.precheck("crosses ADAPT- boundary", "subagent-output")
        self.assertEqual(r["verdict"], "fail")
        self.assertIn("malformed_adapter_ref", r["failed_axes"])


if __name__ == "__main__":
    unittest.main()
