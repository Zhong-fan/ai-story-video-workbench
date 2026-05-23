from __future__ import annotations

import json
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.json_utils import json_loads_object
from app.models import CharacterCard, Project, Storyboard, StoryboardShot, User
from app.storyboard_job_service import StoryboardJobService


class StoryboardShotContinuityTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(bind=engine, future=True)

    def test_replace_shots_persists_structured_character_refs_and_continuity(self) -> None:
        service = StoryboardJobService(settings=object())
        with self.SessionLocal() as session:
            user = User(email="shot@example.com", display_name="分镜用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="视频项目", genre="青春")
            character = CharacterCard(project=project, name="阳菜")
            storyboard = Storyboard(project=project, title="预告片", source_chapter_ids_json="[]")
            session.add_all([project, character, storyboard])
            session.flush()

            count = service._replace_shots(
                session,
                storyboard=storyboard,
                shots=[
                    {
                        "shot_no": 1,
                        "narration_text": "她抬头。",
                        "visual_prompt": "天台近景",
                        "character_refs": [{"character_card_id": character.id, "name": "阳菜"}],
                        "scene_refs": [{"name": "天台"}],
                        "continuity": {
                            "shot_type": "new",
                            "depends_on_shot_no": None,
                            "first_frame_source": "generated",
                            "requires_i2v": True,
                            "end_frame_usage": "feeds_next",
                            "continuity_constraints": ["保持校服和湿发"],
                        },
                        "duration_seconds": 4,
                    }
                ],
            )
            session.flush()
            shot = session.query(StoryboardShot).one()

            self.assertEqual(count, 1)
            self.assertEqual(json.loads(shot.character_refs_json)[0]["character_card_id"], character.id)
            meta = json_loads_object(shot.meta_json)
            self.assertEqual(meta["continuity"]["shot_type"], "new")
            self.assertTrue(meta["continuity"]["requires_i2v"])


if __name__ == "__main__":
    unittest.main()
