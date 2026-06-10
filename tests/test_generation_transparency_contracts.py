from __future__ import annotations

import unittest

from app.api_support_longform import build_storyboard_state_payload


class GenerationTransparencyContractsTest(unittest.TestCase):
    def test_storyboard_payload_exposes_phase1_review_contract(self) -> None:
        payload = build_storyboard_state_payload(
            storyboard={
                "id": 1,
                "progress": {},
                "shots": [],
                "events": [],
            },
            media_assets=[],
            video_tasks=[],
        )

        self.assertIn("preflight_summary", payload["progress"])
        self.assertIn("generation_trace", payload["progress"])
        self.assertIn("review_findings", payload["progress"])
        self.assertIn("rework_hints", payload["progress"])


if __name__ == "__main__":
    unittest.main()
