from __future__ import annotations

import re
from typing import Any


MEETING_TERMS = ("相遇", "见面", "碰面", "重逢", "相见")
FORBID_TERMS = ("不要", "不能", "不得", "别", "禁止")
FIRST_MEETING_TERMS = ("第一次", "首次", "初次", "正式")
RANGE_PATTERN = re.compile(r"第\s*(\d+)\s*(?:章)?\s*(?:到|至|\-|—|–|~|～)\s*(\d+)\s*章")
SINGLE_CHAPTER_PATTERN = re.compile(r"第\s*(\d+)\s*章")


class StoryBoundaryService:
    def parse_rules(self, text: str) -> list[dict[str, Any]]:
        normalized = (text or "").strip()
        if not normalized:
            return []
        sentences = [item.strip() for item in re.split(r"[。；;！？\n]+", normalized) if item.strip()]
        rules: list[dict[str, Any]] = []
        sequence = 1
        for sentence in sentences:
            scope = self._extract_scope(sentence)
            if scope is None:
                scope = {"scope_type": "series", "start_chapter_no": None, "end_chapter_no": None}

            if self._is_forbid_meeting(sentence):
                rules.append(
                    self._build_rule(
                        rule_id=f"story-boundary-{sequence}",
                        sentence=sentence,
                        rule_type="forbid_event",
                        predicate="direct_meeting",
                        subjects=["男主", "女主"],
                        scope=scope,
                    )
                )
                sequence += 1

            if self._is_first_meeting(sentence):
                rules.append(
                    self._build_rule(
                        rule_id=f"story-boundary-{sequence}",
                        sentence=sentence,
                        rule_type="allow_event",
                        predicate="direct_meeting",
                        subjects=["男主", "女主"],
                        scope=scope,
                    )
                )
                sequence += 1

            if self._is_separate_backstory(sentence):
                rules.append(
                    self._build_rule(
                        rule_id=f"story-boundary-{sequence}",
                        sentence=sentence,
                        rule_type="required_focus",
                        predicate="separate_backstory",
                        subjects=["男主", "女主"],
                        scope=scope,
                    )
                )
                sequence += 1

            if not any(item["instruction"] == sentence for item in rules):
                rules.append(
                    self._build_rule(
                        rule_id=f"story-boundary-{sequence}",
                        sentence=sentence,
                        rule_type="directive",
                        predicate="freeform",
                        subjects=[],
                        scope=scope,
                    )
                )
                sequence += 1

        deduped: list[dict[str, Any]] = []
        seen: set[tuple[Any, ...]] = set()
        for item in rules:
            key = (
                item.get("rule_type"),
                item.get("predicate"),
                item.get("start_chapter_no"),
                item.get("end_chapter_no"),
                item.get("instruction"),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def active_rules_for_chapter(self, rules: list[dict[str, Any]], chapter_no: int) -> list[dict[str, Any]]:
        active: list[dict[str, Any]] = []
        for item in rules:
            if not isinstance(item, dict):
                continue
            scope_type = str(item.get("scope_type") or "series").strip() or "series"
            start = self._coerce_int(item.get("start_chapter_no"))
            end = self._coerce_int(item.get("end_chapter_no"))
            if scope_type == "series":
                active.append(item)
            elif scope_type == "chapter" and start == chapter_no:
                active.append(item)
            elif scope_type == "chapter_range" and start is not None and end is not None and start <= chapter_no <= end:
                active.append(item)
        return active

    def summary_line(self, rule: dict[str, Any]) -> str:
        instruction = str(rule.get("instruction") or "").strip()
        if instruction:
            return instruction
        rule_type = str(rule.get("rule_type") or "").strip()
        predicate = str(rule.get("predicate") or "").strip()
        scope = self._scope_label(rule)
        if rule_type == "forbid_event" and predicate == "direct_meeting":
            return f"{scope}：禁止男女主直接相遇"
        if rule_type == "allow_event" and predicate == "direct_meeting":
            return f"{scope}：允许男女主第一次正式见面"
        if rule_type == "required_focus" and predicate == "separate_backstory":
            return f"{scope}：重点写相遇前各自的故事"
        return f"{scope}：{rule_type or '规则'}"

    def prompt_lines(self, rules: list[dict[str, Any]]) -> list[str]:
        return [self.summary_line(item) for item in rules if isinstance(item, dict)]

    def _build_rule(
        self,
        *,
        rule_id: str,
        sentence: str,
        rule_type: str,
        predicate: str,
        subjects: list[str],
        scope: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "rule_id": rule_id,
            "scope_type": scope["scope_type"],
            "start_chapter_no": scope["start_chapter_no"],
            "end_chapter_no": scope["end_chapter_no"],
            "rule_type": rule_type,
            "subjects": subjects,
            "predicate": predicate,
            "instruction": sentence,
            "priority": "hard",
            "status": "active",
        }

    def _extract_scope(self, sentence: str) -> dict[str, Any] | None:
        range_match = RANGE_PATTERN.search(sentence)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2))
            if start > end:
                start, end = end, start
            return {
                "scope_type": "chapter_range",
                "start_chapter_no": start,
                "end_chapter_no": end,
            }
        single_match = SINGLE_CHAPTER_PATTERN.search(sentence)
        if single_match:
            chapter_no = int(single_match.group(1))
            return {
                "scope_type": "chapter",
                "start_chapter_no": chapter_no,
                "end_chapter_no": chapter_no,
            }
        return None

    def _is_forbid_meeting(self, sentence: str) -> bool:
        return any(term in sentence for term in FORBID_TERMS) and any(term in sentence for term in MEETING_TERMS)

    def _is_first_meeting(self, sentence: str) -> bool:
        return any(term in sentence for term in FIRST_MEETING_TERMS) and any(term in sentence for term in MEETING_TERMS)

    def _is_separate_backstory(self, sentence: str) -> bool:
        return "分别" in sentence and "相遇之前" in sentence and any(term in sentence for term in ("故事", "经历", "生活", "主线"))

    def _scope_label(self, rule: dict[str, Any]) -> str:
        scope_type = str(rule.get("scope_type") or "series")
        start = self._coerce_int(rule.get("start_chapter_no"))
        end = self._coerce_int(rule.get("end_chapter_no"))
        if scope_type == "chapter" and start is not None:
            return f"第 {start} 章"
        if scope_type == "chapter_range" and start is not None and end is not None:
            return f"第 {start}-{end} 章"
        return "全书"

    def _coerce_int(self, value: Any) -> int | None:
        try:
            if value is None or value == "":
                return None
            return int(value)
        except (TypeError, ValueError):
            return None
