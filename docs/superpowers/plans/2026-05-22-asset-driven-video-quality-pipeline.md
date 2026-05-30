# Asset-Driven Video Quality Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the video workflow from text-prompt-driven generation into an asset-driven pipeline where uploaded reference images, confirmed visual masters, shot dependency metadata, and quality gates create real continuity from finalized novel chapters to video.

**Architecture:** Keep the existing longform and Jimeng provider stack. Add the minimum missing contracts around uploaded reference assets, AI-assisted asset mapping, structured shot continuity metadata, and preflight blocking. The first version does not add web image search, provider switching, or full automatic visual scoring; it makes the existing stages inherit confirmed assets and fail visibly when required links are missing.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic contracts, existing `output/` static mount, Pinia/Vue workspace UI, existing Jimeng image/video clients, existing OpenAI LLM utility path for classification and storyboard metadata.

---

## Execution Progress

Updated on 2026-05-23:

- [x] Task 1 completed in commit `2dd8bcd` (`feat: upload reference image assets`).
- [x] Task 2 completed in commit `cb0a878` (`feat: classify and confirm reference assets`).
- [x] Task 3 completed in commit `c31d303` (`feat: drive turnarounds from confirmed references`).
- [x] Task 4 completed in commit `0a97245` (`feat: persist storyboard continuity metadata`).
- [x] Task 5 completed in commit `2631808` (`fix: resolve shot character names to locked turnarounds`).
- [x] Task 6 completed in commit `e0dc43c` (`feat: block video tasks on missing visual gates`).
- [ ] Task 7 and later tasks remain pending.

Verification run during execution:

- `python -m unittest tests.test_reference_asset_upload_api`
- `python -m unittest tests.test_reference_asset_service tests.test_reference_asset_api`
- `python -m unittest tests.test_reference_asset_classifier tests.test_reference_asset_api tests.test_reference_asset_service`
- `python -m unittest tests.test_turnaround_uses_reference_assets tests.test_visual_asset_candidates tests.test_visual_asset_locked_references`
- `python -m unittest tests.test_storyboard_shot_continuity tests.test_longform_artifact_delete_api`
- `python -m unittest tests.test_video_preflight_quality_gates`
- `python -m unittest tests.test_longform_artifact_delete_api tests.test_visual_asset_locked_references`
- `python -m compileall app tests`

Code quality check was performed after each completed task slice: failures are surfaced through explicit HTTP errors/events or tests, metadata fallbacks are observable, and no new misleading comments were added.

---

## Scope And Current Code Facts

Current flow:

- Series plan and draft generation already have some hard-constraint support through context packs and violation checks.
- `ReferenceImageAsset` exists, but it is URL-oriented: `remote_url`, `source_page`, `mapped_character_name`, and `status`.
- No backend upload endpoint exists for reference images.
- `VisualAssetService.generate_character_turnaround()` generates from text prompt only and does not pass approved reference images to Jimeng.
- `StoryboardService.generate_storyboard()` asks for `character_refs: ["角色名"]`, but `VisualAssetService._shot_character_ids()` only resolves numeric IDs or `character_card_id`.
- `generate_shot_first_frame()` passes locked turnaround references when it can resolve them, but automatic storyboard output usually cannot resolve them.
- `create_video_task()` and `prepare_video_production()` allow video tasks without locked turnarounds, validated shot continuity, or approved/locked first frames.
- `VideoRenderService` silently falls back to text-to-video when a first-frame asset is missing or not resolvable.
- Frontend video flow is duplicated between `VideoStagePage`, `VideoCreatePage`, and repeated event wiring in `App.vue`.

User-confirmed product direction:

- Reference inheritance mode must be project-level configurable; different projects may use different levels of original-work inheritance.
- First quality push should keep both novel and video workflow, but focus on real inheritance and quality gates rather than more generation features.
- First visual asset source should be user upload, not web search.
- Uploaded reference images should be AI-classified and AI-mapped first, then confirmed by the user.
- Image/video generation should not rely on text prompt as the main source. Text prompt is only a constraint; confirmed images and visual masters should drive generation.
- Continuity matters most: adjacent shots must keep character and scene identity, and continuation/camera-move shots should inherit the previous shot's ending frame.

## Non-Goals For This Plan

- Do not switch all image generation to OpenAI.
- Do not remove Jimeng.
- Do not build web image search in this version.
- Do not build a broad provider plugin system.
- Do not build full automatic CLIP/vision similarity scoring in this version.
- Do not rewrite all frontend pages.
- Do not require perfect automatic quality judgment before users can manually confirm.

Simplicity check: this plan is intentionally narrower than a full production asset system. It solves the confirmed present problem: current pipeline links are fake or soft. It drops web search, full auto scoring, and provider abstraction because uploaded assets plus confirmation gates are enough to create real inheritance for the next implementation slice.

## Target Data Flow

The target workflow is:

1. User locks or confirms novel plan and finished chapters.
2. User uploads reference images.
3. AI classifies each upload as `character_reference`, `scene_reference`, `style_reference`, `composition_reference`, or `unknown`.
4. AI recommends mapping to existing character cards or project-level visual style. User confirms or changes the mapping.
5. Confirmed reference images become `approved` visual inputs.
6. Character turnaround generation uses approved mapped reference images, not text only.
7. AI recommends the best turnaround candidate; user locks one.
8. Storyboard generation outputs structured shot continuity metadata and character IDs, not just names.
9. First-frame generation for new shots uses locked character masters and uploaded scene/style references.
10. Continuation and camera-move shots inherit the previous shot's ending frame as their first-frame source.
11. Video task preflight blocks if required visual links are missing.
12. Video rendering fails visibly instead of silently falling back to text-to-video when image-to-video is required.

## File Structure

Create:

- `app/reference_asset_classifier.py`  
  Classifies uploaded reference images and recommends mappings using the existing OpenAI LLM utility path. First implementation may accept metadata-only inputs and store deterministic fallback results in tests.

- `tests/test_reference_asset_upload_api.py`  
  Covers upload endpoint, output path creation, local public URL, and pending classification status.

- `tests/test_reference_asset_classifier.py`  
  Covers classification result normalization and mapping recommendation handling.

- `tests/test_turnaround_uses_reference_assets.py`  
  Covers approved mapped references being passed into `JimengImageClient.submit_text_to_image()`.

- `tests/test_storyboard_shot_continuity.py`  
  Covers storyboard output containing `character_card_id`, shot continuity metadata, and safe fallback validation failure.

- `tests/test_video_preflight_quality_gates.py`  
  Covers blocking video task creation when required turnarounds, first frames, or continuity links are missing.

Modify:

- `app/models.py`  
  Extend `ReferenceImageAsset` only as needed for local upload support and AI mapping metadata. Prefer adding nullable/defaulted fields over replacing current URL fields.

- `app/db.py`  
  Add migration-safe DDL for new `reference_image_assets` fields.

- `app/contracts.py`  
  Add upload/classification outputs and extend storyboard shot outputs with `continuity` metadata.

- `app/reference_asset_service.py`  
  Add upload registration, local URL hash handling, classification status updates, and mapping confirmation helpers.

- `app/api_routes_projects.py`  
  Add upload endpoint and classify/remap endpoints for reference images.

- `app/visual_asset_service.py`  
  Pass approved reference image URLs into turnaround generation. Resolve shot character names to IDs or require structured refs. Add metadata describing which references were used.

- `app/storyboard_service.py`  
  Update storyboard generation prompt to return structured `character_refs` and `continuity`.

- `app/storyboard_job_service.py`  
  Validate and persist structured shot metadata. Reject poor structured output instead of accepting arbitrary dicts.

- `app/api_routes_longform.py`  
  Add preflight gates before video task creation and before automatic preflight task creation.

- `app/video_render_service.py`  
  Require first-frame/i2v for shots marked `new`, `continuation`, or `camera_move` according to metadata. Do not silently fall back to text-to-video unless shot metadata explicitly allows it.

- `frontend/src/types.ts`  
  Add reference upload, classification, and shot continuity types.

- `frontend/src/api.ts`  
  Add multipart upload, classify, and remap calls.

- `frontend/src/stores/workbench.ts`  
  Add reference upload/classification state actions.

- `frontend/src/components/workspace/LongformPipelinePanel.vue`  
  Add uploaded reference asset review UI and display continuity/preflight gates.

- `frontend/src/App.vue`, `frontend/src/components/workspace/VideoCreatePage.vue`, `frontend/src/components/workspace/VideoStagePage.vue`  
  Reduce duplicate video event wiring only after backend gates are in place.

---

### Task 1: Add Uploadable Reference Asset Records

**Files:**
- Modify: `app/models.py`
- Modify: `app/db.py`
- Modify: `app/contracts.py`
- Modify: `app/reference_asset_service.py`
- Modify: `app/api_routes_projects.py`
- Test: `tests/test_reference_asset_upload_api.py`

- [x] **Step 1: Write the failing upload API test**

Add `tests/test_reference_asset_upload_api.py`:

```python
from __future__ import annotations

import io
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import create_app
from app.auth import issue_token
from app.db import Base, get_db
from app.json_utils import json_loads_object
from app.models import Project, ReferenceImageAsset, User


class ReferenceAssetUploadApiTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(bind=engine, future=True)
        app = create_app()

        def override_db():
            with self.SessionLocal() as session:
                yield session

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)
        with self.SessionLocal() as session:
            user = User(email="upload@example.com", display_name="上传用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="资产驱动项目", genre="青春")
            session.add_all([user, project])
            session.commit()
            self.user_id = user.id
            self.project_id = project.id
        self.token = issue_token(self.user_id)

    def test_upload_reference_image_creates_candidate_with_public_output_url(self) -> None:
        response = self.client.post(
            f"/api/projects/{self.project_id}/reference-images/upload",
            headers={"Authorization": f"Bearer {self.token}"},
            files={"file": ("hina.png", io.BytesIO(b"fake-image-bytes"), "image/png")},
            data={"asset_kind": "character_reference"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["asset_kind"], "character_reference")
        self.assertEqual(payload["provider"], "upload")
        self.assertEqual(payload["status"], "candidate")
        self.assertTrue(payload["remote_url"].startswith("/output/projects/"))
        self.assertEqual(payload["source_page"], "upload:hina.png")

        with self.SessionLocal() as session:
            asset = session.query(ReferenceImageAsset).one()
            self.assertEqual(asset.project_id, self.project_id)
            self.assertEqual(asset.provider, "upload")
            self.assertEqual(asset.asset_kind, "character_reference")
            meta = json_loads_object(asset.meta_json)
            self.assertEqual(meta["classification_status"], "pending")
            self.assertEqual(meta["original_filename"], "hina.png")


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run the upload test to verify it fails**

Run:

```bash
python -m unittest tests.test_reference_asset_upload_api
```

Expected: FAIL because `/reference-images/upload` does not exist and `ReferenceImageAsset.meta_json` does not exist.

- [x] **Step 3: Add model and contract fields**

In `app/models.py`, add to `ReferenceImageAsset`:

```python
    meta_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
```

Add helper property if useful:

```python
    @property
    def meta(self) -> dict[str, Any]:
        try:
            value = json.loads(self.meta_json or "{}")
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    @meta.setter
    def meta(self, value: dict[str, Any]) -> None:
        self.meta_json = json.dumps(value if isinstance(value, dict) else {}, ensure_ascii=False)
```

In `app/contracts.py`, extend `ReferenceImageAssetOut`:

```python
    meta: dict[str, Any] = {}
```

Do not expose raw `remote_url_hash`.

- [x] **Step 4: Add migration-safe DDL**

In `app/db.py`, add migration logic near existing `reference_image_assets` migration:

```python
    if "meta_json" not in columns:
        connection.execute(text("ALTER TABLE reference_image_assets ADD COLUMN meta_json TEXT NOT NULL DEFAULT ('{}')"))
```

Keep SQLite test compatibility by relying on SQLAlchemy `Base.metadata.create_all()` for in-memory tests.

- [x] **Step 5: Add service upload registration**

In `app/reference_asset_service.py`, add:

```python
    def register_uploaded_asset(
        self,
        db: Session,
        *,
        project: Project,
        public_url: str,
        original_filename: str,
        asset_kind: str,
        content_type: str,
        byte_size: int,
    ) -> ReferenceImageAsset:
        normalized_url = public_url.strip()
        if not normalized_url:
            raise ValueError("Uploaded reference asset requires a public URL")
        existing = db.scalar(
            select(ReferenceImageAsset).where(
                ReferenceImageAsset.project_id == project.id,
                ReferenceImageAsset.remote_url_hash == _remote_url_hash(normalized_url),
            )
        )
        if existing is not None:
            return existing
        asset = ReferenceImageAsset(
            project=project,
            source_work=str(project.reference_work or project.title or "uploaded").strip(),
            asset_kind=asset_kind.strip() or "character_reference",
            remote_url=normalized_url,
            remote_url_hash=_remote_url_hash(normalized_url),
            provider="upload",
            source_page=f"upload:{original_filename.strip() or 'reference'}",
            mapped_character_name="",
            status="candidate",
            meta_json=json_dumps(
                {
                    "classification_status": "pending",
                    "original_filename": original_filename,
                    "content_type": content_type,
                    "byte_size": byte_size,
                }
            ),
        )
        db.add(asset)
        db.flush()
        return asset
```

Import `json_dumps` and `Path` only if needed.

- [x] **Step 6: Add FastAPI upload endpoint**

In `app/api_routes_projects.py`, import `UploadFile` and `File`:

```python
from fastapi import Depends, File, Form, HTTPException, UploadFile
```

Add endpoint near existing reference image routes:

```python
    @router.post("/api/projects/{project_id}/reference-images/upload", response_model=ReferenceImageAssetOut)
    def upload_reference_image(
        project_id: int,
        asset_kind: str = Form(default="character_reference"),
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ReferenceImageAssetOut:
        project = _project_or_404(db, current_user.id, project_id)
        content_type = (file.content_type or "").lower()
        if content_type not in {"image/png", "image/jpeg", "image/webp"}:
            raise HTTPException(status_code=422, detail="只支持 PNG、JPEG 或 WebP 参考图。")
        raw = file.file.read()
        if not raw:
            raise HTTPException(status_code=422, detail="上传文件为空。")
        if len(raw) > 12 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="参考图不能超过 12MB。")
        safe_ext = ".png" if content_type == "image/png" else ".jpg" if content_type == "image/jpeg" else ".webp"
        project_dir = f"{project.id:04d}-{_path_slug(project.title)}"
        asset_dir = settings.output_dir / "projects" / project_dir / "reference_assets"
        asset_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(raw).hexdigest()
        path = asset_dir / f"{digest[:16]}{safe_ext}"
        path.write_bytes(raw)
        public_url = _public_asset_url(str(path))
        asset = reference_asset_service.register_uploaded_asset(
            db,
            project=project,
            public_url=public_url,
            original_filename=file.filename or "reference",
            asset_kind=asset_kind,
            content_type=content_type,
            byte_size=len(raw),
        )
        db.commit()
        db.refresh(asset)
        return ReferenceImageAssetOut.model_validate(asset)
```

Add helper `_path_slug()` if no local helper exists in this module, matching the existing path slug behavior:

```python
def _path_slug(value: str, *, fallback: str = "untitled") -> str:
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", value.strip())
    text = re.sub(r"\s+", "-", text).strip(".- ")
    return (text or fallback)[:80]
```

Import `hashlib`, `re`, and `_public_asset_url` from `api_support_longform`.

- [x] **Step 7: Update `ReferenceImageAssetOut` serialization**

If `meta` property is added on model, `model_validate()` should work. If not, build `ReferenceImageAssetOut(...)` manually in route helpers.

- [x] **Step 8: Run the upload test to verify it passes**

Run:

```bash
python -m unittest tests.test_reference_asset_upload_api
```

Expected: PASS.

- [x] **Step 9: Run existing reference asset tests**

Run:

```bash
python -m unittest tests.test_reference_asset_service tests.test_reference_asset_api
```

Expected: PASS.

- [x] **Step 10: Commit**

```bash
git add app/models.py app/db.py app/contracts.py app/reference_asset_service.py app/api_routes_projects.py tests/test_reference_asset_upload_api.py
git commit -m "feat: upload reference image assets"
```

---

### Task 2: Add AI-Assisted Classification And User Confirmation

**Files:**
- Create: `app/reference_asset_classifier.py`
- Modify: `app/reference_asset_service.py`
- Modify: `app/api_routes_projects.py`
- Modify: `app/contracts.py`
- Test: `tests/test_reference_asset_classifier.py`
- Test: `tests/test_reference_asset_api.py`

- [x] **Step 1: Write failing classifier normalization tests**

Add `tests/test_reference_asset_classifier.py`:

```python
from __future__ import annotations

import unittest

from app.reference_asset_classifier import normalize_reference_classification


class ReferenceAssetClassifierTests(unittest.TestCase):
    def test_normalize_reference_classification_keeps_supported_kind_and_mapping(self) -> None:
        result = normalize_reference_classification(
            {
                "asset_kind": "character_reference",
                "mapped_character_name": "阳菜",
                "confidence": 0.91,
                "reason": "图中是少女角色设定图",
                "tags": ["校服", "短发"],
            },
            known_character_names=["阳菜", "帆高"],
        )

        self.assertEqual(result["asset_kind"], "character_reference")
        self.assertEqual(result["mapped_character_name"], "阳菜")
        self.assertEqual(result["confidence"], 0.91)
        self.assertEqual(result["classification_status"], "suggested")

    def test_normalize_reference_classification_drops_unknown_character_mapping(self) -> None:
        result = normalize_reference_classification(
            {
                "asset_kind": "character_reference",
                "mapped_character_name": "未知角色",
                "confidence": "0.8",
                "reason": "不确定",
            },
            known_character_names=["阳菜"],
        )

        self.assertEqual(result["asset_kind"], "character_reference")
        self.assertEqual(result["mapped_character_name"], "")
        self.assertEqual(result["classification_status"], "needs_review")


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run classifier test to verify it fails**

Run:

```bash
python -m unittest tests.test_reference_asset_classifier
```

Expected: FAIL because `app.reference_asset_classifier` does not exist.

- [x] **Step 3: Implement normalization helper**

Create `app/reference_asset_classifier.py`:

```python
from __future__ import annotations

from typing import Any

SUPPORTED_ASSET_KINDS = {
    "character_reference",
    "scene_reference",
    "style_reference",
    "composition_reference",
    "unknown",
}


def normalize_reference_classification(raw: dict[str, Any], *, known_character_names: list[str]) -> dict[str, Any]:
    kind = str(raw.get("asset_kind") or "unknown").strip()
    if kind not in SUPPORTED_ASSET_KINDS:
        kind = "unknown"
    mapped = str(raw.get("mapped_character_name") or "").strip()
    if mapped and mapped not in set(known_character_names):
        mapped = ""
    try:
        confidence = float(raw.get("confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(confidence, 1.0))
    status = "suggested" if kind != "unknown" and (kind != "character_reference" or mapped) else "needs_review"
    tags = [str(item).strip() for item in raw.get("tags", []) if str(item).strip()] if isinstance(raw.get("tags"), list) else []
    return {
        "asset_kind": kind,
        "mapped_character_name": mapped,
        "confidence": confidence,
        "reason": str(raw.get("reason") or "").strip(),
        "tags": tags,
        "classification_status": status,
    }
```

- [x] **Step 4: Run classifier test to verify it passes**

Run:

```bash
python -m unittest tests.test_reference_asset_classifier
```

Expected: PASS.

- [x] **Step 5: Write API tests for confirmation**

Extend `tests/test_reference_asset_api.py` with a test that:

1. Creates a candidate `ReferenceImageAsset`.
2. Sends `PUT /api/projects/{project_id}/reference-images/{asset_id}` with:

```json
{"status":"approved","mapped_character_name":"阳菜","asset_kind":"character_reference","meta":{"classification_status":"confirmed"}}
```

3. Asserts the asset status is `approved`, kind is `character_reference`, mapped name is `阳菜`, and profile sync picks it up.

Expected initial failure: contract does not accept `asset_kind` and `meta`.

- [x] **Step 6: Extend update contract**

In `app/contracts.py`, update `ReferenceImageAssetUpdateRequest`:

```python
class ReferenceImageAssetUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(candidate|approved|rejected)$")
    mapped_character_name: str = Field(default="", max_length=120)
    asset_kind: str | None = Field(default=None, max_length=80)
    meta: dict[str, Any] | None = None
```

- [x] **Step 7: Extend service update**

In `ReferenceAssetService.update_asset_status()`, accept optional `asset_kind` and `meta`:

```python
        if asset_kind is not None and asset_kind.strip():
            asset.asset_kind = asset_kind.strip()
        if meta is not None:
            existing_meta = json_loads_object(asset.meta_json)
            asset.meta_json = json_dumps({**existing_meta, **meta})
```

When status or mapped character changes, call `CharacterReferenceProfileService().ensure_profiles(db, project)` after update in the route, so approved references appear in `visual_reference_asset_ids`.

- [x] **Step 8: Add classification endpoint as metadata-only first**

Add contract:

```python
class ReferenceImageClassifyRequest(BaseModel):
    hints: dict[str, Any] = {}
```

Add route:

```python
    @router.post("/api/projects/{project_id}/reference-images/{asset_id}/classify", response_model=ReferenceImageAssetOut)
    def classify_reference_image(
        project_id: int,
        asset_id: int,
        payload: ReferenceImageClassifyRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ReferenceImageAssetOut:
        project = _project_or_404(db, current_user.id, project_id)
        asset = db.scalar(
            select(ReferenceImageAsset).where(
                ReferenceImageAsset.project_id == project.id,
                ReferenceImageAsset.id == asset_id,
            )
        )
        if asset is None:
            raise HTTPException(status_code=404, detail="参考图不存在。")
        known_names = [card.name for card in project.character_cards if card.deleted_at is None]
        normalized = normalize_reference_classification(payload.hints, known_character_names=known_names)
        asset.asset_kind = normalized["asset_kind"]
        asset.mapped_character_name = normalized["mapped_character_name"]
        existing_meta = json_loads_object(asset.meta_json)
        asset.meta_json = json_dumps({**existing_meta, **normalized})
        db.commit()
        db.refresh(asset)
        return ReferenceImageAssetOut.model_validate(asset)
```

First implementation can classify from provided hints and project character names without computer vision:

```python
        raw = payload.hints
        known_names = [card.name for card in project.character_cards if card.deleted_at is None]
        normalized = normalize_reference_classification(raw, known_character_names=known_names)
```

Store normalized fields into `asset.asset_kind`, `asset.mapped_character_name`, and `asset.meta_json`.

This is deliberately simple. A later step can replace `raw = payload.hints` with actual vision-model classification without changing the confirmation contract.

- [x] **Step 9: Run reference asset tests**

Run:

```bash
python -m unittest tests.test_reference_asset_api tests.test_reference_asset_service tests.test_reference_asset_classifier
```

Expected: PASS.

- [x] **Step 10: Commit**

```bash
git add app/reference_asset_classifier.py app/reference_asset_service.py app/api_routes_projects.py app/contracts.py tests/test_reference_asset_classifier.py tests/test_reference_asset_api.py
git commit -m "feat: classify and confirm reference assets"
```

---

### Task 3: Feed Approved Reference Assets Into Character Turnaround Generation

**Files:**
- Modify: `app/visual_asset_service.py`
- Test: `tests/test_turnaround_uses_reference_assets.py`
- Update: `tests/test_visual_asset_candidates.py`

- [x] **Step 1: Write failing turnaround reference test**

Create `tests/test_turnaround_uses_reference_assets.py`:

```python
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.json_utils import json_dumps, json_loads_object
from app.models import CharacterCard, Project, ReferenceImageAsset, User
from app.reference_asset_service import _remote_url_hash
from app.visual_asset_service import VisualAssetService


class CapturingJimengImageClient:
    calls: list[dict] = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs

    def submit_text_to_image(self, **kwargs):
        self.calls.append(kwargs)
        return "task-1", {"status": "submitted"}


class TurnaroundReferenceAssetTests(unittest.TestCase):
    def setUp(self) -> None:
        CapturingJimengImageClient.calls = []
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(bind=engine, future=True)
        self.settings = SimpleNamespace(
            jimeng_access_key="ak",
            jimeng_secret_key="sk",
            jimeng_endpoint="https://example.com",
            jimeng_region="cn",
            jimeng_service="image",
            jimeng_image_req_key="req",
            jimeng_image_width=1024,
            jimeng_image_height=1024,
            jimeng_poll_timeout_seconds=1,
        )

    def test_character_turnaround_uses_approved_reference_images_for_character(self) -> None:
        service = VisualAssetService(self.settings)
        with self.SessionLocal() as session, tempfile.TemporaryDirectory() as tmpdir:
            user = User(email="ref-turn@example.com", display_name="视觉用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="天空项目", genre="青春", reference_work="上传参考")
            character = CharacterCard(project=project, name="阳菜")
            session.add_all([project, character])
            session.flush()
            ref = ReferenceImageAsset(
                project=project,
                source_work="上传参考",
                asset_kind="character_reference",
                remote_url="/output/projects/0001/reference_assets/hina.png",
                remote_url_hash=_remote_url_hash("/output/projects/0001/reference_assets/hina.png"),
                provider="upload",
                source_page="upload:hina.png",
                mapped_character_name="阳菜",
                status="approved",
                meta_json=json_dumps({"classification_status": "confirmed"}),
            )
            session.add(ref)
            session.commit()

            with patch("app.visual_asset_service.JimengImageClient", CapturingJimengImageClient), patch.object(
                service, "_require_jimeng_image_config", return_value=None
            ), patch.object(
                service, "_wait_for_image_result", return_value=({"kind": "url", "value": "https://example.com/generated.png"}, {"status": "done"})
            ), patch.object(
                service, "_save_image_payload", return_value=None
            ), patch.object(
                service, "_write_provider_debug_sidecar", return_value=None
            ), patch.object(
                service, "_visual_output_dir", return_value=Path(tmpdir)
            ), patch.object(
                service, "_provider_debug_path", side_effect=lambda path: path.with_suffix(".provider.json")
            ):
                asset = service.generate_character_turnaround(db=session, project=project, character=character)

            self.assertEqual(CapturingJimengImageClient.calls[0]["reference_images"], [ref.remote_url])
            meta = json_loads_object(asset.meta_json)
            self.assertEqual(meta["visual_reference_asset_ids"], [ref.id])


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_turnaround_uses_reference_assets
```

Expected: FAIL because `generate_character_turnaround()` does not pass `reference_images`.

- [x] **Step 3: Add approved reference resolver**

In `app/visual_asset_service.py`, add:

```python
    def _approved_character_reference_assets(self, db: Session, *, project: Project, character: CharacterCard) -> list[ReferenceImageAsset]:
        return db.scalars(
            select(ReferenceImageAsset).where(
                ReferenceImageAsset.project_id == project.id,
                ReferenceImageAsset.status == "approved",
                ReferenceImageAsset.asset_kind == "character_reference",
                ReferenceImageAsset.mapped_character_name == character.name,
            )
        ).all()
```

- [x] **Step 4: Pass reference images into Jimeng**

Update `generate_character_turnaround()`:

```python
        reference_assets = self._approved_character_reference_assets(db, project=project, character=character)
        reference_images = [asset.remote_url for asset in reference_assets if asset.remote_url]
        task_id, submit_response = client.submit_text_to_image(
            prompt=prompt,
            width=self.settings.jimeng_image_width,
            height=self.settings.jimeng_image_height,
            reference_images=reference_images,
        )
```

Add metadata:

```python
                    "visual_reference_asset_ids": [asset.id for asset in reference_assets],
                    "visual_reference_image_count": len(reference_images),
```

- [x] **Step 5: Run turnaround tests**

Run:

```bash
python -m unittest tests.test_turnaround_uses_reference_assets tests.test_visual_asset_candidates tests.test_visual_asset_locked_references
```

Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add app/visual_asset_service.py tests/test_turnaround_uses_reference_assets.py tests/test_visual_asset_candidates.py
git commit -m "feat: drive turnarounds from confirmed references"
```

---

### Task 4: Make Storyboard Shots Carry Real Character IDs And Continuity Metadata

**Files:**
- Modify: `app/storyboard_service.py`
- Modify: `app/storyboard_job_service.py`
- Modify: `app/contracts.py`
- Modify: `frontend/src/types.ts`
- Test: `tests/test_storyboard_shot_continuity.py`

- [x] **Step 1: Write failing storyboard continuity tests**

Create `tests/test_storyboard_shot_continuity.py`:

```python
from __future__ import annotations

import json
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.json_utils import json_loads_object
from app.models import CharacterCard, Project, Storyboard, StoryboardShot, User
from app.storyboard_job_service import StoryboardJobService


class StoryboardShotContinuityTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(bind=engine, future=True)

    def test_replace_shots_persists_structured_character_refs_and_continuity(self) -> None:
        service = StoryboardJobService(settings=object())
        with self.SessionLocal() as session:
            user = User(email="shot@example.com", display_name="分镜用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="视频项目", genre="青春")
            character = CharacterCard(project=project, name="阳菜")
            storyboard = Storyboard(project=project, title="预告片", source_chapter_ids_json="[]")
            session.add_all([project, character, storyboard])
            session.flush()

            count = service._replace_shots(
                session,
                storyboard=storyboard,
                shots=[
                    {
                        "shot_no": 1,
                        "narration_text": "她抬头。",
                        "visual_prompt": "天台近景",
                        "character_refs": [{"character_card_id": character.id, "name": "阳菜"}],
                        "scene_refs": [{"name": "天台"}],
                        "continuity": {
                            "shot_type": "new",
                            "depends_on_shot_no": None,
                            "first_frame_source": "generated",
                            "requires_i2v": True,
                            "end_frame_usage": "feeds_next",
                            "continuity_constraints": ["保持校服和湿发"],
                        },
                        "duration_seconds": 4,
                    }
                ],
            )
            session.flush()
            shot = session.query(StoryboardShot).one()

            self.assertEqual(count, 1)
            self.assertEqual(json.loads(shot.character_refs_json)[0]["character_card_id"], character.id)
            meta = json_loads_object(shot.meta_json)
            self.assertEqual(meta["continuity"]["shot_type"], "new")
            self.assertTrue(meta["continuity"]["requires_i2v"])


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_storyboard_shot_continuity
```

Expected: FAIL because `_replace_shots()` does not persist `continuity`.

- [x] **Step 3: Extend storyboard generation prompt**

In `app/storyboard_service.py`, update JSON schema prompt to require structured character refs:

```json
"character_refs": [{"character_card_id": 1, "name": "角色名", "role": "角色在镜头中的作用"}],
"scene_refs": [{"name": "场景名", "role": "场景用途"}],
"continuity": {
  "shot_type": "new|continuation|camera_move|transition",
  "depends_on_shot_no": null,
  "first_frame_source": "generated|previous_last_frame",
  "requires_i2v": true,
  "end_frame_usage": "none|feeds_next",
  "camera_motion": "无|推进|横移|摇镜|拉远",
  "character_state_delta": "角色状态变化",
  "continuity_constraints": ["必须保持的角色、服装、场景和构图连续性"]
}
```

Include a compact character directory before chapter text:

```python
character_directory = [
    {"character_card_id": card.id, "name": card.name, "story_role": card.story_role}
    for card in project.character_cards
    if card.deleted_at is None
]
```

Add it to the prompt and explicitly require returned IDs to come from this list.

- [x] **Step 4: Add continuity normalization**

In `app/storyboard_job_service.py`, add:

```python
    def _normalize_continuity(self, value: Any, *, shot_no: int) -> dict[str, Any]:
        payload = value if isinstance(value, dict) else {}
        shot_type = str(payload.get("shot_type") or "new").strip()
        if shot_type not in {"new", "continuation", "camera_move", "transition"}:
            shot_type = "new"
        depends = payload.get("depends_on_shot_no")
        try:
            depends_on = int(depends) if depends is not None and str(depends).strip() else None
        except (TypeError, ValueError):
            depends_on = None
        first_frame_source = str(payload.get("first_frame_source") or "").strip()
        if first_frame_source not in {"generated", "previous_last_frame"}:
            first_frame_source = "previous_last_frame" if shot_type in {"continuation", "camera_move"} else "generated"
        if shot_type in {"continuation", "camera_move"} and depends_on is None and shot_no > 1:
            depends_on = shot_no - 1
        return {
            "shot_type": shot_type,
            "depends_on_shot_no": depends_on,
            "first_frame_source": first_frame_source,
            "requires_i2v": bool(payload.get("requires_i2v", True)),
            "end_frame_usage": str(payload.get("end_frame_usage") or "none").strip(),
            "camera_motion": str(payload.get("camera_motion") or "").strip(),
            "character_state_delta": str(payload.get("character_state_delta") or "").strip(),
            "continuity_constraints": [str(item).strip() for item in ensure_list(payload.get("continuity_constraints")) if str(item).strip()],
        }
```

- [x] **Step 5: Persist continuity in shot meta**

Update `_replace_shots()`:

```python
            shot_no = int(shot_payload.get("shot_no") or index)
            continuity = self._normalize_continuity(shot_payload.get("continuity"), shot_no=shot_no)
            db.add(
                StoryboardShot(
                    storyboard=storyboard,
                    shot_no=shot_no,
                    narration_text=str(shot_payload.get("narration_text") or "").strip(),
                    visual_prompt=str(shot_payload.get("visual_prompt") or "").strip(),
                    character_refs_json=json_dumps(ensure_list(shot_payload.get("character_refs"))),
                    scene_refs_json=json_dumps(ensure_list(shot_payload.get("scene_refs"))),
                    meta_json=json_dumps(
                        {
                            "audio_script": self._normalize_audio_script(shot_payload.get("audio_script")),
                            "continuity": continuity,
                        }
                    ),
                    duration_seconds=float(shot_payload.get("duration_seconds") or 4),
                    status="draft",
                )
            )
```

- [x] **Step 6: Extend output contract**

In `app/contracts.py`, add to `StoryboardShotOut`:

```python
    continuity: dict[str, Any] = {}
```

In `app/api_support_longform.py`, update `_storyboard_shot_out()` to include:

```python
meta = json_loads_object(shot.meta_json)
continuity=meta.get("continuity") if isinstance(meta.get("continuity"), dict) else {}
```

- [x] **Step 7: Extend frontend types**

In `frontend/src/types.ts`, add `continuity: Record<string, unknown>;` to `StoryboardShot`.

- [x] **Step 8: Run storyboard tests**

Run:

```bash
python -m unittest tests.test_storyboard_shot_continuity
```

Expected: PASS.

- [x] **Step 9: Run longform artifact tests**

Run:

```bash
python -m unittest tests.test_longform_artifact_delete_api
```

Expected: PASS.

- [x] **Step 10: Commit**

```bash
git add app/storyboard_service.py app/storyboard_job_service.py app/contracts.py app/api_support_longform.py frontend/src/types.ts tests/test_storyboard_shot_continuity.py
git commit -m "feat: persist storyboard continuity metadata"
```

---

### Task 5: Resolve Character Names To IDs For Existing And Manual Shots

**Files:**
- Modify: `app/visual_asset_service.py`
- Test: `tests/test_visual_asset_locked_references.py`

- [x] **Step 1: Write failing name-resolution test**

Extend `tests/test_visual_asset_locked_references.py`:

```python
    def test_locked_turnaround_references_resolve_character_name_refs(self) -> None:
        service = VisualAssetService(settings=object())
        with self.SessionLocal() as session:
            user = User(email="visual-name@example.com", display_name="视觉用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="天气之子续作", genre="现代都市")
            character = CharacterCard(project=project, name="阳菜")
            storyboard = Storyboard(project=project, title="预告片", source_chapter_ids_json="[]")
            shot = StoryboardShot(
                storyboard=storyboard,
                shot_no=1,
                narration_text="阳菜站在天台边。",
                visual_prompt="雨后的天台，阳菜回头。",
                character_refs_json=json_dumps(["阳菜"]),
                scene_refs_json="[]",
            )
            session.add_all([project, character, storyboard, shot])
            session.flush()
            locked = MediaAsset(
                project_id=project.id,
                asset_type="character_turnaround",
                uri="output/characters/hina/turnaround-v001.png",
                prompt="三视图",
                status="completed",
                meta_json=json_dumps({"character_card_id": character.id, "character_name": "阳菜", "locked": True}),
            )
            session.add(locked)
            session.commit()

            references = service.locked_turnaround_references(db=session, project=project, shot=shot)

            self.assertEqual(len(references), 1)
            self.assertEqual(references[0]["character_card_id"], character.id)
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_visual_asset_locked_references
```

Expected: FAIL because string name refs are ignored.

- [x] **Step 3: Implement name fallback**

Update `VisualAssetService.locked_turnaround_references()`:

```python
        character_ids = self._shot_character_ids(shot)
        if not character_ids:
            names = self._shot_character_names(shot)
            if names:
                cards = db.scalars(
                    select(CharacterCard).where(
                        CharacterCard.project_id == project.id,
                        CharacterCard.deleted_at.is_(None),
                        CharacterCard.name.in_(names),
                    )
                ).all()
                character_ids = [card.id for card in cards]
```

Add helper:

```python
    def _shot_character_names(self, shot: StoryboardShot) -> list[str]:
        names: list[str] = []
        for item in json_loads_list(shot.character_refs_json):
            if isinstance(item, dict):
                value = item.get("name") or item.get("character_name") or item.get("value")
            else:
                value = item
            name = str(value or "").strip()
            if name and name not in names and self._safe_int(name) is None:
                names.append(name)
        return names
```

- [x] **Step 4: Run visual reference tests**

Run:

```bash
python -m unittest tests.test_visual_asset_locked_references
```

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add app/visual_asset_service.py tests/test_visual_asset_locked_references.py
git commit -m "fix: resolve shot character names to locked turnarounds"
```

---

### Task 6: Add Video Preflight Quality Gates

**Files:**
- Modify: `app/api_routes_longform.py`
- Modify: `app/contracts.py`
- Test: `tests/test_video_preflight_quality_gates.py`

- [x] **Step 1: Write failing preflight gate tests**

Create `tests/test_video_preflight_quality_gates.py` with two tests:

```python
from __future__ import annotations

import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import create_app
from app.auth import issue_token
from app.db import Base, get_db
from app.json_utils import json_dumps
from app.models import CharacterCard, ContextPack, Project, Storyboard, StoryboardShot, User


class VideoPreflightQualityGateTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(bind=engine, future=True)
        app = create_app()

        def override_db():
            with self.SessionLocal() as session:
                yield session

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)
        with self.SessionLocal() as session:
            user = User(email="gate@example.com", display_name="门禁用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="门禁项目", genre="青春")
            character = CharacterCard(project=project, name="阳菜")
            context_pack = ContextPack(project=project, status="confirmed", version=1, resolved_inputs_json=json_dumps({"context_pack_id": 1}))
            storyboard = Storyboard(project=project, title="预告片", source_chapter_ids_json="[]", status="draft")
            shot = StoryboardShot(
                storyboard=storyboard,
                shot_no=1,
                narration_text="阳菜抬头。",
                visual_prompt="天台",
                character_refs_json=json_dumps([{"character_card_id": 1, "name": "阳菜"}]),
                scene_refs_json="[]",
                meta_json=json_dumps({"continuity": {"shot_type": "new", "first_frame_source": "generated", "requires_i2v": True}}),
                status="draft",
            )
            session.add_all([user, project, character, context_pack, storyboard, shot])
            session.commit()
            self.user_id = user.id
            self.project_id = project.id
            self.storyboard_id = storyboard.id
        self.token = issue_token(self.user_id)

    def test_create_video_task_blocks_when_character_turnaround_is_not_locked(self) -> None:
        response = self.client.post(
            f"/api/projects/{self.project_id}/storyboards/{self.storyboard_id}/video-tasks",
            headers={"Authorization": f"Bearer {self.token}"},
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("三视图", response.json()["detail"])

    def test_preflight_without_video_task_returns_gate_summary(self) -> None:
        response = self.client.post(
            f"/api/projects/{self.project_id}/storyboards/{self.storyboard_id}/video-production/preflight",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "generate_character_turnarounds": False,
                "generate_audio_scripts": False,
                "generate_dialogue_audio": False,
                "create_video_task": False,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        events = payload["storyboards"][0]["events"]
        self.assertTrue(any(event["event_type"] == "storyboard_preflight_blocked" for event in events))


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run gate tests to verify they fail**

Run:

```bash
python -m unittest tests.test_video_preflight_quality_gates
```

Expected: FAIL because video task creation does not enforce gates.

- [x] **Step 3: Add gate helper**

In `app/api_routes_longform.py`, add a helper near route-local helpers:

```python
def _video_quality_gate_failures(db: Session, project: Project, storyboard: Storyboard) -> list[str]:
    failures: list[str] = []
    visual_service = VisualAssetService(settings)
    for shot in sorted(storyboard.shots, key=lambda item: item.shot_no):
        refs = visual_service.locked_turnaround_references(db=db, project=project, shot=shot)
        character_refs = json_loads_list(shot.character_refs_json)
        if character_refs and not refs:
            failures.append(f"镜头 {shot.shot_no} 有角色引用，但没有可用的锁定三视图。")
        meta = json_loads_object(shot.meta_json)
        continuity = meta.get("continuity") if isinstance(meta.get("continuity"), dict) else {}
        requires_i2v = continuity.get("requires_i2v") is not False
        first_frame_source = str(continuity.get("first_frame_source") or "generated")
        if requires_i2v and first_frame_source == "generated":
            first_frame = db.scalar(
                select(MediaAsset).where(
                    MediaAsset.project_id == project.id,
                    MediaAsset.storyboard_id == storyboard.id,
                    MediaAsset.shot_id == shot.id,
                    MediaAsset.asset_type == "shot_first_frame",
                    MediaAsset.status == "completed",
                )
            )
            if first_frame is None:
                failures.append(f"镜头 {shot.shot_no} 需要首帧，但还没有完成的首帧素材。")
    return failures
```

This first version does not require every first frame to be locked. It only blocks missing required first frames and missing locked turnarounds for character shots. Lock requirement can be added after users see the flow.

- [x] **Step 4: Use gates in direct video task route**

Before creating a `VideoTask` in `create_video_task()`:

```python
        gate_failures = _video_quality_gate_failures(db, project, storyboard)
        if gate_failures:
            raise HTTPException(status_code=409, detail="视频生产前置检查未通过：" + "；".join(gate_failures[:5]))
```

- [x] **Step 5: Use gates in preflight route**

In `prepare_video_production()`, after optional generation sections and before `if payload.create_video_task`, compute:

```python
        gate_failures = _video_quality_gate_failures(db, project, storyboard)
        preflight_summary["quality_gate_failures"] = gate_failures
        if gate_failures:
            db.add(
                TaskEvent(
                    project_id=project.id,
                    storyboard=storyboard,
                    event_type="storyboard_preflight_blocked",
                    message="视频生产前置检查未通过。",
                    payload_json=json_dumps({"quality_gate_failures": gate_failures}),
                )
            )
            db.commit()
            if payload.create_video_task:
                raise HTTPException(status_code=409, detail="视频生产前置检查未通过：" + "；".join(gate_failures[:5]))
            return _state_out(db, project)
```

- [x] **Step 6: Run gate tests**

Run:

```bash
python -m unittest tests.test_video_preflight_quality_gates
```

Expected: PASS.

- [x] **Step 7: Run longform artifact tests**

Run:

```bash
python -m unittest tests.test_longform_artifact_delete_api tests.test_visual_asset_locked_references
```

Expected: PASS.

- [x] **Step 8: Commit**

```bash
git add app/api_routes_longform.py tests/test_video_preflight_quality_gates.py
git commit -m "feat: block video tasks on missing visual gates"
```

---

### Task 7: Stop Silent Text-To-Video Fallback For Image-Required Shots

**Files:**
- Modify: `app/video_render_service.py`
- Test: `tests/test_video_render_quality_gates.py`

- [ ] **Step 1: Write failing render fallback test**

Create `tests/test_video_render_quality_gates.py`:

```python
from __future__ import annotations

import unittest

from app.json_utils import json_dumps
from app.models import StoryboardShot
from app.video_render_service import VideoRenderService


class VideoRenderQualityGateTests(unittest.TestCase):
    def test_shot_requires_image_to_video_when_continuity_requires_i2v(self) -> None:
        service = VideoRenderService(settings=object())
        shot = StoryboardShot(
            shot_no=2,
            meta_json=json_dumps({"continuity": {"requires_i2v": True, "first_frame_source": "previous_last_frame"}}),
        )

        self.assertTrue(service._shot_requires_i2v(shot))

    def test_transition_can_allow_text_video(self) -> None:
        service = VideoRenderService(settings=object())
        shot = StoryboardShot(
            shot_no=3,
            meta_json=json_dumps({"continuity": {"requires_i2v": False, "shot_type": "transition"}}),
        )

        self.assertFalse(service._shot_requires_i2v(shot))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_video_render_quality_gates
```

Expected: FAIL because `_shot_requires_i2v()` does not exist.

- [ ] **Step 3: Add render helper**

In `app/video_render_service.py`:

```python
    def _shot_requires_i2v(self, shot: StoryboardShot) -> bool:
        meta = json_loads_object(shot.meta_json)
        continuity = meta.get("continuity") if isinstance(meta.get("continuity"), dict) else {}
        return continuity.get("requires_i2v") is not False
```

- [ ] **Step 4: Block silent fallback in `_render_with_jimeng()`**

Update the branch:

```python
            if first_frame_asset is not None:
                first_frame_url = self._resolvable_asset_url(first_frame_asset)
                if first_frame_url:
                    jimeng_task_id, submit_response = image_client.submit_first_frame_to_video(
                        prompt=prompt,
                        image_url=first_frame_url,
                        frames=self.settings.jimeng_frames,
                        aspect_ratio=self.settings.jimeng_aspect_ratio,
                    )
                elif self._shot_requires_i2v(shot):
                    raise RuntimeError(f"镜头 {shot.shot_no} 需要首帧驱动视频，但首帧素材无法解析为可访问 URL。")
                else:
                    jimeng_task_id, submit_response = text_client.submit_text_to_video(
                        prompt=prompt,
                        frames=self.settings.jimeng_frames,
                        aspect_ratio=self.settings.jimeng_aspect_ratio,
                    )
            else:
                if self._shot_requires_i2v(shot):
                    raise RuntimeError(f"镜头 {shot.shot_no} 需要首帧驱动视频，但没有首帧素材。")
                jimeng_task_id, submit_response = text_client.submit_text_to_video(
                    prompt=prompt,
                    frames=self.settings.jimeng_frames,
                    aspect_ratio=self.settings.jimeng_aspect_ratio,
                )
```

- [ ] **Step 5: Run render gate tests**

Run:

```bash
python -m unittest tests.test_video_render_quality_gates
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/video_render_service.py tests/test_video_render_quality_gates.py
git commit -m "fix: block silent text video fallback"
```

---

### Task 8: Frontend Upload And Confirmation UI

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/stores/workbench.ts`
- Modify: `frontend/src/components/workspace/LongformPipelinePanel.vue`
- Test: `tests/test_frontend_reference_asset_upload_wiring.py`

- [ ] **Step 1: Write frontend wiring test**

Add `tests/test_frontend_reference_asset_upload_wiring.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "frontend" / "src" / "api.ts"
STORE = ROOT / "frontend" / "src" / "stores" / "workbench.ts"
PIPELINE = ROOT / "frontend" / "src" / "components" / "workspace" / "LongformPipelinePanel.vue"


class FrontendReferenceAssetUploadWiringTests(unittest.TestCase):
    def test_upload_and_confirm_reference_assets_are_threaded_to_video_panel(self) -> None:
        api_source = API.read_text(encoding="utf-8")
        store_source = STORE.read_text(encoding="utf-8")
        panel_source = PIPELINE.read_text(encoding="utf-8")

        self.assertIn("uploadReferenceImage", api_source)
        self.assertIn("FormData", api_source)
        self.assertIn("classifyReferenceImage", api_source)
        self.assertIn("uploadReferenceImage", store_source)
        self.assertIn("updateReferenceImage", store_source)
        self.assertIn("上传参考图", panel_source)
        self.assertIn("确认映射", panel_source)
        self.assertIn("仅作风格参考", panel_source)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_frontend_reference_asset_upload_wiring
```

Expected: FAIL because frontend upload wiring does not exist.

- [ ] **Step 3: Extend API client**

In `frontend/src/api.ts`:

```ts
  uploadReferenceImage: (token: string, projectId: number, file: File, assetKind = "character_reference") => {
    const body = new FormData();
    body.append("file", file);
    body.append("asset_kind", assetKind);
    return request<ReferenceImageAsset>(`/api/projects/${projectId}/reference-images/upload`, {
      method: "POST",
      token,
      body,
    });
  },
  classifyReferenceImage: (token: string, projectId: number, assetId: number, hints: Record<string, unknown> = {}) =>
    request<ReferenceImageAsset>(`/api/projects/${projectId}/reference-images/${assetId}/classify`, {
      method: "POST",
      token,
      body: JSON.stringify({ hints }),
    }),
```

Ensure `request()` does not force `Content-Type: application/json` when `body` is `FormData`.

- [ ] **Step 4: Extend store**

In `frontend/src/stores/workbench.ts`:

```ts
  async function uploadReferenceImage(file: File, assetKind = "character_reference") {
    if (!token.value || !activeProject.value) return null;
    loading.value = true;
    error.value = "";
    try {
      const asset = await api.uploadReferenceImage(token.value, activeProject.value.project.id, file, assetKind);
      referenceImages.value = [asset, ...referenceImages.value.filter((item) => item.id !== asset.id)];
      return asset;
    } catch (err) {
      error.value = err instanceof Error ? err.message : "上传参考图失败。";
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function classifyReferenceImage(assetId: number, hints: Record<string, unknown> = {}) {
    if (!token.value || !activeProject.value) return null;
    const asset = await api.classifyReferenceImage(token.value, activeProject.value.project.id, assetId, hints);
    referenceImages.value = referenceImages.value.map((item) => item.id === asset.id ? asset : item);
    return asset;
  }
```

Export both functions.

- [ ] **Step 5: Add panel UI**

In `LongformPipelinePanel.vue`, add a video-mode section before "角色视觉母版":

```vue
<section class="panel panel--paper" v-if="isVideoMode">
  <div class="panel-heading">
    <div>
      <p class="panel-heading__kicker">参考资产</p>
      <h2>上传参考图</h2>
      <p class="panel-heading__desc">参考图先由 AI 推荐用途和映射，确认后才进入三视图、首帧和视频链路。</p>
    </div>
  </div>
  <input type="file" accept="image/png,image/jpeg,image/webp" @change="handleReferenceUpload" />
  <div class="card-list" v-if="referenceImages.length">
    <article v-for="asset in referenceImages" :key="asset.id" class="memory-card">
      <strong>{{ asset.asset_kind }} / {{ asset.status }}</strong>
      <span>{{ asset.mapped_character_name || "未绑定角色" }}</span>
      <div class="mode-switch">
        <button class="ghost-button ghost-button--small" type="button" @click="emit('classify-reference-image', asset.id)">AI 推荐</button>
        <button class="ghost-button ghost-button--small" type="button" @click="confirmReferenceAsset(asset)">确认映射</button>
        <button class="ghost-button ghost-button--small" type="button" @click="markStyleReference(asset)">仅作风格参考</button>
      </div>
    </article>
  </div>
</section>
```

This requires adding props/emits for `referenceImages`, `upload-reference-image`, `classify-reference-image`, and update events. Keep first UI simple; do not build a complex drag-and-drop gallery.

- [ ] **Step 6: Thread props/events from `VideoCreatePage`, `VideoStagePage`, and `App.vue`**

Add only the new reference asset props/events. Do not refactor all duplicate video wiring in this task.

- [ ] **Step 7: Run frontend wiring test**

Run:

```bash
python -m unittest tests.test_frontend_reference_asset_upload_wiring
```

Expected: PASS.

- [ ] **Step 8: Run build**

Run:

```bash
npm run build
```

Expected: frontend build succeeds.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/types.ts frontend/src/api.ts frontend/src/stores/workbench.ts frontend/src/components/workspace/LongformPipelinePanel.vue frontend/src/App.vue frontend/src/components/workspace/VideoCreatePage.vue frontend/src/components/workspace/VideoStagePage.vue tests/test_frontend_reference_asset_upload_wiring.py
git commit -m "feat: review uploaded reference assets in video workflow"
```

---

### Task 9: Display Shot Continuity And Gate Failures In The Video UI

**Files:**
- Modify: `frontend/src/components/workspace/LongformPipelinePanel.vue`
- Test: `tests/test_frontend_video_quality_gate_wiring.py`

- [ ] **Step 1: Write frontend gate display test**

Add `tests/test_frontend_video_quality_gate_wiring.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "frontend" / "src" / "components" / "workspace" / "LongformPipelinePanel.vue"


class FrontendVideoQualityGateWiringTests(unittest.TestCase):
    def test_video_panel_displays_continuity_and_preflight_blockers(self) -> None:
        source = PIPELINE.read_text(encoding="utf-8")

        self.assertIn("镜头连续性", source)
        self.assertIn("quality_gate_failures", source)
        self.assertIn("继承上一镜头末帧", source)
        self.assertIn("新首帧", source)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_frontend_video_quality_gate_wiring
```

Expected: FAIL.

- [ ] **Step 3: Add helpers in `LongformPipelinePanel.vue`**

Add:

```ts
function continuityLabel(shot: StoryboardShot) {
  const continuity = shot.continuity || {};
  const shotType = String(continuity.shot_type || "new");
  const source = String(continuity.first_frame_source || "generated");
  const typeLabel: Record<string, string> = {
    new: "新镜头",
    continuation: "连续镜头",
    camera_move: "运镜延续",
    transition: "转场镜头",
  };
  const sourceLabel = source === "previous_last_frame" ? "继承上一镜头末帧" : "新首帧";
  return `${typeLabel[shotType] || "新镜头"} / ${sourceLabel}`;
}

function latestQualityGateFailures() {
  const events = latestStoryboard.value?.events ?? [];
  const event = [...events].reverse().find((item) => item.event_type === "storyboard_preflight_blocked");
  const failures = event?.payload?.quality_gate_failures;
  return Array.isArray(failures) ? failures.map((item) => String(item)) : [];
}
```

- [ ] **Step 4: Render gate and continuity text**

In storyboard section:

```vue
<div v-if="latestQualityGateFailures().length" class="panel-note panel-note--warning">
  <span v-for="failure in latestQualityGateFailures()" :key="failure">{{ failure }}</span>
</div>
```

Inside each shot card:

```vue
<span>镜头连续性：{{ continuityLabel(shot) }}</span>
```

- [ ] **Step 5: Run frontend gate test**

Run:

```bash
python -m unittest tests.test_frontend_video_quality_gate_wiring
```

Expected: PASS.

- [ ] **Step 6: Run build**

Run:

```bash
npm run build
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/workspace/LongformPipelinePanel.vue tests/test_frontend_video_quality_gate_wiring.py
git commit -m "feat: show video continuity and gate failures"
```

---

### Task 10: Remove Duplicate Video Page Wiring

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/components/workspace/VideoStagePage.vue`
- Modify: `frontend/src/components/workspace/VideoCreatePage.vue`
- Modify: `tests/test_frontend_artifact_delete_wiring.py`

- [ ] **Step 1: Update duplicate-wiring test to allow a single video page**

Change `tests/test_frontend_artifact_delete_wiring.py` so it no longer requires both `VideoCreatePage.vue` and `VideoStagePage.vue` to contain every event. It should assert:

```python
self.assertIn("@delete-asset", app_source)
self.assertIn("@delete-video-task", app_source)
self.assertIn("@delete-storyboard", app_source)
self.assertIn("VideoCreatePage", app_source)
```

Remove assertions that require `video_stage_source` to forward every event.

- [ ] **Step 2: Run test to verify current expectations fail after test update if code still duplicates**

Run:

```bash
python -m unittest tests.test_frontend_artifact_delete_wiring
```

Expected: PASS may still occur. This is acceptable because this is a refactor enabling test, not a behavior failure test.

- [ ] **Step 3: Make `VideoStagePage.vue` a tiny alias or remove it from route usage**

Preferred minimal change:

- Keep file for import compatibility.
- Make it render `VideoCreatePage` without redefining every emit type. If TypeScript allows it, use fallthrough attrs:

```vue
<script setup lang="ts">
import VideoCreatePage from "./VideoCreatePage.vue";
</script>

<template>
  <VideoCreatePage v-bind="$attrs" />
</template>
```

If Vue typing complains, instead remove `VideoStagePage` usage from `App.vue` and render `VideoCreatePage` for both `videoStage` and `videoCreate` through one conditional block.

- [ ] **Step 4: Consolidate `App.vue` video page block**

Replace the two duplicated `videoStage`/`videoCreate` blocks with one block:

```vue
<template v-else-if="['videoStage', 'videoCreate'].includes(currentView)">
  <VideoCreatePage
    v-if="isAuthenticated && hasProject"
    :project="activeProject?.project"
    :project-title="activeProject?.project.title"
    :loading="loading"
    :state="longformState"
    :context-pack="contextPack"
    :character-cards="activeProject?.character_cards || []"
    :character-reference-profiles="activeProject?.character_reference_profiles || []"
    :managed-novels="managedNovels"
    :current-novel="currentNovel"
    :preferred-series-plan-id="preferredSeriesPlanId"
    :preferred-draft-version-id="preferredLongformDraftVersionId"
    :preferred-storyboard-id="preferredStoryboardId"
    :preferred-video-task-id="preferredVideoTaskId"
    @generate-plan="submitGenerateSeriesPlan"
    @submit-feedback="submitOutlineFeedback"
    @lock-plan="store.lockSeriesPlan"
    @restore-plan-version="submitRestorePlanVersion"
    @batch-generate="submitBatchGeneration"
    @retry-batch="submitRetryBatch"
    @pause-batch="submitPauseBatch"
    @resume-batch="submitResumeBatch"
    @cancel-batch="submitCancelBatch"
    @open-novel="openNovelForLongform"
    @create-storyboard="submitCreateStoryboard"
    @revise-draft="submitReviseDraft"
    @canonicalize-draft="submitCanonicalizeDraft"
    @create-video-task="(storyboardId) => { openGenerationTraceImmediately(); return store.createVideoTask(storyboardId); }"
    @update-outline="submitUpdateOutline"
    @update-shot="submitUpdateShot"
    @update-asset="submitUpdateAsset"
    @delete-asset="submitDeleteAsset"
    @generate-character-turnaround="submitGenerateCharacterTurnaround"
    @generate-shot-first-frame="submitGenerateShotFirstFrame"
    @generate-audio-scripts="(storyboardId) => { openGenerationTraceImmediately(); return store.generateStoryboardAudioScripts(storyboardId); }"
    @generate-storyboard-voice="(storyboardId) => { openGenerationTraceImmediately(); return store.generateStoryboardVoice(storyboardId, { voice_role: 'dialogue' }); }"
    @prepare-video-production="(storyboardId) => { openGenerationTraceImmediately(); return store.prepareVideoProduction(storyboardId, { generate_character_turnarounds: true, generate_audio_scripts: false, generate_dialogue_audio: false, create_video_task: true }); }"
    @generate-shot-voice="({ storyboardId, shotId, voice_role, character_card_id, dialogue_text, voice_profile, emotion }) => { openGenerationTraceImmediately(); return store.generateShotVoice(storyboardId, shotId, { voice_role, character_card_id, dialogue_text, voice_profile, emotion }); }"
    @create-shot="submitCreateShot"
    @delete-shot="submitDeleteShot"
    @delete-video-task="submitDeleteVideoTask"
    @delete-storyboard="submitDeleteStoryboard"
    @reorder-shots="submitReorderShots"
    @update-video-task="submitUpdateVideoTask"
    @update-visual-style="submitUpdateVisualStyle"
  />
</template>
```

Keep all existing event bindings once.

- [ ] **Step 5: Run frontend wiring tests**

Run:

```bash
python -m unittest tests.test_frontend_artifact_delete_wiring tests.test_frontend_reference_asset_upload_wiring tests.test_frontend_video_quality_gate_wiring
```

Expected: PASS.

- [ ] **Step 6: Run build**

Run:

```bash
npm run build
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/App.vue frontend/src/components/workspace/VideoStagePage.vue tests/test_frontend_artifact_delete_wiring.py
git commit -m "refactor: consolidate video workspace wiring"
```

---

### Task 11: Full Regression And Manual Smoke

**Files:**
- No production code expected unless verification reveals a bug.

- [ ] **Step 1: Run Python targeted suite**

Run:

```bash
python -m unittest tests.test_reference_asset_service tests.test_reference_asset_api tests.test_reference_asset_upload_api tests.test_reference_asset_classifier tests.test_turnaround_uses_reference_assets tests.test_visual_asset_candidates tests.test_visual_asset_locked_references tests.test_storyboard_shot_continuity tests.test_video_preflight_quality_gates tests.test_video_render_quality_gates tests.test_series_planning_service tests.test_violation_check_service tests.test_longform_artifact_delete_api
```

Expected: PASS.

- [ ] **Step 2: Run frontend wiring tests**

Run:

```bash
python -m unittest tests.test_frontend_artifact_delete_wiring tests.test_frontend_reference_asset_upload_wiring tests.test_frontend_video_quality_gate_wiring
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

Run:

```bash
npm run build
```

Expected: PASS.

- [ ] **Step 4: Manual smoke path**

Start the app using the existing local workflow. In browser:

1. Open an existing project.
2. Go to 视频.
3. Upload a reference image.
4. Confirm it as a character reference mapped to an existing character.
5. Generate a turnaround for that character.
6. Confirm metadata includes `visual_reference_asset_ids`.
7. Generate a storyboard from finalized chapters.
8. Confirm each shot displays continuity type.
9. Attempt to create video task before first frames exist.
10. Expected: blocked with quality gate failures.

- [ ] **Step 5: Update plan checkboxes if executing from this plan**

Mark completed steps in this file as implementation proceeds.

---

## Follow-Up Plan After This Slice

After this plan is complete, write a second plan for:

- Extract previous video ending frame into a reusable `shot_last_frame` asset.
- For `continuation` and `camera_move` shots, automatically set first-frame source to the previous `shot_last_frame`.
- Add AI-assisted visual candidate recommendation for turnarounds and first frames.
- Add optional web image search as a separate reference asset source.
- Add stricter visual quality scoring after enough user-confirmed examples exist.

These are explicitly deferred because the current priority is to replace fake text-only links with real confirmed assets and hard gates.

## Self-Review

Spec coverage:

- Uploaded user reference images: Task 1 and Task 8.
- AI recommendation plus user confirmation: Task 2 and Task 8.
- Reference assets drive three-view generation: Task 3.
- Storyboard continuity and character ID linkage: Task 4 and Task 5.
- Quality gates before video: Task 6.
- Stop text-to-video fallback: Task 7.
- Frontend visibility and duplicate cleanup: Task 8, Task 9, Task 10.

Simplicity review:

- The plan does not introduce provider switching, web search, or broad plugin architecture.
- It uses existing models where possible and extends `ReferenceImageAsset` with minimal metadata.
- It does not attempt fully automatic visual scoring in this slice.
- It keeps Jimeng and current longform services intact.

Placeholder scan:

- No `TODO`, `TBD`, or "implement later" placeholders are required to execute the plan.
- Follow-up work is explicitly separated from this plan.

Type consistency:

- `asset_kind`, `mapped_character_name`, `meta`, `continuity`, `quality_gate_failures`, and `visual_reference_asset_ids` are used consistently across contracts, services, and tests.
