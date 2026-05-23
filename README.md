# shorts-forge — 자식 시스템 진입 README

> **부모-자식 분리 패턴**: 본 저장소(`impl/`)는 부모 유기체 *AgenticWorkflow*
> (만능줄기세포 코드베이스 = 방법론·프레임워크)에서 분화한 **자식 시스템
> shorts-forge** — 로컬 실행 YouTube Shorts 자동 생성 AI agentic workflow다.
> 부모 문서(접두어 `AGENTICWORKFLOW-*`)는 *어떻게* AI agentic workflow를
> 정의·검증·구축하는지 방법론을 다루고, 자식 문서(접두어 `SHORTS-FORGE-*`)는
> *무엇을* 만드는지 도메인 고유 아키텍처·메뉴얼을 다룬다. 본 README는 자식
> 시스템 문서 인덱스 = *진입점*이다.

## 자식 시스템 문서 3종 (먼저 읽을 곳)

| 무엇을 찾는가 | 어디로 | 누구를 위한 글 |
|---|---|---|
| 자식 시스템이 무엇인가 · 자매 문서 인덱스 · 정본 4축 위치 | [SHORTS-FORGE-README.md](SHORTS-FORGE-README.md) | 일반 독자 |
| 아키텍처 · 철학 · 4축 SOT · ANCHOR ①②③ · INVARIANT #1 · 8단계 결정론 척추 · 17 게이트 · 2계층 분리 · 의미 라우터 | [SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md](SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md) | 빌더·리뷰어 |
| "시작하자" 진입 · `run`/`--dry-run`/`selfcheck` · 복구 · FAQ · 한 페이지 치트시트 | [SHORTS-FORGE-USER-MANUAL.md](SHORTS-FORGE-USER-MANUAL.md) | 비전문가 소유자 |

## 어디로 가야 하는지 (주제별 길잡이)

| 알고 싶은 것 | 가는 곳 |
|---|---|
| **프로젝트 목적·범위** | [`SHORTS-FORGE-README.md` §1](SHORTS-FORGE-README.md) → 정본은 `../PRD.md §1.3` |
| **워크플로 구조** (8단계 척추 + LLM 단일 터치) | [`SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md` §6](SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md) → 정본은 `../workflow.md §1·§2` |
| **프로젝트 구조** (디렉토리·모듈) | 아래 §"저장소 구조" |
| **스킬·에이전트** (13 스킬 + 4 하니스 에이전트) | [`AGENTS.md`](AGENTS.md) |
| **Context Preservation System** (SOT 4축·decision-log·TRACEABILITY·build_state) | 아래 §"Context Preservation System" |
| **결정 현황·BLOCKING 게이트** | [`decision-log.md`](decision-log.md) → 정본은 `../PRD.md §12` |
| **사용자 진입·"시작하자"** | [`SHORTS-FORGE-USER-MANUAL.md`](SHORTS-FORGE-USER-MANUAL.md) ⚡ |

## 가장 빠른 시작

```bash
shorts-forge start "시작하자"
```

자세한 흐름은 [`SHORTS-FORGE-USER-MANUAL.md` ⚡ 가장 빠른 시작](SHORTS-FORGE-USER-MANUAL.md).

## 저장소 구조

```
impl/                       # 자식 시스템 = 본 저장소(git directory)
├── SHORTS-FORGE-README.md                     # ← 자식 시스템 개요
├── SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md # ← 자식 아키텍처·철학
├── SHORTS-FORGE-USER-MANUAL.md                # ← 사용자 메뉴얼
├── README.md                # ← 본 파일(진입 인덱스·자식 3종 안내)
├── CLAUDE.md                # 작업 규칙 정본(ANCHOR·SOT·2계층·게이트·언어)
├── AGENTS.md                # 에이전트 로스터·빌드 실행 모델
├── GEMINI.md                # 불가침 요약
├── decision-log.md          # PRD §12 BLOCKING 미러 + 세션 결정
├── docs/
│   ├── TRACEABILITY.md      # 모듈 ↔ PRD/workflow/AX/F/GATE
│   └── DESIGN-DECISIONS.md  # 가역 설계값
├── src/shorts_forge/        # 계층 B — 제품 파이프라인
│   ├── cli.py               # `selfcheck` / `run` / `start` 서브명령
│   ├── entry/               # 의미 라우터 + 안내 모드 (router·guide)
│   ├── spine/               # 8단계 결정론 척추 (statemachine·gates·edl·…)
│   ├── stages/              # S1 NORMALIZE … S7 VALIDATE
│   ├── llm/                 # 단일 LLM 메타 노드
│   ├── invariants/          # INVARIANT #1 강제 (netguard·encoding·runlock·…)
│   └── media/               # ffmpeg/probe/image_ops/tonemap 어댑터
├── tests/                   # 계층 A 계약 + 계층 B 제품·E2E·hook 통합
├── .claude/                 # 계층 A — 빌드 하니스 (agents·skills·hooks·state)
├── runtime_root_layout/     # 패키징 시 ProgramData 레이아웃 명세
└── licenses/                # 의존성 라이선스
```

부모 디렉토리 (`../`) = 자식 시스템의 *상위 SOT*:
```
../PRD.md                    # 요구·제약·수용 (v0.9)
../workflow.md               # 설계·8단계 척추·게이트 맵 (v0.6 본문 + currency)
../prd-research/final-research.md  # 근거 13축
```

## Context Preservation System (CPS)

자식 시스템은 *부모 방법론*에서 상속된 다음 메커니즘으로 컨텍스트를 보존한다:

| 보존 객체 | 어디에 | 어펜드-온리 강제 |
|---|---|---|
| 요구·제약·수용 (PRD) | `../PRD.md` | `tools/sot_guardian.py` + `sot-guardian-block.sh` 훅 (본문 바이트 수정 시 PreToolUse exit 2) |
| 설계·8단계 척추 (workflow) | `../workflow.md` | 동상 |
| 근거 13축 (연구) | `../prd-research/final-research.md` | 동상 |
| 모듈 ↔ PRD/workflow 추적 | `docs/TRACEABILITY.md` | `tests/traceability/test_cite_grep.py` + `traceability-update` 스킬 |
| 결정 결과 미러 | `decision-log.md` | 어펜드-온리·세션 §C |
| 빌드 실행 상태 | `.claude/state/build_state.sqlite` (5 테이블) | `python -m tools.build_state` 단일 쓰기 경로·raw SQL 0 |
| 결정 표면 4안 | `decision-surface` 스킬 (`.claude/skills/`) | 형식 강제(label/description/trade-off/preview) |
| 한·영 쌍 산출 | `*.en.md` + `*.ko.md` | `pair-write` 스킬 = SHA-256 앵커·멱등성·롤백 |
| 자동 메모리 (사용자 차원) | `~/.claude/projects/.../memory/MEMORY.md` | 부모 방법론 소관(자식 저장소 *외부*) |

원칙: **본문 0 번복**(어펜드-온리·X3 안정성 클래스). 새 발견은 셀 끝 어펜드 또는
신규 줄만 허용. 버전/상태 토큰의 in-place 정정만 예외.

## 스킬·에이전트 한눈에

자세한 로스터·실행 모델은 [`AGENTS.md`](AGENTS.md) 참조. 요약:

- **하니스 서브에이전트 4종** (`.claude/agents/`): `shorts-forge-build-orchestrator`·
  `tools-foundation-builder`·`korean-translator`·`impact-analyzer`.
- **스킬 13종** (`.claude/skills/`): `append-only`·`decision-surface`·`prd-read`·
  `workflow-read`·`final-research-read`·`glossary-lookup`·`traceability-update`·
  `translatability-precheck`·`intent-classifier`·`network-ledger-audit`·`pair-write`·
  `tdd-loop`·`golden-corpus-curator`.
- **훅 9종** (`.claude/hooks/`, PreToolUse 차단형 + PostToolUse 트리거형):
  `sot-guardian-block`·`network-egress-whitelist`·`pre-commit-pair-check` 등.

## 작업 규칙 (에이전트·기여자)

코드 작업 *전에* 반드시 읽는 정본:

- [`CLAUDE.md`](CLAUDE.md) — ABSOLUTE ANCHOR·SOT 4축·2계층·게이트 규율·언어 정책·
  sf-venv 테스트 명령.
- [`GEMINI.md`](GEMINI.md) — 불가침 7항 요약 (Gemini 에이전트용·CLAUDE.md 전문이
  우선).

## 운영 현황 (2026-05-24 기준)

- 테스트: **311 passed / 0 failed** (263 베이스라인 + 47 entry + 1 W5).
- Increment 1 (SM-1 수직 슬라이스 + INVARIANT #1) 베이스라인 GREEN.
- Phase-0 골든 코퍼스(D4a) = 소유자 소관·미제작.
- 잔존 BLOCKING 17건 (D17은 *해소 형태* 부분 진전). 자세히 = [`decision-log.md`](decision-log.md).

## 라이선스

[`LICENSE`](LICENSE) (배포 시 [`NOTICE`](NOTICE) + [`licenses/`](licenses/) 동봉
필수 — `C-LIC`).
