from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import Project, ReferenceImageAsset, User
from app.reference_asset_service import ReferenceAssetService


class ReferenceAssetServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(bind=engine, future=True)

    def test_discovers_and_deduplicates_candidate_assets(self) -> None:
        service = ReferenceAssetService()
        with self.SessionLocal() as session:
            project = self._project(session)

            assets = service.discover_candidates(
                session,
                project=project,
                candidates=[
                    {
                        "remote_url": "https://example.com/weathering/poster.jpg",
                        "asset_kind": "poster",
                        "provider": "manual",
                        "source_page": "https://example.com/weathering",
                    },
                    {
                        "remote_url": "https://example.com/weathering/poster.jpg",
                        "asset_kind": "poster",
                        "provider": "manual",
                        "source_page": "https://example.com/weathering",
                    },
                ],
            )
            session.commit()

            persisted = session.query(ReferenceImageAsset).filter(ReferenceImageAsset.project_id == project.id).all()
            self.assertEqual(len(assets), 1)
            self.assertEqual(len(persisted), 1)
            self.assertEqual(persisted[0].status, "candidate")
            self.assertEqual(persisted[0].source_work, "天气之子")

    def test_approval_rejection_mapping_and_workflow_state(self) -> None:
        service = ReferenceAssetService()
        with self.SessionLocal() as session:
            project = self._project(session)
            poster, still = service.discover_candidates(
                session,
                project=project,
                candidates=[
                    {"remote_url": "https://example.com/poster.jpg", "asset_kind": "poster"},
                    {"remote_url": "https://example.com/hina.jpg", "asset_kind": "character_sheet"},
                ],
            )
            session.flush()

            service.update_asset_status(session, project=project, asset_id=poster.id, status="approved")
            service.update_asset_status(session, project=project, asset_id=still.id, status="rejected", mapped_character_name="阳菜")
            session.commit()

            state = service.workflow_state(session, project)
            self.assertEqual(state["total_candidates"], 2)
            self.assertEqual(state["approved_count"], 1)
            self.assertEqual(state["rejected_count"], 1)
            self.assertEqual(state["status"], "enough_approved_assets")

    def _project(self, session):
        user = User(email="asset@example.com", display_name="素材用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
        project = Project(owner=user, title="天气之子续作", genre="现代都市", reference_work="天气之子")
        session.add(project)
        session.commit()
        return project


if __name__ == "__main__":
    unittest.main()
