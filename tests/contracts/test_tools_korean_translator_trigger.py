"""Contract tests for hook-backing tools.korean_translator_trigger (§6.8)."""

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401  (sys.path bootstrap side effect)
from tools import korean_translator_trigger as ktt
from tools import build_state

SCHEMA = Path(_toolpath._CLAUDE_DIR) / "state" / "schema.sql"


def _event(file_path):
    return json.dumps({"tool_name": "Write", "tool_input": {"file_path": file_path}})


class KoreanTranslatorTriggerContract(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.runs = self.root / "impl" / ".claude" / "runs"
        self.runs.mkdir(parents=True)
        self.db = str(self.root / "bs.sqlite")

    def tearDown(self):
        self._tmp.cleanup()

    def test_no_file_path_noop(self):
        self.assertEqual(ktt._decide("{}", self.db)["action"], "noop")

    def test_not_en_md_noop(self):
        fp = str(self.runs / "foo.md")
        self.assertEqual(ktt._decide(_event(fp), self.db)["action"], "noop")

    def test_outside_zone_noop(self):
        out = ktt._decide(_event("/somewhere/src/foo.en.md"), self.db)
        self.assertEqual(out["action"], "noop")
        self.assertIn("outside", out["reason"])

    def test_db_missing_defers(self):
        fp = str(self.runs / "foo.en.md")
        Path(fp).write_text("body\n", encoding="utf-8")
        self.assertEqual(ktt._decide(_event(fp), self.db)["action"], "defer")

    def test_enqueue_when_no_row(self):
        build_state.main(["init", "--db", self.db, "--schema", str(SCHEMA)])
        fp = str(self.runs / "foo.en.md")
        Path(fp).write_text("english body\n", encoding="utf-8")
        out = ktt._decide(_event(fp), self.db)
        self.assertEqual(out["action"], "enqueue")
        self.assertEqual(out["subagent"], "korean-translator")
        self.assertEqual(out["en_path"], fp)

    def test_skip_when_ok_row_exists(self):
        build_state.main(["init", "--db", self.db, "--schema", str(SCHEMA)])
        fp = str(self.runs / "foo.en.md")
        Path(fp).write_text("english body\n", encoding="utf-8")
        en_sha = hashlib.sha256(Path(fp).read_bytes()).hexdigest()
        conn = sqlite3.connect(self.db)
        conn.execute(
            "INSERT INTO build_runs(build_run_id, phase, started_at, status) "
            "VALUES('r1','-0.75','2026-05-21T00:00:00Z','running');"
        )
        conn.execute(
            "INSERT INTO pair_outputs(build_run_id, step_id, en_path, ko_path, en_sha, "
            "ko_sha, ko_status, ko_attempts, ts_en) "
            "VALUES('r1','s1',?,?,?,'cafe','ok',0,'2026-05-21T00:00:00Z');",
            (fp, fp.replace(".en.md", ".ko.md"), en_sha),
        )
        conn.commit()
        conn.close()
        self.assertEqual(ktt._decide(_event(fp), self.db)["action"], "skip")

    def test_help_json_tool_name(self):
        self.assertEqual(ktt.HELP_JSON["tool"], "korean_translator_trigger")

    def test_trace_dict_present(self):
        self.assertEqual(ktt.TRACE["adapter_boundary_id"], "ADAPT-TOOL-korean_translator_trigger")


if __name__ == "__main__":
    unittest.main()
