from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_VUE = ROOT / "frontend" / "src" / "App.vue"
STORE = ROOT / "frontend" / "src" / "stores" / "workbench.ts"
PIPELINE = ROOT / "frontend" / "src" / "components" / "workspace" / "LongformPipelinePanel.vue"
VIDEO_CREATE = ROOT / "frontend" / "src" / "components" / "workspace" / "VideoCreatePage.vue"
VIDEO_STAGE = ROOT / "frontend" / "src" / "components" / "workspace" / "VideoStagePage.vue"


class FrontendArtifactDeleteWiringTests(unittest.TestCase):
    def test_delete_actions_are_threaded_through_workspace(self) -> None:
        app_source = APP_VUE.read_text(encoding="utf-8")
        store_source = STORE.read_text(encoding="utf-8")
        pipeline_source = PIPELINE.read_text(encoding="utf-8")
        video_create_source = VIDEO_CREATE.read_text(encoding="utf-8")
        video_stage_source = VIDEO_STAGE.read_text(encoding="utf-8")

        self.assertIn("deleteMediaAsset", store_source)
        self.assertIn("deleteVideoTask", store_source)
        self.assertIn("deleteStoryboard", store_source)

        self.assertIn("delete-asset", pipeline_source)
        self.assertIn("delete-video-task", pipeline_source)
        self.assertIn("delete-storyboard", pipeline_source)
        self.assertIn('@click="emit(\'delete-asset\'', pipeline_source)
        self.assertIn('@click="emit(\'delete-video-task\'', pipeline_source)
        self.assertIn('@click="emit(\'delete-storyboard\'', pipeline_source)

        self.assertIn("@delete-asset", video_create_source)
        self.assertIn("@delete-video-task", video_create_source)
        self.assertIn("@delete-storyboard", video_create_source)
        self.assertIn("@delete-asset", video_stage_source)
        self.assertIn("@delete-video-task", video_stage_source)
        self.assertIn("@delete-storyboard", video_stage_source)
        self.assertIn("@delete-asset", app_source)
        self.assertIn("@delete-video-task", app_source)
        self.assertIn("@delete-storyboard", app_source)


if __name__ == "__main__":
    unittest.main()
