# Reference-Constrained Longform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把当前项目升级为“项目设定 + 原作继承 + 跨章节硬约束 + 参考资产驱动视觉生成”的三阶段工作流，并收敛前端主入口。

**Architecture:** 后端新增结构化约束与参考资产层，在概要生成、正文生成、视觉生成三条链路上增加约束分发和违规校验；前端收敛为 `设定 -> 小说 -> 视频` 三阶段，新增“故事边界”与“参考资产定稿”入口。

**Tech Stack:** FastAPI, SQLAlchemy, OpenAI Responses, Vue 3, Pinia, Playwright regression, Python tests

---

## Current Implementation Status

**已完成：**

- `故事边界` 结构化规则最小切片
- `参考作品继承策略` 最小切片
- `ReferenceFact` 派生、持久化和 `conflict` / `authorized_override` 标注
- 长篇概要阶段的故事边界违规拦截
- 长篇概要输出的章节级 `constraint_snapshot`
- 正文生成后的故事边界违规检查与自动修正
- 参考图候选发现、去重、存储、列表、审批/拒绝和工作流状态 API
- `CharacterReferenceProfile` 正式模型、启动迁移/回填、项目详情 API 和前端状态源
- 项目设定页的最小 UI 接线
- Python 单测、`compileall`、前端 `build`

**部分完成：**

- Context Pack 现在会携带故事边界、参考继承策略、ReferenceFact 快照和授权改写标记
- 小说生成 prompt 已显式注入故事边界和参考继承策略
- 参考资产链路已有后端候选/审批 API，但前端视频阶段审核 UI 尚未接入
- 角色三视图已有单张生成能力；已补充 `character_turnaround` 锁定语义、同角色互斥锁定、`CharacterReferenceProfile` 状态同步、镜头首帧对锁定三视图的 metadata 继承记录
- 前端已新增 `设定 / 小说 / 视频` 三阶段壳层入口，旧功能降为阶段内或次级入口

**架构偏移收口状态：**

- `CharacterReferenceProfile` 已落表，并作为角色视觉母版状态的项目级事实来源。
- `MediaAsset.meta.locked` 仍保留为兼容和素材卡片显示字段，但锁定三视图解析、项目详情和视频阶段三视图状态优先读取 `CharacterReferenceProfile`。
- 下一轮可以继续 Task 11 的参考资产审核 UI、Task 7 的多候选/视频强继承、以及 LightRAG 设计。

**仍未闭合：**

- 三视图真正的多候选批量生成
- 视频链视频模型提交阶段对锁定角色视觉资产的强继承
- 视频阶段参考资产审核完整 UI
- 小说阶段基于结构化 `ViolationCheck` 的完整违规横幅与成功状态拦截
- 三阶段路由恢复、视频预检和关键约束 UI 的人工/Playwright 回归
- Playwright 回归补齐

**新对话建议从这里继续：**

1. Task 11：基于 `CharacterReferenceProfile` 补完 `ReferenceAssetReviewPanel.vue`，把参考图审批和角色映射接入视频阶段
2. Task 7：继续把锁定三视图传递到视频模型提交链路，而不仅是首帧生成链路
3. Task 12：补 Playwright 三阶段导航、故事边界确认、小说硬约束可视化回归

**下一轮验收口径：**

- Task 11 通过条件：视频阶段能查看参考图候选、批准/拒绝候选、把批准图映射到角色，并让 `CharacterReferenceProfile.visual_reference_asset_ids` / `status` 反映审核结果。
- Task 7 通过条件：多候选三视图可生成并锁定；视频模型提交链路读取 `CharacterReferenceProfile.locked_turnaround_asset_id`，而不是只在首帧 metadata 中记录。
- Task 10 通过条件：小说阶段展示结构化 `ViolationCheck`，违规草稿不能被呈现为普通成功状态。
- Task 12 通过条件：`python -m unittest`、`npm run test:regression`、`npm run build` 都有新鲜通过记录。

---

## Immediate Architecture Correction

### Decision: `CharacterReferenceProfile` enters the near-term MVP

Use a lightweight first-class model as the single source of truth for project-character visual status. Keep `MediaAsset.meta.locked` as a denormalized compatibility marker, but do not rely on scanning `MediaAsset` as the only way to answer whether a character is ready for video production.

**Minimal model fields:**

- `id`
- `project_id`
- `character_card_id`
- `reference_character_name`
- `visual_reference_asset_ids_json`
- `locked_turnaround_asset_id`
- `status`: `unmapped` / `mapped` / `reference_assets_ready` / `turnaround_candidate_ready` / `turnaround_locked`
- `notes`
- `created_at`
- `updated_at`

**Ownership boundaries:**

- `CharacterCard`: literary/story character definition.
- `ReferenceImageAsset`: external reference image candidate or approved source.
- `MediaAsset`: generated or uploaded media file.
- `CharacterReferenceProfile`: current visual identity state for one project character.

**Temporary compatibility rule:**

- Existing locked `character_turnaround` media assets remain valid.
- Migration/backfill must create one `CharacterReferenceProfile` per active `CharacterCard`.
- If a completed `character_turnaround` has `meta.locked == true`, backfill `locked_turnaround_asset_id` and `status = "turnaround_locked"` for the matching profile.
- If no locked turnaround exists but completed turnaround candidates exist, set `status = "turnaround_candidate_ready"`.
- If approved `ReferenceImageAsset` rows map to the character name, set `status = "reference_assets_ready"` unless a stronger status applies.

**Downstream rule:**

- Video preflight and shot first-frame generation must consult `CharacterReferenceProfile` first.
- `MediaAsset.meta.locked_turnaround_asset_ids` should record what was used for traceability, but it is not the source of truth.

---

### Task 7A: Add `CharacterReferenceProfile` as the visual identity state source

**Files:**

- Modify: `app/models.py`
- Modify: `app/db.py`
- Modify: `app/contracts.py`
- Modify: `app/api_routes_projects.py`
- Modify: `app/api_routes_longform.py`
- Modify: `app/visual_asset_service.py`
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/stores/workbench.ts`
- Modify: `frontend/src/components/workspace/LongformPipelinePanel.vue`
- Test: `tests/test_character_reference_profile.py`

- [x] **Step 1: Write failing backend tests for profile backfill and lock state**

Create `tests/test_character_reference_profile.py` with tests for:

```python
def test_backfills_profile_from_locked_turnaround_asset():
    # Given a character and a completed character_turnaround MediaAsset with meta.locked true
    # When profile backfill runs
    # Then a profile exists with locked_turnaround_asset_id and status turnaround_locked
```

```python
def test_locking_turnaround_updates_profile_and_unlocks_siblings():
    # Given two completed turnaround assets for the same character
    # When the second is locked
    # Then the profile points to the second asset, the first asset meta.locked is false,
    # and profile.status is turnaround_locked
```

Run:

```bash
python -m unittest tests.test_character_reference_profile
```

Expected: fail because `CharacterReferenceProfile` and profile service do not exist yet.

Implemented in `tests/test_character_reference_profile.py`; red run failed on missing `CharacterReferenceProfile`, then passed after implementation.

- [x] **Step 2: Add the SQLAlchemy model**

Add `CharacterReferenceProfile` in `app/models.py`:

```python
class CharacterReferenceProfile(Base, TimestampMixin):
    __tablename__ = "character_reference_profiles"
    __table_args__ = (UniqueConstraint("project_id", "character_card_id", name="uq_character_reference_profiles_project_character"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    character_card_id: Mapped[int] = mapped_column(ForeignKey("character_cards.id"), nullable=False)
    reference_character_name: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    visual_reference_asset_ids_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    locked_turnaround_asset_id: Mapped[int | None] = mapped_column(ForeignKey("media_assets.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="unmapped", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    project: Mapped["Project"] = relationship(back_populates="character_reference_profiles")
    character_card: Mapped["CharacterCard"] = relationship()
    locked_turnaround_asset: Mapped["MediaAsset | None"] = relationship(foreign_keys=[locked_turnaround_asset_id])
```

Add to `Project`:

```python
character_reference_profiles: Mapped[list["CharacterReferenceProfile"]] = relationship(
    back_populates="project",
    cascade="all, delete-orphan",
)
```

Implemented in `app/models.py` with `Project.character_reference_profiles` relationship and JSON-backed `visual_reference_asset_ids`.

- [x] **Step 3: Add migration/bootstrap support**

Update `app/db.py` so normal startup creates the table and existing deployments get the new columns/table.

Backfill rules:

```python
for each active CharacterCard:
    create profile if missing
    if locked completed character_turnaround exists:
        locked_turnaround_asset_id = asset.id
        status = "turnaround_locked"
    elif completed character_turnaround exists:
        status = "turnaround_candidate_ready"
    elif approved ReferenceImageAsset mapped to character name exists:
        status = "reference_assets_ready"
    else:
        status = "unmapped"
```

Implemented `20260520_0017_character_reference_profile_schema` and startup backfill in `app/db.py`.

- [x] **Step 4: Add service helpers in `app/visual_asset_service.py` or a focused profile service**

Prefer a focused service if the implementation grows beyond 80-120 lines:

```python
class CharacterReferenceProfileService:
    def ensure_profiles(db: Session, project: Project) -> list[CharacterReferenceProfile]: ...
    def apply_turnaround_lock(db: Session, project: Project, asset: MediaAsset, locked: bool) -> CharacterReferenceProfile | None: ...
    def locked_turnaround_for_shot(db: Session, project: Project, shot: StoryboardShot) -> list[dict[str, Any]]: ...
```

`VisualAssetService.apply_turnaround_lock()` should delegate to this service instead of owning profile state itself.

Implemented `CharacterReferenceProfileService` in `app/visual_asset_service.py`; `VisualAssetService.apply_turnaround_lock()` delegates profile state updates and `locked_turnaround_references()` resolves through profiles first.

- [x] **Step 5: Expose profiles in API contracts**

Add `CharacterReferenceProfileOut` in `app/contracts.py`:

```python
class CharacterReferenceProfileOut(BaseModel):
    id: int
    project_id: int
    character_card_id: int
    reference_character_name: str
    visual_reference_asset_ids: list[int] = []
    locked_turnaround_asset_id: int | None = None
    status: str
    notes: str
    created_at: datetime
    updated_at: datetime
```

Add the list to the project detail response or longform/video state response, whichever is already used by the video stage. Prefer project detail if the status belongs to project setup, and mirror in longform state only if needed for polling.

Implemented `CharacterReferenceProfileOut` and `ProjectDetailResponse.character_reference_profiles`; project detail ensures/backfills profiles before returning.

- [x] **Step 6: Update frontend types and store**

Add `CharacterReferenceProfile` to `frontend/src/types.ts` and expose it through `ProjectDetailResponse` or `LongformState`.

Update video-stage computed state to use profiles first:

```ts
const characterTurnaroundState = computed(() =>
  props.characterCards.map((card) => {
    const profile = props.characterReferenceProfiles.find((item) => item.character_card_id === card.id);
    return {
      character: card,
      profile,
      status: profile?.status ?? "unmapped",
      lockedAssetId: profile?.locked_turnaround_asset_id ?? null,
    };
  }),
);
```

Implemented `CharacterReferenceProfile` frontend type, project detail field, video-stage prop threading, profile-first `characterTurnaroundState`, and silent project refresh after turnaround generation/locking.

- [x] **Step 7: Re-run targeted tests**

Run:

```bash
python -m unittest tests.test_character_reference_profile tests.test_visual_asset_locked_references
```

Expected: both pass.

Verified with `python -m unittest tests.test_character_reference_profile tests.test_visual_asset_locked_references tests.test_reference_asset_api`.

- [x] **Step 8: Re-run frontend build**

Run:

```bash
npm run build
```

from `frontend/`.

Expected: Vue template check, `vue-tsc`, and Vite build pass.

- [x] **Step 9: Update this plan after implementation**

After Task 7A is complete, update:

- Current Implementation Status
- Task 1 status for `CharacterReferenceProfile`
- Task 7 status for lock semantics
- Task 11 status for per-character turnaround state

Do not mark downstream video inheritance complete until video task generation itself uses `CharacterReferenceProfile.locked_turnaround_asset_id`.

Task 7A is complete. Downstream video task generation inheritance remains open under Task 7.

---

## File Structure

### Backend new files

- Create: `app/story_boundary_service.py`
- Create: `app/reference_policy_service.py`
- Create: `app/reference_asset_service.py`
- Create: `app/violation_check_service.py`
- Create: `tests/test_story_boundary_service.py`
- Create: `tests/test_reference_policy_service.py`
- Create: `tests/test_violation_check_service.py`

### Backend modified files

- Modify: `app/models.py`
- Modify: `app/contracts.py`
- Modify: `app/schema.py`
- Modify: `app/db.py`
- Modify: `app/api_routes_projects.py`
- Modify: `app/api_routes_longform.py`
- Modify: `app/context_pack_service.py`
- Modify: `app/series_planning_service.py`
- Modify: `app/outline_revision_service.py`
- Modify: `app/story_service.py`
- Modify: `app/batch_generation_service.py`
- Modify: `app/visual_asset_service.py`
- Modify: `app/jimeng_image_client.py`

### Frontend modified files

- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/stores/workbench.ts`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/components/workspace/ProjectSettingsPanel.vue`
- Modify: `frontend/src/components/workspace/ContextReviewPage.vue`
- Modify: `frontend/src/components/workspace/NovelCreatePage.vue`
- Modify: `frontend/src/components/workspace/VideoCreatePage.vue`
- Modify: `frontend/src/components/workspace/GenerationTracePanel.vue`
- Modify: `frontend/src/style.css`
- Modify: `frontend/src/styles/workspace.css`

### Frontend likely new files

- Create: `frontend/src/components/workspace/StoryBoundaryPanel.vue`
- Create: `frontend/src/components/workspace/SetupStagePage.vue`
- Create: `frontend/src/components/workspace/NovelStagePage.vue`
- Create: `frontend/src/components/workspace/VideoStagePage.vue`
- Create: `frontend/src/components/workspace/ReferenceAssetReviewPanel.vue`
- Create: `frontend/src/components/workspace/ConstraintViolationBanner.vue`

---

### Task 1: Extend the data model for structured constraints and reference assets

**Files:**

- Modify: `app/models.py`
- Modify: `app/contracts.py`
- Modify: `app/schema.py`
- Modify: `app/db.py`

- [x] **Step 1: Define minimal project-level storage for story-boundary rules and reference policy**

Add models for:

- `ConstraintRule`
- `ReferenceFact`
- `ReferenceImageAsset`
- `CharacterReferenceProfile`
- `ViolationCheck`

Each model must include timestamps and project ownership fields where applicable.

- [x] **Step 2: Expose API contracts for current story-boundary and reference-policy fields**

Add matching request and response contracts in `app/contracts.py` for:

- creating parsed story-boundary rules
- confirming or editing rules
- listing reference image candidates
- approving/rejecting reference images
- listing violation checks

- [x] **Step 3: Wire database initialization**

Update `app/db.py` and any schema bootstrap path so the new tables are created with the current metadata.

- [x] **Step 4: Add model/service smoke tests**

Create `tests/test_constraint_service.py` with a minimal test that imports the new models and creates an in-memory rule payload.

```python
def test_constraint_rule_payload_smoke():
    payload = {
        "source": "project",
        "scope_type": "chapter_range",
        "start_chapter_no": 1,
        "end_chapter_no": 10,
        "rule_type": "forbid_event",
    }
    assert payload["rule_type"] == "forbid_event"
```

- [x] **Step 5: Verify the model layer**

Run: `python -m unittest`

Expected: the new model and test imports complete without syntax errors.

---

### Task 2: Add a constraint service that turns natural language into hard rules

**Files:**

- Create: `app/constraint_service.py`
- Modify: `app/context_pack_service.py`
- Modify: `app/api_routes_projects.py`
- Test: `tests/test_constraint_service.py`

- [x] **Step 1: Implement parsing and normalization helpers**

`app/constraint_service.py` should:

- accept raw user story-boundary text
- ask the utility model for structured candidate rules
- normalize chapter ranges, subjects, event predicates, and priorities
- reject incomplete rules that do not specify scope or action

- [x] **Step 2: Persist rules as parsed then confirmed project state**

Add API endpoints that:

- submit natural language story boundaries
- return parsed candidate rules
- allow confirm/edit/delete actions

- [x] **Step 3: Make context-pack hard constraints rule-aware**

Update `app/context_pack_service.py` so `hard_constraints` are no longer only generic strings; include active `ConstraintRule` summaries and chapter-range rules in `resolved_inputs`.

- [x] **Step 4: Add tests for chapter-range parsing**

Add tests covering input like:

```python
raw_text = "第1到10章男女主不要相遇，第11章才第一次正式见面。"
```

Expected normalized outputs:

- forbid meeting for chapters 1-10
- allow first meeting at chapter 11

- [x] **Step 5: Verify parsing behavior**

Run: `python -m unittest`

Expected: the parser tests pass for chapter-range hard rules.

---

### Task 3: Add reference-work inheritance facts and authorized-override support

**Files:**

- Modify: `app/api_routes_projects.py`
- Modify: `app/context_pack_service.py`
- Modify: `app/contracts.py`
- Modify: `app/models.py`

- [x] **Step 1: Add project-level reference inheritance fields**

Extend the project/reference workflow so it can store:

- reference inheritance mode
- rewrite start point
- authorized override notes

- [x] **Step 2: Persist derived reference facts**

When a reference work is confirmed, store extracted `ReferenceFact` records for:

- character identity
- relationship baseline
- world rules
- plot facts before rewrite start

- [x] **Step 3: Add conflict semantics**

When a project hard rule conflicts with a reference fact, mark it as:

- `authorized_override` if explicitly allowed
- `conflict` otherwise

- [x] **Step 4: Verify context-pack output for the current policy slice**

Run a local request path or unit test that confirms `resolved_inputs()` includes:

- active project rules
- active reference facts
- authorized override markers

---

### Task 4: Make longform planning inherit series-level hard constraints

**Files:**

- Modify: `app/series_planning_service.py`
- Modify: `app/outline_revision_service.py`
- Modify: `app/api_routes_longform.py`

- [x] **Step 1: Feed structured rules into series planning**

Replace the current “user brief only” planning posture by explicitly injecting:

- active `ConstraintRule` summaries
- active `ReferenceFact` summaries
- authorized overrides

- [x] **Step 2: Require chapter-level constraint snapshots in output**

Each generated chapter outline must include an explicit section in the JSON payload describing:

- inherited hard constraints
- inherited reference facts
- forbidden events for that chapter

- [x] **Step 3: Preserve rules during outline revision**

Update `app/outline_revision_service.py` so user feedback cannot silently drop inherited rules when revising plans.

- [x] **Step 4: Add planning validation**

If an outline says the leads meet in chapter 4 while a chapters 1-10 rule forbids that, reject the plan as invalid.

- [x] **Step 5: Verify planning path**

Run a targeted manual or automated test that generates a 12-chapter plan with:

- rule: chapters 1-10 no direct meeting

Expected: no chapter 1-10 outline includes the meeting event.

---

### Task 5: Add violation checks for outline and draft generation

**Files:**

- Create: `app/violation_check_service.py`
- Modify: `app/story_service.py`
- Modify: `app/batch_generation_service.py`
- Test: `tests/test_violation_check_service.py`

- [x] **Step 1: Implement rule-based violation checks**

`app/violation_check_service.py` should inspect:

- chapter outline JSON
- generated draft content
- active chapter constraints

and return explicit violations.

- [x] **Step 2: Add outline-time rejection**

Hook the service into plan generation and outline revision before persisting a new outline set.

- [x] **Step 3: Add draft-time rejection and retry**

Update `app/story_service.py` and `app/batch_generation_service.py` so generation does both:

- coverage checks
- violation checks

If a hard constraint is violated, the system must not mark the generation successful.

- [x] **Step 4: Add tests for forbidden-meeting detection**

Test fixture:

```python
content = "放学后，男女主在便利店门口正式见面。"
```

Expected: the violation checker flags `direct_meeting` when active rule forbids it for this chapter.

- [x] **Step 5: Verify failure path**

Run: `python -m unittest`

Expected: violating content is flagged and non-violating content passes.

---

### Task 6: Add reference-image discovery and approval flow

**Files:**

- Create: `app/reference_asset_service.py`
- Modify: `app/api_routes_projects.py`
- Modify: `app/contracts.py`

- [x] **Step 1: Add reference-image discovery service**

Implement a service that:

- searches public reference images for a confirmed reference work
- stores them as `ReferenceImageAsset`
- labels them as candidate assets

- [x] **Step 2: Add approval APIs**

Expose endpoints to:

- list discovered assets
- approve assets
- reject assets
- map assets to characters where needed

- [x] **Step 3: Make approval state visible to the project workflow**

The setup stage must know whether a project has:

- no candidates
- candidates pending review
- enough approved assets to proceed

- [x] **Step 4: Verify the discovery path**

Run a manual API check using a known work like 《天气之子》 and confirm the system stores candidate reference assets instead of only textual traits.

---

### Task 7: Rework visual generation to use locked character references

**Files:**

- Modify: `app/visual_asset_service.py`
- Modify: `app/jimeng_image_client.py`
- Modify: `app/api_routes_longform.py`

- [x] **Step 1: Extend the image client for reference-driven generation**

If the provider supports image-conditioned generation, add a method for passing approved reference image URLs or provider-uploaded asset handles alongside prompt text.

- [ ] **Step 2: Generate multiple turnaround candidates**

Replace “single turnaround output” with “multiple candidates for review”.

- [x] **Step 3: Add turnaround lock semantics**

Once a user approves a turnaround asset, mark the associated `CharacterReferenceProfile` as `turnaround_locked`.

Implemented via `CharacterReferenceProfile.locked_turnaround_asset_id` as the source of truth, with `MediaAsset.meta.locked` / `turnaround_status` retained as compatibility metadata. Locking one `character_turnaround` unlocks sibling turnaround assets for the same character.

- [ ] **Step 4: Enforce downstream inheritance**

When generating:

- shot first frames
- storyboard visuals
- later video inputs

use the locked character turnaround asset as a required reference, not optional prompt flavor.

Partially implemented for shot first-frame generation: locked turnaround references are resolved from `StoryboardShot.character_refs`, included in the image prompt, passed to the image client as `reference_images`, and recorded in first-frame `MediaAsset.meta.locked_turnaround_asset_ids`.

- [x] **Step 5: Verify the locked-reference path**

Run a manual generation path where:

- one character turnaround is locked
- a subsequent shot first frame is generated

Expected: the downstream generation records the locked asset ID in metadata.

Verified by `tests/test_visual_asset_locked_references.py`.

---

### Task 8: Restructure the frontend shell into three stages

**Files:**

- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/App.vue`
- Create: `frontend/src/components/workspace/SetupStagePage.vue`
- Create: `frontend/src/components/workspace/NovelStagePage.vue`
- Create: `frontend/src/components/workspace/VideoStagePage.vue`
- Modify: `frontend/src/styles/workspace.css`

- [x] **Step 1: Replace the current top-level workspace view model**

Reduce the primary project navigation to:

- `setup`
- `novel`
- `video`

Keep `generationTrace` and `projectLibrary` as secondary routes or panels.

Implemented new `setupStage`, `novelStage`, and `videoStage` view keys. Persisted legacy noisy views now restore to the matching stage by default; `generationTrace` and `projectLibrary` remain secondary entries.

- [x] **Step 2: Build the setup stage page**

`SetupStagePage.vue` should surface:

- project basics
- story boundaries
- major characters
- series plan status
- context review status

Created `frontend/src/components/workspace/SetupStagePage.vue`.

- [x] **Step 3: Build the novel stage page**

`NovelStagePage.vue` should surface:

- chapter list
- current chapter workspace
- current draft
- next action

Created `NovelStagePage.vue` as the stage wrapper over the existing novel longform panel.

- [x] **Step 4: Build the video stage page**

`VideoStagePage.vue` should surface:

- character turnaround lock status
- storyboard status
- preflight status
- video task status

Created `VideoStagePage.vue` as the stage wrapper over the existing video longform panel.

- [ ] **Step 5: Verify routing and state restoration**

Run the app and confirm the persisted view logic no longer restores users into noisy secondary pages by default.

---

### Task 9: Add the “Story Boundary” authoring and rule confirmation UI

**Files:**

- Create: `frontend/src/components/workspace/StoryBoundaryPanel.vue`
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/stores/workbench.ts`
- Modify: `frontend/src/components/workspace/ProjectSettingsPanel.vue`

- [x] **Step 1: Add client types and store actions**

Add types and API calls for:

- submit story-boundary text
- receive parsed candidate rules
- confirm or edit rules

- [x] **Step 2: Render candidate rules as human-readable cards**

The UI must translate rules into simple summaries like:

- “第 1-10 章：禁止男女主直接相遇”
- “第 11 章：允许第一次正式见面”

- [x] **Step 3: Show active rule summaries in the current project-settings flow**

Users should see confirmed rules without reading raw JSON.

- [x] **Step 4: Verify the UX**

Run the app and confirm a user can describe chapter-range rules once, then confirm structured cards.

---

### Task 10: Show active hard constraints and violations in the novel workflow

**Files:**

- Create: `frontend/src/components/workspace/ConstraintViolationBanner.vue`
- Modify: `frontend/src/components/workspace/NovelCreatePage.vue`
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/stores/workbench.ts`

- [x] **Step 1: Show chapter-effective hard constraints in the current chapter view**

For the selected chapter, show:

- active series rules
- active reference-work facts
- authorized overrides

Added a novel-stage `章节硬约束` panel sourced from chapter `constraint_snapshot`.

- [ ] **Step 2: Show violation banners when generation breaks rules**

If a generated chapter violates a hard rule, show:

- violated rule
- reason
- whether auto-rewrite was attempted

Partial: draft versions whose status/revision summary indicates violation are surfaced as warning cards. Remaining work is to expose/render a richer structured `ViolationCheck` list so the UI does not infer violations from summary text.

- [ ] **Step 3: Block misleading success states**

Do not present a violating draft as a successful final result.

- [ ] **Step 4: Verify chapter UX**

Manual check:

- generate a violating chapter
- confirm the UI shows “violated hard constraint” rather than “success”

---

### Task 11: Add reference-asset review and turnaround lock UI in the video workflow

**Files:**

- Create: `frontend/src/components/workspace/ReferenceAssetReviewPanel.vue`
- Modify: `frontend/src/components/workspace/VideoCreatePage.vue`
- Modify: `frontend/src/stores/workbench.ts`
- Modify: `frontend/src/api.ts`

- [ ] **Step 1: Show candidate reference images for the selected work**

Users must be able to approve or reject discovered assets inside the project.

- [x] **Step 2: Show per-character turnaround state**

Display:

- unmapped
- turnaround pending
- candidate ready
- locked

Added per-character turnaround status in the video-stage longform panel. The display now uses `CharacterReferenceProfile` first and falls back to generated/locked `character_turnaround` media assets for compatibility.

- [ ] **Step 3: Make locked turnaround status gate downstream actions**

Video preflight and shot generation should clearly indicate when a character still lacks a locked turnaround.

- [ ] **Step 4: Verify the video-prep UX**

Manual check:

- without a locked turnaround, the system shows blocked or unstable
- after locking, the system allows downstream steps

---

### Task 12: Verification and regression coverage

**Files:**

- Modify: `frontend/scripts/playwright_regression.mjs`
- Create: `tests/test_longform_constraints.py`

- [x] **Step 1: Add backend regression coverage**

Create Python tests covering:

- chapter-range hard rule parsing
- outline validation against hard rules
- draft violation detection

Added focused backend coverage for locked turnaround resolution and same-character lock exclusivity in `tests/test_visual_asset_locked_references.py`. Existing constraint parsing / outline / draft violation tests remain in place.

- [ ] **Step 2: Add frontend regression coverage**

Update Playwright regression to cover:

- three-stage shell navigation
- story-boundary rule confirmation
- hard-constraint visibility in the novel stage

- [ ] **Step 3: Run backend verification**

Run: `python -m unittest`

Expected: new hard-constraint and violation tests pass.

- [ ] **Step 4: Run frontend verification**

Run: `npm run test:regression`

Expected: three-stage workflow and rule-confirmation regressions pass.

- [ ] **Step 5: Run build verification**

Run: `npm run build`

Expected: frontend builds successfully after navigation and component restructuring.
