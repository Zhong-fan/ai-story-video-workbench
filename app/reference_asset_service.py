from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .json_utils import json_dumps, json_loads_object
from .models import Project, ReferenceImageAsset


class ReferenceAssetService:
    VALID_STATUSES = {"candidate", "approved", "rejected"}

    def discover_candidates(
        self,
        db: Session,
        *,
        project: Project,
        candidates: list[dict[str, Any]] | None = None,
    ) -> list[ReferenceImageAsset]:
        source_work = str(project.reference_work or "").strip()
        if not source_work:
            return []
        assets: list[ReferenceImageAsset] = []
        existing_by_url = {
            item.remote_url: item
            for item in db.scalars(select(ReferenceImageAsset).where(ReferenceImageAsset.project_id == project.id)).all()
        }
        for raw in candidates or []:
            if not isinstance(raw, dict):
                continue
            remote_url = str(raw.get("remote_url") or "").strip()
            if not remote_url:
                continue
            remote_url_hash = _remote_url_hash(remote_url)
            existing = existing_by_url.get(remote_url)
            if existing is not None:
                if existing not in assets:
                    assets.append(existing)
                continue
            asset = ReferenceImageAsset(
                project=project,
                source_work=source_work,
                asset_kind=str(raw.get("asset_kind") or "stills").strip() or "stills",
                remote_url=remote_url,
                remote_url_hash=remote_url_hash,
                provider=str(raw.get("provider") or "manual").strip() or "manual",
                source_page=str(raw.get("source_page") or "").strip(),
                mapped_character_name=str(raw.get("mapped_character_name") or "").strip(),
                status="candidate",
            )
            db.add(asset)
            db.flush()
            existing_by_url[remote_url] = asset
            assets.append(asset)
        return assets

    def register_uploaded_asset(
        self,
        db: Session,
        *,
        project: Project,
        public_url: str,
        original_filename: str,
        asset_kind: str,
        content_type: str,
        byte_size: int,
    ) -> ReferenceImageAsset:
        normalized_url = public_url.strip()
        if not normalized_url:
            raise ValueError("Uploaded reference asset requires a public URL")
        existing = db.scalar(
            select(ReferenceImageAsset).where(
                ReferenceImageAsset.project_id == project.id,
                ReferenceImageAsset.remote_url_hash == _remote_url_hash(normalized_url),
            )
        )
        if existing is not None:
            return existing
        asset = ReferenceImageAsset(
            project=project,
            source_work=str(project.reference_work or project.title or "uploaded").strip(),
            asset_kind=asset_kind.strip() or "character_reference",
            remote_url=normalized_url,
            remote_url_hash=_remote_url_hash(normalized_url),
            provider="upload",
            source_page=f"upload:{original_filename.strip() or 'reference'}",
            mapped_character_name="",
            status="candidate",
            meta_json=json_dumps(
                {
                    "classification_status": "pending",
                    "original_filename": original_filename,
                    "content_type": content_type,
                    "byte_size": byte_size,
                }
            ),
        )
        db.add(asset)
        db.flush()
        return asset

    def list_assets(self, db: Session, *, project: Project) -> list[ReferenceImageAsset]:
        return db.scalars(
            select(ReferenceImageAsset)
            .where(ReferenceImageAsset.project_id == project.id)
            .order_by(ReferenceImageAsset.created_at.desc(), ReferenceImageAsset.id.desc())
        ).all()

    def update_asset_status(
        self,
        db: Session,
        *,
        project: Project,
        asset_id: int,
        status: str,
        mapped_character_name: str = "",
        asset_kind: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> ReferenceImageAsset:
        normalized_status = str(status or "").strip()
        if normalized_status not in self.VALID_STATUSES:
            raise ValueError(f"Unsupported reference asset status: {status}")
        asset = db.scalar(
            select(ReferenceImageAsset).where(
                ReferenceImageAsset.project_id == project.id,
                ReferenceImageAsset.id == asset_id,
            )
        )
        if asset is None:
            raise LookupError("Reference image asset not found")
        asset.status = normalized_status
        if mapped_character_name.strip():
            asset.mapped_character_name = mapped_character_name.strip()
        if asset_kind is not None and asset_kind.strip():
            asset.asset_kind = asset_kind.strip()
        if meta is not None:
            existing_meta = json_loads_object(asset.meta_json)
            asset.meta_json = json_dumps({**existing_meta, **meta})
        db.flush()
        return asset

    def workflow_state(self, db: Session, project: Project) -> dict[str, Any]:
        assets = self.list_assets(db, project=project)
        total = len(assets)
        pending = len([item for item in assets if item.status == "candidate"])
        approved = len([item for item in assets if item.status == "approved"])
        rejected = len([item for item in assets if item.status == "rejected"])
        if total == 0:
            status = "no_candidates"
        elif pending > 0:
            status = "candidates_pending_review"
        elif approved > 0:
            status = "enough_approved_assets"
        else:
            status = "no_approved_assets"
        return {
            "status": status,
            "total_candidates": total,
            "pending_count": pending,
            "approved_count": approved,
            "rejected_count": rejected,
        }


def _remote_url_hash(remote_url: str) -> str:
    return hashlib.sha256(remote_url.encode("utf-8")).hexdigest()
