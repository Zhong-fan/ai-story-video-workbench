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
from app.models import Project, Storyboard, User


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
            user = User(
                email="brief@example.com",
                display_name="Brief User",
                password_hash=b"0" * 32,
                password_salt=b"1" * 16,
            )
            project = Project(
                owner=user,
                title="Star Bridge",
                genre="urban fantasy",
                premise="Two strangers see the same light over the city.",
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

    def test_create_user_brief_storyboard_without_chapters(self) -> None:
        brief = "20 second short: night city, a light bridge appears, two people see the same beam."

        response = self.client.post(
            f"/api/projects/{self.project_id}/storyboards",
            json={
                "source_mode": "user_brief",
                "novel_chapter_ids": [],
                "title": "Star Bridge 20s",
                "reference_video_brief": brief,
                "key_image_strategy": "generate_first_frames",
                "reference_image_asset_ids": [],
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["source_chapter_ids"], [])
        self.assertEqual(payload["progress"]["source_mode"], "user_brief")
        self.assertEqual(payload["progress"]["reference_video_brief"], brief)

        with self.SessionLocal() as session:
            storyboard = session.get(Storyboard, payload["id"])
            self.assertIsNotNone(storyboard)
            self.assertEqual(storyboard.source_chapter_ids_json, "[]")


if __name__ == "__main__":
    unittest.main()
