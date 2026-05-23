# CLAUDE.md — shorts-forge 작업 규칙 (정본)

로컬 실행 전용 YouTube Shorts 자동 생성 워크플로의 **구현 계층**(`impl/`). 이
파일은 이 저장소에서 작업하는 에이전트의 정본 규칙이다. 에이전트 로스터는
[AGENTS.md](AGENTS.md), 결정 현황은 [decision-log.md](decision-log.md) 참조.

## 문서 위상 (2026-05-24 자식 시스템 문서 분리)

본 저장소는 부모 유기체 *AgenticWorkflow*(만능줄기세포 = 방법론)에서 분화한
**자식 시스템 shorts-forge**(도메인 = 로컬 Shorts 자동 생성). 자식 시스템 사용자·
빌더·소유자를 위한 진입 문서 3종은 *접두어 `SHORTS-FORGE-*`*로 분리되며 부모
문서(`AGENTICWORKFLOW-*`)와 파일명 충돌 없이 독립 이해 가능하다.

| 대상 | 진입 문서 |
|---|---|
| 일반 독자·자식 시스템 개요 | [SHORTS-FORGE-README.md](SHORTS-FORGE-README.md) |
| 빌더·리뷰어 — 아키텍처·철학 통합 | [SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md](SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md) |
| 비전문가 소유자 — 사용자 메뉴얼 (`"시작하자"` 진입) | [SHORTS-FORGE-USER-MANUAL.md](SHORTS-FORGE-USER-MANUAL.md) |

본 CLAUDE.md는 *에이전트 작업 규칙*이며 위 3종과 위상 별개 — 충돌 시 본 파일이
작업 규칙으로 우선. 사용자 대면 *내용* 변경(메뉴얼·아키텍처 설명)은
`SHORTS-FORGE-*` 어펜드, 작업 규칙 변경은 본 파일.

## ABSOLUTE ANCHOR (충돌 시 상위 절대 우선)

1. **품질 절대우선** — 추적성·테스트 완결성이 절대 기준. 샘플링 금지. 모든 기능
   × 모든 테스트가 실행 가능한 구조가 목표. "근거 없는 완벽 결론" 금지.
2. **SOT + RLM 불변** — 정본(아래)과 로컬 실행 불변(INVARIANT #1)을 어떤 작업도
   침범하지 않는다. 테스트·문서·빌드는 격리 전략 필수.
3. **승인 후 구현** — 보고/제안 턴과 적용 턴을 분리한다. BLOCKING 결정은 소유자
   몫이며 코드가 단정하지 않는다(@gate_blocked).

## 정본 4축 (SOT — 본문 수정 금지·어펜드-온리)

| 축 | 파일 | 비고 |
|---|---|---|
| 요구·제약·수용 | `../PRD.md` (v0.9) | BLOCKING 등록부 = §12 |
| 설계·워크플로 | `../workflow.md` (§0 v0.6 본문 + §10/§13 v0.9 currency) | 게이트 맵 = §10 |
| 근거(13축) | `../prd-research/final-research.md` | |
| 구현 | `impl/` (본 저장소) | PRD/workflow 의 *하위 산출물* |

- SOT 본문은 **0 번복**한다. 새 발견은 *어펜드-온리*(셀 끝 어펜드 또는 신규 줄).
  버전/상태 토큰의 in-place 정정만 예외(번복 아님, X3 안정성 클래스).
- 이 규율은 `tools/sot_guardian.py` + `sot-guardian-block.sh` 훅이 **diff 강제**한다
  (본문 바이트 수정 시 PreToolUse exit 2). 우회 금지.
- 모든 `src/` 모듈은 `TRACE` dict(`prd`/`workflow`/`ax`/`f`/`gate`)를 보유해야 한다.
  미기재 = `tests/traceability` 실패 = 품질 실패(ANCHOR ①).

## 2계층 — 혼동하면 거짓 GREEN

- **계층 A = 빌드 하니스** (`.claude/{tools,agents,hooks,skills}`): 빌드 *프로세스*를
  구현. contract 테스트(`tests/contracts`)·`exit.json`·"green" 신호는 *전부 이 계층*.
- **계층 B = 제품 파이프라인** (`src/shorts_forge/**`): workflow.md 가 정의한 실제
  기능(8노드 척추·단일 LLM·INVARIANT #1).
- **"contract OK / green"을 제품 완성으로 읽지 말 것.** 제품 검증은 아래 sf-venv
  pytest 경로로 재현한다.

## INVARIANT #1 (PRD §4 — 로컬 실행 불변)

런타임은 클라우드/외부 API/텔레메트리/원격 실행을 호출하지 않는다. 명시 카브아웃
3종(1회 셋업 fetch·사용자 수동 업로드·옵트인 텍스트-only)만 예외. 픽셀(원시
사진/영상)은 어떤 모드에서도 외부 전송 금지. `invariants/netguard.py`가
outbound-deny + 실행당 ledger 로 강제, `tests/invariants/test_network_blocked_e2e.py`가 증명.

## 빌드/테스트 실행 (sf-venv)

`/mnt/c`(DrvFs)는 venv 불가 → Linux fs `~/sf-venv` 사용. 제품 의존 = Pillow + ffmpeg뿐.

```bash
# 전체 제품+하니스 테스트 (cwd=impl)
PYTHONPATH=src:.claude \
  SHORTS_FORGE_FFMPEG=$(~/sf-venv/bin/python -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())') \
  ~/sf-venv/bin/python -m pytest tests/ -p no:cacheprovider
# 도구층만(의존 0·stdlib unittest; cwd=impl/.claude)
cd .claude && python3 -m unittest discover -s ../tests/contracts -p "test_*.py"
```

- 현재 베이스라인: **263 passed / 0 failed** (계층 A 계약 + 계층 B 제품/불변식).
- DrvFs 캐시 불가 → `-p no:cacheprovider` 필수. venv 는 `~/sf-venv`(Linux fs).
- 테스트는 `tmp_path` + 합성 inbox(`tests/fixtures/gen_synthetic.py`)만 사용 —
  **개인 미디어 절대 금지**(PRD §7). 훅 테스트는 cwd=tmp + tmp SOT 디코이로 실
  SOT·실 `build_state.sqlite` 미접근.

## 게이트 규율 (BLOCKING = 소유자 몫)

- BLOCKING 결정(D1–D17)은 `@gate_blocked("D#")`로 *구조적으로 차단*한다. 호출 시
  `GateBlocked` raise. 코드가 게이트 값을 결정하지 않는다.
- 잠정값(D1 문턱·D5 슬랭·D7 티어 등)은 상수 채택 금지·`PROVISIONAL_*` 표식.
- 게이트 현황은 [decision-log.md](decision-log.md) / `docs/TRACEABILITY.md` / SOT `PRD §12`.

## 비코더 소유자 — 결정 표면 방식

소유자는 비기술자다. BLOCKING 결정은 **비기술 4안**(핵심·왜·트레이드오프·다음
결과)으로 제시하고 소유자가 선택한다. 자율 결정·기술 용어 강요 금지.

## 언어 정책 (ANCHOR ③)

- 하니스 계층(`.claude/**`)·`src/`·`tests/` 의 코드/주석/도크스트링 = **영어 단일**
  (제품 소스 한글 0; 한글 대면은 korean-translator + `*.ko.md` 쌍).
- **불변(ANCHOR ② 우선)**: SOT 마커(`·번복 아님·X3 안정성 클래스`), 4안 라벨
  (`핵심/왜/트레이드오프/다음 결과`), `intent_prefilter` 한글 입력 키워드, NFC 한글
  테스트 픽스처(C-I18N 데이터)는 영어화하지 않는다.

## 자주 하는 실수

- ❌ SOT 본문 in-place 수정 → ✅ 어펜드-온리.
- ❌ "169/263 green = 제품 완성" → ✅ 계층 구분.
- ❌ 게이트 값 임의 결정 → ✅ 소유자 4안 표면화.
- ❌ 버그를 픽스처/테스트 약화로 가리기 → ✅ 근본원인 수정(예: C1 = pHash
  색상 인지화로 해결, D1 문턱 값 불변).
