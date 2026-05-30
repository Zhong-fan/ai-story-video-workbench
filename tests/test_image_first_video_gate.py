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
from app.json_utils import json_dumps
from app.models import Project, Storyboard, StoryboardShot, User


class ImageFirstVideoGateTests(unittest.TestCase):
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
            user = User(email="image-gate@example.com", display_name="图片门禁用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(owner=user, title="图片先行", genre="动画短片", reference_work="参考作品")
            storyboard = Storyboard(
                project=project,
                title="图片先行测试",
                source_chapter_ids_json="[]",
                status="draft",
                summary="从参考作品直接生成关键图再生成视频。",
            )
            shot = StoryboardShot(
                storyboard=storyboard,
                shot_no=1,
                narration_text="雨光落下。",
                visual_prompt="雨夜城市，一束光穿过云层。",
                character_refs_json="[]",
                scene_refs_json="[]",
                meta_json=json_dumps(
                    {
                        "continuity": {
                            "requires_i2v": True,
                            "first_frame_source": "generated",
                            "shot_type": "new",
                        },
                        "source_mode": "image_first_reference",
                    }
                ),
                duration_seconds=5,
                status="draft",
            )
            session.add_all([user, project, storyboard, shot])
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
            self.storyboard_id = storyboard.id

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

    def test_image_first_video_task_requires_completed_first_frame(self) -> None:
        response = self.client.post(f"/api/projects/{self.project_id}/storyboards/{self.storyboard_id}/video-tasks")

        self.assertEqual(response.status_code, 409)
        self.assertIn("图片先行镜头缺少已完成首帧", response.json()["detail"])

    def test_render_service_marks_image_first_shot_as_i2v_required(self) -> None:
        from app.video_render_service import VideoRenderService

        with self.SessionLocal() as session:
            storyboard = session.get(Storyboard, self.storyboard_id)
            shot = storyboard.shots[0]

            self.assertTrue(VideoRenderService(load_settings())._shot_requires_i2v(shot))


if __name__ == "__main__":
    unittest.main()
