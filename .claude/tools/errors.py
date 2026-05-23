"""Enumerable exception classes shared by all build-infrastructure tools.

Reference: prompt/workflow-coding.md section 14.1.2 #10 (h). A shared errors module
was chosen over per-module errors files to keep cross-tool exception handling
uniform (authoring decision recorded here, ADR-style).

Every tool raises only the classes enumerated here, so the deterministic
{"status": "error", ...} envelope can map an exception to a stable error code.
"""

from __future__ import annotations

TRACE = {
    "module": "tools.errors",
    "imports": ["__future__"],
    "imported_by": [
        "tools.result",
        "tools.build_state",
        "tools.sot_read",
        "tools.append_only",
    ],
    "writes_state_keys": [],
    "reads_state_keys": [],
    "adapter_boundary_id": "ADAPT-TOOL-errors",
}


class ToolError(Exception):
    """Base class for every deterministic tool error.

    `code` is a stable, machine-readable identifier used in the error envelope.
    """

    code = "tool_error"

    def __init__(self, message: str, **context: object) -> None:
        super().__init__(message)
        self.message = message
        self.context = dict(context)


class UsageError(ToolError):
    """Invalid CLI arguments, missing required fields, or malformed input."""

    code = "usage_error"


class ValidationError(ToolError):
    """Input value failed a schema or invariant check."""

    code = "validation_error"


class NotFoundError(ToolError):
    """A requested section, file, row, or key does not exist."""

    code = "not_found_error"


class StateError(ToolError):
    """build_state.sqlite is missing, uninitialized, or in an unexpected state."""

    code = "state_error"


class IntegrityError(ToolError):
    """A SHA-256 anchor, pair invariant, or atomicity guarantee was violated."""

    code = "integrity_error"


class InvariantViolationError(ToolError):
    """INVARIANT #1 (no network) or another non-negotiable invariant was violated."""

    code = "invariant_violation_error"


ALL_ERRORS = (
    ToolError,
    UsageError,
    ValidationError,
    NotFoundError,
    StateError,
    IntegrityError,
    InvariantViolationError,
)
