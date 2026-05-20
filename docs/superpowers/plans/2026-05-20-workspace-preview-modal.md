# Workspace Preview Modal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the current workspace preview overlay into a reusable modal component so image, audio, and video previews open in a small in-page window instead of being embedded ad hoc inside one large panel.

**Architecture:** Keep the existing workspace preview style shell and move the rendering logic into a shared `PreviewModal.vue` component. The business panel will own preview state and resource selection, while the modal only handles display, close behavior, and media rendering. This keeps the preview UI reusable without changing generation or asset models.

**Tech Stack:** Vue 3, TypeScript, Vite, existing workspace CSS, Python unittest for source-level regression checks.

---

## Progress Log

- 2026-05-20 18:10: Plan created.
- 2026-05-20 18:13: Task 1 complete. `python -m unittest tests.test_workspace_preview_modal` failed as expected because `PreviewModal.vue` does not exist yet.
- 2026-05-20 18:18: Task 2 complete. `python -m unittest tests.test_workspace_preview_modal` passed after extracting `PreviewModal.vue` and wiring `LongformPipelinePanel.vue` to it.
- 2026-05-20 18:20: Task 3 complete. `npm run build` passed from `frontend/` after the shared preview modal extraction.

## Task Status

- [x] Task 1: Add a focused frontend regression test for shared preview modal usage.
- [x] Task 2: Extract the preview overlay into `PreviewModal.vue` and wire `LongformPipelinePanel.vue` to it.
- [x] Task 3: Run verification and record final status.

---

### Task 1: Add Regression Coverage For Shared Preview Modal

**Files:**
- Create: `tests/test_workspace_preview_modal.py`

- [x] **Step 1: Write the failing test**

Create `tests/test_workspace_preview_modal.py` with assertions that:
- `frontend/src/components/workspace/PreviewModal.vue` exists.
- `LongformPipelinePanel.vue` imports `PreviewModal`.
- `LongformPipelinePanel.vue` renders `<PreviewModal`.
- The old inline `asset-modal` markup is no longer embedded directly in `LongformPipelinePanel.vue`.

- [x] **Step 2: Run the focused test and confirm it fails**

Run: `python -m unittest tests.test_workspace_preview_modal`

Expected before implementation: FAIL because `PreviewModal.vue` does not exist and `LongformPipelinePanel.vue` still owns the overlay markup.

- [x] **Step 3: Update this task document**

Mark Task 1 complete and append a Progress Log entry with the test result.

---

### Task 2: Extract And Wire The Shared Preview Modal

**Files:**
- Create: `frontend/src/components/workspace/PreviewModal.vue`
- Modify: `frontend/src/components/workspace/LongformPipelinePanel.vue`

- [x] **Step 1: Implement the modal component**

Create `frontend/src/components/workspace/PreviewModal.vue` with:
- Props: `open`, `title`, `kind`, `url`
- Emit: `close`
- Render:
  - image previews with `<img>`
  - audio previews with `<audio controls>`
  - video previews with `<video controls playsinline>`
- Close behavior:
  - close button
  - backdrop click
  - `Escape` key
- Reuse the existing `.asset-modal`, `.asset-modal__body`, and `.asset-preview` classes.

- [x] **Step 2: Refactor the pipeline panel**

Update `frontend/src/components/workspace/LongformPipelinePanel.vue` to:
- import `PreviewModal`
- keep preview state in the panel
- replace the inline overlay markup with `<PreviewModal>`
- keep current preview open handlers for images, audio, and video

- [x] **Step 3: Run verification**

Run: `python -m unittest tests.test_workspace_preview_modal`

Expected: PASS.

- [x] **Step 4: Update this task document**

Mark Task 2 complete and append a Progress Log entry with the test result.

---

### Task 3: Full Verification

**Files:**
- Modify: this task document only for final status.

- [x] **Step 1: Build the frontend**

Run: `npm run build`

Working directory: `frontend`

Expected: exit 0.

- [x] **Step 2: Update this task document**

Mark Task 3 complete and append a Progress Log entry with the build result.
