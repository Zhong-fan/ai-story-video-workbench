from __future__ import annotations

from textwrap import dedent
from typing import Any

from .config import Settings
from .json_utils import parse_json_object
from .llm import OpenAIResponsesLLM
from .models import NovelChapter, Project
from .visual_style_prompt import build_visual_style_block


class StoryboardService:
    def __init__(self, settings: Settings) -> None:
        if settings.llm_mode != "openai" or not settings.openai_api_key:
            raise RuntimeError("当前项目只支持真实模型模式。")
        self.settings = settings
        self.llm = OpenAIResponsesLLM(
            settings.openai_api_key,
            settings.openai_base_url,
            use_system_proxy=settings.openai_use_system_proxy,
            use_responses=settings.llm_use_responses,
            stream_responses=settings.llm_stream_responses,
            request_timeout_seconds=settings.llm_request_timeout_seconds,
            max_attempts=settings.llm_max_attempts,
            retry_max_sleep_seconds=settings.llm_retry_max_sleep_seconds,
        )

    def generate_storyboard(
        self,
        *,
        project: Project,
        chapters: list[NovelChapter],
        title: str,
        context_pack_inputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        video_feed = context_pack_inputs.get("video_feed", {}) if isinstance(context_pack_inputs, dict) else {}
        project_snapshot = context_pack_inputs.get("project_snapshot", {}) if isinstance(context_pack_inputs, dict) else {}
        hard_constraints = context_pack_inputs.get("hard_constraints", []) if isinstance(context_pack_inputs, dict) else []
        user_decisions = video_feed.get("user_decisions", {}) if isinstance(video_feed, dict) else {}
        reference_constraints = video_feed.get("reference_constraints", {}) if isinstance(video_feed, dict) else {}
        character_visual_anchors = video_feed.get("character_visual_anchors", []) if isinstance(video_feed, dict) else []
        character_directory = [
            {"character_card_id": card.id, "name": card.name, "story_role": card.story_role}
            for card in project.character_cards
            if card.deleted_at is None
        ]
        chapter_text = "\n\n".join(
            f"第 {chapter.chapter_no} 章《{chapter.title}》\n摘要：{chapter.summary}\n正文节选：{chapter.content[:5000]}"
            for chapter in chapters
        )
        system_prompt = dedent(
            """
            你是小说视频化分镜导演和动画美术指导。请把已定稿章节转成图像驱动、轻运镜、视觉叙事优先的短片分镜。
            重点不是流水线凑镜头，而是为每个镜头找到独特的情绪、构图、光影和角色状态。
            输出必须是严格 JSON，不要输出 Markdown。
            """
        ).strip()
        prompt = f"""
项目：{project_snapshot.get("title") or project.title}
类型：{project_snapshot.get("genre") or project.genre}
短片标题：{title}

{build_visual_style_block(project)}

世界设定：
{project_snapshot.get("world_brief") or project.world_brief or "暂无"}

已确认角色视觉锚点：
{character_visual_anchors}

角色 ID 目录：
{character_directory}

已确认参考作品约束：
{reference_constraints}

用户已确认的版本选择：
{user_decisions}

已定稿章节：
{chapter_text}

请输出：
{{
  "title": "...",
  "summary": "短片概述",
  "shots": [
    {{
      "shot_no": 1,
      "narration_text": "旁白/字幕文本",
      "visual_prompt": "可直接用于图像/视频模型的画面提示词，包含角色、场景、景别、机位、构图、光线、色彩、空气质感、情绪",
      "character_refs": [{{"character_card_id": 1, "name": "角色名", "role": "角色在镜头中的作用"}}],
      "scene_refs": [{{"name": "场景名", "role": "场景用途"}}],
      "continuity": {{
        "shot_type": "new|continuation|camera_move|transition",
        "depends_on_shot_no": null,
        "first_frame_source": "generated|previous_last_frame",
        "requires_i2v": true,
        "end_frame_usage": "none|feeds_next",
        "camera_motion": "无|推进|横移|摇镜|拉远",
        "character_state_delta": "角色状态变化",
        "continuity_constraints": ["必须保持的角色、服装、场景和构图连续性"]
      }},
      "audio_script": {{
        "dialogues": [
          {{
            "character_name": "说话角色名",
            "line": "从小说正文和当前镜头意图自动生成的角色对白",
            "emotion": "novel_dialog|soft|sad|angry|hopeful|hesitant",
            "voice_profile": "",
            "start_hint": 0.2,
            "duration_hint": 2.8
          }}
        ],
        "narration": "可选旁白，能不用就留空",
        "subtitle_text": "可用于字幕的压缩文本",
        "music_cue": "音乐氛围提示，例如雨夜、钢琴、轻弦乐、压抑但温柔",
        "sound_effects": ["雨声", "脚步声"]
      }},
      "duration_seconds": 4
    }}
  ]
}}

要求：
- 生成 6 到 12 个镜头。
- 每个镜头都能独立转成图片提示词。
- 每个 visual_prompt 必须明确写出画面媒介、美术方向、角色外观、场景、构图、景别、机位、光影、色彩和空气质感。
- 每个镜头必须从当前章节的具体情节、物件、环境或人物关系中抽取视觉锚点，不要生成“人物站在背景前”的通用镜头。
- 镜头之间要有节奏变化：远景、近景、特写、过肩、低机位、俯视、窗内外反差、前景遮挡等要合理分布，不要重复同一构图。
- visual_prompt 要像给图像/视频模型的最终提示词，直接可用，不要写“表现出”“体现出”这类抽象说明。
- 必须遵守项目级视觉风格锁定；如果用户填写了作者/工作室画风参考，只借鉴可迁移的美术特征，不要复刻原作角色、剧情、专有名词或具体画面。
- 不要改写章节既定事实。
- character_refs 必须返回对象数组，character_card_id 必须来自“角色 ID 目录”；无法确定时保留 name 并省略 ID。
- 每个镜头必须返回 continuity；continuation 和 camera_move 镜头要设置 first_frame_source 为 previous_last_frame，并写明 depends_on_shot_no。
- 必须遵守以下硬约束：{hard_constraints}
- 配音和对白是可选项；没有自然对白时，`audio_script.dialogues` 可以为空，不要为了配音硬塞台词。
- 如果原文没有适合对白，可以用极短旁白或字幕补足信息；视觉叙事优先。
- `audio_script.dialogues` 只包含当前镜头内合理会说出口的话，不要把大段叙述硬改成台词。
- `music_cue` 和 `sound_effects` 只写提示，不生成歌词、旋律名或受版权保护的曲名。
""".strip()
        response = self.llm.generate(
            model=self.settings.utility_model,
            system_prompt=system_prompt,
            user_prompt=prompt,
            json_mode=True,
        )
        payload = parse_json_object(response.text)
        if not isinstance(payload.get("shots"), list):
            raise RuntimeError("分镜模型没有返回 shots。")
        return payload
