from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .api_support import (
    _canonical_project_evolution,
    _character_card_or_404,
    _character_state_out,
    _ensure_default_folder,
    _folder_out,
    _project_chapter_or_404,
    _project_or_404,
    _relationship_state_out,
    _soft_delete_dirty_evolution_for_project,
    _story_event_out,
    _trash_items_for_user,
    _world_perception_out,
)
from .auth import get_current_user
from .contracts import (
    CharacterCardCreateRequest,
    ContextPackBuildRequest,
    ContextPackConfirmResponse,
    ContextPackDecisionRequest,
    ContextPackTodoUpdateRequest,
    ContextPackOut,
    CharacterCardOut,
    CharacterCardUpdateRequest,
    DeleteCharacterCardRequest,
    DeleteProjectRequest,
    GenerationOut,
    MemoryCreateRequest,
    MemoryOut,
    MoveProjectFolderRequest,
    MyWorkspaceOut,
    ProjectChapterCreateRequest,
    ProjectChapterOut,
    ProjectChapterUpdateRequest,
    ProjectBriefingSuggestionRequest,
    ProjectBriefingSuggestionResponse,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectFolderCreateRequest,
    ProjectFolderOut,
    ProjectOut,
    ProjectUpdateRequest,
    ReferenceAssetWorkflowStateOut,
    ReferenceImageAssetOut,
    ReferenceImageAssetUpdateRequest,
    ReferenceImageDiscoverRequest,
    ReferenceWorkResolveRequest,
    ReferenceWorkResolvedOut,
    RestoreTrashItemRequest,
    StoryBoundaryParseRequest,
    StoryBoundaryParseResponse,
    StoryBoundaryRuleOut,
    StoryBoundaryUpdateRequest,
    SourceCreateRequest,
    SourceOut,
)
from .db import get_db
from .config import load_settings
from .context_pack_service import ContextPackService
from .json_utils import json_loads_object
from .models import (
    CharacterCard,
    CharacterStateUpdate,
    ContextPack,
    GenerationRun,
    Memory,
    Novel,
    Project,
    ProjectChapter,
    ProjectFolder,
    RelationshipStateUpdate,
    SourceDocument,
    StoryEvent,
    User,
    WorldPerceptionUpdate,
)
from .project_briefing_service import ProjectBriefingService
from .reference_asset_service import ReferenceAssetService
from .reference_policy_service import ReferencePolicyService
from .story_boundary_service import StoryBoundaryService


def _apply_reference_work_payload(project: Project, payload: ProjectCreateRequest | ProjectUpdateRequest) -> None:
    project.reference_work = payload.reference_work.strip()
    project.reference_work_creator = payload.reference_work_creator.strip()
    project.reference_work_medium = payload.reference_work_medium.strip()
    project.reference_work_synopsis = payload.reference_work_synopsis.strip()
    project.reference_work_style_traits = payload.reference_work_style_traits
    project.reference_work_world_traits = payload.reference_work_world_traits
    project.reference_work_narrative_constraints = payload.reference_work_narrative_constraints
    project.reference_work_confidence_note = payload.reference_work_confidence_note.strip()
    project.reference_inheritance_mode = payload.reference_inheritance_mode
    project.reference_rewrite_start = payload.reference_rewrite_start.strip()
    project.reference_authorized_changes = payload.reference_authorized_changes.strip()
    project.story_boundary_text = payload.story_boundary_text.strip()


def _apply_visual_style_payload(project: Project, payload: ProjectCreateRequest | ProjectUpdateRequest) -> None:
    project.visual_style_locked = bool(payload.visual_style_locked)
    project.visual_style_medium = payload.visual_style_medium.strip()
    project.visual_style_artists = payload.visual_style_artists
    project.visual_style_positive = payload.visual_style_positive
    project.visual_style_negative = payload.visual_style_negative
    project.visual_style_notes = payload.visual_style_notes.strip()


def register_project_routes(router: APIRouter) -> None:
    context_pack_service = ContextPackService()
    story_boundary_service = StoryBoundaryService()
    reference_asset_service = ReferenceAssetService()
    reference_policy_service = ReferencePolicyService()

    @router.get("/api/projects", response_model=list[ProjectOut])
    def list_projects(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> list[ProjectOut]:
        _ensure_default_folder(db, current_user)
        db.commit()
        projects = db.scalars(
            select(Project)
            .where(Project.owner_id == current_user.id, Project.deleted_at.is_(None))
            .order_by(Project.updated_at.desc())
        ).all()
        return [ProjectOut.model_validate(item) for item in projects]

    @router.get("/api/me/workspace", response_model=MyWorkspaceOut)
    def my_workspace(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> MyWorkspaceOut:
        default_folder = _ensure_default_folder(db, current_user)
        projects = db.scalars(
            select(Project)
            .where(Project.owner_id == current_user.id, Project.deleted_at.is_(None))
            .order_by(Project.updated_at.desc())
        ).all()
        folders = db.scalars(
            select(ProjectFolder)
            .where(ProjectFolder.user_id == current_user.id)
            .order_by(ProjectFolder.sort_order.asc(), ProjectFolder.created_at.asc())
        ).all()
        for project in projects:
            if project.folder_id is None:
                project.folder = default_folder
        db.commit()
        return MyWorkspaceOut(
            folders=[_folder_out(item) for item in folders],
            projects=[ProjectOut.model_validate(item) for item in projects],
            trash=_trash_items_for_user(db, current_user.id),
        )

    @router.post("/api/me/folders", response_model=ProjectFolderOut)
    def create_project_folder(
        payload: ProjectFolderCreateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ProjectFolderOut:
        _ensure_default_folder(db, current_user)
        name = payload.name.strip()
        exists = db.scalar(select(ProjectFolder).where(ProjectFolder.user_id == current_user.id, ProjectFolder.name == name))
        if exists is not None:
            raise HTTPException(status_code=409, detail="文件夹名称已存在。")
        max_order = db.scalar(
            select(ProjectFolder.sort_order)
            .where(ProjectFolder.user_id == current_user.id)
            .order_by(ProjectFolder.sort_order.desc())
            .limit(1)
        )
        folder = ProjectFolder(user=current_user, name=name, sort_order=(max_order or 0) + 1, is_default=False)
        db.add(folder)
        db.commit()
        db.refresh(folder)
        return _folder_out(folder)

    @router.post("/api/projects/briefing-suggestions", response_model=ProjectBriefingSuggestionResponse)
    def suggest_project_briefing(
        payload: ProjectBriefingSuggestionRequest,
        current_user: User = Depends(get_current_user),
    ) -> ProjectBriefingSuggestionResponse:
        _ = current_user
        settings = load_settings()
        service = ProjectBriefingService(settings=settings)
        suggestions = service.suggest(
            kind=payload.kind,
            title=payload.title,
            genre=payload.genre,
            reference_work=payload.reference_work,
            seed_text=payload.seed_text,
        )
        return ProjectBriefingSuggestionResponse(kind=payload.kind, suggestions=suggestions)

    @router.post("/api/projects/reference-work/resolve", response_model=ReferenceWorkResolvedOut)
    def resolve_reference_work(
        payload: ReferenceWorkResolveRequest,
        current_user: User = Depends(get_current_user),
    ) -> ReferenceWorkResolvedOut:
        _ = current_user
        settings = load_settings()
        service = ProjectBriefingService(settings=settings)
        result = service.resolve_reference_work(query=payload.query, genre=payload.genre)
        return ReferenceWorkResolvedOut(**result)

    @router.post("/api/projects/{project_id}/story-boundaries/parse", response_model=StoryBoundaryParseResponse)
    def parse_story_boundaries(
        project_id: int,
        payload: StoryBoundaryParseRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> StoryBoundaryParseResponse:
        _project_or_404(db, current_user.id, project_id)
        rules = story_boundary_service.parse_rules(payload.story_boundary_text)
        return StoryBoundaryParseResponse(
            story_boundary_text=payload.story_boundary_text.strip(),
            rules=[StoryBoundaryRuleOut(**item) for item in rules],
        )

    @router.put("/api/projects/{project_id}/story-boundaries", response_model=ProjectOut)
    def update_story_boundaries(
        project_id: int,
        payload: StoryBoundaryUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ProjectOut:
        project = _project_or_404(db, current_user.id, project_id)
        project.story_boundary_text = payload.story_boundary_text.strip()
        project.story_boundary_rules = [item.model_dump() for item in payload.rules]
        db.commit()
        db.refresh(project)
        return ProjectOut.model_validate(project)

    @router.post("/api/projects/{project_id}/reference-images/discover", response_model=list[ReferenceImageAssetOut])
    def discover_reference_images(
        project_id: int,
        payload: ReferenceImageDiscoverRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> list[ReferenceImageAssetOut]:
        project = _project_or_404(db, current_user.id, project_id)
        assets = reference_asset_service.discover_candidates(
            db,
            project=project,
            candidates=[item.model_dump() for item in payload.candidates],
        )
        db.commit()
        for asset in assets:
            db.refresh(asset)
        return [ReferenceImageAssetOut.model_validate(item) for item in assets]

    @router.get("/api/projects/{project_id}/reference-images", response_model=list[ReferenceImageAssetOut])
    def list_reference_images(
        project_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> list[ReferenceImageAssetOut]:
        project = _project_or_404(db, current_user.id, project_id)
        return [ReferenceImageAssetOut.model_validate(item) for item in reference_asset_service.list_assets(db, project=project)]

    @router.put("/api/projects/{project_id}/reference-images/{asset_id}", response_model=ReferenceImageAssetOut)
    def update_reference_image(
        project_id: int,
        asset_id: int,
        payload: ReferenceImageAssetUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ReferenceImageAssetOut:
        project = _project_or_404(db, current_user.id, project_id)
        try:
            asset = reference_asset_service.update_asset_status(
                db,
                project=project,
                asset_id=asset_id,
                status=payload.status,
                mapped_character_name=payload.mapped_character_name,
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="参考图候选不存在。") from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        db.commit()
        db.refresh(asset)
        return ReferenceImageAssetOut.model_validate(asset)

    @router.get("/api/projects/{project_id}/reference-images/workflow-state", response_model=ReferenceAssetWorkflowStateOut)
    def reference_image_workflow_state(
        project_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ReferenceAssetWorkflowStateOut:
        project = _project_or_404(db, current_user.id, project_id)
        return ReferenceAssetWorkflowStateOut(**reference_asset_service.workflow_state(db, project))

    @router.post("/api/projects", response_model=ProjectOut)
    def create_project(
        payload: ProjectCreateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ProjectOut:
        default_folder = _ensure_default_folder(db, current_user)
        project = Project(
            owner_id=current_user.id,
            folder=default_folder,
            title=payload.title,
            genre=payload.genre,
            world_brief=payload.world_brief,
            writing_rules=payload.writing_rules,
            style_profile=payload.style_profile,
        )
        _apply_reference_work_payload(project, payload)
        _apply_visual_style_payload(project, payload)
        db.add(project)
        db.flush()
        reference_policy_service.sync_project_reference_facts(db, project)
        db.commit()
        db.refresh(project)
        return ProjectOut.model_validate(project)

    @router.put("/api/projects/{project_id}/folder", response_model=ProjectOut)
    def move_project_to_folder(
        project_id: int,
        payload: MoveProjectFolderRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ProjectOut:
        project = _project_or_404(db, current_user.id, project_id)
        if payload.folder_id is None:
            folder = _ensure_default_folder(db, current_user)
        else:
            folder = db.scalar(
                select(ProjectFolder).where(ProjectFolder.user_id == current_user.id, ProjectFolder.id == payload.folder_id)
            )
            if folder is None:
                raise HTTPException(status_code=404, detail="文件夹不存在。")
        project.folder = folder
        db.commit()
        db.refresh(project)
        return ProjectOut.model_validate(project)

    @router.put("/api/projects/{project_id}", response_model=ProjectOut)
    def update_project(
        project_id: int,
        payload: ProjectUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ProjectOut:
        project = _project_or_404(db, current_user.id, project_id)
        project.title = payload.title.strip()
        project.genre = payload.genre.strip()
        _apply_reference_work_payload(project, payload)
        _apply_visual_style_payload(project, payload)
        project.world_brief = payload.world_brief.strip()
        project.writing_rules = payload.writing_rules.strip()
        project.style_profile = payload.style_profile
        reference_policy_service.sync_project_reference_facts(db, project)
        db.commit()
        db.refresh(project)
        return ProjectOut.model_validate(project)

    @router.post("/api/projects/{project_id}/chapters", response_model=ProjectChapterOut)
    def create_project_chapter(
        project_id: int,
        payload: ProjectChapterCreateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ProjectChapterOut:
        project = _project_or_404(db, current_user.id, project_id)
        chapter_no = payload.chapter_no or (max((item.chapter_no for item in project.project_chapters), default=0) + 1)
        if any(item.chapter_no == chapter_no for item in project.project_chapters):
            raise HTTPException(status_code=409, detail=f"第 {chapter_no} 章已经存在。")
        chapter = ProjectChapter(
            project=project,
            title=payload.title.strip(),
            premise=payload.premise.strip(),
            chapter_no=chapter_no,
        )
        db.add(chapter)
        db.commit()
        db.refresh(chapter)
        return ProjectChapterOut.model_validate(chapter)

    @router.put("/api/projects/{project_id}/chapters/{chapter_id}", response_model=ProjectChapterOut)
    def update_project_chapter(
        project_id: int,
        chapter_id: int,
        payload: ProjectChapterUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ProjectChapterOut:
        project = _project_or_404(db, current_user.id, project_id)
        chapter = _project_chapter_or_404(db, project.id, chapter_id)
        if any(item.id != chapter.id and item.chapter_no == payload.chapter_no for item in project.project_chapters):
            raise HTTPException(status_code=409, detail=f"第 {payload.chapter_no} 章已经存在。")
        chapter.title = payload.title.strip()
        chapter.premise = payload.premise.strip()
        chapter.chapter_no = payload.chapter_no
        db.commit()
        db.refresh(chapter)
        return ProjectChapterOut.model_validate(chapter)

    @router.delete("/api/projects/{project_id}", response_model=ProjectOut)
    def delete_project(
        project_id: int,
        payload: DeleteProjectRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ProjectOut:
        project = db.scalar(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id))
        if project is None:
            raise HTTPException(status_code=404, detail="项目不存在。")
        if payload.hard_delete:
            db.delete(project)
            db.commit()
            return ProjectOut.model_validate(project)
        project.deleted_at = datetime.utcnow()
        db.commit()
        db.refresh(project)
        return ProjectOut.model_validate(project)

    @router.post("/api/trash/{item_id}/restore")
    def restore_trash_item(
        item_id: int,
        payload: RestoreTrashItemRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> dict[str, object]:
        if payload.item_type == "project":
            item = db.scalar(select(Project).where(Project.id == item_id, Project.owner_id == current_user.id))
            if item is None:
                raise HTTPException(status_code=404, detail="项目不存在。")
            item.deleted_at = None
            if item.folder_id is None:
                item.folder = _ensure_default_folder(db, current_user)
        elif payload.item_type == "novel":
            item = db.scalar(select(Novel).where(Novel.id == item_id, Novel.owner_id == current_user.id))
            if item is None:
                raise HTTPException(status_code=404, detail="作品不存在。")
            item.deleted_at = None
        elif payload.item_type == "dirty_evolution":
            if item_id >= 3_000_000:
                item = db.scalar(
                    select(WorldPerceptionUpdate)
                    .join(Project, WorldPerceptionUpdate.project_id == Project.id)
                    .where(WorldPerceptionUpdate.id == item_id - 3_000_000, Project.owner_id == current_user.id)
                )
            elif item_id >= 2_000_000:
                item = db.scalar(
                    select(StoryEvent)
                    .join(Project, StoryEvent.project_id == Project.id)
                    .where(StoryEvent.id == item_id - 2_000_000, Project.owner_id == current_user.id)
                )
            elif item_id >= 1_000_000:
                item = db.scalar(
                    select(RelationshipStateUpdate)
                    .join(Project, RelationshipStateUpdate.project_id == Project.id)
                    .where(RelationshipStateUpdate.id == item_id - 1_000_000, Project.owner_id == current_user.id)
                )
            else:
                item = db.scalar(
                    select(CharacterStateUpdate)
                    .join(Project, CharacterStateUpdate.project_id == Project.id)
                    .where(CharacterStateUpdate.id == item_id, Project.owner_id == current_user.id)
                )
            if item is None:
                raise HTTPException(status_code=404, detail="脏演化记录不存在。")
            item.deleted_at = None
        else:
            item = db.scalar(
                select(CharacterCard)
                .join(Project, CharacterCard.project_id == Project.id)
                .where(CharacterCard.id == item_id, Project.owner_id == current_user.id)
            )
            if item is None:
                raise HTTPException(status_code=404, detail="人物卡不存在。")
            item.deleted_at = None
        db.commit()
        return {"status": "restored"}

    @router.get("/api/projects/{project_id}", response_model=ProjectDetailResponse)
    def project_detail(
        project_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ProjectDetailResponse:
        project = _project_or_404(db, current_user.id, project_id)
        context_pack = context_pack_service.latest_for_project(db, project.id)
        generations = db.scalars(
            select(GenerationRun).where(GenerationRun.project_id == project.id).order_by(GenerationRun.created_at.desc())
        ).all()
        character_updates, relationship_updates, story_events, world_updates = _canonical_project_evolution(db, project)
        return ProjectDetailResponse(
            project=ProjectOut.model_validate(project),
            project_chapters=[
                ProjectChapterOut.model_validate(item)
                for item in sorted(project.project_chapters, key=lambda chapter: chapter.chapter_no)
            ],
            memories=[MemoryOut.model_validate(item) for item in project.memories],
            character_cards=[
                CharacterCardOut.model_validate(item) for item in project.character_cards if item.deleted_at is None
            ],
            sources=[SourceOut.model_validate(item) for item in project.source_documents],
            generations=[GenerationOut.model_validate(item) for item in generations],
            character_state_updates=[_character_state_out(item) for item in character_updates[:20]],
            relationship_state_updates=[_relationship_state_out(item) for item in relationship_updates[:20]],
            story_events=[_story_event_out(item) for item in story_events[:20]],
            world_perception_updates=[_world_perception_out(item) for item in world_updates[:20]],
            context_pack=ContextPackOut(**context_pack_service.as_dict(context_pack)) if context_pack is not None else None,
        )

    @router.get("/api/projects/{project_id}/context-pack", response_model=ContextPackOut | None)
    def get_context_pack(
        project_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ContextPackOut | None:
        project = _project_or_404(db, current_user.id, project_id)
        context_pack = context_pack_service.latest_for_project(db, project.id)
        if context_pack is None:
            return None
        if context_pack_service.is_stale(context_pack, project) and context_pack.status == "confirmed":
            context_pack.status = "stale"
            db.commit()
            db.refresh(context_pack)
        return ContextPackOut(**context_pack_service.as_dict(context_pack))

    @router.post("/api/projects/{project_id}/context-pack/build", response_model=ContextPackOut)
    def build_context_pack(
        project_id: int,
        payload: ContextPackBuildRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ContextPackOut:
        project = _project_or_404(db, current_user.id, project_id)
        context_pack = context_pack_service.build(
            db,
            project=project,
            reference_mode=payload.reference_mode,
            user_notes=payload.user_notes,
            user_decisions=payload.user_decisions,
            confirm_after_build=payload.confirm_after_build,
        )
        db.commit()
        db.refresh(context_pack)
        return ContextPackOut(**context_pack_service.as_dict(context_pack))

    @router.post("/api/projects/{project_id}/context-pack/rebuild", response_model=ContextPackOut)
    def rebuild_context_pack(
        project_id: int,
        payload: ContextPackBuildRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ContextPackOut:
        project = _project_or_404(db, current_user.id, project_id)
        latest = context_pack_service.latest_for_project(db, project.id)
        if latest is None:
            context_pack = context_pack_service.build(
                db,
                project=project,
                reference_mode=payload.reference_mode,
                user_notes=payload.user_notes,
                user_decisions=payload.user_decisions,
                confirm_after_build=payload.confirm_after_build,
            )
        else:
            context_pack_service.update_user_decisions(latest, payload.user_decisions)
            context_pack = context_pack_service.rebuild(
                db,
                project=project,
                existing=latest,
                confirm_after_build=payload.confirm_after_build,
            )
        db.commit()
        db.refresh(context_pack)
        return ContextPackOut(**context_pack_service.as_dict(context_pack))

    @router.post("/api/projects/{project_id}/context-pack/confirm", response_model=ContextPackConfirmResponse)
    def confirm_context_pack(
        project_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ContextPackConfirmResponse:
        project = _project_or_404(db, current_user.id, project_id)
        context_pack = context_pack_service.latest_for_project(db, project.id)
        if context_pack is None:
            raise HTTPException(status_code=404, detail="当前项目还没有生成前校对稿。")
        if context_pack_service.is_stale(context_pack, project):
            context_pack.status = "stale"
            db.commit()
            raise HTTPException(status_code=409, detail="项目设定已变化，需要重新生成校对稿。")
        context_pack_service.confirm(context_pack)
        db.commit()
        db.refresh(context_pack)
        return ContextPackConfirmResponse(
            status="confirmed",
            context_pack=ContextPackOut(**context_pack_service.as_dict(context_pack)),
        )

    @router.put("/api/projects/{project_id}/context-pack/decisions", response_model=ContextPackOut)
    def update_context_pack_decisions(
        project_id: int,
        payload: ContextPackDecisionRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ContextPackOut:
        project = _project_or_404(db, current_user.id, project_id)
        context_pack = context_pack_service.latest_for_project(db, project.id)
        if context_pack is None:
            raise HTTPException(status_code=404, detail="当前项目还没有生成前校对稿。")
        context_pack_service.update_user_decisions(context_pack, payload.user_decisions)
        rebuilt = context_pack_service.build(
            db,
            project=project,
            reference_mode=context_pack.reference_mode,
            user_notes=context_pack.user_notes,
            user_decisions=json_loads_object(context_pack.user_decisions_json),
            confirm_after_build=context_pack.status == "confirmed",
        )
        db.commit()
        db.refresh(rebuilt)
        return ContextPackOut(**context_pack_service.as_dict(rebuilt))

    @router.put("/api/projects/{project_id}/context-pack/todos", response_model=ContextPackOut)
    def update_context_pack_todo(
        project_id: int,
        payload: ContextPackTodoUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ContextPackOut:
        project = _project_or_404(db, current_user.id, project_id)
        context_pack = context_pack_service.latest_for_project(db, project.id)
        if context_pack is None:
            raise HTTPException(status_code=404, detail="当前项目还没有生成前校对稿。")
        context_pack_service.update_user_decisions(context_pack, {f"task:{payload.task_id}": payload.status})
        rebuilt = context_pack_service.build(
            db,
            project=project,
            reference_mode=context_pack.reference_mode,
            user_notes=context_pack.user_notes,
            user_decisions=json_loads_object(context_pack.user_decisions_json),
            confirm_after_build=context_pack.status == "confirmed",
        )
        db.commit()
        db.refresh(rebuilt)
        return ContextPackOut(**context_pack_service.as_dict(rebuilt))

    @router.post("/api/projects/{project_id}/dirty-evolution/trash")
    def trash_dirty_evolution_for_project(
        project_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> dict[str, object]:
        project = _project_or_404(db, current_user.id, project_id)
        stats = _soft_delete_dirty_evolution_for_project(db, project)
        db.commit()
        return {"status": "trashed", "stats": stats}

    @router.post("/api/projects/{project_id}/memories", response_model=MemoryOut)
    def create_memory(
        project_id: int,
        payload: MemoryCreateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> MemoryOut:
        project = _project_or_404(db, current_user.id, project_id)
        memory = Memory(
            project=project,
            title=payload.title,
            content=payload.content,
            memory_scope=payload.memory_scope,
            importance=payload.importance,
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return MemoryOut.model_validate(memory)

    @router.post("/api/projects/{project_id}/character-cards", response_model=CharacterCardOut)
    def create_character_card(
        project_id: int,
        payload: CharacterCardCreateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> CharacterCardOut:
        project = _project_or_404(db, current_user.id, project_id)
        card = CharacterCard(
            project=project,
            name=payload.name.strip(),
            age=payload.age.strip(),
            gender=payload.gender.strip(),
            personality=payload.personality.strip(),
            story_role=payload.story_role.strip(),
            background=payload.background.strip(),
            voice_provider=payload.voice_provider.strip(),
            voice_speaker=payload.voice_speaker.strip(),
            voice_style=payload.voice_style.strip(),
            voice_speed=payload.voice_speed,
            voice_pitch=payload.voice_pitch,
        )
        db.add(card)
        db.commit()
        db.refresh(card)
        return CharacterCardOut.model_validate(card)

    @router.put("/api/projects/{project_id}/character-cards/{card_id}", response_model=CharacterCardOut)
    def update_character_card(
        project_id: int,
        card_id: int,
        payload: CharacterCardUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> CharacterCardOut:
        project = _project_or_404(db, current_user.id, project_id)
        card = _character_card_or_404(db, project.id, card_id)
        card.name = payload.name.strip()
        card.age = payload.age.strip()
        card.gender = payload.gender.strip()
        card.personality = payload.personality.strip()
        card.story_role = payload.story_role.strip()
        card.background = payload.background.strip()
        card.voice_provider = payload.voice_provider.strip()
        card.voice_speaker = payload.voice_speaker.strip()
        card.voice_style = payload.voice_style.strip()
        card.voice_speed = payload.voice_speed
        card.voice_pitch = payload.voice_pitch
        db.commit()
        db.refresh(card)
        return CharacterCardOut.model_validate(card)

    @router.delete("/api/projects/{project_id}/character-cards/{card_id}", response_model=CharacterCardOut)
    def delete_character_card(
        project_id: int,
        card_id: int,
        payload: DeleteCharacterCardRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> CharacterCardOut:
        project = _project_or_404(db, current_user.id, project_id)
        card = db.scalar(select(CharacterCard).where(CharacterCard.project_id == project.id, CharacterCard.id == card_id))
        if card is None:
            raise HTTPException(status_code=404, detail="人物卡不存在。")
        if payload.hard_delete:
            result = CharacterCardOut.model_validate(card)
            db.delete(card)
            db.commit()
            return result
        card.deleted_at = datetime.utcnow()
        db.commit()
        db.refresh(card)
        return CharacterCardOut.model_validate(card)

    @router.post("/api/projects/{project_id}/sources", response_model=SourceOut)
    def create_source(
        project_id: int,
        payload: SourceCreateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> SourceOut:
        project = _project_or_404(db, current_user.id, project_id)
        source = SourceDocument(
            project=project,
            title=payload.title,
            content=payload.content,
            source_kind=payload.source_kind,
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return SourceOut.model_validate(source)
