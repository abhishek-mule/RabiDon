from __future__ import annotations

from dataclasses import dataclass

from rabidon.tts.segments import Segment
from rabidon.utils.hashing import sha256_json


@dataclass(frozen=True)
class ScenePlan:
    status: str  # provisional|resolved
    plan: dict

    @property
    def plan_hash(self) -> str:
        return sha256_json(self.plan)


def build_provisional(script_revision_id: int, lines: list[str]) -> ScenePlan:
    scenes = []
    for i, line in enumerate([l for l in lines if l.strip()]):
        scenes.append({
            "id": f"s{i+1}",
            "narration_text": line.strip(),
            "narration_segment_ids": [],
            "timeline_start_ms": None,
            "timeline_end_ms": None,
            "estimated_duration_ms": max(1200, min(9000, len(line) * 55)),
            "on_screen_text": line.strip()[:80],
            "layers": [{"kind": "solid", "color": "#111827", "motion": "slow_zoom"}],
            "transition_out": "cut",
        })
    return ScenePlan("provisional", {
        "schema_version": 1, "script_revision_id": script_revision_id,
        "status": "provisional", "scenes": scenes,
    })


def resolve_with_segments(provisional: ScenePlan, segments: list[Segment],
                          timing_revision_id: str) -> ScenePlan:
    ok = [s for s in segments if s.status == "ok"]
    scenes = []
    for i, seg in enumerate(ok):
        scenes.append({
            "id": f"s{i+1}",
            "narration_text": seg.text,
            "narration_segment_ids": [seg.index],
            "timeline_start_ms": seg.start_ms,
            "timeline_end_ms": seg.end_ms,
            "on_screen_text": seg.text.strip()[:80],
            "layers": [{"kind": "solid", "color": "#111827", "motion": "slow_zoom"}],
            "transition_out": "cut",
        })
    return ScenePlan("resolved", {
        "schema_version": 1,
        "script_revision_id": provisional.plan.get("script_revision_id"),
        "status": "resolved",
        "timing_revision_id": timing_revision_id,
        "scenes": scenes,
    })
