"""User guidance mode — first screen after start intent is recognized.

Tone: no theory; concrete (choice -> result -> command) mapping only.

Structural rule (ANCHOR ②): the option catalog is a frozen module-level
tuple of frozen dataclasses; it cannot be extended at runtime, no branch
inserts items, and nothing here addresses the build harness. The fixed
catalog matches exactly the product CLI verbs (run / run --dry-run), so
the layer-A rebuild path cannot appear in any code path.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TextIO

TRACE = {
    "prd": "§10 OPS-1, §1.2",
    "workflow": "§1",
    "ax": ["AX-ONBOARD"],
    "f": [],
    "gate": [],
}


@dataclass(frozen=True)
class GuideOption:
    label: str
    result: str
    command: str


OPTIONS: tuple[GuideOption, ...] = (
    GuideOption(
        label="풀 렌더",
        result="입력 폴더의 사진·영상을 ≤59초 9:16 mp4 한 개와 한국어 메타초안으로 생성한다.",
        command="shorts-forge run <입력_폴더>",
    ),
    GuideOption(
        label="스토리보드 미리보기 (렌더 없음)",
        result="실제 렌더 없이 어떤 클립 순서·길이로 만들어질지 텍스트 스토리보드만 출력한다.",
        command="shorts-forge run <입력_폴더> --dry-run",
    ),
)


def render(stream: TextIO) -> None:
    """Write the guidance screen to ``stream``. No interactive input."""
    stream.write("아래에서 한 가지를 골라 해당 명령을 실행하세요:\n\n")
    for i, opt in enumerate(OPTIONS, start=1):
        stream.write(f"  {i}) {opt.label}\n")
        stream.write(f"     무엇이 일어나는가: {opt.result}\n")
        stream.write(f"     명령: {opt.command}\n\n")
    stream.write("선택지에 없는 항목은 본 진입점에서 노출되지 않습니다.\n")
