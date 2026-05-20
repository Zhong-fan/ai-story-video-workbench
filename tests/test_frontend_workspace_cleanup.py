from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_VUE = ROOT / "frontend" / "src" / "App.vue"
PROJECT_LIBRARY_PANEL = ROOT / "frontend" / "src" / "components" / "workspace" / "ProjectContentLibraryPanel.vue"


class FrontendWorkspaceCleanupTests(unittest.TestCase):
    def test_project_content_library_entry_points_are_removed(self) -> None:
        app_source = APP_VUE.read_text(encoding="utf-8")

        self.assertNotIn("ProjectContentLibraryPanel", app_source)
        self.assertNotIn("projectLibrary", app_source)
        self.assertNotIn("项目内容库", app_source)
        self.assertFalse(PROJECT_LIBRARY_PANEL.exists())


if __name__ == "__main__":
    unittest.main()
