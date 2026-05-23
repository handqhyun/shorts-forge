"""S1 NORMALIZE — 회전 베이크 멱등·NFC·오염필터·신뢰도 태깅(PRD §4 C-INPUT/C-SPINE)."""
from __future__ import annotations

from pathlib import Path

from shorts_forge.media import image_ops
from shorts_forge.spine.runstate import new_run
from shorts_forge.stages.s1_normalize import S1Normalize


def _run_s1(inbox, root):
    rs = new_run(root, inbox, code_version="test", seed=1)
    stage = S1Normalize()
    res = stage.run(rs)
    stage.validate_output(rs, res)
    return rs, res


def test_s1_isolates_contamination_but_keeps_valid(synthetic_inbox, ascii_root):
    rs, res = _run_s1(synthetic_inbox, ascii_root)
    iso_text = " ".join(res.isolated_inputs)
    assert "broken.jpg" in iso_text          # 0바이트
    assert "weird.heic" in iso_text          # 디코드 불가([GATE:D9] 조달 안 함)
    assert "PANO_0001" in iso_text           # 파노 종횡비
    assert "Screenshot" in iso_text          # 스크린샷명 프록시(잠정)
    assert "IMG_DUP" in iso_text             # 근중복(pHash)
    # 유효 자산은 보존·배치 비중단
    assert len(rs.assets) >= 14
    names = {Path(a.src_path_nfc).name for a in rs.assets}
    assert any(n.startswith("IMG_0000") for n in names)


def test_s1_nfd_korean_filename_preserved(synthetic_inbox, ascii_root):
    rs, _ = _run_s1(synthetic_inbox, ascii_root)
    # NFD '여행사진.jpg' 가 NFC 정규화되어 무성 손실 없이 포함
    joined = "".join(a.src_path_nfc for a in rs.assets)
    assert "여행사진" in joined


def test_s1_rotation_baked_and_idempotent(synthetic_inbox, ascii_root):
    rs, _ = _run_s1(synthetic_inbox, ascii_root)
    # 모든 still 자산은 회전 베이크 완료(orientation=1)
    for a in rs.assets:
        if a.kind == "still":
            assert a.orientation == 1
    # EXIF Orientation=6 였던 IMG_0002 → 정규화 PNG 는 세로(회전 반영)
    rotated = [a for a in rs.assets
               if Path(a.src_path_nfc).name == "IMG_0002.jpg"]
    assert rotated
    from PIL import Image
    with Image.open(rotated[0].work_path) as im:
        w, h = im.size
    assert h > w                              # 1200x800 → 800x1200
    # 재베이크 멱등(정규화본엔 EXIF 없음 → 추가 회전 없음)
    again = Path(rs.stage_dir("S1")) / "reb.png"
    image_ops.bake_rotation_and_normalize(rotated[0].work_path, again)
    with Image.open(again) as im2:
        assert im2.size == (w, h)


def test_s1_confidence_tier_from_exif(synthetic_inbox, ascii_root):
    rs, _ = _run_s1(synthetic_inbox, ascii_root)
    # 카메라 EXIF DateTimeOriginal 보유 → 최상 신뢰도(tier 1, C-SPINE 5단계)
    cam = [a for a in rs.assets
           if Path(a.src_path_nfc).name.startswith("IMG_00")]
    assert cam and all(a.confidence_tier == 1 for a in cam)
    # 신뢰도-태그 연대순 안정 정렬(단조 가정 금지·best-effort)
    ts = [a.timestamp for a in rs.assets if a.timestamp is not None]
    assert ts == sorted(ts)
