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
from app.db import Base, get_db
from app.json_utils import json_dumps
from app.models import CharacterCard, CharacterReferenceProfile, MediaAsset, Project, Storyboard, StoryboardShot, TaskEvent, User, VideoTask


class LongformArtifactDeleteApiTests(unittest.TestCase):
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
            user = User(email="delete-api@example.com", display_name="删除用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="天气之子续作", genre="现代都市")
            session.add(project)
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

    def test_delete_media_asset_removes_asset_and_clears_locked_turnaround_profile(self) -> None:
        with self.SessionLocal() as session:
            project = session.get(Project, self.project_id)
            character = CharacterCard(project=project, name="阳菜", age="16", gender="女", personality="明亮", story_role="女主", background="")
            session.add(character)
            session.flush()
            asset = MediaAsset(
                project_id=self.project_id,
                asset_type="character_turnaround",
                uri="output/turnaround-v001.png",
                prompt="三视图",
                status="completed",
                meta_json=json_dumps({"character_card_id": character.id, "character_name": character.name, "locked": True}),
            )
            session.add(asset)
            session.flush()
            profile = CharacterReferenceProfile(
                project_id=self.project_id,
                character_card_id=character.id,
                reference_character_name=character.name,
                locked_turnaround_asset_id=asset.id,
                status="turnaround_locked",
            )
            session.add(profile)
            session.commit()
            asset_id = asset.id
            profile_id = profile.id

        response = self.client.delete(f"/api/projects/{self.project_id}/media-assets/{asset_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "deleted")
        with self.SessionLocal() as session:
            self.assertIsNone(session.get(MediaAsset, asset_id))
            profile = session.get(CharacterReferenceProfile, profile_id)
            self.assertIsNotNone(profile)
            self.assertIsNone(profile.locked_turnaround_asset_id)
            self.assertNotEqual(profile.status, "turnaround_locked")

    def test_delete_video_task_removes_task_and_events(self) -> None:
        with self.SessionLocal() as session:
            storyboard = Storyboard(project_id=self.project_id, title="预告片", source_chapter_ids_json="[]")
            session.add(storyboard)
            session.flush()
            task = VideoTask(project_id=self.project_id, storyboard_id=storyboard.id, task_status="completed", output_uri="output/video.mp4")
            session.add(task)
            session.flush()
            event = TaskEvent(project_id=self.project_id, storyboard_id=storyboard.id, video_task_id=task.id, event_type="video_done")
            session.add(event)
            session.commit()
            task_id = task.id
            event_id = event.id

        response = self.client.delete(f"/api/projects/{self.project_id}/video-tasks/{task_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "deleted")
        with self.SessionLocal() as session:
            self.assertIsNone(session.get(VideoTask, task_id))
            self.assertIsNone(session.get(TaskEvent, event_id))

    def test_delete_storyboard_removes_shots_assets_video_tasks_and_events(self) -> None:
        with self.SessionLocal() as session:
            storyboard = Storyboard(project_id=self.project_id, title="预告片", source_chapter_ids_json="[]")
            session.add(storyboard)
            session.flush()
            shot = StoryboardShot(storyboard_id=storyboard.id, shot_no=1, narration_text="雨停了。", visual_prompt="屋顶", character_refs_json="[]", scene_refs_json="[]")
            session.add(shot)
            session.flush()
            asset = MediaAsset(
                project_id=self.project_id,
                storyboard_id=storyboard.id,
                shot_id=shot.id,
                asset_type="shot_first_frame",
                uri="output/frame.png",
                prompt="屋顶",
                status="completed",
            )
            task = VideoTask(project_id=self.project_id, storyboard_id=storyboard.id, task_status="completed", output_uri="output/video.mp4")
            session.add_all([asset, task])
            session.flush()
            storyboard_event = TaskEvent(project_id=self.project_id, storyboard_id=storyboard.id, event_type="storyboard_done")
            task_event = TaskEvent(project_id=self.project_id, storyboard_id=storyboard.id, video_task_id=task.id, event_type="video_done")
            session.add_all([storyboard_event, task_event])
            session.commit()
            storyboard_id = storyboard.id
            shot_id = shot.id
            asset_id = asset.id
            task_id = task.id
            event_ids = [storyboard_event.id, task_event.id]

        response = self.client.delete(f"/api/projects/{self.project_id}/storyboards/{storyboard_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "deleted")
        with self.SessionLocal() as session:
            self.assertIsNone(session.get(Storyboard, storyboard_id))
            self.assertIsNone(session.get(StoryboardShot, shot_id))
            self.assertIsNone(session.get(MediaAsset, asset_id))
            self.assertIsNone(session.get(VideoTask, task_id))
            for event_id in event_ids:
                self.assertIsNone(session.get(TaskEvent, event_id))


if __name__ == "__main__":
    unittest.main()
