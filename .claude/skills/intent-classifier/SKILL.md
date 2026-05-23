---
name: intent-classifier
description: Classify owner input intent into 5 categories (BLOCKING / [DESIGN] / [INFRA-DESIGN] / build-progress / meta-question) and surface for owner confirmation. Decides 0.
---

# intent-classifier

Classify owner input intent into one of five categories and surface the classification for **owner confirmation only**. This skill identifies; it does not decide. Single permitted path for orchestrator `§3.2 책임 8`.

## Categories (IQ-17 RESOLVED 2026-05-20: 5)

| Category | Meaning | Routing on confirmation |
|---|---|---|
| `BLOCKING` | New owner-only policy decision (D1–D17 class) | blocking-surfacer |
| `[DESIGN]` | Implementation choice that requires ADR | fork mechanism + adr-recorder |
| `[INFRA-DESIGN]` | Build-infrastructure choice (IQ-1~19 class) | blocking-surfacer (decision-surface 4-option) |
| `build-progress` | Move the build forward (next stage, run task) | orchestrator dispatch |
| `meta-question` | Question, status query, confirmation | answer in place; no task |

## Arguments

| Name | Type | Description |
|---|---|---|
| `raw_input_text` | string | Owner input verbatim |
| `current_open_gates` | array | Subset of D1..D17 currently open |
| `current_open_iqs` | array | Subset of IQ-1..IQ-19 currently open |
| `last_session_phase` | string | `-1` / `0` / `1` / `2+` |

## Output

```json
{
  "intent_category": "BLOCKING" | "[DESIGN]" | "[INFRA-DESIGN]" | "build-progress" | "meta-question",
  "linked_gate_id": "D14" | null,
  "linked_iq_id": "IQ-3" | null,
  "linked_section_id": "§4.3.5" | null,
  "ambiguity_level": "clear" | "multi-intent" | "undecidable",
  "confirmation_payload_en_md": "...",
  "confirmation_payload_ko_md": "..."
}
```

## Behavior

### 1. Topic matching (hybrid: deterministic + LLM-judgment)

- Substring + keyword match against §16 IQ table topics
- Substring + keyword match against PRD §12 gate-table topics
- Substring + keyword match against workflow.md §10 gate map
- Substring + keyword match against §17 traceability table

### 2. Ambiguity classification

- Multiple matches → `ambiguity_level='multi-intent'` → route to `blocking-surfacer` for 4-option disambiguation
- Zero matches → `ambiguity_level='undecidable'` → route to `blocking-surfacer`
- Single match → `ambiguity_level='clear'`

### 3. Confirmation surface (only when `clear`)

- Author English original at `prompt/decisions/intent-<ts>.en.md`
- Invoke `korean-translator` (§4.4.4) for the Korean pair
- Owner-facing render via `AskUserQuestion` shows the Korean translation only
- Wait for owner confirmation; emit no further action until confirmed

### 4. Post-confirmation

- Orchestrator initiates the routed path (`blocking-surfacer` / `fork` / `adr-recorder` / `dispatch` / inline answer)
- The decision itself is **not** in this skill's scope

## CLI backing

Backing tool: `tools.intent_prefilter` (run via `python -m tools.intent_prefilter --raw-input <text>`). The deterministic prefilter handles only the substring/keyword pass and the `undecidable` short-circuit; the remaining logical arguments above feed the LLM classification step, not the CLI.

| Flag | Type | Description |
|---|---|---|
| `--raw-input` | str | Owner input verbatim (maps to `raw_input_text`) |

## Classification

**Hybrid.** Substring / keyword matching = deterministic. Intent-category classification = LLM-judgment (multi-intent detection cannot be fully deterministic — quality priority per §0 #1).

## SOT preservation

- Read-only against SOT four axes (via `prd-read` / `workflow-read` / `final-research-read` skills)
- Writes only `prompt/decisions/intent-<ts>.{en,ko}.md` via the `pair-write` skill (§5.3.5)

## Caller restriction

Only the orchestrator (per §3.2 책임 8) may invoke this skill. Other subagents must not call this skill — intent classification is the orchestrator's single authority (autonomous-N+1 avoidance per `feedback-l3-b-branch`).

## References

- workflow-coding.md §5.2.3 (this skill's specification)
- workflow-coding.md §3.2 책임 8 (orchestrator caller)
- workflow-coding.md §16 IQ-17 (category count, RESOLVED 2026-05-20)
- workflow-coding.md §13.5 (bilingual pair operation)
