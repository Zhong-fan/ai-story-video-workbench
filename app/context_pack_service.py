from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .json_utils import json_dumps, json_loads_list, json_loads_object
from .models import ContextPack, Project
from .reference_policy_service import ReferencePolicyService
from .story_boundary_service import StoryBoundaryService


def _compact_text(value: str, *, fallback: str = "未填写") -> str:
    text = (value or "").strip()
    return text or fallback


class ContextPackService:
    def __init__(self) -> None:
        self.story_boundary_service = StoryBoundaryService()
        self.reference_policy_service = ReferencePolicyService()

    def build(
        self,
        db: Session,
        *,
        project: Project,
        reference_mode: str,
        user_notes: str,
        user_decisions: dict[str, str] | None = None,
        confirm_after_build: bool = False,
    ) -> ContextPack:
        payload = self._compose_payload(
            project=project,
            reference_mode=reference_mode,
            user_notes=user_notes,
            user_decisions=user_decisions or {},
        )
        version_no = self._next_version_no(db, project.id)
        pack = ContextPack(
            project=project,
            version_no=version_no,
            status="confirmed" if confirm_after_build else "draft",
            reference_mode=reference_mode,
            user_notes=user_notes.strip(),
            source_fingerprint=payload["source_fingerprint"],
            project_snapshot_json=json_dumps(payload["project_snapshot"]),
            character_snapshot_json=json_dumps(payload["character_snapshot"]),
            reference_snapshot_json=json_dumps(payload["reference_snapshot"]),
            source_snapshot_json=json_dumps(payload["source_snapshot"]),
            conflict_report_json=json_dumps(payload["conflict_report"]),
            user_decisions_json=json_dumps(payload["user_decisions"]),
            derived_constraints_json=json_dumps(payload["derived_constraints"]),
            feed_preview_json=json_dumps(payload["feed_preview"]),
            confirmed_at=datetime.utcnow() if confirm_after_build else None,
        )
        db.add(pack)
        db.flush()
        return pack

    def rebuild(
        self,
        db: Session,
        *,
        project: Project,
        existing: ContextPack,
        confirm_after_build: bool = False,
    ) -> ContextPack:
        return self.build(
            db,
            project=project,
            reference_mode=existing.reference_mode,
            user_notes=existing.user_notes,
            user_decisions=json_loads_object(existing.user_decisions_json),
            confirm_after_build=confirm_after_build,
        )

    def confirm(self, pack: ContextPack) -> ContextPack:
        pack.status = "confirmed"
        pack.confirmed_at = datetime.utcnow()
        return pack

    def latest_for_project(self, db: Session, project_id: int) -> ContextPack | None:
        return db.scalar(select(ContextPack).where(ContextPack.project_id == project_id).order_by(ContextPack.version_no.desc()))

    def require_confirmed(self, db: Session, project: Project) -> ContextPack:
        pack = self.latest_for_project(db, project.id)
        if pack is None:
            raise RuntimeError("请先完成生成前校对，并确认创作上下文包。")
        if self.is_stale(pack, project):
            pack.status = "stale"
            raise RuntimeError("项目设定、人物卡或参考作品已变化，请重新生成并确认创作上下文包。")
        if pack.status != "confirmed":
            raise RuntimeError("当前创作上下文包尚未确认，请先在生成前校对页面确认。")
        return pack

    def resolved_inputs(self, pack: ContextPack) -> dict[str, Any]:
        payload = self.as_dict(pack)
        story_feed = payload.get("feed_preview", {}).get("story_generation", {})
        video_feed = payload.get("feed_preview", {}).get("video_generation", {})
        return {
            "context_pack_id": payload.get("id"),
            "context_pack_version": payload.get("version_no"),
            "reference_mode": payload.get("reference_mode"),
            "story_feed": story_feed if isinstance(story_feed, dict) else {},
            "video_feed": video_feed if isinstance(video_feed, dict) else {},
            "hard_constraints": payload.get("derived_constraints", {}).get("hard_constraints", []),
            "soft_constraints": payload.get("derived_constraints", {}).get("soft_constraints", []),
            "story_boundary_rules": payload.get("derived_constraints", {}).get("story_boundary_rules", []),
            "character_snapshot": payload.get("character_snapshot", []),
            "reference_snapshot": payload.get("reference_snapshot", {}),
            "project_snapshot": payload.get("project_snapshot", {}),
            "todo_tasks": payload.get("todo_tasks", []),
            "choice_questions": payload.get("choice_questions", []),
        }

    def is_stale(self, pack: ContextPack, project: Project) -> bool:
        return (pack.source_fingerprint or "") != self.compute_fingerprint(project)

    def as_dict(self, pack: ContextPack) -> dict[str, Any]:
        derived_constraints = json_loads_object(pack.derived_constraints_json)
        return {
            "id": pack.id,
            "project_id": pack.project_id,
            "version_no": pack.version_no,
            "status": pack.status,
            "reference_mode": pack.reference_mode,
            "user_notes": pack.user_notes,
            "source_fingerprint": pack.source_fingerprint,
            "project_snapshot": json_loads_object(pack.project_snapshot_json),
            "character_snapshot": json_loads_list(pack.character_snapshot_json),
            "reference_snapshot": json_loads_object(pack.reference_snapshot_json),
            "source_snapshot": json_loads_object(pack.source_snapshot_json),
            "conflict_report": json_loads_list(pack.conflict_report_json),
            "user_decisions": json_loads_object(pack.user_decisions_json),
            "user_guidance": json_loads_list(derived_constraints.get("user_guidance_json", "[]") if isinstance(derived_constraints.get("user_guidance_json"), str) else "[]"),
            "choice_questions": json_loads_list(derived_constraints.get("choice_questions_json", "[]") if isinstance(derived_constraints.get("choice_questions_json"), str) else "[]"),
            "todo_tasks": json_loads_list(derived_constraints.get("todo_tasks_json", "[]") if isinstance(derived_constraints.get("todo_tasks_json"), str) else "[]"),
            "derived_constraints": derived_constraints,
            "feed_preview": json_loads_object(pack.feed_preview_json),
            "confirmed_at": pack.confirmed_at,
            "created_at": pack.created_at,
            "updated_at": pack.updated_at,
        }

    def update_user_decisions(self, pack: ContextPack, user_decisions: dict[str, str]) -> ContextPack:
        current = json_loads_object(pack.user_decisions_json)
        normalized = {str(key): str(value) for key, value in (user_decisions or {}).items() if str(key).strip() and str(value).strip()}
        pack.user_decisions_json = json_dumps({**current, **normalized})
        return pack

    def compute_fingerprint(self, project: Project) -> str:
        source = {
            "project": {
                "title": project.title,
                "genre": project.genre,
                "reference_work": project.reference_work,
                "reference_work_creator": project.reference_work_creator,
                "reference_work_medium": project.reference_work_medium,
                "reference_work_synopsis": project.reference_work_synopsis,
                "reference_work_style_traits": project.reference_work_style_traits,
                "reference_work_world_traits": project.reference_work_world_traits,
                "reference_work_narrative_constraints": project.reference_work_narrative_constraints,
                "reference_work_confidence_note": project.reference_work_confidence_note,
                "reference_inheritance_mode": project.reference_inheritance_mode,
                "reference_rewrite_start": project.reference_rewrite_start,
                "reference_authorized_changes": project.reference_authorized_changes,
                "visual_style_locked": project.visual_style_locked,
                "visual_style_medium": project.visual_style_medium,
                "visual_style_artists": project.visual_style_artists,
                "visual_style_positive": project.visual_style_positive,
                "visual_style_negative": project.visual_style_negative,
                "visual_style_notes": project.visual_style_notes,
                "world_brief": project.world_brief,
                "writing_rules": project.writing_rules,
                "style_profile": project.style_profile,
                "story_boundary_text": project.story_boundary_text,
                "story_boundary_rules": project.story_boundary_rules,
            },
            "characters": [
                {
                    "name": item.name,
                    "age": item.age,
                    "gender": item.gender,
                    "story_role": item.story_role,
                    "personality": item.personality,
                    "background": item.background,
                    "voice_provider": item.voice_provider,
                    "voice_speaker": item.voice_speaker,
                    "voice_style": item.voice_style,
                }
                for item in project.character_cards
                if item.deleted_at is None
            ],
            "memories": [
                {"title": item.title, "content": item.content, "scope": item.memory_scope, "importance": item.importance}
                for item in project.memories
            ],
            "sources": [{"title": item.title, "content": item.content, "source_kind": item.source_kind} for item in project.source_documents],
        }
        return hashlib.sha256(json_dumps(source).encode("utf-8")).hexdigest()

    def _next_version_no(self, db: Session, project_id: int) -> int:
        latest = self.latest_for_project(db, project_id)
        return (latest.version_no + 1) if latest is not None else 1

    def _compose_payload(self, *, project: Project, reference_mode: str, user_notes: str, user_decisions: dict[str, str]) -> dict[str, Any]:
        project_snapshot = {
            "title": project.title,
            "genre": project.genre,
            "world_brief": _compact_text(project.world_brief),
            "writing_rules": _compact_text(project.writing_rules),
            "story_boundary_text": project.story_boundary_text.strip(),
            "story_boundary_rules": project.story_boundary_rules,
            "style_profile": project.style_profile,
            "visual_style_locked": project.visual_style_locked,
            "visual_style_medium": _compact_text(project.visual_style_medium, fallback="未指定"),
            "visual_style_artists": project.visual_style_artists,
            "visual_style_positive": project.visual_style_positive,
            "visual_style_negative": project.visual_style_negative,
            "visual_style_notes": _compact_text(project.visual_style_notes),
            "user_notes": user_notes.strip(),
        }

        character_snapshot = [
            {
                "id": item.id,
                "name": item.name.strip(),
                "age": item.age.strip(),
                "gender": item.gender.strip(),
                "story_role": item.story_role.strip(),
                "personality": item.personality.strip(),
                "background": item.background.strip(),
                "voice_provider": item.voice_provider.strip(),
                "voice_speaker": item.voice_speaker.strip(),
                "voice_style": item.voice_style.strip(),
            }
            for item in project.character_cards
            if item.deleted_at is None
        ]

        reference_snapshot = {
            "mode": reference_mode,
            "reference_work": project.reference_work.strip(),
            "creator": project.reference_work_creator.strip(),
            "medium": project.reference_work_medium.strip(),
            "synopsis": project.reference_work_synopsis.strip(),
            "style_traits": project.reference_work_style_traits,
            "world_traits": project.reference_work_world_traits,
            "narrative_constraints": project.reference_work_narrative_constraints,
            "confidence_note": project.reference_work_confidence_note.strip(),
            "inheritance_mode": project.reference_inheritance_mode,
            "rewrite_start": project.reference_rewrite_start.strip(),
            "authorized_changes": project.reference_authorized_changes.strip(),
        }
        reference_facts = self.reference_policy_service.facts_snapshot(list(getattr(project, "reference_facts", [])))
        reference_snapshot["reference_facts"] = self.reference_policy_service.mark_fact_conflicts(
            reference_facts,
            project.story_boundary_rules,
            authorized_changes=project.reference_authorized_changes,
        )
        reference_snapshot["authorized_overrides"] = [
            item["summary"]
            for item in reference_snapshot["reference_facts"]
            if item.get("status") == "authorized_override" and str(item.get("summary") or "").strip()
        ]

        source_snapshot = {
            "memories": [
                {
                    "title": item.title,
                    "content": item.content,
                    "scope": item.memory_scope,
                    "importance": item.importance,
                }
                for item in sorted(project.memories, key=lambda item: item.importance, reverse=True)
            ],
            "sources": [{"title": item.title, "content": item.content, "source_kind": item.source_kind} for item in project.source_documents],
        }

        conflict_report = self._build_conflict_report(
            project_snapshot=project_snapshot,
            character_snapshot=character_snapshot,
            reference_snapshot=reference_snapshot,
            source_snapshot=source_snapshot,
        )
        derived_constraints = self._build_constraints(
            project_snapshot=project_snapshot,
            character_snapshot=character_snapshot,
            reference_snapshot=reference_snapshot,
            conflict_report=conflict_report,
            user_decisions=user_decisions,
        )
        feed_preview = self._build_feed_preview(
            project_snapshot=project_snapshot,
            character_snapshot=character_snapshot,
            reference_snapshot=reference_snapshot,
            source_snapshot=source_snapshot,
            derived_constraints=derived_constraints,
            user_decisions=user_decisions,
        )

        return {
            "source_fingerprint": self.compute_fingerprint(project),
            "project_snapshot": project_snapshot,
            "character_snapshot": character_snapshot,
            "reference_snapshot": reference_snapshot,
            "source_snapshot": source_snapshot,
            "conflict_report": conflict_report,
            "user_decisions": user_decisions,
            "derived_constraints": derived_constraints,
            "feed_preview": feed_preview,
        }

    def _build_conflict_report(
        self,
        *,
        project_snapshot: dict[str, Any],
        character_snapshot: list[dict[str, Any]],
        reference_snapshot: dict[str, Any],
        source_snapshot: dict[str, Any],
    ) -> list[dict[str, Any]]:
        conflicts: list[dict[str, Any]] = []
        names = [str(item.get("name") or "").strip() for item in character_snapshot if str(item.get("name") or "").strip()]
        duplicate_names = sorted({name for name in names if names.count(name) > 1})
        if duplicate_names:
            conflicts.append(
                {
                    "severity": "error",
                    "code": "duplicate_character_name",
                    "title": "人物姓名重复",
                    "detail": f"人物卡中存在重复姓名：{'、'.join(duplicate_names)}",
                    "related_items": duplicate_names,
                }
            )
        if not character_snapshot:
            conflicts.append(
                {
                    "severity": "warning",
                    "code": "missing_character_cards",
                    "title": "尚未填写人物卡",
                    "detail": "没有人物卡时，后续概要、正文和视频链路的人物一致性会明显下降。",
                    "related_items": [],
                }
            )
        if not str(project_snapshot.get("world_brief") or "").strip() or project_snapshot.get("world_brief") == "未填写":
            conflicts.append(
                {
                    "severity": "warning",
                    "code": "missing_world_brief",
                    "title": "世界观设定较弱",
                    "detail": "当前项目的世界观约束较少，模型更容易自行补设定。",
                    "related_items": [],
                }
            )
        if reference_snapshot.get("mode") in {"content_reference", "hybrid_reference"} and not str(reference_snapshot.get("synopsis") or "").strip():
            conflicts.append(
                {
                    "severity": "warning",
                    "code": "content_reference_without_synopsis",
                    "title": "内容参考缺少结构化摘要",
                    "detail": "你选择了内容参考模式，但参考作品缺少足够的结构化内容，系统不能假设模型天然知道原著全部细节。",
                    "related_items": [str(reference_snapshot.get("reference_work") or "").strip()],
                }
            )
        if reference_snapshot.get("reference_work") and names:
            matched = [name for name in names if name in str(reference_snapshot.get("synopsis") or "")]
            if not matched and reference_snapshot.get("mode") in {"content_reference", "hybrid_reference"}:
                conflicts.append(
                    {
                        "severity": "info",
                        "code": "reference_character_unverified",
                        "title": "原著人物映射未验证",
                        "detail": "当前内容参考模式还没有把人物卡与参考作品摘要中的角色映射明确对齐，建议在生成前检查后确认。",
                        "related_items": names[:6],
                    }
                )
        if not source_snapshot.get("memories") and not source_snapshot.get("sources"):
            conflicts.append(
                {
                    "severity": "info",
                    "code": "limited_supporting_materials",
                    "title": "辅助素材较少",
                    "detail": "当前除了项目设定和人物卡之外，几乎没有长期资料或补充资料可供约束生成。",
                    "related_items": [],
                }
            )
        return conflicts

    def _build_constraints(
        self,
        *,
        project_snapshot: dict[str, Any],
        character_snapshot: list[dict[str, Any]],
        reference_snapshot: dict[str, Any],
        conflict_report: list[dict[str, Any]],
        user_decisions: dict[str, str],
    ) -> dict[str, Any]:
        character_names = [item["name"] for item in character_snapshot if item.get("name")]
        story_boundary_rules = (
            project_snapshot.get("story_boundary_rules", [])
            if isinstance(project_snapshot.get("story_boundary_rules"), list)
            else []
        )
        hard_constraints = [
            "已确认人物姓名不得漂移或替换。",
            "已确认人物性别、身份、角色定位不得与人物卡冲突。",
            "世界观、写作规则和视觉风格锁定内容必须优先服从。",
        ]
        if reference_snapshot.get("mode") in {"content_reference", "hybrid_reference"}:
            hard_constraints.append("内容参考模式下，确认过的参考作品核心设定不能被随意违背。")
        hard_constraints.extend(self.reference_policy_service.hard_constraints(reference_snapshot))
        for fact in reference_snapshot.get("reference_facts", []):
            if not isinstance(fact, dict):
                continue
            summary = str(fact.get("summary") or "").strip()
            status = str(fact.get("status") or "").strip()
            if status == "conflict":
                hard_constraints.append(f"参考事实冲突待确认：{summary}")
            elif status == "authorized_override":
                hard_constraints.append(f"参考事实已授权改写：{summary}")
            elif summary:
                hard_constraints.append(f"默认继承参考事实：{summary}")
        hard_constraints.extend(self.story_boundary_service.prompt_lines(story_boundary_rules))
        soft_constraints = [
            f"风格档位：{project_snapshot.get('style_profile')}",
            "参考作品默认只提供可迁移的风格、叙事与镜头约束。",
        ]
        user_guidance, choice_questions, todo_tasks = self._build_user_guidance(
            conflict_report=conflict_report,
            reference_snapshot=reference_snapshot,
            character_snapshot=character_snapshot,
            user_decisions=user_decisions,
        )
        return {
            "hard_constraints": hard_constraints,
            "soft_constraints": soft_constraints,
            "story_boundary_rules": story_boundary_rules,
            "locked_character_names": character_names,
            "locked_reference_mode": reference_snapshot.get("mode") or "style_reference",
            "user_decisions": user_decisions,
            "user_guidance_json": json_dumps(user_guidance),
            "choice_questions_json": json_dumps(choice_questions),
            "todo_tasks_json": json_dumps(todo_tasks),
        }

    def _build_user_guidance(
        self,
        *,
        conflict_report: list[dict[str, Any]],
        reference_snapshot: dict[str, Any],
        character_snapshot: list[dict[str, Any]],
        user_decisions: dict[str, str],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        guidance: list[dict[str, Any]] = []
        questions: list[dict[str, Any]] = []
        tasks: list[dict[str, Any]] = []

        for item in conflict_report:
            code = str(item.get("code") or "")
            if code == "duplicate_character_name":
                guidance.append(
                    {
                        "title": "先统一重复人物姓名",
                        "detail": item.get("detail") or "",
                        "suggested_action": "回到人物卡页面，给重复角色改成唯一名字，再重新生成校对稿。",
                    }
                )
                tasks.append(
                    {
                        "task_id": "fix_duplicate_character_names",
                        "title": "修复重复人物名",
                        "detail": "保证每张人物卡对应唯一姓名，避免后续概要和正文混淆角色。",
                        "status": "todo",
                    }
                )
            elif code == "missing_character_cards":
                guidance.append(
                    {
                        "title": "先补主要人物卡",
                        "detail": item.get("detail") or "",
                        "suggested_action": "至少补齐男女主、关键配角和反派的人物卡，再进入概要和正文生成。",
                    }
                )
                tasks.append(
                    {
                        "task_id": "add_primary_character_cards",
                        "title": "补充主要人物卡",
                        "detail": "至少补齐主角、关键配角和主要冲突角色。",
                        "status": "todo",
                    }
                )
            elif code == "content_reference_without_synopsis":
                questions.append(
                    {
                        "question_id": "reference_content_strategy",
                        "question": "你希望参考作品走哪一版？",
                        "options": ["只参考风格", "只参考内容", "内容和风格都参考"],
                        "recommendation": "如果你既要原著内容边界，又要整体气质，推荐选择内容和风格都参考，并补结构化原著摘要。",
                    }
                )
                tasks.append(
                    {
                        "task_id": "add_reference_structured_summary",
                        "title": "补充原著结构化摘要",
                        "detail": "给参考作品补上角色、关系、世界规则和叙事禁区摘要。",
                        "status": "todo",
                    }
                )
            elif code == "reference_character_unverified":
                guidance.append(
                    {
                        "title": "确认人物卡与原著角色的映射",
                        "detail": item.get("detail") or "",
                        "suggested_action": "明确哪些人物卡是在复现原著角色，哪些只是借鉴气质，避免系统混写。",
                    }
                )
                questions.append(
                    {
                        "question_id": "reference_character_mapping",
                        "question": "这些人物卡你想走哪一版？",
                        "options": ["严格对齐原著角色", "只保留气质和关系，不保留原著角色身份"],
                        "recommendation": "如果你希望系统检查是否符合原著，推荐严格对齐原著角色。",
                    }
                )

        if reference_snapshot.get("reference_work") and reference_snapshot.get("mode") in {"content_reference", "hybrid_reference"}:
            tasks.append(
                {
                    "task_id": "confirm_reference_version_strategy",
                    "title": "确认参考作品版本策略",
                    "detail": "明确后续生成是‘严格贴近原著’还是‘借原著改写原创’。",
                    "status": "todo",
                }
            )
        if character_snapshot and not any(item.get("story_role") for item in character_snapshot):
            guidance.append(
                {
                    "title": "补角色定位会更稳",
                    "detail": "当前部分人物卡没有明确 story_role，后续模型更容易误判出场优先级。",
                    "suggested_action": "给主要人物补上主角、女主、反派、导师等角色定位。",
                }
            )
            tasks.append(
                {
                    "task_id": "fill_story_roles",
                    "title": "补主要人物 story_role",
                    "detail": "为主要人物补全角色定位字段，降低概要和正文错配概率。",
                    "status": "todo",
                }
            )

        decisions = user_decisions if isinstance(user_decisions, dict) else {}
        for task in tasks:
            task_id = str(task.get("task_id") or "").strip()
            if task_id and decisions.get(f"task:{task_id}"):
                task["status"] = str(decisions.get(f"task:{task_id}") or "todo")

        return guidance, questions, tasks

    def _build_feed_preview(
        self,
        *,
        project_snapshot: dict[str, Any],
        character_snapshot: list[dict[str, Any]],
        reference_snapshot: dict[str, Any],
        source_snapshot: dict[str, Any],
        derived_constraints: dict[str, Any],
        user_decisions: dict[str, str],
    ) -> dict[str, Any]:
        return {
            "story_generation": {
                "project_core": {
                    "title": project_snapshot.get("title"),
                    "genre": project_snapshot.get("genre"),
                    "world_brief": project_snapshot.get("world_brief"),
                    "writing_rules": project_snapshot.get("writing_rules"),
                "story_boundary_text": project_snapshot.get("story_boundary_text"),
                "reference_policy": self.reference_policy_service.prompt_block(reference_snapshot),
            },
                "character_constraints": character_snapshot[:12],
                "reference_constraints": reference_snapshot,
                "supporting_memories": source_snapshot.get("memories", [])[:12],
                "supporting_sources": source_snapshot.get("sources", [])[:6],
                "user_decisions": user_decisions,
                "hard_constraints": derived_constraints.get("hard_constraints", []),
                "soft_constraints": derived_constraints.get("soft_constraints", []),
                "story_boundary_rules": derived_constraints.get("story_boundary_rules", []),
            },
            "video_generation": {
                "visual_style_medium": project_snapshot.get("visual_style_medium"),
                "visual_style_notes": project_snapshot.get("visual_style_notes"),
                "visual_style_artists": project_snapshot.get("visual_style_artists", []),
                "character_visual_anchors": [
                    {
                        "name": item.get("name"),
                        "story_role": item.get("story_role"),
                        "background": item.get("background"),
                    }
                    for item in character_snapshot[:12]
                ],
                "user_decisions": user_decisions,
                "reference_constraints": reference_snapshot,
                "hard_constraints": derived_constraints.get("hard_constraints", []),
            },
        }
