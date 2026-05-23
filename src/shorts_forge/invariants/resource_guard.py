"""자원 가드 — peak-RAM 예산·below-normal 우선순위·encode/model 동시금지.

추적: PRD §4 C-HW·§10 OPS-6 · workflow.md §9 · [F §3.7]
【AX-HW】 i7-1360P·Iris Xe·15.7GB 공유 RAM(실측). 피크 작업 RAM ≈10–11GB·
순차 파이프라인·encode+model 동시 실행 금지·below-normal 우선순위. NVENC/CUDA
의존은 INVARIANT #1 위반정의(C-HW) — 본 가드는 그 가정을 코드에서 차단.

설계: stdlib + ctypes(Windows)만(psutil 비의존). ctypes 실패 시 우아 강등(로그).
"""
from __future__ import annotations

import contextlib
import ctypes
import threading

TRACE = {
    "prd": "§4 C-HW",
    "workflow": "§9",
    "ax": ["AX-HW", "AX-OPS"],
    "f": ["§3.7"],
    "gate": [],
}

# 측정 봉투 기본 예산(PRD §5.1·§4 C-HW). 가역: config 로 주입 가능.
PEAK_RAM_BUDGET_BYTES = 11 * 1024**3  # ≈11GB 피크 작업 RAM 상한

_BELOW_NORMAL_PRIORITY_CLASS = 0x00004000

# encode 와 model 의 프로세스-내 상호배제(동시 실행 금지 — OPS-6)
_heavy_lock = threading.Lock()


class ResourceViolation(RuntimeError):
    """RAM 예산 초과 또는 encode/model 동시 실행 시도(C-HW 위반)."""


def set_below_normal_priority() -> bool:
    """프로세스 우선순위 below-normal(사용자 데스크톱 비기아). best-effort."""
    try:
        handle = ctypes.windll.kernel32.GetCurrentProcess()  # type: ignore[attr-defined]
        ok = ctypes.windll.kernel32.SetPriorityClass(  # type: ignore[attr-defined]
            handle, _BELOW_NORMAL_PRIORITY_CLASS
        )
        return bool(ok)
    except (AttributeError, OSError):
        return False  # 비-Windows/제한 환경 → 우아 강등(불변식 비위반)


def _avail_phys_bytes() -> int | None:
    class _MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    try:
        stat = _MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):  # type: ignore[attr-defined]
            return int(stat.ullAvailPhys)
    except (AttributeError, OSError):
        return None
    return None


def check_ram_budget(min_headroom_bytes: int = 1 * 1024**3) -> None:
    """가용 물리 RAM 이 헤드룸 미만이면 거부(피크 천장 보호). 측정 불가 시 통과."""
    avail = _avail_phys_bytes()
    if avail is not None and avail < min_headroom_bytes:
        raise ResourceViolation(
            f"가용 RAM 부족(avail={avail}, 최소헤드룸={min_headroom_bytes}). "
            f"피크 예산 {PEAK_RAM_BUDGET_BYTES} 보호(C-HW·OPS-6)."
        )


@contextlib.contextmanager
def heavy_section(kind: str):
    """무거운 구간(encode|model) 상호배제 — 동시 실행 금지(OPS-6, [F §3.7]).

    encode 와 model 을 동시에 잡으려는 설계는 구조적으로 거부된다.
    """
    if kind not in ("encode", "model"):
        raise ValueError(f"heavy_section kind 는 encode|model: {kind!r}")
    if not _heavy_lock.acquire(blocking=False):
        raise ResourceViolation(
            f"encode/model 동시 실행 금지(OPS-6·C-HW). 순차 파이프라인 강제. kind={kind}"
        )
    try:
        check_ram_budget()
        yield
    finally:
        _heavy_lock.release()
