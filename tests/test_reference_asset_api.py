from __future__ import annotations

import unittest

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api_routes_projects import register_project_routes
from app.auth import get_current_user
from app.db import Base, get_db
from app.models import CharacterCard, Project, ReferenceImageAsset, User


class ReferenceAssetApiTests(unittest.TestCase):
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
            self.user = User(email="api@example.com", display_name="接口用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            self.project = Project(owner=self.user, title="天气之子续作", genre="现代都市", reference_work="天气之子")
            session.add(self.project)
            session.commit()
            self.user_id = self.user.id
            self.project_id = self.project.id

        app = FastAPI()
        router = APIRouter()
        register_project_routes(router)
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

    def test_reference_image_discovery_approval_api_path(self) -> None:
        discover_response = self.client.post(
            f"/api/projects/{self.project_id}/reference-images/discover",
            json={
                "candidates": [
                    {
                        "remote_url": "https://example.com/weathering-with-you/poster.jpg",
                        "asset_kind": "poster",
                        "provider": "manual",
                        "source_page": "https://example.com/weathering-with-you",
                    }
                ]
            },
        )
        self.assertEqual(discover_response.status_code, 200)
        discovered = discover_response.json()
        self.assertEqual(len(discovered), 1)
        self.assertEqual(discovered[0]["source_work"], "天气之子")
        self.assertEqual(discovered[0]["status"], "candidate")

        list_response = self.client.get(f"/api/projects/{self.project_id}/reference-images")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        asset_id = discovered[0]["id"]
        approve_response = self.client.put(
            f"/api/projects/{self.project_id}/reference-images/{asset_id}",
            json={"status": "approved", "mapped_character_name": "阳菜"},
        )
        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(approve_response.json()["status"], "approved")
        self.assertEqual(approve_response.json()["mapped_character_name"], "阳菜")

        state_response = self.client.get(f"/api/projects/{self.project_id}/reference-images/workflow-state")
        self.assertEqual(state_response.status_code, 200)
        self.assertEqual(state_response.json()["status"], "enough_approved_assets")
        self.assertEqual(state_response.json()["approved_count"], 1)

        with self.SessionLocal() as session:
            persisted = session.query(ReferenceImageAsset).filter(ReferenceImageAsset.project_id == self.project_id).all()
            self.assertEqual(len(persisted), 1)
            self.assertEqual(persisted[0].source_work, "天气之子")

    def test_project_detail_includes_character_reference_profiles(self) -> None:
        with self.SessionLocal() as session:
            project = session.get(Project, self.project_id)
            session.add(
                CharacterCard(
                    project=project,
                    name="阳菜",
                    age="16",
                    gender="女",
                    personality="明亮坚定",
                    story_role="女主",
                    background="",
                )
            )
            session.commit()

        response = self.client.get(f"/api/projects/{self.project_id}")

        self.assertEqual(response.status_code, 200)
        profiles = response.json()["character_reference_profiles"]
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0]["reference_character_name"], "阳菜")
        self.assertEqual(profiles[0]["status"], "unmapped")


if __name__ == "__main__":
    unittest.main()
