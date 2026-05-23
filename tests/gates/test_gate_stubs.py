"""게이트 강제 — 차단 경로는 GateBlocked 만 raise(우발적 구현 구조적 불가).

추적: PRD §12 D1–D16 · workflow.md §10 게이트 맵 · [F §8]
"""
from __future__ import annotations

import pytest

from shorts_forge import cli
from shorts_forge.spine.gates import GATES, GateBlocked
from shorts_forge.stages.s1_normalize import procure_decoder
from shorts_forge.stages.s3_select_order import energy_arc_reorder
from shorts_forge.stages.s5_audio import load_library
from shorts_forge.llm.template_fallback import resolve_slang

# @gate_blocked 래퍼는 인자를 무시하고 무조건 raise → 0-인자 호출로 일괄 검증
@pytest.mark.parametrize("fn,gid", [
    (procure_decoder, "D9"),     # HEVC 디코더 조달(HARD-BLOCKED)
    (energy_arc_reorder, "D5"),  # 에너지아크/트렌드(잠정)
    (load_library, "D2"),        # 음악 라이브러리 콘텐츠(HARD-BLOCKED)
    (resolve_slang, "D5"),       # 슬랭 렉시콘(잠정)
    (cli.publish, "D3"),         # 자동게시(B3 보류·HARD-BLOCKED)
])
def test_blocked_path_raises_correct_gate(fn, gid):
    with pytest.raises(GateBlocked) as ei:
        fn()
    assert ei.value.gate_id == gid
    assert getattr(fn, "__gate_blocked__", None) == gid


def test_gate_registry_complete():
    assert set(GATES) == {
        "D1", "D2", "D3", "D5", "D6", "D7", "D8", "D9",
        "D10", "D11", "D12", "D13", "D14", "D15", "D16",
    }
    assert "D4" not in GATES   # D4 해소(소유자·D4a) — 코퍼스 제작은 별도 BLOCKING
    assert "D17" not in GATES  # D17=빌드타임 게이트, 런타임 미배치(workflow.md §10 의도적 미배치)


def test_cli_has_no_publish_verb():
    with pytest.raises(SystemExit):       # publish 서브커맨드 부재
        cli.main(["publish", "anything"])


def test_full_pipeline_never_raises_gateblocked(synthetic_inbox, ascii_root):
    # S5 내부 load_library 호출→GateBlocked 포착이 정상(차단 동작 검증)
    rc = cli.cmd_run(str(synthetic_inbox), root=str(ascii_root),
                     dry_run=True, seed=1)
    assert rc == 0
