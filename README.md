# shorts-forge

로컬 실행 전용 YouTube Shorts 자동 생성 AI agentic workflow — **게이트 비의존 구현**.

> 이 저장소는 4계층 산출물 중 *구현* 계층이다. 정본 입력:
> - 요구·제약·수용: `../PRD.md` (v0.9)
> - 설계·워크플로: `../workflow.md` (v0.6 본문 + §10/§13 v0.9 D17 currency)
> - 근거(13축 종합): `../prd-research/final-research.md`
>
> 본 코드는 PRD/workflow 의 **하위 산출물**이며 그것을 *단정하지 않는다*. 모든
> 모듈은 PRD §·workflow §·【AX-*】·[F §n]·[GATE:D#] 포인터를 보유한다(ANCHOR ①;
> 추적 불가 = 품질 실패). 매트릭스: `docs/TRACEABILITY.md`.

## 범위 (Increment 1 — SM-1 수직 슬라이스)

PRD §2 SM-1(임의 비공허 입력 → 항상 산출, 100%) 과 PRD §4 INVARIANT #1(로컬
불변, 100%) 을 end-to-end 로 *증명*하는 최소 수직 슬라이스. 모델 0 경로만.

**절대 구현 금지(게이트 차단)**: 자동 게시(D3=B3 보류) · 음악 라이브러리
콘텐츠(D2) · HEVC 디코더 조달 결정(D9) · MS Store/Azure 서명 채널(D6 잔존).
**잠정만**: 트렌드/슬랭(D5) · Content-ID(D8) · 디바이스 티어 임계(D7) · 수치 문턱(D1).
상세: `docs/TRACEABILITY.md` 게이트 맵, `../workflow.md` §10.

## INVARIANT #1 (PRD §4)

런타임은 어떤 클라우드/외부 API/텔레메트리/원격 실행도 호출하지 않는다.
명시 카브아웃 3종(1회 셋업 fetch·사용자 수동 업로드·옵트인 텍스트-only)만 예외.
픽셀(원시 사진/영상)은 어떤 모드에서도 외부 전송 금지. 검증: 네트워크 차단
E2E + 실행당 network ledger 비-카브아웃 송신 0.

## 개발

```
pip install -e .[dev]
pytest                                   # 전체 그린 = Increment 1 완료 기준
python -m shorts_forge.cli selfcheck     # 불변식 하니스 자가점검
python -m shorts_forge.cli run --dry-run <입력폴더>   # 스토리보드(렌더 없음)
python -m shorts_forge.cli run <입력폴더>             # ≤59s 9:16 .mp4 + KR 메타초안
```

> `/mnt/c`(DrvFs)에서는 venv 가 불가하므로 실제 검증은 Linux fs `~/sf-venv`로 한다
> (제품 의존 = Pillow + ffmpeg). 정확한 명령·격리 전략은 [CLAUDE.md](CLAUDE.md) 참조.

> 개발 환경은 시스템 Python 을 쓰지만 **코드는 시스템/Store Python 을 호출/의존
> 하지 않는다**([F §3.13]). 런타임 인터프리터·ffmpeg 번들은 패키징(설치기)
> 소관이며 `runtime_root_layout/LAYOUT.md` 에 명시. ffmpeg 바이너리 경로 해석은
> `media/ffmpeg_cli.py` 어댑터가 추상화한다(가역, workflow §0 #7).

## 테스트 (현재 263 passed / 0 failed)

검증은 **2계층**으로 분리된다(혼동 = 거짓 GREEN):

- **계층 A — 빌드 하니스** (`.claude/{tools,hooks}`): 계약 테스트(`tests/contracts`)·
  게이트·추적성. 빌드 *프로세스* 검증이며 제품 완성을 뜻하지 않는다.
- **계층 B — 제품 파이프라인** (`src/shorts_forge/**`): 8노드 척추·불변식·E2E.

테스트 전략 4종(`docs` 외 `tests/` 하위):

| 종 | 위치 | 범위 |
|---|---|---|
| CLI E2E | `tests/cli/` | subprocess 진입점·full 렌더·`--dry-run`·publish 부재(D3) |
| 파이프라인 통합 | `tests/stages/`·`tests/spine/` | S1–S7 스테이지별 출력계약·EDL·캐시 리롤경계 |
| Dry-Run | `tests/dryrun/` | 스토리보드 결정경로(렌더 없음·F-7 거짓GREEN 가드) |
| Hook 통합 | `tests/hooks/` | 9개 `.sh` 래퍼 stdin→exit(SOT diff 강제·egress deny) |

> "Playwright E2E"는 제품에 UI 표면이 없어 CLI E2E 로 정직 치환했다.
> 알려진 제품 버그 C1(pHash 색맹 과격리)·C2(NFD 한글 무성드롭)는 해소 —
> [decision-log.md](decision-log.md) §C.

## 문서

- [CLAUDE.md](CLAUDE.md) — 작업 규칙 정본(ANCHOR·SOT·2계층·게이트·언어·테스트).
- [AGENTS.md](AGENTS.md) — 에이전트 로스터·빌드 실행 모델·신규 에이전트 규약.
- [GEMINI.md](GEMINI.md) — 불가침 규칙 요약(Gemini 에이전트용).
- [decision-log.md](decision-log.md) — BLOCKING(PRD §12 미러)·[DESIGN]·세션 구현결정.
- `docs/TRACEABILITY.md` — 모듈 ↔ PRD/workflow/AX/F/GATE 추적 매트릭스.
- `docs/DESIGN-DECISIONS.md` — 확정·가역 설계값 상세.
