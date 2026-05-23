"""내부 EDL 스키마 + C-* 결정론 검증.

추적: PRD §8 C-OUT/C-LEN/C-THUMB·§7 NEVER·§9 R-CAP2 · workflow.md §4 [DESIGN] · [F §3.1]
[DESIGN] D-FG: EDL→필터그래프는 결정론 매핑(s4). 판단 노드는 EDL *제안*만 반환,
결정론 코드(본 모듈)가 C-* 검증 후에만 미디어 연산 호출(R-CAP2).
"""
from __future__ import annotations

import json
from pathlib import Path

from ..invariants import encoding

TRACE = {
    "prd": "§8 C-OUT",
    "workflow": "§4",
    "ax": ["AX-MEDIA", "AX-CRAFT"],
    "f": ["§3.1"],
    "gate": [],
}

# C-OUT/C-LEN 하드 제약(PRD §4) — 변경 시 성공 정의가 바뀜
TARGET_W, TARGET_H, TARGET_FPS, MAX_SECONDS = 1080, 1920, 30, 59
# PRD §7 NEVER / G6: 금지 전환(별 와이프/플래시줌+SFX/글리치 와이프)
FORBIDDEN_TRANSITIONS = frozenset({"star_wipe", "flash_zoom", "glitch_wipe"})
ALLOWED_TRANSITIONS = frozenset({"cut"})  # 증분1=클린 컷만


class EDLInvalid(ValueError):
    """EDL 이 C-* 하드 제약 위반(미디어 연산 호출 전 차단 — R-CAP2)."""


def new_edl(run_id: str, seed: int) -> dict:
    return {
        "edl_version": "1",
        "run_id": run_id,
        "seed": seed,
        "target": {"w": TARGET_W, "h": TARGET_H, "fps": TARGET_FPS,
                   "max_seconds": MAX_SECONDS},
        "spine_kind": "chronological",   # D5 잠정: 연대순만(에너지아크 차단)
        "hero_ref": None,                # C-THUMB: 첫 프레임=가용 최강
        "timeline": [],                  # 정렬 클립/정지 엔트리
        "audio": {"track_ref": None,     # [GATE:D2] 라이브러리 콘텐츠 미번들 → null
                  "loudness": {"I": -14, "TP": -1}},
        "provenance": {"stage_versions": {}, "cache_hits": []},
    }


def add_entry(edl: dict, *, source_ref: str, kind: str, t_in: float, t_out: float,
              transform_916: dict, motion: dict | None = None,
              transition_in: str = "cut", caption_tokens: list | None = None,
              beat_offset_ms: int = 0) -> None:
    edl["timeline"].append({
        "idx": len(edl["timeline"]),
        "source_ref": source_ref,
        "kind": kind,
        "in": round(float(t_in), 3),
        "out": round(float(t_out), 3),
        "transform_916": transform_916,
        "motion": motion or {"type": "none"},
        "transition_in": transition_in,
        "caption_tokens": caption_tokens or [],
        "beat_offset_ms": int(beat_offset_ms),
    })


def total_seconds(edl: dict) -> float:
    return round(sum(e["out"] - e["in"] for e in edl["timeline"]), 3)


def validate(edl: dict) -> None:
    """C-OUT/C-LEN/C-THUMB/G6 결정론 검증. 위반 시 EDLInvalid(미디어 연산 차단)."""
    t = edl.get("target", {})
    if (t.get("w"), t.get("h"), t.get("fps")) != (TARGET_W, TARGET_H, TARGET_FPS):
        raise EDLInvalid(f"C-OUT 지오메트리 위반: {t}")
    tl = edl.get("timeline", [])
    if not tl:
        raise EDLInvalid("빈 타임라인 — SM-1 바닥은 최소 1 엔트리 보장해야 함")
    dur = total_seconds(edl)
    if dur <= 0 or dur > MAX_SECONDS:
        raise EDLInvalid(f"C-LEN 위반(≤{MAX_SECONDS}s): {dur}s")
    for e in tl:
        if e["transition_in"] in FORBIDDEN_TRANSITIONS:
            raise EDLInvalid(f"G6 금지 전환: {e['transition_in']}")
        if e["transition_in"] not in ALLOWED_TRANSITIONS:
            raise EDLInvalid(f"증분1 미허용 전환: {e['transition_in']}")
        if e["out"] <= e["in"]:
            raise EDLInvalid(f"엔트리 시간 역전: idx={e['idx']}")
    if edl.get("hero_ref") is None:
        raise EDLInvalid("C-THUMB: hero_ref(첫 프레임=가용 최강) 미설정")


def dump(edl: dict, path: str | Path) -> Path:
    """EDL 직렬화 — UTF-8·ensure_ascii=False(한글 보존)·결정론(sort_keys)."""
    validate(edl)
    p = encoding.nfc_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(edl, **encoding.json_dump_kwargs()), encoding="utf-8")
    return p
