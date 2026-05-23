"""3-axis --help / --help-json / SKILL.md synchronization gate.

Reference: prompt/workflow-coding.md §14.1.2 #10 (b), §4.2.6 Exit contract (c),
§15.1.8 종료 조건 (c), §15.1.5 v0.5 추가 진입 조건.

Three axes must agree:

  Axis A  `--help-json`   — the machine-readable HELP_JSON dict
  Axis B  argparse        — the registered CLI options (`build_parser()`)
  Axis C  SKILL.md        — the "## CLI backing" argument table of each skill
                            backed by a deterministic tool

A↔B is checked for every tool (flat tools and the build_state subcommand tree).
A/B↔C is checked for every SKILL.md that declares a CLI backing. Skills with no
CLI backing section are pure LLM-judgment (decision-surface, golden-corpus-curator)
and are exempt from the CLI axis.
"""

import argparse
import contextlib
import importlib
import io
import json
import pkgutil
import re
import unittest
from pathlib import Path

import _toolpath  # noqa: F401  (sys.path bootstrap side effect)
import tools

# Long options that are I/O plumbing, not logical arguments, and so are
# intentionally absent from HELP_JSON["args"].
META = {"--help", "-h", "--help-json", "--stdin"}

# Common modules that are not CLI tools.
NON_TOOLS = {"__init__", "errors", "result", "sot_append_rules"}

CLAUDE_DIR = Path(_toolpath._CLAUDE_DIR)
SKILLS_DIR = CLAUDE_DIR / "skills"

_BACKTICK_FLAG = re.compile(r"`(--[a-z0-9-]+)`")
_BACKING = re.compile(r"tools\.([a-z0-9_]+)")


def _tool_modules():
    names = [m.name for m in pkgutil.iter_modules(tools.__path__) if m.name not in NON_TOOLS]
    return sorted(names)


def _long_opts(parser) -> set:
    opts = set()
    for action in parser._actions:
        for s in action.option_strings:
            if s.startswith("--") and s not in META:
                opts.add(s)
    return opts


def _subparsers(parser):
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices
    return {}


def _expected_tool_args(mod) -> set:
    """The full logical-argument set a backing tool exposes (flat or subcommand)."""
    hj = mod.HELP_JSON
    if "args" in hj:
        return set(hj["args"])
    out = set()
    for spec in hj.get("subcommands", {}).values():
        out.update(spec.get("args", {}))
    return out


def _cli_backing_section(text: str):
    """Return (backing_module_name, set_of_flags) or None if no CLI backing."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().lower() == "## cli backing":
            start = i
            break
    if start is None:
        return None
    body = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        body.append(line)
    section = "\n".join(body)
    backing_match = _BACKING.search(section)
    backing = backing_match.group(1) if backing_match else None
    flags = set(_BACKTICK_FLAG.findall(section))
    return backing, flags


class HelpJsonArgparseSyncContract(unittest.TestCase):
    """Axis A <-> Axis B for every tool."""

    def test_flat_tool_args_match_argparse(self):
        for name in _tool_modules():
            mod = importlib.import_module(f"tools.{name}")
            hj = getattr(mod, "HELP_JSON", None)
            self.assertIsNotNone(hj, f"{name}: missing HELP_JSON")
            self.assertEqual(hj.get("tool"), name, f"{name}: HELP_JSON.tool mismatch")
            parser = mod.build_parser()
            if "args" in hj:
                self.assertEqual(
                    set(hj["args"]), _long_opts(parser),
                    f"{name}: HELP_JSON args != argparse options",
                )

    def test_subcommand_tool_args_match_argparse(self):
        for name in _tool_modules():
            mod = importlib.import_module(f"tools.{name}")
            hj = mod.HELP_JSON
            if "subcommands" not in hj:
                continue
            choices = _subparsers(mod.build_parser())
            for subname, spec in hj["subcommands"].items():
                self.assertIn(subname, choices, f"{name}: subcommand {subname} not in parser")
                self.assertEqual(
                    set(spec["args"]), _long_opts(choices[subname]),
                    f"{name}.{subname}: HELP_JSON args != argparse options",
                )


class HelpJsonDeterminismContract(unittest.TestCase):
    """`--help-json` output must be byte-identical across invocations."""

    def test_help_json_byte_identical(self):
        for name in _tool_modules():
            mod = importlib.import_module(f"tools.{name}")

            def _run():
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = mod.main(["--help-json"])
                return rc, buf.getvalue()

            rc1, out1 = _run()
            rc2, out2 = _run()
            self.assertEqual(rc1, 0, f"{name}: --help-json rc != 0")
            self.assertEqual(out1, out2, f"{name}: --help-json not byte-identical")
            self.assertEqual(
                json.loads(out1), mod.HELP_JSON,
                f"{name}: --help-json output != HELP_JSON",
            )


class SkillCliBackingSyncContract(unittest.TestCase):
    """Axis C: SKILL.md '## CLI backing' table <-> backing tool HELP_JSON args."""

    def test_every_skill_has_frontmatter_name(self):
        for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
            text = skill_md.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---"), f"{skill_md}: missing frontmatter")
            self.assertIn("name:", text.split("---", 2)[1], f"{skill_md}: missing name")

    def test_cli_backing_matches_tool_help_json(self):
        checked = 0
        for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
            text = skill_md.read_text(encoding="utf-8")
            parsed = _cli_backing_section(text)
            if parsed is None:
                continue  # LLM-only skill: exempt from CLI axis
            backing, flags = parsed
            self.assertIsNotNone(backing, f"{skill_md}: CLI backing names no tools.<name>")
            mod = importlib.import_module(f"tools.{backing}")
            expected = _expected_tool_args(mod)
            self.assertEqual(
                flags, expected,
                f"{skill_md}: CLI backing flags {sorted(flags)} != "
                f"tools.{backing} args {sorted(expected)}",
            )
            checked += 1
        self.assertGreaterEqual(checked, 9, "expected >=9 deterministic-backed skills")


if __name__ == "__main__":
    unittest.main()
