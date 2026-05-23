# 추적성 매트릭스 (ANCHOR ① — 추적 불가 = 품질 실패)

모듈 ↔ PRD § / workflow.md § / 【AX-*】 / [F §n] / [GATE:D#]. 각 `src/` 모듈은
`TRACE` dict 를 노출하며 `tests/traceability/test_cite_grep.py` 가 강제한다.
정본: `../PRD.md` **v0.9** · `../workflow.md` **v0.6** · `../prd-research/final-research.md`. (v0.2→v0.9/v0.6 = 어펜드-온리·**섹션번호 불변**이라 본 §-앵커 무성부패 없음 — 버전핀만 X3 동반갱신; D10–D16·ALIGNMENT #1 표면화 아래.) **(v0.9/v0.6 currency 2026-05-21·번복 아님·X3 안정성 클래스·버전핀 in-place 동반갱신·§-앵커/본문 무수정·workflow §10/§13 v0.9 D17 currency 반영·D17 빌드게이트 신규 표면화 ↓하단)**

## 불변식 하니스 (INVARIANT #1)

| 모듈 | PRD | workflow | [F] | 역할 |
|---|---|---|---|---|
| invariants/encoding.py | §4 C-I18N | §6 | §3.11 | NFC·UTF-8·ASCII-root 강제 |
| invariants/netguard.py | §4 INVARIANT #1·§2 SM-3 | §6 | §3.4 | outbound-deny + network ledger + 카브아웃 3종 |
| invariants/runlock.py | §10 OPS-6 | §9 | §3.4 | 전역 단일 FIFO run 락 |
| invariants/resource_guard.py | §4 C-HW·§10 OPS-6 | §9 | §3.7 | RAM 예산·below-normal·encode/model 동시금지 |
| invariants/seed.py | §7 ALWAYS | §0 #5 | §3.2 | 결정론 고정 seed |

## 척추 (state / EDL / contracts / gates)

| 모듈 | PRD | workflow | [F] | 역할 |
|---|---|---|---|---|
| spine/db.py | §10 OPS-3 | §4 | §3.2 | SQLite 스키마 (runs/inputs/checkpoints/cache/network_ledger/gate_log) |
| spine/runstate.py | §10 OPS-3 | §4 | §3.2 | run blackboard |
| spine/edl.py | §8 C-OUT·§7 NEVER | §4 [DESIGN] | §3.1 | 내부 EDL 스키마+검증 |
| spine/contracts.py | §9 R-CAP2 | §0 #6·§2 | §2 | StageContract ABC |
| spine/gates.py | §12 D1–D16·§4 ALIGNMENT #1 | §10 게이트 맵 | §8 | GateBlocked + @gate_blocked |
| spine/cache.py | §7 ALWAYS | §4 [DESIGN] | §3.2 | 콘텐츠주소·리롤 경계 |
| spine/statemachine.py | §6 J-2·§11 | §1·§4 | §3.2 | 멱등 선형 DAG S1..S7 |

## 단계 (S1–S7)

| 모듈 | PRD | workflow | 【AX】 | [F] | GATE |
|---|---|---|---|---|---|
| stages/s1_normalize.py | §4 C-INPUT/C-SPINE/C-I18N·§3.2 | §2 S1 | AX-INPUT/AX-I18N | §3.10 | [GATE:D9] procure_decoder |
| stages/s2_ingest_analyze.py | §9 R-CAP4·§7 NEVER | §2 S2 | AX-INTEL/AX-CRAFT | §3.3 | — |
| stages/s3_select_order.py | §8 C-THUMB·§7 | §2 S3 | AX-CRAFT/AX-INPUT | §3.9 | [GATE:D5] |
| stages/s4_assemble.py | §8 C-OUT/C-THUMB·§7 NEVER | §2 S4 [DESIGN] | AX-MEDIA | §3.1 | — |
| stages/s5_audio.py | §4 C-MUSIC·§7 NEVER | §2 S5 | AX-MEDIA/AX-LICENSE | §3.1/§3.8 | [GATE:D2] [GATE:D8] |
| stages/s6_render.py | §4 C-OUT/C-HW/C-LEN | §2 S6 | AX-HW/AX-I18N | §3.7/§3.11 | — (NVENC 금지) |
| stages/s7_validate.py | §8 GATE G1–G7·§4 | §2 S7·§7 | AX-OPS/AX-CRAFT/AX-EVAL | §3.4/§3.9/§3.12 | [GATE:D1] [GATE:D8] |

## 미디어 어댑터 / LLM / CLI

| 모듈 | PRD | workflow | [F] | GATE |
|---|---|---|---|---|
| media/ffmpeg_cli.py | §4 C-OUT/C-LIC/C-HW | §2 S6·§0 #7 | §3.1/§3.7 | — |
| media/probe.py | §4 C-INPUT | §2 S1/S7 | §3.10 | — |
| media/image_ops.py | §4 C-INPUT | §2 S1 | §3.10 | — |
| media/tonemap.py | §4 C-INPUT | §2 S1 [DESIGN] | §3.10 | — |
| llm/template_fallback.py | §9 R-CAP3·§2 SM-1 | §5 | §3.11 | [GATE:D5] resolve_slang |
| cli.py | §6 J-1..J-5·§3.2 | §1·§9 | §3.4 | [GATE:D3] (publish verb 부재) |

## 게이트 맵 (workflow §10 ↔ 코드)

| GATE | PRD §12 | 코드 표현 | 분류 |
|---|---|---|---|
| D1 | 수치 문턱 | s7/eval 값 `PROVISIONAL_D1` 표식, 상수 채택 금지 | 잠정 ratchet |
| D2 | 음악 소싱 | s5 `load_library()`=@gate_blocked; music/ 절대 미채움 | HARD-BLOCKED |
| D3 | 자동게시 | publish verb 부재; `publish()`=@gate_blocked | HARD-BLOCKED(B3 보류) |
| D5 | 트렌드/슬랭 | `resolve_slang()`=@gate_blocked; S3 연대순·비-슬랭 | 잠정 |
| D6 | 서명 채널 | `msix_channel()`=@gate_blocked; OV-sideload 타깃만 | 부분 해제(스파이크 잔존) |
| D7 | 디바이스 티어 | 보수 기본 티어; `autotier_measure()`=@gate_blocked | 잠정 |
| D8 | Content-ID | s5 `contentid_claim()` placeholder | 잠정 |
| D9 | HEVC 디코더 조달 | s1 `procure_decoder()`=@gate_blocked; probe된 디코더만 | HARD-BLOCKED |
| D10 | 빌드/구현 실현성(X1) | 코드 모듈 없음 — §11 빌드순서 선결, gates.py 표면화 등록 | K-class 미측정(표면화) |
| D11 | unrecoverable-failure taxonomy(X2) | 코드 모듈 없음 — §9/OPS-8 부분-상태 손상 복구 매트릭스 미명세 | 표면화(제3 BLOCKING 후보) |
| D12 | 위임-결정자 정합(L2·메타) | 코드 표현 없음(메타) — gates.py 표면화 등록 | 표면화(메타) |
| D13 | 빌드정확성 수용객체(G2) | 코드 모듈 없음 — §7 하니스는 출력품질만 | 표면화(제2 BLOCKING 후보·§8과 별개) |
| D14 | 무드음악 매칭 차원 | s5_audio.py 휴리스틱 매칭만·s7_validate.py 무드게이트 부재 | 표면화(★제1목적 직격) |
| D15 | 실사용자 수용루프 | s7_validate.py·eval 하니스 판정자=소유자/머신만 | 표면화 |
| D16 | 트렌드 갱신운영·부패수용 | s3_select_order.py·llm/template_fallback.py D5와 별개 운영축 | 표면화(D5 보완) |

> D4(Phase-0 골든 소유권)=해소(소유자); 코퍼스 *제작*은 별도 병행 BLOCKING.
> 본 구현은 eval 하니스 *구조*만, 코퍼스 미제작 (PRD §8.4/§11). Increment 1 미포함.
> **2026-05-19 PRD v0.3–v0.5 / workflow v0.3 정합(impl 표면화)**: D10–D16·§4 ALIGNMENT #1을 본 매트릭스+spine/gates.py GATES 레지스트리에 표면화(은폐 아님 — PRD §13 X3 안정성 계약 impl 계층 연장). D10–D16은 대부분 *코드 모듈 부재*(BLOCKING 미결정·수용객체/빌드선결/메타) → 표면화 등록만, 코드 결정 안 함(gates.py ANCHOR ③ 동일). §-앵커는 섹션번호 불변으로 무성부패 없음(버전핀만 X3 동반갱신).

> **(v0.9 currency 2026-05-21·어펜드-온리·번복 아님·X3 안정성 클래스)** PRD §12-**D17**(Claude Code 빌드 인증 연속성·단절 복구; v0.7 신규·v0.8 §11-L1 외부 0번 진입점 채택·v0.9 인증채널=구독 로그인 단독 부분 진전)을 본 매트릭스에 표면화. D17은 **빌드타임 게이트**(시스템 *존재* 메타전제·§8 패키징/§11 빌드순서)로 런타임 제품 게이트 D1–D16과 범주 별개 — workflow.md §10 게이트맵과 동형으로 *인라인 `[GATE:D17]` 의도적 미배치*이며 런타임 `spine/gates.py` GATES 레지스트리에 **등재하지 않는다**(런타임 D1–D16 한정이 정상·빌드 결정은 `build_state.sqlite` `build_decisions` 소관). 표면화만·코드 결정 안 함(ANCHOR ③). 종전 매트릭스가 D16에서 정지해 PRD v0.7+ 최상위 메타전제를 누락하던 desync 교정(workflow §13 v0.7~v0.9 인계 동형). D17 *해소 형태* 세부(단절 복구 메커니즘·등재 위치 §12 vs §5.2·SM-5/J-5 매핑)는 PRD §12-D17 잔존(번복 아님).
