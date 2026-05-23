"""S7 VALIDATE — 이진 GATE G1–G7(하드페일) + 원자적 출력 + manifest.

추적: PRD §8 GATE G1–G7·§4 INVARIANT #1 검증·§10 OPS-3 · workflow.md §2 S7·§7
 · 【AX-OPS】【AX-CRAFT】【AX-EVAL】 [F §3.4/§3.9/§3.12]
G1–G7 전부 통과 필수(미통과=수용 불가). 머신-프록시 D2/D3/D4/D6/D7 및 수치
문턱은 [GATE:D1] 잠정(Phase-0 골든 보정 전 미정의) — 본 증분 미산정. D1/D5
인간평가 큐는 Inc6. G7 한글 줄바꿈 정밀검사는 Inc4(libass+OFL 폰트=카브아웃 #1).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from pathlib import Path

from ..invariants import encoding
from ..media import ffmpeg_cli
from ..spine import edl as edlmod
from ..spine.contracts import StageContract, StageResult
from ..spine.runstate import RunState

TRACE = {
    "prd": "§8 GATE",
    "workflow": "§2 S7",
    "ax": ["AX-OPS", "AX-CRAFT", "AX-EVAL"],
    "f": ["§3.4", "§3.9", "§3.12"],
    "gate": ["D1", "D8"],
}

_DUR_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)")


def _media_info(path: str) -> dict:
    proc = subprocess.run(
        [ffmpeg_cli.resolve_ffmpeg(), "-hide_banner", "-i", path],
        capture_output=True, text=True, timeout=120,
    )
    err = proc.stderr or ""
    info = {"duration": 0.0, "width": 0, "height": 0, "has_audio": False}
    m = _DUR_RE.search(err)
    if m:
        h, mm, ss = m.groups()
        info["duration"] = int(h) * 3600 + int(mm) * 60 + float(ss)
    if "Video:" in err:
        for tok in err.split("Video:")[1].split(","):
            t = tok.strip()
            mm2 = re.search(r"(\d{3,5})x(\d{3,5})", t)
            if mm2:
                info["width"], info["height"] = int(mm2.group(1)), int(mm2.group(2))
                break
    info["has_audio"] = "Audio:" in err
    return info


def _first_frame_nonblack(rs: RunState, mp4: str) -> bool:
    fp = rs.stage_dir("S7") / "firstframe.png"
    ffmpeg_cli.run(["-i", mp4, "-frames:v", "1", "-f", "image2", str(fp)])
    from PIL import Image

    with Image.open(fp) as im:
        g = im.convert("L").resize((32, 32))
        px = list(g.getdata())
    return (sum(px) / len(px)) > 8.0   # 비흑(레터박스 전체 검정 아님)


class S7Validate(StageContract):
    stage_id = "S7"
    TRACE = TRACE

    def run(self, rs: RunState) -> StageResult:
        assert rs.edl is not None
        gates: dict[str, bool] = {}
        notes: dict[str, str] = {}
        tl = rs.edl["timeline"]
        total = edlmod.total_seconds(rs.edl)

        # G5/G6/G4/G7 = EDL 구조 기반(렌더 무관, dry-run 도 검사)
        from .s3_select_order import PROVISIONAL_D1_SHOT_BAND_MIN, SHOT_BAND_MAX

        gates["G5"] = PROVISIONAL_D1_SHOT_BAND_MIN <= len(tl) <= SHOT_BAND_MAX
        notes["G5"] = f"샷수 {len(tl)} (하한=잠정 [GATE:D1])"
        gates["G6"] = all(e["transition_in"] in edlmod.ALLOWED_TRANSITIONS
                          and e["transition_in"] not in edlmod.FORBIDDEN_TRANSITIONS
                          for e in tl)
        gates["G4"] = all(e["motion"]["type"] != "none" for e in tl)
        notes["G4"] = "정지샷 무모션 금지 — Ken Burns 적용(구조 검사)"
        gates["G7"] = all(e["caption_tokens"] for e in tl)
        notes["G7"] = "캡션 영역 존재(증분1 ASCII 바). 한글 줄바꿈 정밀=Inc4 libass"

        if rs.dry_run:
            gates["G1"] = total <= edlmod.MAX_SECONDS
            gates["G2"] = gates["G3"] = True  # 렌더 없음 — 구조 통과 간주
            notes["G1"] = f"dry-run: EDL 총 {total}s ≤ {edlmod.MAX_SECONDS}s"
            self._manifest(rs, gates, notes, output=rs.output_path)
            return self._result(rs, gates, notes)

        mp4 = rs.output_path or ""
        mi = _media_info(mp4)
        gates["G1"] = (mi["duration"] <= edlmod.MAX_SECONDS + 0.5
                       and (mi["width"], mi["height"]) == (1080, 1920))
        notes["G1"] = (f"{mi['width']}x{mi['height']} {mi['duration']:.2f}s "
                       f"(≤{edlmod.MAX_SECONDS}s·9:16)")
        gates["G2"] = _first_frame_nonblack(rs, mp4)
        notes["G2"] = "첫 렌더 프레임=사실상 썸네일=훅(비흑·비풀레터박스)"
        gates["G3"] = mi["has_audio"]
        notes["G3"] = "오디오 스트림 존재(증분1 무음 AAC·논클립)"

        # 원자적 출력: .part → 교체 (OPS-3)
        out_dir = rs.root / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        final = out_dir / f"{rs.run_id}.mp4"
        part = out_dir / f"{rs.run_id}.mp4.part"
        if all(gates.values()):
            shutil.copyfile(mp4, part)
            part.replace(final)        # 원자적 교체(검증 후)
            rs.output_path = str(final)

        self._manifest(rs, gates, notes, output=rs.output_path)
        return self._result(rs, gates, notes)

    def _result(self, rs, gates, notes) -> StageResult:
        passed = all(gates.values())
        ge = [(g, "pass" if ok else "fail", notes.get(g, ""))
              for g, ok in sorted(gates.items())]
        return StageResult(
            ok=passed, stage_id=self.stage_id, artifact_ref=rs.output_path,
            gate_events=ge,
            detail=("GATE 전체 통과" if passed
                    else "GATE 미통과: " + ",".join(g for g, ok in gates.items()
                                                  if not ok)),
        )

    def validate_output(self, rs, result: StageResult) -> None:
        if not result.ok:
            raise RuntimeError(f"S7 수용 GATE 미통과(하드페일): {result.detail}")

    def _manifest(self, rs: RunState, gates, notes, output) -> None:
        non_carveout = [vars(e) for e in rs.ledger.non_carveout()]
        iso = rs.conn.execute(
            "SELECT COUNT(*) c FROM inputs WHERE run_id=? AND isolated=1",
            (rs.run_id,)).fetchone()["c"]
        total_in = rs.conn.execute(
            "SELECT COUNT(*) c FROM inputs WHERE run_id=?",
            (rs.run_id,)).fetchone()["c"]
        man = {
            "run_id": rs.run_id, "seed": rs.seed,
            "code_version": rs.code_version, "ts": time.time(),
            "output": output,
            "gates": gates, "gate_notes": notes,
            "network_ledger": {
                "total": len(rs.ledger.entries),
                "non_carveout": non_carveout,
                "invariant1_clean": rs.ledger.is_clean(),  # SM-3·PRD §4 검증법
            },
            "inputs_total": total_in,
            "assets": len(rs.assets),
            "isolated": iso,                # 파일별 격리(배치 비중단, C-INPUT)
        }
        p = rs.stage_dir("S7") / "manifest.json"
        p.write_text(json.dumps(man, **encoding.json_dump_kwargs()),
                     encoding="utf-8")
