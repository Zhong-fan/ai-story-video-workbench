from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

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
