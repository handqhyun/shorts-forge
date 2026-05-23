"""Contract tests for N-5 tools.swarm_fallback."""

import argparse
import sqlite3
import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401
from tools import swarm_fallback, build_state


SCHEMA = Path(_toolpath._CLAUDE_DIR) / "state" / "schema.sql"


class SwarmFallbackContract(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self._tmp.name) / "bs.sqlite")
        build_state.main(["init", "--db", self.db, "--schema", str(SCHEMA)])
        build_state.main([
            "create-run", "--db", self.db, "--build-run-id", "r1",
            "--phase", "-0.75", "--started-at", "2026-05-21T09:00:00Z",
        ])

    def tearDown(self):
        self._tmp.cleanup()

    def _task(self, tid, heartbeat):
        build_state.main([
            "update-task", "--db", self.db, "--task-id", tid, "--build-run-id", "r1",
            "--subagent-name", "x", "--status", "in_progress", "--created-at", "2026-05-21T09:00:00Z",
        ])
        c = sqlite3.connect(self.db)
        c.execute("UPDATE build_tasks SET last_heartbeat_at=? WHERE task_id=?", (heartbeat, tid))
        c.commit()
        c.close()

    def _ns(self, now):
        return argparse.Namespace(db=self.db, build_run_id="r1", now=now)

    def test_no_stall_when_recent(self):
        self._task("t1", "2026-05-21T10:04:00Z")
        r = swarm_fallback.cmd(self._ns("2026-05-21T10:05:00Z"))
        self.assertEqual(r.data["action"], "none")

    def test_stall_detected_after_10min(self):
        self._task("t1", "2026-05-21T09:50:00Z")
        r = swarm_fallback.cmd(self._ns("2026-05-21T10:05:00Z"))
        self.assertIn("t1", r.data["stalled_tasks"])

    def test_solo_mode_at_three_stalls(self):
        for t in ("t1", "t2", "t3"):
            self._task(t, "2026-05-21T09:00:00Z")
        r = swarm_fallback.cmd(self._ns("2026-05-21T10:05:00Z"))
        self.assertEqual(r.data["action"], "solo-mode")

    def test_trace_help(self):
        self.assertEqual(swarm_fallback.TRACE["adapter_boundary_id"], "ADAPT-TOOL-swarm_fallback")
        self.assertEqual(swarm_fallback.HELP_JSON["tool"], "swarm_fallback")


if __name__ == "__main__":
    unittest.main()
