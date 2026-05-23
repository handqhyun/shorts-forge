---
name: final-research-read
description: Parse prompt/prd-research/final-research.md and extract by axis (【AX-*】) or section ([F §n]). Single source of truth for research evidence.
---

# final-research-read

Extract evidence from `prompt/prd-research/final-research.md` by axis (`【AX-*】`) or section (`[F §n]`). Single permitted path to research content; no subagent reads the research file directly.

## When to invoke

- A subagent needs a research axis or section as decision evidence (e.g. `【AX-CRAFT】`, `[F §3]`).
- Never `Read` `prompt/prd-research/final-research.md` directly.

## Arguments

| Name | Type | Description |
|---|---|---|
| `axis` | string | Axis locator `【AX-*】` (mutually exclusive with `section`) |
| `section` | string | Section locator `[F §n]` (mutually exclusive with `axis`) |

## Output

Verbatim axis/section text. Byte-identical for identical input.

## CLI backing

Backing tool: `tools.sot_read` (run via `python -m tools.sot_read --source final-research --axis "<arg>"` or `--section "<arg>"`). `--source` is fixed to `final-research`.

| Flag | Type | Description |
|---|---|---|
| `--source` | enum | `final-research` (fixed for this skill) |
| `--axis` | str | `【AX-*】` axis locator |
| `--section` | str | `[F §n]` section locator |
| `--root` | str | SOT root override (auto-detected if omitted) |

## Classification

**Deterministic script** — `【AX-*】` / `[F §n]` extraction by regex. No re-interpretation or summarization of evidence axes.

## SOT preservation

Read-only. Never writes any SOT axis.

## References

- workflow-coding.md §5.1.3 (this skill's specification)
- workflow-coding.md §14.1.2 #10 (CLI tool authoring convention)
