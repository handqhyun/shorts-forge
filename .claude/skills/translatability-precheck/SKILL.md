---
name: translatability-precheck
description: Validate the translatability of an English original before commit. Runs before pair-write emits the English commit; deterministic identifier/structure/marker checks plus an LLM ambiguity pass.
---

# translatability-precheck

Validate that an English original is safe to translate *before* it is committed via `pair-write`. Early detection here shortens the decision distance that would otherwise be spent on three failed `korean-translator` retries (ANCHOR ① quality-first).

## When to invoke

- A producing subagent has an English artifact ready and is about to call `pair-write` (§5.3.5). Run this skill first, exactly once. A `verdict='fail'` blocks the `pair-write` call.

## Arguments

| Name | Type | Description |
|---|---|---|
| `en_content` | string | English original text |
| `en_path_intended` | string | Intended commit path |
| `step_id` | string | Artifact identifier |
| `category` | enum | `4-option-decision-surface` / `adr-body` / `owner-guide` / `subagent-output` / `currency-marker` |

## Output

`PrecheckReport{verdict: 'pass'|'fail', failed_axes: list, ambiguity_score: float, identifier_integrity_ok: bool, structure_ok: bool, markers_ok: bool}`.

## CLI backing

Backing tool: `tools.translatability_precheck` (run via `python -m tools.translatability_precheck --en-content <text> --category <category>`). The tool performs the deterministic (a)–(d) checks; the LLM (e)–(g) pass runs only on input that clears the deterministic prefilter.

| Flag | Type | Description |
|---|---|---|
| `--en-content` | str | English original (maps to `en_content`) |
| `--category` | enum | Artifact category (maps to `category`) |

## Classification

**Hybrid** — (a) identifier integrity (`§N.M`, `[GATE:D*]`, `ADAPT-*`), (b) code-block / shell / path integrity, (c) currency-marker regex, (d) 4-option structure are deterministic. (e) ambiguity, (f) Korean-style English, (g) ANCHOR-violation vocabulary are LLM-judgment, gated behind the deterministic prefilter.

## SOT preservation

Read-only — `en_content` is an argument, no disk write (pre-commit stage). No SOT access.

## References

- workflow-coding.md §5.3.6 (this skill's specification)
- workflow-coding.md §5.3.5 (pair-write, gated by this skill's verdict)
- workflow-coding.md §4.4.5 (translation-verifier downstream)
