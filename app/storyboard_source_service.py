from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .creative_source_contracts import build_source_trace
from .json_utils import json_dumps
from .models import Novel, NovelChapter, Project, ReferenceImageAsset


@dataclass
class StoryboardSourceArtifact:
    source_mode: str
    title: str
    source_chapter_ids: list[int] = field(default_factory=list)
    reference_video_brief: str = ""
    key_image_strategy: str = "generate_first_frames"
    reference_image_asset_ids: list[int] = field(default_factory=list)
    chapters: list[NovelChapter] = field(default_factory=list)
    reference_image_notes: list[str] = field(default_factory=list)
    source_trace: dict[str, Any] = field(default_factory=dict)

    def event_payload(self) -> dict[str, Any]:
        return {
            "source_mode": self.source_mode,
            "novel_chapter_ids": self.source_chapter_ids,
            "reference_video_brief": self.reference_video_brief,
            "key_image_strategy": self.key_image_strategy,
            "reference_image_asset_ids": self.reference_image_asset_ids,
            "source_trace": self.source_trace,
        }

    def source_chapter_ids_json(self) -> str:
        return json_dumps(self.source_chapter_ids)


class StoryboardSourceService:
    def build(
        self,
        db: Session,
        *,
        project: Project,
        current_user_id: int,
        source_mode: str,
        title: str,
        novel_chapter_ids: list[int],
        reference_video_brief: str,
        key_image_strategy: str,
        reference_image_asset_ids: list[int],
    ) -> StoryboardSourceArtifact:
        if source_mode == "novel_chapters":
            chapters = self._chapters_for_project(
                db,
                project=project,
                current_user_id=current_user_id,
                novel_chapter_ids=novel_chapter_ids,
            )
            if len(chapters) != len(set(novel_chapter_ids)):
                raise RuntimeError("只能选择当前项目下已发布/定稿章节生成分镜。")
            return StoryboardSourceArtifact(
                source_mode=source_mode,
                title=title,
                source_chapter_ids=novel_chapter_ids,
                chapters=chapters,
                source_trace=build_source_trace(
                    source_mode=source_mode,
                    novel_chapter_ids=novel_chapter_ids,
                    reference_video_brief="",
                    reference_image_asset_ids=[],
                    key_image_strategy=key_image_strategy,
                ),
            )

        reference_assets = db.scalars(
            select(ReferenceImageAsset).where(
                ReferenceImageAsset.project_id == project.id,
                ReferenceImageAsset.id.in_(reference_image_asset_ids),
            )
        ).all()
        return StoryboardSourceArtifact(
            source_mode=source_mode,
            title=title,
            source_chapter_ids=[],
            reference_video_brief=reference_video_brief.strip(),
            key_image_strategy=key_image_strategy,
            reference_image_asset_ids=[asset.id for asset in reference_assets],
            reference_image_notes=[self._reference_image_note(asset) for asset in reference_assets],
            source_trace=build_source_trace(
                source_mode=source_mode,
                novel_chapter_ids=[],
                reference_video_brief=reference_video_brief.strip(),
                reference_image_asset_ids=[asset.id for asset in reference_assets],
                key_image_strategy=key_image_strategy,
            ),
        )

    def _chapters_for_project(
        self,
        db: Session,
        *,
        project: Project,
        current_user_id: int,
        novel_chapter_ids: list[int],
    ) -> list[NovelChapter]:
        return db.scalars(
            select(NovelChapter)
            .join(Novel, NovelChapter.novel_id == Novel.id)
            .where(
                Novel.owner_id == current_user_id,
                Novel.project_id == project.id,
                Novel.deleted_at.is_(None),
                NovelChapter.id.in_(novel_chapter_ids),
            )
            .order_by(NovelChapter.chapter_no.asc())
        ).all()

    def _reference_image_note(self, asset: ReferenceImageAsset) -> str:
        parts = [asset.asset_kind, asset.mapped_character_name, asset.source_work, asset.remote_url]
        return " / ".join(str(item).strip() for item in parts if str(item or "").strip())
