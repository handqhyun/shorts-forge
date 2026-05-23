---
name: network-ledger-audit
description: Enforce INVARIANT #1 — scan impl/src for forbidden network imports (requests/urllib/httpx/aiohttp outside the netguard carveout) and scan the runtime ledger for non-carveout egress.
---

# network-ledger-audit

Enforce INVARIANT #1 (no network). Scans a Python source tree (AST) for forbidden network imports outside the `invariants/netguard.py` carveout, and scans the runtime network ledger for non-carveout egress events. INVARIANT #1 is non-negotiable, so the scan is deterministic AST — a single missed import is an RLM breach.

## When to invoke

- Before a stage/cross-cutting builder is marked complete (gate evidence).
- Whenever `impl/src/**/*.py` changes, to confirm no network import was introduced.

## Arguments

| Name | Type | Description |
|---|---|---|
| `src` | string | Source tree to scan (default `impl/src/`) |
| `ledger` | string | Runtime network ledger JSON path (optional) |

## Output

`AuditReport{forbidden_imports: list, ledger_violations: list, invariant1_ok: bool}`.

## CLI backing

Backing tool: `tools.netguard_audit` (run via `python -m tools.netguard_audit --src impl/src/ --ledger impl/.claude/state/network-ledger.json`).

| Flag | Type | Description |
|---|---|---|
| `--src` | str | Source tree to scan (maps to `src`) |
| `--ledger` | str | Network ledger JSON path (maps to `ledger`) |

## Classification

**Deterministic script** — `ast.walk` import nodes + forbidden-prefix match + carveout whitelist + ledger JSON parse. Zero LLM calls.

## SOT preservation

Read-only. INVARIANT #1 (RLM) enforcement.

## References

- workflow-coding.md §5.3.2 (this skill's specification)
- workflow-coding.md §4.2.6 Exit contract (d) (gate evidence)
- workflow-coding.md §14.1.2 #10 (CLI tool authoring convention)
