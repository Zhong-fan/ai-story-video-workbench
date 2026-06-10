from __future__ import annotations

import unittest

from app.video_quality_service import build_review_findings


class VideoReviewFindingsTest(unittest.TestCase):
    def test_continuity_failure_routes_to_shot_level(self) -> None:
        findings = build_review_findings(
            shot_results=[
                {
                    "shot_no": 3,
                    "continuity_failed": True,
                    "pacing_failed": False,
                    "local_defect": False,
                }
            ]
        )

        self.assertEqual(findings[0]["severity"], "blocking")
        self.assertEqual(findings[0]["recommended_rework_level"], "shot")

    def test_pacing_and_local_defect_use_expected_rework_levels(self) -> None:
        findings = build_review_findings(
            shot_results=[
                {
                    "shot_no": 2,
                    "continuity_failed": False,
                    "pacing_failed": True,
                    "local_defect": True,
                }
            ]
        )

        self.assertEqual(findings[0]["category"], "pacing")
        self.assertEqual(findings[0]["recommended_rework_level"], "storyboard")
        self.assertEqual(findings[1]["category"], "local_defect")
        self.assertEqual(findings[1]["recommended_rework_level"], "local_fix")


if __name__ == "__main__":
    unittest.main()
