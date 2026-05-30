from __future__ import annotations

import re
from typing import Any


POSITIVE_MEETING_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        r"(?<!不)(?<!没有)(?<!尚未)(第一次|首次|初次|正式|终于)?(相遇|见面|碰面|重逢|相见)",
        r"遇见了",
        r"碰到了",
        r"见到了",
    )
]
NEGATIVE_MEETING_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        r"不.{0,2}(相遇|见面|碰面|重逢|相见)",
        r"没有.{0,2}(相遇|见面|碰面|重逢|相见)",
        r"尚未.{0,2}(相遇|见面|碰面|重逢|相见)",
    )
]


class ViolationCheckService:
    def check_outline(self, outline: dict[str, Any], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        text = self._outline_text(outline)
        return self._check_text(text, rules)

    def check_content(self, content: str, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return self._check_text(content, rules)

    def _check_text(self, text: str, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized = (text or "").strip()
        if not normalized:
            return []
        violations: list[dict[str, Any]] = []
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            rule_type = str(rule.get("rule_type") or "").strip()
            predicate = str(rule.get("predicate") or "").strip()
            if rule_type == "forbid_event" and predicate == "direct_meeting" and self._contains_positive_meeting(normalized):
                violations.append(
                    {
                        "rule_id": str(rule.get("rule_id") or ""),
                        "rule_type": rule_type,
                        "predicate": predicate,
                        "message": str(rule.get("instruction") or "违反了禁止相遇规则。"),
                    }
                )
        return violations

    def _outline_text(self, outline: dict[str, Any]) -> str:
        chunks: list[str] = [
            str(outline.get("title") or ""),
            str(outline.get("chapter_goal") or ""),
            str(outline.get("conflict") or ""),
            str(outline.get("emotion_tone") or ""),
            str(outline.get("ending_hook") or ""),
        ]
        for key in ("must_happen", "character_progress"):
            value = outline.get(key)
            if isinstance(value, list):
                chunks.append(" ".join(str(item) for item in value))
            elif value is not None:
                chunks.append(str(value))
        return "\n".join(chunk for chunk in chunks if chunk.strip())

    def _contains_positive_meeting(self, text: str) -> bool:
        return any(pattern.search(text) for pattern in POSITIVE_MEETING_PATTERNS)
