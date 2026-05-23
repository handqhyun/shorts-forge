"""전역 단일 run 락 — 직렬·FIFO(동시 다중 run 금지).

추적: PRD §10 OPS-6("전역 단일 run 락(직렬·FIFO)") · workflow.md §9 · [F §3.4/§3.7]
【AX-HW】 메모리 천장(공유 RAM ≈10–11GB 피크) → 동시 다중 run = 보장된 OOM.
v1 비목표: 무인 동시 다중 run/배치 병렬(PRD §3.2).

설계: O_EXCL 원자적 락파일 + PID staleness 재확보. FIFO 는 단일성의 부가속성.
"""
from __future__ import annotations

import contextlib
import os
from pathlib import Path

TRACE = {
    "prd": "§10 OPS-6",
    "workflow": "§9",
    "ax": ["AX-HW", "AX-OPS"],
    "f": ["§3.4", "§3.7"],
    "gate": [],
}


class RunLockBusy(RuntimeError):
    """다른 run 이 전역 락 보유 중 — 직렬 FIFO 정책(동시 실행 거부)."""


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)  # Windows: 살아있으면 OK, 없으면 OSError
    except OSError:
        return False
    return True


@contextlib.contextmanager
def run_lock(lock_path: str | os.PathLike):
    """전역 단일 run 락 획득. 보유 중이면 RunLockBusy(직렬 강제)."""
    lp = Path(lock_path)
    lp.parent.mkdir(parents=True, exist_ok=True)

    # stale 락(죽은 PID) 재확보
    if lp.exists():
        try:
            held = int(lp.read_text(encoding="utf-8").strip() or "-1")
        except (ValueError, OSError):
            held = -1
        if _pid_alive(held):
            raise RunLockBusy(
                f"전역 run 락 보유 중(pid={held}). 동시 다중 run 금지(OPS-6)."
            )
        with contextlib.suppress(OSError):
            lp.unlink()

    try:
        fd = os.open(str(lp), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RunLockBusy("전역 run 락 경합(동시 획득 시도). 직렬 FIFO.") from exc

    try:
        os.write(fd, str(os.getpid()).encode("utf-8"))
        os.close(fd)
        yield lp
    finally:
        with contextlib.suppress(OSError):
            lp.unlink()
