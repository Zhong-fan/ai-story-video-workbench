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
from app.models import Project, Storyboard, User


class ImageFirstReferenceStoryboardTests(unittest.TestCase):
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
            user = User(email="image-first@example.com", display_name="图片先行用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(
                owner=user,
                title="雨夜短片",
                genre="都市奇幻",
                reference_work="天气之子",
                premise="一个雨夜里，陌生人追着一束光穿过城市。",
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

    def test_create_image_first_storyboard_without_chapters(self) -> None:
        response = self.client.post(
            f"/api/projects/{self.project_id}/storyboards",
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

        with self.SessionLocal() as session:
            storyboard = session.get(Storyboard, payload["id"])
            self.assertIsNotNone(storyboard)
            self.assertEqual(storyboard.source_chapter_ids_json, "[]")

    def test_image_first_storyboard_job_generates_i2v_shots_without_chapters(self) -> None:
        response = self.client.post(
            f"/api/projects/{self.project_id}/storyboards",
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

        fake_payload = {
            "title": "雨夜追光 15 秒",
            "summary": "图片先行短片。",
            "shots": [
                {
                    "shot_no": 1,
                    "narration_text": "雨光落下。",
                    "visual_prompt": "二维动画电影，雨夜城市街口，通透蓝绿色光影，一束光穿过雨幕。",
                    "character_refs": [],
                    "scene_refs": [{"name": "雨夜街口", "role": "开场场景"}],
                    "continuity": {
                        "shot_type": "new",
                        "depends_on_shot_no": None,
                        "first_frame_source": "generated",
                        "requires_i2v": True,
                    },
                    "audio_script": {},
                    "duration_seconds": 5,
                }
            ],
        }

        from app.config import load_settings
        from app.storyboard_job_service import StoryboardJobService

        with patch("app.storyboard_job_service.StoryboardService") as storyboard_service_class:
            storyboard_service_class.return_value.generate_image_first_storyboard.return_value = fake_payload
            with self.SessionLocal() as session:
                storyboard = session.get(Storyboard, storyboard_id)
                StoryboardJobService(load_settings()).run_storyboard(db=session, storyboard=storyboard)
                session.refresh(storyboard)

                self.assertEqual(storyboard.status, "draft")
                self.assertEqual(len(storyboard.shots), 1)
                self.assertIn('"requires_i2v": true', storyboard.shots[0].meta_json)
                storyboard_service_class.return_value.generate_image_first_storyboard.assert_called_once()


if __name__ == "__main__":
    unittest.main()
