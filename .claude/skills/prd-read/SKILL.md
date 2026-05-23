---
name: prd-read
description: Parse prompt/PRD.md and extract a requested section verbatim. Single source of truth for PRD content; no other subagent reads PRD.md directly.
---

# prd-read

Extract a requested section of `prompt/PRD.md` verbatim. This is the **single permitted path** to PRD content — every subagent that needs PRD text invokes this skill rather than reading `PRD.md` directly. Centralizing the parse removes the per-caller interpretation drift that a raw `Read` would introduce.

## When to invoke

- The orchestrator or any subagent needs a PRD gate, invariant, or section (e.g. `§12-D14`, `§4 INVARIANT #1`, `§8 GATE`).
- Never `Read` `prompt/PRD.md` directly — route through this skill so the extraction is deterministic and citable.

## Arguments

| Name | Type | Description |
|---|---|---|
| `section` | string | Section locator — ATX header (`## 12. BLOCKING`) or table-row anchor (`§12-D14`) |

## Output

Verbatim section text plus metadata (`version`, `last-currency`). Byte-identical for identical input.

## CLI backing

Backing tool: `tools.sot_read` (run via `python -m tools.sot_read --source PRD --section "<arg>"`). `--source` is fixed to `PRD` for this skill; the remaining flags are the shared `sot_read` surface.

| Flag | Type | Description |
|---|---|---|
| `--source` | enum | `PRD` (fixed for this skill) |
| `--section` | str | Section locator passed through from `section` |
| `--axis` | str | Unused for PRD (final-research axis selector) |
| `--root` | str | SOT root override (auto-detected if omitted) |

## Classification

**Deterministic script** — `§N` header regex + verbatim byte slice. Zero LLM calls; no summarization or paraphrase of SOT content.

## SOT preservation

Read-only. Never writes any SOT axis. Output preserves the Korean SOT body verbatim inside an English citation container (titles/metadata only are rendered in English).

## References

- workflow-coding.md §5.1.1 (this skill's specification)
- workflow-coding.md §14.1.2 #10 (CLI tool authoring convention)
- workflow-coding.md §16 IQ-24 / IQ-25 (CLI single-path lock)
