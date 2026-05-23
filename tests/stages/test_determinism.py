"""결정론 — 동일 입력+고정 seed → 동일 EDL·동일 스트림 파라미터([F §3.2])."""
from __future__ import annotations

import json
from pathlib import Path

from shorts_forge import cli
from shorts_forge.stages.s7_validate import _media_info


def _edl_normalized(root: Path) -> dict:
    run_dir = sorted((root / "runs").iterdir())[-1]
    edl = json.loads((run_dir / "S4" / "edl.json").read_text(encoding="utf-8"))
    # 휘발성 제거: run_id, 엔트리별 절대 slide_src 경로(run_id 포함)
    edl.pop("run_id", None)
    for e in edl["timeline"]:
        e.pop("slide_src", None)
    return edl


def _out_mp4(root: Path) -> str:
    run_dir = sorted((root / "runs").iterdir())[-1]
    man = json.loads(
        (run_dir / "S7" / "manifest.json").read_text(encoding="utf-8"))
    return man["output"]


def test_same_seed_same_input_is_deterministic(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "gen_synthetic",
        Path(__file__).parents[1] / "fixtures" / "gen_synthetic.py")
    gs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gs)

    in_a = gs.make_inbox(tmp_path / "inA")
    in_b = gs.make_inbox(tmp_path / "inB")     # 동일 절차 생성(결정론)
    root_a, root_b = tmp_path / "rA", tmp_path / "rB"
    root_a.mkdir(); root_b.mkdir()

    assert cli.cmd_run(str(in_a), root=str(root_a), dry_run=False,
                       seed=1234567) == 0
    assert cli.cmd_run(str(in_b), root=str(root_b), dry_run=False,
                       seed=1234567) == 0

    # EDL 결정론(휘발성 제거 후 완전 동일) — 콘텐츠주소 해시·순서·duration
    assert _edl_normalized(root_a) == _edl_normalized(root_b)

    # 출력 스트림 파라미터 동일(해상도·길이)
    a, b = _media_info(_out_mp4(root_a)), _media_info(_out_mp4(root_b))
    assert (a["width"], a["height"]) == (b["width"], b["height"]) == (1080, 1920)
    assert abs(a["duration"] - b["duration"]) < 0.05
