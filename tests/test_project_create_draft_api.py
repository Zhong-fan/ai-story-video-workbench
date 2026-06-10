from __future__ import annotations

import unittest

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api_routes_projects import register_project_routes
from app.auth import get_current_user
from app.config import load_settings
from app.db import Base, get_db
from app.models import Project, User


class ProjectCreateDraftApiTests(unittest.TestCase):
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
                email="draft-api@example.com",
                display_name="草稿用户",
                password_hash=b"0" * 32,
                password_salt=b"1" * 16,
            )
            session.add(user)
            session.commit()
            self.user_id = user.id

        app = FastAPI()
        router = APIRouter()
        register_project_routes(router, settings=load_settings())
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

    def test_import_script_returns_editable_project_draft_without_creating_project(self) -> None:
        response = self.client.post(
            "/api/projects/import-draft",
            json={
                "title": "",
                "genre": "都市短剧",
                "original_filename": "rain-night.txt",
                "script_text": "雨夜重逢\n女主在便利店外遇见失踪三年的男主，两人被迫一起躲雨。第二场写男主隐瞒身份。",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["mode"], "upload")
        self.assertEqual(payload["project"]["title"], "雨夜重逢")
        self.assertEqual(payload["project"]["genre"], "都市短剧")
        self.assertIn("rain-night.txt", payload["source_summary"])
        self.assertIn("女主在便利店外遇见失踪三年的男主", payload["project"]["world_brief"])
        self.assertIn("保留原剧本", payload["project"]["writing_rules"])
        with self.SessionLocal() as session:
            self.assertEqual(session.scalars(select(Project)).all(), [])

    def test_ai_brief_returns_editable_project_draft_without_creating_project(self) -> None:
        response = self.client.post(
            "/api/projects/brief-draft",
            json={
                "title": "雨夜逆袭",
                "genre": "都市情感短剧",
                "protagonist": "被家族放弃的女律师",
                "core_conflict": "她必须在七天内证明亡父遗嘱被篡改",
                "audience": "喜欢强情绪反转和女性成长的短剧观众",
                "tone": "高压、克制、每集结尾有反转",
                "episode_count": 24,
                "reference_work": "黑暗荣耀",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["mode"], "ai")
        self.assertEqual(payload["project"]["title"], "雨夜逆袭")
        self.assertEqual(payload["project"]["genre"], "都市情感短剧")
        self.assertIn("被家族放弃的女律师", payload["project"]["world_brief"])
        self.assertIn("七天内证明亡父遗嘱被篡改", payload["project"]["world_brief"])
        self.assertIn("每集结尾", payload["project"]["writing_rules"])
        self.assertIn("黑暗荣耀", payload["project"]["reference_work"])
        with self.SessionLocal() as session:
            self.assertEqual(session.scalars(select(Project)).all(), [])


if __name__ == "__main__":
    unittest.main()
