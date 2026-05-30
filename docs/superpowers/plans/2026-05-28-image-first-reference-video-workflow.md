# Image-First Reference Video Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a video workflow that can start from a reference work or user-provided images, generate and lock key images first, then produce image-to-video shots without requiring a finished novel chapter.

**Architecture:** Keep the existing `Storyboard`, `StoryboardShot`, `MediaAsset`, `ReferenceImageAsset`, `CharacterReferenceProfile`, and Jimeng image/video stack, but separate the domains: novel produces chapter artifacts, storyboard consumes source artifacts and produces shot plans, and video consumes shot plans plus locked media assets. Extend storyboard creation with a source mode through a small source-adapter layer so the old novel-to-video path remains unchanged while a new image-first path creates storyboard shots from a reference brief and uses locked/generated first-frame images as required video inputs. Store new workflow metadata in existing JSON fields first; only add columns if later queries prove the JSON metadata insufficient.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic contracts, existing OpenAI LLM utility path, existing Jimeng image/video clients, Vue 3, Pinia, Python unittest, frontend regression/build scripts.

---

## Scope

This plan implements the product direction: video creation should not be limited to `novel -> storyboard -> video`. Users must also be able to start from:

- a reference work and a target short-video brief
- approved reference images
- generated key images
- uploaded existing images

The intended workflow is:

`reference work / images / style brief -> key image candidates -> user locks images -> image-to-video shots -> final video`

## Bounded Contexts

This plan intentionally separates the three main domains. They stay in the same FastAPI app and database for now; the boundary is service ownership and typed artifacts, not separate deployments.

### Novel Domain

Owns:

- project premise and longform planning inputs
- novels and chapters
- draft versions and canonicalized chapters
- chapter-level constraint snapshots

Produces:

- chapter artifacts that can be consumed by storyboard generation

Must not know:

- video providers
- first-frame generation
- video task state

### Storyboard Domain

Owns:

- storyboard jobs
- source-mode normalization
- conversion from source artifact to shot plan
- `Storyboard` and `StoryboardShot`
- shot continuity metadata

Consumes:

- chapter artifacts from the novel domain
- reference brief artifacts from the reference/image-first source
- existing image assets selected by the user

Produces:

- shot plans with visual prompts, narration, character refs, scene refs, and continuity requirements

Must not know:

- Jimeng task submission details
- final video task progress
- novel draft internals beyond the chapter artifact fields it receives

### Video Domain

Owns:

- video preflight gates
- shot first-frame requirements
- image-to-video versus text-to-video decision rules
- video tasks and render progress

Consumes:

- storyboard shots
- locked/generated `MediaAsset` records
- `CharacterReferenceProfile` visual master state

Produces:

- pending media task records
- video task records
- final rendered video URI

Must not know:

- how a novel chapter was drafted
- how a reference brief was expanded into shots

### Shared Asset Domain

Owns:

- `ReferenceImageAsset`
- `MediaAsset`
- `CharacterReferenceProfile`
- uploaded/generated image metadata

This is the shared contract between storyboard and video. The shared domain should expose asset status and identifiers; it should not embed storyboard-generation or video-rendering workflow decisions.

## Simplicity Check

The simpler boundary is a source-adapter layer inside the existing app, not a new service, plugin system, or provider abstraction. The confirmed need is three inputs into storyboard generation: chapters, reference brief, and existing images. A small adapter layer solves that now while keeping novel, storyboard, and video code from directly reaching into each other's internals.

## Non-Goals

- Do not remove the current novel-to-video workflow.
- Do not build web search in this plan.
- Do not build full visual similarity scoring.
- Do not add a provider abstraction.
- Do not allow silent text-to-video fallback for image-first shots.
- Do not replicate copyrighted scenes, exact characters, or exact shot sequences from a reference work unless the user has authorized source material. The UI and prompts should frame this as inheriting transferable visual/storytelling traits.

## Current Code Facts

- `CreateStoryboardRequest` currently requires `novel_chapter_ids: list[int]` with `min_length=1`.
- `StoryboardJobService.create_job()` validates selected novel chapters and stores them in `source_chapter_ids_json`.
- `StoryboardJobService.run_storyboard()` loads chapters and calls `StoryboardService.generate_storyboard(...)`.
- `Storyboard` has no dedicated source mode column; it has `source_chapter_ids_json`, `summary`, `status`, and events.
- `StoryboardShot.meta_json` already stores `audio_script` and `continuity`.
- `MediaAsset` already supports project-level and shot-level assets with `asset_type`, `uri`, `prompt`, `status`, and `meta_json`.
- `VisualAssetService.generate_shot_first_frame()` already creates `shot_first_frame`.
- `VideoRenderService` already prefers a first-frame asset for Jimeng image-to-video, but text-to-video fallback must be blocked for image-first shots.

## File Structure

Create:

- `app/storyboard_source_service.py`  
  Builds source artifacts for storyboard generation. It hides whether the storyboard source came from novel chapters, a reference brief, or existing images.

- `tests/test_image_first_reference_storyboard.py`  
  Backend tests for creating an image-first storyboard without chapters and preserving source metadata.

- `tests/test_image_first_video_gate.py`  
  Backend tests for blocking image-first video tasks when required locked first-frame images are missing.

- `tests/test_frontend_image_first_video_wiring.py`  
  Source-level regression that checks the frontend exposes the new mode and calls the new payload fields.

Modify:

- `app/contracts.py`  
  Extend storyboard creation contracts with source mode and image-first fields.

- `app/storyboard_job_service.py`  
  Split storyboard job creation and execution by source mode while preserving the current chapter path. It should delegate source loading to `StoryboardSourceService` instead of directly mixing novel lookup and image-first logic.

- `app/storyboard_service.py`  
  Add generation methods that consume normalized storyboard source artifacts. It should not load novels, reference images, or video task state directly.

- `app/api_routes_longform.py`  
  Accept the new storyboard request mode, enforce context pack where needed, and update video quality gates for image-first shots. Route code should remain orchestration only.

- `app/api_support_longform.py`  
  Include source mode and image-first metadata in `StoryboardOut` via `progress` or existing metadata fields.

- `app/video_render_service.py`  
  Treat image-first shots as requiring image-to-video and fail visibly when no usable first frame exists.

- `frontend/src/types.ts`  
  Extend `CreateStoryboardPayload` and add small typed helpers for image-first source options.

- `frontend/src/api.ts`  
  Keep the same endpoint, send the expanded payload.

- `frontend/src/stores/workbench.ts`  
  Preserve existing `createStoryboard()` callers and add a wrapper for image-first storyboard creation.

- `frontend/src/components/workspace/VideoStagePage.vue`  
  Add the source-mode selector and image-first entry controls.

- `frontend/src/components/workspace/VideoCreatePage.vue`  
  Show image-first storyboards and the required first-frame/key-image state.

---

## Task 1: Backend Contract For Storyboard Source Mode

**Files:**

- Modify: `app/contracts.py`
- Test: `tests/test_image_first_reference_storyboard.py`

- [ ] **Step 1: Write the failing API contract test**

Create `tests/test_image_first_reference_storyboard.py`:

```python
import unittest

from fastapi.testclient import TestClient

from app.api import create_app
from app.db import SessionLocal, init_db
from app.models import Project, Storyboard, User


class ImageFirstReferenceStoryboardTests(unittest.TestCase):
    def setUp(self) -> None:
        init_db()
        self.client = TestClient(create_app())
        with SessionLocal() as session:
            user = User(username="image-first-user", password_hash="x")
            project = Project(
                owner=user,
                title="雨夜短片",
                genre="都市奇幻",
                reference_work="天气之子",
                premise="一个雨夜里，陌生人追着一束光穿过城市。",
            )
            session.add_all([user, project])
            session.commit()
            self.user_id = user.id
            self.project_id = project.id

    def _auth_headers(self) -> dict[str, str]:
        return {"X-Debug-User-Id": str(self.user_id)}

    def test_create_image_first_storyboard_without_chapters(self) -> None:
        response = self.client.post(
            f"/api/projects/{self.project_id}/storyboards",
            headers=self._auth_headers(),
            json={
                "source_mode": "image_first_reference",
                "novel_chapter_ids": [],
                "title": "雨夜追光 15 秒",
                "reference_video_brief": "参考动画电影里通透雨夜和城市光影，生成一个 15 秒竖屏短片。",
                "key_image_strategy": "generate_first_frames",
                "reference_image_asset_ids": [],
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["source_chapter_ids"], [])
        self.assertEqual(payload["progress"]["source_mode"], "image_first_reference")
        self.assertEqual(payload["progress"]["key_image_strategy"], "generate_first_frames")

        with SessionLocal() as session:
            storyboard = session.get(Storyboard, payload["id"])
            self.assertIsNotNone(storyboard)
            self.assertEqual(storyboard.source_chapter_ids_json, "[]")
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
python -m unittest tests.test_image_first_reference_storyboard
```

Expected: FAIL with a validation error because `novel_chapter_ids` currently requires at least one item and `source_mode` is not supported.

- [ ] **Step 3: Extend `CreateStoryboardRequest`**

In `app/contracts.py`, replace `CreateStoryboardRequest` with:

```python
class CreateStoryboardRequest(BaseModel):
    source_mode: str = Field(default="novel_chapters", max_length=40)
    novel_chapter_ids: list[int] = Field(default_factory=list, max_length=12)
    title: str = Field(default="", max_length=255)
    reference_video_brief: str = Field(default="", max_length=4000)
    key_image_strategy: str = Field(default="generate_first_frames", max_length=80)
    reference_image_asset_ids: list[int] = Field(default_factory=list, max_length=50)
```

- [ ] **Step 4: Validate source modes in the API route**

In `app/api_routes_longform.py`, inside `create_storyboard()`, normalize:

```python
source_mode = payload.source_mode.strip() or "novel_chapters"
if source_mode not in {"novel_chapters", "image_first_reference", "existing_images"}:
    raise HTTPException(status_code=422, detail="不支持的分镜来源模式。")
if source_mode == "novel_chapters" and not payload.novel_chapter_ids:
    raise HTTPException(status_code=422, detail="从小说生成分镜时必须选择至少一个章节。")
if source_mode in {"image_first_reference", "existing_images"} and not payload.reference_video_brief.strip():
    raise HTTPException(status_code=422, detail="图片先行视频需要填写目标片段说明。")
```

- [ ] **Step 5: Run the test and verify this task passes**

Run:

```bash
python -m unittest tests.test_image_first_reference_storyboard
```

Expected: PASS after Task 2 adds service support. If it still fails because service support is missing, continue to Task 2 before marking both tasks complete.

---

## Task 2: Image-First Storyboard Job Creation

**Files:**

- Create: `app/storyboard_source_service.py`
- Modify: `app/storyboard_job_service.py`
- Modify: `app/api_routes_longform.py`
- Modify: `app/api_support_longform.py`
- Test: `tests/test_image_first_reference_storyboard.py`

- [ ] **Step 1: Add source artifact types**

Create `app/storyboard_source_service.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .json_utils import json_dumps
from .models import Novel, NovelChapter, Project, ReferenceImageAsset


@dataclass
class StoryboardSourceArtifact:
    source_mode: str
    title: str
    source_chapter_ids: list[int] = field(default_factory=list)
    reference_video_brief: str = ""
    key_image_strategy: str = "generate_first_frames"
    reference_image_asset_ids: list[int] = field(default_factory=list)
    chapter_payloads: list[dict[str, Any]] = field(default_factory=list)
    reference_image_notes: list[str] = field(default_factory=list)

    def event_payload(self) -> dict[str, Any]:
        return {
            "source_mode": self.source_mode,
            "novel_chapter_ids": self.source_chapter_ids,
            "reference_video_brief": self.reference_video_brief,
            "key_image_strategy": self.key_image_strategy,
            "reference_image_asset_ids": self.reference_image_asset_ids,
        }

    def source_chapter_ids_json(self) -> str:
        return json_dumps(self.source_chapter_ids)


class StoryboardSourceService:
    def build(
        self,
        db: Session,
        *,
        project: Project,
        current_user_id: int,
        source_mode: str,
        title: str,
        novel_chapter_ids: list[int],
        reference_video_brief: str,
        key_image_strategy: str,
        reference_image_asset_ids: list[int],
    ) -> StoryboardSourceArtifact:
        if source_mode == "novel_chapters":
            chapters = self._chapters_for_project(
                db,
                project=project,
                current_user_id=current_user_id,
                novel_chapter_ids=novel_chapter_ids,
            )
            if len(chapters) != len(set(novel_chapter_ids)):
                raise RuntimeError("只能选择当前项目下已发布/定稿章节生成分镜。")
            return StoryboardSourceArtifact(
                source_mode=source_mode,
                title=title,
                source_chapter_ids=novel_chapter_ids,
                chapter_payloads=[self._chapter_payload(item) for item in chapters],
            )

        reference_assets = db.scalars(
            select(ReferenceImageAsset).where(
                ReferenceImageAsset.project_id == project.id,
                ReferenceImageAsset.id.in_(reference_image_asset_ids),
            )
        ).all()
        return StoryboardSourceArtifact(
            source_mode=source_mode,
            title=title,
            source_chapter_ids=[],
            reference_video_brief=reference_video_brief.strip(),
            key_image_strategy=key_image_strategy,
            reference_image_asset_ids=[asset.id for asset in reference_assets],
            reference_image_notes=[self._reference_image_note(asset) for asset in reference_assets],
        )

    def _chapters_for_project(
        self,
        db: Session,
        *,
        project: Project,
        current_user_id: int,
        novel_chapter_ids: list[int],
    ) -> list[NovelChapter]:
        return db.scalars(
            select(NovelChapter)
            .join(Novel, NovelChapter.novel_id == Novel.id)
            .where(
                Novel.owner_id == current_user_id,
                Novel.project_id == project.id,
                Novel.deleted_at.is_(None),
                NovelChapter.id.in_(novel_chapter_ids),
            )
            .order_by(NovelChapter.chapter_no.asc())
        ).all()

    def _chapter_payload(self, chapter: NovelChapter) -> dict[str, Any]:
        return {
            "id": chapter.id,
            "chapter_no": chapter.chapter_no,
            "title": chapter.title,
            "summary": chapter.summary,
            "content": chapter.content,
        }

    def _reference_image_note(self, asset: ReferenceImageAsset) -> str:
        return f"{asset.asset_kind}: {asset.mapped_character_name or asset.source_work or asset.remote_url}".strip()
```

- [ ] **Step 2: Add job arguments without changing existing callers**

Update `StoryboardJobService.create_job()` signature:

```python
def create_job(
    self,
    *,
    db: Session,
    project: Project,
    current_user_id: int,
    novel_chapter_ids: list[int],
    title: str,
    source_mode: str = "novel_chapters",
    reference_video_brief: str = "",
    key_image_strategy: str = "generate_first_frames",
    reference_image_asset_ids: list[int] | None = None,
) -> Storyboard:
```

- [ ] **Step 3: Delegate source loading**

Inside `create_job()`, replace direct chapter lookup with:

```python
source = StoryboardSourceService().build(
    db,
    project=project,
    current_user_id=current_user_id,
    source_mode=source_mode,
    title=title,
    novel_chapter_ids=novel_chapter_ids,
    reference_video_brief=reference_video_brief,
    key_image_strategy=key_image_strategy,
    reference_image_asset_ids=reference_image_asset_ids or [],
)
```

- [ ] **Step 4: Store image-first metadata in storyboard progress**

When creating `Storyboard`, set `summary` to the brief and keep metadata in `progress`-compatible event payloads:

```python
storyboard = Storyboard(
    project=project,
    title=source.title.strip() or f"{project.title} 图片先行短片",
    source_chapter_ids_json=source.source_chapter_ids_json(),
    summary=source.reference_video_brief if source.source_mode != "novel_chapters" else "",
    status="queued",
    error_message="",
)
```

Add the queue event payload:

```python
payload=source.event_payload()
```

- [ ] **Step 5: Pass the new fields from the route**

In `create_storyboard()`, call:

```python
storyboard = StoryboardJobService(settings).create_job(
    db=db,
    project=project,
    current_user_id=current_user.id,
    novel_chapter_ids=payload.novel_chapter_ids,
    title=title,
    source_mode=source_mode,
    reference_video_brief=payload.reference_video_brief,
    key_image_strategy=payload.key_image_strategy,
    reference_image_asset_ids=payload.reference_image_asset_ids,
)
```

- [ ] **Step 6: Expose source metadata in `_storyboard_out()`**

In `app/api_support_longform.py`, compute source metadata from the first `storyboard_queued` event payload. Include these keys in `StoryboardOut.progress`:

```python
"source_mode": source_mode,
"reference_video_brief": reference_video_brief,
"key_image_strategy": key_image_strategy,
"reference_image_asset_ids": reference_image_asset_ids,
```

Default `source_mode` to `"novel_chapters"` for old storyboards.

- [ ] **Step 7: Run the focused test**

Run:

```bash
python -m unittest tests.test_image_first_reference_storyboard
```

Expected: PASS.

---

## Task 3: Generate Storyboard Shots From Reference Brief

**Files:**

- Modify: `app/storyboard_service.py`
- Modify: `app/storyboard_job_service.py`
- Test: `tests/test_image_first_reference_storyboard.py`

- [ ] **Step 1: Add a failing service-level test**

Extend `tests/test_image_first_reference_storyboard.py`:

```python
    def test_image_first_storyboard_job_generates_shots_with_i2v_continuity(self) -> None:
        response = self.client.post(
            f"/api/projects/{self.project_id}/storyboards",
            headers=self._auth_headers(),
            json={
                "source_mode": "image_first_reference",
                "novel_chapter_ids": [],
                "title": "雨夜追光 15 秒",
                "reference_video_brief": "三镜头：雨中街口、抬头看光、光穿过云层。",
                "key_image_strategy": "generate_first_frames",
                "reference_image_asset_ids": [],
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        storyboard_id = response.json()["id"]

        from app.storyboard_job_service import StoryboardJobService
        from app.config import Settings

        with SessionLocal() as session:
            storyboard = session.get(Storyboard, storyboard_id)
            StoryboardJobService(Settings()).run_storyboard(db=session, storyboard=storyboard)
            session.refresh(storyboard)
            self.assertEqual(storyboard.status, "draft")
            self.assertGreaterEqual(len(storyboard.shots), 1)
            for shot in storyboard.shots:
                self.assertTrue(shot.visual_prompt.strip())
                self.assertIn('"requires_i2v": true', shot.meta_json)
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
python -m unittest tests.test_image_first_reference_storyboard
```

Expected: FAIL because `run_storyboard()` still assumes chapter-backed jobs.

- [ ] **Step 3: Add `generate_image_first_storyboard()`**

In `app/storyboard_service.py`, add a method:

```python
def generate_image_first_storyboard(
    self,
    *,
    project: Project,
    title: str,
    reference_video_brief: str,
    reference_image_notes: list[str],
    context_pack_inputs: dict[str, Any],
) -> dict[str, Any]:
    prompt = self._build_image_first_storyboard_prompt(
        project=project,
        title=title,
        reference_video_brief=reference_video_brief,
        reference_image_notes=reference_image_notes,
        context_pack_inputs=context_pack_inputs,
    )
    return self._generate_storyboard_from_prompt(prompt)
```

If the existing service does not have `_generate_storyboard_from_prompt()`, extract the current LLM call body from `generate_storyboard()` into that helper first.

- [ ] **Step 4: Add explicit image-first prompt requirements**

The prompt must require each shot to include:

```text
- visual_prompt: enough detail to generate a still key image first
- continuity.requires_i2v: true
- continuity.first_frame_source: generated
- continuity.shot_type: new / continuation / camera_move / transition
- narration_text: short enough for the shot duration
```

It must also include:

```text
Do not copy exact copyrighted scenes or exact character designs from the reference work. Use transferable traits such as medium, lighting, camera language, color relationships, weather, atmosphere, composition rhythm, and emotional texture.
```

- [ ] **Step 5: Route `run_storyboard()` by source mode**

In `StoryboardJobService.run_storyboard()`, derive `source_mode` from the queue event payload. For `image_first_reference` and `existing_images`, skip chapter loading and call `StoryboardService.generate_image_first_storyboard(...)`.

- [ ] **Step 6: Run the focused test**

Run:

```bash
python -m unittest tests.test_image_first_reference_storyboard
```

Expected: PASS.

---

## Task 4: Key Image Assets Before Video

**Files:**

- Modify: `app/api_routes_longform.py`
- Modify: `app/visual_asset_service.py`
- Test: `tests/test_image_first_video_gate.py`

- [ ] **Step 1: Write the failing video gate test**

Create `tests/test_image_first_video_gate.py`:

```python
import unittest

from fastapi.testclient import TestClient

from app.api import create_app
from app.db import SessionLocal, init_db
from app.json_utils import json_dumps
from app.models import Project, Storyboard, StoryboardShot, User


class ImageFirstVideoGateTests(unittest.TestCase):
    def setUp(self) -> None:
        init_db()
        self.client = TestClient(create_app())
        with SessionLocal() as session:
            user = User(username="image-gate-user", password_hash="x")
            project = Project(owner=user, title="图片先行", genre="动画短片", reference_work="参考作品")
            storyboard = Storyboard(
                project=project,
                title="图片先行测试",
                source_chapter_ids_json="[]",
                status="draft",
                summary="从参考作品直接生成关键图再生成视频。",
            )
            shot = StoryboardShot(
                storyboard=storyboard,
                shot_no=1,
                narration_text="雨光落下。",
                visual_prompt="雨夜城市，一束光穿过云层。",
                character_refs_json="[]",
                scene_refs_json="[]",
                meta_json=json_dumps(
                    {
                        "continuity": {
                            "requires_i2v": True,
                            "first_frame_source": "generated",
                            "shot_type": "new",
                        },
                        "source_mode": "image_first_reference",
                    }
                ),
                duration_seconds=5,
                status="draft",
            )
            session.add_all([user, project, storyboard, shot])
            session.commit()
            self.user_id = user.id
            self.project_id = project.id
            self.storyboard_id = storyboard.id

    def test_image_first_video_task_requires_completed_first_frame(self) -> None:
        response = self.client.post(
            f"/api/projects/{self.project_id}/storyboards/{self.storyboard_id}/video-tasks",
            headers={"X-Debug-User-Id": str(self.user_id)},
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("图片先行镜头缺少已完成首帧", response.text)
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
python -m unittest tests.test_image_first_video_gate
```

Expected: FAIL if video task creation currently accepts the storyboard or fails for a less specific reason.

- [ ] **Step 3: Add image-first first-frame gate**

In `_video_quality_gate_failures()` in `app/api_routes_longform.py`, inspect shot continuity. If `requires_i2v` is true or shot metadata/source mode is `image_first_reference` / `existing_images`, require a completed `shot_first_frame` media asset for that shot.

Failure text:

```python
f"镜头 {shot.shot_no} 图片先行镜头缺少已完成首帧。"
```

- [ ] **Step 4: Ensure first-frame generation is the primary action**

In `generate_shot_first_frame()`, keep the existing endpoint but make sure image-first shots store metadata:

```python
"source_mode": "image_first_reference",
"i2v_required": True,
"key_image_role": "first_frame",
```

when the shot or storyboard source mode is image-first.

- [ ] **Step 5: Run the focused test**

Run:

```bash
python -m unittest tests.test_image_first_video_gate
```

Expected: PASS.

---

## Task 5: Video Rendering Must Not Fall Back To Text For Image-First Shots

**Files:**

- Modify: `app/video_render_service.py`
- Test: `tests/test_image_first_video_gate.py`

- [ ] **Step 1: Add a failing render-service test**

Extend `tests/test_image_first_video_gate.py` with a service-level test that creates a `VideoTask` for an image-first storyboard without first frames, then calls the render path and expects an explicit failure before text-to-video.

Expected error message:

```text
图片先行镜头必须使用首帧图生视频，不能回退到文生视频。
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
python -m unittest tests.test_image_first_video_gate
```

Expected: FAIL because current render behavior can fall back to text-to-video.

- [ ] **Step 3: Add `_shot_requires_i2v()`**

In `app/video_render_service.py`, add:

```python
def _shot_requires_i2v(self, shot: StoryboardShot) -> bool:
    meta = json_loads_dict(shot.meta_json)
    continuity = meta.get("continuity") if isinstance(meta.get("continuity"), dict) else {}
    source_mode = str(meta.get("source_mode") or continuity.get("source_mode") or "").strip()
    return bool(continuity.get("requires_i2v")) or source_mode in {"image_first_reference", "existing_images"}
```

- [ ] **Step 4: Block fallback**

Where the service decides between image-to-video and text-to-video, if `_shot_requires_i2v(shot)` is true and `_shot_first_frame_asset(...)` returns `None`, raise:

```python
RuntimeError("图片先行镜头必须使用首帧图生视频，不能回退到文生视频。")
```

- [ ] **Step 5: Run the focused test**

Run:

```bash
python -m unittest tests.test_image_first_video_gate
```

Expected: PASS.

---

## Task 6: Frontend Source Mode And Store Wiring

**Files:**

- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/stores/workbench.ts`
- Modify: `frontend/src/components/workspace/VideoStagePage.vue`
- Modify: `frontend/src/components/workspace/VideoCreatePage.vue`
- Test: `tests/test_frontend_image_first_video_wiring.py`

- [ ] **Step 1: Write source-level frontend regression**

Create `tests/test_frontend_image_first_video_wiring.py`:

```python
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendImageFirstVideoWiringTests(unittest.TestCase):
    def test_image_first_payload_and_ui_are_wired(self) -> None:
        types_source = (ROOT / "frontend" / "src" / "types.ts").read_text(encoding="utf-8")
        store_source = (ROOT / "frontend" / "src" / "stores" / "workbench.ts").read_text(encoding="utf-8")
        stage_source = (ROOT / "frontend" / "src" / "components" / "workspace" / "VideoStagePage.vue").read_text(encoding="utf-8")
        create_source = (ROOT / "frontend" / "src" / "components" / "workspace" / "VideoCreatePage.vue").read_text(encoding="utf-8")

        self.assertIn('source_mode?: "novel_chapters" | "image_first_reference" | "existing_images"', types_source)
        self.assertIn("reference_video_brief", types_source)
        self.assertIn("createImageFirstStoryboard", store_source)
        self.assertIn("image_first_reference", stage_source)
        self.assertIn("先生成关键图", stage_source)
        self.assertIn("shot_first_frame", create_source)
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
python -m unittest tests.test_frontend_image_first_video_wiring
```

Expected: FAIL because the frontend has no image-first source mode yet.

- [ ] **Step 3: Extend frontend payload type**

In `frontend/src/types.ts`, update:

```ts
export interface CreateStoryboardPayload {
  source_mode?: "novel_chapters" | "image_first_reference" | "existing_images";
  novel_chapter_ids: number[];
  title: string;
  reference_video_brief?: string;
  key_image_strategy?: "generate_first_frames" | "use_existing_images";
  reference_image_asset_ids?: number[];
}
```

- [ ] **Step 4: Add store wrapper**

In `frontend/src/stores/workbench.ts`, add:

```ts
async function createImageFirstStoryboard(payload: {
  title: string;
  reference_video_brief: string;
  key_image_strategy?: "generate_first_frames" | "use_existing_images";
  reference_image_asset_ids?: number[];
}) {
  return createStoryboard({
    source_mode: "image_first_reference",
    novel_chapter_ids: [],
    title: payload.title,
    reference_video_brief: payload.reference_video_brief,
    key_image_strategy: payload.key_image_strategy ?? "generate_first_frames",
    reference_image_asset_ids: payload.reference_image_asset_ids ?? [],
  });
}
```

Export it from the returned store object.

- [ ] **Step 5: Add video-stage controls**

In `VideoStagePage.vue`, add a compact source selector with three options:

- `从小说章节生成`
- `参考作品 -> 先生成关键图`
- `已有图片 -> 图生视频`

The image-first panel must collect:

- title
- reference/video brief
- optional approved reference image selection

Primary button text:

```text
先生成关键图
```

- [ ] **Step 6: Show first-frame readiness in create page**

In `VideoCreatePage.vue`, for image-first storyboards show shot cards with:

- `shot_first_frame` completed/missing state
- action to generate first frame
- disabled video task button until all required first frames are completed

- [ ] **Step 7: Run frontend wiring test**

Run:

```bash
python -m unittest tests.test_frontend_image_first_video_wiring
```

Expected: PASS.

---

## Task 7: Regression And Build Verification

**Files:**

- Existing test and frontend files only.

- [ ] **Step 1: Run focused backend tests**

Run:

```bash
python -m unittest tests.test_image_first_reference_storyboard tests.test_image_first_video_gate
```

Expected: PASS.

- [ ] **Step 2: Run frontend wiring test**

Run:

```bash
python -m unittest tests.test_frontend_image_first_video_wiring
```

Expected: PASS.

- [ ] **Step 3: Run existing related backend tests**

Run:

```bash
python -m unittest tests.test_reference_asset_api tests.test_turnaround_uses_reference_assets tests.test_visual_asset_locked_references tests.test_video_preflight_quality_gates
```

Expected: PASS.

- [ ] **Step 4: Compile Python**

Run:

```bash
python -m compileall app tests
```

Expected: PASS with no syntax errors.

- [ ] **Step 5: Build frontend**

Run:

```bash
npm run build
```

Expected: PASS.

- [ ] **Step 6: Run regression suite if available**

Run:

```bash
npm run test:regression
```

Expected: PASS. If the command fails because the local browser/test dependency is unavailable, record the exact failure in the final handoff.

---

## Acceptance Criteria

- A user can create a storyboard with no novel chapters using `source_mode = "image_first_reference"`.
- The resulting storyboard records `source_mode`, `reference_video_brief`, `key_image_strategy`, and selected reference image IDs in API output.
- Image-first storyboard shots require image-to-video continuity.
- Video task creation blocks until required shot first frames exist.
- Rendering image-first shots cannot silently fall back to text-to-video.
- Frontend video stage offers a clear “参考作品 -> 先生成关键图” entry.
- Existing novel-to-video behavior remains compatible.

## Self-Review Notes

- Spec coverage: the plan covers source-mode contracts, job creation, reference-brief shot generation, key-image gating, render fallback blocking, frontend wiring, and verification.
- Placeholder scan: no unfinished placeholder markers remain.
- Type consistency: backend uses `source_mode`, `reference_video_brief`, `key_image_strategy`, and `reference_image_asset_ids`; frontend uses the same field names.
