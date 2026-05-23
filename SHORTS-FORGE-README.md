# SHORTS-FORGE-README.md — 자식 시스템 개요

> **부모-자식 분리 패턴**: 본 저장소(`impl/`)는 부모 유기체 **AgenticWorkflow**
> (만능줄기세포 코드베이스 = 방법론·프레임워크)에서 분화한 **자식 시스템
> shorts-forge**(도메인 = 로컬 실행 YouTube Shorts 자동 생성)다. 부모는 *어떻게*
> AI agentic workflow를 정의·검증·구축하는지(방법론)를 다루고, 자식은 *무엇을*
> 만드는지(도메인 고유 척추·게이트·산출물)를 다룬다. 본 README와 자매 두 문서
> (`SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md`·`SHORTS-FORGE-USER-MANUAL.md`)
> 는 부모 문서(접두어 `AGENTICWORKFLOW-*`)와 *파일명 충돌 없이* 자식 시스템을
> 독립 이해·운영 가능하게 한다.

## 자매 문서 (자식 시스템 3종)

| 무엇을 찾는가 | 어디로 |
|---|---|
| **자식 시스템 개요 (본 문서)** | 본 문서 |
| 아키텍처·철학 (4축 SOT·ANCHOR·INVARIANT·8단계 척추·17 게이트·2계층·의미 라우터) | [SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md](SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md) |
| 사용자 메뉴얼 (`"시작하자"` 진입·`run`/`--dry-run`/`selfcheck`·복구·FAQ·치트시트) | [SHORTS-FORGE-USER-MANUAL.md](SHORTS-FORGE-USER-MANUAL.md) |

## 1. 이 자식 시스템은 무엇인가

**한 줄 정의** (PRD §1.3):
> 사용자의 사진·동영상을 입력하면, 그 자료를 *활용*해 *적절한 음악*과 함께
> 약 1분(≤59초)의 트렌디한 9:16 YouTube Shorts를 만들어 주는, **사용자 로컬
> Windows PC 전용** AI agentic workflow.

**대상 사용자** (PRD §1.2): 한국어를 쓰는 비전문가, 터미널·설정파일·개발도구를
사용할 수 없음. 입력 = iPhone/Android 카메라롤(HEIC·HDR HEVC·혼합 방향·한글
파일명).

**산출** (PRD §6 J-3): `≤59초·9:16·1080×1920·30fps` mp4 + 한국어 메타 초안
(제목·설명·해시태그). **자동 게시 없음**(`[GATE:D3]` 보류 — 사용자가 직접
업로드).

## 2. 가장 쉬운 사용법 — "시작하자"

```bash
shorts-forge start "시작하자"
```

자연어 한 마디로 *사용자 안내 모드*가 열리고, 정확히 2개의 카탈로그(`풀 렌더` /
`스토리보드 미리보기`)와 실행 명령을 보여 준다. 자세한 흐름·예시·복구는
[`SHORTS-FORGE-USER-MANUAL.md`](SHORTS-FORGE-USER-MANUAL.md) 참조.

## 3. 자매 문서

| 문서 | 대상 독자 | 다루는 것 |
|---|---|---|
| [SHORTS-FORGE-USER-MANUAL.md](SHORTS-FORGE-USER-MANUAL.md) | 비전문가 소유자 | "시작하자" 진입·`run`/`--dry-run`/`selfcheck`·복구·자주 묻는 질문 |
| [SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md](SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md) | 빌더·리뷰어 | 4축 SOT·ANCHOR ①②③·INVARIANT #1·8단계 척추·17개 게이트·2계층 분리·결정 표면 |

## 4. 부모 문서와의 분리 규약

| 접두어 | 위상 | 결정 객체 | 변경 규율 |
|---|---|---|---|
| `AGENTICWORKFLOW-*` (부모) | 방법론·프레임워크 | *어떻게* 만드는가 (PRD/workflow/SOT/ANCHOR 메타) | 부모 저장소 소관 |
| `SHORTS-FORGE-*` (자식) | 도메인 산출물 | *무엇을* 만드는가 (8단계 척추·17 게이트·≤59s mp4) | 본 저장소 어펜드-온리 |

자식 시스템은 부모 방법론을 *상속*하지만(ANCHOR·SOT·결정 표면), 부모 결정을
*단정하지 않는다*. BLOCKING은 항상 자식 SOT(`../PRD.md §12`)에 등록된다.

## 5. 작업자(에이전트·기여자)용 진입점

본 README는 *시스템·문서 진입*이다. 코드 작업 규칙·게이트 규율은 별도:

- [`CLAUDE.md`](CLAUDE.md) — 정본 작업 규칙(ANCHOR·SOT·2계층·게이트·언어).
- [`AGENTS.md`](AGENTS.md) — 에이전트 로스터·빌드 실행 모델(orchestrator + SQLite).
- [`GEMINI.md`](GEMINI.md) — 불가침 요약(Gemini 에이전트용).
- [`decision-log.md`](decision-log.md) — PRD §12 BLOCKING 미러·세션 구현 결정.
- [`docs/TRACEABILITY.md`](docs/TRACEABILITY.md) — 모듈 ↔ PRD/workflow/AX/F/GATE 매트릭스.
- [`docs/DESIGN-DECISIONS.md`](docs/DESIGN-DECISIONS.md) — 확정·가역 설계값.

## 6. 정본(SOT) 4축

자식 시스템의 *결정 권한*은 본 저장소가 아니라 부모 디렉토리의 SOT 4축에 있다
(어펜드-온리·본문 0 번복):

| 축 | 경로 | 비고 |
|---|---|---|
| 요구·제약·수용 | `../PRD.md` (v0.9) | BLOCKING 등록부 = §12 |
| 설계·워크플로 | `../workflow.md` (§0 본문 v0.6 + §10/§13 v0.7~v0.9 D17 currency) | 게이트 맵 = §10 |
| 근거(13축) | `../prd-research/final-research.md` | |
| 구현 | `impl/` (본 저장소) | PRD/workflow의 *하위 산출물* |

## 7. 운영 현황 (2026-05-24 기준)

- 테스트: **263 passed + 47 entry + 1 W5 = 311 passed / 0 failed** (계층 A 계약 +
  계층 B 제품·불변식 + 의미 라우터·안내 모드).
- Increment 1(SM-1 수직 슬라이스 + INVARIANT #1) 베이스라인 GREEN.
- Phase-0 골든 코퍼스(D4a) = 소유자 소관·미제작(Phase-1 선결).
- 잔존 BLOCKING: D1·D2·D3(B3 보류)·D5·D7·D8·D9·D10·D11·D12·D13·D14·D15·D16·
  D17(*해소 형태* 잔존). 자세한 위상 = [`decision-log.md`](decision-log.md).
