"""Product usage entry surfaces: smart router + user guidance mode.

Strictly layer-B (product). This package does not import the layer-A build
harness (.claude/), so infrastructure rebuild is structurally unreachable
from any branch reachable through these modules.

Trace: PRD §10 OPS-1 (one-click trigger), §1.2 (non-coder user) ·
workflow.md §1 · ANCHOR AX-ONBOARD.
"""

TRACE = {
    "prd": "§10 OPS-1, §1.2",
    "workflow": "§1",
    "ax": ["AX-ONBOARD"],
    "f": [],
    "gate": [],
}
