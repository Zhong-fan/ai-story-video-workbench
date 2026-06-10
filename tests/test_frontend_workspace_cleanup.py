from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_VUE = ROOT / "frontend" / "src" / "App.vue"
PROJECT_LIBRARY_PANEL = ROOT / "frontend" / "src" / "components" / "workspace" / "ProjectContentLibraryPanel.vue"
WORKSPACE_SIDEBAR = ROOT / "frontend" / "src" / "components" / "workspace" / "WorkspaceSidebar.vue"
WORKSPACE_TRASH_PANEL = ROOT / "frontend" / "src" / "components" / "workspace" / "WorkspaceTrashPanel.vue"
WORKSPACE_PROJECT_CREATE_PANEL = ROOT / "frontend" / "src" / "components" / "workspace" / "WorkspaceProjectCreatePanel.vue"
PROJECT_CREATE_WIZARD = ROOT / "frontend" / "src" / "components" / "workspace" / "ProjectCreateWizard.vue"
STUDIO_WORKSPACE_PANEL = ROOT / "frontend" / "src" / "components" / "workspace" / "StudioWorkspacePanel.vue"
ASSET_LIBRARY_PANEL = ROOT / "frontend" / "src" / "components" / "workspace" / "AssetLibraryPanel.vue"
PLAYWRIGHT_REGRESSION = ROOT / "frontend" / "scripts" / "playwright_regression.mjs"
PLAYWRIGHT_AUDIT = ROOT / "scripts" / "playwright_audit.mjs"


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
        self.assertIn("先把项目核心设定立住", project_create_source)

    def test_agent_workspace_create_modes_are_wired_to_project_create(self) -> None:
        app_source = APP_VUE.read_text(encoding="utf-8")
        studio_source = STUDIO_WORKSPACE_PANEL.read_text(encoding="utf-8")
        project_create_source = WORKSPACE_PROJECT_CREATE_PANEL.read_text(encoding="utf-8")
        wizard_source = PROJECT_CREATE_WIZARD.read_text(encoding="utf-8")
        api_source = (ROOT / "frontend" / "src" / "api.ts").read_text(encoding="utf-8")
        store_source = (ROOT / "frontend" / "src" / "stores" / "workbench.ts").read_text(encoding="utf-8")

        self.assertIn('activeStudioAgent = ref<"shortDrama" | "novel" | "anime">', app_source)
        self.assertIn('projectCreateMode = ref<"upload" | "ai" | "manual">', app_source)
        self.assertIn(":creation-mode=\"projectCreateMode\"", app_source)
        self.assertIn("workflowCards", studio_source)
        self.assertIn('mode: "upload"', studio_source)
        self.assertIn('mode: "manual"', studio_source)
        self.assertIn("emit('start-create', { agent: entry.agent, mode: entry.mode })", studio_source)
        self.assertIn("creationMode", project_create_source)
        self.assertIn(':active-agent="activeAgent"', project_create_source)
        self.assertIn("activeAgent", wizard_source)
        self.assertIn("上传剧本建项目", wizard_source)
        self.assertIn("AI 生成剧本", wizard_source)
        self.assertIn("自主输入", wizard_source)
        self.assertIn("importProjectDraft", api_source)
        self.assertIn("createProjectBriefDraft", api_source)
        self.assertIn("loadImportedProjectDraft", store_source)
        self.assertIn("loadAiProjectDraft", store_source)
        self.assertIn("剧本正文或梗概", wizard_source)
        self.assertIn("生成项目草稿", wizard_source)
        self.assertIn("主角", wizard_source)
        self.assertIn("核心冲突", wizard_source)

    def test_agent_workspace_entry_copy_matches_active_agent(self) -> None:
        app_source = APP_VUE.read_text(encoding="utf-8")
        sidebar_source = WORKSPACE_SIDEBAR.read_text(encoding="utf-8")
        studio_source = STUDIO_WORKSPACE_PANEL.read_text(encoding="utf-8")
        project_create_source = WORKSPACE_PROJECT_CREATE_PANEL.read_text(encoding="utf-8")

        self.assertIn("workflowCards", studio_source)
        self.assertIn("视频创作", studio_source)
        self.assertIn("小说创作", studio_source)
        self.assertIn("动画资产", studio_source)
        self.assertNotIn("短剧Agent</button>", sidebar_source)
        self.assertNotIn("小说Agent</button>", sidebar_source)
        self.assertNotIn("动漫Agent</button>", sidebar_source)
        self.assertIn("emptyText", studio_source)
        self.assertIn("@open-project-create=\"openSidebarProjectCreate($event)\"", app_source)
        self.assertIn("(e: \"open-project-create\", mode: CreationMode): void", sidebar_source)
        self.assertIn("createHeaderCopies", project_create_source)
        self.assertIn("小说导入", project_create_source)
        self.assertIn("动画项目设定", project_create_source)
        self.assertIn("creationModeCopies", PROJECT_CREATE_WIZARD.read_text(encoding="utf-8"))
        self.assertIn("AI 生成小说", PROJECT_CREATE_WIZARD.read_text(encoding="utf-8"))
        self.assertIn("角色与场景设定", PROJECT_CREATE_WIZARD.read_text(encoding="utf-8"))

    def test_asset_library_is_real_read_only_view_not_disabled_stub(self) -> None:
        app_source = APP_VUE.read_text(encoding="utf-8")
        asset_source = ASSET_LIBRARY_PANEL.read_text(encoding="utf-8")

        self.assertIn("import AssetLibraryPanel", app_source)
        self.assertIn("assetLibrary", app_source)
        self.assertTrue(ASSET_LIBRARY_PANEL.exists())
        self.assertNotIn("上传待接入", asset_source)
        self.assertNotIn("disabled>上传", asset_source)
        self.assertIn("按项目管理图片和视频资产", asset_source)

    def test_workspace_surfaces_project_and_media_asset_codes(self) -> None:
        app_source = APP_VUE.read_text(encoding="utf-8")
        studio_source = STUDIO_WORKSPACE_PANEL.read_text(encoding="utf-8")
        asset_source = ASSET_LIBRARY_PANEL.read_text(encoding="utf-8")
        trash_source = WORKSPACE_TRASH_PANEL.read_text(encoding="utf-8")

        self.assertIn("media_asset", app_source)
        self.assertIn("formatProjectCode", studio_source)
        self.assertIn("formatProjectCode", asset_source)
        self.assertIn("formatProjectCode", trash_source)
        self.assertIn("M${String(item.item_id).padStart(6, \"0\")}", trash_source)

    def test_playwright_regression_targets_current_agent_workspace(self) -> None:
        regression_source = PLAYWRIGHT_REGRESSION.read_text(encoding="utf-8")

        self.assertIn("短剧Agent", regression_source)
        self.assertIn("上传剧本", regression_source)
        self.assertIn("AI生成剧本", regression_source)
        self.assertIn("自主输入", regression_source)
        self.assertIn("先把项目核心设定立住", regression_source)
        self.assertIn(".project-home-card", regression_source)
        self.assertNotIn("先把小说的核心设定立住", regression_source)
        self.assertNotIn("小说标题", regression_source)
        self.assertNotIn('"我的项目"', regression_source)

    def test_playwright_audit_writes_to_repo_output_directory(self) -> None:
        audit_source = PLAYWRIGHT_AUDIT.read_text(encoding="utf-8")

        self.assertIn('path.resolve("output/playwright-audit")', audit_source)
        self.assertIn('createRequire(new URL("../frontend/package.json", import.meta.url))', audit_source)
        self.assertNotIn("E:/Computer/Wyc_Xc/MVP", audit_source)


if __name__ == "__main__":
    unittest.main()
