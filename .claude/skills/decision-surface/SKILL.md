---
name: decision-surface
description: Render a BLOCKING decision into a 4-option Korean decision surface (label / description / preview) for the owner. Surfaces; never decides.
---

# decision-surface

Render a BLOCKING decision into the `feedback-decision-surface` 4-option Korean surface (핵심 / 왜 / 트레이드오프 / 다음 결과). The compression from a technical gate state to a non-technical 4-option choice is the LLM-judgment core of this skill. It surfaces the decision for the owner; it never decides.

## When to invoke

- `blocking-surfacer` (§4.4.2) needs to present a `[GATE:D*]` to the owner as four mutually-exclusive options.

## Arguments

| Name | Type | Description |
|---|---|---|
| `gate_id` | string | Gate identifier (e.g. `D14`) |
| `context_md` | string | Current gate state as markdown |

## Output

`prompt/decisions/<gate-id>-<timestamp>.md` (4-option Korean) plus an `AskUserQuestion` payload. The English original is authority; the Korean is the rendered surface (produced via `korean-translator` and committed via `pair-write`).

## Classification

**LLM-judgment.** The technical → non-technical 4-option compression cannot be done deterministically. No CLI backing tool — this skill is pure LLM-judgment.

## SOT preservation

Read-only against the SOT four axes. Writes only `prompt/decisions/<gate-id>-<timestamp>.{en,ko}.md` via the `pair-write` skill (§5.3.5). The decision itself is the owner's; this skill produces the surface only.

## References

- workflow-coding.md §5.2.1 (this skill's specification)
- workflow-coding.md §4.4.2 (blocking-surfacer caller)
- feedback-decision-surface (4-option format)
