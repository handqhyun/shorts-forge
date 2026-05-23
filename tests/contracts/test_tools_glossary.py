"""Contract tests for P-6 tools.glossary."""

import argparse
import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401
from tools import glossary


def _ns(mode, pairs, store):
    return argparse.Namespace(mode=mode, term_pairs=pairs, store=store)


class GlossaryContract(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = str(Path(self._tmp.name) / "g.json")

    def tearDown(self):
        self._tmp.cleanup()

    def test_append_then_lookup(self):
        glossary.cmd(_ns("append", '[{"en_term":"a","ko_term":"가"}]', self.store))
        r = glossary.cmd(_ns("lookup", '[{"en_term":"a","ko_term":"가"}]', self.store))
        self.assertIn("a", r.data["matched"])

    def test_drift_detected(self):
        glossary.cmd(_ns("append", '[{"en_term":"a","ko_term":"가"}]', self.store))
        r = glossary.cmd(_ns("check-drift", '[{"en_term":"a","ko_term":"나"}]', self.store))
        self.assertEqual(r.data["drift_count"], 1)

    def test_no_drift_same_term(self):
        glossary.cmd(_ns("append", '[{"en_term":"a","ko_term":"가"}]', self.store))
        r = glossary.cmd(_ns("check-drift", '[{"en_term":"a","ko_term":"가"}]', self.store))
        self.assertEqual(r.data["drift_count"], 0)

    def test_frozen_rejects_append(self):
        Path(self.store).write_text('{"frozen": true, "entries": []}', encoding="utf-8")
        r = glossary.cmd(_ns("append", '[{"en_term":"a","ko_term":"가"}]', self.store))
        self.assertEqual(r.data["appended"], [])
        self.assertEqual(r.data["rejected_post_freeze"], ["a"])

    def test_trace_help(self):
        self.assertEqual(glossary.TRACE["adapter_boundary_id"], "ADAPT-TOOL-glossary")
        self.assertEqual(glossary.HELP_JSON["tool"], "glossary")


if __name__ == "__main__":
    unittest.main()
