# shorts-forge-browser — 아키텍처·위상

> 자식 시스템 — 부모 `shorts-forge` (로컬 Python CLI) 와 별 객체.
> 2026-05-25 소유자 결정 안 B (브라우저 안 정적 사이트). 부모 정본
> (`../PRD.md` · `../workflow.md` · `../impl/`) 본문 0 수정.

## 부모와의 분기

부모 `shorts-forge` (impl/) 와 본 자식은 *런타임·언어·배포·정체성*이 완전히
다르다. **공통**은 *정신*만 — 8단계 결정론 척추·픽셀 송신 0·자동 게시 0.

| 축 | 부모 (impl/) | 자식 (web/) |
|---|---|---|
| 언어 | Python 3.x + ffmpeg subprocess | HTML/JS (브라우저 네이티브) |
| 런타임 | 사용자 Windows PC (sf-venv) | 사용자 브라우저 |
| 배포 | 1회 셋업 + 로컬 CLI | 정적 호스팅 또는 단일 HTML 파일 |
| 입력 | Inbox 폴더 (HEIC/HEVC/Live Photo 등) | File API (브라우저 지원 이미지) |
| 출력 | `.mp4` (H.264 + AAC, ≤59초, -14 LUFS) | `.webm` (VP9/VP8, 가변) |
| INVARIANT | #1 = 로컬 PC 전용 | **재해석**: 브라우저 외 전송 0 |
| 의존 | Pillow·imageio-ffmpeg·sqlite | 의존 0 (CDN 0·npm 0) |

## INVARIANT #1 재해석

부모의 INVARIANT #1 = "런타임에 어떤 클라우드 서비스·외부 API·텔레메트리·
원격 실행도 호출하지 않는다." (PRD §4)

자식의 *동등* 보장 = "**사용자 브라우저 외부로 픽셀·메타데이터 전송 0**" —
즉:

- 사진/영상 바이트는 JavaScript 안에서만 (`File` → `Image` → `Canvas` →
  `MediaRecorder` → `Blob`) 흐르고 `fetch()`·`XMLHttpRequest`로 어디에도 보내지
  않는다.
- 본 페이지는 *외부 자원 의존 0* — CDN script/style/font 0. 정적 호스팅이라도
  페이지 로드 외 요청 0.
- 텔레메트리·analytics·tracking pixel 0.

이 보장은 코드 인스펙터로 즉시 검증 가능하다 (`index.html` 안에 `fetch(`·
`XMLHttpRequest`·`src="http`·`src="//"` 0건).

## 8단계 척추 — 자식 시스템 매핑 (walking skeleton)

| 부모 단계 | 자식 walking skeleton (v0.1) | 별 turn 잔존 |
|---|---|---|
| S1 NORMALIZE | `File` → `Image` (브라우저 디코더가 EXIF·회전 처리) | NFD/NFC·오염 필터·pHash 디덥 포팅 |
| S2 INGEST/ANALYZE | (없음) | Canvas pixel inspection 휴리스틱 |
| S3 SELECT/ORDER | 사용자 선택 순서 그대로 | 신뢰도-태그 연대순 (EXIF DateTime) |
| S4 ASSEMBLE | Canvas cover-crop 9:16 | Ken Burns 좌표 보간 |
| S5 AUDIO | 무음 (anullsrc 동등) | 부모 `music/` lex 포팅 — `<input type=file>` |
| S6 RENDER | `MediaRecorder` (webm VP9/VP8) | `ffmpeg.wasm` 도입 시 mp4 (별 turn 결정) |
| S7 VALIDATE | (없음) | 길이/해상도/포맷 자동 검증 |
| META | 파일명에 사용자 메모 sanitize | 부모 `draft_metadata` 패턴 — 메타 JSON 동시 산출 |

## 결정·잔존

- **D2-web (음악 입력)**: `<input type=file accept=audio/*>` + Web Audio API
  믹스 — 별 turn.
- **D3-web (자동 게시)**: 영원히 없음 — 부모 PRD §3.2 동형.
- **D5-web (트렌디)**: 부모 lex 패턴은 *서버 없는 정적 사이트*에서 어떻게
  편집·저장할지 결정 필요 (URL fragment? LocalStorage? Download/Upload `.txt`?)
  — 별 turn 결정 표면.
- **D-format (mp4 vs webm)**: ffmpeg.wasm 도입 비용 (수 MiB CDN·COOP/COEP
  헤더 요구) vs webm 그대로 — 별 turn 결정.
- **D-deploy (호스팅 위치)**: GitHub Pages? Cloudflare Pages? 단일 HTML 파일
  배포만? — 소유자 결정.

## 부모-자식 정본 분리 패턴

본 자식 시스템 신설로 인한 부모 정본 변경 0건:

- `../PRD.md` 0 수정 (본문 0 번복·신규 §·신규 D 행 0)
- `../workflow.md` 0 수정
- `../impl/` 0 수정 (영향 없음)

본 자식은 *별 저장소로 추후 분리 가능*하도록 자기-완비형(self-contained)으로
설계되었다. 현재 `web/` 디렉토리에 모든 파일이 있으며 부모 코드 0 import.

[[project-child-docs]] 패턴 동형 (2026-05-24 부모-자식 문서 분리 정신).
