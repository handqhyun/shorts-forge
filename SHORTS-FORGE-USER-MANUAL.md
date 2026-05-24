# SHORTS-FORGE-USER-MANUAL.md — 사용자 메뉴얼

> **누구를 위한 글인가**: 한국어를 쓰는 비전문가 — 터미널·설정파일·코드를 잘
> 모르더라도 본 문서만 보고 시작할 수 있도록 작성되었다. 가장 쉬운 사용법
> ("시작하자")부터 한 단계씩 안내한다.
>
> **부모-자식 분리**: 본 메뉴얼은 자식 시스템 *shorts-forge* (로컬 Shorts
> 자동 생성) 전용이다. 부모 유기체 *AgenticWorkflow* 방법론 자체의 메뉴얼은
> 별도(`AGENTICWORKFLOW-*` 접두어).

## 자매 문서 (자식 시스템 3종)

| 무엇을 찾는가 | 어디로 |
|---|---|
| 자식 시스템 개요·자매 인덱스·정본 4축 위치 | [SHORTS-FORGE-README.md](SHORTS-FORGE-README.md) |
| 아키텍처·철학 (4축 SOT·ANCHOR·INVARIANT·8단계 척추·17 게이트·2계층·의미 라우터) | [SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md](SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md) |
| **사용자 메뉴얼 (본 문서)** | 본 문서 |

---

## ⚡ 가장 빠른 시작 — "시작하자" 한 마디

터미널을 열고 다음 한 줄을 입력한다:

```bash
shorts-forge start "시작하자"
```

그러면 화면에 **두 가지 선택지**가 나타난다:

```
shorts-forge 0.1.0 ready.
아래에서 한 가지를 골라 해당 명령을 실행하세요:

  1) 풀 렌더
     무엇이 일어나는가: 입력 폴더의 사진·영상을 모아 세로형 짧은 영상 한 편
                     (휴대폰 화면 비율·최대 약 1분)과 한국어 제목·설명 초안을
                     만든다.
     명령: shorts-forge run <입력_폴더>

  2) 스토리보드 미리보기 (렌더 없음)
     무엇이 일어나는가: 실제 영상은 만들지 않고, 어떤 사진·영상이 어떤
                     순서·길이로 들어갈지 글로만 보여 준다.
     명령: shorts-forge run <입력_폴더> --dry-run

선택지에 없는 항목은 본 진입점에서 노출되지 않습니다.
```

**다음 단계**: 두 명령 중 하나를 골라, `<입력_폴더>` 자리에 사진·영상이 들어
있는 폴더 경로를 적어 다시 실행한다.

> 💡 시작 명령은 **자연어**다. `"시작"`, `"시작하자"`, `"워크플로우 시작"`,
> `"start"`, `"let's start"` 같은 표현이 모두 인식된다. 인식 방법은 *키워드
> 박제*가 아니라 *의미 기반*이라(아래 §6 참조) 비슷한 표현이면 통한다.

---

## 1. 설치 (1회)

`shorts-forge`는 사용자 로컬 Windows PC에서만 돌아간다(클라우드 0). 설치는
한 번만 하면 된다.

### 1.1 무엇이 필요한가

- Windows 11 PC.
- 사진·영상이 들어 있는 폴더(예: 휴대폰에서 옮긴 사진들).
- 인터넷 (설치 *그 순간*에만 필요 — 모델·런타임·CC0 음악 라이브러리를 한 번
  내려받기 위해). 그 후로는 영원히 오프라인.

### 1.2 한 줄 설치 (개발용)

```bash
pip install -e .[dev]
```

> 정식 설치(소유자가 클릭만 하는 단일 인스톨러)는 `J-0` 단계로 별도 패키징된다
> (`runtime_root_layout/LAYOUT.md`). 이 메뉴얼은 *지금 개발 중인 단계*를 다룬다.

### 1.3 첫실행 자가 점검

설치가 잘 됐는지 한 줄로 확인:

```bash
shorts-forge selfcheck
```

다음과 같이 나오면 정상:

```
shorts-forge 0.1.0 — selfcheck
  [OK] UTF-8 런타임
  [OK] ffmpeg 해석: /path/to/ffmpeg
  [OK] 게이트 레지스트리 15개: D1,D10,D11,D12,D13,D14,D15,D16,D2,D3,D5,D6,D7,D8,D9
  [OK] netguard 설치/복원 (아웃바운드 기본거부)
  [OK] publish verb 부재 ([GATE:D3] 자동게시 차단)
selfcheck: PASS
```

`PASS`면 다음 단계로. `FAIL`이면 [§7 자주 만나는 문제](#7-자주-만나는-문제)
참조.

---

## 2. 가장 쉬운 사용법 (3단계)

### 단계 1 — 폴더 준비

사진·영상을 *한 폴더*에 모아 둔다. 폴더 안에 있는 모든 사진·영상이 한 편의
Shorts에 쓰인다.

```
C:\Users\woori\내Shorts재료\
├── IMG_1234.HEIC
├── IMG_1235.HEIC
├── VID_2026_05_24.mov
├── 셀카.jpg
└── ...
```

> ⚠️ **개인 미디어는 절대 외부로 나가지 않는다**(INVARIANT #1). 클라우드·외부
> API·텔레메트리 0. 안심하고 진짜 본인 사진을 넣어도 된다.

### 단계 2 — "시작하자"로 명령 확인

```bash
shorts-forge start "시작하자"
```

화면에 두 선택지가 뜬다(위 ⚡ 시작 참조).

### 단계 3 — 골라서 실행

**A. 진짜 영상이 필요할 때 → 풀 렌더**:

```bash
shorts-forge run "C:\Users\woori\내Shorts재료"
```

기다리면 다음이 나온다:

```
run 20260524-153012-abc12345: 완료
  출력: C:\Users\woori\.sf_root\runs\20260524-153012-abc12345\output.mp4
  메타초안 제목: (한국어 자동 생성 제목)
  INVARIANT #1 네트워크 원장 clean(비-카브아웃 0): True
```

`.mp4` 파일이 *바로 그 자리*에 만들어진다.

**B. "먼저 어떻게 들어갈지 보고 싶다" → 스토리보드 미리보기**:

```bash
shorts-forge run "C:\Users\woori\내Shorts재료" --dry-run
```

실제 영상은 만들지 않고, 어떤 사진·영상이 어떤 *순서·길이·전환*으로 들어갈지
글로 보여 준다. 시간·디스크 거의 0.

### 단계 4 — 게시 (수동)

`shorts-forge`는 **자동 게시를 하지 않는다**(`[GATE:D3]`·소유자 결정 보류).
v1에서는 사용자가 직접 YouTube에 업로드한다:

1. 위에서 만들어진 `.mp4` 파일을 찾는다.
2. 같은 폴더에 한국어 메타 초안(제목·설명·해시태그)이 있다.
3. YouTube 앱/웹에서 직접 업로드하고, 메타 초안을 복사·붙여넣고 1탭 편집한 뒤
   게시.

> 💡 침묵 자동 게시는 영원히 없다. *항상* 사용자가 마지막 게시 버튼을 누른다.

---

## 3. 명령 한눈에 보기

| 명령 | 무엇이 일어나는가 | 언제 쓰는가 |
|---|---|---|
| `shorts-forge start "시작하자"` | 사용자 안내 모드 = 두 선택지를 보여 준다 | **가장 먼저**. 어떻게 시작하는지 잊었을 때. |
| `shorts-forge run <폴더>` | 입력 폴더 → ≤59초 9:16 mp4 + 한국어 메타 초안 | 진짜 Shorts가 필요할 때. |
| `shorts-forge run <폴더> --dry-run` | 스토리보드만 (렌더 없음) | 영상 만들기 전에 "어떻게 들어갈지" 미리 보고 싶을 때. |
| `shorts-forge selfcheck` | 불변식·환경 점검(단일 보고) | 설치 직후·뭔가 이상할 때. |

**의도적으로 없는 명령**:
- `publish`·`upload` — `[GATE:D3]` 자동 게시 보류. 영원히 사용자 수동.
- 빌드 하니스 진입(`build`·`infra`·`harness` 등) — 사용자 안내 모드에서 노출되지
  않으며 *어떤 분기·플래그·관리자 모드로도* 들어갈 수 없다(구조적 격리).

---

## 4. 실패하면 어떻게 되는가 — 단일 "복구"

`shorts-forge`는 비전문가가 *터미널·HTTP 에러·수동 다운로드*를 보지 않게
설계되었다(PRD §10 OPS-5·SM-5). 실패 시:

| 상황 | 무엇이 일어나는가 | 사용자 행동 |
|---|---|---|
| 일부 사진이 손상되어 디코드 실패 | 그 파일만 격리 로그·배치 비중단 | 그대로 결과 확인. 불량 자산만 별도 알림. |
| 1회 셋업 다운로드 중단 | 다음 실행에 재개·무결성 검증 | "복구" 한 번. |
| 렌더 중 OOM·디코더 없음 | 단계 체크포인트 + 멱등 재진입 | 같은 명령 재실행 — 끝난 단계는 *건너뛴다*. |
| 네트워크 원장에 비-카브아웃 송신 발견 | INVARIANT #1 위반 = 종료 코드 2 | (현재 베이스라인에서는 발생 0건.) |

> 모든 실패는 비전문가 *단일 GUI "복구" 버튼*으로 회복하는 것이 요구이다(현재
> CLI 단계 — GUI는 J-0 패키징 단계 산출물).

---

## 5. 산출물은 어떻게 생겼나

### 5.1 영상 사양 (`C-OUT`)
- 컨테이너: MP4 (H.264 High + AAC-LC)
- 해상도: 1080 × 1920 (9:16 세로)
- 프레임률: 30fps
- 비트레이트: ~8–12Mbps
- 라우드니스: −14 LUFS / ≈−1 dBTP (2-pass loudnorm)
- 길이: **≤59초** (Content ID 전역 차단 절벽 회피)

### 5.2 메타 초안 (한국어)
- 제목 1줄
- 설명 (게시 전 1탭 편집)
- 해시태그

### 5.3 무엇이 *없는가*
- 음악 라이브러리 콘텐츠 — `[GATE:D2]` 미해소. 매칭 *엔진*만 있고 콘텐츠는
  번들되지 않는다 (CC0/소유/커미션만 허용).
- "트렌딩 사운드/슬랭" — `[GATE:D5]` 잠정. 연대순·비-슬랭 안전 카피로 폴백.
- 자동 게시 — `[GATE:D3]` 보류.
- HEVC 디코더 *조달* 결정 — `[GATE:D9]` 미해소. probe된 디코더만 사용.

---

## 6. "시작하자"는 어떻게 인식되나 (의미 라우터)

`shorts-forge start "..."` 명령은 *키워드 박제*가 아닌 **의미 기반 인식**을
사용한다(`src/shorts_forge/entry/router.py`). 두 개의 의미 개념(ConceptAnchor)이
있다:

| 개념 | 인식되는 표현(예시) |
|---|---|
| **INITIATE** (시작 의도) | 시작·시작하자·시작하기·시작해·시작해줘·시작합시다·스타트·start·begin·kickoff·kick off·go·let's start·lets start |
| **WORK_OBJECT** (작업 대상) | 워크플로우(를)·워크플로(를)·작업(을)·프로세스·파이프라인·workflow·work·task·process·pipeline |

**작동 원리**:
1. 사용자 입력을 NFC 정규화 + casefold + 양끝 공백·끝 구두점 제거.
2. 입력에서 단어·2-단어 묶음·전체 문장의 *후보*를 만든다.
3. 그 후보가 INITIATE 개념의 표현 집합과 교집합이 있으면 → `START_USAGE` 의도
   확정 → 안내 모드 출력.
4. 인식 실패 → 표준 에러로 예시 안내·종료 코드 1.

**중요**:
- 임베딩 0 · LLM 0 · 외부 API 0 (INVARIANT #1 보존).
- 새 표현 추가는 *데이터*(개념 집합)에 한 단어 추가하는 것이며, 인식 로직은
  변하지 않는다.

---

## 7. 자주 만나는 문제

### Q1. `shorts-forge` 명령이 안 먹는다
`pip install -e .[dev]`가 끝났는지 확인. 또는:
```bash
python -m shorts_forge.cli selfcheck
```

### Q2. `selfcheck`에서 ffmpeg `[FAIL]`이 뜬다
ffmpeg가 깔리지 않았거나 경로가 안 잡혔다. `imageio-ffmpeg`가 의존성에 포함되어
있어 보통 자동 해결되지만, 수동으로 환경변수를 설정할 수 있다:
```bash
export SHORTS_FORGE_FFMPEG=/full/path/to/ffmpeg
```

### Q3. 한글 파일명이 깨진다
NFC 정규화는 자동으로 처리된다(`C-I18N` 비협상). 만약 그래도 문제가 나면
[`decision-log.md`](decision-log.md) §C `2026-05-23 C2 NFD 한글 무성드롭 해소`
참조 — 동일 클래스 버그는 해소됨.

### Q4. 작업 경로에 한글이 있으면 안 되나?
**그렇다**. 작업 루트는 ASCII만 허용된다(`invariants/encoding.py`). 기본값
`.sf_root` (또는 `SHORTS_FORGE_ROOT` 환경변수). 입력 폴더 *경로*에는 한글이
있어도 되지만, 작업 루트는 ASCII.

### Q5. 영상이 너무 짧다/길다
- 너무 길면 자동으로 ≤59초로 잘린다(`C-LEN` 비협상).
- 너무 짧으면 입력이 부족한 것. 사진·영상을 더 넣고 다시 실행.

### Q6. "INVARIANT #1 네트워크 원장 clean: False"가 떴다
무언가가 외부로 송신을 시도했다. 정상이라면 발생하지 않아야 한다 — 본 베이스라인
(263 + 47 + 1 = 311 통과)에서는 0건. 발생 시 [`decision-log.md`](decision-log.md)
와 함께 보고.

---

## 8. 더 알고 싶다면

- 자식 시스템 아키텍처·철학 (4축 SOT·ANCHOR·INVARIANT·8단계 척추·17 게이트·
  2계층·의미 라우터의 *원리*) → [`SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md`](SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md)
- 자식 시스템 개요·자매 문서 인덱스 → [`SHORTS-FORGE-README.md`](SHORTS-FORGE-README.md)
- 결정 현황 (게이트·세션 결정·미러) → [`decision-log.md`](decision-log.md)
- 모듈 ↔ PRD/workflow 추적 → [`docs/TRACEABILITY.md`](docs/TRACEABILITY.md)

---

## 부록 A — 한 페이지 치트시트

```
시작:    shorts-forge start "시작하자"

풀 렌더:  shorts-forge run <폴더>
미리보기: shorts-forge run <폴더> --dry-run
점검:    shorts-forge selfcheck

산출:    <루트>\runs\<run_id>\output.mp4
        + 한국어 메타 초안 (제목·설명·해시태그)

게시:    영원히 *사용자 수동* (YouTube 앱/웹).
        자동 게시는 [GATE:D3] 보류 — 침묵 자동 게시 0.

불변:    클라우드·외부 API·텔레메트리 0 (INVARIANT #1).
        실행당 네트워크 원장 = 비-카브아웃 송신 0.
```
