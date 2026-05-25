# shorts-forge-browser — 브라우저 안 Shorts 생성

> **자식 시스템 — 부모 `shorts-forge` (로컬 CLI)에서 분기.** 2026-05-25 소유자
> 결정 안 B(브라우저 안 정적 사이트). 부모 정본
> (`../PRD.md` · `../workflow.md` · `../impl/`)은 본 자식 시스템과 별 객체이며
> 본 어펜드로 0 수정된다. 자세한 위상은 [`ARCH.md`](ARCH.md) 참조.

## 라이브 URL

🌐 **https://handqhyun.github.io/shorts-forge/** (GitHub Actions 자동 배포)

## 무엇인가

사진 여러 장 + (옵션) 음악·메모·트렌디 키워드를 입력하면 **9:16 세로 영상**과
**메타데이터 JSON**을 브라우저 안에서 만든다. 서버 0·업로드 0·텔레메트리 0 —
입력 바이트는 사용자 브라우저 밖으로 나가지 않는다.

부모 `shorts-forge` (Python 로컬 CLI)의 정신 채택:
- INVARIANT #1 *재해석*: "로컬 PC 전용" → "**브라우저 외 전송 0**"
- 픽셀 외부 송신 0
- 자동 게시 0
- 8단계 결정론 척추 (자식 단순화 매핑 — `ARCH.md` 참조)

## 어떻게 쓰나

### 방법 1 — 라이브 URL (가장 쉬움)

위 URL 접속 → 사진 선택 → (옵션) 음악·메모·키워드 입력 → [영상 만들기] →
영상 + 메타데이터 JSON 다운로드.

### 방법 2 — 더블클릭 (오프라인)

1. `index.html` 다운로드 후 더블클릭 (Chrome/Edge/Firefox/Safari 권장).
2. 동일.

### 방법 3 — 로컬 서버 (`file://` 일부 API 제약 회피)

```bash
cd web
python3 -m http.server 8000
# 브라우저에서 http://localhost:8000 열기
```

### 방법 4 — 정적 호스팅에 직접 배포 (포크 후)

`web/` 폴더 (또는 `impl/site/` 사본)를 정적 호스팅에 — 빌드 0·서버 0:

- GitHub Pages (Actions 워크플로우 `.github/workflows/pages.yml` 포함)
- Cloudflare Pages / Netlify / Vercel — Build command 없음·Output directory `site`

## 입력 4가지

| 번호 | 항목 | 효과 |
|---|---|---|
| ① | 사진 (여러 장) | 9:16 cover-crop 슬라이드 |
| ② | 음악 (옵션·`.mp3`/`.m4a`/`.wav`/`.ogg`) | 영상 사운드트랙. 짧으면 loop·길면 자름. **라이선스 책임=사용자** |
| ③ | 영상 내용 메모 (옵션) | 메타 description·파일명·title에 반영 |
| ④ | 트렌디 키워드 (옵션·한 줄에 한 단어) | 해시태그 자동 어펜드 (기본 4 + 입력 ≤15). LocalStorage 자동 저장 |

## 산출물 2가지

- **`.mp4`** (브라우저 지원 시 — H.264+AAC) 또는 **`.webm`** (폴백 — VP9/VP8)
- **`.metadata.json`** — 부모 `draft_metadata` 동형. title·description·hashtags·source·duration·cuts 등

## v0.2 제약 (현행)

| 항목 | 현행 | 별 turn 잔존 |
|---|---|---|
| 출력 컨테이너 | mp4 (브라우저 지원 시) 또는 webm 폴백 | ffmpeg.wasm 전면 mp4 강제 — 비용/이득 별 결정 |
| 음악 라우드니스 | identity (브라우저 인코더 자체 처리) | 정밀 -14 LUFS 2-pass loudnorm |
| 음악 매칭 차원 | 소유자 선택 (부모 D14 안 2 동형) | 매칭 엔진 미도입 |
| 자동 배열 | 사용자 선택 순서 | 부모 S3 신뢰도-태그 연대순 휴리스틱 포팅 |
| 길이 한도 | 사용자 입력 (컷당 초) | 부모 C-LEN ≤59s 강제 |
| Ken Burns | 없음 | canvas 좌표 보간 |
| 휴대폰 1080p | 5장 이상 메모리 압박 가능 | 720p 옵션·점진 인코드 |
| 라이선스 검증 | 0 (사용자 책임) | (영원히 없음 정책 가능) |

## 라이선스 / 책임

- 사용자가 만든 또는 권리를 가진 사진·음악만 사용 권장.
- 본 사이트는 라이선스를 검증하지 않는다.
- 자동 YouTube 업로드 0 — 사용자가 직접 게시.

## 부록: CCM·인스피레이션 음악 합법 출처 (v0.3에서 UI에도 추가됨)

본 사이트는 음악을 **자동으로 가져오거나 삽입하지 않는다** (브라우저 외 전송
0 원칙). 인기 CCM 대부분 (Hillsong·Bethel·Elevation·Maverick City·국내 메이저
CCM 등)은 **CCLI 등 상업 라이선스 보호곡**이라 무단 사용 시 YouTube Content
ID 클레임·법적 책임 발생. CCLI는 *교회 예배 사용*만 커버하며 SNS·YouTube
게시는 별도 라이선스 필요.

본인 권리 있는 트랙(본인 작곡·구매·발행권)만 사용. 없으시면 아래에서 직접
다운로드 후 음악 슬롯에 선택:

| 출처 | 라이선스 | 메모 |
|---|---|---|
| [YouTube Audio Library](https://www.youtube.com/audiolibrary) | Google 운영·YouTube 게시 안전 | 장르 필터 "Christian"·"Inspirational" — **가장 안전** |
| [Pixabay Music](https://pixabay.com/music/) | Pixabay 라이선스 (상업 OK) | 검색 "worship"·"praise"·"hymn" |
| [Free Music Archive](https://freemusicarchive.org/) | CC0·CC-BY·CC-BY-SA 등 | 트랙별 라이선스 명시 확인 |
| [ccMixter](https://ccmixter.org/) | CC 라이선스 | 검색 "worship" |
| [Bensound](https://www.bensound.com/) | Free (크레딧) 또는 구매 | "Inspirational" 카테고리 |
| [Hymnary.org](https://hymnary.org/) | Public Domain 찬송가 | 녹음 자체는 별도 확인 |

크레딧 권장: 영상 설명(③)에 출처 한 줄.

## 변경 노트

- **v0.5 (2026-05-25)** — BGM 품질 ↑ (procedural 정교화·CDN 추가 0): 이펙트
  체인(Reverb·Chorus·Compressor·EQ3·FeedbackDelay lofi only)·베이스 라인 추가
  (MonoSynth sine 1옥타브 아래·lofi 워킹 베이스 passing tone)·8바 phrase
  A-A-B-A 변주·모드별 instrument 차별화(lofi=FMSynth e-piano / ambient=Synth
  sine + AMSynth pad layer / acoustic=FMSynth bright)·dynamics(seeded LCG
  velocity 0.55-0.9)·드럼 패턴(lofi=kick+hat+rim·acoustic=sparse kick·ambient=
  none). **한계는 여전**: 가사·보컬·실 악기 샘플 0. 진짜 피아노 샘플
  (Salamander)·ML 모델은 v0.5 안정 후 별 turn.
- **v0.4 (2026-05-25)** — 자동 BGM 생성 추가 (Tone.js procedural·CCM/예배에
  적합한 무드 3종: Lo-Fi Piano · Ambient Pad · Acoustic Arpeggio). 결정론 화성
  진행(I-V-vi-IV 변형) · 사용자 음악 파일 없을 때 토글 ON 시 자동 생성. 메타
  JSON `ai_disclosure=true`로 명시. CDN 의존 1개 (Tone.js) 추가 — 사용자 콘텐츠
  외부 전송 0 보존(INVARIANT 재해석은 ARCH.md 참조). **한계**: 진짜 프로 음질
  아님 — "심플 신시사이저 BGM" 수준. CCM 가사·보컬·실 악기 0.
- **v0.3 (2026-05-25)** — CCM·인스피레이션 합법 무료 음악 출처 카탈로그 6개
  추가 (UI details 박스 + README 부록). 자동 fetch/삽입 0 (브라우저 외 전송
  0 유지·INVARIANT 보존). 부모 정본 0 변경. 코드 의존 0.
- **v0.2 (2026-05-25)** — mp4 폴백 webm·음악 입력 (Web Audio + MediaStreamDestination)·
  트렌디 lex textarea + LocalStorage·메타데이터 JSON 동시 산출. 부모 D2/D14/D5/v1.1
  정신 통합. 의존 0 유지.
- **v0.1 (2026-05-25)** — walking skeleton. Canvas + MediaRecorder. 의존 0·CDN 0·
  단일 HTML 파일.
