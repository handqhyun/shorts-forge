"""netguard — INVARIANT #1 로컬 불변 강제 + 실행당 network ledger.

추적: PRD §4 INVARIANT #1·§2 SM-3·§7 NEVER · workflow.md §6 · [F §3.4]
【AX-OPS】 아웃바운드 기본거부 + 실행당 네트워크 원장. 비-카브아웃 송신 0 이
INVARIANT #1 검증·SM-3. 픽셀(원시 사진/영상)은 어떤 모드에서도 외부 전송 NEVER.

설계: import 시 전역 monkeypatch 하지 않는다(테스트 러너/pip 안정성). 실행 경로가
guarded() 로 명시 설치한다. 카브아웃 3종(PRD §4)만 contextvar 스택으로 허용·기록.
"""
from __future__ import annotations

import contextlib
import contextvars
import socket
import time
from dataclasses import dataclass, field

TRACE = {
    "prd": "§4 INVARIANT #1",
    "workflow": "§6",
    "ax": ["AX-OPS"],
    "f": ["§3.4"],
    "gate": [],
}

# 카브아웃 3종 — PRD §4 명시적 비위반 예외(그 외 아웃바운드 = 위반)
CARVEOUT_SETUP_FETCH = "carveout:setup_fetch"      # 1회 ~6–12GB 셋업(재개·SHA-256·완료 후 락)
CARVEOUT_MANUAL_UPLOAD = "carveout:manual_upload"  # 사용자 주도 수동 업로드(런타임 밖)
CARVEOUT_OPTIN_TEXT = "carveout:optin_text"        # 옵트인 텍스트-only(픽셀 NEVER·기본 OFF)
_VALID_CARVEOUTS = frozenset(
    {CARVEOUT_SETUP_FETCH, CARVEOUT_MANUAL_UPLOAD, CARVEOUT_OPTIN_TEXT}
)

_carveout_stack: contextvars.ContextVar[tuple[str, ...]] = contextvars.ContextVar(
    "shorts_forge_carveout_stack", default=()
)


class InvariantViolation(RuntimeError):
    """런타임 비-카브아웃 아웃바운드 = INVARIANT #1 위반(run 즉시 실패)."""


@dataclass
class NetworkLedgerEntry:
    ts: float
    target: str
    carveout_id: str | None


@dataclass
class NetworkLedger:
    """실행당 네트워크 원장. 비-카브아웃 항목 존재 = INVARIANT #1 위반·SM-3 실패."""

    entries: list[NetworkLedgerEntry] = field(default_factory=list)

    def record(self, target: str, carveout_id: str | None) -> None:
        self.entries.append(NetworkLedgerEntry(time.time(), target, carveout_id))

    def non_carveout(self) -> list[NetworkLedgerEntry]:
        return [e for e in self.entries if e.carveout_id is None]

    def is_clean(self) -> bool:
        """비-카브아웃 송신 0 → INVARIANT #1 검증 통과(PRD §4 검증법·SM-3)."""
        return len(self.non_carveout()) == 0


@contextlib.contextmanager
def carveout(carveout_id: str):
    """명시 카브아웃 범위. 내부 아웃바운드는 허용되나 원장에 카브아웃으로 기록."""
    if carveout_id not in _VALID_CARVEOUTS:
        raise InvariantViolation(f"미정의 카브아웃: {carveout_id!r}")
    token = _carveout_stack.set(_carveout_stack.get() + (carveout_id,))
    try:
        yield
    finally:
        _carveout_stack.reset(token)


def _active_carveout() -> str | None:
    stack = _carveout_stack.get()
    return stack[-1] if stack else None


@contextlib.contextmanager
def guarded(ledger: NetworkLedger):
    """실행 경로가 파이프라인 전체를 감싸 INVARIANT #1 강제(아웃바운드 기본거부).

    socket.socket.connect 를 단일 choke point 로 패치(create_connection 도 경유).
    카브아웃 범위 밖 아웃바운드 → 원장 기록 + InvariantViolation.
    """
    original_connect = socket.socket.connect

    def guarded_connect(self, address):
        target = repr(address)
        active = _active_carveout()
        ledger.record(target, active)
        if active is None:
            raise InvariantViolation(
                f"비-카브아웃 아웃바운드 차단(INVARIANT #1·PRD §4): {target}. "
                f"런타임은 클라우드/외부 API/텔레메트리 호출 금지."
            )
        return original_connect(self, address)

    socket.socket.connect = guarded_connect  # type: ignore[method-assign]
    try:
        yield ledger
    finally:
        socket.socket.connect = original_connect  # type: ignore[method-assign]
