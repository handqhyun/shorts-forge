# GEMINI.md — shorts-forge

이 저장소의 정본 작업 규칙은 [CLAUDE.md](CLAUDE.md), 에이전트 구성은
[AGENTS.md](AGENTS.md), 결정 현황은 [decision-log.md](decision-log.md)다.
Gemini 에이전트도 동일 규칙을 따른다. 아래는 **불가침 요약** — 충돌 시 CLAUDE.md
전문이 우선한다.

**자식 시스템 사용자 대면 문서 3종** (2026-05-24·`SHORTS-FORGE-*` 접두어):
[SHORTS-FORGE-README.md](SHORTS-FORGE-README.md) (개요·인덱스)·
[SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md](SHORTS-FORGE-ARCHITECTURE-AND-PHILOSOPHY.md)
(아키텍처)·[SHORTS-FORGE-USER-MANUAL.md](SHORTS-FORGE-USER-MANUAL.md) (메뉴얼).
사용자 대면 *내용* 어펜드는 위 3종, 작업 규칙은 본 파일 + CLAUDE.md.

## 불가침 (위반 시 작업 중단)

1. **SOT 본문 수정 금지** — `../PRD.md`·`../workflow.md`·`../prd-research/final-research.md`
   는 어펜드-온리. 본문 0 번복. 버전/상태 토큰 in-place 정정만 예외. (훅이 diff 강제.)
2. **INVARIANT #1** — 런타임은 네트워크/클라우드/원격 호출 금지(카브아웃 3종 외).
   픽셀 외부 전송 절대 금지.
3. **BLOCKING 결정은 소유자 몫** — D1–D17 게이트 값을 코드/에이전트가 결정하지
   않는다(`@gate_blocked` 차단). 비코더 소유자에게 4안(핵심·왜·트레이드오프·다음
   결과)으로 표면화.
4. **2계층 구분** — 계약/"green"은 빌드 하니스(계층 A)일 뿐 제품(계층 B) 완성이
   아니다.
5. **추적성** — 모든 `src/` 모듈에 `TRACE` dict. 미기재 = 품질 실패.
6. **언어** — 코드/주석/도크스트링은 영어 단일. SOT 마커·4안 라벨·한글 입력
   키워드·NFC 테스트 픽스처는 불변(영어화 금지).
7. **개인 미디어 금지** — 테스트·예시는 합성 inbox(`tests/fixtures/gen_synthetic.py`)만.

## 테스트 실행

```bash
PYTHONPATH=src:.claude \
  SHORTS_FORGE_FFMPEG=$(~/sf-venv/bin/python -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())') \
  ~/sf-venv/bin/python -m pytest tests/ -p no:cacheprovider   # 263 passed 기준
```
