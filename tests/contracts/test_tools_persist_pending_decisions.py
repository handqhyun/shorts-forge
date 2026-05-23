"""Contract tests for hook-backing tools.persist_pending_decisions (§6.6 Stop)."""

import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401  (sys.path bootstrap side effect)
from tools import persist_pending_decisions as ppd
from tools import build_state

SCHEMA = Path(_toolpath._CLAUDE_DIR) / "state" / "schema.sql"


class PersistPendingDecisionsContract(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.db = str(self.root / "bs.sqlite")
        self.out = str(self.root / "pending.md")

    def tearDown(self):
        self._tmp.cleanup()

    def _seed_open_decision(self):
        build_state.main(["init", "--db", self.db, "--schema", str(SCHEMA)])
        build_state.main([
            "create-run", "--db", self.db, "--build-run-id", "r1",
            "--phase", "-0.75", "--started-at", "2026-05-21T00:00:00Z", "--status", "running",
        ])
        build_state.main([
            "insert-decision", "--db", self.db, "--decision-id", "d1",
            "--build-run-id", "r1", "--decision-type", "BLOCKING", "--gate-id", "D14",
        ])

    def test_db_absent_no_write(self):
        ns = ppd.build_parser().parse_args(["--db", self.db, "--out", self.out])
        data = ppd.cmd(ns).data
        self.assertFalse(data["db_present"])
        self.assertFalse(data["wrote"])

    def test_dry_run_lists_open_without_writing(self):
        self._seed_open_decision()
        ns = ppd.build_parser().parse_args(["--db", self.db, "--out", self.out, "--dry-run"])
        data = ppd.cmd(ns).data
        self.assertEqual(data["open_count"], 1)
        self.assertFalse(data["wrote"])
        self.assertFalse(Path(self.out).exists())

    def test_write_appends_snapshot(self):
        self._seed_open_decision()
        ns = ppd.build_parser().parse_args(
            ["--db", self.db, "--out", self.out, "--now", "2026-05-21T12:00:00Z"]
        )
        data = ppd.cmd(ns).data
        self.assertTrue(data["wrote"])
        body = Path(self.out).read_text(encoding="utf-8")
        self.assertIn("d1", body)
        self.assertIn("D14", body)
        self.assertIn("2026-05-21T12:00:00Z", body)

    def test_help_json_tool_name(self):
        self.assertEqual(ppd.HELP_JSON["tool"], "persist_pending_decisions")

    def test_trace_dict_present(self):
        self.assertEqual(ppd.TRACE["adapter_boundary_id"], "ADAPT-TOOL-persist_pending_decisions")


if __name__ == "__main__":
    unittest.main()
