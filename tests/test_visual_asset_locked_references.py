from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.json_utils import json_dumps, json_loads_object
from app.models import CharacterCard, MediaAsset, Project, Storyboard, StoryboardShot, User
from app.visual_asset_service import VisualAssetService


class VisualAssetLockedReferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(bind=engine, future=True)

    def test_locked_turnaround_references_are_resolved_for_shot_characters(self) -> None:
        service = VisualAssetService(settings=object())  # helper under test does not read provider settings
        with self.SessionLocal() as session:
            user = User(email="visual@example.com", display_name="视觉用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="天气之子续作", genre="现代都市")
            character = CharacterCard(
                project=project,
                name="阳菜",
                age="16",
                gender="女",
                personality="明亮坚定",
                story_role="女主",
                background="拥有改变天气的秘密。",
            )
            storyboard = Storyboard(project=project, title="预告片", source_chapter_ids_json="[]")
            shot = StoryboardShot(
                storyboard=storyboard,
                shot_no=1,
                narration_text="阳菜站在天台边。",
                visual_prompt="雨后的天台，阳菜回头。",
                character_refs_json=json_dumps([{"character_card_id": 1, "name": "阳菜"}]),
                scene_refs_json="[]",
            )
            session.add_all([project, character, storyboard, shot])
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
            session.commit()

            references = service.locked_turnaround_references(db=session, project=project, shot=shot)

            self.assertEqual(len(references), 1)
            self.assertEqual(references[0]["asset_id"], locked.id)
            self.assertEqual(references[0]["character_card_id"], character.id)
            self.assertEqual(references[0]["uri"], locked.uri)

    def test_locked_turnaround_references_resolve_character_name_refs(self) -> None:
        service = VisualAssetService(settings=object())
        with self.SessionLocal() as session:
            user = User(email="visual-name@example.com", display_name="视觉用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="天气之子续作", genre="现代都市")
            character = CharacterCard(project=project, name="阳菜")
            storyboard = Storyboard(project=project, title="预告片", source_chapter_ids_json="[]")
            shot = StoryboardShot(
                storyboard=storyboard,
                shot_no=1,
                narration_text="阳菜站在天台边。",
                visual_prompt="雨后的天台，阳菜回头。",
                character_refs_json=json_dumps(["阳菜"]),
                scene_refs_json="[]",
            )
            session.add_all([project, character, storyboard, shot])
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
            session.commit()

            references = service.locked_turnaround_references(db=session, project=project, shot=shot)

            self.assertEqual(len(references), 1)
            self.assertEqual(references[0]["character_card_id"], character.id)

    def test_locking_turnaround_unlocks_other_candidates_for_same_character(self) -> None:
        service = VisualAssetService(settings=object())
        with self.SessionLocal() as session:
            user = User(email="lock@example.com", display_name="锁定用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="天气之子续作", genre="现代都市")
            character = CharacterCard(project=project, name="帆高", age="16", gender="男", personality="执拗", story_role="男主", background="离家少年。")
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

            self.assertFalse(json_loads_object(old_asset.meta_json)["locked"])
            self.assertTrue(json_loads_object(new_asset.meta_json)["locked"])
            self.assertEqual(json_loads_object(new_asset.meta_json)["turnaround_status"], "turnaround_locked")


if __name__ == "__main__":
    unittest.main()
