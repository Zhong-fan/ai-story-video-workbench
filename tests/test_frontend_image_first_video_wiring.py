from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendImageFirstVideoWiringTests(unittest.TestCase):
    def test_image_first_payload_and_ui_are_wired(self) -> None:
        types_source = (ROOT / "frontend" / "src" / "types.ts").read_text(encoding="utf-8")
        store_source = (ROOT / "frontend" / "src" / "stores" / "workbench.ts").read_text(encoding="utf-8")
        stage_source = (ROOT / "frontend" / "src" / "components" / "workspace" / "VideoStagePage.vue").read_text(encoding="utf-8")
        create_source = (ROOT / "frontend" / "src" / "components" / "workspace" / "VideoCreatePage.vue").read_text(encoding="utf-8")

        self.assertIn('source_mode?: "novel_chapters" | "image_first_reference" | "existing_images"', types_source)
        self.assertIn("reference_video_brief", types_source)
        self.assertIn("createImageFirstStoryboard", store_source)
        self.assertIn("image_first_reference", stage_source)
        self.assertIn("先生成关键图", stage_source)
        self.assertIn("shot_first_frame", create_source)


if __name__ == "__main__":
    unittest.main()
