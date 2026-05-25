"""S5 AUDIO — owner-supplied music or silent fallback.

추적: PRD §4 C-MUSIC·§7 NEVER·§3.2·§12-D2/D14 v1.2 · workflow.md §2 S5·§10 v1.2 · 【AX-LICENSE】【AX-MEDIA】 [F §3.8/§3.1]
[GATE:D2] v1.2 currency 2026-05-25 (option 2): 소유자 수동 로컬 음악 폴더.
`<sf_root>/music/` 안 소유자 배치 .mp3/.m4a/.wav 파일을 결정론(seed-based)으로
선택. 빈 폴더 / 파일 없음 = 무음 폴백(현 silent_inc1 동형).
[GATE:D14] v1.2: 매칭 차원 = '소유자 선택' (코드 명시 매칭 엔진 부재).
[GATE:D8] Content-ID 오클레임 메커니즘 = placeholder.
로컬 음악 *생성*은 기본 아님(옵트인 백그라운드 실험, 미구현).
"""
from __future__ import annotations

from ..music import loader as music_loader
from ..spine.contracts import StageContract, StageResult
from ..spine.runstate import RunState

TRACE = {
    "prd": "§4 C-MUSIC·§12-D2/D14 v1.2",
    "workflow": "§2 S5·§10 v1.2",
    "ax": ["AX-LICENSE", "AX-MEDIA"],
    "f": ["§3.8", "§3.1"],
    "gate": ["D2", "D8", "D14"],
}


def load_library(sf_root=None) -> list:
    """[GATE:D2] v1.2 currency 2026-05-25 (option 2).

    Returns sorted list of owner-placed music tracks under
    ``<sf_root>/music/``. Empty list when ``sf_root`` is ``None`` or the
    directory is missing/empty — caller falls back to silent_inc1.
    INVARIANT #1: read-only; no external fetch.
    """
    if sf_root is None:
        return []
    return music_loader.discover_tracks(sf_root)


def contentid_claim_placeholder() -> dict:
    """[GATE:D8] Content-ID 오클레임 관리 = 미결정 → placeholder 인터페이스만."""
    return {"gate": "D8", "status": "placeholder",
            "note": "오클레임 관리 메커니즘 미결정(제품설계). 자리표시만."}


class S5Audio(StageContract):
    stage_id = "S5"
    TRACE = TRACE

    def run(self, rs: RunState) -> StageResult:
        assert rs.edl is not None
        rs.edl["audio"]["contentid"] = contentid_claim_placeholder()
        gate_events = [("D8", "blocked", "Content-ID 메커니즘 placeholder")]

        # D2/D14 v1.2 (option 2): owner-managed local music folder.
        # Deterministic seed-based pick. Empty → silent_inc1 fallback (현 동작 동형).
        track = music_loader.load_for_run(rs.root, rs.seed)
        if track is None:
            rs.edl["audio"]["track_ref"] = None
            rs.edl["audio"]["mode"] = "silent_inc1"
            rs.edl["audio"]["source"] = "fallback_silent_no_owner_music"
            gate_events.append(("D2", "fallback",
                                "음악 폴더 비어있음·무음 폴백(silent_inc1 동형)"))
            detail = "무음 null-track(소유자 음악 없음·D8 placeholder)"
        else:
            rs.edl["audio"]["track_ref"] = str(track)
            rs.edl["audio"]["mode"] = "owner_track"
            rs.edl["audio"]["source"] = (
                "owner_manual_music_folder (D2/D14 v1.2 option2; "
                "license=owner_responsibility)"
            )
            gate_events.append(("D2", "owner",
                                f"소유자 음악 선택(seed-결정론): {track.name}"))
            gate_events.append(("D14", "owner",
                                "매칭 차원=소유자 선택(코드 명시 매칭 엔진 부재)"))
            detail = f"소유자 음악 트랙: {track.name} (D2/D14 v1.2 option2)"

        return StageResult(ok=True, stage_id=self.stage_id,
                           gate_events=gate_events, detail=detail)
