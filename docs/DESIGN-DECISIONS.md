# [DESIGN] 결정값 — 확정·가역

workflow.md §12 가 *구현 방법* 으로 위임한 설계-계층 결정. PRD §12 소유자 게이트와
별개. 각 값은 *근거 있는 출발점*이며 상태모델/어댑터 뒤 캡슐화되어 **가역**
(workflow §0 #7). C-*·INVARIANT #1 위반 없는 한 설계 자유.

| # | 결정 | 확정값 | 가역 지점 | 근거 |
|---|---|---|---|---|
| D-CS | 작업 색공간 | BT.709 primaries·8-bit·limited-range Rec.709. HDR/P3 → S1서 1회 톤맵(HLG npl≈400 / DoVi npl≈100, npl 튜너블) | `media/tonemap.py` | workflow S1 [DESIGN], [F §3.10] |
| D-FG | EDL→필터그래프 | 엔트리별 결정론 ffmpeg 체인: `scale`+`crop/pad`→사전 업스케일 `zoompan`, `concat` 결합, 자막 libass `ass`(S6), 단일 인코드 패스 | `stages/s4_assemble.py` 매핑 | workflow S4 [DESIGN], [F §3.1] |
| D-ENC | QSV vs x264 | x264 CPU `veryfast` CRF~20 상시 베이스라인. `h264_qsv`=옵트인만, v1 자동선택 금지. QSV *디코드*만 S1 HEVC서 허용+CPU 폴백. **NVENC/CUDA 절대 금지(C-HW)** | `media/ffmpeg_cli.py` 프리셋·`config/defaults` | workflow S6 [DESIGN], [F §3.7/§3.10] · D7 잔존 |
| D-RR | 리롤 캐시 경계 | 무효화 = 창의 노드만 {S3 정렬, S5 매칭, LLM 메타}. S1/S2 콘텐츠주소 산출물 리롤 시 항상 재사용. `creative_epoch` 는 창의 캐시 키만 포함 | `spine/cache.py` CREATIVE_NODES | workflow §4 [DESIGN], [F §3.2] |
| D-DB | Inbox 디바운스 | 안정-크기 디바운스(N=3 연속 무변, 1s 간격) + 20s 정적창 = 1배치. "지금 처리" 원클릭 확정. 자동시작 = 옵트인만 | `config/defaults.py` | workflow §1, PRD §10 OPS-1, [F §3.4] |
| D-TR | 트레이스 헤더 규약 | 모든 `src/` 모듈에 `TRACE` dict (`prd`/`workflow`/`ax`/`f`/`gate` 키). 미기재 = `tests/traceability` 실패 = 품질 실패 | `tests/traceability/test_cite_grep.py` | ANCHOR ① |

## 상태머신 선택 (workflow §12)

손수제작 결정론 상태머신 1순위 채택([F §3.2], workflow §4) — 클라우드 위험 0·
최소 풋프린트. LangGraph-로컬은 동일 RunState 뒤 가역 대안(PRD 비차단), 본
증분 미채택.

## Increment 1 강등 경계 (SM-1)

모델 0 = 정상 경로(증분 1은 모델 경로 미구현). 지능 터치는 전부 고전 폴백:
S2=고전 CV 특징, S3=신뢰도-태그 연대순, S5=무음 null-track, LLM 메타=KR 템플릿.
`models/` 비어도 유효 ≤59s·9:16·1080×1920 H.264/AAC + KR 메타초안 산출(PRD §2=100%).
