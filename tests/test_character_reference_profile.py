from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.json_utils import json_dumps, json_loads_object
from app.models import CharacterCard, CharacterReferenceProfile, MediaAsset, Project, User
from app.visual_asset_service import CharacterReferenceProfileService, VisualAssetService


class CharacterReferenceProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(bind=engine, future=True)

    def test_backfills_profile_from_locked_turnaround_asset(self) -> None:
        service = CharacterReferenceProfileService()
        with self.SessionLocal() as session:
            user = User(email="profile@example.com", display_name="视觉用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="天气之子续作", genre="现代都市")
            character = CharacterCard(project=project, name="阳菜", age="16", gender="女", personality="明亮坚定", story_role="女主", background="")
            session.add_all([project, character])
            session.flush()
            locked = MediaAsset(
                project_id=project.id,
                asset_type="character_turnaround",
                uri="output/characters/hina/turnaround-v001.png",
                prompt="三视图",
                status="completed",
                meta_json=json_dumps({"character_card_id": character.id, "character_name": "阳菜", "locked": True}),
            )
            session.add(locked)
            session.flush()

            profiles = service.ensure_profiles(session, project)

            self.assertEqual(len(profiles), 1)
            self.assertEqual(profiles[0].character_card_id, character.id)
            self.assertEqual(profiles[0].reference_character_name, "阳菜")
            self.assertEqual(profiles[0].locked_turnaround_asset_id, locked.id)
            self.assertEqual(profiles[0].status, "turnaround_locked")

    def test_locking_turnaround_updates_profile_and_unlocks_siblings(self) -> None:
        service = VisualAssetService(settings=object())
        with self.SessionLocal() as session:
            user = User(email="profile-lock@example.com", display_name="锁定用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="天气之子续作", genre="现代都市")
            character = CharacterCard(project=project, name="帆高", age="16", gender="男", personality="执拗", story_role="男主", background="")
            session.add_all([project, character])
            session.flush()
            old_asset = MediaAsset(
                project_id=project.id,
                asset_type="character_turnaround",
                uri="old.png",
                status="completed",
                meta_json=json_dumps({"character_card_id": character.id, "character_name": "帆高", "locked": True}),
            )
            new_asset = MediaAsset(
                project_id=project.id,
                asset_type="character_turnaround",
                uri="new.png",
                status="completed",
                meta_json=json_dumps({"character_card_id": character.id, "character_name": "帆高", "locked": False}),
            )
            session.add_all([old_asset, new_asset])
            session.flush()

            service.apply_turnaround_lock(db=session, project=project, asset=new_asset, locked=True)
            profile = session.query(CharacterReferenceProfile).filter_by(character_card_id=character.id).one()

            self.assertFalse(json_loads_object(old_asset.meta_json)["locked"])
            self.assertTrue(json_loads_object(new_asset.meta_json)["locked"])
            self.assertEqual(profile.locked_turnaround_asset_id, new_asset.id)
            self.assertEqual(profile.status, "turnaround_locked")


if __name__ == "__main__":
    unittest.main()
