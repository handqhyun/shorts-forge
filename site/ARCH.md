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

자식의 동등 보장 = "**사용자 콘텐츠(사진·음악·메모·키워드)의 브라우저 외부
전송 0**":

- 사진/음악 바이트는 JavaScript 안에서만 (`File` → `Image`/`AudioContext`/
  `Tone.js synthesis` → `Canvas`/`MediaStreamDestination` → `MediaRecorder`
  → `Blob`) 흐르고 `fetch()`·`XMLHttpRequest`로 어디에도 보내지 않는다.
- 트렌디 키워드는 브라우저 LocalStorage에만 저장 (서버 0·다른 사용자 미공유).
- 텔레메트리·analytics·tracking pixel 0.
- **v0.4 이후**: Tone.js 라이브러리(CDN 1개)는 페이지 로드 시 *코드*만 받는다
  (사용자 콘텐츠 송신 0). 부모 PRD §4 카브아웃 #1 ("1회 셋업 fetch") 정신
  정합. 사용자 미디어는 여전히 절대 외부로 나가지 않는다.

코드 인스펙터로 즉시 검증 가능:
- `index.html` 안에 `XMLHttpRequest`·tracking pixel 0건.
- 외부 `src` = Tone.js CDN 1개 (코드 라이브러리) + 사용자 클릭 anchor 6개
  (CCM 출처 카탈로그·noopener noreferrer). 자동 `fetch()` 0건.

## 8단계 척추 — 자식 시스템 매핑 (v0.2)

| 부모 단계 | 자식 v0.2 | 별 turn 잔존 |
|---|---|---|
| **S1 NORMALIZE** | `File` → `Image` (브라우저 디코더가 EXIF·회전 처리) | NFD/NFC·오염 필터·pHash 디덥 포팅 |
| **S2 INGEST/ANALYZE** | (없음) | Canvas pixel 휴리스틱 |
| **S3 SELECT/ORDER** | 사용자 선택 순서 그대로 | 신뢰도-태그 연대순 (EXIF DateTime) |
| **S4 ASSEMBLE** | Canvas 9:16 cover-crop | Ken Burns 좌표 보간 |
| **S5 AUDIO** | **3-tier 우선순위**: (a) owner audio file → AudioContext → MediaStreamDestination · (b) 자동 BGM (Tone.js procedural · 무드 3종 · 결정론 화성) → MediaStreamDestination · (c) 무음. | 정밀 -14 LUFS 2-pass loudnorm·crossfade·BPM 매칭·Magenta MusicVAE 통합 (v0.4 별 turn) |
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

### v0.4 결정 (2026-05-25)

- **D-music-gen**: "자동 곡 생성 프로그램" 사용자 요청 — 결정표면 4안
  (A/B/C/D) 중 **안 C (브라우저 ML 모델)** 채택. 그러나 *Magenta.js의 모바일
  안정성·TensorFlow.js 의존 무게·CDN URL 변동 위험*을 이유로 **v0.4는 안 C의
  부분 채택만 진행** — Tone.js 기반 procedural 합성기로 동작 검증 우선.
  Magenta.js 통합은 동작 baseline 확보 후 별 turn.

### v0.5 결정 (2026-05-25)

- **D-bgm-quality**: "BGM 퀄리티 ↑" 사용자 요청 (v0.4 모바일 동작 검증 완료
  후). 자율 진행 — procedural 안에서 가능한 4축 확장: (1) 이펙트 체인
  강화 (Reverb·Chorus·Compressor·EQ3·FeedbackDelay) (2) 베이스 라인 추가
  (MonoSynth 1옥타브 아래) (3) 8바 phrase A-A-B-A 변주 (4) 모드별 instrument
  차별화(lofi=FMSynth e-piano·ambient=Synth+AMSynth pad layer·acoustic=FMSynth
  bright). dynamics = seeded LCG velocity 0.55-0.9. 결정론 보존.

### v1.3 결정 (2026-05-25)

- **D-title-card**: 사용자 "앞에 제목 넣을지 말지·중앙 큰 글자·시간 선택"
  요청. ③-2 카드(체크박스+텍스트+초)·resolvePhase에 `title` phase 추가·
  drawTitle (120px bold·중앙·자체 fade in/out 0.5초씩)·totalTimeWithTransitions
  에 titleSec offset·메타 JSON `title` 객체.
- **D-audio-duck-ramp**: 사용자 "제목 동안 음량 줄이고 천천히 원래로" 요청.
  Web Audio AudioParam linearRampToValueAtTime로 BGM master gain(0.2→0.85)
  + 본인 음악 GainNode(0.2→1.0) 동일 패턴 적용. ramp window = title 끝나기
  0.5초 전부터 끝나고 1.5초까지 (~2초). 프레임 정확도.
- **D-validation**: title이 비활성/공백이면 titleSec=0·기존 흐름 그대로
  (회귀 0). resolvePhase·totalTime·drawPhase·makeBgm/Owner audio가 일관되게
  titleSec 0 케이스를 노옵 처리.
- **D-no-cdn**: CDN 변경 0. INVARIANT 보존(자가검증).
- **잔존 (별 turn)**: 제목 폰트/색 옵션·자막처럼 위치 옵션·끝 크레딧·로고
  오버레이·제목 + 부제목 2줄·제목 카드에 사진 1장 배경.

### v1.2 결정 (2026-05-25)

- **D-captions-burnin**: 사용자 "자막 삽입 가능하게" 요청. textarea(④-2)
  한 줄당 한 컷 매칭·자동 정렬 결과 순서대로. Canvas 2D `fillText` +
  `strokeText` (외곽선) + 둥근 모서리 반투명 검은 배경. CDN 추가 0.
- **D-caption-layout**: 화면 하단 ~13% 위치·시스템 폰트(Apple SD Gothic Neo·
  Noto Sans KR)·54px bold·greedy word wrap (한국어 char fallback)·최대 4줄·
  한 자막당 200자 cap.
- **D-caption-timing**: cut hold 중에만 표시(트랜지션/intro/outro 시 0).
  단순·예측 가능. cross fade 중 caption fade는 별 turn 잔존.
- **D-caption-alignment**: 한 줄 = 한 cut slot. 빈 줄 = 자막 없음(slot 차지).
  `#` 으로 시작하는 줄 = 주석 (slot 차지 안 함). 사용자 정렬 의도 명확화.
- **D-meta-disclosure**: `media_order[].caption` + `captions_used` /
  `captions_total_slots` 메타 JSON 필드 추가.
- **잔존 (별 turn)**: 트랜지션 중 자막 fade·자막 위치 옵션(상단/중앙)·
  폰트/크기/색 옵션·SRT 형식 import·OCR/STT 자동 생성·다국어.

### v1.1 결정 (2026-05-25)

- **D-video-full-duration**: 사용자 "동영상은 컷당 초 영향 안 받고 전부
  들어간다" 명시. v1.0의 video-clamp-to-perCut 정책 *번복*. video cut hold
  = `video.duration` (clamp [0.6초, 10분]). image cut hold = perCut 유지.
- **D-per-cut-hold-refactor**: resolvePhase + totalTimeWithTransitions가
  단일 perCut 인자 대신 `holdSecs` 배열을 받음. v0.8 transition system은
  per-cut 시간을 *데이터*로 다루는 일관된 구조로 일반화.
- **D-safety-clamp**: video hold 안전 클램프(min 0.6초·max 10분). 매우
  짧은 영상이 트랜지션보다 짧지 않도록·매우 긴 영상이 브라우저 메모리
  고갈 안 일으키도록. 사용자 의도 "전체"는 *대부분 사례에서* 그대로
  적용·극단값만 클램프.
- **D-meta-hold-disclosure**: `media_order` 각 항목에 `hold_sec` 추가 —
  사용자가 메타 JSON에서 실제 사용된 길이를 확인 가능.
- **D-no-cdn**: CDN 변경 0. INVARIANT 보존(v1.0과 동일·자가검증 통과).
- **잔존 (별 turn)**: 동영상 일부 구간만 사용(start/end trim)·여러 동영상
  사이 BPM/음악 sync·내용 분석 기반 정렬.

### v1.0 결정 (2026-05-25)

- **D-video-input**: 사용자 "동영상 삽입 가능하게" 요청. `<input
  accept="image/*,video/*">` + `loadVideo()` (HTMLVideoElement·muted=true·
  playsInline=true·crossOrigin='anonymous'). drawCoverCrop를 image/video
  통합 처리(naturalWidth || videoWidth fallback). 컷별 video.currentTime 0
  리셋 + ensureVideoState로 play/pause idempotent.
- **D-audio-mute-policy**: 사용자 "음악이 있으면 동영상 음향 X" 명시.
  v1.0 minimum = *항상 video.muted = true* (모바일 안정성·iOS Safari
  video.captureStream() 미지원 회피). 음악 없을 때 video audio 살리는
  옵션은 별 turn 결정 잔존.
- **D-auto-sort**: 사용자 "사진 분석 후 잘 맞는 순서" 요청. v1.0 minimum =
  *시간순* (EXIF DateTimeOriginal/CreateDate/ModifyDate → File.lastModified
  폴백). 사진은 exifr 라이브러리(~10KB CDN) 사용·동영상은 lastModified만.
  내용 기반 정렬(밝기·채도·색·얼굴·CV)은 별 turn 잔존.
- **D-cdn-exifr**: exifr CDN 1개 추가 (jsdelivr `exifr/dist/lite.umd.js`).
  INVARIANT 'no upload' 보존 — 라이브러리 자체 fetch만·사용자 콘텐츠
  외부 송신 0. 부모 PRD §4 카브아웃 #1 ("1회 셋업 fetch") 정신 정합.
- **D-time-accounting**: video는 v0.8 transition system과 그대로 호환 —
  resolvePhase·drawPhase의 image 자리에 video element가 들어감
  (Canvas 2D drawImage는 둘 다 받음). 단, transition (cross/fadeBlack)
  중에는 두 video가 동시 play (active set).
- **D-meta-extension**: 메타 JSON에 photos/videos count + media_order
  (각 미디어의 kind/name/timestamp) 추가 — 사용자가 자동 정렬 결과를
  확인 가능.
- **잔존 (별 turn)**: video 음향 옵션 (음악 없을 때 살림)·내용 기반 정렬
  (밝기·채도·색 군집화·face detection)·video duration 정확 사용 (현재 =
  perCut으로 강제 자름)·video transcode (브라우저 안 ffmpeg.wasm)·
  thumbnail 생성·정렬 사용자 override (drag-drop).

### v0.9 결정 (2026-05-25)

- **D-mood-categories-expand**: 사용자 "음악 카테고리 적다·더 늘려" 요청.
  3개(ambient·lofi·acoustic) → 8개(+cinematic·hymn·jazz_cafe·upbeat_pop·
  meditation). 각 mood가 독립적인 chord progression·CHORD_SYMBOLS·
  instrument·drum pattern·effects chain·TRANSITION_PROFILES 정의.
- **D-key-variety**: 기존 3개는 모두 C major였음 → cinematic만 C minor 도입
  (epic). 나머지 신규 mood는 C major 유지(ImprovRNN의 chord-conditioning
  안전성 우선).
- **D-arpeggio-variants**: upbeat_pop은 16분음 + 빠른 4-on-floor·jazz_cafe는
  brush swing comping·hymn은 SATB 4성부 voicing·meditation은 stacked 5도
  드론. Mood 간 *식별 가능한 차이* 명시.
- **D-no-cdn**: v0.8과 동일 — CDN 추가 0·INVARIANT 보존(자동 fetch 0 자가검증).
- **잔존 (별 turn)**: BPM 사용자 조절·키 선택(C/D/E/F·major/minor)·다중 mood
  mix·사용자 정의 chord progression·MIDI export·각 mood 미리 듣기 버튼.

### v0.8 결정 (2026-05-25)

- **D-transitions**: 사용자 "컷과 컷 사이에 여러 페이드 인/페이드 아웃 효과를
  적절히" 요청. 단순 cut → 트랜지션 시스템 도입. Canvas 2D `globalAlpha`
  기반 per-frame composite (외부 라이브러리 0).
- **D-transition-profile**: BGM 무드와 자동 매칭 — ambient=1.0초 crossfade·
  lofi=0.6초 crossfade + 3컷마다 0.4초 fade-through-black·acoustic=0.4초
  crossfade·BGM OFF=0.5초 기본. 사용자 입력 0 추가(UI 단순 유지).
- **D-time-accounting**: 총 시간 = intro + N×perCut + (N−1)×trans + outro.
  BGM 합성 길이와 메타 JSON `duration_sec`도 이 총 시간 따름.
- **D-no-cdn**: CDN 추가 0·v0.7 INVARIANT 보존(코드 라이브러리·정적 자원
  외 fetch 0). 자동 fetch 토큰 0건 자가검증 유지.
- **잔존 (별 turn)**: Ken Burns(컷 안 micro-motion)·slide/wipe 트랜지션·
  사용자 직접 프로파일 선택 UI·트랜지션 길이 사용자 조절.

### v0.7 결정 (2026-05-25)

- **D-melody-chord-conditioned**: 사용자 "멜로디 더 좋게·인터넷 음악 학습"
  요청 → 결정표면 4안 중 **안 1 (더 큰 사전 학습된 모델 도입)** 채택.
  Magenta `MusicRNN` + `chord_pitches_improv` 체크포인트 도입. v0.6
  MusicVAE의 가장 큰 약점(우리 화성과 무관한 random sample)을 직접 해소 —
  우리 lofi/ambient/acoustic 화성을 chord symbol로 입력하면 ImprovRNN이
  *chord-conditioned* 멜로디 생성. 결과 멜로디가 화성에 정합.
- **D-chord-mapping**: 우리 procedural progression → ImprovRNN chord
  symbol 매핑 hardcode (lofi=Cmaj7-Am7-Dm7-G7..., ambient=C-Am-F-G,
  acoustic=C-G-Am-F-G). barsNeeded × 1 chord 반복.
- **D-fallback-extended**: 4단계 → 5단계 fallback. T1+(ImprovRNN+piano)·
  T1(MusicVAE+piano)·T2(procedural+piano)·T3(v0.5 FMSynth)·silent.
  ImprovRNN 실패해도 MusicVAE 폴백·MusicVAE 실패해도 procedural 폴백.
- **D-cdn-policy 불변**: INVARIANT 'no upload' 보존 *유지*. Magenta
  ImprovRNN 체크포인트도 Google magentadata bucket (정적 자원·공개).
  사용자 콘텐츠 송신 0 자가검증 유지.
- **모바일 비용 증가**: 첫 로드 ~40-90초 (ImprovRNN ~5-10MB 추가). 견고한
  fallback으로 위험 격리.
- **잔존 (별 turn)**: Magenta MusicTransformer(더 큰 모델)·MusicGen-small
  (transformers.js·~300MB·PC only)·Performance RNN(dynamics·timing)·다중
  instrument sample pack·SaaS API 분기(별 신규 프로젝트).

### v0.6 결정 (2026-05-25)

- **D-piano-sampler**: 사용자 명시 "1번(Salamander) + 2번(Magenta) 모두 도입"
  요청 (v0.5 모바일 동작 검증 후). Salamander Grand Piano (CC0·9음 subset
  ~3-5MB·Tone.js GitHub Pages 호스팅) 도입 채택. Tone.Sampler로 통합 — 모든
  무드에서 lead instrument = 진짜 피아노.
- **D-ml-melody**: Magenta MusicVAE (`mel_2bar_small` 체크포인트·Google
  magentadata storage) 도입 채택. NoteSequence → C major transpose → Tone
  스케줄. 2바 sample 여러 개 concatenate로 영상 길이 cover.
- **D-fallback-chain**: 4단계 견고한 폴백 (T1: Magenta+Salamander·T2:
  Salamander only·T3: v0.5 procedural). 어느 단계에서 실패해도 BGM 반드시
  산출. `_enhancementCache`로 lazy load 1회만.
- **D-cdn-policy-update**: INVARIANT 'no upload' 보존 *유지* — CDN은 코드
  라이브러리·정적 오디오 샘플·ML 모델 가중치(모두 공개 정적 자원)만 받음.
  사용자 콘텐츠는 어떤 CDN/서버에도 송신 0(자동 fetch 토큰 0건 자가검증).
  부모 PRD §4 카브아웃 #1 ("1회 셋업 fetch") 정신 정합.
- **모바일 리스크 명시**: 첫 로드 ~30-60초·~20MB 다운로드·iOS Safari TFJS
  호환성 검증 못함·Magenta 유지보수 ↓(2022 이후 적극 업데이트 ↓). 견고한
  fallback으로 위험 격리.
- **잔존 (별 turn)**: 더 큰 Salamander subset (음역 확장)·MusicVAE
  `mel_4bar` 모델·chord-conditioned ImprovRNN·다중 instrument sample pack·
  BPM/키 옵션·실시간 사진 컷↔화성 동기·SaaS 음악 API 분기(별 신규 프로젝트).
- **D-cdn**: Tone.js CDN 1개 도입 (`cdn.jsdelivr.net/npm/tone@14.7.77/...`).
  INVARIANT 'no upload' *재해석*: "사용자 콘텐츠 외부 전송 0"은 보존(불변).
  코드 라이브러리 자체의 페이지 로드 시 1회 다운로드는 부모 PRD §4
  INVARIANT #1 카브아웃 #1 ("1회 셋업 fetch") 정신에 정합 — 사용자 미디어가
  아닌 *코드 자체*의 fetch. Tone.js는 사용자 콘텐츠를 받지 않는다(synthesis
  파라미터·노드 그래프만).
- **D-bgm-modes**: 무드 3종 — Lo-Fi Piano (재즈 7화음·잔잔), Ambient Pad
  (I-vi-IV-V·예배 분위기), Acoustic Arpeggio (밝음·일상). 모두 C major·결정론.
- **D-priority**: 오디오 소스 우선순위 = (a) 본인 음악 파일 > (b) 자동 BGM
  (토글 ON 시) > (c) 무음. 메타 JSON `audio_source` 필드와 `ai_disclosure`로
  BGM 사용 시 명시.
- **잔존 (별 turn)**: Magenta MusicVAE 도입·SoundFont 샘플·드럼 패턴 확장·
  BPM 옵션·다중 모드 mix·실시간 음악 동기화 (사진 컷에 맞춰 화성 전환).

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

- **v1.3 (2026-05-25)** — 제목 카드 + 음악 음량 자동 ramp-up. ③-2 카드
  (체크박스·텍스트·초 1-8)·resolvePhase에 `title` phase·drawTitle (120px
  bold·중앙·fade in/out)·BGM master gain + 본인 음악 GainNode가 동일하게
  title 중 0.2 → 끝나기 0.5초 전부터 1.5초간 원래 음량으로 linear ramp.
  메타 JSON title 객체. CDN 변경 0·INVARIANT 보존.
- **v1.2 (2026-05-25)** — 자막 burn-in 시스템 도입 (④-2 textarea·한 줄당
  한 컷·자동 정렬 결과 순서대로). Canvas 2D fillText + strokeText + 둥근
  검은 배경. 한국어 wrap(word + char fallback)·최대 4줄·시스템 폰트.
  cut hold 중에만 표시(트랜지션 시 0). 메타 JSON media_order[].caption +
  captions_used/total_slots. CDN 변경 0·INVARIANT 보존.
- **v1.1 (2026-05-25)** — 동영상 hold 시간 = 자기 duration 전체 (v1.0의
  perCut clamp 번복). resolvePhase/totalTimeWithTransitions를 per-cut
  holdSecs 배열로 일반화. 안전 클램프 [0.6초, 10분]. 메타 JSON
  media_order에 hold_sec 기록. CDN 변경 0·INVARIANT 보존.
- **v1.0 (2026-05-25)** — 동영상 입력 지원 (사진+동영상 혼재)·EXIF 기반
  자동 시간순 정렬 (exifr CDN ~10KB 추가)·동영상 음향 항상 mute (음악
  우선 정책)·video element 관리 (play/pause per cut·currentTime 0 리셋)·
  transition system과 호환 (cross 중 두 video 동시 play). 메타 JSON에
  media_order 추가. INVARIANT 보존 (자동 fetch 0 자가검증).
- **v0.9 (2026-05-25)** — BGM 무드 3→8개 확장 (cinematic·hymn·jazz_cafe·
  upbeat_pop·meditation 신규). 각 mood가 chord progression·instrument·
  drum pattern·effects chain·transition profile 독립 정의. cinematic은
  C minor (epic)·기타는 C major 유지. CDN 추가 0·INVARIANT 보존.
- **v0.8 (2026-05-25)** — 컷 사이 트랜지션 시스템 도입. Canvas 2D alpha-
  blend per-frame composite (외부 라이브러리 0). BGM 무드와 자동 매칭 —
  ambient=1.0초 crossfade·lofi=0.6초 crossfade + 3컷마다 페이드 블랙·
  acoustic=0.4초 crossfade. 인트로/아웃트로 페이드. 메타 JSON
  `transitions` 필드 추가. 총 시간/BGM 길이 자동 재계산. CDN 추가 0·
  INVARIANT 보존.
- **v0.7 (2026-05-25)** — Magenta ImprovRNN(`chord_pitches_improv` 체크포인트·
  ~5-10MB 추가) 도입. chord-conditioned 멜로디 생성으로 v0.6의 무관한
  random sample 문제 해소. 5단계 fallback (T1+/T1/T2/T3/silent). 우리
  lofi/ambient/acoustic 화성을 chord symbol로 매핑하여 ImprovRNN에 입력 →
  화성에 정합하는 멜로디. INVARIANT 보존. 모바일 첫 로드 ~40-90초.
- **v0.6 (2026-05-25)** — Salamander Grand Piano sampler(9음·~3-5MB)+Magenta
  MusicVAE(`mel_2bar_small`·~10-20MB) lazy load + 4단계 fallback chain
  (T1/T2/T3). 메타 source에 tier 명시. INVARIANT 보존(CDN=정적 자원만·사용자
  콘텐츠 송신 0 자가검증 통과). 모바일 첫 로드 ~30-60초 가능·견고한 폴백으로
  실패 격리. 부모 정본 0 수정.
- **v0.5 (2026-05-25)** — BGM 품질 ↑: 이펙트 체인(Reverb·Chorus·Compressor·
  EQ3·FeedbackDelay)·베이스 라인 추가·8바 phrase A-A-B-A 변주·모드별 instrument
  차별화·dynamics(seeded LCG velocity)·드럼 패턴 차별화. CDN 추가 0·INVARIANT
  보존. Salamander piano sample/Magenta.js는 v0.5 안정 검증 후 별 turn.
- **v0.4 (2026-05-25)** — 자동 BGM 생성 (Tone.js procedural·무드 3종)·CDN 1개
  추가 (Tone.js). INVARIANT 재해석 갱신 ("사용자 콘텐츠 외부 전송 0"은 불변·
  코드 라이브러리 페이지 로드 시 1회 fetch는 부모 카브아웃 정신 정합). 부모
  정본 0 수정. Magenta.js ML 모델은 모바일 안정성 검증 후 별 turn 잔존.
- **v0.3 (2026-05-25)** — CCM·인스피레이션 합법 무료 음악 출처 카탈로그 추가
  (UI details + README 부록). 자동 fetch/삽입 0 (INVARIANT 'no upload' 보존).
  부모 정본 0 수정. 텍스트 link만 (의존 0 유지).
- **v0.2 (2026-05-25)** — 음악 입력 (Web Audio + MediaStreamDestination) ·
  트렌디 lex textarea + LocalStorage · 메타데이터 JSON 동시 산출 · mp4 폴백 webm.
  부모 D2/D5/D14/D16/v1.1 정신 통합. 의존 0 유지·INVARIANT 'no upload' 자가
  검증 통과 (코드 인스펙터로 fetch/외부 src 0건).
- **v0.1 (2026-05-25)** — walking skeleton. Canvas + MediaRecorder. 의존 0·
  CDN 0. 단일 HTML 파일.
