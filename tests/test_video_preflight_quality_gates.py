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
from app.json_utils import json_dumps
from app.models import CharacterCard, Project, Storyboard, StoryboardShot, User


class VideoPreflightQualityGateTests(unittest.TestCase):
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
            user = User(email="gate@example.com", display_name="门禁用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="门禁项目", genre="青春")
            character = CharacterCard(project=project, name="阳菜")
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
            session.add_all([user, project, character, storyboard, shot])
            session.flush()
            ContextPackService().build(
                session,
                project=project,
                reference_mode="hybrid_reference",
                user_notes="",
                confirm_after_build=True,
            )
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

    def test_create_video_task_blocks_when_character_turnaround_is_not_locked(self) -> None:
        response = self.client.post(f"/api/projects/{self.project_id}/storyboards/{self.storyboard_id}/video-tasks")

        self.assertEqual(response.status_code, 409)
        self.assertIn("三视图", response.json()["detail"])

    def test_preflight_without_video_task_returns_gate_summary(self) -> None:
        response = self.client.post(
            f"/api/projects/{self.project_id}/storyboards/{self.storyboard_id}/video-production/preflight",
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
