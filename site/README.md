# shorts-forge-browser — 브라우저 안 Shorts 생성

> **자식 시스템 — 부모 `shorts-forge` (로컬 CLI)에서 분기.** 2026-05-25 소유자
> 결정 안 B(브라우저 안 ffmpeg-less 정적 사이트). 부모 정본
> (`../PRD.md` · `../workflow.md` · `../impl/`)은 본 자식 시스템과 별 객체이며
> 본 어펜드로 0 수정된다. 자세한 위상은 [`ARCH.md`](ARCH.md) 참조.

## 무엇인가

사진 여러 장을 골라 **9:16 세로 슬라이드 영상**(webm)을 브라우저 안에서 만든다.
서버 0·업로드 0·텔레메트리 0 — 사진은 사용자 브라우저 밖으로 나가지 않는다.

부모 `shorts-forge` (Python 로컬 CLI)의 *정신*만 채택:
- 8단계 결정론 척추 (현행 walking skeleton은 슬라이드만 — 정밀화는 별 turn)
- INVARIANT #1 *재해석*: "로컬 PC 전용" → "**브라우저 외 전송 0**"
- 픽셀 외부 송신 0
- 자동 게시 0

## 어떻게 쓰나

### 방법 1 — 더블클릭 (가장 쉬움)

1. `index.html` 더블클릭 (Chrome/Edge/Firefox 권장).
2. 사진 여러 장 선택 → [영상 만들기] 클릭.
3. 다운로드 링크 클릭 → `.webm` 파일 받기.

### 방법 2 — 로컬 서버 (`file://` 제약 회피)

브라우저에 따라 `file://`에서 일부 API가 막힐 수 있다. 그 경우:

```bash
cd web
python3 -m http.server 8000
# 브라우저에서 http://localhost:8000 열기
```

### 방법 3 — 정적 호스팅에 배포 (누구나 URL로 접근)

`web/` 폴더 통째로 정적 호스팅에 올린다 — 빌드 0·서버 0:

- GitHub Pages (저장소 Settings → Pages → main branch /web 폴더)
- Cloudflare Pages (Build command 없음 · Output directory `web`)
- Netlify (Drag & drop `web/` 폴더)
- 어떤 정적 호스팅이든 가능 (Vercel·S3·Firebase Hosting…)

호스팅 후에도 **사용자 사진은 호스팅 서버를 거치지 않는다** — JavaScript가
브라우저 안에서만 처리한다.

## 제약 (walking skeleton v0.1)

| 항목 | 현행 | 별 turn 잔존 |
|---|---|---|
| 포맷 | `.webm` (VP9/VP8) | `.mp4` (H.264) — ffmpeg.wasm 통합 필요 |
| 음악 | 무음 | 부모 `music/` lex 패턴 포팅 — File API 음악 선택 |
| 메모/lex | 메모는 파일명에만 | 메타데이터 JSON 동시 산출 (부모 `draft_metadata` 패턴) |
| 자동 배열 | 사용자 선택 순서 그대로 | 부모 S3 신뢰도-태그 연대순 휴리스틱 포팅 |
| 길이 한도 | 사용자 입력 (컷당 초) | 부모 C-LEN ≤59s 강제 |
| Ken Burns | 없음 | 별 turn (canvas 좌표 보간) |
| 휴대폰 성능 | 1080p 슬라이드 OK·5장 이상은 메모리 압박 가능 | 720p 옵션·점진 인코드 |

## 라이선스 / 책임

- 사용자가 직접 만든 사진 또는 권리를 가진 사진만 사용 권장.
- 본 사이트는 라이선스를 검증하지 않는다.
- 자동 YouTube 업로드 0 — 사용자가 직접 게시.

## 변경 노트

- **v0.1 (2026-05-25)** — walking skeleton. Canvas + MediaRecorder. 의존 0·CDN 0·
  단일 HTML 파일. 부모 shorts-forge v1.2 정신 채택·픽셀 송신 0.
