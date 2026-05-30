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
from app.json_utils import json_loads_object
from app.models import CharacterCard, CharacterReferenceProfile, Project, ReferenceImageAsset, User


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


    def test_confirm_reference_image_updates_kind_meta_and_syncs_profile(self) -> None:
        with self.SessionLocal() as session:
            project = session.get(Project, self.project_id)
            card = CharacterCard(
                project=project,
                name="阳菜",
                age="16",
                gender="女",
                personality="明亮坚定",
                story_role="女主",
                background="",
            )
            asset = ReferenceImageAsset(
                project=project,
                source_work=project.reference_work,
                asset_kind="unknown",
                remote_url="https://example.com/hina.png",
                remote_url_hash="asset-hash",
                provider="manual",
                source_page="https://example.com",
                mapped_character_name="",
                status="candidate",
            )
            session.add_all([card, asset])
            session.commit()
            asset_id = asset.id
            card_id = card.id

        response = self.client.put(
            f"/api/projects/{self.project_id}/reference-images/{asset_id}",
            json={
                "status": "approved",
                "mapped_character_name": "阳菜",
                "asset_kind": "character_reference",
                "meta": {"classification_status": "confirmed"},
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["status"], "approved")
        self.assertEqual(payload["asset_kind"], "character_reference")
        self.assertEqual(payload["mapped_character_name"], "阳菜")
        self.assertEqual(payload["meta"]["classification_status"], "confirmed")

        with self.SessionLocal() as session:
            asset = session.get(ReferenceImageAsset, asset_id)
            self.assertEqual(json_loads_object(asset.meta_json)["classification_status"], "confirmed")
            profile = session.query(CharacterReferenceProfile).filter_by(character_card_id=card_id).one()
            self.assertEqual(profile.status, "reference_assets_ready")
            self.assertEqual(profile.visual_reference_asset_ids, [asset_id])

    def test_classify_reference_image_updates_suggested_metadata(self) -> None:
        with self.SessionLocal() as session:
            project = session.get(Project, self.project_id)
            card = CharacterCard(
                project=project,
                name="阳菜",
                age="16",
                gender="女",
                personality="明亮坚定",
                story_role="女主",
                background="",
            )
            asset = ReferenceImageAsset(
                project=project,
                source_work=project.reference_work,
                asset_kind="unknown",
                remote_url="https://example.com/hina-classify.png",
                remote_url_hash="classify-hash",
                provider="upload",
                source_page="upload:hina.png",
                mapped_character_name="",
                status="candidate",
            )
            session.add_all([card, asset])
            session.commit()
            asset_id = asset.id

        response = self.client.post(
            f"/api/projects/{self.project_id}/reference-images/{asset_id}/classify",
            json={
                "hints": {
                    "asset_kind": "character_reference",
                    "mapped_character_name": "阳菜",
                    "confidence": 0.9,
                    "reason": "角色参考图",
                }
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["asset_kind"], "character_reference")
        self.assertEqual(payload["mapped_character_name"], "阳菜")
        self.assertEqual(payload["meta"]["classification_status"], "suggested")
        self.assertEqual(payload["meta"]["confidence"], 0.9)


if __name__ == "__main__":
    unittest.main()
