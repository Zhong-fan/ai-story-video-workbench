from __future__ import annotations

import base64
import hashlib
import time
import urllib.request
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from .config import Settings
from .jimeng_image_client import JimengImageClient
from .json_utils import json_dumps, json_loads_object
from .models import CharacterCard, MediaAsset, Project, Storyboard, StoryboardShot, TaskEvent
from .video_render_service import VideoRenderService
from .visual_style_prompt import build_character_visual_prompt, build_visual_generation_prompt, project_visual_style_summary


class VisualAssetService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_shot_first_frame(
        self,
        *,
        db: Session,
        project: Project,
        storyboard: Storyboard,
        shot: StoryboardShot,
        context_pack_inputs: dict[str, Any] | None = None,
    ) -> MediaAsset:
        self._require_jimeng_image_config()
        existing_assets = db.query(MediaAsset).filter(
            MediaAsset.project_id == project.id,
            MediaAsset.storyboard_id == storyboard.id,
            MediaAsset.shot_id == shot.id,
            MediaAsset.asset_type == "shot_first_frame",
        ).all()
        for asset in existing_assets:
            meta = json_loads_object(asset.meta_json)
            if asset.status == "completed" and meta.get("locked") is True:
                return asset

        prompt = build_visual_generation_prompt(project=project, shot=shot, include_narration=False, max_length=1800)
        client = JimengImageClient(
            access_key=self.settings.jimeng_access_key,
            secret_key=self.settings.jimeng_secret_key,
            endpoint=self.settings.jimeng_endpoint,
            region=self.settings.jimeng_region,
            service=self.settings.jimeng_service,
            req_key=self.settings.jimeng_image_req_key,
        )
        task_id, submit_response = client.submit_text_to_image(
            prompt=prompt,
            width=self.settings.jimeng_image_width,
            height=self.settings.jimeng_image_height,
        )
        if task_id:
            image_payload, result_response = self._wait_for_image_result(client=client, task_id=task_id)
        else:
            data = submit_response.get("data") if isinstance(submit_response.get("data"), dict) else {}
            urls = client._extract_image_urls(data)
            images = client._extract_image_base64(data)
            if urls:
                image_payload = {"kind": "url", "value": urls[0]}
            elif images:
                image_payload = {"kind": "base64", "value": images[0]}
            else:
                raise RuntimeError("即梦图片接口没有返回 task_id 或图片 URL。")
            result_response = submit_response

        output_dir = self._shot_visual_output_dir(project=project, storyboard=storyboard, shot=shot)
        output_dir.mkdir(parents=True, exist_ok=True)
        image_path = output_dir / f"shot-{shot.shot_no:03d}-first-frame-v001.png"
        self._save_image_payload(payload=image_payload, path=image_path)
        provider_debug_path = self._provider_debug_path(image_path)
        self._write_provider_debug_sidecar(
            path=provider_debug_path,
            payload={
                "provider": "jimeng",
                "asset_type": "shot_first_frame",
                "shot_id": shot.id,
                "shot_no": shot.shot_no,
                "task_id": task_id,
                "submit_response": self._sanitize_provider_payload(submit_response),
                "result_response": self._sanitize_provider_payload(result_response),
            },
        )

        asset = next((item for item in existing_assets if item.asset_type == "shot_first_frame"), None)
        if asset is None:
            asset = MediaAsset(
                project_id=project.id,
                storyboard=storyboard,
                shot=shot,
                asset_type="shot_first_frame",
                uri=str(image_path),
                prompt=prompt,
                status="completed",
                meta_json=json_dumps({}),
            )
            db.add(asset)

        asset.uri = str(image_path)
        asset.prompt = prompt
        asset.status = "completed"
        existing_meta = self._compact_asset_meta(json_loads_object(asset.meta_json))
        asset.meta_json = json_dumps(
            {
                **existing_meta,
                "shot_id": shot.id,
                "shot_no": shot.shot_no,
                "locked": False,
                "provider": "jimeng",
                "req_key": self.settings.jimeng_image_req_key,
                "jimeng_task_id": task_id,
                "provider_debug_uri": str(provider_debug_path),
                "submit_summary": self._summarize_jimeng_image_response(submit_response),
                "result_summary": self._summarize_jimeng_image_response(result_response),
                "image_source": image_payload["kind"],
                "width": self.settings.jimeng_image_width,
                "height": self.settings.jimeng_image_height,
                "mime_type": "image/png",
                "visual_style": project_visual_style_summary(project),
                "context_pack_id": context_pack_inputs.get("context_pack_id") if isinstance(context_pack_inputs, dict) else None,
                "context_pack_version": context_pack_inputs.get("context_pack_version") if isinstance(context_pack_inputs, dict) else None,
                "context_pack_reference_mode": context_pack_inputs.get("reference_mode") if isinstance(context_pack_inputs, dict) else None,
            }
        )
        db.add(
            TaskEvent(
                project_id=project.id,
                storyboard=storyboard,
                event_type="visual_asset_shot_first_frame_completed",
                message=f"镜头 {shot.shot_no} 首帧生成完成。",
                payload_json=json_dumps({"asset_type": "shot_first_frame", "shot_id": shot.id, "shot_no": shot.shot_no, "uri": str(image_path)}),
            )
        )
        db.commit()
        db.refresh(asset)
        return asset

    def generate_character_turnaround(
        self,
        *,
        db: Session,
        project: Project,
        character: CharacterCard,
        chapter_no: int | None = None,
        prompt_note: str = "",
        context_pack_inputs: dict[str, Any] | None = None,
    ) -> MediaAsset:
        self._require_jimeng_image_config()
        locked_existing = db.query(MediaAsset).filter(
            MediaAsset.project_id == project.id,
            MediaAsset.asset_type == "character_turnaround",
        ).all()
        for asset in locked_existing:
            meta = json_loads_object(asset.meta_json)
            if (
                asset.status == "completed"
                and meta.get("character_card_id") == character.id
                and meta.get("locked") is True
            ):
                return asset
        prompt = self._build_turnaround_prompt(project=project, character=character, prompt_note=prompt_note)
        client = JimengImageClient(
            access_key=self.settings.jimeng_access_key,
            secret_key=self.settings.jimeng_secret_key,
            endpoint=self.settings.jimeng_endpoint,
            region=self.settings.jimeng_region,
            service=self.settings.jimeng_service,
            req_key=self.settings.jimeng_image_req_key,
        )
        task_id, submit_response = client.submit_text_to_image(
            prompt=prompt,
            width=self.settings.jimeng_image_width,
            height=self.settings.jimeng_image_height,
        )
        if task_id:
            image_payload, result_response = self._wait_for_image_result(client=client, task_id=task_id)
        else:
            data = submit_response.get("data") if isinstance(submit_response.get("data"), dict) else {}
            urls = client._extract_image_urls(data)
            images = client._extract_image_base64(data)
            if urls:
                image_payload = {"kind": "url", "value": urls[0]}
            elif images:
                image_payload = {"kind": "base64", "value": images[0]}
            else:
                raise RuntimeError("即梦图片接口没有返回 task_id 或图片 URL。")
            result_response = submit_response

        output_dir = self._visual_output_dir(project=project, chapter_no=chapter_no, character=character)
        output_dir.mkdir(parents=True, exist_ok=True)
        image_path = output_dir / "turnaround-v001.png"
        self._save_image_payload(payload=image_payload, path=image_path)
        provider_debug_path = self._provider_debug_path(image_path)
        self._write_provider_debug_sidecar(
            path=provider_debug_path,
            payload={
                "provider": "jimeng",
                "asset_type": "character_turnaround",
                "character_card_id": character.id,
                "character_name": character.name,
                "task_id": task_id,
                "submit_response": self._sanitize_provider_payload(submit_response),
                "result_response": self._sanitize_provider_payload(result_response),
            },
        )

        asset = MediaAsset(
            project_id=project.id,
            storyboard_id=None,
            shot_id=None,
            asset_type="character_turnaround",
            uri=str(image_path),
            prompt=prompt,
            status="completed",
            meta_json=json_dumps(
                {
                    "character_card_id": character.id,
                    "character_name": character.name,
                    "version": 1,
                    "locked": False,
                    "views": ["front", "side", "back"],
                    "provider": "jimeng",
                    "req_key": self.settings.jimeng_image_req_key,
                    "jimeng_task_id": task_id,
                    "provider_debug_uri": str(provider_debug_path),
                    "submit_summary": self._summarize_jimeng_image_response(submit_response),
                    "result_summary": self._summarize_jimeng_image_response(result_response),
                    "image_source": image_payload["kind"],
                    "width": self.settings.jimeng_image_width,
                    "height": self.settings.jimeng_image_height,
                    "mime_type": "image/png",
                    "visual_style": project_visual_style_summary(project),
                    "context_pack_id": context_pack_inputs.get("context_pack_id") if isinstance(context_pack_inputs, dict) else None,
                    "context_pack_version": context_pack_inputs.get("context_pack_version") if isinstance(context_pack_inputs, dict) else None,
                    "context_pack_reference_mode": context_pack_inputs.get("reference_mode") if isinstance(context_pack_inputs, dict) else None,
                }
            ),
        )
        db.add(asset)
        db.add(
            TaskEvent(
                project_id=project.id,
                event_type="visual_asset_character_turnaround_completed",
                message=f"{character.name} 三视图生成完成。",
                payload_json=json_dumps({"asset_type": asset.asset_type, "uri": str(image_path), "character_card_id": character.id}),
            )
        )
        db.commit()
        db.refresh(asset)
        return asset

    def _require_jimeng_image_config(self) -> None:
        missing = []
        if not self.settings.jimeng_access_key:
            missing.append("JIMENG_ACCESS_KEY")
        if not self.settings.jimeng_secret_key:
            missing.append("JIMENG_SECRET_KEY")
        if not self.settings.jimeng_image_req_key:
            missing.append("JIMENG_IMAGE_REQ_KEY")
        if missing:
            raise RuntimeError("即梦图片生成配置缺失：" + "、".join(missing))

    def _wait_for_image_result(self, *, client: JimengImageClient, task_id: str) -> tuple[dict[str, str], dict[str, Any]]:
        deadline = time.monotonic() + self.settings.jimeng_poll_timeout_seconds
        last_response: dict[str, Any] = {}
        while time.monotonic() < deadline:
            result = client.get_image_result(task_id=task_id)
            last_response = result.raw
            if result.status == "done":
                if result.image_urls:
                    return {"kind": "url", "value": result.image_urls[0]}, result.raw
                if result.image_base64:
                    return {"kind": "base64", "value": result.image_base64[0]}, result.raw
                raise RuntimeError(f"即梦图片任务已完成但没有返回图片 URL 或 base64：{task_id}")
            if result.status in {"not_found", "expired"}:
                raise RuntimeError(f"即梦图片任务状态异常：{result.status}，task_id={task_id}")
            if result.status not in {"in_queue", "generating"}:
                raise RuntimeError(f"即梦图片任务返回未知状态：{result.status}，task_id={task_id}")
            time.sleep(self.settings.jimeng_poll_interval_seconds)
        raise RuntimeError(f"即梦图片任务等待超时：task_id={task_id}, last_response={last_response}")

    def _download_file(self, *, url: str, path: Path) -> None:
        try:
            with urllib.request.urlopen(url, timeout=180) as response:
                content = response.read()
        except Exception as exc:
            raise RuntimeError(f"下载即梦图片失败：{exc}") from exc
        if not content:
            raise RuntimeError("下载即梦图片失败：返回空文件。")
        path.write_bytes(content)

    def _save_image_payload(self, *, payload: dict[str, str], path: Path) -> None:
        if payload["kind"] == "url":
            self._download_file(url=payload["value"], path=path)
            return
        if payload["kind"] == "base64":
            path.write_bytes(base64.b64decode(payload["value"]))
            return
        raise RuntimeError(f"不支持的图片返回类型：{payload['kind']}")

    def _provider_debug_path(self, asset_path: Path) -> Path:
        return asset_path.with_name(f"{asset_path.name}.provider.json")

    def _write_provider_debug_sidecar(self, *, path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json_dumps(payload), encoding="utf-8")

    def _compact_asset_meta(self, meta: dict[str, Any]) -> dict[str, Any]:
        drop_keys = {"submit_response", "result_response", "submit_summary", "result_summary", "provider_debug_uri"}
        return {key: value for key, value in meta.items() if key not in drop_keys}

    def _summarize_jimeng_image_response(self, response: dict[str, Any]) -> dict[str, Any]:
        data = response.get("data") if isinstance(response.get("data"), dict) else {}
        return {
            "code": response.get("code"),
            "message": response.get("message") or response.get("msg") or "",
            "status": data.get("status") or "",
            "task_id": data.get("task_id") or "",
            "image_url_count": len(JimengImageClient._extract_image_urls(data)),
            "has_image_base64": bool(JimengImageClient._extract_image_base64(data)),
        }

    def _sanitize_provider_payload(self, value: Any) -> Any:
        if isinstance(value, dict):
            cleaned: dict[str, Any] = {}
            for key, item in value.items():
                if key == "binary_data_base64":
                    if isinstance(item, list):
                        cleaned[key] = {"omitted": True, "items": len(item)}
                    elif isinstance(item, str):
                        cleaned[key] = {"omitted": True, "chars": len(item)}
                    else:
                        cleaned[key] = {"omitted": True}
                    continue
                cleaned[key] = self._sanitize_provider_payload(item)
            return cleaned
        if isinstance(value, list):
            if len(value) > 20:
                preview = [self._sanitize_provider_payload(item) for item in value[:20]]
                preview.append(f"... ({len(value) - 20} more items)")
                return preview
            return [self._sanitize_provider_payload(item) for item in value]
        if isinstance(value, str) and len(value) > 1200:
            return value[:1200] + f"... [truncated {len(value) - 1200} chars]"
        return value

    def _visual_output_dir(self, *, project: Project, chapter_no: int | None, character: CharacterCard) -> Path:
        path_helper = VideoRenderService(self.settings)
        project_dir = f"{project.id:04d}-{path_helper._path_slug(project.title)}"
        chapter_dir = f"chapter-{chapter_no:03d}" if chapter_no is not None else "characters"
        character_dir = f"{character.id:04d}-{path_helper._path_slug(character.name)}"
        return self.settings.output_dir / "projects" / project_dir / "chapters" / chapter_dir / "visual_assets" / "characters" / character_dir

    def _shot_visual_output_dir(self, *, project: Project, storyboard: Storyboard, shot: StoryboardShot) -> Path:
        path_helper = VideoRenderService(self.settings)
        project_dir = f"{project.id:04d}-{path_helper._path_slug(project.title)}"
        storyboard_dir = f"{storyboard.id:04d}-{path_helper._path_slug(storyboard.title)}"
        return self.settings.output_dir / "projects" / project_dir / "storyboards" / storyboard_dir / "shots" / f"shot-{shot.shot_no:03d}" / "first_frame"

    def _build_turnaround_prompt(self, *, project: Project, character: CharacterCard, prompt_note: str) -> str:
        differentiation = self._character_differentiation_anchor(character)
        details = [
            f"角色名：{character.name}",
            f"年龄：{character.age}",
            f"性别：{character.gender}",
            f"角色定位：{character.story_role}",
            f"性格：{character.personality}",
            f"背景：{character.background}",
            f"角色差异锚点：{differentiation}",
            "请把角色定位、性格和背景转化为可见外观，而不是只画普通美型人物。",
        ]
        return build_character_visual_prompt(project=project, character_details=details, prompt_note=prompt_note)

    def _character_differentiation_anchor(self, character: CharacterCard) -> str:
        seed = f"{character.id}:{character.name}:{character.story_role}:{character.personality}:{character.background}"
        digest = hashlib.sha256(seed.encode("utf-8")).digest()
        palettes = [
            "天青、白、少量暖橙点缀",
            "靛蓝、灰白、银色细节",
            "墨绿、米白、深棕皮革细节",
            "酒红、黑、冷灰金属细节",
            "浅紫、雾粉、珍珠白细节",
            "暖黄、藏青、浅棕布料细节",
        ]
        silhouettes = [
            "修长利落，窄肩长外套",
            "轻盈少年感，短外套和清晰腰线",
            "沉稳成熟，长衣摆和层叠内搭",
            "行动派轮廓，短靴、束口袖和功能性配件",
            "温柔文艺轮廓，柔软针织或衬衫层次",
            "冷静疏离轮廓，直线剪裁和低饱和配色",
        ]
        motifs = [
            "透明伞、雨滴或晴雨交界的细节",
            "旧书、笔记本或书签",
            "星空、列车票或远行符号",
            "耳机、相机或小型机械物件",
            "发夹、丝带或细小首饰",
            "校服改造、徽章或围巾",
        ]
        return "；".join(
            [
                f"专属配色：{palettes[digest[0] % len(palettes)]}",
                f"轮廓语言：{silhouettes[digest[1] % len(silhouettes)]}",
                f"标志物：{motifs[digest[2] % len(motifs)]}",
            ]
        )
