---
name: tdd-loop
description: RED -> GREEN -> REFACTOR loop. Runs the test runner, checks the ratchet, and surfaces regressions deterministically.
---

# tdd-loop

Drive a RED → GREEN → REFACTOR loop for a stage or module. Runs the test suite, compares the ratchet metrics, and surfaces any regression. Test outcomes are read from the runner's machine output — never inferred.

## When to invoke

- A stage-builder has authored a RED test and needs the RED → GREEN transition verified.
- A change must be checked against the ratchet (`impl/tests/ratchet.json`) for regression.

## Arguments

| Name | Type | Description |
|---|---|---|
| `test_path` | string | Path to the test file or directory |
| `impl_path` | string | Path to the implementation under test |
| `ratchet_path` | string | Path to `ratchet.json` |

## Output

`TestResult{red_pass, green_pass, ratchet_status}`.

## CLI backing

Backing tool: `tools.tdd_loop` (run via `python -m tools.tdd_loop --test-path <p> --impl-path <p> --ratchet-path <p>`).

| Flag | Type | Description |
|---|---|---|
| `--test-path` | str | Test file/dir (maps to `test_path`) |
| `--impl-path` | str | Implementation path (maps to `impl_path`) |
| `--ratchet-path` | str | Ratchet JSON path (maps to `ratchet_path`) |

## Classification

**Deterministic script** — runs the test runner (pytest if present, else `unittest`, graceful degradation) and diffs ratchet numbers. The runner's pass/fail and the numeric ratchet comparison are never LLM-interpreted.

## SOT preservation

Read-only against SOT. Operates on `impl/tests/` and `impl/src/`.

## References

- workflow-coding.md §5.3.1 (this skill's specification)
- workflow-coding.md §6.5 (code-review-and-ratchet hook caller)
- workflow-coding.md §14.1.2 #10 (CLI tool authoring convention)
