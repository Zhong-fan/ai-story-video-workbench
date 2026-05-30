# Creative Domain Decoupling Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first implementation slice for the OpenSpec change `decouple-creative-domains`: canonical source modes, source traces, source-independent storyboard metadata, and inspectable video quality plan/result records.

**Architecture:** Keep the current FastAPI app and database. Add small contract/helper modules around the existing storyboard and video code so `novel_chapters`, `image_first_reference`, `existing_images`, and `user_brief` flow through the same source-artifact and shot-plan path. Store new metadata in existing JSON/event fields first; avoid schema changes in this phase.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, existing `TaskEvent`, existing `Storyboard`/`StoryboardShot`/`VideoTask` models, Python `unittest`, Vue/Pinia source-level frontend checks.

---

## Scope

This plan implements the first foundation slice only.

In scope:

- Canonical `source_mode` contract.
- `user_brief` storyboard source support.
- Source trace metadata from storyboard queue event into each shot.
- Video quality plan before render.
- Video quality result after render completion or failure.
- Regression tests for the above.

Out of scope for this plan:

- Full microservice extraction.
- New database tables.
- Full node-based workflow editor.
- Full frontend redesign.
- Provider abstraction refactor beyond using existing call sites.

## Current Code Facts

- `CreateStoryboardRequest` already has `source_mode`, `reference_video_brief`, `key_image_strategy`, and `reference_image_asset_ids` in `app/contracts.py`.
- `app/api_routes_longform.py` currently accepts `novel_chapters`, `image_first_reference`, and `existing_images`, but not `user_brief`.
- `app/storyboard_source_service.py` already builds a `StoryboardSourceArtifact`, but it does not expose a first-class `source_trace`.
- `app/storyboard_job_service.py` writes `storyboard_queued` events and replaces shots, but shot `meta_json` does not consistently include `source_mode` or `source_trace`.
- `_video_quality_gate_failures()` already blocks missing locked character visuals and missing first frames, but it returns plain strings and has no quality plan/result.
- `VideoTask.progress_json` and `TaskEvent.payload_json` are available for quality metadata without adding columns.

## File Structure

Create:

- `app/creative_source_contracts.py`  
  Canonical source mode constants, validation helpers, and source trace builders.

- `app/video_quality_service.py`  
  Builds `video_quality_plan`, evaluates `video_quality_result`, and formats actionable quality gate failures.

- `tests/test_user_brief_storyboard_source.py`  
  Verifies `user_brief` can create and run storyboard generation without chapters.

- `tests/test_storyboard_source_trace.py`  
  Verifies queued source trace is copied into shot metadata and API output.

- `tests/test_video_quality_plan_result.py`  
  Verifies video task creation stores a quality plan and render completion/failure records a result.

Modify:

- `app/contracts.py`  
  Keep request shape, but import or reference canonical source mode values in comments/types only if this project accepts runtime imports in contracts. Do not add a hard dependency that causes import cycles.

- `app/api_routes_longform.py`  
  Use canonical source mode helpers, accept `user_brief`, create video quality plan on video task creation, and expose quality gate details.

- `app/api_support_longform.py`  
  Include `source_trace`, `video_quality_plan`, and `video_quality_result` in progress outputs.

- `app/storyboard_source_service.py`  
  Add source trace construction and validate mode-specific source requirements.

- `app/storyboard_job_service.py`  
  Pass source payload into shot replacement and write `source_mode` / `source_trace` into each shot `meta_json`.

- `app/video_render_service.py`  
  Record a quality result when render completes or fails.

- `frontend/src/types.ts`  
  Add `user_brief` to source mode type.

- `frontend/src/stores/workbench.ts`  
  Preserve existing calls and add a small wrapper for brief-sourced storyboard creation.

---

### Task 1: Canonical Source Mode Contract

**Files:**
- Create: `app/creative_source_contracts.py`
- Modify: `app/api_routes_longform.py`
- Modify: `frontend/src/types.ts`
- Test: `tests/test_user_brief_storyboard_source.py`

- [ ] **Step 1: Write the failing backend API test**

Create `tests/test_user_brief_storyboard_source.py`:

```python
from __future__ import annotations

import unittest

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api_routes_longform import register_longform_routes
from app.auth import get_current_user
from app.config import load_settings
from app.context_pack_service import ContextPackService
from app.db import Base, get_db
from app.models import Project, User


class UserBriefStoryboardSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite://",
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(bind=engine, future=True)
        with self.SessionLocal() as session:
            user = User(email="brief@example.com", display_name="Brief 用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="星桥短片", genre="都市奇幻", premise="两个人隔着城市看见同一束星光。")
            session.add_all([user, project])
            session.flush()
            ContextPackService().build(session, project=project, reference_mode="style_reference", user_notes="", confirm_after_build=True)
            session.commit()
            self.user_id = user.id
            self.project_id = project.id

        app = FastAPI()
        router = APIRouter()
        register_longform_routes(router, settings=load_settings())
        app.include_router(router)

        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        def override_current_user():
            with self.SessionLocal() as session:
                return session.get(User, self.user_id)

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_current_user
        self.client = TestClient(app)

    def test_create_user_brief_storyboard_without_chapters(self) -> None:
        response = self.client.post(
            f"/api/projects/{self.project_id}/storyboards",
            json={
                "source_mode": "user_brief",
                "novel_chapter_ids": [],
                "title": "星桥 20 秒短片",
                "reference_video_brief": "20 秒短片：夜色城市、星桥出现、两个人抬头看到同一束光。",
                "key_image_strategy": "generate_first_frames",
                "reference_image_asset_ids": [],
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["source_chapter_ids"], [])
        self.assertEqual(payload["progress"]["source_mode"], "user_brief")
        self.assertEqual(payload["progress"]["reference_video_brief"], "20 秒短片：夜色城市、星桥出现、两个人抬头看到同一束光。")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the failing test**

Run:

```powershell
python -m unittest tests.test_user_brief_storyboard_source
```

Expected: FAIL with status `422` and detail `不支持的分镜来源模式。`

- [ ] **Step 3: Add canonical source mode helpers**

Create `app/creative_source_contracts.py`:

```python
from __future__ import annotations

from typing import Any

SOURCE_MODE_NOVEL_CHAPTERS = "novel_chapters"
SOURCE_MODE_IMAGE_FIRST_REFERENCE = "image_first_reference"
SOURCE_MODE_EXISTING_IMAGES = "existing_images"
SOURCE_MODE_USER_BRIEF = "user_brief"

SUPPORTED_SOURCE_MODES = {
    SOURCE_MODE_NOVEL_CHAPTERS,
    SOURCE_MODE_IMAGE_FIRST_REFERENCE,
    SOURCE_MODE_EXISTING_IMAGES,
    SOURCE_MODE_USER_BRIEF,
}

NON_NOVEL_SOURCE_MODES = {
    SOURCE_MODE_IMAGE_FIRST_REFERENCE,
    SOURCE_MODE_EXISTING_IMAGES,
    SOURCE_MODE_USER_BRIEF,
}

IMAGE_CONTROLLED_SOURCE_MODES = {
    SOURCE_MODE_IMAGE_FIRST_REFERENCE,
    SOURCE_MODE_EXISTING_IMAGES,
}


def normalize_source_mode(value: str | None) -> str:
    source_mode = str(value or "").strip() or SOURCE_MODE_NOVEL_CHAPTERS
    if source_mode not in SUPPORTED_SOURCE_MODES:
        raise ValueError("不支持的分镜来源模式。")
    return source_mode


def source_mode_requires_brief(source_mode: str) -> bool:
    return source_mode in NON_NOVEL_SOURCE_MODES


def source_mode_requires_chapters(source_mode: str) -> bool:
    return source_mode == SOURCE_MODE_NOVEL_CHAPTERS


def source_mode_requires_i2v(source_mode: str) -> bool:
    return source_mode in IMAGE_CONTROLLED_SOURCE_MODES


def build_source_trace(
    *,
    source_mode: str,
    novel_chapter_ids: list[int],
    reference_video_brief: str,
    reference_image_asset_ids: list[int],
    key_image_strategy: str,
) -> dict[str, Any]:
    return {
        "source_mode": source_mode,
        "novel_chapter_ids": novel_chapter_ids,
        "reference_video_brief": reference_video_brief,
        "reference_image_asset_ids": reference_image_asset_ids,
        "key_image_strategy": key_image_strategy,
    }
```

- [ ] **Step 4: Use helpers in storyboard route validation**

In `app/api_routes_longform.py`, import helpers near the existing imports:

```python
from .creative_source_contracts import normalize_source_mode, source_mode_requires_brief, source_mode_requires_chapters
```

Replace the source mode validation in `create_storyboard()` with:

```python
        try:
            source_mode = normalize_source_mode(payload.source_mode)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if source_mode_requires_chapters(source_mode) and not payload.novel_chapter_ids:
            raise HTTPException(status_code=422, detail="从小说生成分镜时必须选择至少一个章节。")
        if source_mode_requires_brief(source_mode) and not payload.reference_video_brief.strip():
            raise HTTPException(status_code=422, detail="非小说来源视频需要填写目标片段说明。")
```

- [ ] **Step 5: Add frontend source mode type**

In `frontend/src/types.ts`, update the storyboard source mode type used by `CreateStoryboardPayload` to include `user_brief`.

Expected final shape:

```ts
source_mode?: "novel_chapters" | "image_first_reference" | "existing_images" | "user_brief";
```

- [ ] **Step 6: Run the backend and frontend source checks**

Run:

```powershell
python -m unittest tests.test_user_brief_storyboard_source tests.test_image_first_reference_storyboard tests.test_frontend_image_first_video_wiring
```

Expected: PASS for backend tests. If `tests.test_frontend_image_first_video_wiring` still expects the old union without `user_brief`, update that test assertion to the new union and rerun.

- [ ] **Step 7: Commit**

```powershell
git add app/creative_source_contracts.py app/api_routes_longform.py frontend/src/types.ts tests/test_user_brief_storyboard_source.py tests/test_frontend_image_first_video_wiring.py
git commit -m "feat: add canonical storyboard source modes"
```

### Task 2: Source Trace Propagation Into Storyboard Shots

**Files:**
- Modify: `app/storyboard_source_service.py`
- Modify: `app/storyboard_job_service.py`
- Modify: `app/api_support_longform.py`
- Test: `tests/test_storyboard_source_trace.py`

- [ ] **Step 1: Write the failing source trace test**

Create `tests/test_storyboard_source_trace.py`:

```python
from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api_routes_longform import register_longform_routes
from app.auth import get_current_user
from app.config import load_settings
from app.context_pack_service import ContextPackService
from app.db import Base, get_db
from app.json_utils import json_loads_object
from app.models import Project, Storyboard, User
from app.storyboard_job_service import StoryboardJobService


class StoryboardSourceTraceTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite://", future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(bind=engine, future=True)
        with self.SessionLocal() as session:
            user = User(email="trace@example.com", display_name="Trace 用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="追光短片", genre="都市奇幻", premise="雨夜里追逐城市光束。")
            session.add_all([user, project])
            session.flush()
            ContextPackService().build(session, project=project, reference_mode="style_reference", user_notes="", confirm_after_build=True)
            session.commit()
            self.user_id = user.id
            self.project_id = project.id

        app = FastAPI()
        router = APIRouter()
        register_longform_routes(router, settings=load_settings())
        app.include_router(router)

        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        def override_current_user():
            with self.SessionLocal() as session:
                return session.get(User, self.user_id)

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_current_user
        self.client = TestClient(app)

    def test_source_trace_is_copied_to_shot_meta(self) -> None:
        response = self.client.post(
            f"/api/projects/{self.project_id}/storyboards",
            json={
                "source_mode": "user_brief",
                "novel_chapter_ids": [],
                "title": "追光 15 秒",
                "reference_video_brief": "三镜头：雨夜街口、追逐光束、光照亮天空。",
                "key_image_strategy": "generate_first_frames",
                "reference_image_asset_ids": [],
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        storyboard_id = response.json()["id"]

        fake_payload = {
            "title": "追光 15 秒",
            "summary": "从 brief 生成的短片。",
            "shots": [
                {
                    "shot_no": 1,
                    "narration_text": "雨夜里，光从街角亮起。",
                    "visual_prompt": "二维动画电影，雨夜街角，蓝绿色光束。",
                    "character_refs": [],
                    "scene_refs": [],
                    "continuity": {"shot_type": "new", "first_frame_source": "generated", "requires_i2v": True},
                    "audio_script": {},
                    "duration_seconds": 5,
                }
            ],
        }

        with patch("app.storyboard_job_service.StoryboardService") as service_class:
            service_class.return_value.generate_image_first_storyboard.return_value = fake_payload
            with self.SessionLocal() as session:
                storyboard = session.get(Storyboard, storyboard_id)
                StoryboardJobService(load_settings()).run_storyboard(db=session, storyboard=storyboard)
                session.refresh(storyboard)

                meta = json_loads_object(storyboard.shots[0].meta_json)
                self.assertEqual(meta["source_mode"], "user_brief")
                self.assertEqual(meta["source_trace"]["source_mode"], "user_brief")
                self.assertEqual(meta["source_trace"]["reference_video_brief"], "三镜头：雨夜街口、追逐光束、光照亮天空。")
```

- [ ] **Step 2: Run the failing test**

Run:

```powershell
python -m unittest tests.test_storyboard_source_trace
```

Expected: FAIL with `KeyError: 'source_mode'` or `KeyError: 'source_trace'`.

- [ ] **Step 3: Add source trace to source artifacts**

In `app/storyboard_source_service.py`, import:

```python
from .creative_source_contracts import build_source_trace
```

Add a field to `StoryboardSourceArtifact`:

```python
    source_trace: dict[str, Any] = field(default_factory=dict)
```

Update `event_payload()`:

```python
            "source_trace": self.source_trace,
```

When returning the novel source artifact, set:

```python
                source_trace=build_source_trace(
                    source_mode=source_mode,
                    novel_chapter_ids=novel_chapter_ids,
                    reference_video_brief="",
                    reference_image_asset_ids=[],
                    key_image_strategy=key_image_strategy,
                ),
```

When returning a non-novel source artifact, set:

```python
            source_trace=build_source_trace(
                source_mode=source_mode,
                novel_chapter_ids=[],
                reference_video_brief=reference_video_brief.strip(),
                reference_image_asset_ids=[asset.id for asset in reference_assets],
                key_image_strategy=key_image_strategy,
            ),
```

- [ ] **Step 4: Copy source trace into each storyboard shot**

In `app/storyboard_job_service.py`, change the call:

```python
            shot_count = self._replace_shots(db, storyboard=storyboard, shots=ensure_list(generated.get("shots")))
```

to:

```python
            shot_count = self._replace_shots(
                db,
                storyboard=storyboard,
                shots=ensure_list(generated.get("shots")),
                source_payload=source_payload,
            )
```

Change the method signature:

```python
    def _replace_shots(self, db: Session, *, storyboard: Storyboard, shots: list[Any], source_payload: dict[str, Any]) -> int:
```

Before `db.add(StoryboardShot(...))`, compute:

```python
            source_mode = str(source_payload.get("source_mode") or "novel_chapters")
            source_trace = source_payload.get("source_trace") if isinstance(source_payload.get("source_trace"), dict) else {}
            if not source_trace:
                source_trace = {
                    "source_mode": source_mode,
                    "novel_chapter_ids": ensure_list(source_payload.get("novel_chapter_ids")),
                    "reference_video_brief": str(source_payload.get("reference_video_brief") or ""),
                    "reference_image_asset_ids": ensure_list(source_payload.get("reference_image_asset_ids")),
                    "key_image_strategy": str(source_payload.get("key_image_strategy") or "generate_first_frames"),
                }
```

Update the `meta_json` payload:

```python
                        {
                            "source_mode": source_mode,
                            "source_trace": source_trace,
                            "audio_script": self._normalize_audio_script(shot_payload.get("audio_script")),
                            "continuity": continuity,
                        }
```

- [ ] **Step 5: Include source trace in storyboard progress**

In `app/api_support_longform.py`, inside `_storyboard_progress()`, add:

```python
        "source_trace": queued_payload.get("source_trace") if isinstance(queued_payload.get("source_trace"), dict) else {},
```

- [ ] **Step 6: Run source trace and existing storyboard tests**

Run:

```powershell
python -m unittest tests.test_storyboard_source_trace tests.test_image_first_reference_storyboard tests.test_storyboard_shot_continuity
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add app/storyboard_source_service.py app/storyboard_job_service.py app/api_support_longform.py tests/test_storyboard_source_trace.py
git commit -m "feat: propagate storyboard source traces"
```

### Task 3: Video Quality Plan On Video Task Creation

**Files:**
- Create: `app/video_quality_service.py`
- Modify: `app/api_routes_longform.py`
- Modify: `app/api_support_longform.py`
- Test: `tests/test_video_quality_plan_result.py`

- [ ] **Step 1: Write the failing quality plan test**

Create `tests/test_video_quality_plan_result.py` with the setup below:

```python
from __future__ import annotations

import unittest

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api_routes_longform import register_longform_routes
from app.auth import get_current_user
from app.config import load_settings
from app.db import Base, get_db
from app.json_utils import json_loads_object
from app.models import Project, Storyboard, StoryboardShot, User, VideoTask


class VideoQualityPlanResultTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite://", future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(bind=engine, future=True)
        with self.SessionLocal() as session:
            user = User(email="quality@example.com", display_name="Quality 用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="质量短片", genre="都市奇幻", premise="一束光改变雨夜城市。")
            storyboard = Storyboard(project=project, title="质量短片", source_chapter_ids_json="[]", status="draft", summary="三镜头短片。")
            session.add_all([user, project, storyboard])
            session.flush()
            shot = StoryboardShot(
                storyboard=storyboard,
                shot_no=1,
                narration_text="雨夜街口出现一束光。",
                visual_prompt="二维动画电影，雨夜城市街口，蓝绿色光束。",
                character_refs_json="[]",
                scene_refs_json="[]",
                meta_json='{"source_mode":"user_brief","source_trace":{"source_mode":"user_brief","reference_video_brief":"三镜头短片。"},"continuity":{"requires_i2v":false,"first_frame_source":"generated"},"audio_script":{"subtitle_text":"雨夜街口出现一束光。"}}',
                duration_seconds=5,
                status="draft",
            )
            session.add(shot)
            session.commit()
            self.user_id = user.id
            self.project_id = project.id
            self.storyboard_id = storyboard.id

        app = FastAPI()
        router = APIRouter()
        register_longform_routes(router, settings=load_settings())
        app.include_router(router)

        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        def override_current_user():
            with self.SessionLocal() as session:
                return session.get(User, self.user_id)

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_current_user
        self.client = TestClient(app)

    def test_video_task_stores_quality_plan(self) -> None:
        response = self.client.post(f"/api/projects/{self.project_id}/storyboards/{self.storyboard_id}/video-tasks")

        self.assertEqual(response.status_code, 200, response.text)
        with self.SessionLocal() as session:
            task = session.query(VideoTask).one()
            progress = json_loads_object(task.progress_json)
            quality_plan = progress["video_quality_plan"]
            self.assertEqual(quality_plan["source_mode"], "user_brief")
            self.assertEqual(quality_plan["shot_count"], 1)
            self.assertEqual(quality_plan["structure"]["opening"], "镜头 1 建立情境。")
            self.assertEqual(quality_plan["shots"][0]["shot_no"], 1)
            self.assertEqual(quality_plan["shots"][0]["purpose"], "雨夜街口出现一束光。")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the failing quality plan test**

Run:

```powershell
python -m unittest tests.test_video_quality_plan_result
```

Expected: FAIL with `KeyError: 'video_quality_plan'`.

- [ ] **Step 3: Implement `VideoQualityService`**

Create `app/video_quality_service.py`:

```python
from __future__ import annotations

from typing import Any

from .json_utils import ensure_list, json_loads_object
from .models import Storyboard, VideoTask


class VideoQualityService:
    def build_quality_plan(self, storyboard: Storyboard) -> dict[str, Any]:
        shots = sorted(storyboard.shots, key=lambda item: item.shot_no)
        first_meta = json_loads_object(shots[0].meta_json) if shots else {}
        source_trace = first_meta.get("source_trace") if isinstance(first_meta.get("source_trace"), dict) else {}
        source_mode = str(first_meta.get("source_mode") or source_trace.get("source_mode") or "novel_chapters")
        planned_shots = []
        for shot in shots:
            meta = json_loads_object(shot.meta_json)
            audio_script = meta.get("audio_script") if isinstance(meta.get("audio_script"), dict) else {}
            planned_shots.append(
                {
                    "shot_no": shot.shot_no,
                    "purpose": shot.narration_text.strip() or shot.visual_prompt.strip(),
                    "visual_continuity": ensure_list((meta.get("continuity") or {}).get("continuity_constraints") if isinstance(meta.get("continuity"), dict) else []),
                    "subtitle_text": str(audio_script.get("subtitle_text") or "").strip(),
                    "duration_seconds": shot.duration_seconds,
                }
            )
        return {
            "source_mode": source_mode,
            "source_trace": source_trace,
            "shot_count": len(planned_shots),
            "structure": {
                "opening": "镜头 1 建立情境。" if planned_shots else "",
                "development": "中段镜头推进变化。" if len(planned_shots) >= 2 else "",
                "ending": f"镜头 {planned_shots[-1]['shot_no']} 收束情绪或动作。" if planned_shots else "",
            },
            "shots": planned_shots,
            "quality_dimensions": ["short_film_structure", "visual_stability", "content_consistency"],
        }

    def build_result(
        self,
        *,
        task: VideoTask,
        status: str,
        message: str,
    ) -> dict[str, Any]:
        progress = json_loads_object(task.progress_json)
        plan = progress.get("video_quality_plan") if isinstance(progress.get("video_quality_plan"), dict) else {}
        passed = status == "completed" and bool(task.output_uri)
        return {
            "status": "passed" if passed else "failed",
            "message": message,
            "checked_against_plan": bool(plan),
            "short_film_structure": "passed" if passed else "requires_manual_review",
            "visual_stability": "requires_manual_review",
            "content_consistency": "requires_manual_review",
        }
```

- [ ] **Step 4: Store quality plan when creating a video task**

In `app/api_routes_longform.py`, import:

```python
from .video_quality_service import VideoQualityService
```

Inside `create_video_task()`, replace the existing `task = VideoTask(...)` block:

```python
        task = VideoTask(
            project_id=project.id,
            storyboard=storyboard,
            task_status="queued",
            output_uri="",
            progress_json=service.task_progress_json(storyboard=storyboard),
            error_message="",
        )
```

with:

```python
        progress = json_loads_object(service.task_progress_json(storyboard=storyboard))
        progress["video_quality_plan"] = VideoQualityService().build_quality_plan(storyboard)
        task = VideoTask(
            project_id=project.id,
            storyboard=storyboard,
            task_status="queued",
            output_uri="",
            progress_json=json_dumps(progress),
            error_message="",
        )
```

- [ ] **Step 5: Expose quality plan in video task output progress**

No code change is expected in `app/api_support_longform.py` for this step because `_video_task_out()` already returns parsed `task.progress_json` as `progress`. Verify the existing function still contains this shape:

```python
    progress = json_loads_object(task.progress_json)
    return VideoTaskOut(
        ...
        progress=progress,
        ...
    )
```

- [ ] **Step 6: Run quality plan and video gate tests**

Run:

```powershell
python -m unittest tests.test_video_quality_plan_result tests.test_video_preflight_quality_gates tests.test_image_first_video_gate
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add app/video_quality_service.py app/api_routes_longform.py app/api_support_longform.py tests/test_video_quality_plan_result.py
git commit -m "feat: create video quality plans"
```

### Task 4: Video Quality Result On Render Completion Or Failure

**Files:**
- Modify: `app/video_render_service.py`
- Modify: `app/video_quality_service.py`
- Test: `tests/test_video_quality_plan_result.py`

- [ ] **Step 1: Extend the failing test for completion result**

Append this test method to `VideoQualityPlanResultTests`:

```python
    def test_video_quality_result_marks_completed_output_as_passed(self) -> None:
        from app.json_utils import json_dumps
        from app.video_quality_service import VideoQualityService

        with self.SessionLocal() as session:
            storyboard = session.get(Storyboard, self.storyboard_id)
            task = VideoTask(
                project_id=self.project_id,
                storyboard=storyboard,
                task_status="completed",
                output_uri="output/video_tasks/1/final.mp4",
                progress_json=json_dumps({"video_quality_plan": VideoQualityService().build_quality_plan(storyboard)}),
                error_message="",
            )
            session.add(task)
            session.flush()

            result = VideoQualityService().build_result(task=task, status="completed", message="视频生成完成。")

            self.assertEqual(result["status"], "passed")
            self.assertTrue(result["checked_against_plan"])
            self.assertEqual(result["short_film_structure"], "passed")
```

- [ ] **Step 2: Run the quality result unit test**

Run:

```powershell
python -m unittest tests.test_video_quality_plan_result
```

Expected: PASS if Task 3 already added `build_result()`. If it fails, fix `build_result()` exactly as shown in Task 3 Step 3.

- [ ] **Step 3: Record result in render success path**

In `app/video_render_service.py`, import:

```python
from .video_quality_service import VideoQualityService
```

Find the path that marks `task.task_status = "completed"` and sets `task.output_uri`. Immediately after those assignments, add:

```python
        progress = json_loads_object(task.progress_json)
        progress["video_quality_result"] = VideoQualityService().build_result(
            task=task,
            status="completed",
            message="视频生成完成。",
        )
        task.progress_json = json_dumps(progress)
```

- [ ] **Step 4: Record result in render failure path**

Find the path that marks `task.task_status = "failed"` and sets `task.error_message`. Immediately after those assignments, add:

```python
        progress = json_loads_object(task.progress_json)
        progress["video_quality_result"] = VideoQualityService().build_result(
            task=task,
            status="failed",
            message=task.error_message or "视频生成失败。",
        )
        task.progress_json = json_dumps(progress)
```

- [ ] **Step 5: Expose result in video task output progress**

No code change is expected in `app/api_support_longform.py` for this step because `_video_task_out()` already returns parsed `task.progress_json` as `progress`. Verify `video_quality_result` appears in the API response after it is written to `task.progress_json`.


- [ ] **Step 6: Run render and quality tests**

Run:

```powershell
python -m unittest tests.test_video_quality_plan_result tests.test_image_first_video_gate tests.test_video_preflight_quality_gates
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add app/video_render_service.py app/video_quality_service.py app/api_support_longform.py tests/test_video_quality_plan_result.py
git commit -m "feat: record video quality results"
```

### Task 5: Brief Source Frontend Wiring

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/stores/workbench.ts`
- Test: `tests/test_frontend_image_first_video_wiring.py`

- [ ] **Step 1: Extend the frontend wiring test**

In `tests/test_frontend_image_first_video_wiring.py`, update or add assertions:

```python
        self.assertIn('"user_brief"', types_source)
        self.assertIn("createBriefStoryboard", store_source)
        self.assertIn('source_mode: "user_brief"', store_source)
```

- [ ] **Step 2: Run the failing frontend wiring test**

Run:

```powershell
python -m unittest tests.test_frontend_image_first_video_wiring
```

Expected: FAIL because the store does not yet expose `createBriefStoryboard`.

- [ ] **Step 3: Add brief source payload type**

In `frontend/src/types.ts`, make sure `CreateStoryboardPayload` includes:

```ts
  source_mode?: "novel_chapters" | "image_first_reference" | "existing_images" | "user_brief";
  reference_video_brief?: string;
```

- [ ] **Step 4: Add store wrapper**

In `frontend/src/stores/workbench.ts`, next to the existing storyboard creation wrapper, add:

```ts
  async function createBriefStoryboard(payload: {
    project_id: number;
    title?: string;
    reference_video_brief: string;
  }) {
    return createStoryboard({
      project_id: payload.project_id,
      source_mode: "user_brief",
      novel_chapter_ids: [],
      title: payload.title ?? "",
      reference_video_brief: payload.reference_video_brief,
      key_image_strategy: "generate_first_frames",
      reference_image_asset_ids: [],
    });
  }
```

Add `createBriefStoryboard` to the returned store object.

- [ ] **Step 5: Run frontend source test and build**

Run:

```powershell
python -m unittest tests.test_frontend_image_first_video_wiring
```

Expected: PASS.

Run:

```powershell
npm run build
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add frontend/src/types.ts frontend/src/stores/workbench.ts tests/test_frontend_image_first_video_wiring.py
git commit -m "feat: wire brief sourced storyboards"
```

### Task 6: Final Regression

**Files:**
- Verify only.

- [ ] **Step 1: Run targeted backend regression**

Run:

```powershell
python -m unittest tests.test_user_brief_storyboard_source tests.test_storyboard_source_trace tests.test_video_quality_plan_result tests.test_image_first_reference_storyboard tests.test_image_first_video_gate tests.test_video_preflight_quality_gates tests.test_storyboard_shot_continuity
```

Expected: PASS.

- [ ] **Step 2: Run existing broader regression**

Run:

```powershell
python -m unittest
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

Run:

```powershell
npm run build
```

Expected: PASS.

- [ ] **Step 4: Commit any final fixes**

If Step 1, Step 2, or Step 3 revealed a real defect, commit the focused fix:

```powershell
git add -A
git commit -m "fix: stabilize creative domain foundation"
```

If no files changed after verification, do not create an empty commit.

---

## Self-Review Notes

Spec coverage:

- Multi-source workflow: Tasks 1, 2, and 5.
- Storyboard independence and source trace: Task 2.
- Asset references and first-frame quality gates: Task 3 uses existing gates; full asset domain deepening remains a later plan.
- Video quality plan/result: Tasks 3 and 4.
- Task runtime normalization: not implemented in this foundation plan beyond quality metadata in `progress_json`; create a separate task-runtime plan after this slice.
- Frontend workflow: Task 5 provides a brief-source wrapper but not a full UI redesign.

This plan intentionally does not implement every OpenSpec task. It produces the first working, testable slice needed before deeper asset, task runtime, and UI work.
