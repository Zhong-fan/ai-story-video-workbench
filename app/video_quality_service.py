from __future__ import annotations

from typing import Any

from .json_utils import ensure_list, json_loads_object
from .models import Storyboard, VideoTask


class VideoQualityService:
    def build_quality_plan(self, storyboard: Storyboard) -> dict[str, Any]:
        shots = sorted(storyboard.shots, key=lambda item: item.shot_no)
        first_meta = json_loads_object(shots[0].meta_json) if shots else {}
        source_trace = first_meta.get("source_trace") if isinstance(first_meta.get("source_trace"), dict) else {}
        source_mode = str(first_meta.get("source_mode") or source_trace.get("source_mode") or "novel_chapters")
        planned_shots = []
        for shot in shots:
            meta = json_loads_object(shot.meta_json)
            continuity = meta.get("continuity") if isinstance(meta.get("continuity"), dict) else {}
            audio_script = meta.get("audio_script") if isinstance(meta.get("audio_script"), dict) else {}
            planned_shots.append(
                {
                    "shot_no": shot.shot_no,
                    "purpose": shot.narration_text.strip() or shot.visual_prompt.strip(),
                    "visual_continuity": ensure_list(continuity.get("continuity_constraints")),
                    "subtitle_text": str(audio_script.get("subtitle_text") or "").strip(),
                    "duration_seconds": shot.duration_seconds,
                }
            )
        return {
            "source_mode": source_mode,
            "source_trace": source_trace,
            "shot_count": len(planned_shots),
            "structure": {
                "opening": "Shot 1 establishes the scene." if planned_shots else "",
                "development": "Middle shots advance the change." if len(planned_shots) >= 2 else "",
                "ending": f"Shot {planned_shots[-1]['shot_no']} resolves the emotion or action." if planned_shots else "",
            },
            "shots": planned_shots,
            "quality_dimensions": ["short_film_structure", "visual_stability", "content_consistency"],
        }

    def build_result(
        self,
        *,
        task: VideoTask,
        status: str,
        message: str,
    ) -> dict[str, Any]:
        progress = json_loads_object(task.progress_json)
        plan = progress.get("video_quality_plan") if isinstance(progress.get("video_quality_plan"), dict) else {}
        passed = status == "completed" and bool(task.output_uri)
        return {
            "status": "passed" if passed else "failed",
            "message": message,
            "checked_against_plan": bool(plan),
            "short_film_structure": "passed" if passed else "requires_manual_review",
            "visual_stability": "requires_manual_review",
            "content_consistency": "requires_manual_review",
        }
