"""Contract tests for P-7 tools.append_only."""

import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401
from tools import append_only


class AppendOnlyContract(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = str(Path(self._tmp.name) / "doc.md")
        Path(self.target).write_text("body\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_canonical_marker_accepted(self):
        rc = append_only.main([
            "--target", self.target, "--anchor", "a1", "--version", "v0.9.6",
            "--currency-text", "(v0.9.6 currency 2026-05-21·번복 아님·X3 안정성 클래스·x)",
        ])
        self.assertEqual(rc, 0)

    def test_non_canonical_rejected(self):
        rc = append_only.main([
            "--target", self.target, "--anchor", "a1", "--version", "v0.9.6",
            "--currency-text", "just some text",
        ])
        self.assertEqual(rc, 1)

    def test_version_token_must_be_present(self):
        rc = append_only.main([
            "--target", self.target, "--anchor", "a1", "--version", "v0.9.7",
            "--currency-text", "(v0.9.6 currency 2026-05-21·번복 아님·X3 안정성 클래스)",
        ])
        self.assertEqual(rc, 1)  # version v0.9.7 not in the text

    def test_missing_target_rejected(self):
        rc = append_only.main([
            "--target", "/no/such/file.md", "--version", "v0.9.6",
            "--currency-text", "(v0.9.6 currency 2026-05-21·번복 아님·X3 안정성 클래스)",
        ])
        self.assertEqual(rc, 1)

    def test_marker_regex_three_segment_version(self):
        self.assertTrue(append_only.CANONICAL_MARKER.search(
            "(v0.9.6 currency 2026-05-21·번복 아님·X3 안정성 클래스)"
        ))
        self.assertTrue(append_only.CANONICAL_MARKER.search(
            "(v0.4 currency 2026-05-20·번복 아님·X3 안정성 클래스)"
        ))

    def test_help_json_tool_name(self):
        self.assertEqual(append_only.HELP_JSON["tool"], "append_only")

    def test_trace_dict_present(self):
        self.assertEqual(append_only.TRACE["adapter_boundary_id"], "ADAPT-TOOL-append_only")


if __name__ == "__main__":
    unittest.main()
