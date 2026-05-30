from __future__ import annotations

import unittest

from app.story_boundary_service import StoryBoundaryService


class StoryBoundaryServiceTests(unittest.TestCase):
    def test_parse_chapter_range_no_meeting_rule(self) -> None:
        service = StoryBoundaryService()
        rules = service.parse_rules("第1到10章男女主不要相遇，先分别讲清楚他们相遇之前的故事。第11章才第一次正式见面。")

        forbid_rule = next(
            item for item in rules if item["rule_type"] == "forbid_event" and item["predicate"] == "direct_meeting"
        )
        self.assertEqual(forbid_rule["scope_type"], "chapter_range")
        self.assertEqual(forbid_rule["start_chapter_no"], 1)
        self.assertEqual(forbid_rule["end_chapter_no"], 10)

        allow_rule = next(
            item for item in rules if item["rule_type"] == "allow_event" and item["predicate"] == "direct_meeting"
        )
        self.assertEqual(allow_rule["scope_type"], "chapter")
        self.assertEqual(allow_rule["start_chapter_no"], 11)

    def test_active_rules_for_chapter(self) -> None:
        service = StoryBoundaryService()
        rules = service.parse_rules("第1到10章男女主不要相遇。第11章才第一次正式见面。")
        active_for_ch4 = service.active_rules_for_chapter(rules, 4)
        active_for_ch11 = service.active_rules_for_chapter(rules, 11)
        self.assertTrue(any(item["rule_type"] == "forbid_event" for item in active_for_ch4))
        self.assertTrue(any(item["rule_type"] == "allow_event" for item in active_for_ch11))


if __name__ == "__main__":
    unittest.main()
