from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_VUE = ROOT / "frontend" / "src" / "App.vue"
PROJECT_LIBRARY_PANEL = ROOT / "frontend" / "src" / "components" / "workspace" / "ProjectContentLibraryPanel.vue"
WORKSPACE_SIDEBAR = ROOT / "frontend" / "src" / "components" / "workspace" / "WorkspaceSidebar.vue"
WORKSPACE_TRASH_PANEL = ROOT / "frontend" / "src" / "components" / "workspace" / "WorkspaceTrashPanel.vue"
WORKSPACE_PROJECT_CREATE_PANEL = ROOT / "frontend" / "src" / "components" / "workspace" / "WorkspaceProjectCreatePanel.vue"


class FrontendWorkspaceCleanupTests(unittest.TestCase):
    def test_project_content_library_entry_points_are_removed(self) -> None:
        app_source = APP_VUE.read_text(encoding="utf-8")

        self.assertNotIn("ProjectContentLibraryPanel", app_source)
        self.assertNotIn("projectLibrary", app_source)
        self.assertNotIn("项目内容库", app_source)
        self.assertFalse(PROJECT_LIBRARY_PANEL.exists())

    def test_workspace_sidebar_is_extracted_from_app_template(self) -> None:
        app_source = APP_VUE.read_text(encoding="utf-8")
        sidebar_source = WORKSPACE_SIDEBAR.read_text(encoding="utf-8")

        self.assertIn("import WorkspaceSidebar", app_source)
        self.assertIn("<WorkspaceSidebar", app_source)
        self.assertNotIn('<aside id="primary-sidebar"', app_source)
        self.assertIn('id="primary-sidebar"', sidebar_source)
        self.assertIn("open-project-create", sidebar_source)

    def test_workspace_trash_panel_is_extracted_from_app_template(self) -> None:
        app_source = APP_VUE.read_text(encoding="utf-8")
        self.assertTrue(WORKSPACE_TRASH_PANEL.exists())
        trash_source = WORKSPACE_TRASH_PANEL.read_text(encoding="utf-8")

        self.assertIn("import WorkspaceTrashPanel", app_source)
        self.assertIn("<WorkspaceTrashPanel", app_source)
        self.assertNotIn("已删除内容", app_source)
        self.assertIn("已删除内容", trash_source)
        self.assertIn("restore", trash_source)

    def test_workspace_project_create_panel_is_extracted_from_app_template(self) -> None:
        app_source = APP_VUE.read_text(encoding="utf-8")
        self.assertTrue(WORKSPACE_PROJECT_CREATE_PANEL.exists())
        project_create_source = WORKSPACE_PROJECT_CREATE_PANEL.read_text(encoding="utf-8")

        self.assertIn("import WorkspaceProjectCreatePanel", app_source)
        self.assertIn("<WorkspaceProjectCreatePanel", app_source)
        self.assertNotIn("先把小说的核心设定立住", app_source)
        self.assertIn("ProjectCreateWizard", project_create_source)
        self.assertIn("先把小说的核心设定立住", project_create_source)


if __name__ == "__main__":
    unittest.main()
