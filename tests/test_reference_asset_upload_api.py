from __future__ import annotations

import io
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
from app.models import Project, ReferenceImageAsset, User


class ReferenceAssetUploadApiTests(unittest.TestCase):
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
                email="upload@example.com",
                display_name="上传用户",
                password_hash=b"0" * 32,
                password_salt=b"1" * 16,
            )
            project = Project(owner=user, title="资产驱动项目", genre="青春")
            session.add_all([user, project])
            session.commit()
            self.user_id = user.id
            self.project_id = project.id

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

    def test_upload_reference_image_creates_candidate_with_public_output_url(self) -> None:
        response = self.client.post(
            f"/api/projects/{self.project_id}/reference-images/upload",
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
