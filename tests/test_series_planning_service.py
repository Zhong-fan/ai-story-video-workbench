from __future__ import annotations

import unittest
import json
from types import SimpleNamespace

from app.reference_policy_service import ReferencePolicyService
from app.series_planning_service import SeriesPlanningService
from app.story_boundary_service import StoryBoundaryService
from app.violation_check_service import ViolationCheckService


class FakeLLM:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def generate(self, **_: object) -> SimpleNamespace:
        return SimpleNamespace(text=json.dumps(self.payload, ensure_ascii=False))


class SeriesPlanningServiceTests(unittest.TestCase):
    def test_attaches_chapter_constraint_snapshots(self) -> None:
        service = object.__new__(SeriesPlanningService)
        service.story_boundary_service = StoryBoundaryService()
        rules = service.story_boundary_service.parse_rules("第1到10章男女主不要相遇。第11章才第一次正式见面。")
        payload = {
            "series": {"title": "测试", "target_chapter_count": 12},
            "arcs": [{"arc_no": 1, "start_chapter_no": 1, "end_chapter_no": 12, "title": "主线"}],
            "chapters": [
                {
                    "chapter_no": chapter_no,
                    "title": f"第 {chapter_no} 章",
                    "chapter_goal": "分别推进各自生活线。",
                    "must_happen": [],
                    "must_not_happen": [],
                }
                for chapter_no in range(1, 13)
            ],
        }

        service._attach_constraint_snapshots(
            payload,
            story_boundary_rules=rules,
            reference_facts=[
                {
                    "fact_type": "relationship_state",
                    "payload": {"summary": "改写起点前男女主尚未在本项目中重逢"},
                    "status": "active",
                }
            ],
            authorized_overrides=["允许第 11 章安排第一次正式见面。"],
        )

        chapter_4 = payload["chapters"][3]
        chapter_11 = payload["chapters"][10]
        self.assertIn("constraint_snapshot", chapter_4)
        self.assertTrue(any(item["predicate"] == "direct_meeting" for item in chapter_4["constraint_snapshot"]["hard_constraints"]))
        self.assertTrue(any("不要相遇" in item for item in chapter_4["must_not_happen"]))
        self.assertTrue(any(item["rule_type"] == "allow_event" for item in chapter_11["constraint_snapshot"]["hard_constraints"]))
        self.assertEqual(chapter_4["constraint_snapshot"]["reference_facts"][0]["fact_type"], "relationship_state")
        self.assertEqual(chapter_4["constraint_snapshot"]["authorized_overrides"], ["允许第 11 章安排第一次正式见面。"])

    def test_generate_plan_adds_snapshots_to_12_chapter_output(self) -> None:
        service = object.__new__(SeriesPlanningService)
        service.settings = SimpleNamespace(writer_model="test-model")
        service.reference_policy_service = ReferencePolicyService()
        service.story_boundary_service = StoryBoundaryService()
        service.violation_check_service = ViolationCheckService()
        service.llm = FakeLLM(
            {
                "series": {"title": "测试", "target_chapter_count": 12},
                "arcs": [{"arc_no": 1, "start_chapter_no": 1, "end_chapter_no": 12, "title": "主线"}],
                "chapters": [
                    {
                        "chapter_no": chapter_no,
                        "title": f"第 {chapter_no} 章",
                        "chapter_goal": "分别推进各自生活线。",
                        "must_happen": [],
                        "must_not_happen": [],
                    }
                    for chapter_no in range(1, 13)
                ],
            }
        )
        project = SimpleNamespace(
            title="测试项目",
            genre="现代都市",
            reference_work="",
            reference_work_synopsis="",
            reference_work_style_traits=[],
            reference_work_world_traits=[],
            reference_work_narrative_constraints=[],
            world_brief="",
            writing_rules="",
            memories=[],
            character_cards=[],
            source_documents=[],
        )
        rules = service.story_boundary_service.parse_rules("第1到10章男女主不要相遇。第11章才第一次正式见面。")

        payload = service.generate_plan(
            project=project,
            target_chapter_count=12,
            user_brief="",
            context_pack_inputs={"story_boundary_rules": rules},
        )

        early_chapters = payload["chapters"][:10]
        self.assertEqual(len(payload["chapters"]), 12)
        self.assertTrue(
            all(any(item["predicate"] == "direct_meeting" for item in chapter["constraint_snapshot"]["forbidden_events"]) for chapter in early_chapters)
        )
        self.assertTrue(all(any("不要相遇" in item for item in chapter["must_not_happen"]) for chapter in early_chapters))

    def test_validate_story_boundaries_rejects_12_chapter_plan_with_early_meeting(self) -> None:
        service = object.__new__(SeriesPlanningService)
        service.story_boundary_service = StoryBoundaryService()

        service.violation_check_service = ViolationCheckService()
        rules = service.story_boundary_service.parse_rules("第1到10章男女主不要相遇。第11章才第一次正式见面。")
        payload = {
            "series": {"title": "测试", "target_chapter_count": 12},
            "arcs": [{"arc_no": 1, "start_chapter_no": 1, "end_chapter_no": 12, "title": "主线"}],
            "chapters": [
                {
                    "chapter_no": chapter_no,
                    "title": f"第 {chapter_no} 章",
                    "chapter_goal": "分别推进各自生活线。",
                    "must_happen": [],
                    "must_not_happen": [],
                }
                for chapter_no in range(1, 13)
            ],
        }
        payload["chapters"][3]["chapter_goal"] = "男女主在便利店门口第一次正式见面。"

        with self.assertRaisesRegex(RuntimeError, "第 4 章概要违反故事边界"):
            service._validate_story_boundaries(payload, rules)


if __name__ == "__main__":
    unittest.main()
