"""S5 AUDIO — 증분1=무음 null-track. 라이브러리 콘텐츠 [GATE:D2] 차단.

추적: PRD §4 C-MUSIC·§7 NEVER·§3.2 · workflow.md §2 S5 · 【AX-LICENSE】【AX-MEDIA】 [F §3.8/§3.1]
[GATE:D2] CC0/소유 라이브러리 *콘텐츠* 소싱·번들 미해소 → load_library() 차단,
EDL audio.track_ref=null 유지. 매칭 *엔진* 설계는 가능하나 콘텐츠 없음 → 증분1
무음(렌더서 anullsrc AAC). [GATE:D8] Content-ID 오클레임 메커니즘 = placeholder.
로컬 음악 *생성*은 기본 아님(옵트인 백그라운드 실험, 미구현).
"""
from __future__ import annotations

from ..spine.contracts import StageContract, StageResult
from ..spine.gates import GateBlocked, gate_blocked
from ..spine.runstate import RunState

TRACE = {
    "prd": "§4 C-MUSIC",
    "workflow": "§2 S5",
    "ax": ["AX-LICENSE", "AX-MEDIA"],
    "f": ["§3.8", "§3.1"],
    "gate": ["D2", "D8"],
}


@gate_blocked("D2")
def load_library():
    """[GATE:D2] CC0/소유 음악 라이브러리 *콘텐츠* 번들 = HARD-BLOCKED.

    소싱·큐레이션·진위·미러 미해소. music/ 디렉터리를 절대 채우지 않는다.
    """


def contentid_claim_placeholder() -> dict:
    """[GATE:D8] Content-ID 오클레임 관리 = 미결정 → placeholder 인터페이스만."""
    return {"gate": "D8", "status": "placeholder",
            "note": "오클레임 관리 메커니즘 미결정(제품설계). 자리표시만."}


class S5Audio(StageContract):
    stage_id = "S5"
    TRACE = TRACE

    def run(self, rs: RunState) -> StageResult:
        assert rs.edl is not None
        # D2 차단 확인(우발적 콘텐츠 번들 구조적 불가) — 호출하지 않음이 정상
        gate_events = [("D2", "blocked", "음악 라이브러리 콘텐츠 미번들(잠정 무음)"),
                       ("D8", "blocked", "Content-ID 메커니즘 placeholder")]
        rs.edl["audio"]["track_ref"] = None        # 무음 null-track
        rs.edl["audio"]["mode"] = "silent_inc1"
        rs.edl["audio"]["contentid"] = contentid_claim_placeholder()
        # 방어: load_library 가 호출되면 GateBlocked(여기선 호출 안 함)
        try:
            load_library()
            return StageResult(False, self.stage_id,
                               detail="D2 차단 우회 시도 감지(불가)")
        except GateBlocked:
            pass
        return StageResult(ok=True, stage_id=self.stage_id,
                           gate_events=gate_events,
                           detail="무음 null-track(D2/D8 차단·잠정)")
