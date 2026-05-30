from __future__ import annotations

from .models import Project, StoryboardShot


def project_visual_style_summary(project: Project) -> dict[str, list[str] | str | bool]:
    """Return user-facing and prompt-facing visual style constraints for a project."""
    reference = (project.reference_work or "").strip()
    medium = (project.visual_style_medium or "").strip()
    artists = _clean_list(project.visual_style_artists)
    positive = _clean_list(project.visual_style_positive)
    negative = _clean_list(project.visual_style_negative)

    style_name = medium or "未指定画面媒介"
    if artists:
        style_name = f"{medium or '未指定画面媒介'}，参考：{'、'.join(artists[:4])}"
    elif reference:
        style_name = f"{medium or '未指定画面媒介'}，参考《{reference}》的可迁移视觉特征"

    return {
        "reference": reference,
        "locked": bool(project.visual_style_locked),
        "style_name": style_name,
        "medium": medium,
        "artists": _dedupe(artists),
        "positive": _dedupe(positive),
        "negative": _dedupe(negative),
        "notes": (project.visual_style_notes or "").strip(),
    }


def build_visual_style_block(project: Project) -> str:
    summary = project_visual_style_summary(project)
    reference = summary["reference"]
    reference_line = f"参考作品：{reference}" if reference else "参考作品：无"
    artist_line = f"作者/工作室风格参考：{'；'.join(summary['artists'])}" if summary["artists"] else "作者/工作室风格参考：无"
    expanded_style = _expanded_style_notes(reference=reference, artists=summary["artists"])
    positive = "；".join(summary["positive"]) if summary["positive"] else ""
    negative = "；".join(summary["negative"]) if summary["negative"] else ""
    notes = str(summary["notes"]).strip()
    locked = "开启" if summary["locked"] else "未开启"
    lines = [
        "项目级视觉风格锁定：",
        f"锁定状态：{locked}",
        reference_line,
        f"画面媒介：{summary['medium'] or '未指定'}",
        artist_line,
    ]
    if expanded_style:
        lines.append(f"可迁移视觉要点：{expanded_style}")
    if positive:
        lines.append(f"补充风格提示：{positive}")
    if negative:
        lines.append(f"明确避开：{negative}")
    if notes:
        lines.append(f"补充说明：{notes}")
    lines.append("如果镜头内容与风格冲突，优先保持项目级视觉风格和角色一致性。")
    return "\n".join(lines).strip()


def build_visual_generation_prompt(
    *,
    project: Project,
    shot: StoryboardShot,
    include_narration: bool = True,
    max_length: int = 1800,
) -> str:
    parts = [
        build_visual_style_block(project),
        "项目视觉上下文：",
        f"项目名：{project.title}",
        f"类型：{project.genre or '未指定'}",
        f"世界观：{(project.world_brief or '暂无').strip()[:500]}",
        _reference_constraint_block(shot),
        "镜头画面：",
        shot.visual_prompt.strip(),
        "镜头生成要求：优先遵守镜头角色约束和场景约束，其次遵守项目级视觉风格；每个镜头必须像正式动画电影分镜，不要像默认 AI 素材或流水线模板。",
        "画面必须有明确机位、景别、主体关系、前中后景、光源方向、空气质感、色彩层次和情绪目的；避免空泛的“电影感”“唯美”“高质量”。",
        "角色外观必须继承已锁定三视图或角色视觉锚点，不要换脸、换发型、换服装主色；动作自然，画面稳定，避免文字、水印、字幕、logo。",
    ]
    narration = shot.narration_text.strip()
    if include_narration and narration:
        parts.append(f"剧情信息：{narration}")
    return "\n".join(part for part in parts if part).strip()[:max_length]


def build_character_visual_prompt(
    *,
    project: Project,
    character_details: list[str],
    prompt_note: str = "",
    max_length: int = 1800,
) -> str:
    parts = [
        build_visual_style_block(project),
        "为小说视频化生成角色三视图设定图。",
        *[item for item in character_details if item.strip()],
    ]
    if prompt_note.strip():
        parts.append(f"本章造型要求：{prompt_note.strip()}")
    parts.extend(
        [
            "输出一张干净的角色 turnaround sheet，同一角色同一服装，包含正面、侧面、背面三视图，三个人物等高排列。",
            "背景保持设定稿用途的浅色干净底，可加入极淡的天空色、雨光、窗光或色块氛围，但不要画成完整场景。",
            "完整站姿，全身入画，表情中性，服装细节清晰，横向排版，三视图之间留出清楚间距。",
            "角色必须符合项目级画面媒介和作者/工作室风格参考，不要偏离用户锁定的视觉方向。",
            "必须强化这个角色自己的识别点：独特脸型、发型轮廓、主色与辅色、服装材质、鞋包或随身物件，不要生成通用模板脸。",
            "如果批量生成多个角色，每个角色都要有明显不同的身高体态、轮廓语言、配色方案和服装层次，但保持同一项目的统一美术体系。",
            "画面要像可交给动画团队继续制作的角色设定图：干净、精致、有审美判断，不要像随机游戏立绘拼贴。",
            "不要文字、不要水印、不要 logo、不要背景场景、不要多余角色、不要夸张姿势、不要畸形手指、不要脸部变形。",
        ]
    )
    return "\n".join(parts).strip()[:max_length]


def _expanded_style_notes(*, reference: str, artists: list[str]) -> str:
    text = " ".join([reference, *artists]).lower()
    if not text:
        return ""
    notes: list[str] = []
    if "新海诚" in text or "shinkai" in text:
        notes.extend(
            [
                "现代日系动画电影感",
                "通透高饱和但不脏的天空与云层",
                "逆光、边缘光、空气透视和细腻环境光",
                "真实城市或校园生活质感",
                "干净线稿与精细背景细节",
                "蓝、青、粉橙等冷暖分层色彩",
            ]
        )
    return "；".join(_dedupe(notes))


def _reference_constraint_block(shot: StoryboardShot) -> str:
    character_refs = _normalize_refs(shot.character_refs_json)
    scene_refs = _normalize_refs(shot.scene_refs_json)
    lines: list[str] = []
    if character_refs:
        lines.append("镜头角色约束：")
        for item in character_refs[:6]:
            name = str(item.get("name") or item.get("character_name") or item.get("value") or "").strip()
            role = str(item.get("story_role") or item.get("role") or "").strip()
            look = str(item.get("appearance") or item.get("look") or item.get("description") or "").strip()
            pieces = [piece for piece in [name, role, look] if piece]
            if pieces:
                lines.append(f"- {' / '.join(pieces)}")
    if scene_refs:
        lines.append("镜头场景约束：")
        for item in scene_refs[:6]:
            name = str(item.get("name") or item.get("scene_name") or item.get("value") or "").strip()
            mood = str(item.get("mood") or item.get("lighting") or item.get("description") or "").strip()
            props = str(item.get("props") or item.get("layout") or "").strip()
            pieces = [piece for piece in [name, mood, props] if piece]
            if pieces:
                lines.append(f"- {' / '.join(pieces)}")
    return "\n".join(lines).strip()


def _normalize_refs(value: object) -> list[dict[str, object]]:
    if isinstance(value, str):
        try:
            import json

            parsed = json.loads(value)
        except Exception:
            return []
        if isinstance(parsed, list):
            normalized: list[dict[str, object]] = []
            for item in parsed:
                if isinstance(item, dict):
                    normalized.append(item)
                elif isinstance(item, str) and item.strip():
                    normalized.append({"value": item.strip()})
            return normalized
        return []
    if isinstance(value, list):
        normalized: list[dict[str, object]] = []
        for item in value:
            if isinstance(item, dict):
                normalized.append(item)
            elif isinstance(item, str) and item.strip():
                normalized.append({"value": item.strip()})
        return normalized
    return []


def _clean_list(values: list[str]) -> list[str]:
    return [str(item).strip() for item in values if str(item).strip()]


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result
