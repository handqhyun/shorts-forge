"""Contract tests for N-4 tools.sot_guardian."""

import unittest

import _toolpath  # noqa: F401
from tools import sot_guardian


class SotGuardianContract(unittest.TestCase):
    def test_sot_axis_denied(self):
        self.assertTrue(sot_guardian._is_sot_axis("prompt/PRD.md"))
        self.assertTrue(sot_guardian._is_sot_axis("prompt/workflow.md"))
        self.assertTrue(sot_guardian._is_sot_axis("prompt/impl/docs/TRACEABILITY.md"))

    def test_non_sot_allowed(self):
        self.assertFalse(sot_guardian._is_sot_axis("impl/src/foo.py"))
        self.assertFalse(sot_guardian._is_sot_axis("prompt/workflow-coding.md"))

    def test_canonical_marker_matches(self):
        self.assertTrue(sot_guardian.CANONICAL_MARKER.search(
            "(v0.9.6 currency 2026-05-21·번복 아님·X3 안정성 클래스)"
        ))

    def test_non_marker_no_match(self):
        self.assertIsNone(sot_guardian.CANONICAL_MARKER.search("just text"))

    def test_main_deny_exit_2(self):
        rc = sot_guardian.main([
            "--pre-tool-use", "--file", "prompt/PRD.md", "--tool", "Write",
        ])
        self.assertEqual(rc, 2)

    def test_main_allow_exit_0(self):
        rc = sot_guardian.main([
            "--pre-tool-use", "--file", "impl/src/x.py", "--tool", "Write",
        ])
        self.assertEqual(rc, 0)

    def test_trace_help(self):
        self.assertEqual(sot_guardian.TRACE["adapter_boundary_id"], "ADAPT-TOOL-sot_guardian")
        self.assertEqual(sot_guardian.HELP_JSON["tool"], "sot_guardian")


class SingleSourceContract(unittest.TestCase):
    """R1: the canonical marker + verifier have ONE definition (no dual SoT)."""

    def test_marker_is_shared_object(self):
        from tools import append_only, sot_append_rules
        self.assertIs(sot_guardian.CANONICAL_MARKER, sot_append_rules.CANONICAL_MARKER)
        self.assertIs(append_only.CANONICAL_MARKER, sot_append_rules.CANONICAL_MARKER)

    def test_verifier_is_shared_object(self):
        from tools import sot_append_rules
        self.assertIs(sot_guardian.verify_append_only, sot_append_rules.verify_append_only)


class VerifyAppendOnlyContract(unittest.TestCase):
    """C1 / F-1: write-time diff verification (model 나: append + §11.2 token whitelist)."""

    def _ok(self, before, after):
        ok, _ = sot_guardian.verify_append_only(before, after)
        return ok

    def test_identical_allowed(self):
        self.assertTrue(self._ok("a\nb\n", "a\nb\n"))

    def test_trailing_newline_append_allowed(self):
        # New currency line appended at EOF.
        before = "# T\n\n| D14 | x |\n"
        after = before + "\n(v0.9 currency 2026-05-21·번복 아님·X3 안정성 클래스) note\n"
        self.assertTrue(self._ok(before, after))

    def test_end_of_cell_append_allowed(self):
        # Intra-line pure addition before the trailing pipe (end-of-cell append).
        before = "| D14 | foo |\n"
        after = "| D14 | foo (v0.8 currency add) |\n"
        self.assertTrue(self._ok(before, after))

    def test_version_token_correction_allowed(self):
        before = "> 상태: DRAFT v0.6 — body unchanged\n"
        after = "> 상태: DRAFT v0.9 — body unchanged\n"
        self.assertTrue(self._ok(before, after))

    def test_body_modification_denied(self):
        before = "decision: adopt option 4\n"
        after = "decision: adopt option 2\n"  # reversion, not a token
        self.assertFalse(self._ok(before, after))

    def test_line_deletion_denied(self):
        before = "line1\nline2\nline3\n"
        after = "line1\nline3\n"  # line2 removed
        self.assertFalse(self._ok(before, after))

    def test_word_deletion_within_line_denied(self):
        before = "the quick brown fox\n"
        after = "the brown fox\n"  # 'quick' deleted — not pure addition
        self.assertFalse(self._ok(before, after))

    def test_cmd_guard_sot_append_allowed(self):
        import tempfile, os
        before = "| D14 | foo |\n"
        with tempfile.TemporaryDirectory() as d:
            base = os.path.join(d, "PRD.md")
            new = os.path.join(d, "new.txt")
            with open(base, "w", encoding="utf-8") as f:
                f.write(before)
            with open(new, "w", encoding="utf-8") as f:
                f.write(before + "\nnew row appended\n")
            ns = sot_guardian.build_parser().parse_args(
                ["--file", "prompt/PRD.md", "--tool", "Write",
                 "--baseline-file", base, "--new-content-file", new]
            )
            res = sot_guardian.cmd_guard(ns)
            self.assertEqual(res.data["decision"], "allow")

    def test_cmd_guard_sot_body_edit_denied(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            base = os.path.join(d, "PRD.md")
            new = os.path.join(d, "new.txt")
            with open(base, "w", encoding="utf-8") as f:
                f.write("decision: adopt option 4\n")
            with open(new, "w", encoding="utf-8") as f:
                f.write("decision: adopt option 2\n")
            ns = sot_guardian.build_parser().parse_args(
                ["--file", "prompt/PRD.md", "--tool", "Write",
                 "--baseline-file", base, "--new-content-file", new]
            )
            res = sot_guardian.cmd_guard(ns)
            self.assertEqual(res.data["decision"], "deny")

    def test_cmd_guard_sot_no_content_fails_closed(self):
        # No proposed content + no currency marker on a SOT axis → deny (fail-closed).
        ns = sot_guardian.build_parser().parse_args(
            ["--file", "prompt/PRD.md", "--tool", "Write"]
        )
        res = sot_guardian.cmd_guard(ns)
        self.assertEqual(res.data["decision"], "deny")


if __name__ == "__main__":
    unittest.main()
