---
name: golden-corpus-curator
description: Phase-0 D4a corpus curation aid. Walks the owner through the workflow.md §7 authoring standard (8-12 minimal set, D1-D7 level anchors, seed-frozen, personal media forbidden, single non-expert self-consistency).
---

# golden-corpus-curator

A Phase-0, D4a corpus-curation aid. Walks the owner through the `workflow.md §7` authoring standard for the golden corpus: an 8–12 minimal set, D1–D7 level anchors, seed-frozen inputs, **no personal media**, and single non-expert self-consistency.

## When to invoke

- Phase-0 D4a: the owner needs guided help assembling the golden corpus.

## Owner-facing surface

Owner guidance is presented in Korean (carveout). Internal processing is English; the English original is authored first and the Korean owner-facing text is produced via `korean-translator` (§4.4.4). Migration timing is gated by `[INFRA-D-LANG-4]`.

## Classification

**LLM-judgment.** Guidance authoring and self-consistency review are not deterministic. No CLI backing tool.

## SOT preservation

Read-only against the SOT four axes (via the reader skills). Personal media is forbidden per `workflow.md §7` / PRD §7 NEVER.

## References

- workflow-coding.md §5.3.4 (this skill's specification)
- workflow.md §7 (authoring standard)
- PRD §7 (personal media NEVER)
