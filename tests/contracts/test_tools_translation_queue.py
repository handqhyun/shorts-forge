"""Contract tests for hook-backing tools.translation_queue (§6.1, §6.2)."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401  (sys.path bootstrap side effect)
from tools import translation_queue, build_state, errors

SCHEMA = Path(_toolpath._CLAUDE_DIR) / "state" / "schema.sql"


class TranslationQueueContract(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self._tmp.name) / "bs.sqlite")

    def tearDown(self):
        self._tmp.cleanup()

    def _seed(self, *rows):
        build_state.main(["init", "--db", self.db, "--schema", str(SCHEMA)])
        conn = sqlite3.connect(self.db)
        conn.execute(
            "INSERT INTO build_runs(build_run_id, phase, started_at, status) "
            "VALUES('r1','-0.75','2026-05-21T00:00:00Z','running');"
        )
        for step_id, ts_en, ko_status in rows:
            conn.execute(
                "INSERT INTO pair_outputs(build_run_id, step_id, en_path, ko_path, "
                "en_sha, ko_status, ko_attempts, ts_en) VALUES(?,?,?,?,?,?,0,?);",
                ("r1", step_id, f"{step_id}.en.md", f"{step_id}.ko.md", "deadbeef", ko_status, ts_en),
            )
        conn.commit()
        conn.close()

    def _ns(self, mode):
        return translation_queue.build_parser().parse_args(["--mode", mode, "--db", self.db])

    def test_db_absent_zero_pending(self):
        data = translation_queue.cmd(self._ns("check")).data
        self.assertFalse(data["db_present"])
        self.assertEqual(data["pending_count"], 0)

    def test_counts_only_unfinished(self):
        self._seed(
            ("s1", "2026-05-21T01:00:00Z", "pending"),
            ("s2", "2026-05-21T02:00:00Z", "ok"),       # finished -> excluded
            ("s3", "2026-05-21T03:00:00Z", "produced"),
        )
        data = translation_queue.cmd(self._ns("check")).data
        self.assertTrue(data["db_present"])
        self.assertEqual(data["pending_count"], 2)
        self.assertIn("s1", data["step_ids"])
        self.assertNotIn("s2", data["step_ids"])

    def test_summary_oldest_first(self):
        self._seed(
            ("late", "2026-05-21T09:00:00Z", "failed"),
            ("early", "2026-05-21T01:00:00Z", "pending"),
        )
        data = translation_queue.cmd(self._ns("summary")).data
        self.assertEqual(data["oldest_step_id"], "early")

    def test_bad_mode_rejected(self):
        with self.assertRaises(errors.ValidationError):
            translation_queue.cmd(self._ns("flush"))

    def test_help_json_tool_name(self):
        self.assertEqual(translation_queue.HELP_JSON["tool"], "translation_queue")

    def test_trace_dict_present(self):
        self.assertEqual(translation_queue.TRACE["adapter_boundary_id"], "ADAPT-TOOL-translation_queue")


if __name__ == "__main__":
    unittest.main()
