---
name: append-only
description: Currency-line writer — the single permitted path to SOT writes. Validates end-of-cell / new-line append position and the canonical (vX.Y currency YYYY-MM-DD) marker.
---

# append-only

Validate and apply an append-only currency line. This is the **single permitted path** that may write to a SOT axis, and it may only ever *append* a currency marker — never modify existing body text. Every other write to a SOT axis is blocked by the `sot-guardian` PreToolUse hook (§6.3).

## When to invoke

- A currency note must be appended to a SOT axis (PRD / workflow / final-research / TRACEABILITY) at an end-of-cell or new-line position.
- Never `Edit` / `Write` a SOT axis directly.

## Arguments

| Name | Type | Description |
|---|---|---|
| `target_file` | string | SOT axis file to append to |
| `target_anchor` | string | Anchor identifying the append site |
| `currency_text` | string | The currency note to append |
| `version` | string | `vX.Y` version marker |
| `x3_class` | string | X3-stability declaration (`currency·번복 아님·X3 안정성 클래스`) |

## Output

Diff preview; on owner confirmation, the append is applied.

## CLI backing

Backing tool: `tools.append_only` (run via `python -m tools.append_only --target <file> --anchor <id> --version <vX.Y> --currency-text <text>`).

| Flag | Type | Description |
|---|---|---|
| `--target` | str | SOT axis file (maps to `target_file`) |
| `--anchor` | str | Append-site anchor (maps to `target_anchor`) |
| `--version` | str | `vX.Y` version marker |
| `--currency-text` | str | Currency note text |

## Classification

**Deterministic validator.** The currency marker is recognized by a single canonical regex `\(v\d+\.\d+ currency \d{4}-\d{2}-\d{2}·번복 아님·X3 안정성 클래스\)` plus a deterministic cell-end / new-line position check. The v0.1 "LLM naturalness assist" was removed (v0.5): ambiguity = failure, per ANCHOR ①.

## SOT preservation

This is the *only* permitted SOT write path, and it only appends currency markers — body text is never modified. Append position and marker format are enforced deterministically.

## References

- workflow-coding.md §5.2.2 (this skill's specification)
- workflow-coding.md §6.3 (sot-guardian blocks all other SOT writes)
- workflow-coding.md §16 IQ-27 (CLI single-path lock)
