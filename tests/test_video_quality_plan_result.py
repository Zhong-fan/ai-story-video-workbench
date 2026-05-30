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
from app.json_utils import json_loads_object
from app.models import Project, Storyboard, StoryboardShot, User, VideoTask


class VideoQualityPlanResultTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite://", future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(bind=engine, future=True)
        with self.SessionLocal() as session:
            user = User(
                email="quality@example.com",
                display_name="Quality User",
                password_hash=b"0" * 32,
                password_salt=b"1" * 16,
            )
            project = Project(
                owner=user,
                title="Quality Short",
                genre="urban fantasy",
                premise="A beam of light changes a rainy city.",
            )
            storyboard = Storyboard(
                project=project,
                title="Quality Short",
                source_chapter_ids_json="[]",
                status="draft",
                summary="A three-shot short.",
            )
            session.add_all([user, project, storyboard])
            session.flush()
            ContextPackService().build(
                session,
                project=project,
                reference_mode="style_reference",
                user_notes="",
                confirm_after_build=True,
            )
            shot = StoryboardShot(
                storyboard=storyboard,
                shot_no=1,
                narration_text="A light appears on a rainy street.",
                visual_prompt="Animated film frame, rainy city street, blue green light beam.",
                character_refs_json="[]",
                scene_refs_json="[]",
                meta_json=(
                    '{"source_mode":"user_brief",'
                    '"source_trace":{"source_mode":"user_brief","reference_video_brief":"A three-shot short."},'
                    '"continuity":{"requires_i2v":false,"first_frame_source":"generated"},'
                    '"audio_script":{"subtitle_text":"A light appears on a rainy street."}}'
                ),
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
            self.assertEqual(quality_plan["structure"]["opening"], "Shot 1 establishes the scene.")
            self.assertEqual(quality_plan["shots"][0]["shot_no"], 1)
            self.assertEqual(quality_plan["shots"][0]["purpose"], "A light appears on a rainy street.")


if __name__ == "__main__":
    unittest.main()
