"""[DESIGN] 가역 기본값 — 근거 있는 출발점, 잠금 아님(workflow §0 #7).

추적: PRD §10 OPS-1·§5.1 C-HW · workflow.md §1/§12 [DESIGN] · [F §3.4/§3.7]
docs/DESIGN-DECISIONS.md 와 동기. 모든 값 config 주입으로 교체 가능.
"""
from __future__ import annotations

TRACE = {
    "prd": "§10 OPS-1",
    "workflow": "§1",
    "ax": ["AX-OPS", "AX-HW"],
    "f": ["§3.4", "§3.7"],
    "gate": [],
}

# D-DB Inbox 디바운스(PRD §10 OPS-1·[F §3.4]) — 안정-크기 + 정적창
INBOX_STABLE_POLLS = 3          # N회 연속 무변 → 파일 준비
INBOX_POLL_INTERVAL_S = 1.0
INBOX_QUIET_WINDOW_S = 20.0     # 정적창 = 1배치 경계
INBOX_AUTOSTART = False         # 자동시작=옵트인만(v1 안전 디폴트, "지금 처리" 원클릭)

# D-ENC 인코드(PRD §4 C-OUT/C-HW·[F §3.7]) — x264 CPU 베이스라인
ENCODE_CRF = 20
ENCODE_PRESET = "veryfast"
ENABLE_QSV = False              # h264_qsv=옵트인만(v1 자동선택 금지). NVENC 절대 금지.

# D-CS 톤맵 npl 튜너블([F §3.10])
HLG_NPL = 400
DOVI_NPL = 100
