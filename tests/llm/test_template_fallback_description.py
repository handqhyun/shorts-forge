"""template_fallback description seed — PRD §3.1 v1.1 (option A owner seed).

Reference: PRD §3.1 v1.1 currency · workflow.md §S1/§5 v1.1 ·
src/shorts_forge/llm/template_fallback.py.
"""
from __future__ import annotations

from types import SimpleNamespace

from shorts_forge.llm import template_fallback as TF
from shorts_forge.notes import description_loader as DL


def _rs(inbox, root=None, n_assets=3):
    edl = {"timeline": [{"in": 0.0, "out": 4.0}, {"in": 0.0, "out": 4.0}]}
    assets = [SimpleNamespace(isolated=False) for _ in range(n_assets)]
    return SimpleNamespace(
        edl=edl, assets=assets,
        root=root if root is not None else inbox.parent / "sfroot_no_lex",
        inbox=inbox,
    )


def _write_seed(inbox, text):
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / DL.DESCRIPTION_FILENAME).write_text(text, encoding="utf-8")


def test_missing_seed_uses_neutral_fallback(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    meta = TF.draft_metadata(_rs(inbox))
    assert meta["description_seed_used"] is False
    # neutral KR fallback contains the canonical phrase
    assert "직접 찍은 사진과 영상" in meta["description"]
    assert "총 3개 컷" in meta["description"]


def test_seed_present_replaces_fallback_prose(tmp_path):
    inbox = tmp_path / "inbox"
    _write_seed(inbox, "오늘은 한강에서 자전거를 탔어요.")
    meta = TF.draft_metadata(_rs(inbox))
    assert meta["description_seed_used"] is True
    assert meta["description"].startswith("오늘은 한강에서 자전거를 탔어요.")
    # fallback prose is no longer present
    assert "직접 찍은 사진과 영상" not in meta["description"]


def test_seed_appends_auto_info(tmp_path):
    inbox = tmp_path / "inbox"
    _write_seed(inbox, "메모 한 줄.")
    meta = TF.draft_metadata(_rs(inbox))
    # auto info line carries seconds and cut count
    assert "자동 정보" in meta["description"]
    assert "초" in meta["description"]
    assert "컷" in meta["description"]


def test_seed_multiline_preserved(tmp_path):
    inbox = tmp_path / "inbox"
    _write_seed(inbox, "첫 줄.\n둘째 줄.\n셋째 줄.")
    meta = TF.draft_metadata(_rs(inbox))
    assert "첫 줄." in meta["description"]
    assert "둘째 줄." in meta["description"]
    assert "셋째 줄." in meta["description"]


def test_seed_source_tag_records_owner(tmp_path):
    inbox = tmp_path / "inbox"
    _write_seed(inbox, "메모")
    assert "description_seed=owner" in TF.draft_metadata(_rs(inbox))["source"]


def test_no_seed_source_tag_records_fallback(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    assert "description_seed=fallback" in TF.draft_metadata(_rs(inbox))["source"]


def test_seed_deterministic(tmp_path):
    inbox = tmp_path / "inbox"
    _write_seed(inbox, "안정 시드")
    m1 = TF.draft_metadata(_rs(inbox))
    m2 = TF.draft_metadata(_rs(inbox))
    assert m1 == m2


def test_corrupt_seed_falls_back_silently(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / DL.DESCRIPTION_FILENAME).write_bytes(b"\xff\xfe bad utf-8 \x80")
    meta = TF.draft_metadata(_rs(inbox))
    assert meta["description_seed_used"] is False
    assert "직접 찍은 사진과 영상" in meta["description"]


def test_oversize_seed_falls_back_silently(tmp_path):
    inbox = tmp_path / "inbox"
    _write_seed(inbox, "x" * (DL.MAX_BYTES + 1))
    meta = TF.draft_metadata(_rs(inbox))
    assert meta["description_seed_used"] is False
    assert "직접 찍은 사진과 영상" in meta["description"]


def test_seed_truncated_at_max_chars(tmp_path):
    inbox = tmp_path / "inbox"
    _write_seed(inbox, "가" * (DL.MAX_CHARS + 50))
    meta = TF.draft_metadata(_rs(inbox))
    assert meta["description_seed_used"] is True
    # description starts with the truncated seed (MAX_CHARS chars), then auto info
    seed_part = meta["description"].split("\n\n")[0]
    assert len(seed_part) == DL.MAX_CHARS
