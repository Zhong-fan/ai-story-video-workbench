from __future__ import annotations

from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from .models import Project, ReferenceFact


class ReferencePolicyService:
    def prompt_block(self, snapshot: dict[str, Any]) -> str:
        reference_work = str(snapshot.get("reference_work") or "").strip()
        if not reference_work:
            return ""
        inheritance_mode = str(snapshot.get("inheritance_mode") or "style_only").strip()
        rewrite_start = str(snapshot.get("rewrite_start") or "").strip()
        authorized_changes = str(snapshot.get("authorized_changes") or "").strip()
        lines = [f"参考作品：{reference_work}"]
        if inheritance_mode == "strict_inherit":
            lines.append("原作事实默认继承：未明确授权改写的地方，原作既有事实继续成立。")
        elif inheritance_mode == "characters_and_world":
            lines.append("默认继承角色与世界规则，但剧情可以从指定节点重新展开。")
        else:
            lines.append("默认只继承风格与气质，不自动继承完整原作事实。")
        if rewrite_start:
            lines.append(f"改写起点：{rewrite_start}")
        if authorized_changes:
            lines.append(f"授权改写：{authorized_changes}")
        return "\n".join(lines)

    def hard_constraints(self, snapshot: dict[str, Any]) -> list[str]:
        reference_work = str(snapshot.get("reference_work") or "").strip()
        if not reference_work:
            return []
        inheritance_mode = str(snapshot.get("inheritance_mode") or "style_only").strip()
        rewrite_start = str(snapshot.get("rewrite_start") or "").strip()
        authorized_changes = str(snapshot.get("authorized_changes") or "").strip()
        lines: list[str] = []
        if inheritance_mode == "strict_inherit":
            lines.append(f"参考作品《{reference_work}》的原作事实默认继承，未授权改写处不得偏离。")
        elif inheritance_mode == "characters_and_world":
            lines.append(f"参考作品《{reference_work}》的角色身份与世界规则默认继承。")
        if rewrite_start:
            lines.append(f"当前改写起点：{rewrite_start}")
        if authorized_changes:
            lines.append(f"当前已授权改写：{authorized_changes}")
        return lines

    def derive_reference_facts(self, project: Project) -> list[dict[str, Any]]:
        reference_work = str(project.reference_work or "").strip()
        if not reference_work:
            return []
        mode = str(project.reference_inheritance_mode or "style_only").strip()
        if mode == "style_only":
            return []

        facts: list[dict[str, Any]] = []
        synopsis = str(project.reference_work_synopsis or "").strip()
        rewrite_start = str(project.reference_rewrite_start or "").strip()
        if synopsis:
            facts.append(
                self._fact(
                    fact_type="plot_fact",
                    reference_work=reference_work,
                    suffix="synopsis",
                    summary=synopsis,
                    source="reference_work_synopsis",
                    rewrite_start=rewrite_start,
                )
            )
        for index, trait in enumerate(project.reference_work_world_traits, start=1):
            facts.append(
                self._fact(
                    fact_type="world_rule",
                    reference_work=reference_work,
                    suffix=f"world-{index}",
                    summary=trait,
                    source="reference_work_world_traits",
                    rewrite_start=rewrite_start,
                )
            )
        for index, item in enumerate(project.reference_work_narrative_constraints, start=1):
            facts.append(
                self._fact(
                    fact_type="relationship_state" if self._looks_like_relationship_fact(item) else "plot_fact",
                    reference_work=reference_work,
                    suffix=f"narrative-{index}",
                    summary=item,
                    source="reference_work_narrative_constraints",
                    rewrite_start=rewrite_start,
                )
            )
        if rewrite_start:
            facts.append(
                self._fact(
                    fact_type="plot_fact",
                    reference_work=reference_work,
                    suffix="rewrite-baseline",
                    summary=f"改写起点前的原作事实必须成立：{rewrite_start}",
                    source="reference_rewrite_start",
                    rewrite_start=rewrite_start,
                )
            )
        return facts

    def sync_project_reference_facts(self, db: Session, project: Project) -> list[ReferenceFact]:
        facts = self.derive_reference_facts(project)
        db.execute(delete(ReferenceFact).where(ReferenceFact.project_id == project.id))
        persisted: list[ReferenceFact] = []
        for item in facts:
            fact = ReferenceFact(
                project=project,
                fact_type=str(item["fact_type"]),
                reference_key=str(item["reference_key"]),
                chapter_effective_until=item.get("chapter_effective_until"),
                status=str(item.get("status") or "active"),
            )
            fact.payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
            db.add(fact)
            persisted.append(fact)
        db.flush()
        return persisted

    def facts_snapshot(self, facts: list[ReferenceFact] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        snapshot: list[dict[str, Any]] = []
        for item in facts:
            if isinstance(item, ReferenceFact):
                payload = item.payload
                snapshot.append(
                    {
                        "id": item.id,
                        "fact_type": item.fact_type,
                        "reference_key": item.reference_key,
                        "chapter_effective_until": item.chapter_effective_until,
                        "payload": payload,
                        "summary": str(payload.get("summary") or "").strip(),
                        "status": item.status,
                    }
                )
            elif isinstance(item, dict):
                payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
                snapshot.append(
                    {
                        "fact_type": str(item.get("fact_type") or "").strip(),
                        "reference_key": str(item.get("reference_key") or "").strip(),
                        "chapter_effective_until": item.get("chapter_effective_until"),
                        "payload": payload,
                        "summary": str(item.get("summary") or payload.get("summary") or "").strip(),
                        "status": str(item.get("status") or "active").strip(),
                    }
                )
        return [item for item in snapshot if item.get("fact_type") and item.get("reference_key")]

    def mark_fact_conflicts(
        self,
        facts: list[dict[str, Any]],
        story_boundary_rules: list[dict[str, Any]],
        *,
        authorized_changes: str,
    ) -> list[dict[str, Any]]:
        authorized_text = str(authorized_changes or "").strip()
        result: list[dict[str, Any]] = []
        for fact in self.facts_snapshot(facts):
            conflict_rule_ids = [
                str(rule.get("rule_id") or "")
                for rule in story_boundary_rules
                if self._rule_conflicts_with_fact(rule, fact)
            ]
            conflict_rule_ids = [item for item in conflict_rule_ids if item]
            if conflict_rule_ids:
                fact["conflict_rule_ids"] = conflict_rule_ids
                fact["status"] = "authorized_override" if self._authorized_for_fact(fact, authorized_text) else "conflict"
            result.append(fact)
        return result

    def _fact(
        self,
        *,
        fact_type: str,
        reference_work: str,
        suffix: str,
        summary: str,
        source: str,
        rewrite_start: str,
    ) -> dict[str, Any]:
        payload = {
            "summary": str(summary or "").strip(),
            "source": source,
            "rewrite_start": rewrite_start,
        }
        return {
            "fact_type": fact_type,
            "reference_key": f"{reference_work}:{suffix}",
            "chapter_effective_until": None,
            "payload": payload,
            "summary": payload["summary"],
            "status": "active",
        }

    def _looks_like_relationship_fact(self, text: str) -> bool:
        return any(term in str(text or "") for term in ("关系", "相遇", "重逢", "见面", "身份"))

    def _rule_conflicts_with_fact(self, rule: dict[str, Any], fact: dict[str, Any]) -> bool:
        if rule.get("rule_type") != "forbid_event" or rule.get("predicate") != "direct_meeting":
            return False
        summary = str(fact.get("summary") or "").strip()
        if not summary or not any(term in summary for term in ("相遇", "见面", "重逢", "相见")):
            return False
        subjects = [str(item).strip() for item in rule.get("subjects", []) if str(item).strip()]
        return not subjects or any(subject in summary for subject in subjects)

    def _authorized_for_fact(self, fact: dict[str, Any], authorized_text: str) -> bool:
        if not authorized_text:
            return False
        summary = str(fact.get("summary") or "")
        if any(term in authorized_text for term in ("重逢", "相遇", "见面", "关系")) and any(
            term in summary for term in ("重逢", "相遇", "见面", "关系")
        ):
            return True
        return any(term and term in authorized_text for term in str(fact.get("reference_key") or "").split(":"))
