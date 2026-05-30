from __future__ import annotations

import unittest

from app.reference_asset_classifier import normalize_reference_classification


class ReferenceAssetClassifierTests(unittest.TestCase):
    def test_normalize_reference_classification_keeps_supported_kind_and_mapping(self) -> None:
        result = normalize_reference_classification(
            {
                "asset_kind": "character_reference",
                "mapped_character_name": "阳菜",
                "confidence": 0.91,
                "reason": "图中是少女角色设定图",
                "tags": ["校服", "短发"],
            },
            known_character_names=["阳菜", "帆高"],
        )

        self.assertEqual(result["asset_kind"], "character_reference")
        self.assertEqual(result["mapped_character_name"], "阳菜")
        self.assertEqual(result["confidence"], 0.91)
        self.assertEqual(result["classification_status"], "suggested")

    def test_normalize_reference_classification_drops_unknown_character_mapping(self) -> None:
        result = normalize_reference_classification(
            {
                "asset_kind": "character_reference",
                "mapped_character_name": "未知角色",
                "confidence": "0.8",
                "reason": "不确定",
            },
            known_character_names=["阳菜"],
        )

        self.assertEqual(result["asset_kind"], "character_reference")
        self.assertEqual(result["mapped_character_name"], "")
        self.assertEqual(result["classification_status"], "needs_review")


if __name__ == "__main__":
    unittest.main()
