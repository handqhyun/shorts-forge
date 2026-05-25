# shorts-forge-browser — 아키텍처·위상

> 자식 시스템 — 부모 `shorts-forge` (로컬 Python CLI) 와 별 객체.
> 2026-05-25 소유자 결정 안 B (브라우저 안 정적 사이트). 부모 정본
> (`../PRD.md` · `../workflow.md` · `../impl/`) 본문 0 수정.

## 라이브 URL

- 정적 배포: **https://handqhyun.github.io/shorts-forge/**
- 배포 경로: GitHub Actions (`.github/workflows/pages.yml`) — main 브랜치의
  `site/` 폴더를 그대로 발행 (Jekyll 우회 — `.nojekyll`).

## 부모와의 분기

부모 `shorts-forge` (impl/) 와 본 자식은 *런타임·언어·배포·정체성*이 완전히
다르다. **공통**은 *정신*만 — 픽셀 송신 0·자동 게시 0·소유자 직접 입력.

| 축 | 부모 (impl/) | 자식 (web/) |
|---|---|---|
| 언어 | Python 3.x + ffmpeg subprocess | HTML/JS (브라우저 네이티브) |
| 런타임 | 사용자 Windows PC (sf-venv) | 사용자 브라우저 |
| 배포 | 1회 셋업 + 로컬 CLI | 정적 호스팅 (GitHub Pages 등) 또는 단일 HTML |
| 입력 | Inbox 폴더 + `<sf_root>/lex/trending.txt` + `<sf_root>/music/` + `<inbox>/description.txt` | `<input>` 4종 (사진·음악·메모·lex) — 동일 정신 |
| 출력 | `.mp4` (H.264 + AAC, ≤59초, -14 LUFS 2-pass) + 메타초안 JSON | `.mp4` (가용 시) 또는 `.webm` (폴백) + 메타데이터 JSON |
| INVARIANT | #1 = 로컬 PC 전용 | **재해석**: 브라우저 외 전송 0 |
| 의존 | Pillow·imageio-ffmpeg·sqlite | 의존 0 (CDN 0·npm 0·ffmpeg.wasm 0) |

## INVARIANT #1 재해석

부모의 INVARIANT #1 = "런타임에 어떤 클라우드 서비스·외부 API·텔레메트리·
원격 실행도 호출하지 않는다." (PRD §4)

자식의 동등 보장 = "**사용자 브라우저 외부로 픽셀·메타데이터·텍스트 전송 0**":

- 사진/음악 바이트는 JavaScript 안에서만 (`File` → `Image`/`AudioContext`
  → `Canvas`/`MediaStreamDestination` → `MediaRecorder` → `Blob`) 흐르고
  `fetch()`·`XMLHttpRequest`로 어디에도 보내지 않는다.
- 트렌디 키워드는 브라우저 LocalStorage에만 저장 (서버 0·다른 사용자 미공유).
- 본 페이지는 외부 자원 의존 0 — CDN script/style/font/이미지 0. 페이지
  로드 외 네트워크 요청 0.
- 텔레메트리·analytics·tracking pixel 0.

코드 인스펙터로 즉시 검증 가능:
- `index.html` 안에 `fetch(` · `XMLHttpRequest` · `src="http` · `src="//"` ·
  `@import` 0건.

## 8단계 척추 — 자식 시스템 매핑 (v0.2)

| 부모 단계 | 자식 v0.2 | 별 turn 잔존 |
|---|---|---|
| **S1 NORMALIZE** | `File` → `Image` (브라우저 디코더가 EXIF·회전 처리) | NFD/NFC·오염 필터·pHash 디덥 포팅 |
| **S2 INGEST/ANALYZE** | (없음) | Canvas pixel 휴리스틱 |
| **S3 SELECT/ORDER** | 사용자 선택 순서 그대로 | 신뢰도-태그 연대순 (EXIF DateTime) |
| **S4 ASSEMBLE** | Canvas 9:16 cover-crop | Ken Burns 좌표 보간 |
| **S5 AUDIO** | **owner audio file → AudioContext → MediaStreamDestination** (option file → audio track of combined MediaStream). 짧으면 loop·길면 stop=총길이. 음악 없으면 무음. | 정밀 -14 LUFS 2-pass loudnorm·crossfade·apad+atrim·BPM 매칭 |
| **S6 RENDER** | `MediaRecorder` (mp4 H.264+AAC 우선 · webm VP9/VP8 폴백). 비디오/오디오 트랙 결합. | ffmpeg.wasm 통합 시 mp4 강제 (별 결정) |
| **S7 VALIDATE** | 없음 | 길이/해상도/포맷 자동 검증 |
| **META** (부모 §5 LLM 노드) | 결정론 KR 메타 JSON 동시 산출. seed = memo textarea (parent description.txt 동형). hashtags = base 4 + lex (parent lex/trending.txt 동형·dedup·≤15). | 다국어·요약 모델·BPM 정합 |

## 결정·잔존

### 본 turn 결정 (v0.2)

- **D-format**: `MediaRecorder.isTypeSupported` 우선순위 자동 선택 — mp4
  (H.264+AAC) 우선·실패 시 webm (VP9/VP8). ffmpeg.wasm 미도입 (의존 0 유지·
  30 MiB CDN/COOP-COEP 회피). 사용자에겐 details 토글로 짧게 설명.
- **D2-web (음악 입력)**: `<input type=file accept=audio/*>` + Web Audio API
  (`decodeAudioData` → `MediaStreamDestination`). 부모 D2 안 2 동형 — 소유자
  직접 파일·라이선스 책임=소유자·짧으면 loop·길면 stop으로 자름. 정밀
  라우드니스 정규화는 별 turn 잔존.
- **D5-web (트렌디 lex)**: textarea (한 줄에 한 단어·`#` 주석·NFC). 저장 =
  브라우저 LocalStorage (`shorts_forge_browser_lex_v1` 키). 부모 lex 정신
  동형 — 외부 fetch 0. "키워드 저장 지우기" 버튼으로 명시 삭제.
- **D-meta (메타 산출)**: 부모 `draft_metadata` 동형 JSON 별 다운로드. 영상에
  메타 임베드는 안 함 (mp4 metadata box 변경 = ffmpeg/별 라이브러리 필요).

### v0.3 결정 (2026-05-25)

- **D-music-catalog**: "자동 음악 선택·삽입" 사용자 요청 — 결정표면 4안
  (P/Q/R/S) 중 **안 R (합법 무료 음악 출처 카탈로그 추가)** 채택. 이유:
  자동 fetch는 INVARIANT 'no upload'·부모 v1.2 D2/D14·저작권 (CCM 인기곡
  대부분 CCLI 상업 보호) 동시 위반. 카탈로그 안내는 사용자의 *출처 발견 부담*만
  해소하며 다운로드는 사용자 본인이 직접. UI details 박스 + README 부록. 자동
  매칭/삽입 기능 추가 **0**. CCLI 안내 명시 (예배 사용만 커버·SNS 별도).

### 잔존 (별 turn)

- **D3-web (자동 게시)**: 영원히 없음 — 부모 PRD §3.2 동형. 변경 0.
- **D-deploy 확장**: Cloudflare Pages·Netlify·Vercel 다중 배포·custom domain —
  소유자 결정.
- **D-locale**: 영어/일본어 UI 옵션 — 본 v0.2는 한국어 단일.
- **D-format 진화**: ffmpeg.wasm 도입 시 mp4 강제·정밀 loudnorm·자막 burnin —
  의존 vs 호환성 트레이드오프 재결정.
- **D-thumbnail**: 영상 첫 프레임 자동 추출 별 다운로드.

## 부모-자식 정본 분리 패턴

본 자식 시스템 신설·진화로 인한 부모 정본 변경 0건:

- `../PRD.md` 0 수정 (본문 0 번복·신규 §·신규 D 행 0)
- `../workflow.md` 0 수정
- `../impl/src/` 0 수정 (Python 코드 0)

본 자식은 *별 저장소로 추후 분리 가능*하도록 자기-완비형(self-contained)으로
설계되었다 (`web/` 디렉토리 + `impl/site/` 미러). 부모 코드 0 import.

[[project-child-docs]] 패턴 동형 (2026-05-24 부모-자식 문서 분리 정신).

## 변경 노트

- **v0.3 (2026-05-25)** — CCM·인스피레이션 합법 무료 음악 출처 카탈로그 추가
  (UI details + README 부록). 자동 fetch/삽입 0 (INVARIANT 'no upload' 보존).
  부모 정본 0 수정. 텍스트 link만 (의존 0 유지).
- **v0.2 (2026-05-25)** — 음악 입력 (Web Audio + MediaStreamDestination) ·
  트렌디 lex textarea + LocalStorage · 메타데이터 JSON 동시 산출 · mp4 폴백 webm.
  부모 D2/D5/D14/D16/v1.1 정신 통합. 의존 0 유지·INVARIANT 'no upload' 자가
  검증 통과 (코드 인스펙터로 fetch/외부 src 0건).
- **v0.1 (2026-05-25)** — walking skeleton. Canvas + MediaRecorder. 의존 0·
  CDN 0. 단일 HTML 파일.
