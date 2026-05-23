"""Contract tests for P-3 tools.impact_analyze."""

import argparse
import json
import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401
from tools import impact_analyze


def _ns(root, sha, changed, srcroot):
    return argparse.Namespace(
        task_id="t1", build_run_id="r1", changed_files_sha=sha,
        changed_files=changed, src_root=srcroot, out_root=str(root),
    )


class ImpactAnalyzeContract(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.src = self.root / "src"
        self.src.mkdir()
        (self.src / "base.py").write_text("X = 1\n", encoding="utf-8")
        (self.src / "consumer.py").write_text("from base import X\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_downstream_detected(self):
        r = impact_analyze.cmd(_ns(self.root / "runs", "sha1", "src/base.py", str(self.src)))
        out = json.loads((self.root / "runs" / "r1" / "impact" / "t1.json").read_text(encoding="utf-8"))
        self.assertIn(str((self.src / "consumer.py").as_posix()), out["downstream_modules"])

    def test_idempotent_same_sha(self):
        impact_analyze.cmd(_ns(self.root / "runs", "sha1", "src/base.py", str(self.src)))
        r2 = impact_analyze.cmd(_ns(self.root / "runs", "sha1", "src/base.py", str(self.src)))
        self.assertTrue(r2.data["cached"])

    def test_new_sha_not_cached(self):
        impact_analyze.cmd(_ns(self.root / "runs", "sha1", "src/base.py", str(self.src)))
        r2 = impact_analyze.cmd(_ns(self.root / "runs", "sha2", "src/base.py", str(self.src)))
        self.assertFalse(r2.data["cached"])

    def test_trace_help(self):
        self.assertEqual(impact_analyze.TRACE["adapter_boundary_id"], "ADAPT-TOOL-impact_analyze")
        self.assertEqual(impact_analyze.HELP_JSON["tool"], "impact_analyze")

    def test_deferred_checks_surfaced(self):
        impact_analyze.cmd(_ns(self.root / "runs", "sha1", "src/base.py", str(self.src)))
        out = json.loads((self.root / "runs" / "r1" / "impact" / "t1.json").read_text(encoding="utf-8"))
        names = {d["check"] for d in out["deferred_checks"]}
        self.assertEqual(
            names,
            {"ratchet_remeasure_required", "red_regen_required", "adapter_dto_signature"},
        )
        # Deferred fields are empty lists, but the deferral is explicit, not silent.
        self.assertEqual(out["ratchet_remeasure_required"], [])
        self.assertEqual(out["red_regen_required"], [])

    def test_no_warnings_for_traceless_module(self):
        impact_analyze.cmd(_ns(self.root / "runs", "sha1", "src/base.py", str(self.src)))
        out = json.loads((self.root / "runs" / "r1" / "impact" / "t1.json").read_text(encoding="utf-8"))
        self.assertEqual(out["shotgun_warnings"], [])
        self.assertEqual(out["adapter_boundary_violations"], [])


def _trace_module(**fields):
    return "TRACE = " + repr(fields) + "\n"


class ImpactAnalyzeDeterministicFields(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.src = self.root / "src"
        self.src.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, changed):
        impact_analyze.cmd(_ns(self.root / "runs", "shaX", changed, str(self.src)))
        return json.loads((self.root / "runs" / "r1" / "impact" / "t1.json").read_text(encoding="utf-8"))

    def test_undeclared_import_warned(self):
        (self.src / "mod.py").write_text(
            "import socket\n" + _trace_module(imports=["json"], adapter_boundary_id=""),
            encoding="utf-8",
        )
        out = self._run("mod.py")
        reasons = " ".join(w["reason"] for w in out["shotgun_warnings"])
        self.assertIn("undeclared imports in mod.py", reasons)
        affected = [a for w in out["shotgun_warnings"] for a in w["affected"]]
        self.assertIn("socket", affected)

    def test_declared_import_no_false_positive(self):
        (self.src / "mod.py").write_text(
            "from __future__ import annotations\nimport socket\nfrom . import errors\n"
            + _trace_module(imports=["socket", "tools.errors"], adapter_boundary_id=""),
            encoding="utf-8",
        )
        out = self._run("mod.py")
        self.assertEqual(out["shotgun_warnings"], [])

    def test_state_key_ripple(self):
        (self.src / "writer.py").write_text(
            _trace_module(imports=[], writes_state_keys=["build_tasks"], adapter_boundary_id=""),
            encoding="utf-8",
        )
        (self.src / "reader.py").write_text(
            _trace_module(imports=[], reads_state_keys=["build_tasks"], adapter_boundary_id=""),
            encoding="utf-8",
        )
        out = self._run("writer.py")
        affected = [a for w in out["shotgun_warnings"] for a in w["affected"]]
        self.assertIn((self.src / "reader.py").as_posix(), affected)

    def test_unknown_adapter_boundary_id(self):
        (self.src / "mod.py").write_text(
            _trace_module(imports=[], adapter_boundary_id="ADAPT-BOGUS"),
            encoding="utf-8",
        )
        out = self._run("mod.py")
        ids = [v["boundary_id"] for v in out["adapter_boundary_violations"]]
        self.assertEqual(ids, ["ADAPT-BOGUS"])

    def test_known_and_tool_adapter_ids_ok(self):
        (self.src / "stage.py").write_text(
            _trace_module(imports=[], adapter_boundary_id="ADAPT-S1-IN"), encoding="utf-8",
        )
        (self.src / "tool.py").write_text(
            _trace_module(imports=[], adapter_boundary_id="ADAPT-TOOL-foo"), encoding="utf-8",
        )
        out = self._run("stage.py,tool.py")
        self.assertEqual(out["adapter_boundary_violations"], [])


if __name__ == "__main__":
    unittest.main()
