# AGENTS.md — shorts-forge 에이전트 로스터·협업 규약

작업 규칙(ANCHOR·SOT·2계층·게이트·언어)은 [CLAUDE.md](CLAUDE.md)가 정본이다. 이
파일은 *에이전트 구성*과 협업 규약을 다룬다.

## 문서 위상 (2026-05-24 자식 시스템 문서 분리)

본 AGENTS.md는 *에이전트 내부 문서*(로스터·실행 모델·신규 에이전트 규약)다.
자식 시스템 사용자·빌더·소유자를 위한 진입 문서는 별도 — `SHORTS-FORGE-*` 접두어
3종(부모 *AgenticWorkflow* 방법론 문서 `AGENTICWORKFLOW-*`와 분리):

| 대상 | 진입 문서 |
|---|---|
| 자식 시스템 개요·자매 문서 인덱스 | [SHORTS-FORGE-README.md](SHORTS-FORGE-README.md) |
| 아키텍처·철학 통합 | [SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md](SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md) |
| 사용자 메뉴얼 (`"시작하자"` 진입) | [SHORTS-FORGE-USER-MANUAL.md](SHORTS-FORGE-USER-MANUAL.md) |

**신규 에이전트가 만드는 사용자 대면 산출**(메뉴얼·아키텍처 설명·비전문가 안내)
은 위 3종에 어펜드해야 한다 — 본 AGENTS.md·CLAUDE.md·GEMINI.md에 사용자 대면
설명을 누적하지 않는다(역할 분리·X3 안정성).

## 실행 모델

"Product Build"의 엔진은 yaml 이 아니라 **orchestrator 서브에이전트 + SQLite 상태**다.

- 상태: `.claude/state/build_state.sqlite` (5테이블: `build_runs`·`build_tasks`·
  `build_decisions`·`build_forks`·`pair_outputs`). 쓰기는 **반드시**
  `python -m tools.build_state <subcmd>`(cwd=`.claude`·raw SQL 0).
- 레지스트리 등가물: 런타임 게이트 = `src/shorts_forge/spine/gates.py`(D1–D16),
  빌드타임 = `build_decisions`(D17), 추적 = `docs/TRACEABILITY.md`.
- `state.yaml`·`step-registry.yaml`은 **존재하지 않으며 만들지 않는다** (GATES +
  TRACEABILITY 가 이미 레지스트리). 이를 전제하는 지시는 거짓 전제로 취급.

## 하니스 서브에이전트 (`.claude/agents/` — 4종)

| 에이전트 | 역할 | 비고 |
|---|---|---|
| `shorts-forge-build-orchestrator` | 빌드 페이즈 진행·태스크 디스패치·게이트 점검 | `build_state` 단일 쓰기경로 사용 |
| `tools-foundation-builder` | 계층 A 도구(.py) 빌드 | 영어-only 규약 보유 |
| `korean-translator` | 영어 원본 → `*.ko.md` 쌍 생성 | `pair-write`로 원자적 쌍 기록 |
| `impact-analyzer` | `src/` 변경 영향분석(단일 도구 디스패치) | `tools/impact_analyze.py` relay·LLM 손수계산 0 |

## 결손 에이전트 (빌드 전진 범위 제한)

`blocking-surfacer`(F-21 dead-end)·`translation-verifier`(§4.4.5 ko 'ok' 승격자)·
Phase-1 제품 빌더(~18종: tdd-test-author·code-reviewer·traceability-auditor·
스테이지 빌더 등) **미생성**. 결손 에이전트에 의존하는 게이트(예: §8 task-verification
게이트1~4·gate5 ko 'ok')는 결정론 강제 불가 구간이 있음 — [decision-log.md](decision-log.md) 참조.

## 신규 에이전트 생성 규약

- **언어**: system prompt·산출 커밋은 영어 단일(§4.1 공통 spec 언어규약).
  `tools-foundation-builder` 동형. 미반영 시 orchestrator 책임 #2에 "§4.1 언어규약
  주입" 1줄 추가(별 turn·승인).
- **추적**: 에이전트가 만드는 `src/` 모듈은 `TRACE` dict 필수(ANCHOR ①).
- **게이트**: BLOCKING 영역은 코드로 결정하지 말고 `@gate_blocked` 차단 + 소유자
  4안 표면화.
- **품질 분리**: 자기 코드 자기 리뷰 금지 — 독립 `code-reviewer` 디스패치(에이전트
  품질 분리, B-6 회귀 방지).

## 훅 (`.claude/hooks/` — 9종, 얇은 래퍼 → `python3 -m tools.X`)

PreToolUse(차단형): `sot-guardian-block`(SOT diff 강제 exit 2)·
`network-egress-whitelist`(INVARIANT #1 egress deny)·`pre-commit-pair-check`(쌍 위반 차단).
PostToolUse/Stop/SessionStart(트리거): `korean-translator-trigger`·`impact-trigger`·
`code-review-and-ratchet`·`persist-pending-decisions`·`load-context-from-sot`·
`sot-guardian-integrity-check`. `.sh` 래퍼 통합 검증 = `tests/hooks/test_hook_wrappers.py`.

## 스킬 (`.claude/skills/` — 13종)

`append-only`·`decision-surface`·`prd-read`·`workflow-read`·`final-research-read`·
`glossary-lookup`·`traceability-update`·`translatability-precheck`·`intent-classifier`·
`network-ledger-audit`·`pair-write`·`tdd-loop`·`golden-corpus-curator`.
