from __future__ import annotations

from typing import Any

SOURCE_MODE_NOVEL_CHAPTERS = "novel_chapters"
SOURCE_MODE_IMAGE_FIRST_REFERENCE = "image_first_reference"
SOURCE_MODE_EXISTING_IMAGES = "existing_images"
SOURCE_MODE_USER_BRIEF = "user_brief"

SUPPORTED_SOURCE_MODES = {
    SOURCE_MODE_NOVEL_CHAPTERS,
    SOURCE_MODE_IMAGE_FIRST_REFERENCE,
    SOURCE_MODE_EXISTING_IMAGES,
    SOURCE_MODE_USER_BRIEF,
}

NON_NOVEL_SOURCE_MODES = {
    SOURCE_MODE_IMAGE_FIRST_REFERENCE,
    SOURCE_MODE_EXISTING_IMAGES,
    SOURCE_MODE_USER_BRIEF,
}

IMAGE_CONTROLLED_SOURCE_MODES = {
    SOURCE_MODE_IMAGE_FIRST_REFERENCE,
    SOURCE_MODE_EXISTING_IMAGES,
}


def normalize_source_mode(value: str | None) -> str:
    source_mode = str(value or "").strip() or SOURCE_MODE_NOVEL_CHAPTERS
    if source_mode not in SUPPORTED_SOURCE_MODES:
        raise ValueError("不支持的分镜来源模式。")
    return source_mode


def source_mode_requires_brief(source_mode: str) -> bool:
    return source_mode in NON_NOVEL_SOURCE_MODES


def source_mode_requires_chapters(source_mode: str) -> bool:
    return source_mode == SOURCE_MODE_NOVEL_CHAPTERS


def source_mode_requires_i2v(source_mode: str) -> bool:
    return source_mode in IMAGE_CONTROLLED_SOURCE_MODES


def build_source_trace(
    *,
    source_mode: str,
    novel_chapter_ids: list[int],
    reference_video_brief: str,
    reference_image_asset_ids: list[int],
    key_image_strategy: str,
) -> dict[str, Any]:
    return {
        "source_mode": source_mode,
        "novel_chapter_ids": novel_chapter_ids,
        "reference_video_brief": reference_video_brief,
        "reference_image_asset_ids": reference_image_asset_ids,
        "key_image_strategy": key_image_strategy,
    }
