from __future__ import annotations

import unittest

from app.story_boundary_service import StoryBoundaryService
from app.violation_check_service import ViolationCheckService


class ViolationCheckServiceTests(unittest.TestCase):
    def test_detects_direct_meeting_violation_in_outline(self) -> None:
        rule_service = StoryBoundaryService()
        violation_service = ViolationCheckService()
        rules = rule_service.parse_rules("第1到10章男女主不要相遇。")
        active_rules = rule_service.active_rules_for_chapter(rules, 4)
        outline = {
            "chapter_no": 4,
            "chapter_goal": "两人在便利店门口第一次正式相遇，并开始交谈。",
            "must_happen": ["男女主见面"],
            "must_not_happen": [],
        }
        violations = violation_service.check_outline(outline, active_rules)
        self.assertTrue(violations)

    def test_ignores_negative_statement(self) -> None:
        rule_service = StoryBoundaryService()
        violation_service = ViolationCheckService()
        rules = rule_service.parse_rules("第1到10章男女主不要相遇。")
        active_rules = rule_service.active_rules_for_chapter(rules, 4)
        content = "两人仍然没有相遇，只是在各自的生活里继续前进。"
        violations = violation_service.check_content(content, active_rules)
        self.assertFalse(violations)

    def test_ignores_forbidden_event_list_in_outline(self) -> None:
        rule_service = StoryBoundaryService()
        violation_service = ViolationCheckService()
        rules = rule_service.parse_rules("第1到10章男女主不要相遇。")
        active_rules = rule_service.active_rules_for_chapter(rules, 4)
        outline = {
            "chapter_no": 4,
            "chapter_goal": "分别推进两条生活线。",
            "must_happen": ["男主完成转学准备", "女主处理家庭压力"],
            "must_not_happen": ["第 1-10 章：禁止男女主直接相遇"],
        }
        violations = violation_service.check_outline(outline, active_rules)
        self.assertFalse(violations)


if __name__ == "__main__":
    unittest.main()
