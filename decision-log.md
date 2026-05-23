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
| D2 | 음악 라이브러리 콘텐츠 소싱 | HARD-BLOCKED | `s5.load_library()` @gate_blocked·`music/` 미채움 |
| D3 | 자동 게시 | HARD-BLOCKED (B3 보류) | `cli.publish()` @gate_blocked·publish verb 부재 |
| D4 | Phase-0 골든 소유권 | **해소(소유자)** | 코퍼스 *제작*은 별도 병행(Inc1 미포함) |
| D5 | 트렌드/슬랭 렉시콘 | 잠정 | `s3.energy_arc_reorder()`·`llm.resolve_slang()` @gate_blocked·연대순 폴백 |
| D6 | 서명/배포 채널 | 부분 해제(스파이크 잔존) | OV-sideload 타깃·`msix_channel()` @gate_blocked |
| D7 | 디바이스 티어 임계 | 잠정 | 보수 기본 티어·`autotier_measure()` @gate_blocked |
| D8 | Content-ID 오클레임 | 잠정 | `s5.contentid_claim()` placeholder |
| D9 | HEVC 디코더 조달 | HARD-BLOCKED | `s1.procure_decoder()` @gate_blocked·probe된 디코더만 |
| D10 | 빌드/구현 실현성(X1) | 표면화(K-class 미측정) | 코드 모듈 없음·gates.py 등록만 |
| D11 | unrecoverable-failure taxonomy(X2) | 표면화 | 코드 모듈 없음(§9/OPS-8 부분-상태 복구 미명세) |
| D12 | 위임-결정자 정합(L2·메타) | 표면화(메타) | 코드 표현 없음 |
| D13 | 빌드정확성 수용객체(G2) | 표면화 | 하니스는 출력품질만 |
| D14 | 무드음악 매칭 차원 | 표면화(★제1목적 직격) | s5 휴리스틱만·s7 무드게이트 부재 |
| D15 | 실사용자 수용루프 | 표면화 | 판정자=소유자/머신만 |
| D16 | 트렌드 갱신운영·부패수용 | 표면화(D5 보완) | s3·llm 운영축 |
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
