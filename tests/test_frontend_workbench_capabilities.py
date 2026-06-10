from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "frontend" / "src" / "api.ts"
STORE = ROOT / "frontend" / "src" / "stores" / "workbench.ts"
TYPES = ROOT / "frontend" / "src" / "types.ts"
TOONFLOW_WORKBENCH = ROOT / "frontend" / "src" / "components" / "workspace" / "ToonflowWorkbench.vue"


class FrontendWorkbenchCapabilitiesTests(unittest.TestCase):
    def test_video_and_asset_store_capabilities_are_preserved(self) -> None:
        api_source = API.read_text(encoding="utf-8")
        store_source = STORE.read_text(encoding="utf-8")
        types_source = TYPES.read_text(encoding="utf-8")

        self.assertIn('source_mode?: "novel_chapters" | "image_first_reference" | "existing_images"', types_source)
        self.assertIn('"user_brief"', types_source)
        self.assertIn("reference_video_brief", types_source)

        for name in [
            "createImageFirstStoryboard",
            "createBriefStoryboard",
            "deleteStoryboard",
            "deleteVideoTask",
            "deleteMediaAsset",
            "generateCharacterTurnaround",
            "generateShotFirstFrame",
        ]:
            self.assertIn(name, store_source)

        for name in [
            "deleteStoryboard",
            "deleteVideoTask",
            "deleteMediaAsset",
            "generateCharacterTurnaround",
            "generateShotFirstFrame",
        ]:
            self.assertIn(name, api_source)

    def test_new_workbench_surfaces_assets_and_production_without_legacy_panels(self) -> None:
        source = TOONFLOW_WORKBENCH.read_text(encoding="utf-8")

        self.assertIn("mediaAssets", source)
        self.assertIn("productionTracks", source)
        self.assertIn("storyboards", source)
        self.assertIn("videoTaskCount", source)
        self.assertIn("characterCards", source)
        self.assertNotIn("PreviewModal", source)
        self.assertNotIn("LongformPipelinePanel", source)


if __name__ == "__main__":
    unittest.main()
