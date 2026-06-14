<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import type {
  LongformState,
  MediaAsset,
  Project,
  ProjectCreateDraft,
  ProjectDetailResponse,
  ProjectPayload,
  Storyboard,
  StoryboardShot,
  TaskEvent,
  TrashItem,
  VideoTask,
} from "../../types";

type CreationMode = "upload" | "ai" | "manual";
type WorkbenchModule = "projects" | "script" | "assets" | "production" | "settings" | "trash";
type RailItem = { module: WorkbenchModule; label: string; iconPaths: string[] };

const props = defineProps<{
  currentView: string;
  isAuthenticated: boolean;
  username?: string | null;
  projects: Project[];
  activeProject: ProjectDetailResponse | null;
  longformState: LongformState;
  trashItems: TrashItem[];
  trashSummary: Record<TrashItem["item_type"], number>;
  workspaceSearch: string;
  loading: boolean;
  form: ProjectCreateDraft;
}>();

const emit = defineEmits<{
  (e: "login"): void;
  (e: "register"): void;
  (e: "logout"): void;
  (e: "go", view: "studio" | "projectCreate" | "assetLibrary" | "trash"): void;
  (e: "open-project-create", mode: CreationMode): void;
  (e: "open-project", projectId: number): void;
  (e: "delete-project", projectId: number): void;
  (e: "restore-trash", item: TrashItem): void;
  (e: "update-media-asset", assetId: number, meta: Record<string, unknown>): void;
  (e: "delete-media-asset", assetId: number): void;
  (e: "create-video-task", storyboardId: number): void;
  (e: "delete-video-task", taskId: number): void;
  (e: "save-project-settings", payload: ProjectPayload): void;
  (e: "update:workspace-search", value: string): void;
  (e: "update:title", value: string): void;
  (e: "update:genre", value: string): void;
  (e: "update:world-brief", value: string): void;
  (e: "update:writing-rules", value: string): void;
  (e: "submit-create"): void;
}>();

const activeModule = ref<WorkbenchModule>("projects");
const activeStoryboardId = ref<number | null>(null);
const settingsDraft = reactive({ title: "", genre: "", world_brief: "", writing_rules: "" });
const railItems: RailItem[] = [
  { module: "projects", label: "项目", iconPaths: ["M3.5 7.5h6l2 2h9v9a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z", "M3.5 11.5h17"] },
  { module: "script", label: "编剧", iconPaths: ["M6 3.5h9l3 3v14H6z", "M15 3.5v4h4", "M9 11h6M9 15h6M9 18h4"] },
  { module: "assets", label: "资产", iconPaths: ["M4 5.5h16v13H4z", "m6 15 3-3 2.5 2.5 2-2 2.5 2.5", "M15.5 9h.01"] },
  { module: "production", label: "出片", iconPaths: ["M4.5 4.5h15v15h-15z", "m10 9 5 3-5 3z"] },
  { module: "settings", label: "设置", iconPaths: ["M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z", "M19 13.5v-3l-2-.7-.7-1.7.9-1.9-2.1-2.1-1.9.9-1.7-.7-.7-2h-3l-.7 2-1.7.7-1.9-.9-2.1 2.1.9 1.9-.7 1.7-2 .7v3l2 .7.7 1.7-.9 1.9 2.1 2.1 1.9-.9 1.7.7.7 2h3l.7-2 1.7-.7 1.9.9 2.1-2.1-.9-1.9.7-1.7z"] },
  { module: "trash", label: "回收站", iconPaths: ["M5.5 7h13", "M9 7V4.5h6V7", "m7.5 7 .8 13h7.4l.8-13", "M10 10.5v6M14 10.5v6"] },
];

const visibleProjects = computed(() => {
  const keyword = props.workspaceSearch.trim().toLowerCase();
  if (!keyword) return props.projects;
  return props.projects.filter((project) =>
    [project.title, project.genre, project.world_brief, project.writing_rules].join(" ").toLowerCase().includes(keyword),
  );
});
const selectedProject = computed(() => props.activeProject?.project ?? null);
const characterCards = computed(() => props.activeProject?.character_cards ?? []);
const chapterCount = computed(() => props.activeProject?.project_chapters.length ?? 0);
const storyboards = computed(() => props.longformState.storyboards);
const mediaAssets = computed(() => props.longformState.media_assets);
const videoTasks = computed(() => props.longformState.video_tasks);
const selectedStoryboard = computed(() =>
  storyboards.value.find((item) => item.id === activeStoryboardId.value) ?? storyboards.value[0] ?? null,
);
const selectedStoryboardTasks = computed(() =>
  selectedStoryboard.value ? videoTasks.value.filter((task) => task.storyboard_id === selectedStoryboard.value?.id) : [],
);
const selectedStoryboardAssets = computed(() =>
  selectedStoryboard.value ? mediaAssets.value.filter((asset) => asset.storyboard_id === selectedStoryboard.value?.id) : mediaAssets.value,
);
const recentEvents = computed(() => {
  const events: TaskEvent[] = [];
  for (const storyboard of storyboards.value) events.push(...storyboard.events);
  for (const task of videoTasks.value) events.push(...task.events);
  return events.sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 8);
});
const workspaceTitle = computed(() => {
  if (props.currentView === "projectCreate") return "新建项目";
  if (activeModule.value === "projects") return "我的项目";
  if (activeModule.value === "trash") return "回收站";
  return selectedProject.value?.title || "选择一个项目";
});
const preflight = computed(() => {
  const value = selectedStoryboard.value?.progress?.preflight_summary;
  return value && typeof value === "object" ? value as Record<string, unknown> : null;
});
const reviewFindings = computed(() => {
  const value = selectedStoryboard.value?.progress?.review_findings;
  return Array.isArray(value) ? value as Array<Record<string, unknown>> : [];
});
const sourceMode = computed(() => {
  const trace = selectedStoryboard.value?.progress?.generation_trace;
  if (trace && typeof trace === "object" && "source_mode" in trace) return String(trace.source_mode);
  return selectedStoryboard.value?.source_chapter_ids?.length ? "novel_chapters" : "未记录";
});

function selectModule(module: WorkbenchModule) {
  activeModule.value = module;
  if (module === "trash") emit("go", "trash");
  else if (module === "assets") emit("go", "assetLibrary");
  else emit("go", "studio");
}
function openProject(projectId: number) {
  if (!projectId) return;
  activeModule.value = "script";
  emit("open-project", projectId);
}
function selectStoryboard(storyboard: Storyboard) {
  activeStoryboardId.value = storyboard.id;
}
function videoTasksByStoryboard(storyboardId: number) {
  return videoTasks.value.filter((task) => task.storyboard_id === storyboardId);
}
function hasActiveVideoTask(tasks: VideoTask[]) {
  return tasks.some((task) => ["queued", "running"].includes(task.task_status));
}
function statusLabel(status: string | undefined) {
  const labels: Record<string, string> = {
    pending: "等待中", queued: "排队中", running: "生产中", completed: "已完成",
    failed: "失败", blocked: "已阻断", locked: "已锁定", draft: "草稿",
  };
  return labels[status || ""] || status || "未记录";
}
function statusTone(status: string | undefined) {
  if (["completed", "locked", "ready", "passed"].includes(status || "")) return "good";
  if (["failed", "blocked"].includes(status || "")) return "bad";
  if (["running", "queued", "warning"].includes(status || "")) return "warn";
  return "neutral";
}
function formatDateTime(value: string | undefined) {
  if (!value) return "未记录";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "未记录" : date.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}
function shortText(value: string | undefined, fallback: string, length = 90) {
  const text = value?.trim() || fallback;
  return text.length > length ? `${text.slice(0, length)}…` : text;
}
function assetKindLabel(value: string) {
  const lower = value.toLowerCase();
  if (lower.includes("video")) return "视频";
  if (lower.includes("voice") || lower.includes("audio")) return "音频";
  if (lower.includes("turnaround")) return "角色三视图";
  if (lower.includes("last_frame")) return "尾帧";
  if (lower.includes("frame")) return "首帧";
  return "素材";
}
function assetIsLocked(asset: MediaAsset) {
  return asset.meta?.locked === true || asset.meta?.candidate_status === "locked";
}
function assetCandidateLabel(asset: MediaAsset) {
  const version = asset.meta?.candidate_version || asset.meta?.version;
  if (version) return `候选 v${version}${assetIsLocked(asset) ? " · 已采用" : ""}`;
  return assetIsLocked(asset) ? "已采用" : "候选资产";
}
function assetLockMeta(locked: boolean) {
  return { locked, candidate_status: locked ? "locked" : "candidate" };
}
function shotAsset(shot: StoryboardShot) {
  return selectedStoryboardAssets.value.find((asset) => asset.shot_id === shot.id && asset.asset_type.includes("frame"));
}
function projectSettingsPayload() {
  const project = selectedProject.value;
  if (!project) return null;
  return {
    title: settingsDraft.title.trim() || project.title,
    genre: settingsDraft.genre.trim() || project.genre,
    reference_work: project.reference_work,
    reference_work_creator: project.reference_work_creator,
    reference_work_medium: project.reference_work_medium,
    reference_work_synopsis: project.reference_work_synopsis,
    reference_work_style_traits: [...project.reference_work_style_traits],
    reference_work_world_traits: [...project.reference_work_world_traits],
    reference_work_narrative_constraints: [...project.reference_work_narrative_constraints],
    reference_work_confidence_note: project.reference_work_confidence_note,
    reference_inheritance_mode: project.reference_inheritance_mode,
    reference_rewrite_start: project.reference_rewrite_start,
    reference_authorized_changes: project.reference_authorized_changes,
    story_boundary_text: project.story_boundary_text,
    visual_style_locked: project.visual_style_locked,
    visual_style_medium: project.visual_style_medium,
    visual_style_artists: [...project.visual_style_artists],
    visual_style_positive: [...project.visual_style_positive],
    visual_style_negative: [...project.visual_style_negative],
    visual_style_notes: project.visual_style_notes,
    world_brief: settingsDraft.world_brief.trim(),
    writing_rules: settingsDraft.writing_rules.trim(),
    style_profile: project.style_profile,
  };
}
function saveProjectSettings() {
  const payload = projectSettingsPayload();
  if (payload) emit("save-project-settings", payload);
}

watch(() => props.currentView, (view) => {
  if (view === "trash") activeModule.value = "trash";
  else if (view === "assetLibrary") activeModule.value = "assets";
  else if (view === "projectCreate") activeModule.value = "projects";
}, { immediate: true });
watch(selectedProject, (project) => {
  settingsDraft.title = project?.title ?? "";
  settingsDraft.genre = project?.genre ?? "";
  settingsDraft.world_brief = project?.world_brief ?? "";
  settingsDraft.writing_rules = project?.writing_rules ?? "";
}, { immediate: true });
watch(storyboards, (items) => {
  if (!items.some((item) => item.id === activeStoryboardId.value)) activeStoryboardId.value = items[0]?.id ?? null;
}, { immediate: true });
</script>

<template>
  <div class="toon-shell">
    <aside class="toon-rail" aria-label="ToonFlow style navigation">
      <button class="toon-rail__brand" type="button" aria-label="ChenFlow 项目" :aria-current="activeModule === 'projects' ? 'page' : undefined" @click="selectModule('projects')">CF</button>
      <button v-for="item in railItems.slice(0, 4)" :key="item.module" type="button" :class="{ active: activeModule === item.module }" :aria-current="activeModule === item.module ? 'page' : undefined" :aria-label="item.label" :title="item.label" @click="selectModule(item.module)">
        <svg aria-hidden="true" viewBox="0 0 24 24"><path v-for="path in item.iconPaths" :key="path" :d="path" /></svg><small class="toon-rail__label">{{ item.label }}</small>
      </button>
      <i aria-hidden="true"></i>
      <button v-for="item in railItems.slice(4)" :key="item.module" type="button" :class="{ active: activeModule === item.module }" :aria-current="activeModule === item.module ? 'page' : undefined" :aria-label="item.label" :title="item.label" @click="selectModule(item.module)">
        <svg aria-hidden="true" viewBox="0 0 24 24"><path v-for="path in item.iconPaths" :key="path" :d="path" /></svg><small class="toon-rail__label">{{ item.label }}</small>
      </button>
    </aside>

    <main class="toon-stage">
      <header class="toon-topbar">
        <div class="toon-heading">
          <span>ChenFlow Studio</span>
          <h1>{{ workspaceTitle }}</h1>
        </div>
        <nav aria-label="Project modules">
          <button v-for="item in railItems.slice(1, 5)" :key="item.module" type="button" :class="{ active: activeModule === item.module }" :aria-current="activeModule === item.module ? 'page' : undefined" @click="selectModule(item.module)">
            <svg aria-hidden="true" viewBox="0 0 24 24"><path v-for="path in item.iconPaths" :key="path" :d="path" /></svg>{{ item.label }}
          </button>
        </nav>
        <div class="toon-user">
          <template v-if="isAuthenticated"><span>{{ username || "已登录" }}</span><button type="button" @click="emit('logout')">退出</button></template>
          <template v-else><button type="button" @click="emit('login')">登录</button><button type="button" class="toon-button--dark" @click="emit('register')">创建账号</button></template>
        </div>
      </header>

      <section v-if="!isAuthenticated" class="toon-empty">
        <strong>从故事材料到最终成片，都留在一个项目里。</strong>
        <p>登录后建立项目，组织剧本、资产、分镜、质量门禁和视频任务。</p>
        <div><button type="button" class="toon-button--dark" @click="emit('register')">创建账号</button><button type="button" @click="emit('login')">登录</button></div>
      </section>

      <section v-else-if="currentView === 'projectCreate'" class="toon-create">
        <header><span>NEW PROJECT</span><h2>建立创作项目</h2><p>先录入最小必要信息，后续内容在生产工作台中持续补齐。</p></header>
        <form @submit.prevent="emit('submit-create')">
          <label><span>项目标题</span><input :value="form.title" maxlength="120" autocomplete="off" @input="emit('update:title', ($event.target as HTMLInputElement).value)" /></label>
          <label><span>题材 / 风格</span><input :value="form.genre" maxlength="80" autocomplete="off" @input="emit('update:genre', ($event.target as HTMLInputElement).value)" /></label>
          <label><span>原著或故事资料</span><textarea :value="form.world_brief" rows="8" @input="emit('update:world-brief', ($event.target as HTMLTextAreaElement).value)" /></label>
          <label><span>改编要求</span><textarea :value="form.writing_rules" rows="5" @input="emit('update:writing-rules', ($event.target as HTMLTextAreaElement).value)" /></label>
          <footer><button type="submit" class="toon-button--dark" :disabled="loading">{{ loading ? "创建中..." : "创建项目" }}</button><button type="button" @click="emit('go', 'studio')">取消</button></footer>
        </form>
      </section>

      <section v-else-if="activeModule === 'projects'" class="toon-projects">
        <header class="toon-section-head"><div><span>PROJECT LIBRARY</span><h2>我的项目</h2><p>管理所有长篇、短剧和视频续作项目。</p></div><button type="button" class="toon-button--dark" @click="emit('open-project-create', 'manual')">＋ 新建项目</button></header>
        <div class="toon-project-toolbar"><input :value="workspaceSearch" aria-label="搜索项目" placeholder="搜索项目名称、题材或故事资料…" @input="emit('update:workspace-search', ($event.target as HTMLInputElement).value)" /><span>{{ visibleProjects.length }} 个项目</span></div>
        <div v-if="visibleProjects.length" class="toon-project-grid">
          <article v-for="project in visibleProjects" :key="project.id" tabindex="0" @click="openProject(project.id)" @keydown.enter.self.prevent="openProject(project.id)" @keydown.space.self.prevent="openProject(project.id)">
            <header><strong>{{ project.title }}</strong><span>{{ project.genre || "未设置题材" }}</span></header>
            <p>{{ shortText(project.world_brief || project.writing_rules, "打开项目继续整理故事、资产与视频。", 130) }}</p>
            <footer><time>{{ formatDateTime(project.updated_at) }}</time><button type="button" @click.stop="emit('delete-project', project.id)">删除</button></footer>
          </article>
        </div>
        <div v-else class="toon-empty"><strong>还没有项目</strong><p>创建第一个项目，把故事材料、人物、分镜和视频生产放进同一个工作台。</p></div>
      </section>

      <section v-else-if="activeModule === 'trash'" class="toon-projects">
        <header class="toon-section-head"><div><span>TRASH</span><h2>回收站</h2><p>项目 {{ trashSummary.project }} · 资产 {{ trashSummary.media_asset }}</p></div></header>
        <div v-if="trashItems.length" class="toon-project-grid">
          <article v-for="item in trashItems" :key="`${item.item_type}-${item.item_id}`"><header><strong>{{ item.title }}</strong><span>{{ item.item_type }}</span></header><p>{{ item.subtitle }}</p><footer><time>{{ formatDateTime(item.deleted_at) }}</time><button type="button" @click="emit('restore-trash', item)">恢复</button></footer></article>
        </div>
        <div v-else class="toon-empty"><strong>回收站目前是空的</strong><p>删除的项目和资产会暂存在这里。</p></div>
      </section>

      <section v-else class="toon-workbench">
        <aside class="toon-inspector">
          <label class="toon-project-select"><span>当前项目</span><select :value="selectedProject?.id || ''" @change="openProject(Number(($event.target as HTMLSelectElement).value))"><option value="" disabled>选择项目</option><option v-for="project in projects" :key="project.id" :value="project.id">{{ project.title }}</option></select></label>
          <div class="toon-inspector__block"><strong>生产概览</strong><dl><div><dt>章节</dt><dd>{{ chapterCount }}</dd></div><div><dt>草稿</dt><dd>{{ longformState.draft_versions.length }}</dd></div><div><dt>资产</dt><dd>{{ mediaAssets.length }}</dd></div><div><dt>分镜</dt><dd>{{ storyboards.length }}</dd></div></dl></div>
          <div class="toon-inspector__block"><strong>下一步</strong><p v-if="!selectedProject">先选择一个项目。</p><p v-else-if="!storyboards.length">故事资料已进入项目，下一步需要生成或导入分镜。</p><p v-else-if="!mediaAssets.length">分镜已经存在，下一步准备角色资产和镜头首帧。</p><p v-else-if="!videoTasks.length">资产已经进入生产区，下一步执行预检并创建视频任务。</p><p v-else>视频任务已经开始，持续关注右侧运行记录和质量结果。</p></div>
          <div v-if="storyboards.length" class="toon-storyboard-list"><strong>分镜稿</strong><button v-for="storyboard in storyboards" :key="storyboard.id" type="button" :class="{ active: selectedStoryboard?.id === storyboard.id }" @click="selectStoryboard(storyboard)"><span>{{ storyboard.title }}</span><small>{{ storyboard.shots.length }} 镜头 · {{ statusLabel(storyboard.status) }}</small></button></div>
        </aside>

        <div class="toon-canvas" :class="`toon-canvas--${activeModule}`" :aria-label="`${activeModule}画布`">
          <div class="toon-canvas-toolbar"><div><span class="toon-dot"></span><strong>{{ selectedProject?.title || "未选择项目" }}</strong><small>{{ activeModule === "script" ? "编剧工作台" : activeModule === "assets" ? "资产工作台" : activeModule === "production" ? "出片工作台" : "项目设置" }}</small></div><div><button type="button" title="刷新状态" @click="selectedProject && emit('open-project', selectedProject.id)">↻</button><span>画布 100%</span></div></div>

          <div v-if="!selectedProject" class="toon-empty toon-empty--canvas"><strong>先打开一个项目</strong><p>选择项目后，真实生产数据会铺在这张画布上。</p></div>

          <div v-else-if="activeModule === 'script'" class="toon-flow">
            <article class="toon-flow-node toon-flow-node--source"><header><span>01 · 故事源</span><b :class="`tone-${selectedProject?.world_brief ? 'good' : 'warn'}`">{{ selectedProject?.world_brief ? "已录入" : "待补充" }}</b></header><h3>{{ selectedProject?.title }}</h3><p>{{ shortText(selectedProject?.world_brief, "尚未录入故事资料。") }}</p><footer>{{ selectedProject?.reference_work || "原创项目" }}</footer></article>
            <span class="toon-connector">→</span>
            <article class="toon-flow-node"><header><span>02 · 创作约束</span><b :class="`tone-${selectedProject?.writing_rules ? 'good' : 'warn'}`">{{ selectedProject?.writing_rules ? "已设置" : "待补充" }}</b></header><h3>改编策略</h3><p>{{ shortText(selectedProject?.writing_rules, "尚未设置改编要求。") }}</p><footer>{{ characterCards.length }} 人物卡 · {{ props.activeProject?.sources.length || 0 }} 资料</footer></article>
            <span class="toon-connector">→</span>
            <article class="toon-flow-node"><header><span>03 · 长篇产物</span><b :class="`tone-${longformState.draft_versions.length ? 'good' : 'neutral'}`">{{ longformState.draft_versions.length ? "有草稿" : "未开始" }}</b></header><h3>{{ longformState.series_plans[0]?.title || "系列规划与正文" }}</h3><p>{{ longformState.series_plans[0]?.theme || "概要、章节规划和正文版本会在这里汇总。" }}</p><footer>{{ longformState.series_plans.length }} 份规划 · {{ longformState.draft_versions.length }} 个草稿</footer></article>
            <span class="toon-connector">→</span>
            <article class="toon-flow-node"><header><span>04 · 分镜出口</span><b :class="`tone-${storyboards.length ? 'good' : 'neutral'}`">{{ storyboards.length ? "已连接" : "未开始" }}</b></header><h3>{{ selectedStoryboard?.title || "等待分镜" }}</h3><p>{{ selectedStoryboard?.summary || "完成故事与正文准备后，从这里进入镜头生产。" }}</p><footer>{{ selectedStoryboard?.shots.length || 0 }} 镜头</footer></article>
          </div>

          <div v-else-if="activeModule === 'assets'" class="toon-asset-board">
            <article v-for="asset in mediaAssets" :key="asset.id" class="toon-asset-card">
              <div class="toon-asset-card__preview"><img v-if="/^https?:|^data:|\\.(png|jpg|jpeg|webp|gif)$/i.test(asset.uri)" :src="asset.uri" :alt="assetKindLabel(asset.asset_type)" loading="lazy" /><span v-else>{{ assetKindLabel(asset.asset_type) }}</span></div>
              <header><strong>{{ assetKindLabel(asset.asset_type) }} #{{ asset.id }}</strong><b :class="`tone-${assetIsLocked(asset) ? 'good' : 'neutral'}`">{{ assetCandidateLabel(asset) }}</b></header>
              <p>{{ shortText(asset.prompt || asset.status, "项目素材", 72) }}</p>
              <footer><button v-if="!assetIsLocked(asset)" type="button" :disabled="loading" @click="emit('update-media-asset', asset.id, assetLockMeta(true))">设为采用</button><button v-else type="button" :disabled="loading" @click="emit('update-media-asset', asset.id, assetLockMeta(false))">取消采用</button><button type="button" :disabled="loading" @click="emit('delete-media-asset', asset.id)">删除候选</button></footer>
            </article>
            <div v-if="!mediaAssets.length" class="toon-empty toon-empty--canvas"><strong>等待生成资产</strong><p>角色三视图、场景图、镜头首帧和音频会铺在这里。</p></div>
          </div>

          <div v-else-if="activeModule === 'production'" class="toon-production-board">
            <template v-if="selectedStoryboard">
              <article class="toon-storyboard-table">
                <header><div><span>分镜表</span><h3>{{ selectedStoryboard.title }}</h3></div><b :class="`tone-${statusTone(selectedStoryboard.status)}`">{{ statusLabel(selectedStoryboard.status) }}</b></header>
                <div class="toon-shot-table"><div class="toon-shot-table__head"><span>镜头</span><span>画面与动作</span><span>时长</span><span>状态</span></div><div v-for="shot in selectedStoryboard.shots" :key="shot.id" class="toon-shot-row"><span>S{{ String(shot.shot_no).padStart(2, "0") }}</span><span><strong>{{ shortText(shot.narration_text, "无旁白", 36) }}</strong><small>{{ shortText(shot.visual_prompt, "尚未填写视觉提示词", 58) }}</small></span><span>{{ shot.duration_seconds }}s</span><span>{{ statusLabel(shot.status) }}</span></div></div>
              </article>
              <span class="toon-connector">→</span>
              <article class="toon-frame-panel"><header><div><span>镜头面板</span><h3>{{ selectedStoryboard.shots.length }} 个镜头</h3></div><button type="button" :disabled="loading || hasActiveVideoTask(selectedStoryboardTasks)" @click="emit('create-video-task', selectedStoryboard.id)">{{ hasActiveVideoTask(selectedStoryboardTasks) ? "生产中" : "创建视频任务" }}</button></header><div class="toon-frame-grid"><div v-for="shot in selectedStoryboard.shots" :key="shot.id"><img v-if="shotAsset(shot)?.uri" :src="shotAsset(shot)?.uri" alt="" /><span v-else>未生成</span><small>S{{ String(shot.shot_no).padStart(2, "0") }}</small></div></div></article>
            </template>
            <div v-else class="toon-empty toon-empty--canvas"><strong>Track 1 · 分镜</strong><p>生成或导入分镜后，这里会形成可审核的镜头生产轨道。</p></div>
          </div>

          <form v-else-if="activeModule === 'settings' && selectedProject" class="toon-settings" @submit.prevent="saveProjectSettings()"><header><span>PROJECT SETTINGS</span><h3>{{ selectedProject.title }}</h3></header><label><span>项目标题</span><input v-model="settingsDraft.title" maxlength="120" /></label><label><span>题材 / 风格</span><input v-model="settingsDraft.genre" maxlength="80" /></label><label><span>故事资料</span><textarea v-model="settingsDraft.world_brief" rows="7" /></label><label><span>改编要求</span><textarea v-model="settingsDraft.writing_rules" rows="6" /></label><footer><button type="submit" class="toon-button--dark" :disabled="loading">{{ loading ? "保存中..." : "保存设置" }}</button></footer></form>
        </div>

        <aside class="toon-agent">
          <header><div><span class="toon-dot"></span><strong>生产监督</strong></div><small>{{ selectedStoryboard?.title || "项目状态" }}</small></header>
          <section><span>来源与预检</span><dl><div><dt>来源模式</dt><dd>{{ sourceMode }}</dd></div><div><dt>预检状态</dt><dd :class="`tone-text-${statusTone(String(preflight?.readiness || ''))}`">{{ preflight ? statusLabel(String(preflight.readiness)) : "尚未执行" }}</dd></div><div><dt>质量问题</dt><dd>{{ reviewFindings.length }}</dd></div></dl></section>
          <section v-if="reviewFindings.length"><span>质量复查</span><article v-for="finding in reviewFindings.slice(0, 4)" :key="String(finding.finding_id)"><b :class="`tone-${finding.severity === 'blocking' ? 'bad' : 'warn'}`">{{ finding.severity === "blocking" ? "阻断" : "建议" }}</b><strong>{{ finding.title }}</strong><p>{{ finding.detail }}</p></article></section>
          <section><span>运行记录</span><article v-for="event in recentEvents" :key="event.id"><time>{{ formatDateTime(event.created_at) }}</time><strong>{{ event.message }}</strong></article><p v-if="!recentEvents.length">当前项目还没有生产运行记录。</p></section>
          <section v-if="selectedStoryboardTasks.length"><span>视频任务</span><article v-for="task in selectedStoryboardTasks" :key="task.id"><b :class="`tone-${statusTone(task.task_status)}`">{{ statusLabel(task.task_status) }}</b><strong>任务 #{{ task.id }}</strong><a v-if="task.output_uri" :href="task.output_uri" target="_blank" rel="noreferrer">查看输出</a><button type="button" :disabled="loading || task.task_status === 'running'" @click="emit('delete-video-task', task.id)">删除任务</button></article></section>
        </aside>
      </section>
    </main>
  </div>
</template>

<style scoped>
.toon-shell { min-height: calc(100vh - 32px); display: grid; grid-template-columns: 68px minmax(0, 1fr); gap: 12px; color: var(--toon-ink); font-family: "Microsoft YaHei", "PingFang SC", sans-serif; --toon-ink: oklch(31% .055 345); --toon-ink-soft: oklch(47% .045 345); --toon-ink-muted: oklch(61% .035 345); --toon-glass: rgba(255,248,252,.68); --toon-glass-strong: rgba(255,251,253,.82); --toon-line: rgba(255,226,239,.86); --toon-rose: oklch(65% .155 350); --toon-rose-deep: oklch(55% .14 350); --toon-rose-soft: oklch(95% .045 350); --toon-shadow: 0 20px 48px color-mix(in oklab, var(--toon-rose) 15%, transparent); }
button, input, textarea, select { font: inherit; }
button { min-height: 42px; border: 1px solid color-mix(in oklab, var(--toon-rose) 18%, transparent); border-radius: 9px; background: rgba(255,249,252,.7); color: var(--toon-ink); padding: 0 13px; cursor: pointer; }
button:hover { border-color: color-mix(in oklab, var(--toon-rose) 42%, transparent); background: rgba(255,252,254,.92); }
button:focus-visible, input:focus-visible, textarea:focus-visible, select:focus-visible { outline: 2px solid color-mix(in oklab, var(--rose-strong) 66%, white); outline-offset: 2px; }
button:disabled { cursor: wait; opacity: .48; }
.toon-button--dark { border-color: transparent; background: var(--toon-rose); color: white; }
.toon-button--dark:hover { background: var(--toon-rose-deep); color: white; }
.toon-rail, .toon-stage { border: 1px solid var(--toon-line); background: var(--toon-glass); box-shadow: var(--toon-shadow); backdrop-filter: blur(24px) saturate(1.12); -webkit-backdrop-filter: blur(24px) saturate(1.12); }
.toon-rail { position: sticky; top: 16px; height: calc(100vh - 32px); display: grid; grid-template-rows: repeat(5, 48px) 1fr repeat(2, 48px); gap: 8px; padding: 10px; border-radius: 18px; }
.toon-rail button { width: 46px; padding: 0; border: 0; background: transparent; color: var(--toon-ink-soft); }
.toon-rail svg, .toon-topbar nav svg { width: 21px; height: 21px; fill: none; stroke: currentColor; stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; }
.toon-topbar nav svg { width: 17px; height: 17px; }
.toon-rail__label { display: none; font-size: .68rem; font-weight: 700; }
.toon-rail button.active, .toon-rail__brand { background: var(--toon-rose); color: oklch(99% .008 350); box-shadow: 0 10px 22px color-mix(in oklab, var(--toon-rose) 30%, transparent); }
.toon-rail__brand { font-size: .84rem !important; letter-spacing: -.08em; }
.toon-stage { min-width: 0; min-height: calc(100vh - 32px); display: grid; grid-template-rows: auto minmax(0, 1fr); gap: 14px; padding: 18px; border-radius: 18px; }
.toon-topbar { display: grid; grid-template-columns: minmax(220px, 1fr) auto auto; gap: 18px; align-items: center; padding: 0 4px 14px; border-bottom: 1px solid rgba(110,52,78,.1); }
.toon-heading { min-width: 0; }
.toon-heading span, .toon-section-head span, .toon-create header span, .toon-settings header span { color: var(--toon-ink-muted); font-size: .72rem; font-weight: 800; letter-spacing: .12em; }
.toon-heading h1, .toon-section-head h2, .toon-create h2 { margin: 3px 0 0; overflow: hidden; font-size: 1.45rem; line-height: 1.2; text-overflow: ellipsis; white-space: nowrap; }
.toon-topbar nav, .toon-user, .toon-empty > div, .toon-create footer { display: flex; gap: 8px; align-items: center; }
.toon-topbar nav button { display: flex; gap: 7px; align-items: center; border-color: transparent; background: transparent; }
.toon-topbar nav button.active { border-color: transparent; background: var(--toon-rose); color: white; }
.toon-user { justify-content: end; }
.toon-user > span { max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.toon-empty { min-height: 280px; display: grid; place-content: center; justify-items: start; gap: 10px; padding: 28px; border: 1px dashed rgba(151,77,109,.24); border-radius: 14px; background: rgba(255,255,255,.46); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); }
.toon-empty strong { font-size: 1.25rem; }.toon-empty p { max-width: 56ch; margin: 0; color: var(--toon-ink-soft); line-height: 1.7; }
.toon-create { display: grid; grid-template-columns: minmax(220px, .55fr) minmax(0, 1fr); gap: 64px; align-content: start; padding: 42px; }
.toon-create header p, .toon-section-head p { max-width: 60ch; color: var(--toon-ink-soft); line-height: 1.65; }
.toon-create form, .toon-create label, .toon-settings, .toon-settings label { display: grid; gap: 10px; }
.toon-create form, .toon-settings { gap: 16px; }
.toon-create input, .toon-create textarea, .toon-settings input, .toon-settings textarea, .toon-project-select select, .toon-project-toolbar input { width: 100%; border: 1px solid color-mix(in oklab, var(--toon-rose) 20%, transparent); border-radius: 9px; background: rgba(255,250,253,.74); padding: 11px 12px; color: var(--toon-ink); }
.toon-create textarea, .toon-settings textarea { resize: vertical; line-height: 1.65; }
.toon-projects { display: grid; gap: 18px; align-content: start; padding: 20px; }
.toon-section-head { display: flex; justify-content: space-between; gap: 24px; align-items: end; }
.toon-section-head h2 { font-size: 2rem; }
.toon-project-toolbar { display: flex; gap: 12px; align-items: center; }.toon-project-toolbar input { max-width: 520px; }.toon-project-toolbar span { color: var(--toon-ink-soft); font-size: .85rem; }
.toon-project-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }
.toon-project-grid article { min-height: 210px; display: grid; gap: 18px; align-content: start; padding: 20px; border: 1px solid var(--toon-line); border-radius: 12px; background: rgba(255,255,255,.54); box-shadow: 0 12px 30px rgba(213,91,141,.08); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); cursor: pointer; }
.toon-project-grid article:hover { border-color: rgba(218,91,145,.3); background: rgba(255,255,255,.76); box-shadow: 0 16px 34px rgba(213,91,141,.14); transform: translateY(-1px); }
.toon-project-grid header, .toon-project-grid footer, .toon-flow-node header, .toon-flow-node footer, .toon-asset-card header, .toon-asset-card footer, .toon-storyboard-table > header, .toon-frame-panel > header, .toon-agent > header { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
.toon-project-grid header strong { font-size: 1.12rem; }.toon-project-grid header span, .toon-project-grid time { color: var(--toon-ink-muted); font-size: .78rem; }
.toon-project-grid p { margin: 0; color: var(--toon-ink-soft); line-height: 1.7; }.toon-project-grid footer { margin-top: auto; }
.toon-workbench { min-height: 0; display: grid; grid-template-columns: 244px minmax(620px, 1fr) 308px; gap: 10px; overflow: auto; }
.toon-inspector, .toon-agent { min-height: 0; overflow: auto; border: 1px solid var(--toon-line); border-radius: 12px; background: var(--toon-glass); box-shadow: 0 14px 34px rgba(213,91,141,.08); backdrop-filter: blur(22px); -webkit-backdrop-filter: blur(22px); }
.toon-inspector { display: grid; gap: 18px; align-content: start; padding: 14px; }
.toon-project-select, .toon-inspector__block, .toon-storyboard-list { display: grid; gap: 9px; }
.toon-project-select > span, .toon-inspector__block > strong, .toon-storyboard-list > strong { color: var(--toon-ink-soft); font-size: .75rem; letter-spacing: .06em; }
.toon-inspector__block { padding-top: 16px; border-top: 1px solid rgba(110,52,78,.09); }
.toon-inspector__block dl, .toon-agent dl { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin: 0; }
.toon-inspector__block dl div, .toon-agent dl div { display: grid; gap: 3px; padding: 9px; background: rgba(255,239,246,.62); border: 1px solid rgba(255,255,255,.76); border-radius: 8px; }
dt { color: var(--toon-ink-muted); font-size: .7rem; } dd { margin: 0; font-weight: 800; }
.toon-inspector__block p { margin: 0; color: var(--toon-ink-soft); font-size: .85rem; line-height: 1.65; }
.toon-storyboard-list button { height: auto; display: grid; gap: 3px; justify-items: start; padding: 10px; text-align: left; }
.toon-storyboard-list button.active { border-color: transparent; background: var(--toon-rose); color: white; }.toon-storyboard-list small { opacity: .66; }
.toon-canvas { min-height: 720px; overflow: auto; border: 1px solid var(--toon-line); border-radius: 12px; background: radial-gradient(circle, rgba(132,67,96,.18) 1px, transparent 1px) 0 0 / 18px 18px, rgba(255,255,255,.4); box-shadow: inset 0 1px 0 rgba(255,255,255,.72); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); }
.toon-canvas-toolbar { position: sticky; top: 0; z-index: 3; display: flex; justify-content: space-between; gap: 16px; align-items: center; padding: 11px 14px; border-bottom: 1px solid rgba(110,52,78,.1); background: rgba(255,255,255,.78); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }
.toon-canvas-toolbar > div { display: flex; gap: 9px; align-items: center; }.toon-canvas-toolbar small, .toon-canvas-toolbar span:last-child { color: var(--toon-ink-muted); font-size: .75rem; }.toon-canvas-toolbar button { min-height: 34px; padding: 0 10px; }
.toon-dot { width: 8px; height: 8px; border-radius: 50%; background: #17a34a; }
.toon-empty--canvas { margin: 80px auto; width: min(520px, calc(100% - 48px)); }
.toon-flow, .toon-production-board { min-width: 1100px; display: flex; gap: 18px; align-items: center; padding: 52px 32px; }
.toon-flow-node { width: 250px; min-height: 230px; display: grid; gap: 15px; align-content: start; padding: 16px; border: 1px solid var(--toon-line); border-radius: 12px; background: rgba(255,255,255,.72); box-shadow: 0 14px 30px rgba(213,91,141,.1); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); }
.toon-flow-node--source { margin-top: -80px; }.toon-flow-node:nth-of-type(2) { margin-top: 80px; }.toon-flow-node:nth-of-type(3) { margin-top: -30px; }
.toon-flow-node h3, .toon-flow-node p { margin: 0; }.toon-flow-node p { color: var(--toon-ink-soft); font-size: .84rem; line-height: 1.65; }.toon-flow-node footer { margin-top: auto; color: var(--toon-ink-muted); font-size: .75rem; }
.toon-flow-node header span, .toon-storyboard-table header span, .toon-frame-panel header span { color: var(--toon-ink-soft); font-size: .72rem; font-weight: 800; letter-spacing: .06em; }
.toon-connector { color: color-mix(in oklab, var(--toon-rose) 58%, var(--toon-ink-soft)); font-size: 1.5rem; }
[class^="tone-"], [class*=" tone-"] { display: inline-flex; width: fit-content; border-radius: 4px; padding: 3px 6px; font-size: .68rem; font-weight: 800; }
.tone-good { background: #d9f5e3; color: #087434; }.tone-warn { background: #fff0c9; color: #8a5b00; }.tone-bad { background: #ffe0df; color: #a11d17; }.tone-neutral { background: var(--toon-rose-soft); color: var(--toon-ink-soft); }
.tone-text-good { color: #087434; }.tone-text-warn { color: #8a5b00; }.tone-text-bad { color: #a11d17; }.tone-text-neutral { color: var(--toon-ink-soft); }
.toon-asset-board { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 12px; align-content: start; padding: 24px; }
.toon-asset-card { display: grid; gap: 10px; padding: 10px; border: 1px solid var(--toon-line); border-radius: 10px; background: rgba(255,255,255,.7); box-shadow: 0 12px 26px rgba(213,91,141,.08); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); }
.toon-asset-card__preview { aspect-ratio: 16/10; display: grid; place-items: center; overflow: hidden; border-radius: 7px; background: rgba(255,235,244,.72); color: var(--toon-ink-muted); }.toon-asset-card__preview img { width: 100%; height: 100%; object-fit: cover; }
.toon-asset-card p { min-height: 3em; margin: 0; color: var(--toon-ink-soft); font-size: .76rem; line-height: 1.55; }.toon-asset-card footer { justify-content: start; flex-wrap: wrap; }.toon-asset-card footer button { min-height: 32px; padding: 0 8px; font-size: .72rem; }
.toon-storyboard-table { width: 540px; max-height: 610px; overflow: auto; border: 1px solid var(--toon-line); border-radius: 10px; background: rgba(255,255,255,.7); box-shadow: 0 14px 30px rgba(213,91,141,.1); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); }.toon-storyboard-table > header, .toon-frame-panel > header { position: sticky; top: 0; z-index: 2; padding: 13px; border-bottom: 1px solid rgba(110,52,78,.1); background: rgba(255,255,255,.88); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); }.toon-storyboard-table h3, .toon-frame-panel h3 { margin: 3px 0 0; font-size: .95rem; }
.toon-shot-table__head, .toon-shot-row { display: grid; grid-template-columns: 52px minmax(260px, 1fr) 52px 70px; align-items: start; }.toon-shot-table__head { position: sticky; top: 67px; padding: 8px 10px; background: rgba(255,234,243,.88); color: var(--toon-ink-soft); font-size: .68rem; }.toon-shot-row { padding: 10px; border-top: 1px solid rgba(110,52,78,.08); font-size: .74rem; }.toon-shot-row:nth-child(odd) { background: rgba(255,249,252,.54); }.toon-shot-row > span:nth-child(2) { display: grid; gap: 4px; }.toon-shot-row small { color: var(--toon-ink-soft); line-height: 1.5; }
.toon-frame-panel { width: 520px; min-height: 430px; border: 1px solid var(--toon-line); border-radius: 10px; background: rgba(255,255,255,.7); box-shadow: 0 14px 30px rgba(213,91,141,.1); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); }.toon-frame-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; padding: 10px; }.toon-frame-grid > div { position: relative; aspect-ratio: 16/10; display: grid; place-items: center; overflow: hidden; border-radius: 5px; background: rgba(255,235,244,.72); color: var(--toon-ink-muted); font-size: .68rem; }.toon-frame-grid img { width: 100%; height: 100%; object-fit: cover; }.toon-frame-grid small { position: absolute; top: 4px; left: 4px; padding: 2px 4px; border-radius: 3px; background: var(--toon-rose); color: white; font-size: .58rem; }
.toon-settings { width: min(720px, calc(100% - 48px)); margin: 28px; padding: 22px; border: 1px solid var(--toon-line); border-radius: 12px; background: rgba(255,255,255,.72); box-shadow: 0 14px 30px rgba(213,91,141,.1); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); }.toon-settings h3 { margin: 4px 0 0; }
.toon-agent { display: grid; gap: 0; align-content: start; }.toon-agent > header { position: sticky; top: 0; z-index: 2; padding: 14px; border-bottom: 1px solid rgba(110,52,78,.1); background: rgba(255,255,255,.8); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }.toon-agent > header > div { display: flex; gap: 8px; align-items: center; }.toon-agent > header small { color: var(--toon-ink-muted); }
.toon-agent section { display: grid; gap: 10px; padding: 14px; border-bottom: 1px solid rgba(110,52,78,.08); }.toon-agent section > span { color: var(--toon-ink-soft); font-size: .72rem; font-weight: 800; letter-spacing: .08em; }.toon-agent article { display: grid; gap: 6px; padding: 10px; border: 1px solid rgba(255,255,255,.82); border-radius: 8px; background: rgba(255,255,255,.5); }.toon-agent article p, .toon-agent section > p { margin: 0; color: var(--toon-ink-soft); font-size: .76rem; line-height: 1.55; }.toon-agent article time { color: var(--toon-ink-muted); font-size: .68rem; }.toon-agent article a { color: var(--toon-rose-deep); font-size: .76rem; font-weight: 800; }.toon-agent article button { min-height: 32px; width: fit-content; font-size: .72rem; }
@media (max-width: 1180px) { .toon-workbench { grid-template-columns: 220px minmax(620px, 1fr); }.toon-agent { grid-column: 1 / -1; max-height: 360px; }.toon-topbar { grid-template-columns: minmax(180px, 1fr) auto; }.toon-user { grid-column: 1 / -1; justify-content: start; } }
@media (max-width: 900px) { .toon-shell { grid-template-columns: minmax(0, 1fr); }.toon-rail { position: sticky; top: 8px; z-index: 8; height: auto; grid-template-columns: repeat(7, minmax(64px, 1fr)); grid-template-rows: auto; overflow-x: auto; padding: 8px; }.toon-rail i { display: none; }.toon-rail button { width: auto; min-width: 64px; min-height: 50px; display: grid; place-content: center; gap: 2px; font-size: 1.05rem; }.toon-rail__brand { min-width: 52px !important; }.toon-rail__label { display: block; }.toon-stage { min-height: auto; }.toon-topbar nav { display: none; }.toon-workbench { grid-template-columns: minmax(0, 1fr); overflow: visible; }.toon-inspector, .toon-agent { max-height: none; }.toon-inspector { grid-template-columns: repeat(2, minmax(0, 1fr)); }.toon-project-select, .toon-storyboard-list { grid-column: 1 / -1; }.toon-canvas { min-height: 620px; }.toon-flow, .toon-production-board { min-width: 980px; } }
@media (max-width: 760px) { .toon-shell { gap: 8px; }.toon-stage { padding: 12px; }.toon-topbar, .toon-create, .toon-section-head { display: grid; grid-template-columns: minmax(0, 1fr); }.toon-user { grid-column: auto; }.toon-project-toolbar { align-items: stretch; flex-direction: column; }.toon-inspector { grid-template-columns: minmax(0, 1fr); }.toon-project-select, .toon-storyboard-list { grid-column: auto; }.toon-canvas { min-height: 560px; scroll-snap-type: x proximity; }.toon-flow > *, .toon-production-board > * { scroll-snap-align: start; }.toon-create { padding: 18px; gap: 24px; } }
@media (max-width: 460px) { .toon-rail { grid-template-columns: repeat(7, 62px); }.toon-topbar { gap: 12px; }.toon-heading h1 { font-size: 1.15rem; }.toon-user { width: 100%; overflow-x: auto; }.toon-user button { min-height: 44px; }.toon-canvas-toolbar { align-items: flex-start; }.toon-canvas-toolbar > div:last-child { flex-shrink: 0; }.toon-project-grid { grid-template-columns: minmax(0, 1fr); }.toon-create form { padding: 14px; } }
</style>
