# Workbench Cleanup And Candidate Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the unnecessary project content library entry point, make unwanted project/generated content removable, and make important generated visual outputs manageable as selectable candidates.

**Architecture:** Keep the existing FastAPI + SQLAlchemy backend and Vue + Pinia frontend. Reuse existing project soft-delete and media asset metadata patterns, add small DELETE endpoints for generated artifacts, and expose candidate actions in the existing longform/video workspace instead of introducing a separate library page.

**Tech Stack:** FastAPI, SQLAlchemy, PyMySQL/SQLite tests, Vue 3, Pinia, TypeScript, Vite, Python unittest.

---

## Progress Log

- 2026-05-20 17:00: Plan created.
- 2026-05-20 17:08: Task 1 complete. `python -m unittest tests.test_frontend_workspace_cleanup` passed; `rg` found no remaining `projectLibrary`/`ProjectContentLibraryPanel` references under `frontend/src`.
- 2026-05-20 17:17: Task 2 complete. `python -m unittest tests.test_longform_artifact_delete_api` passed after adding DELETE routes for media assets, video tasks, and storyboards.
- 2026-05-20 17:38: Task 3 complete. `python -m unittest tests.test_frontend_artifact_delete_wiring` passed after threading delete events through the video workspace and adding delete buttons for visual assets, storyboard drafts, storyboard assets, and completed video tasks.
- 2026-05-20 17:44: Task 4 complete. `python -m unittest tests.test_visual_asset_candidates` passed after adding versioned character turnaround outputs, candidate metadata, and candidate-oriented UI labels/actions.
- 2026-05-20 17:54: Task 5 verification complete. `python -m unittest tests.test_frontend_workspace_cleanup tests.test_longform_artifact_delete_api tests.test_frontend_artifact_delete_wiring tests.test_visual_asset_candidates` and `python -m unittest tests.test_reference_asset_api tests.test_reference_asset_service tests.test_visual_asset_locked_references tests.test_character_reference_profile` passed; `python -m compileall app tests` passed; `npm run build` passed from `frontend/`.

## Task Status

- [x] Task 1: Remove the project content library route and UI entry points.
- [x] Task 2: Add backend deletion for generated artifacts that users can safely discard.
- [x] Task 3: Add frontend delete actions for generated artifacts and refresh state after deletion.
- [x] Task 4: Add candidate-oriented visual asset handling for repeated image generation.
- [x] Task 5: Run verification and record final status.

---

### Task 1: Remove Project Content Library Entry Points

**Files:**
- Modify: `frontend/src/App.vue`
- Delete: `frontend/src/components/workspace/ProjectContentLibraryPanel.vue`
- Test: `tests/test_frontend_workspace_cleanup.py`

- [x] **Step 1: Write the failing test**

Create `tests/test_frontend_workspace_cleanup.py` with assertions that `App.vue` no longer imports or renders `ProjectContentLibraryPanel`, no longer includes `projectLibrary`, and does not show the sidebar label `项目内容库`.

- [x] **Step 2: Run the focused test and confirm it fails**

Run: `python -m unittest tests.test_frontend_workspace_cleanup`

Expected before implementation: FAIL because `projectLibrary`, `ProjectContentLibraryPanel`, or `项目内容库` still exists in `frontend/src/App.vue`.

- [x] **Step 3: Remove the UI route and component references**

Edit `frontend/src/App.vue` to remove:
- `ProjectContentLibraryPanel` import.
- `projectLibrary` from authenticated route guards and stage view lists.
- `openProjectLibrary()` and `handleLibraryOpenItem()` if unused after removing the view.
- Sidebar buttons labeled `内容库` and `项目内容库`.
- The template block that renders `<ProjectContentLibraryPanel ... />`.

Delete `frontend/src/components/workspace/ProjectContentLibraryPanel.vue` after references are gone.

- [x] **Step 4: Run verification**

Run: `python -m unittest tests.test_frontend_workspace_cleanup`

Expected: PASS.

- [x] **Step 5: Update this task document**

Mark Task 1 complete and append a Progress Log entry with the test result.

---

### Task 2: Add Backend Delete Endpoints For Generated Artifacts

**Files:**
- Modify: `app/api_routes_longform.py`
- Modify: `frontend/src/api.ts`
- Test: `tests/test_longform_artifact_delete_api.py`

- [x] **Step 1: Write failing API tests**

Create `tests/test_longform_artifact_delete_api.py` with tests for:
- `DELETE /api/projects/{project_id}/media-assets/{asset_id}` removes a media asset belonging to the current user's project.
- Deleting a `character_turnaround` asset clears any `CharacterReferenceProfile.locked_turnaround_asset_id` pointing to it.
- `DELETE /api/projects/{project_id}/video-tasks/{task_id}` removes a video task and related task events.
- `DELETE /api/projects/{project_id}/storyboards/{storyboard_id}` removes the storyboard, shots, storyboard media assets, video tasks, and related task events.

- [x] **Step 2: Run focused tests and confirm they fail**

Run: `python -m unittest tests.test_longform_artifact_delete_api`

Expected before implementation: FAIL with 405/404 because the DELETE routes do not exist.

- [x] **Step 3: Implement delete routes**

Add routes in `app/api_routes_longform.py` near the existing update routes:
- `DELETE /api/projects/{project_id}/media-assets/{asset_id}` returning `{"status": "deleted"}`.
- `DELETE /api/projects/{project_id}/video-tasks/{task_id}` returning `{"status": "deleted"}`.
- `DELETE /api/projects/{project_id}/storyboards/{storyboard_id}` returning `{"status": "deleted"}`.

When deleting media assets:
- Verify ownership through `_project_or_404`.
- If the asset is a locked `character_turnaround`, clear matching profile lock and resync profile state.
- Delete related `TaskEvent` rows that point to the asset only when represented in event payload is not required; keep this implementation focused on direct FK-like references.

When deleting video tasks:
- Delete `TaskEvent.video_task_id == task.id`.
- Delete the `VideoTask`.

When deleting storyboards:
- Delete `TaskEvent.storyboard_id == storyboard.id`.
- Delete `TaskEvent.video_task_id` for tasks under the storyboard.
- Delete `MediaAsset.storyboard_id == storyboard.id`.
- Delete `VideoTask.storyboard_id == storyboard.id`.
- Delete the `Storyboard`; existing cascade handles shots.

- [x] **Step 4: Add frontend API wrappers**

Add to `frontend/src/api.ts`:
- `deleteMediaAsset(token, projectId, assetId)`.
- `deleteVideoTask(token, projectId, taskId)`.
- `deleteStoryboard(token, projectId, storyboardId)`.

- [x] **Step 5: Run verification**

Run: `python -m unittest tests.test_longform_artifact_delete_api`

Expected: PASS.

- [x] **Step 6: Update this task document**

Mark Task 2 complete and append a Progress Log entry with the test result.

---

### Task 3: Expose Delete Actions In The Workspace

**Files:**
- Modify: `frontend/src/stores/workbench.ts`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/components/workspace/VideoCreatePage.vue`
- Modify: `frontend/src/components/workspace/VideoStagePage.vue`
- Modify: `frontend/src/components/workspace/LongformPipelinePanel.vue`
- Test: `tests/test_frontend_artifact_delete_wiring.py`

- [x] **Step 1: Write failing frontend wiring tests**

Create `tests/test_frontend_artifact_delete_wiring.py` with source assertions that:
- `workbench.ts` exposes `deleteMediaAsset`, `deleteVideoTask`, and `deleteStoryboard`.
- `LongformPipelinePanel.vue` emits `delete-asset`, `delete-video-task`, and `delete-storyboard`.
- The visual asset cards and video output cards include delete buttons.

- [x] **Step 2: Run focused tests and confirm they fail**

Run: `python -m unittest tests.test_frontend_artifact_delete_wiring`

Expected before implementation: FAIL because delete methods and emits are absent.

- [x] **Step 3: Implement store actions**

Add store actions:
- `deleteMediaAsset(assetId: number)`: calls API, refreshes longform state, refreshes active project if profile locks may change.
- `deleteVideoTask(taskId: number)`: calls API and refreshes longform state.
- `deleteStoryboard(storyboardId: number)`: calls API and refreshes longform state.

- [x] **Step 4: Thread emits through page components**

Update `VideoCreatePage.vue` and `VideoStagePage.vue` to pass delete events from `LongformPipelinePanel` to `App.vue`.

- [x] **Step 5: Add buttons in `LongformPipelinePanel.vue`**

Add delete buttons in:
- Visual assets list.
- Storyboard header.
- Storyboard asset list.
- Video output list.

Existing shot delete remains unchanged.

- [x] **Step 6: Run verification**

Run: `python -m unittest tests.test_frontend_artifact_delete_wiring`

Expected: PASS.

- [x] **Step 7: Update this task document**

Mark Task 3 complete and append a Progress Log entry with the test result.

---

### Task 4: Candidate-Oriented Visual Asset Handling

**Files:**
- Modify: `app/visual_asset_service.py`
- Modify: `frontend/src/components/workspace/LongformPipelinePanel.vue`
- Test: `tests/test_visual_asset_candidates.py`

- [x] **Step 1: Write failing service tests**

Create `tests/test_visual_asset_candidates.py` with source-level or unit tests showing:
- Repeated character turnaround generation should not overwrite `turnaround-v001.png`.
- New unlocked candidates should get increasing candidate version metadata.
- A locked candidate remains selected, while unlocked candidates can coexist and be deleted.

- [x] **Step 2: Run focused tests and confirm they fail**

Run: `python -m unittest tests.test_visual_asset_candidates`

Expected before implementation: FAIL because generated file paths are fixed to `turnaround-v001.png` and the UI does not present candidate-specific actions.

- [x] **Step 3: Implement candidate version naming**

In `VisualAssetService.generate_character_turnaround`, compute the next version for the character from existing `MediaAsset` rows and write `turnaround-vNNN.png` instead of always writing `turnaround-v001.png`.

Set media metadata:
- `candidate_version`: integer.
- `candidate_status`: `"candidate"`.
- `locked`: false by default.

- [x] **Step 4: Update UI copy and grouping**

In `LongformPipelinePanel.vue`, display candidate version labels for visual assets and make the primary action text clear:
- unlocked: `设为采用`
- locked: `取消采用`
- delete: `删除候选`

- [x] **Step 5: Run verification**

Run: `python -m unittest tests.test_visual_asset_candidates`

Expected: PASS.

- [x] **Step 6: Update this task document**

Mark Task 4 complete and append a Progress Log entry with the test result.

---

### Task 5: Full Verification

**Files:**
- Modify: this task document only for final status.

- [x] **Step 1: Run backend focused tests**

Run:
`python -m unittest tests.test_frontend_workspace_cleanup tests.test_longform_artifact_delete_api tests.test_frontend_artifact_delete_wiring tests.test_visual_asset_candidates`

Expected: PASS.

- [x] **Step 2: Run existing related tests**

Run:
`python -m unittest tests.test_reference_asset_api tests.test_reference_asset_service tests.test_visual_asset_locked_references tests.test_character_reference_profile`

Expected: PASS.

- [x] **Step 3: Compile Python**

Run:
`python -m compileall app tests`

Expected: exit 0.

- [x] **Step 4: Build frontend**

Run:
`npm run build`

Working directory: `frontend`

Expected: exit 0.

- [x] **Step 5: Update this task document**

Mark Task 5 complete, record all verification outputs, and note any residual risk.

Residual risk: frontend verification used production build and source-level wiring tests, not a browser interaction pass.
