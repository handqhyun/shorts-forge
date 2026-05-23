---
name: traceability-update
description: Append-only update of impl/docs/TRACEABILITY.md. Validates the TRACE dict of a modified module before producing the append preview.
---

# traceability-update

Produce an append-only update to `impl/docs/TRACEABILITY.md` for a modified module, after validating that module's `TRACE` dict (D-TR convention). The append format is deterministic so the traceability ledger stays machine-greppable.

## When to invoke

- A module under `impl/src/` (or `impl/.claude/tools/`) was added or changed and its traceability row must be recorded.

## Arguments

| Name | Type | Description |
|---|---|---|
| `module` | string | Path to the modified module |
| `currency` | string | Currency note for the append |

## Output

A preview of the append-only TRACEABILITY.md entry. `TRACEABILITY.md` is a SOT axis — the actual write is gated and never performed inline by this skill.

## CLI backing

Backing tool: `tools.traceability_update` (run via `python -m tools.traceability_update --module <path> --currency <text>`).

| Flag | Type | Description |
|---|---|---|
| `--module` | str | Modified module path (maps to `module`) |
| `--currency` | str | Currency note (maps to `currency`) |

## Classification

**Deterministic script** — `TRACE` dict AST validation + append-only formatting. The append format is never varied by an LLM.

## SOT preservation

`impl/docs/TRACEABILITY.md` is a SOT axis: this skill validates and previews only; the gated write goes through the append-only path. No inline SOT write.

## References

- workflow-coding.md §5.3.3 (this skill's specification)
- workflow-coding.md §4.3.4 (traceability-auditor enforcement)
- workflow-coding.md §14.1.2 #9 (TRACE dict 5 fields)
