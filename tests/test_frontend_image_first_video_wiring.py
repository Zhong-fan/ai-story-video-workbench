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
        self.assertIn('"user_brief"', types_source)
        self.assertIn("createBriefStoryboard", store_source)
        self.assertIn('source_mode: "user_brief"', store_source)
        self.assertIn("image_first_reference", pipeline_source)
        self.assertIn('value="existing_images"', pipeline_source)
        self.assertIn("先生成关键图", pipeline_source)
        self.assertIn("shot_first_frame", pipeline_source)

    def test_continuity_tail_frame_ui_is_wired(self) -> None:
        pipeline_source = (ROOT / "frontend" / "src" / "components" / "workspace" / "LongformPipelinePanel.vue").read_text(encoding="utf-8")

        self.assertIn("shot_last_frame", pipeline_source)
        self.assertIn("previous_last_frame", pipeline_source)
        self.assertIn("继承上一镜头尾帧", pipeline_source)
        self.assertIn("视频门禁", pipeline_source)

    def test_generation_transparency_panel_prioritizes_render_prompt_display(self) -> None:
        panel_source = (ROOT / "frontend" / "src" / "components" / "workspace" / "GenerationTransparencyPanel.vue").read_text(encoding="utf-8")

        self.assertIn("最终执行 Prompt", panel_source)
        self.assertIn("renderPromptSources", panel_source)
        self.assertIn("渲染 Prompt 来源", panel_source)

    def test_render_prompt_source_focus_is_wired(self) -> None:
        panel_source = (ROOT / "frontend" / "src" / "components" / "workspace" / "GenerationTransparencyPanel.vue").read_text(encoding="utf-8")
        pipeline_source = (ROOT / "frontend" / "src" / "components" / "workspace" / "LongformPipelinePanel.vue").read_text(encoding="utf-8")

        self.assertIn("focus-render-source", panel_source)
        self.assertIn("@focus-render-source", pipeline_source)
        self.assertIn("focusRenderPromptSource", pipeline_source)

    def test_preflight_issue_focus_is_wired(self) -> None:
        panel_source = (ROOT / "frontend" / "src" / "components" / "workspace" / "VideoPreflightReviewPanel.vue").read_text(encoding="utf-8")
        pipeline_source = (ROOT / "frontend" / "src" / "components" / "workspace" / "LongformPipelinePanel.vue").read_text(encoding="utf-8")

        self.assertIn("focus-preflight-issue", panel_source)
        self.assertIn("@focus-preflight-issue", pipeline_source)
        self.assertIn("focusPreflightIssue", pipeline_source)


if __name__ == "__main__":
    unittest.main()
