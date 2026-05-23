"""미디어 엔진 어댑터 — 엔진 선택을 캡슐화(가역, workflow §0 #7).

추적: PRD §4 C-OUT/C-HW/C-LIC · workflow.md §0 #7·§2 · [F §3.1/§3.7/§3.10]
ffmpeg 바이너리 경로 해석·코덱 프리셋을 추상화 → 제품은 자체 LGPL ffmpeg
번들로 교체 가능, 본 문서 권고 기본값은 *근거 있는 출발점*이지 잠금 아님.
"""

TRACE = {
    "prd": "§4 C-OUT",
    "workflow": "§0 #7",
    "ax": ["AX-MEDIA", "AX-HW"],
    "f": ["§3.1", "§3.7"],
    "gate": [],
}
