from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendImageFirstVideoWiringTests(unittest.TestCase):
    def test_image_first_payload_and_ui_are_wired(self) -> None:
        types_source = (ROOT / "frontend" / "src" / "types.ts").read_text(encoding="utf-8")
        store_source = (ROOT / "frontend" / "src" / "stores" / "workbench.ts").read_text(encoding="utf-8")
        pipeline_source = (ROOT / "frontend" / "src" / "components" / "workspace" / "LongformPipelinePanel.vue").read_text(encoding="utf-8")

        self.assertIn('source_mode?: "novel_chapters" | "image_first_reference" | "existing_images"', types_source)
        self.assertIn("reference_video_brief", types_source)
        self.assertIn("createImageFirstStoryboard", store_source)
        self.assertIn("image_first_reference", pipeline_source)
        self.assertIn("先生成关键图", pipeline_source)
        self.assertIn("shot_first_frame", pipeline_source)


if __name__ == "__main__":
    unittest.main()
