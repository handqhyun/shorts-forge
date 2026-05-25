# decision-log.md — 결정 현황 (파생 미러)

> **권위 주의**: BLOCKING 게이트의 정본은 `../PRD.md §12`이며 본 파일은 *읽기용
> 미러/다이제스트*다. 충돌 시 SOT(PRD §12 / workflow §10 게이트맵 / `docs/TRACEABILITY.md`)가
> 우선한다. 본 로그는 어떤 BLOCKING 도 *확정 결론*하지 않는다(ANCHOR ③). 갱신은
> 어펜드-온리.

## A. BLOCKING 게이트 (소유자 몫 — PRD §12)

런타임 게이트 D1–D16은 `src/shorts_forge/spine/gates.py`에 표면화·`@gate_blocked`로
구조적 차단. D17은 *빌드타임* 게이트(`build_state.build_decisions` 소관·런타임
gates.py 미등재가 정상).

| GATE | 주제 | 분류 | 코드 표현 |
|---|---|---|---|
| D1 | 수치 문턱(샷대역·길이·품질) | 잠정 ratchet | `PROVISIONAL_D1_*` 표식·상수 채택 금지 |
| D2 | 음악 라이브러리 콘텐츠 소싱 | HARD-BLOCKED → **해소(v1.2 currency 2026-05-25·안 2 소유자 수동 로컬 음악 폴더·PRD §12-D2 정본)** | `s5.load_library()` @gate_blocked 해제·`<sf_root>/music/` 소유자 배치·loader.discover_tracks |
| D3 | 자동 게시 | HARD-BLOCKED (B3 보류) | `cli.publish()` @gate_blocked·publish verb 부재 |
| D4 | Phase-0 골든 소유권 | **해소(소유자)** | 코퍼스 *제작*은 별도 병행(Inc1 미포함) |
| D5 | 트렌드/슬랭 렉시콘 | 잠정 → **해소(v1.0 currency 2026-05-25·안 2 소유자 수동 로컬 렉시콘·PRD §12-D5 정본)** | `s3.energy_arc_reorder()`·`llm.resolve_slang()` @gate_blocked·연대순 폴백 (별 turn: @gate_blocked 해제 + 렉시콘 로더 신설) |
| D6 | 서명/배포 채널 | 부분 해제(스파이크 잔존) | OV-sideload 타깃·`msix_channel()` @gate_blocked |
| D7 | 디바이스 티어 임계 | 잠정 | 보수 기본 티어·`autotier_measure()` @gate_blocked |
| D8 | Content-ID 오클레임 | 잠정 | `s5.contentid_claim()` placeholder |
| D9 | HEVC 디코더 조달 | HARD-BLOCKED | `s1.procure_decoder()` @gate_blocked·probe된 디코더만 |
| D10 | 빌드/구현 실현성(X1) | 표면화(K-class 미측정) | 코드 모듈 없음·gates.py 등록만 |
| D11 | unrecoverable-failure taxonomy(X2) | 표면화 | 코드 모듈 없음(§9/OPS-8 부분-상태 복구 미명세) |
| D12 | 위임-결정자 정합(L2·메타) | 표면화(메타) | 코드 표현 없음 |
| D13 | 빌드정확성 수용객체(G2) | 표면화 | 하니스는 출력품질만 |
| D14 | 무드음악 매칭 차원 | 표면화(★제1목적 직격) → **해소(v1.2 currency 2026-05-25·D2와 단일 결정 수렴·매칭 차원='소유자 선택'·코드 명시 매칭 엔진 부재·PRD §12-D14 정본)** | s5 결정론 선택(seed-based)만·매칭 엔진 0·소유자 큐레이션 한정 |
| D15 | 실사용자 수용루프 | 표면화 | 판정자=소유자/머신만 |
| D16 | 트렌드 갱신운영·부패수용 | 표면화(D5 보완) → **해소(v1.0 currency 2026-05-25·D5와 단일 결정 수렴·소유자 수동 편집·정상 강등 수용판정·PRD §12-D16 정본)** | s3·llm 운영축 (별 turn: 운영 정책 코드화) |
| D17 | Claude Code 빌드 인증 연속성 | *해소 형태* 잔존(빌드타임) | `build_decisions`·런타임 gates.py 미등재가 정상 |

## B. [DESIGN] 결정값 (확정·가역 — workflow §12 위임)

C-*·INVARIANT #1 위반 없는 한 상태모델/어댑터 뒤 캡슐화되어 가역. 상세
`docs/DESIGN-DECISIONS.md`.

| # | 결정 | 확정값 | 가역 지점 |
|---|---|---|---|
| D-CS | 작업 색공간 | BT.709·8-bit·limited; HDR/P3 → S1 1회 톤맵 | `media/tonemap.py` |
| D-FG | EDL→필터그래프 | 엔트리별 결정론 ffmpeg 체인(cover-crop→zoompan→concat) | `stages/s4_assemble.py` |
| D-ENC | QSV vs x264 | x264 CPU 베이스라인·NVENC/CUDA 절대 금지(C-HW) | `media/ffmpeg_cli.py` |
| D-RR | 리롤 캐시 경계 | 무효화 = 창의 노드만 {S3·S5·LLM_META} | `spine/cache.py` CREATIVE_NODES |
| D-DB | Inbox 디바운스 | 안정-크기 디바운스 + 정적창 = 1배치 | `config/defaults.py` |
| D-TR | 트레이스 헤더 | 모든 src 모듈 `TRACE` dict 필수 | `tests/traceability` |
| 상태머신 | 엔진 선택 | 손수제작 결정론 상태머신(LangGraph-로컬은 가역 대안·미채택) | `spine/statemachine.py` |

## C. 세션 구현 결정 (가역·설계계층 — 소유자 게이트 아님)

> 모두 `src/`·`tests/`·문서 계층 한정. SOT 본문·게이트 값 불변.

- **(2026-05-22) 테스트 전략 4종 채택** — CLI E2E / 파이프라인 통합 / Dry-Run /
  Hook. **D-1: "Playwright E2E"는 거짓 전제**(제품에 UI 없음·CLI 단일 `shorts-forge`)
  → CLI E2E(subprocess)로 정직 치환. Dry-Run 의 G2/G3 자명통과(F-7)는 렌더 검증으로
  오독 금지(거짓 GREEN 가드 명시).
- **(2026-05-22~23) 미커버 매트릭스 셀 전수 직접검증 승격** — S2/S3/S4/S5/S6 +
  edl/cache/image_ops/tonemap/probe + 9 훅 .sh 래퍼. 총 테스트 → **263 passed/0 failed**
  (ANCHOR ① 무샘플링).
- **(2026-05-23) C1 — pHash 과격리 해소** — 근본원인 = luma-only(grayscale) pHash 가
  색상만 다른 프레임을 동일 구조로 접음. 수정 = **192비트 색상 인지 pHash**(RGB
  채널별 64-bit DCT 연결). **근중복 문턱 값 6 불변 → D1 게이트 결정 회피**(해시
  품질 개선으로 처리, 게이트 불가침). `image_ops.phash`.
- **(2026-05-23) C2 — NFD 한글 무성드롭 해소** — 근본원인 = `s1_normalize`가
  `nfc_path(f)`로 NFC화한 경로를 probe 에 전달 → 디스크 NFD 실파일 불일치로 무성
  격리(workflow [GATE:D11] 자가경고 실증). 수정 = 읽기는 iterdir 실경로 `f`·NFC는
  신원 기록에만 + work 파일명 ASCII 보장(`_ascii_stem`). `stages/s1_normalize.py`.
- **C3(S7 G2 first-frame-black)** = 현 코드 GREEN(이미 해소). 3 클러스터 종결.
- **(2026-05-23) 계층B 진입 라우팅 + 사용자 안내 모드 추가** — 소유자 override
  ("안 만든다" 1턴 전 결정 → "구현 시작" 본 턴; 번복 아님·새 결정). 위치 = `src/
  shorts_forge/entry/{__init__,router,guide}.py` + `cli.py` `start` 서브명령. 의미 기반
  인식 = ConceptAnchor(INITIATE/WORK_OBJECT) 멤버십 + NFC/casefold/토큰화 정규화
  (키워드 박제 금지·임베딩 0·LLM 0·INVARIANT #1 보존). 계층A(`.claude`) 임포트·
  심볼 0(AST 단정)·frozen `guide.OPTIONS` (정확히 `run`/`run --dry-run` 2개 고정·
  user-text 어디에도 build/infra/harness/orchestrator/재실행/재빌드 부재). **ANCHOR
  ② 형식적 침범 가시화**: 라우팅/모드 추가가 SOT 미등재이며 본 turn 어펜드는
  *표면화*만(정합화 = SOT 라우팅 정식 등재는 별 turn·BLOCKING 후보로 표면화만).
  검증: pytest **310 passed / 0 failed**(263 베이스라인 + 47 신규·회귀 0).
- **(2026-05-23) W1 적용 — SOT 라우팅 정식 등재 (ANCHOR ② 정합 사슬 복원)** —
  소유자 명시 "W1 적용" 지시로 `prompt/workflow.md §1 line 42` 에 *제품-사용
  진입 표면* (`[자연어 시작] → [라우터: ConceptAnchor 의미 인식] → [세션 초기화]
  → [안내 모드: frozen 카탈로그 2건] → {run, run --dry-run}` 단방향) 정식 등재
  currency 어펜드 + `§10 line 266` cross-ref currency + `§13` 신규 표 행 어펜드.
  **본 적용의 한정**: ANCHOR ② 정합 사슬 *복원*만 — 직상 bullet 의 "ANCHOR ②
  형식적 침범 가시화" 잔존 (a) 해소. 코드/테스트/본 §C 직상 bullet *베이스라인
  불변* (310 passed / 0 failed)·SOT 본문 0 수정·블록 신규 줄/표 행만. **위상 구분
  (불변)**: 본 W1 = 제품-사용 진입(계층 B)·D17 외부 0번 진입점 = 빌드 부트스트랩
  (계층 A)와 별 위상(병합 금지·양립). **잔존(별 turn)**: 직상 bullet 의 (b) PRD §10
  OPS-1 GUI 진입 관계 정의·(c) D-LANG 보존은 본 W1 범위 밖(여전히 잔존).
- **(2026-05-23) W2~W5 적용 — 5거장 채점 약점 4건 일괄 해소 (가역·설계 계층)** —
  소유자 명시 "제안하는 아키텍처 구현을 시작하라" 지시. **W2**: `cli.py` `main()`
  if-elif → `_build_parser()` + `_DISPATCH` dict 추출(`main()` 5줄·신규 verb 추가 시
  `main()` 무변경 — Ousterhout C3 complexity downward 7→10). **W3**: `entry/guide.py`
  `OPTIONS[*].result` 비코더 친화 정제 — `"≤59초 9:16 mp4"` → `"세로형 짧은 영상
  한 편(휴대폰 화면 비율·최대 약 1분)"`·`label`/`command`/금지 토큰 부재 보존
  (Norman C2 control→effect 8→10). **W4**: `cmd_start` 미인식 경로 `print` 2건 →
  `file=sys.stderr` 전환 (Hoare C2 8→10·POSIX 관례 정합). **W5**: `tests/router/
  test_intent.py` `test_router_and_guide_no_dynamic_import` 신규 — AST Call 노드
  단정으로 `__import__` / `importlib.import_module` 부재 강제(직전 `test_router_and_
  guide_imports_are_clean` 정적 단정 우회 차단·Dijkstra C1 9→10). **본 적용의
  한정**: 5건 모두 가역·세션 구현 결정 클래스(C-* / INVARIANT #1 / SOT BLOCKING
  무관·D1–D17 0 결정·미결정 17 불변). **검증**: pytest **311 passed / 0 failed**
  (310 베이스라인 + 1 신규·회귀 0·131초). **예상 채점 변동**: 135/150 → ~147/150
  (Dijkstra 25→26·Hoare 28→30·Norman 28→30·Ousterhout 25→28·Beck 29→30·합 ~144;
  W2 의 dispatcher 추출이 Dijkstra C1 의 cli 비대화 -1 도 부분 회수). **잔존(별
  turn)**: 직상 bullet 들의 (b) PRD §10 OPS-1 GUI 진입 관계 정의·(c) D-LANG 보존
  은 본 W2~W5 범위 밖. SOT 본문 어펜드 부재 — 본 4건은 *세션 구현 결정*이며
  workflow.md `§1 line 42` 정식 등재의 "frozen 카탈로그 2건·의미 기반 인식" 정의는
  보존(label/command/금지 토큰/2-tuple 불변).
- **(2026-05-24) 자식 시스템 문서 분리 패턴 적용 (가역·문서 계층·소유자 명시 지시)** —
  소유자 명시 지시("자식 시스템 readme/ARCHITECTURE-AND-PHILOSOPHY/USER-MANUAL
  별도 작성·부모 AgenticWorkflow와 구별·git 디렉토리 진입 문서 자식 연결로 대체·
  CLAUDE/AGENTS/README/decision-log/ARCH/USER-MANUAL 업데이트"). **신규 3종**
  (`impl/` 루트·`SHORTS-FORGE-*` 접두어): `SHORTS-FORGE-README.md`(개요·자매
  인덱스·정본 4축 위치)·`SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md`(4축 SOT·
  ANCHOR ①②③·INVARIANT #1·ALIGNMENT #1·8단계 척추·17 게이트·2계층 분리·
  의미 라우터·결정 표면 통합)·`SHORTS-FORGE-USER-MANUAL.md`(비전문가용
  "시작하자" 진입 중심·`run`/`--dry-run`/`selfcheck`·복구·FAQ·치트시트).
  **진입 README 대체**: `impl/README.md`를 자식 3종 + 작업규칙(CLAUDE/AGENTS/
  GEMINI) + 운영문서(decision-log/TRACEABILITY/DESIGN-DECISIONS)로 연결하는
  *인덱스*로 재작성·주제별 길잡이(목적·워크플로 구조·프로젝트 구조·스킬·CPS·
  결정) 포함. **연관 어펜드**: CLAUDE.md/AGENTS.md/GEMINI.md 상단에 "문서 위상"
  블록 어펜드(사용자 대면 *내용* 어펜드는 `SHORTS-FORGE-*` 3종 소관·에이전트 작업
  규칙은 본 운영 문서 소관·역할 분리·X3 안정성). 신규 두 자식 문서(ARCH·USER-MANUAL)
  상단에 *자매 문서 네비게이션* 블록 추가. **부모-자식 분리 규약**: 부모
  *AgenticWorkflow* 방법론 문서는 `AGENTICWORKFLOW-*` 접두어(별 저장소·본 turn
  미생성)·자식 도메인 산출물은 `SHORTS-FORGE-*` 접두어(본 turn 생성·파일명 충돌
  0·검색 명확화·문서 위상 즉시 식별). **본 적용의 한정**: 가역·문서 계층 한정·
  SOT 본문(`../PRD.md`·`../workflow.md`·`../prd-research/final-research.md`)
  0 수정·`src/`/`tests/` 0 변경·코드 베이스라인 311 passed/0 failed 불변·D1–D17
  미결정 17 불변·신규 BLOCKING 0·결정 표면 4안 미발생(BLOCKING 결정 아님).
  **L3 정지성 메타**: 사용자 명시 지시 = §11-L3 정지 술어 *(b) 분기*(사용자
  명시 지시·입력 생성) 정합·자율 N+1 0([[feedback-l3-b-branch]] 동형).
- **(2026-05-25) USER-MANUAL selfcheck 예시 출력 게이트 ID 나열 D10 누락 정정 (X3 안정성·문서 계층·소유자 명시 지시)** —
  소유자 명시 지시("D10 누락 수정 적용해줘") 직전 turn 자식 3종 검증 보고서 적출
  사소한 불일치 1건 해소. **근본**: `SHORTS-FORGE-USER-MANUAL.md:93` selfcheck
  예시 코드블록 출력 `[OK] 게이트 레지스트리 15개: D1,D11,D12,...,D9` 가 카운트
  표기 "15"는 정확하나 나열된 ID는 14개(D10 빠짐) — 실 코드 `cli.py:79`
  `sorted(GATES)` 출력(lexicographic: `D1,D10,D11,D12,D13,D14,D15,D16,D2,D3,D5,
  D6,D7,D8,D9` = 15)과 한 토큰 desync. **수정**: `D1,` 직후·`D11,` 직전에
  `D10,` 1 토큰 삽입(lexicographic 위치 정합·`spine/gates.py:36` `GATES` dict
  실제 15 entries 정합). diff +1/-1 = 1 줄 변경. **본 적용의 한정**: 예시 코드
  블록 *문자열 표시*만 정정 — `cli.py`/`spine/gates.py`/`tests/` 0 수정·SOT
  본문(`../PRD.md`/`../workflow.md`/`../prd-research/final-research.md`) 0 수정·
  코드 베이스라인 311 passed/0 failed 불변·D1–D17 미결정 17 불변·신규
  BLOCKING 0·게이트 레지스트리 *의미* 0 변경. **X3 안정성 클래스 동형**: 본
  정정 = 표시 토큰 in-place 정합(앵커 포인터 위생·번복 아님·결정 변경 0)
  — `[[feedback-append-only]]` 의 "버전/상태 토큰 in-place 정정만 예외" 동형.
  **검증**: 동일 패턴 다른 위치 0건(`SHORTS-FORGE-*.md`/`README.md`/`docs/*.md`
  grep 결과 단일 hit). **L3 정지성 메타**: 사용자 명시 지시 = §11-L3 정지 술어
  *(b) 분기* 정합·자율 N+1 0([[feedback-anchor3-apply-gate]] 동형·보고 turn →
  명시 적용 turn 분리 준수).
