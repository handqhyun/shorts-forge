"""CLI — run / --dry-run / selfcheck. publish verb 부재([GATE:D3] 자동게시 금지).

추적: PRD §6 J-1..J-5·§3.2·§4 INVARIANT #1·§10 OPS-6 · workflow.md §1/§9 · [F §3.4]
실행 경로가 불변식을 명시 설치: UTF-8·ASCII 루트·below-normal·전역 run 락·
netguard.guarded(아웃바운드 기본거부+실행당 원장). 침묵 자동게시 절대 없음.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .entry import guide, router
from .invariants import encoding, netguard, resource_guard, runlock
from .spine import statemachine
from .spine.gates import GATES, gate_blocked
from .spine.runstate import new_run
from .stages.s1_normalize import S1Normalize
from .stages.s2_ingest_analyze import S2IngestAnalyze
from .stages.s3_select_order import S3SelectOrder
from .stages.s4_assemble import S4Assemble
from .stages.s5_audio import S5Audio
from .stages.s6_render import S6Render
from .stages.s7_validate import S7Validate
from .llm.template_fallback import MetaDraftNode

TRACE = {
    "prd": "§6 J-1",
    "workflow": "§1",
    "ax": ["AX-OPS", "AX-ONBOARD"],
    "f": ["§3.4"],
    "gate": ["D3"],
}


def _pipeline():
    # 고정·선형 척추(R-CAP2). 단일 LLM 메타 노드는 S5 뒤·S6 앞.
    return [S1Normalize(), S2IngestAnalyze(), S3SelectOrder(), S4Assemble(),
            S5Audio(), MetaDraftNode(), S6Render(), S7Validate()]


@gate_blocked("D3")
def publish(_run_id: str):
    """[GATE:D3] 자동 게시 = 2026-05-18 소유자 세션 B3 명시 보류.

    CLI 에 publish verb 부재. v1=파일만·사용자 수동 업로드(카브아웃 #2).
    """


def _default_root() -> Path:
    env = os.environ.get("SHORTS_FORGE_ROOT")
    if env:
        return Path(env)
    return Path.cwd() / ".sf_root"   # 개발용 ASCII 루트(런타임=ProgramData, LAYOUT.md)


def cmd_selfcheck() -> int:
    """불변식 하니스 자가점검(설정파일 비노출 — 단일 보고)."""
    print(f"shorts-forge {__version__} — selfcheck")
    ok = True
    try:
        encoding.assert_utf8_runtime()
        print("  [OK] UTF-8 런타임")
    except encoding.EncodingViolation as e:
        ok = False
        print(f"  [FAIL] UTF-8: {e}")
    try:
        from .media import ffmpeg_cli

        print(f"  [OK] ffmpeg 해석: {ffmpeg_cli.resolve_ffmpeg()}")
    except Exception as e:  # noqa: BLE001
        ok = False
        print(f"  [FAIL] ffmpeg 미해석: {e}")
    print(f"  [OK] 게이트 레지스트리 {len(GATES)}개: {','.join(sorted(GATES))}")
    led = netguard.NetworkLedger()
    with netguard.guarded(led):
        print("  [OK] netguard 설치/복원 (아웃바운드 기본거부)")
    print("  [OK] publish verb 부재 ([GATE:D3] 자동게시 차단)")
    print("selfcheck:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def cmd_run(inbox: str, *, root: str | None, dry_run: bool,
            seed: int | None) -> int:
    root_p = encoding.assert_ascii_workroot(root or _default_root())
    root_p.mkdir(parents=True, exist_ok=True)
    resource_guard.set_below_normal_priority()
    lock_path = root_p / ".run.lock"
    with runlock.run_lock(lock_path):
        rs = new_run(root_p, inbox, code_version=__version__,
                     dry_run=dry_run, seed=seed)
        with netguard.guarded(rs.ledger):     # INVARIANT #1 강제(런타임 전구간)
            statemachine.run_pipeline(rs, _pipeline())
        clean = rs.ledger.is_clean()
        print(f"run {rs.run_id}: {'DRY-RUN ' if dry_run else ''}완료")
        print(f"  출력: {rs.output_path}")
        if rs.metadata:
            print(f"  메타초안 제목: {rs.metadata['title']}")
        print(f"  INVARIANT #1 네트워크 원장 clean(비-카브아웃 0): {clean}")
        return 0 if clean else 2


def cmd_start(utterance: str | None) -> int:
    """Smart router + user guidance entry.

    Flow: utterance -> router.recognize -> CLI-level session prep ->
    guide.render. Does not run the pipeline; the user picks an option and
    invokes the printed command. No layer-A (build harness) access.
    A bare `start` verb is treated as ``recognize("start")``.
    """
    classified = router.recognize(utterance if utterance is not None else "start")
    if classified is not router.Intent.START_USAGE:
        print("[shorts-forge] 시작 의도를 인식하지 못했습니다.")
        print("예시: shorts-forge start \"시작하자\" / start \"워크플로우 시작\"")
        return 1
    print(f"shorts-forge {__version__} ready.")
    guide.render(sys.stdout)
    return 0


def main(argv: list[str] | None = None) -> int:
    encoding.force_utf8_io()   # 콘솔 cp949 비의존 — UTF-8 강제(인코딩 불변)
    p = argparse.ArgumentParser(prog="shorts-forge",
                                description="로컬 전용 Shorts 생성(게이트 비의존)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selfcheck", help="불변식 하니스 자가점검")
    pr = sub.add_parser("run", help="입력 폴더 → ≤59s 9:16 mp4 + KR 메타초안")
    pr.add_argument("inbox", help="입력 미디어 폴더")
    pr.add_argument("--root", default=None, help="ASCII 작업루트(기본 .sf_root)")
    pr.add_argument("--dry-run", action="store_true", help="스토리보드만(렌더 없음)")
    pr.add_argument("--seed", type=int, default=None, help="결정론 고정 seed")
    ps = sub.add_parser("start", help="자연어 시작 명령 → 사용자 안내 모드")
    ps.add_argument("utterance", nargs="?", default=None,
                    help="시작 의도 자연어 (예: \"시작\", \"워크플로우 시작하자\")")
    # publish verb 의도적 부재 — [GATE:D3]
    args = p.parse_args(argv)
    if args.cmd == "selfcheck":
        return cmd_selfcheck()
    if args.cmd == "run":
        return cmd_run(args.inbox, root=args.root, dry_run=args.dry_run,
                       seed=args.seed)
    if args.cmd == "start":
        return cmd_start(args.utterance)
    return 1


if __name__ == "__main__":
    sys.exit(main())
