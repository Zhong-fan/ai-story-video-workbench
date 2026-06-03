from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from .config import Settings
from .json_utils import json_dumps, json_loads_object
from .models import MediaAsset


def project_code(project_id: int) -> str:
    return f"p{project_id:06d}"


def media_asset_code(asset_id: int) -> str:
    return f"m{asset_id:06d}"


def media_asset_file_path(asset: MediaAsset, *, settings: Settings, file_name: str, deleted: bool = False) -> Path:
    return _media_asset_dir(asset, settings=settings, deleted=deleted) / file_name


def soft_delete_media_asset(asset: MediaAsset, *, settings: Settings) -> None:
    original_uri = asset.uri
    source = _uri_to_path(original_uri, settings=settings)
    file_name = _file_name_for_uri(original_uri, asset=asset)
    deleted_path = _unique_path(_media_asset_dir(asset, settings=settings, deleted=True) / file_name)
    file_missing = True

    if source is not None and source.exists() and source.is_file():
        deleted_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(source), str(deleted_path))
        except OSError as exc:
            raise RuntimeError(f"移动素材到回收站失败：{exc}") from exc
        file_missing = False

    meta = json_loads_object(asset.meta_json)
    asset.uri = str(deleted_path)
    asset.deleted_at = datetime.utcnow()
    asset.meta_json = json_dumps(
        {
            **meta,
            "original_uri": meta.get("original_uri") or original_uri,
            "deleted_uri": str(deleted_path),
            "file_missing": file_missing,
        }
    )


def restore_media_asset(asset: MediaAsset, *, settings: Settings) -> None:
    meta = json_loads_object(asset.meta_json)
    deleted_uri = str(meta.get("deleted_uri") or asset.uri)
    source = _uri_to_path(deleted_uri, settings=settings)
    file_name = _file_name_for_uri(deleted_uri, asset=asset)
    restored_path = _unique_path(_media_asset_dir(asset, settings=settings, deleted=False) / file_name)
    file_missing = True

    if source is not None and source.exists() and source.is_file():
        restored_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(source), str(restored_path))
        except OSError as exc:
            raise RuntimeError(f"恢复素材文件失败：{exc}") from exc
        file_missing = False

    asset.uri = str(restored_path)
    asset.deleted_at = None
    asset.meta_json = json_dumps(
        {
            **meta,
            "restored_uri": str(restored_path),
            "file_missing": file_missing,
        }
    )


def _media_asset_dir(asset: MediaAsset, *, settings: Settings, deleted: bool) -> Path:
    bucket = "deleted" if deleted else "assets"
    return _output_dir(settings) / "projects" / project_code(asset.project_id) / bucket / "media" / media_asset_code(asset.id)


def _file_name_for_uri(uri: str, *, asset: MediaAsset) -> str:
    name = Path((uri or "").replace("\\", "/")).name
    return name or f"{media_asset_code(asset.id)}.bin"


def _uri_to_path(uri: str, *, settings: Settings) -> Path | None:
    if not uri:
        return None
    normalized = uri.replace("\\", "/")
    if normalized.startswith("/output/"):
        return _output_dir(settings) / normalized.removeprefix("/output/")
    if normalized.startswith("output/"):
        return settings.root_dir / normalized
    path = Path(uri)
    if path.is_absolute():
        return path
    return settings.root_dir / path


def _output_dir(settings: Settings) -> Path:
    value = getattr(settings, "output_dir", None)
    if value is not None:
        return Path(value)
    root_dir = getattr(settings, "root_dir", None)
    if root_dir is not None:
        return Path(root_dir) / "output"
    return Path("output")


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for index in range(2, 10_000):
        candidate = path.with_name(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Cannot allocate unique media asset path: {path}")
