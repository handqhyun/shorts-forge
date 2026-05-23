"""Contract tests for hook-backing tools.netguard_pretool (§6.4 PreToolUse Bash)."""

import json
import tempfile
import unittest
from pathlib import Path

import _toolpath  # noqa: F401  (sys.path bootstrap side effect)
from tools import netguard_pretool, errors


class NetguardPretoolContract(unittest.TestCase):
    def _ns(self, command, carveouts="impl/.claude/state/network-carveouts.json"):
        return netguard_pretool.build_parser().parse_args(
            ["--command", command, "--carveouts", carveouts]
        )

    def test_no_egress_allowed(self):
        data = netguard_pretool.cmd(self._ns("ls -la && python -m tools.sot_read")).data
        self.assertEqual(data["decision"], "allow")

    def test_curl_denied(self):
        data = netguard_pretool.cmd(self._ns("curl http://example.com/x")).data
        self.assertEqual(data["decision"], "deny")

    def test_pip_install_denied(self):
        data = netguard_pretool.cmd(self._ns("pip install requests")).data
        self.assertEqual(data["decision"], "deny")

    def test_carveout_allows_match(self):
        with tempfile.TemporaryDirectory() as d:
            cv = Path(d) / "carveouts.json"
            cv.write_text(json.dumps({"allow_substrings": ["pip install -e ."]}), encoding="utf-8")
            data = netguard_pretool.cmd(self._ns("pip install -e .", str(cv))).data
            self.assertEqual(data["decision"], "allow")
            self.assertIn("carveout", data["reason"])

    def test_missing_command_is_usage_error(self):
        ns = netguard_pretool.build_parser().parse_args([])
        with self.assertRaises(errors.UsageError):
            netguard_pretool.cmd(ns)

    def test_stdin_command_extraction(self):
        import io
        import sys
        raw = '{"tool_input": {"command": "wget http://x"}}'
        old = sys.stdin
        sys.stdin = io.StringIO(raw)
        try:
            extracted = netguard_pretool._command_from_stdin()
        finally:
            sys.stdin = old
        self.assertEqual(extracted, "wget http://x")

    def test_deterministic_same_input_same_output(self):
        a = netguard_pretool.cmd(self._ns("curl http://x")).data
        b = netguard_pretool.cmd(self._ns("curl http://x")).data
        self.assertEqual(a, b)

    def test_help_json_tool_name(self):
        self.assertEqual(netguard_pretool.HELP_JSON["tool"], "netguard_pretool")

    def test_trace_dict_present(self):
        self.assertEqual(netguard_pretool.TRACE["adapter_boundary_id"], "ADAPT-TOOL-netguard_pretool")


if __name__ == "__main__":
    unittest.main()
