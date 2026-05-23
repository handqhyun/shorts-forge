---
name: workflow-read
description: Parse prompt/workflow.md and extract a section, including D-2/D-3/D-4 contracts in machine-readable form. Single source of truth for workflow content.
---

# workflow-read

Extract a requested section of `prompt/workflow.md` verbatim, and expose the D-2 / D-3 / D-4 contracts of a stage in machine-readable form. Single permitted path to workflow content; `tdd-test-author` consumes the D-3 extraction to author RED tests, so the parse must be deterministic and stable.

## When to invoke

- A subagent needs a workflow section, gate, or stage contract (e.g. `§2.S3`, `§10.D5`, `§7 D-3`).
- `tdd-test-author` needs the D-3 judgment predicates of a stage to generate RED tests.
- Never `Read` `prompt/workflow.md` directly.

## Arguments

| Name | Type | Description |
|---|---|---|
| `section` | string | Section locator (`§2.S3`, `§10.D5`, `§7 D-3`) |

## Output

JSON: `{section, body_text, contracts: {d2_input, d2_output, d3_pass, d3_fail, d3_degrade, d4_recovery}}`. Byte-identical for identical input — the RED-test generator depends on this stability.

## CLI backing

Backing tool: `tools.sot_read` (run via `python -m tools.sot_read --source workflow --section "<arg>"`). `--source` is fixed to `workflow`.

| Flag | Type | Description |
|---|---|---|
| `--source` | enum | `workflow` (fixed for this skill) |
| `--section` | str | Section locator passed through from `section` |
| `--axis` | str | Unused for workflow (final-research axis selector) |
| `--root` | str | SOT root override (auto-detected if omitted) |

## Classification

**Deterministic script** — regex + structural parser. D-2/D-3/D-4 extraction is deterministic; the contracts dict is never reconstructed or predicted by an LLM.

## SOT preservation

Read-only. Never writes any SOT axis.

## References

- workflow-coding.md §5.1.2 (this skill's specification)
- workflow-coding.md §4.3.1 (tdd-test-author consumes D-3 extraction)
- workflow-coding.md §14.1.2 #10 (CLI tool authoring convention)
