"""Contract tests for N-2 tools.intent_prefilter."""

import unittest

import _toolpath  # noqa: F401
from tools import intent_prefilter


class IntentPrefilterContract(unittest.TestCase):
    def test_gate_clear(self):
        r = intent_prefilter.prefilter("D14 음악 결정")
        self.assertEqual(r["candidate_categories"], ["BLOCKING"])
        self.assertEqual(r["ambiguity_level"], "clear")

    def test_iq_infra_design(self):
        r = intent_prefilter.prefilter("IQ-20 검토")
        self.assertIn("[INFRA-DESIGN]", r["candidate_categories"])

    def test_multi_intent_needs_llm(self):
        r = intent_prefilter.prefilter("IQ-20 어떻게 진행할까?")
        self.assertEqual(r["ambiguity_level"], "multi-intent")
        self.assertTrue(r["needs_llm"])

    def test_undecidable_routes_to_bs(self):
        r = intent_prefilter.prefilter("zzzz")
        self.assertEqual(r["ambiguity_level"], "undecidable")
        self.assertTrue(r["route_to_blocking_surfacer"])

    def test_gate_word_boundary(self):
        # 'D170' must not match the D17 gate pattern.
        r = intent_prefilter.prefilter("the value D170 is large")
        self.assertNotIn("BLOCKING", r["candidate_categories"])

    def test_trace_help(self):
        self.assertEqual(intent_prefilter.TRACE["adapter_boundary_id"], "ADAPT-TOOL-intent_prefilter")
        self.assertEqual(intent_prefilter.HELP_JSON["tool"], "intent_prefilter")

    def test_decision_surface_echo_not_meta_via_why(self):
        # A full 4-option echo: "왜" is structural here, must not trigger meta-question.
        r = intent_prefilter.prefilter("핵심 A 왜 B 트레이드오프 C 다음 결과 D")
        self.assertNotIn("meta-question", r["candidate_categories"])

    def test_genuine_why_still_meta(self):
        # No full 4-option structure: "왜" remains a meta interrogative signal.
        r = intent_prefilter.prefilter("왜 이렇게 동작하는지 설명해줘")
        self.assertIn("meta-question", r["candidate_categories"])

    def test_decision_echo_with_other_meta_kw_still_meta(self):
        # "왜" suppressed, but an independent meta keyword ("?") still classifies meta.
        r = intent_prefilter.prefilter("핵심 A 왜 B 트레이드오프 C 다음 결과 D 어떻게?")
        self.assertIn("meta-question", r["candidate_categories"])


if __name__ == "__main__":
    unittest.main()
