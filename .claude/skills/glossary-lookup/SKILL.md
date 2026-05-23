---
name: glossary-lookup
description: Read-write single path to impl/.claude/state/glossary.json. Computes glossary_drift for a translation by comparing English->Korean term pairings against accepted history. Append-only after Stage C freeze.
---

# glossary-lookup

The single read-write path to `impl/.claude/state/glossary.json`. Computes `glossary_drift` for the current translation by comparing English → Korean term pairings against historically accepted pairings. Append-only after the Stage C freeze (`frozen=true`).

## When to invoke

- `korean-translator` (§4.4.4) — `mode='check-drift'` while translating, then `mode='append'` for new accepted terms.
- `translation-verifier` (§4.4.5) — `mode='check-drift'` on re-verification.
- Never read or write `glossary.json` directly.

## Arguments

| Name | Type | Description |
|---|---|---|
| `term_pairs` | array | List of `{en_term, ko_term, source_pair_row_id}` |
| `mode` | enum | `lookup` / `append` / `check-drift` |

## Output

- `lookup`: `LookupResult{matched, missing}`
- `append`: `AppendResult{appended, rejected_post_freeze}` (rejects new terms once frozen)
- `check-drift`: `DriftReport{drift_count, drift_pairs}`

## CLI backing

Backing tool: `tools.glossary` (run via `python -m tools.glossary --mode <lookup|append|check-drift> --term-pairs <json>`).

| Flag | Type | Description |
|---|---|---|
| `--mode` | enum | `lookup` / `append` / `check-drift` (maps to `mode`) |
| `--term-pairs` | str | JSON array of term pairs (maps to `term_pairs`) |
| `--store` | str | glossary.json path (default `impl/.claude/state/glossary.json`) |

## Classification

**Deterministic script** — JSON read/write, exact-match hash comparison, `frozen` flag. Zero LLM calls; term matching is character-exact (no synonym generalization, which would mask drift).

## SOT preservation

Write zone = `impl/.claude/state/glossary.json` only (outside the SOT four axes). Not matched by the sot-guardian SOT fileMatcher.

## References

- workflow-coding.md §5.3.7 (this skill's specification)
- workflow-coding.md §4.4.4 / §4.4.5 (callers)
- workflow-coding.md §13.5.8.1 (Stage C freeze policy)
