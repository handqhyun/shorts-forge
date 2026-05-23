"""A-2 pipeline integration — direct unit coverage of the EDL C-* hard
constraints (edl.validate), the deterministic gate that R-CAP2 requires to pass
BEFORE any media op runs. Previously covered only transitively via full E2E.

Reference: PRD §4/§8 C-OUT/C-LEN/C-THUMB · workflow.md §4 [DESIGN] D-FG ·
ANCHOR (1) no sampling.
"""
from __future__ import annotations

import pytest

from shorts_forge.spine import edl as E


def _valid_edl():
    e = E.new_edl("run0", seed=1)
    e["hero_ref"] = "slide_000.png"
    E.add_entry(e, source_ref="a.jpg", kind="still", t_in=0.0, t_out=4.0,
                transform_916={}, motion={"type": "kenburns"})
    E.add_entry(e, source_ref="b.jpg", kind="still", t_in=0.0, t_out=4.0,
                transform_916={}, motion={"type": "kenburns"})
    return e


def test_valid_edl_passes():
    E.validate(_valid_edl())              # no raise


def test_total_seconds():
    assert E.total_seconds(_valid_edl()) == 8.0


def test_empty_timeline_rejected():
    e = E.new_edl("r", 1)
    e["hero_ref"] = "x"
    with pytest.raises(E.EDLInvalid):
        E.validate(e)


def test_clen_overlength_rejected():
    e = _valid_edl()
    E.add_entry(e, source_ref="c.jpg", kind="still", t_in=0.0,
                t_out=E.MAX_SECONDS + 10, transform_916={},
                motion={"type": "kenburns"})
    with pytest.raises(E.EDLInvalid):
        E.validate(e)


def test_cout_geometry_violation_rejected():
    e = _valid_edl()
    e["target"]["w"] = 720
    with pytest.raises(E.EDLInvalid):
        E.validate(e)


@pytest.mark.parametrize("bad", sorted(E.FORBIDDEN_TRANSITIONS))
def test_g6_forbidden_transition_rejected(bad):
    e = _valid_edl()
    e["timeline"][0]["transition_in"] = bad
    with pytest.raises(E.EDLInvalid):
        E.validate(e)


def test_non_allowed_transition_rejected():
    e = _valid_edl()
    e["timeline"][0]["transition_in"] = "fade"   # not in ALLOWED (Inc1 = cut only)
    with pytest.raises(E.EDLInvalid):
        E.validate(e)


def test_time_reversal_rejected():
    e = _valid_edl()
    e["timeline"][0]["out"] = e["timeline"][0]["in"]   # out <= in
    with pytest.raises(E.EDLInvalid):
        E.validate(e)


def test_missing_hero_ref_rejected():
    e = _valid_edl()
    e["hero_ref"] = None
    with pytest.raises(E.EDLInvalid):     # C-THUMB
        E.validate(e)
