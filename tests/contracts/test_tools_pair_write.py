"""Contract tests for P-5 tools.pair_write."""

import os
import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401
from tools import pair_write, build_state


SCHEMA = Path(_toolpath._CLAUDE_DIR) / "state" / "schema.sql"


class PairWriteContract(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.db = str(self.root / "bs.sqlite")
        build_state.main(["init", "--db", self.db, "--schema", str(SCHEMA)])
        build_state.main([
            "create-run", "--db", self.db, "--build-run-id", "r1",
            "--phase", "-0.75", "--started-at", "2026-05-21T10:00:00Z",
        ])
        self._cwd = os.getcwd()
        os.chdir(self.root)
        (self.root / "impl/.claude/runs/r1").mkdir(parents=True, exist_ok=True)
        Path("en.txt").write_text("english body\n", encoding="utf-8")
        Path("ko.txt").write_text("한국어 본문\n", encoding="utf-8")

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _args(self, **over):
        base = dict(
            db=self.db,
            en_path="impl/.claude/runs/r1/doc.en.md",
            en_content_file="en.txt",
            ko_path="impl/.claude/runs/r1/doc.ko.md",
            ko_content_file="ko.txt",
            step_id="s1", build_run_id="r1", task_id=None,
            ko_status="ok", now="2026-05-21T10:05:00Z",
        )
        base.update(over)
        import argparse
        return argparse.Namespace(**base)

    def test_atomic_commit_creates_both(self):
        r = pair_write.cmd_write(self._args())
        self.assertTrue(r.data["atomicity_ok"])
        self.assertTrue(Path("impl/.claude/runs/r1/doc.en.md").is_file())
        self.assertTrue(Path("impl/.claude/runs/r1/doc.ko.md").is_file())

    def test_idempotent_rerun(self):
        pair_write.cmd_write(self._args())
        r2 = pair_write.cmd_write(self._args(now="2026-05-21T10:09:00Z"))
        self.assertTrue(r2.data["idempotent"])

    def test_sot_axis_rejected(self):
        from tools import errors
        with self.assertRaises(errors.ToolError):
            pair_write.cmd_write(self._args(
                en_path="prompt/PRD.md", ko_path="prompt/PRD.ko.md",
            ))

    def test_sibling_convention_enforced(self):
        from tools import errors
        with self.assertRaises(errors.ValidationError):
            pair_write.cmd_write(self._args(
                ko_path="impl/.claude/runs/r1/other.ko.md",
            ))

    def test_non_ok_write_requires_task_id(self):
        # §8 gate 5 keys on task_id; a non-ok pair written without one would be invisible
        # to set-task-completed's backstop. Reject it at the write path.
        from tools import errors
        with self.assertRaises(errors.ValidationError):
            pair_write.cmd_write(self._args(
                ko_status="produced", task_id=None, ko_content_file=None,
            ))

    def test_non_ok_write_with_task_id_links_row(self):
        import sqlite3
        pair_write.cmd_write(self._args(
            ko_status="produced", task_id="t-x", ko_content_file=None,
        ))
        conn = sqlite3.connect(self.db)
        row = conn.execute(
            "SELECT task_id, ko_status FROM pair_outputs WHERE step_id='s1';"
        ).fetchone()
        conn.close()
        # The row is now gate-5-visible (task_id populated, status not yet 'ok').
        self.assertEqual(row, ("t-x", "produced"))

    def test_trace_help(self):
        self.assertEqual(pair_write.TRACE["adapter_boundary_id"], "ADAPT-TOOL-pair_write")
        self.assertEqual(pair_write.HELP_JSON["tool"], "pair_write")


if __name__ == "__main__":
    unittest.main()
