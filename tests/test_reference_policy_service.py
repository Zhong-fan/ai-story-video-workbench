from __future__ import annotations

import unittest
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.context_pack_service import ContextPackService
from app.db import Base
from app.models import Project, ReferenceFact, User
from app.reference_policy_service import ReferencePolicyService


class ReferencePolicyServiceTests(unittest.TestCase):
    def test_builds_prompt_block_from_snapshot(self) -> None:
        service = ReferencePolicyService()
        snapshot = {
            "reference_work": "天气之子",
            "inheritance_mode": "strict_inherit",
            "rewrite_start": "电影结尾之后续写",
            "authorized_changes": "允许改写后续剧情，但原作既有事实默认继承。",
        }
        block = service.prompt_block(snapshot)
        self.assertIn("天气之子", block)
        self.assertIn("默认继承", block)
        self.assertIn("电影结尾之后续写", block)
        self.assertIn("允许改写后续剧情", block)

    def test_context_pack_includes_reference_policy_hard_constraints(self) -> None:
        service = ContextPackService()
        project = SimpleNamespace(
            title="测试项目",
            genre="现代都市",
            reference_work="天气之子",
            reference_work_creator="新海诚",
            reference_work_medium="动画电影",
            reference_work_synopsis="一个围绕东京、天气与相遇展开的故事。",
            reference_work_style_traits=["透明感"],
            reference_work_world_traits=["都市雨天"],
            reference_work_narrative_constraints=["不能直接照搬原作剧情节点"],
            reference_work_confidence_note="高置信度",
            reference_inheritance_mode="strict_inherit",
            reference_rewrite_start="电影结尾之后续写",
            reference_authorized_changes="允许改写续作剧情，但不允许篡改原作既有事实。",
            story_boundary_text="",
            story_boundary_rules=[],
            visual_style_locked=True,
            visual_style_medium="动画电影",
            visual_style_artists=["新海诚"],
            visual_style_positive=[],
            visual_style_negative=[],
            visual_style_notes="",
            world_brief="现代东京背景",
            writing_rules="保持透明、克制、轻盈。",
            style_profile="light_novel",
            character_cards=[],
            memories=[],
            source_documents=[],
        )
        payload = service._compose_payload(
            project=project,
            reference_mode="content_reference",
            user_notes="",
            user_decisions={},
        )
        derived = payload["derived_constraints"]
        hard_constraints = derived["hard_constraints"]
        self.assertTrue(any("原作事实默认继承" in item for item in hard_constraints))
        self.assertTrue(any("电影结尾之后续写" in item for item in hard_constraints))
        self.assertEqual(payload["reference_snapshot"]["inheritance_mode"], "strict_inherit")
        self.assertEqual(payload["reference_snapshot"]["rewrite_start"], "电影结尾之后续写")

    def test_syncs_derived_reference_facts_to_database(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine, future=True)
        service = ReferencePolicyService()

        with SessionLocal() as session:
            user = User(email="user@example.com", display_name="测试用户", password_hash=b"0" * 32, password_salt=b"1" * 16)
            project = Project(
                owner=user,
                title="天气之子续作",
                genre="现代都市",
                reference_work="天气之子",
                reference_work_synopsis="帆高与阳菜在东京重逢，天气规则仍影响城市。",
                reference_inheritance_mode="strict_inherit",
                reference_rewrite_start="电影结尾之后",
                reference_authorized_changes="允许续写后续剧情。",
            )
            project.reference_work_world_traits = ["持续降雨后的东京", "天气与祈愿有关"]
            project.reference_work_narrative_constraints = ["电影结尾前的关系状态必须成立"]
            session.add(project)
            session.commit()

            facts = service.sync_project_reference_facts(session, project)
            session.commit()

            persisted = session.query(ReferenceFact).filter(ReferenceFact.project_id == project.id).all()
            self.assertEqual(len(persisted), len(facts))
            self.assertTrue(any(item.fact_type == "relationship_state" for item in persisted))
            self.assertTrue(any(item.fact_type == "world_rule" for item in persisted))
            self.assertTrue(all(item.status == "active" for item in persisted))

    def test_marks_reference_fact_conflicts_and_authorized_overrides(self) -> None:
        service = ReferencePolicyService()
        facts = [
            {
                "fact_type": "relationship_state",
                "reference_key": "天气之子:rewrite_baseline",
                "summary": "改写起点前，帆高与阳菜已经重逢。",
                "status": "active",
            }
        ]
        rules = [
            {
                "rule_id": "story-boundary-1",
                "rule_type": "forbid_event",
                "predicate": "direct_meeting",
                "subjects": ["帆高", "阳菜"],
                "scope_type": "chapter_range",
                "start_chapter_no": 1,
                "end_chapter_no": 10,
                "instruction": "第1到10章帆高和阳菜不要相遇。",
            }
        ]

        conflicts = service.mark_fact_conflicts(facts, rules, authorized_changes="")
        authorized = service.mark_fact_conflicts(facts, rules, authorized_changes="允许改写帆高和阳菜的重逢关系。")

        self.assertEqual(conflicts[0]["status"], "conflict")
        self.assertEqual(conflicts[0]["conflict_rule_ids"], ["story-boundary-1"])
        self.assertEqual(authorized[0]["status"], "authorized_override")


if __name__ == "__main__":
    unittest.main()
