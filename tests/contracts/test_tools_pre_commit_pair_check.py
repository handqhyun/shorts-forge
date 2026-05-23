"""Contract tests for hook-backing tools.pre_commit_pair_check (§6.9, §13.5.6)."""

import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401  (sys.path bootstrap side effect)
from tools import pre_commit_pair_check as pc


class PreCommitPairCheckContract(unittest.TestCase):
    def _ns(self, staged, repo="."):
        return pc.build_parser().parse_args(["--staged", staged, "--repo", repo])

    def test_en_without_ko_sibling_violation(self):
        with tempfile.TemporaryDirectory() as d:
            data = pc.cmd(self._ns("docs/a.en.md", d)).data
            self.assertFalse(data["pair_ok"])
            self.assertEqual(data["violations"][0]["reason"], "missing Korean sibling")

    def test_both_staged_ok(self):
        with tempfile.TemporaryDirectory() as d:
            data = pc.cmd(self._ns("docs/a.en.md\ndocs/a.ko.md", d)).data
            self.assertTrue(data["pair_ok"])

    def test_ko_orphan_violation(self):
        with tempfile.TemporaryDirectory() as d:
            data = pc.cmd(self._ns("docs/a.ko.md", d)).data
            self.assertFalse(data["pair_ok"])
            self.assertIn("orphan", data["violations"][0]["reason"])

    def test_sibling_on_disk_satisfies(self):
        with tempfile.TemporaryDirectory() as d:
            sib = Path(d) / "docs" / "a.ko.md"
            sib.parent.mkdir(parents=True)
            sib.write_text("ko\n", encoding="utf-8")
            data = pc.cmd(self._ns("docs/a.en.md", d)).data
            self.assertTrue(data["pair_ok"])

    def test_deterministic_same_input_same_output(self):
        with tempfile.TemporaryDirectory() as d:
            a = pc.cmd(self._ns("docs/a.en.md", d)).data
            b = pc.cmd(self._ns("docs/a.en.md", d)).data
            self.assertEqual(a, b)

    def test_help_json_tool_name(self):
        self.assertEqual(pc.HELP_JSON["tool"], "pre_commit_pair_check")

    def test_trace_dict_present(self):
        self.assertEqual(pc.TRACE["adapter_boundary_id"], "ADAPT-TOOL-pre_commit_pair_check")


if __name__ == "__main__":
    unittest.main()
