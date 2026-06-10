from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_VUE = ROOT / "frontend" / "src" / "App.vue"
WORKBENCH_STORE = ROOT / "frontend" / "src" / "stores" / "workbench.ts"
TOONFLOW_WORKBENCH = ROOT / "frontend" / "src" / "components" / "workspace" / "ToonflowWorkbench.vue"
WORKSPACE_DIR = ROOT / "frontend" / "src" / "components" / "workspace"
PLAYWRIGHT_AUDIT = ROOT / "scripts" / "playwright_audit.mjs"


class FrontendToonflowWorkbenchTests(unittest.TestCase):
    def test_app_uses_single_toonflow_workbench_surface(self) -> None:
        app_source = APP_VUE.read_text(encoding="utf-8")

        self.assertIn("import ToonflowWorkbench", app_source)
        self.assertEqual(app_source.count("<ToonflowWorkbench"), 1)
        self.assertNotIn("WorkspaceSidebar", app_source)
        self.assertNotIn("WorkspaceProjectCreatePanel", app_source)
        self.assertNotIn("LongformPipelinePanel", app_source)
        self.assertNotIn("NovelEditorPanel", app_source)
        self.assertNotIn("VideoStagePage", app_source)

    def test_legacy_workspace_components_are_removed(self) -> None:
        remaining = sorted(path.name for path in WORKSPACE_DIR.glob("*.vue"))

        self.assertEqual(remaining, ["ToonflowWorkbench.vue"])

    def test_toonflow_workbench_matches_project_canvas_model(self) -> None:
        source = TOONFLOW_WORKBENCH.read_text(encoding="utf-8")

        self.assertIn("策划：从原著或简报建立事件图谱", source)
        self.assertIn("编剧", source)
        self.assertIn("资产", source)
        self.assertIn("出片", source)
        self.assertIn("toon-canvas", source)
        self.assertIn("批量生产设置", source)
        self.assertNotIn("视频创作", source)
        self.assertNotIn("小说创作", source)
        self.assertNotIn("动画资产", source)

    def test_agent_panel_does_not_show_fake_command_input(self) -> None:
        source = TOONFLOW_WORKBENCH.read_text(encoding="utf-8")

        self.assertNotIn("输入生产指令", source)
        self.assertNotIn("toon-agent__input", source)
        self.assertIn("toon-agent__status", source)

    def test_asset_cards_wire_existing_asset_actions(self) -> None:
        app_source = APP_VUE.read_text(encoding="utf-8")
        source = TOONFLOW_WORKBENCH.read_text(encoding="utf-8")

        self.assertIn('(e: "update-media-asset"', source)
        self.assertIn('(e: "delete-media-asset"', source)
        self.assertIn('candidate_status: locked ? "locked" : "candidate"', source)
        self.assertIn('@click="emit(\'update-media-asset\', asset.id, assetLockMeta(true))"', source)
        self.assertIn('@click="emit(\'update-media-asset\', asset.id, assetLockMeta(false))"', source)
        self.assertIn('@click="emit(\'delete-media-asset\', asset.id)"', source)
        self.assertNotIn("<span>设为采用</span>", source)
        self.assertNotIn("<span>取消采用</span>", source)
        self.assertNotIn("<span>删除候选</span>", source)

        self.assertIn('@update-media-asset="updateMediaAsset"', app_source)
        self.assertIn('@delete-media-asset="store.deleteMediaAsset"', app_source)

    def test_production_canvas_wires_video_task_actions(self) -> None:
        app_source = APP_VUE.read_text(encoding="utf-8")
        source = TOONFLOW_WORKBENCH.read_text(encoding="utf-8")

        self.assertIn('(e: "create-video-task"', source)
        self.assertIn('(e: "delete-video-task"', source)
        self.assertIn("videoTasksByStoryboard", source)
        self.assertIn('@click="emit(\'create-video-task\', track.storyboard.id)"', source)
        self.assertIn('@click="emit(\'delete-video-task\', task.id)"', source)
        self.assertIn("生产任务 {{ task.id }}", source)
        self.assertNotIn("Track 3 · 视频出片", source)

        self.assertIn('@create-video-task="store.createVideoTask"', app_source)
        self.assertIn('@delete-video-task="store.deleteVideoTask"', app_source)

    def test_settings_canvas_wires_project_update(self) -> None:
        app_source = APP_VUE.read_text(encoding="utf-8")
        source = TOONFLOW_WORKBENCH.read_text(encoding="utf-8")

        self.assertIn('(e: "save-project-settings"', source)
        self.assertIn("projectSettingsPayload()", source)
        self.assertIn("settingsDraft.title", source)
        self.assertIn("settingsDraft.genre", source)
        self.assertIn("settingsDraft.world_brief", source)
        self.assertIn("settingsDraft.writing_rules", source)
        self.assertIn('@submit.prevent="saveProjectSettings()"', source)
        self.assertIn('emit("save-project-settings", payload)', source)

        self.assertIn('@save-project-settings="store.updateProject"', app_source)

    def test_project_create_is_not_restored_as_startup_view(self) -> None:
        app_source = APP_VUE.read_text(encoding="utf-8")
        restorable_block = app_source.split("const restorableViews: ViewKey[] = [", 1)[1].split("];", 1)[0]

        self.assertNotIn('"projectCreate"', restorable_block)
        self.assertNotIn('"setupStage"', restorable_block)
        self.assertNotIn('"novelStage"', restorable_block)
        self.assertNotIn('"videoStage"', restorable_block)
        self.assertIn("window.scrollTo({ top: 0, left: 0, behavior: \"auto\" })", app_source)

    def test_startup_api_failure_is_handled_without_unhandled_rejection(self) -> None:
        store_source = WORKBENCH_STORE.read_text(encoding="utf-8")
        initialize_block = store_source.split("async function initialize() {", 1)[1].split("async function refreshCaptcha()", 1)[0]

        self.assertIn("try {", initialize_block)
        self.assertIn('error.value = err instanceof Error ? err.message : "启动工作台失败。";', initialize_block)
        self.assertNotIn("throw", initialize_block)

    def test_playwright_audit_writes_to_repo_output_directory(self) -> None:
        audit_source = PLAYWRIGHT_AUDIT.read_text(encoding="utf-8")

        self.assertIn('path.resolve("output/playwright-audit")', audit_source)
        self.assertIn('createRequire(new URL("../frontend/package.json", import.meta.url))', audit_source)
        self.assertNotIn("E:/Computer/Wyc_Xc/MVP", audit_source)


if __name__ == "__main__":
    unittest.main()
