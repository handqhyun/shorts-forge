"""S1 NORMALIZE — 결정론 정규화(분석 전 필수). 완전 구현.

추적: PRD §4 C-INPUT/C-SPINE/C-I18N·§3.2 · workflow.md §2 S1 · 【AX-INPUT】【AX-I18N】 [F §3.10]
probe-first allow-list → (회전 1회 베이크·sRGB 작업표현) → NFC 경로 →
오염 필터(0바이트/디코드불가/파노/근중복 pHash) 사전 제거 → 5단계 신뢰도 태깅
→ 파일별 실패 격리(1 손상이 배치 중단 금지, C-INPUT). [GATE:D9] 디코더 *조달*
결정 차단 — 환경 probe된 가용 디코더만 사용(우리는 조달하지 않음).
"""
from __future__ import annotations

import json

from ..invariants import encoding
from ..media import image_ops, probe as probemod
from ..spine import cache as cachemod
from ..spine.contracts import StageContract, StageResult
from ..spine.gates import gate_blocked
from ..spine.runstate import Asset, RunState

TRACE = {
    "prd": "§4 C-INPUT",
    "workflow": "§2 S1",
    "ax": ["AX-INPUT", "AX-I18N"],
    "f": ["§3.10"],
    "gate": ["D9"],
}

# 파노 종횡비 임계(결정론 오염 프록시). 스크린샷 분류기는 [F §3.10] 미해결 —
# 실파일 튜닝 금지(② 경계), 보수적 파일명 토큰 프록시만(잠정·명시).
_PANO_RATIO_HI, _PANO_RATIO_LO = 2.5, 0.4
_SCREENSHOT_NAME_TOKENS = ("screenshot", "스크린샷", "kakaotalk", "screen_shot")
_NEAR_DUP_HAMMING = 6


@gate_blocked("D9")
def procure_decoder():
    """[GATE:D9] HEVC 디코더 번들 vs OS-제공 = 법적 미해결. 조달 결정 금지.

    S1 은 본 함수를 호출하지 않는다 — 환경 probe된 가용 디코더만 사용.
    """


def _ascii_stem(stem: str) -> str:
    """ASCII 보장 결정론 work 파일 stem. 한글/NFD 원본명이 ASCII 작업루트로
    새면 인코딩 불변(validate_output)을 깨므로, 비-ASCII stem 은 안정 해시로 치환."""
    if encoding.is_ascii(stem):
        return stem
    import hashlib
    return "u" + hashlib.sha256(stem.encode("utf-8")).hexdigest()[:12]


class S1Normalize(StageContract):
    stage_id = "S1"
    TRACE = TRACE

    def run(self, rs: RunState) -> StageResult:
        inbox = rs.inbox
        if not inbox.exists():
            return StageResult(False, self.stage_id, detail=f"inbox 부재: {inbox}")

        files = sorted(
            (p for p in inbox.iterdir() if p.is_file()),
            key=lambda p: encoding.nfc(p.name),  # 결정론 순서(NFC)
        )
        kept_phashes: list[int] = []
        isolated: list[str] = []

        for f in files:
            # Read from the real on-disk entry (its bytes may be NFD); record
            # the NFC form as canonical identity. nfc_path(f) can name a path
            # that does not exist on an NFD-storing filesystem, which previously
            # made probe() report "absent" and silently drop NFD Korean names
            # (C2, the [GATE:D11] hazard realised in code).
            src = encoding.nfc_path(f)
            info = probemod.probe(f)

            # --- 오염/디코드불가 사전 제거(파일별 격리, 배치 비중단) ---
            reason = self._contamination_reason(src, info)
            if reason:
                self._record_input(rs, src, info, isolated=True, reason=reason)
                isolated.append(f"{src.name}: {reason}")
                continue

            if info["kind"] == "still":
                work = rs.stage_dir("S1") / f"norm_{_ascii_stem(src.stem)}.png"
                try:
                    image_ops.bake_rotation_and_normalize(f, work)
                    ph = image_ops.phash(work)
                except Exception as exc:  # noqa: BLE001 — 격리(비중단)
                    r = f"정규화 실패: {type(exc).__name__}"
                    self._record_input(rs, src, info, isolated=True, reason=r)
                    isolated.append(f"{src.name}: {r}")
                    continue
                if any(image_ops.is_near_duplicate(ph, k, _NEAR_DUP_HAMMING)
                       for k in kept_phashes):
                    r = "근중복(pHash) — 인접 노출 금지"
                    self._record_input(rs, src, info, isolated=True, reason=r)
                    isolated.append(f"{src.name}: {r}")
                    continue
                kept_phashes.append(ph)
                ch = cachemod.file_hash(work)
                tier, ts = probemod.confidence_tier(src, info["exif_dt"])
                rs.assets.append(Asset(
                    src_path_nfc=str(src), content_hash=ch, kind="still",
                    confidence_tier=tier, timestamp=ts,
                    orientation=1,  # 회전 베이크 완료 → 정규화
                    quality={"w": info["width"], "h": info["height"]},
                    work_path=str(work),
                ))
                self._record_input(rs, src, info, isolated=False, reason="",
                                   content_hash=ch, tier=tier)
            else:  # clip — 증분1: 메타만(트랜스코드는 Inc4 S6)
                ch = cachemod.file_hash(f)
                tier, ts = probemod.confidence_tier(src, info["exif_dt"])
                rs.assets.append(Asset(
                    src_path_nfc=str(src), content_hash=ch, kind="clip",
                    confidence_tier=tier, timestamp=ts,
                    quality={"w": info["width"], "h": info["height"]},
                    work_path=str(f),   # 실 디스크 경로(NFD 가능) — 다운스트림 read
                ))
                self._record_input(rs, src, info, isolated=False, reason="",
                                   content_hash=ch, tier=tier)

        # 신뢰도-태그 연대순 안정 정렬(C-SPINE: 단조 가정 금지·best-effort)
        rs.assets.sort(key=lambda a: (
            a.timestamp if a.timestamp is not None else float("inf"),
            a.confidence_tier, a.content_hash,
        ))

        manifest = rs.stage_dir("S1") / "normalized.json"
        manifest.write_text(json.dumps({
            "assets": [vars(a) for a in rs.assets],
            "isolated": isolated,
        }, **encoding.json_dump_kwargs()), encoding="utf-8")

        return StageResult(
            ok=True, stage_id=self.stage_id, artifact_ref=str(manifest),
            isolated_inputs=isolated,
            detail=f"정규화 {len(rs.assets)}건, 격리 {len(isolated)}건",
        )

    def validate_output(self, rs: RunState, result: StageResult) -> None:
        super().validate_output(rs, result)
        # 회전은 베이크 완료(orientation=1), NFC 경로 보장
        for a in rs.assets:
            if a.kind == "still" and a.orientation != 1:
                raise RuntimeError(f"회전 미베이크: {a.src_path_nfc}")
            if not encoding.is_ascii(str(a.work_path)) and a.kind == "still":
                # 작업표현은 ASCII 작업루트 하위(인코딩 불변)
                raise RuntimeError(f"작업표현 비-ASCII 경로: {a.work_path}")

    # --- helpers ---
    def _contamination_reason(self, src, info: dict) -> str:
        if not info["decodable"]:
            return info.get("reason") or "디코드 불가"
        w, h = info.get("width", 0), info.get("height", 0)
        if info["kind"] == "still" and w and h:
            ratio = w / h
            if ratio >= _PANO_RATIO_HI or ratio <= _PANO_RATIO_LO:
                return f"파노라마류 종횡비({w}x{h})"
        low = src.name.lower()
        if any(tok in low for tok in _SCREENSHOT_NAME_TOKENS):
            return "스크린샷류(파일명 프록시·잠정 [F §3.10])"
        return ""

    def _record_input(self, rs: RunState, src, info: dict, *, isolated: bool,
                      reason: str, content_hash: str | None = None,
                      tier: int | None = None) -> None:
        rs.conn.execute(
            "INSERT OR REPLACE INTO inputs "
            "(run_id, src_path_nfc, content_hash, kind, confidence_tier, "
            " orientation, isolated, isolate_reason) VALUES (?,?,?,?,?,?,?,?)",
            (rs.run_id, str(src), content_hash or f"raw:{src.name}",
             info.get("kind"), tier, info.get("orientation", 1),
             1 if isolated else 0, reason),
        )
        rs.conn.commit()
