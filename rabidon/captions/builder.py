from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rabidon.tts.segments import Segment


@dataclass(frozen=True)
class CaptionIssue:
    code: str
    detail: str


def _ms_to_srt(ms: int) -> str:
    ms = max(0, ms)
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1000
    ms %= 1000
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _ms_to_ass(ms: int) -> str:
    cs = max(0, ms) // 10
    h = cs // 360000
    cs %= 360000
    m = cs // 6000
    cs %= 6000
    s = cs // 100
    cs %= 100
    return f"{h}:{m:02}:{s:02}.{cs:02}"


def validate_segments(segments: list[Segment]) -> list[CaptionIssue]:
    issues: list[CaptionIssue] = []
    prev_end = -1
    for s in segments:
        if not s.text.strip():
            issues.append(CaptionIssue("empty_text", f"segment {s.index}"))
        if s.status != "ok":
            issues.append(CaptionIssue("segment_status", f"{s.index}:{s.status}"))
        if s.end_ms <= s.start_ms:
            issues.append(CaptionIssue("invalid_timing", f"segment {s.index}"))
        if s.start_ms < prev_end:
            issues.append(CaptionIssue("overlap", f"segment {s.index} starts before previous ends"))
        prev_end = s.end_ms
    return issues


def write_srt(segments: list[Segment], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    n = 0
    for s in segments:
        if s.status != "ok" or not s.text.strip():
            continue
        n += 1
        lines.append(str(n))
        lines.append(f"{_ms_to_srt(s.start_ms)} --> {_ms_to_srt(s.end_ms)}")
        lines.append(s.text.strip())
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_ass(segments: list[Segment], path: Path, *, play_res_x: int = 1080,
              play_res_y: int = 1920, font_name: str = "Noto Sans Devanagari") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,{font_name},54,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,3,0,2,90,90,160,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    events: list[str] = []
    for s in segments:
        if s.status != "ok" or not s.text.strip():
            continue
        text = s.text.strip().replace("\n", r"\N")
        events.append(f"Dialogue: 0,{_ms_to_ass(s.start_ms)},{_ms_to_ass(s.end_ms)},Default,,0,0,0,,{text}")
    path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
