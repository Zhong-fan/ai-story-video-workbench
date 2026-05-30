from __future__ import annotations

from typing import Any

SUPPORTED_ASSET_KINDS = {
    "character_reference",
    "scene_reference",
    "style_reference",
    "composition_reference",
    "unknown",
}


def normalize_reference_classification(raw: dict[str, Any], *, known_character_names: list[str]) -> dict[str, Any]:
    kind = str(raw.get("asset_kind") or "unknown").strip()
    if kind not in SUPPORTED_ASSET_KINDS:
        kind = "unknown"
    mapped = str(raw.get("mapped_character_name") or "").strip()
    if mapped and mapped not in set(known_character_names):
        mapped = ""
    try:
        confidence = float(raw.get("confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(confidence, 1.0))
    status = "suggested" if kind != "unknown" and (kind != "character_reference" or mapped) else "needs_review"
    tags = [str(item).strip() for item in raw.get("tags", []) if str(item).strip()] if isinstance(raw.get("tags"), list) else []
    return {
        "asset_kind": kind,
        "mapped_character_name": mapped,
        "confidence": confidence,
        "reason": str(raw.get("reason") or "").strip(),
        "tags": tags,
        "classification_status": status,
    }
