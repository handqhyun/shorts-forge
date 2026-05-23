-- impl/.claude/state/schema.sql
-- Build infrastructure state schema for shorts-forge build orchestrator.
-- Reference: workflow-coding.md §3.4.
-- Distinct from runtime SQLite (workflow.md §4); append-only growth policy.
-- IQ-11 RESOLVED 2026-05-20: SQLite chosen as build_state store.
--
-- (v0.9.6 currency 2026-05-21·번복 아님·X3 안정성 클래스·F-1 해소·token 부패 정정)
-- Phase-(-0.75) tools-foundation-builder correction: pair_outputs.ko_status CHECK
-- enum corrected from the 3-value set ('pending','ok','failed') to the 4-value set
-- ('pending','produced','ok','failed') per workflow-coding.md §3.4 v0.4 currency.
-- The 'produced' state is the intermediate set by korean-translator before
-- translation-verifier (§4.4.5) promotes it to 'ok'. This is an in-place token
-- correction under workflow-coding.md §11.2 exception class (no decision overturn,
-- X3 stability class) — body otherwise unchanged.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS build_runs (
  build_run_id TEXT PRIMARY KEY,
  -- (v0.9.6 currency 2026-05-21·번복 아님·X3 안정성 클래스·F-33 해소·token 부패 정정)
  -- phase enum extended from v0.1 4-value set to include Phase-(-0.5) (§15.1.5 v0.4)
  -- and Phase-(-0.75) (§15.1.8 v0.9.2). In-place token correction under §11.2
  -- exception class — no decision overturn, X3 stability class.
  phase TEXT NOT NULL CHECK (phase IN ('-1', '-0.75', '-0.5', '0', '1', '2+')),
  started_at TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('running', 'halted_on_gate', 'completed', 'failed')),
  halted_gate TEXT
);

CREATE TABLE IF NOT EXISTS build_tasks (
  task_id TEXT PRIMARY KEY,
  build_run_id TEXT NOT NULL REFERENCES build_runs(build_run_id),
  subagent_name TEXT NOT NULL,
  stage TEXT,
  status TEXT NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'timeout')),
  red_test_path TEXT,
  artifact_path TEXT,
  last_heartbeat_at TEXT,
  created_at TEXT NOT NULL,
  completed_at TEXT
);

CREATE TABLE IF NOT EXISTS build_decisions (
  decision_id TEXT PRIMARY KEY,
  build_run_id TEXT NOT NULL REFERENCES build_runs(build_run_id),
  decision_type TEXT NOT NULL CHECK (decision_type IN ('BLOCKING', 'DESIGN', 'INFRA-DESIGN')),
  gate_id TEXT,
  surface_md_path TEXT,
  owner_resolved_at TEXT,
  resolution_text TEXT
);

CREATE TABLE IF NOT EXISTS build_forks (
  fork_id TEXT PRIMARY KEY,
  build_run_id TEXT NOT NULL REFERENCES build_runs(build_run_id),
  design_question TEXT NOT NULL,
  worktree_path TEXT NOT NULL,
  branch_name TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('running', 'merged', 'discarded')),
  adr_appended_at TEXT
);

-- v0.2 currency append: english-original + korean-translation pair tracking.
-- Reference: workflow-coding.md §13.5 / §4.4.4 korean-translator / §5.3.5 pair-write.
-- IQ-13 RESOLVED 2026-05-20: sibling-file 1:1 (.en.md + .ko.md).
-- IQ-14 RESOLVED 2026-05-20: per-step translation.
-- IQ-15 RESOLVED 2026-05-20: strict (ko_status='ok' required for step completion).
CREATE TABLE IF NOT EXISTS pair_outputs (
  build_run_id TEXT NOT NULL REFERENCES build_runs(build_run_id),
  task_id TEXT REFERENCES build_tasks(task_id),
  step_id TEXT NOT NULL,
  en_path TEXT NOT NULL,
  ko_path TEXT NOT NULL,
  en_sha TEXT NOT NULL,
  ko_sha TEXT,
  ko_status TEXT NOT NULL CHECK (ko_status IN ('pending', 'produced', 'ok', 'failed')),
  ko_attempts INTEGER NOT NULL DEFAULT 0,
  ts_en TEXT NOT NULL,
  ts_ko TEXT,
  PRIMARY KEY (build_run_id, step_id, en_path)
);

-- (v0.9.6 currency 2026-05-21) F-22 minor resolution: lookup index for the
-- PostToolUse korean-translator-trigger idempotency query (en_path + en_sha).
CREATE INDEX IF NOT EXISTS idx_pair_outputs_en_path_sha
  ON pair_outputs (en_path, en_sha);
