"""Contract tests for hook-backing tools.impact_trigger (§6.9)."""

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401  (sys.path bootstrap side effect)
from tools import impact_trigger as it
from tools import build_state

SCHEMA = Path(_toolpath._CLAUDE_DIR) / "state" / "schema.sql"


def _event(file_path):
    return json.dumps({"tool_name": "Write", "tool_input": {"file_path": file_path}})


class ImpactTriggerContract(unittest.TestCase):
    def test_no_file_path_noop(self):
        self.assertEqual(it._decide("{}", "missing.sqlite")["action"], "noop")

    def test_not_src_py_noop(self):
        out = it._decide(_event("docs/notes.md"), "missing.sqlite")
        self.assertEqual(out["action"], "noop")

    def test_db_missing_defers(self):
        out = it._decide(_event("impl/src/foo.py"), "/no/such/db.sqlite")
        self.assertEqual(out["action"], "defer")

    def _running_db(self, root):
        db = str(root / "bs.sqlite")
        build_state.main(["init", "--db", db, "--schema", str(SCHEMA)])
        build_state.main([
            "create-run", "--db", db, "--build-run-id", "r1",
            "--phase", "-0.75", "--started-at", "2026-05-21T00:00:00Z", "--status", "running",
        ])
        build_state.main([
            "update-task", "--db", db, "--task-id", "t1", "--build-run-id", "r1",
            "--subagent-name", "tools-foundation-builder", "--status", "in_progress",
            "--created-at", "2026-05-21T00:01:00Z",
        ])
        return db

    def test_enqueue_with_running_task(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "impl" / "src").mkdir(parents=True)
            (root / "impl" / "src" / "foo.py").write_text("x = 1\n", encoding="utf-8")
            db = self._running_db(root)
            old = os.getcwd()
            os.chdir(root)
            try:
                out = it._decide(_event("impl/src/foo.py"), db)
            finally:
                os.chdir(old)
            self.assertEqual(out["action"], "enqueue")
            self.assertEqual(out["task_id"], "t1")
            self.assertEqual(out["subagent"], "impact-analyzer")

    def test_skip_when_cached(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "impl" / "src" / "foo.py"
            src.parent.mkdir(parents=True)
            src.write_text("x = 1\n", encoding="utf-8")
            db = self._running_db(root)
            sha = hashlib.sha256(src.read_bytes()).hexdigest()
            cache = root / "impl" / ".claude" / "runs" / "r1" / "impact" / "t1.json"
            cache.parent.mkdir(parents=True)
            cache.write_text(json.dumps({"changed_files_sha": sha}), encoding="utf-8")
            old = os.getcwd()
            os.chdir(root)
            try:
                out = it._decide(_event("impl/src/foo.py"), db)
            finally:
                os.chdir(old)
            self.assertEqual(out["action"], "skip")

    def test_help_json_tool_name(self):
        self.assertEqual(it.HELP_JSON["tool"], "impact_trigger")

    def test_trace_dict_present(self):
        self.assertEqual(it.TRACE["adapter_boundary_id"], "ADAPT-TOOL-impact_trigger")


if __name__ == "__main__":
    unittest.main()
