# 런타임 루트 레이아웃 (문서화 전용 — 여기서 생성하지 않음)

추적: PRD §4(INVARIANT #1 인코딩 위반정의)·§6 J-0·§10 OPS · workflow.md §6/§8 · [F §3.13/§3.11]

제품 설치기(별도 산출물, 본 저장소 범위 밖)가 아래 트리를 생성한다. **ASCII-only**,
사용자 프로필 경로(`C:\Users\<한글이름>`) 비의존 — 한글 사용자명+CP949+subprocess =
보장된 실패([F §3.13]). 코드는 이 루트를 `SHORTS_FORGE_ROOT` 환경/설정으로 주입받고,
부재 시 개발용 임시 ASCII 경로로 폴백한다(테스트는 tmp 사용).

```
C:\ProgramData\ShortsForge\
├─ python\          사설 번들 인터프리터       시스템/Store Python 절대 비의존 [F §3.13]
├─ bin\ffmpeg\      LGPL ffmpeg + libass>=0.17 GPL 인코더 없음·고지 동봉 [F §3.1/§3.11]
├─ models\          1회 셋업 fetch 산출(카브아웃 #1)  빈 상태여도 SM-1 동작(모델=품질만)
├─ music\           [GATE:D2] HARD-BLOCKED       우리가 절대 채우지 않음(라이선스 미해소)
├─ fonts\           KR 폰트 + OFL.txt(카브아웃 #1)  Pretendard/Noto Sans KR(OFL) [F §3.11]
├─ inbox\           사용자 입력 드롭(J-1)        안정-크기 디바운스+정적창 1배치
├─ work\            중간 작업표현               below-normal·원자적
├─ runs\<run_id>\   단계별 체크포인트·산출       멱등 재진입(OPS-3)
├─ out\             최종 .mp4 + 메타초안         원자적 .part→교체
├─ state.sqlite     run 상태·network ledger     비-카브아웃 송신 0 = INVARIANT #1 검증
├─ offline.lock     1회 셋업 후 오프라인 락      부재 시 로컬-only/SM-1 모드
└─ logs\            JSON 로그                    서버형 관찰 스택 금지(OPS-4)
```

카브아웃 3종(PRD §4, 그 외 네트워크 = 위반):
1. 1회 ~6–12GB 셋업 fetch(재개·SHA-256·미러우선·완료 후 offline.lock)
2. 사용자 주도 수동 YouTube 업로드(런타임 밖)
3. 옵트인 텍스트-only(파생 텍스트만·픽셀 NEVER·기본 OFF)
