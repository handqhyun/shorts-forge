"""Contract tests for P-11 tools.build_state.

Standard library unittest (pytest is the spec runner but absent in this env;
unittest.TestCase runs identically under both).
"""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401  (sys.path bootstrap side effect)
from tools import build_state


SCHEMA = Path(_toolpath._CLAUDE_DIR) / "state" / "schema.sql"


class BuildStateContract(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self._tmp.name) / "bs.sqlite")
        rc = build_state.main(["init", "--db", self.db, "--schema", str(SCHEMA)])
        self.assertEqual(rc, 0)

    def tearDown(self):
        self._tmp.cleanup()

    def test_init_creates_five_tables(self):
        rc = build_state.main(["init", "--db", self.db, "--schema", str(SCHEMA)])
        self.assertEqual(rc, 0)

    def test_create_run_phase_minus_075(self):
        rc = build_state.main([
            "create-run", "--db", self.db, "--build-run-id", "r1",
            "--phase", "-0.75", "--started-at", "2026-05-21T10:00:00Z",
            "--status", "running",
        ])
        self.assertEqual(rc, 0)

    def test_create_run_rejects_unknown_phase(self):
        rc = build_state.main([
            "create-run", "--db", self.db, "--build-run-id", "r2",
            "--phase", "99", "--started-at", "2026-05-21T10:00:00Z",
        ])
        self.assertEqual(rc, 1)  # validation_error

    def test_set_pair_status_rejects_bad_enum(self):
        # ko_status='okay' must be rejected (F-1 enum guard).
        rc = build_state.main([
            "set-pair-status", "--db", self.db, "--build-run-id", "r1",
            "--step-id", "s1", "--en-path", "x.en.md", "--ko-status", "okay",
        ])
        self.assertEqual(rc, 1)

    def test_help_json_deterministic(self):
        # --help-json output must be byte-identical across invocations.
        a = json.dumps(build_state.HELP_JSON, sort_keys=True, separators=(",", ":"))
        b = json.dumps(build_state.HELP_JSON, sort_keys=True, separators=(",", ":"))
        self.assertEqual(a, b)
        self.assertEqual(build_state.HELP_JSON["tool"], "build_state")

    def test_trace_dict_present(self):
        self.assertIn("adapter_boundary_id", build_state.TRACE)
        self.assertEqual(build_state.TRACE["adapter_boundary_id"], "ADAPT-TOOL-build_state")

    # --- §8 task-verification gate 5 (Korean pair) backstop on set-task-completed (B-4) ---

    def _seed_task(self, task_id):
        build_state.main([
            "create-run", "--db", self.db, "--build-run-id", "r1",
            "--phase", "-0.5", "--started-at", "2026-05-21T10:00:00Z", "--status", "running",
        ])
        rc = build_state.main([
            "update-task", "--db", self.db, "--task-id", task_id,
            "--build-run-id", "r1", "--subagent-name", "stage-x-builder",
            "--status", "in_progress", "--created-at", "2026-05-21T10:00:00Z",
        ])
        self.assertEqual(rc, 0)

    def _seed_pair(self, task_id, step_id, ko_status):
        conn = sqlite3.connect(self.db)
        try:
            conn.execute(
                "INSERT INTO pair_outputs (build_run_id, task_id, step_id, en_path, "
                "ko_path, en_sha, ko_status, ts_en) VALUES (?,?,?,?,?,?,?,?);",
                ("r1", task_id, step_id, f"{step_id}.en.md", f"{step_id}.ko.md",
                 "deadbeef", ko_status, "2026-05-21T10:00:00Z"),
            )
            conn.commit()
        finally:
            conn.close()

    def test_set_task_completed_exempt_when_no_pairs(self):
        # A task with no pair_outputs rows is gate-5-exempt and completes (§8.1).
        self._seed_task("t-nopair")
        rc = build_state.main([
            "set-task-completed", "--db", self.db, "--task-id", "t-nopair",
            "--completed-at", "2026-05-21T11:00:00Z",
        ])
        self.assertEqual(rc, 0)

    def test_set_task_completed_blocked_by_non_ok_pair(self):
        # A pair_outputs row stuck at 'produced' blocks completion (integrity_error).
        self._seed_task("t-produced")
        self._seed_pair("t-produced", "s1", "produced")
        rc = build_state.main([
            "set-task-completed", "--db", self.db, "--task-id", "t-produced",
            "--completed-at", "2026-05-21T11:00:00Z",
        ])
        self.assertEqual(rc, 1)
        # The task must remain not-completed after a blocked attempt.
        conn = sqlite3.connect(self.db)
        try:
            status = conn.execute(
                "SELECT status FROM build_tasks WHERE task_id='t-produced';"
            ).fetchone()[0]
        finally:
            conn.close()
        self.assertNotEqual(status, "completed")

    def test_set_task_completed_passes_when_all_pairs_ok(self):
        # Every pair row at ko_status='ok' => gate 5 satisfied, completion allowed.
        self._seed_task("t-ok")
        self._seed_pair("t-ok", "s1", "ok")
        self._seed_pair("t-ok", "s2", "ok")
        rc = build_state.main([
            "set-task-completed", "--db", self.db, "--task-id", "t-ok",
            "--completed-at", "2026-05-21T11:00:00Z",
        ])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
