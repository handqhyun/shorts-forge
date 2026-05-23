"""Contract tests for hook-backing tools.sot_checksum (§6.1 SessionStart)."""

import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401  (sys.path bootstrap side effect)
from tools import sot_checksum, errors


class SotChecksumContract(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "PRD.md").write_text("prd body\n", encoding="utf-8")
        (self.root / "workflow.md").write_text("workflow body\n", encoding="utf-8")
        self.store = str(self.root / "sot-checksums.json")

    def tearDown(self):
        self._tmp.cleanup()

    def _ns(self, mode):
        return sot_checksum.build_parser().parse_args(
            ["--mode", mode, "--root", str(self.root), "--store", self.store]
        )

    def test_store_then_check_integrity_ok(self):
        self.assertTrue(sot_checksum.cmd(self._ns("store")).data["stored"])
        data = sot_checksum.cmd(self._ns("check")).data
        self.assertTrue(data["integrity_ok"])
        self.assertEqual(data["mismatches"], [])

    def test_check_detects_mismatch_after_edit(self):
        sot_checksum.cmd(self._ns("store"))
        (self.root / "PRD.md").write_text("prd body MUTATED\n", encoding="utf-8")
        data = sot_checksum.cmd(self._ns("check")).data
        self.assertFalse(data["integrity_ok"])
        self.assertIn("PRD.md", data["mismatches"])

    def test_check_without_baseline(self):
        data = sot_checksum.cmd(self._ns("check")).data
        self.assertFalse(data["baseline_present"])

    def test_bad_mode_rejected(self):
        ns = sot_checksum.build_parser().parse_args(
            ["--mode", "wipe", "--root", str(self.root), "--store", self.store]
        )
        with self.assertRaises(errors.ValidationError):
            sot_checksum.cmd(ns)

    def test_deterministic_same_input_same_output(self):
        sot_checksum.cmd(self._ns("store"))
        a = sot_checksum.cmd(self._ns("check")).data
        b = sot_checksum.cmd(self._ns("check")).data
        self.assertEqual(a, b)

    def test_help_json_tool_name(self):
        self.assertEqual(sot_checksum.HELP_JSON["tool"], "sot_checksum")

    def test_trace_dict_present(self):
        self.assertEqual(sot_checksum.TRACE["adapter_boundary_id"], "ADAPT-TOOL-sot_checksum")


if __name__ == "__main__":
    unittest.main()
