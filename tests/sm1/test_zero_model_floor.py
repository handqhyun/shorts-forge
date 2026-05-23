"""SM-1 바닥 — 모델 0 에서도 유효 ≤59s·9:16 mp4 + KR 메타초안(PRD §2=100%).

추적: PRD §2 SM-1·§7 ALWAYS·§9 R-CAP1 · workflow.md §0 #4 · [F §3.3]
"""
from __future__ import annotations

import json

from shorts_forge import cli
from shorts_forge.stages.s7_validate import _media_info


def test_zero_model_produces_valid_short(synthetic_inbox, ascii_root):
    # models/ 디렉터리 미존재 = 모델 0(증분1 정상 경로). 네트워크 0.
    rc = cli.cmd_run(str(synthetic_inbox), root=str(ascii_root),
                     dry_run=False, seed=1234567)
    assert rc == 0

    run_dir = sorted((ascii_root / "runs").iterdir())[-1]
    manifest = json.loads(
        (run_dir / "S7" / "manifest.json").read_text(encoding="utf-8"))

    # 모든 이진 GATE 통과(미통과=수용 불가)
    assert all(manifest["gates"].values()), manifest["gates"]

    out_mp4 = manifest["output"]
    assert out_mp4 and out_mp4.endswith(".mp4")
    mi = _media_info(out_mp4)
    assert (mi["width"], mi["height"]) == (1080, 1920)      # 9:16 1080×1920
    assert 0 < mi["duration"] <= 59.5                        # C-LEN ≤59s
    assert mi["has_audio"]                                   # 무음 AAC 존재

    # KR 메타초안(텍스트만·픽셀 NEVER) — J-3
    meta_files = list((ascii_root / "out").glob("*.metadata.json"))
    assert meta_files
    meta = json.loads(meta_files[0].read_text(encoding="utf-8"))
    assert meta["title"] and any(ord(c) > 0x3000 for c in meta["title"])  # 한글 포함
    assert len(meta["hashtags"]) <= 15                       # >15 면 전부 무시
    assert meta["ai_disclosure"] is False                    # 무음·실사 조합


def test_some_inputs_isolated_but_batch_not_aborted(synthetic_inbox, ascii_root):
    cli.cmd_run(str(synthetic_inbox), root=str(ascii_root),
                dry_run=False, seed=1)
    run_dir = sorted((ascii_root / "runs").iterdir())[-1]
    manifest = json.loads(
        (run_dir / "S7" / "manifest.json").read_text(encoding="utf-8"))
    # 0바이트·디코드불가·파노·스크린샷명·근중복 격리되나 배치는 완주
    assert manifest["isolated"] >= 5
    assert manifest["assets"] > manifest["isolated"]
