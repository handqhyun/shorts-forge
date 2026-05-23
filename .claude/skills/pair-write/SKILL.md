---
name: pair-write
description: Atomically commit English-original + Korean-translation pair (*.en.md + *.ko.md siblings) with SHA-256 anchors, idempotency, and rollback. Single permitted write path for any bilingual artifact.
---

# pair-write

Atomically commit an English-original + Korean-translation pair to the build artifact zone. Single permitted path for any `*.en.md` + `*.ko.md` sibling write produced by stage / cross-cutting / quality / meta subagents. Rejects half-pair writes and SOT-axis paths.

## When to invoke

Invoke this skill whenever a subagent produces a bilingual artifact:

- `korean-translator` (§4.4.4) — after generating a translation
- `blocking-surfacer` (§4.4.2) — after producing a 4-option decision surface
- `adr-recorder` (§4.3.3) — once IQ-16 일괄 마이그레이션 Stage B step 4 reaches ADR artifacts
- Any stage / cross-cutting builder producing bilingual documentation

**Never** call `Write` or `Edit` directly on `*.en.md` / `*.ko.md` paths. Direct writes are blocked by `code-reviewer` per §13.5.6(e).

## Arguments

| Name | Type | Description |
|---|---|---|
| `en_path` | string | Absolute path ending `.en.md` |
| `en_content` | string | English original (verbatim) |
| `ko_path` | string | Sibling: same basename, `.ko.md` suffix, same parent directory |
| `ko_content` | string | Korean translation |
| `step_id` | string | Artifact identifier (e.g., `adr-014`, `gate-d14-2026-05-20`) |
| `build_run_id` | string | UUID v4 from `build_runs` |
| `task_id` | string \| null | UUID v4 from `build_tasks` (nullable for non-task artifacts) |
| `ko_status` | enum | `'ok'` (strict default per IQ-15 RESOLVED) or `'pending'` (only when translator deferred per lenient-mode carveout) |

## Output

```json
{
  "en_sha": "...",
  "ko_sha": "...",
  "ts_en": "2026-05-20T...",
  "ts_ko": "2026-05-20T...",
  "pair_row_id": "(build_run_id, step_id, en_path)",
  "atomicity_ok": true
}
```

## Behavior

### 1. Sibling-convention validation (IQ-13 RESOLVED 2026-05-20)

- `en_path` ends `.en.md`
- `ko_path` is the same basename with `.ko.md` suffix
- `dirname(en_path) == dirname(ko_path)`
- Reject otherwise with `atomicity_ok=false`.

### 2. Write-zone validation (strict whitelist)

Allowed:

- `impl/.claude/runs/**`
- `impl/docs/**`
- `prompt/decisions/**`

Rejected (sot-guardian PreToolUse hook also blocks; this skill rejects first as defense-in-depth):

- `prompt/PRD.md`
- `prompt/workflow.md`
- `prompt/prd-research/final-research.md`
- `prompt/impl/docs/TRACEABILITY.md`

### 3. SHA-256 computation

- `en_sha = sha256(en_content)`
- `ko_sha = sha256(ko_content)` (only if `ko_status='ok'`)

### 4. Idempotency check

Query `pair_outputs` for matching `(build_run_id, step_id, en_path)`. If existing row has the same `en_sha` and `ko_status='ok'`, return the cached result; perform no write.

### 5. Atomic commit

- Write `en_path` first.
- If `ko_status='ok'`: write `ko_path` second. On failure → delete `en_path` (rollback) and return `atomicity_ok=false`.
- If `ko_status='pending'`: keep `en_path`; do not write `ko_path`; mark the row for the recovery-observability-builder retry queue.

### 6. `pair_outputs` row upsert

```sql
INSERT INTO pair_outputs
  (build_run_id, task_id, step_id, en_path, ko_path,
   en_sha, ko_sha, ko_status, ko_attempts, ts_en, ts_ko)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (build_run_id, step_id, en_path) DO UPDATE SET
  en_sha = excluded.en_sha,
  ko_sha = COALESCE(excluded.ko_sha, ko_sha),
  ko_status = excluded.ko_status,
  ko_attempts = ko_attempts + (CASE WHEN excluded.ko_status = 'failed' THEN 1 ELSE 0 END),
  ts_en = excluded.ts_en,
  ts_ko = COALESCE(excluded.ts_ko, ts_ko);
```

## CLI backing

Backing tool: `tools.pair_write` (run via `python -m tools.pair_write --en-path <p> --en-content-file <p> --ko-path <p> --ko-content-file <p> --step-id <id> --build-run-id <id> --task-id <id> --ko-status <ok|pending>`). Large bodies are passed by file (`--en-content-file` / `--ko-content-file`) rather than inline, so the CLI surface differs from the skill's logical `en_content` / `ko_content` arguments above.

| Flag | Type | Description |
|---|---|---|
| `--en-path` | str | English path ending `.en.md` |
| `--en-content-file` | str | File holding the English original body |
| `--ko-path` | str | Sibling `.ko.md` path |
| `--ko-content-file` | str | File holding the Korean translation body |
| `--step-id` | str | Artifact identifier |
| `--build-run-id` | str | `build_runs` id |
| `--task-id` | str | `build_tasks` id (nullable) |
| `--ko-status` | enum | `ok` (strict) / `pending` |
| `--db` | str | build_state db (default `impl/.claude/state/build_state.sqlite`) |
| `--now` | str | ISO-8601 timestamp override (determinism) |

## Classification

**Deterministic verification + deterministic commit.** Zero LLM calls. Translation itself is performed separately by the `korean-translator` subagent; this skill handles only the atomic commit.

## SOT preservation

The write-zone whitelist is enforced deterministically. SOT four-axis paths are rejected by this skill and additionally by the `sot-guardian` PreToolUse hook (defense in depth).

## RLM alignment

- **Idempotency**: `(build_run_id, step_id, en_path)` PK uniqueness; same `en_sha` re-invocation is a no-op.
- **Recovery**: failed Korean write leaves a `ko_status='pending'` row for the retry queue. English original is authority — re-translation is always possible without re-running the producing subagent.
- **Determinism**: SHA-256 anchors and atomic-commit semantics are 100 % deterministic.

## References

- workflow-coding.md §5.3.5 (this skill's specification)
- workflow-coding.md §3.4 (`pair_outputs` schema)
- workflow-coding.md §4.4.4 (`korean-translator` invokes this skill)
- workflow-coding.md §13.5 (bilingual pair operation)
- workflow-coding.md §16 IQ-13 / IQ-15 (RESOLVED 2026-05-20)
