"""Contract tests for P-1 tools.sot_read."""

import unittest

import _toolpath  # noqa: F401
from tools import sot_read, errors


SAMPLE = """# Doc

## 12. BLOCKING

| ID | desc |
|---|---|
| D14 | music matching |
| D17 | auth continuity |

## 13. Next

body of 13
"""


class SotReadContract(unittest.TestCase):
    def test_atx_header_section(self):
        body = sot_read.extract_section(SAMPLE, "## 13. Next")
        self.assertTrue(body.startswith("## 13. Next"))
        self.assertIn("body of 13", body)
        # must stop before any following same/higher-level header (none here)
        self.assertNotIn("## 12.", body)

    def test_table_row_fallback_d17(self):
        body = sot_read.extract_section(SAMPLE, "§12-D17")
        self.assertTrue(body.lstrip().startswith("| D17 |"))
        self.assertIn("auth continuity", body)

    def test_table_row_fallback_d14_not_d17(self):
        body = sot_read.extract_section(SAMPLE, "§12-D14")
        self.assertIn("music matching", body)
        self.assertNotIn("auth continuity", body)

    def test_missing_section_raises(self):
        with self.assertRaises(errors.NotFoundError):
            sot_read.extract_section(SAMPLE, "§99-NOPE")

    def test_deterministic_same_input_same_output(self):
        a = sot_read.extract_section(SAMPLE, "§12-D17")
        b = sot_read.extract_section(SAMPLE, "§12-D17")
        self.assertEqual(a, b)

    def test_help_json_tool_name(self):
        self.assertEqual(sot_read.HELP_JSON["tool"], "sot_read")

    def test_trace_dict_present(self):
        self.assertEqual(sot_read.TRACE["adapter_boundary_id"], "ADAPT-TOOL-sot_read")


if __name__ == "__main__":
    unittest.main()
