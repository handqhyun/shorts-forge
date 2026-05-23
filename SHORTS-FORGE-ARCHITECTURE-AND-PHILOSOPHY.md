# SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md — 자식 시스템 아키텍처·철학

> **부모-자식 분리**: 본 문서는 자식 시스템 *shorts-forge* (로컬 Shorts 자동
> 생성)의 도메인 고유 아키텍처·철학을 다룬다. 부모 유기체 *AgenticWorkflow*
> 방법론(어떻게 PRD/workflow/근거 4축을 정의·검증·전파하는지) 자체는 부모
> 저장소(`AGENTICWORKFLOW-*` 접두어)가 소유한다. 본 문서는 부모 방법론의
> *적용 결과*를 자식 도메인 형태로 제시한다.

## 자매 문서 (자식 시스템 3종)

| 무엇을 찾는가 | 어디로 |
|---|---|
| 자식 시스템 개요·자매 인덱스·정본 4축 위치 | [SHORTS-FORGE-README.md](SHORTS-FORGE-README.md) |
| **아키텍처·철학 (본 문서)** | 본 문서 |
| 사용자 메뉴얼 (`"시작하자"` 진입·`run`/`--dry-run`/`selfcheck`·복구·FAQ) | [SHORTS-FORGE-USER-MANUAL.md](SHORTS-FORGE-USER-MANUAL.md) |

작업 규칙·에이전트 로스터·결정 현황은 별도 운영 문서: [CLAUDE.md](CLAUDE.md)·
[AGENTS.md](AGENTS.md)·[GEMINI.md](GEMINI.md)·[decision-log.md](decision-log.md)·
[docs/TRACEABILITY.md](docs/TRACEABILITY.md).

## 1. 철학 한 줄

> *비전문가의 사적 미디어를 클라우드로 보내지 않으면서, 결정 표면을 소유자에게
> 돌려주는, 결정론적 8단계 척추 위에 LLM 단일 터치만 허용하는 로컬 워크플로.*

세 가지가 직교한다:

1. **로컬성** (INVARIANT #1) — 픽셀은 어떤 모드에서도 외부로 나가지 않는다.
2. **결정 위상** (ANCHOR ③) — 코드는 BLOCKING을 단정하지 않고, 비코더 소유자에게
   *4안 결정 표면*으로 돌려준다.
3. **추적성** (ANCHOR ①) — 모든 모듈은 PRD §·workflow §·연구 축·게이트로
   역추적된다. 추적 불가 = 품질 실패.

## 2. 4계층 SOT (정본 위상)

```
PRD.md            (요구·제약·수용)        ─┐
workflow.md       (설계·8단계 척추·게이트맵) ├─ 본문 0 번복·어펜드-온리
final-research.md (근거 13축)              ─┘
impl/             (구현 — 본 저장소 = 하위 산출물; 결정 단정 0)
```

- `PRD.md §12` = BLOCKING 등록부(D1–D17), 소유자 결정 소관.
- `workflow.md §10` = 게이트 맵(BLOCKING ↔ 설계 영향).
- `workflow.md §1` = 8단계 결정론 척추 + *제품-사용 진입 표면*(2026-05-23 W1 등재).
- `impl/`은 *어떤 BLOCKING도 결정하지 않는다*. 미해소 게이트 의존 경로는
  `@gate_blocked` 데코레이터로 **구조적 차단**된다(호출 시 `GateBlocked` raise).

## 3. ABSOLUTE ANCHOR (충돌 시 상위 절대 우선)

| ANCHOR | 술어 | 자식 시스템 구현 |
|---|---|---|
| ① 추적성 절대 | 샘플링 금지·모든 기능 × 모든 테스트 | `TRACE` dict 필수·`tests/traceability/test_cite_grep.py` |
| ② 정합 사슬 | SOT 본문 0 번복·계층 경계 절대 | `sot_guardian.py` PreToolUse exit 2·`.claude`/`src` 임포트 단절 AST 단정 |
| ③ 결정 위임 | 코드가 BLOCKING 단정 안 함·소유자 4안 표면화 | `@gate_blocked(D#)` + `decision-surface` 스킬 |

## 4. INVARIANT #1 — 로컬 실행 불변

> 시스템의 *모든 산출 연산*은 사용자 로컬 PC에서만. 런타임에 어떤 클라우드·
> 외부 API·텔레메트리·원격 실행도 호출하지 않는다. **픽셀(원시 사진/영상)은
> 어떤 모드에서도 외부 전송 금지.**

**명시 카브아웃 3종**(=위반 아님):
1. 1회성 셋업 다운로드 ~6–12GB (모델·런타임·CC0 음악) → 이후 오프라인 락.
2. 사용자 주도 수동 YouTube 업로드 (브라우저로).
3. 옵트인 "향상" 모드 — 파생 *텍스트만*·페이로드 사전 미리보기·기본 OFF.

**강제 메커니즘**:
- `invariants/netguard.py` = outbound-deny + 실행당 network ledger.
- `tests/invariants/test_network_blocked_e2e.py` = E2E 증명.
- 매 실행은 `network_ledger`에 비-카브아웃 송신 0건이어야 종료(SM-3 = 100%).

## 5. ALIGNMENT #1 — 제1 핵심 목적 정합

§1.3 제1 목적은 **6 원자**로 분해되어 *판정 기준*으로 작동한다:

| 원자 | 명제 | 책임 단계·게이트 |
|---|---|---|
| ① 사진+동영상 *둘다* 입력 | 노하우-닫힘 | S1 NORMALIZE |
| ② 그 자산을 *활용* | 노하우-닫힘 | S2/S3 |
| ③ *적절한* 음악 (무드 정합) | **공백** | `[GATE:D14]` ★ |
| ④ ≈1분 (≤59초) | 노하우-닫힘 | S6 RENDER·`[C-LEN]` |
| ⑤ 트렌디 | **공백** | `[GATE:D5]`·`[GATE:D16]` |
| ⑥ 9:16 Shorts | 노하우-닫힘 | S6·`[C-OUT]` |

서열(비협상): **INVARIANT #1 > ALIGNMENT #1 > 그 외 모든 요구**.

## 6. 8단계 결정론 척추 + 단일 LLM 터치

```
[J-0 셋업 1회]  →  Inbox 트리거(J-1)
  ▼
S1 NORMALIZE → S2 INGEST/ANALYZE → S3 SELECT/ORDER → S4 ASSEMBLE → S5 AUDIO
  └ 결정론 ──────────────────────┘ └판단①┘ └결정론─────────────────────
                                    (단일 LLM 터치: 메타 초안 ③)
                                                              │
                                                              ▼
                                        → LLM_META → S6 RENDER → S7 VALIDATE
                                                          결정론
                                                              │
                                                              ▼
                              산출: ≤59s 9:16 mp4 + 한국어 메타 초안
                                    (게시 전 1탭 편집·자동 게시 0)
```

**제어 패러다임**:
- 흐름은 *고정·선형*(R-CAP2 — LLM이 흐름을 결정하지 않는다).
- 단일 run · 직렬 · FIFO · 전역 락(`invariants/runlock.py`).
- 단계당 `precheck → run → validate_output → checkpoint → next`.
- 체크포인트 센티넬 + SQLite로 *멱등 재진입*(`spine/statemachine.py`).
- **단일 LLM 노드** = 메타 초안(제목·설명·해시태그) 한국어 산출. 미디어
  연산·흐름 결정·게이트 판정에는 LLM 0(R-CAP2/3/5).

**자료 계약(D-2)·판단 술어(D-3)·전이오류 복구(D-4)**: 각 단계가 명시한다
(`workflow.md §2` 본문).

## 7. 제품-사용 진입 표면 (W1·2026-05-23 SOT 정식 등재)

8단계 척추 *앞*에 **단방향 진입 표면**이 위치한다:

```
[자연어 시작 발화]
   ▼
[스마트 라우터: 의미 기반 인식]
   - ConceptAnchor: INITIATE · WORK_OBJECT 멤버십
   - 정규화: NFC + casefold + 토큰화(단·2-gram·전체)
   - 키워드 박제 금지 · 임베딩 0 · LLM 0 (INVARIANT #1 보존)
   ▼
[세션 초기화: 결정 분기 0]
   ▼
[사용자 안내 모드: frozen 카탈로그 정확 2건]
   ▼
{shorts-forge run <폴더>,  shorts-forge run <폴더> --dry-run}
```

**노출 규칙(절대·구조)**: 안내 모드 카탈로그는 빌드 하니스 진입을 *어떤 분기·
플래그·관리자 모드로도* 노출하지 않는다. 필터/은닉이 아닌 **모드 경계 분리**:
- frozen tuple of frozen dataclass (`entry/guide.py` `OPTIONS`)
- AST 임포트 단정 (`tests/router/test_intent.py`)
- 소스 토큰 부재 (build/infra/harness/orchestrator/재빌드 0)
- subprocess stdout 단정 (`tests/cli/test_start_e2e.py`)

코드: `src/shorts_forge/entry/router.py` + `src/shorts_forge/entry/guide.py` +
`src/shorts_forge/cli.py` `start` 서브명령.

## 8. 2계층 분리 — 혼동하면 거짓 GREEN

| 계층 | 위치 | 다루는 것 | "green" 신호 의미 |
|---|---|---|---|
| **A — 빌드 하니스** | `.claude/{tools,agents,hooks,skills}` | 빌드 *프로세스* 자체(SOT 가드·게이트 점검·번역 쌍·추적 갱신) | 빌드 *프로세스* OK, 제품 완성 아님 |
| **B — 제품 파이프라인** | `src/shorts_forge/**` | 실제 8단계 척추·LLM 노드·INVARIANT #1 | 제품 *기능* 검증 GREEN |

> "169/263 green = 제품 완성"은 **거짓**. 계층 A가 169 통과해도 계층 B 미검증이면
> 제품 미완성. 빌드 하니스의 contract 테스트는 *프로세스* 검증이다.

빌드 엔진은 **orchestrator 서브에이전트 + SQLite 상태**다(yaml 아님):
- 상태: `.claude/state/build_state.sqlite` — 5테이블(`build_runs`·`build_tasks`·
  `build_decisions`·`build_forks`·`pair_outputs`).
- 쓰기 단일 경로: `python -m tools.build_state <subcmd>` (raw SQL 0).
- 레지스트리 = 런타임 게이트(`spine/gates.py`) + 빌드타임(`build_decisions` D17) +
  추적(`docs/TRACEABILITY.md`). **`state.yaml`/`step-registry.yaml`은 존재하지 않으며
  만들지 않는다** — 이를 전제하는 지시는 거짓 전제로 취급.

## 9. 결정 표면 (Decision Surface) — 비코더 4안

소유자는 비기술자다(PRD §1.2). BLOCKING 결정은 **비기술 4안**으로 표면화하고
소유자가 선택한다:

| 필드 | 의미 |
|---|---|
| 핵심(label) | 1~5 단어, 비기술 명사 |
| 왜(description) | 무엇이 일어나는지·왜 결정해야 하는지 |
| 트레이드오프 | 선택의 비용·이득 |
| 다음 결과(preview) | 선택 시 *바로 보이는* 결과 |

자율 결정·기술 용어 강요 금지. 스킬 `decision-surface`가 이 형식을 강제한다.

## 10. 17개 게이트 (BLOCKING — 소유자 결정 소관)

런타임 D1–D16은 `spine/gates.py` 레지스트리에 표면화·`@gate_blocked` 데코레이터로
구조적 차단된다(미해소 전 호출 = `GateBlocked` raise). D17은 *빌드타임* 게이트
(`build_state.build_decisions` 소관·런타임 미등재가 정상).

| 분류 | 게이트 |
|---|---|
| HARD-BLOCKED | D2 음악 소싱·D3 자동 게시·D9 HEVC 디코더 조달·D10 빌드 실현성·D11 unrecoverable taxonomy·D13 빌드 정확성 수용·D14 무드 음악 매칭·D15 실사용자 수용 루프 |
| PROVISIONAL | D1 수치 문턱·D5 트렌드/슬랭·D7 디바이스 티어·D8 Content-ID·D12 위임-결정자 정합·D16 트렌드 갱신 운영 |
| PARTIAL | D6 서명 채널 (베이스라인 = OV sideload 확정) |
| 해소 | D4 골든 코퍼스 소유권(2026-05-18 D4a)·D17 *해소 형태* 부분 진전(2026-05-20 v0.9) |

자세한 위상·소관·코드 표현 = [`decision-log.md`](decision-log.md) + 
[`docs/TRACEABILITY.md`](docs/TRACEABILITY.md) 게이트 맵.

## 11. 어펜드-온리 규율

SOT 본문은 **0 번복**한다. 새 발견은 *어펜드-온리* — 셀 끝 어펜드 또는 신규 줄.
버전/상태 토큰의 in-place 정정만 예외(번복 아님·X3 안정성 클래스). 강제 메커니즘:

- `tools/sot_guardian.py` + `sot-guardian-block.sh` 훅 = PreToolUse 단계에서 본문
  바이트 수정 시 **exit 2** (우회 금지).
- 회의 산물·정본 모두 동일 규율(자식 시스템 메모리 [[feedback-append-only]] 동형).

## 12. 한국어·언어 정책 (ANCHOR ③)

- 하니스 계층(`.claude/**`)·`src/`·`tests/`의 코드/주석/도크스트링 = **영어 단일**.
- 한글 대면은 `korean-translator` 서브에이전트 + `*.ko.md` 쌍 (`pair-write` 스킬로
  원자적 쌍 기록 + SHA-256 앵커 + 멱등성).
- **불변(영어화 금지·ANCHOR ② 우선)**: SOT 마커(`·번복 아님·X3 안정성 클래스`),
  4안 라벨(`핵심·왜·트레이드오프·다음 결과`), `intent_prefilter` 한글 입력
  키워드, NFC 한글 테스트 픽스처(C-I18N 데이터).

## 13. 부모-자식 책임 분리 요약

| 책임 | 부모 (AgenticWorkflow) | 자식 (shorts-forge) |
|---|---|---|
| 방법론 (SOT 4축·ANCHOR·결정 표면 형식) | ✔ 소유 | ✔ 적용 |
| 도메인 척추 (8단계·S1–S7) | – | ✔ 소유 |
| 17개 게이트 | – | ✔ 소유 |
| INVARIANT #1 강제 메커니즘 | 패턴 | 구현 (`invariants/netguard.py`) |
| 의미 라우터·안내 모드 | – | ✔ 소유 |
| 어펜드-온리·X3 안정성 | 규율 | 구현 (`tools/sot_guardian.py`) |
| 결정 단정 | **금지** | **금지**(@gate_blocked) |

자식 시스템은 부모 *방법론을 빌려* 도메인 산출물을 만들 뿐, 부모를 *수정하지
않는다*. 부모의 진화는 별 저장소·별 turn.
