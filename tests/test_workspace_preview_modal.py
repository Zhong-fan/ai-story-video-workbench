from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREVIEW_MODAL = ROOT / "frontend" / "src" / "components" / "workspace" / "PreviewModal.vue"
PIPELINE = ROOT / "frontend" / "src" / "components" / "workspace" / "LongformPipelinePanel.vue"


class WorkspacePreviewModalTests(unittest.TestCase):
    def test_preview_modal_is_shared_component(self) -> None:
        self.assertTrue(PREVIEW_MODAL.exists(), "Preview modal should live in a reusable workspace component")
        modal_source = PREVIEW_MODAL.read_text(encoding="utf-8")
        pipeline_source = PIPELINE.read_text(encoding="utf-8")

        self.assertIn("defineProps", modal_source)
        self.assertIn("kind: PreviewKind", modal_source)
        self.assertIn('kind === "image"', modal_source)
        self.assertIn('kind === "audio"', modal_source)
        self.assertIn("<video", modal_source)
        self.assertIn("Escape", modal_source)
        self.assertIn('@click.self="close"', modal_source)

        self.assertIn('import PreviewModal from "./PreviewModal.vue"', pipeline_source)
        self.assertIn("<PreviewModal", pipeline_source)
        self.assertNotIn('class="asset-modal" role="dialog"', pipeline_source)


if __name__ == "__main__":
    unittest.main()
