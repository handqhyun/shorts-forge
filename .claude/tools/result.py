"""Single output envelope for every build-infrastructure tool.

Every tool prints exactly one JSON object of the form:

    {"status": "ok" | "error", "data": <object|null>, "errors": [<error>...]}

Reference: prompt/workflow-coding.md section 14.1.2 #10 (c). Pydantic is named in
#10 (a), but it is an external dependency and #10 (d) mandates standard library
only with external dependency 0; this module therefore uses dataclasses +
manual validation (recorded divergence: see workflow-coding currency F-32 note).
"""

from __future__ import annotations

import dataclasses
import json
import sys
from typing import Any

from . import errors

TRACE = {
    "module": "tools.result",
    "imports": ["dataclasses", "json", "sys", "typing", "tools.errors"],
    "imported_by": [
        "tools.build_state",
        "tools.sot_read",
        "tools.append_only",
    ],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-result",
}


@dataclasses.dataclass(frozen=True)
class ToolResult:
    """Immutable deterministic result envelope."""

    status: str  # "ok" | "error"
    data: Any = None
    errors: tuple = ()

    def __post_init__(self) -> None:
        if self.status not in ("ok", "error"):
            raise errors.ValidationError(
                f"status must be 'ok' or 'error', got {self.status!r}"
            )

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "data": self.data,
            "errors": list(self.errors),
        }

    def to_json(self) -> str:
        # sort_keys + fixed separators => byte-identical output for identical input.
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


def ok(data: Any = None) -> ToolResult:
    return ToolResult(status="ok", data=data)


def err(exc: Exception) -> ToolResult:
    if isinstance(exc, errors.ToolError):
        entry = {"code": exc.code, "message": exc.message, "context": exc.context}
    else:
        entry = {"code": "unexpected", "message": str(exc), "context": {}}
    return ToolResult(status="error", data=None, errors=(entry,))


def emit(result: ToolResult) -> int:
    """Print the envelope to stdout and return the process exit code."""

    sys.stdout.write(result.to_json() + "\n")
    return 0 if result.status == "ok" else 1


def run_guarded(fn) -> int:
    """Execute fn() -> ToolResult, converting any ToolError into an error envelope."""

    try:
        return emit(fn())
    except errors.ToolError as exc:
        return emit(err(exc))
