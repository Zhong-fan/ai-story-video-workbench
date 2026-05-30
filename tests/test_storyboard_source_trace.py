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
            user = User(
                email="trace@example.com",
                display_name="Trace User",
                password_hash=b"0" * 32,
                password_salt=b"1" * 16,
            )
            project = Project(
                owner=user,
                title="Light Chase",
                genre="urban fantasy",
                premise="A beam of light crosses the city in the rain.",
            )
            session.add_all([user, project])
            session.flush()
            ContextPackService().build(
                session,
                project=project,
                reference_mode="style_reference",
                user_notes="",
                confirm_after_build=True,
            )
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
        brief = "Three shots: rain street, chasing a light beam, the sky turns bright."
        response = self.client.post(
            f"/api/projects/{self.project_id}/storyboards",
            json={
                "source_mode": "user_brief",
                "novel_chapter_ids": [],
                "title": "Light Chase 15s",
                "reference_video_brief": brief,
                "key_image_strategy": "generate_first_frames",
                "reference_image_asset_ids": [],
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        storyboard_id = response.json()["id"]

        fake_payload = {
            "title": "Light Chase 15s",
            "summary": "A brief-sourced short.",
            "shots": [
                {
                    "shot_no": 1,
                    "narration_text": "A light rises on a rainy street.",
                    "visual_prompt": "Animated film frame, rainy city street, blue green light beam.",
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
                self.assertEqual(meta["source_trace"]["reference_video_brief"], brief)


if __name__ == "__main__":
    unittest.main()
