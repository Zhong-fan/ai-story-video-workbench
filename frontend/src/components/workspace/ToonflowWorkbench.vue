<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import type { LongformState, MediaAsset, Project, ProjectCreateDraft, ProjectDetailResponse, ProjectPayload, TrashItem, VideoTask } from "../../types";

type CreationMode = "upload" | "ai" | "manual";
type WorkbenchModule = "projects" | "script" | "assets" | "production" | "settings" | "trash";
type RailItem = {
  module: WorkbenchModule;
  label: string;
  paths: string[];
};

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
const settingsDraft = reactive({
  title: "",
  genre: "",
  world_brief: "",
  writing_rules: "",
});
const moduleLabels: Record<WorkbenchModule, string> = {
  projects: "项目",
  script: "编剧",
  assets: "资产",
  production: "出片",
  settings: "设置",
  trash: "回收站",
};
const railItems: RailItem[] = [
  {
    module: "projects",
    label: "项目",
    paths: [
      "M6 12.5A2.5 2.5 0 0 1 8.5 10H15l2 3h8.5A2.5 2.5 0 0 1 28 15.5v8A2.5 2.5 0 0 1 25.5 26h-17A2.5 2.5 0 0 1 6 23.5v-11Z",
      "M10 18h14",
    ],
  },
  {
    module: "script",
    label: "编剧",
    paths: [
      "M9 7h10l4 4v14H9V7Z",
      "M19 7v5h5",
      "M12 16h9M12 20h7",
    ],
  },
  {
    module: "assets",
    label: "资产",
    paths: [
      "M7 9h18v17H7V9Z",
      "m9 23 5.2-6 3.8 4.2 2.4-2.7L25 23",
      "M20.5 13.5h.01",
    ],
  },
  {
    module: "production",
    label: "出片",
    paths: [
      "M8 8h18v18H8V8Z",
      "m14 13 7 4-7 4v-8Z",
    ],
  },
  {
    module: "settings",
    label: "设置",
    paths: [
      "M9 11h14M9 17h14M9 23h14",
      "M13 9v4M20 15v4M16 21v4",
    ],
  },
  {
    module: "trash",
    label: "回收站",
    paths: [
      "M10 12h14",
      "M13 12V9h8v3",
      "M12 15l1 11h8l1-11",
      "M16 17v6M19 17v6",
    ],
  },
];

const visibleProjects = computed(() => {
  const keyword = props.workspaceSearch.trim().toLowerCase();
  if (!keyword) return props.projects;
  return props.projects.filter((project) =>
    [project.title, project.genre, project.world_brief, project.writing_rules].join(" ").toLowerCase().includes(keyword),
  );
});

const selectedProject = computed(() => props.activeProject?.project ?? null);
const workspaceTitle = computed(() => {
  if (props.currentView === "projectCreate") return "新建项目";
  if (activeModule.value === "projects") return "我的项目";
  if (activeModule.value === "trash") return "回收站";
  return selectedProject.value?.title || "选择一个项目";
});
const characterCards = computed(() => props.activeProject?.character_cards ?? []);
const chapterCount = computed(() => props.activeProject?.project_chapters.length ?? 0);
const scriptCount = computed(() => props.longformState.draft_versions.length);
const storyboardCount = computed(() => props.longformState.storyboards.length);
const mediaAssets = computed(() => props.longformState.media_assets);
const videoTaskCount = computed(() => props.longformState.video_tasks.length);

const productionTracks = computed(() => {
  return props.longformState.storyboards.slice(0, 6).map((storyboard, index) => ({
    storyboard,
    tasks: videoTasksByStoryboard(storyboard.id),
    title: storyboard.title || `Storyboard ${index + 1}`,
    meta: `${storyboard.shots.length} 镜头 · ${storyboard.status || "待生产"}`,
    detail: storyboard.summary || "分镜已进入生产画布，可继续补首帧、配音和视频任务。",
  }));
});

function videoTasksByStoryboard(storyboardId: number) {
  return props.longformState.video_tasks.filter((task) => task.storyboard_id === storyboardId);
}

function hasActiveVideoTask(tasks: VideoTask[]) {
  return tasks.some((task) => ["queued", "running"].includes(task.task_status));
}

function productionTaskLabel(task: VideoTask) {
  const status = task.task_status || "pending";
  const output = task.output_uri ? " · 有输出" : "";
  return `${status}${output}`;
}

function fallbackProductionTracks() {
  return [
    {
      title: "Track 1 · 文本拆镜",
      meta: "等待剧本",
      detail: "生成或导入剧本后，这里会形成可拖拽的镜头轨道。",
    },
    {
      title: "Track 2 · 角色资产",
      meta: `${characterCards.value.length} 人物`,
      detail: "人物三视图、服装、表情和声音会挂到镜头节点上。",
    },
  ];
}

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

watch(
  () => props.currentView,
  (view) => {
    if (view === "trash") activeModule.value = "trash";
    else if (view === "assetLibrary") activeModule.value = "assets";
    else if (view === "projectCreate") activeModule.value = "projects";
  },
  { immediate: true },
);

watch(
  selectedProject,
  (project) => {
    settingsDraft.title = project?.title ?? "";
    settingsDraft.genre = project?.genre ?? "";
    settingsDraft.world_brief = project?.world_brief ?? "";
    settingsDraft.writing_rules = project?.writing_rules ?? "";
  },
  { immediate: true },
);

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
  if (!payload) return;
  emit("save-project-settings", payload);
}

function formatDateTime(value: string | undefined) {
  if (!value) return "未记录";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "未记录";
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatProjectCode(value: number) {
  return `P${String(value).padStart(6, "0")}`;
}

function assetKindLabel(value: string) {
  const lower = value.toLowerCase();
  if (lower.includes("video")) return "视频";
  if (lower.includes("voice") || lower.includes("audio")) return "音频";
  if (lower.includes("turnaround")) return "三视图";
  if (lower.includes("frame")) return "首帧";
  return "素材";
}

function assetCandidateLabel(asset: { meta: Record<string, unknown> }) {
  const version = asset.meta?.candidate_version || asset.meta?.version;
  const status = asset.meta?.candidate_status || (asset.meta?.locked ? "locked" : "");
  if (version) return `候选 v${version}${status === "locked" ? " · 已采用" : ""}`;
  if (status === "locked") return "已采用";
  return "候选资产";
}

function assetIsLocked(asset: MediaAsset) {
  return asset.meta?.locked === true || asset.meta?.candidate_status === "locked";
}

function assetLockMeta(locked: boolean) {
  return {
    locked,
    candidate_status: locked ? "locked" : "candidate",
  };
}

function itemCode(item: TrashItem) {
  if (item.item_type === "media_asset") return `M${String(item.item_id).padStart(6, "0")}`;
  if (item.item_type === "project") return formatProjectCode(item.item_id);
  return "";
}
</script>

<template>
  <div class="toon-shell">
    <aside class="toon-rail" aria-label="ToonFlow style navigation">
      <div class="toon-rail__brand" aria-label="ChenFlow">CF</div>
      <button
        v-for="item in railItems.slice(0, 4)"
        :key="item.module"
        type="button"
        :class="{ active: activeModule === item.module }"
        :aria-current="activeModule === item.module ? 'page' : undefined"
        :aria-label="item.label"
        :title="item.label"
        @click="selectModule(item.module)"
      >
        <svg aria-hidden="true" viewBox="0 0 32 32">
          <path v-for="path in item.paths" :key="path" :d="path" />
        </svg>
      </button>
      <span></span>
      <button
        v-for="item in railItems.slice(4)"
        :key="item.module"
        type="button"
        :class="{ active: activeModule === item.module }"
        :aria-current="activeModule === item.module ? 'page' : undefined"
        :aria-label="item.label"
        :title="item.label"
        @click="selectModule(item.module)"
      >
        <svg aria-hidden="true" viewBox="0 0 32 32">
          <path v-for="path in item.paths" :key="path" :d="path" />
        </svg>
      </button>
    </aside>

    <main class="toon-stage">
      <header class="toon-topbar">
        <div>
          <p>ChenFlow</p>
          <h1>{{ workspaceTitle }}</h1>
        </div>
        <nav aria-label="Project modules">
          <button type="button" :class="{ active: activeModule === 'script' }" :aria-current="activeModule === 'script' ? 'page' : undefined" @click="selectModule('script')">编剧</button>
          <button type="button" :class="{ active: activeModule === 'assets' }" :aria-current="activeModule === 'assets' ? 'page' : undefined" @click="selectModule('assets')">资产</button>
          <button type="button" :class="{ active: activeModule === 'production' }" :aria-current="activeModule === 'production' ? 'page' : undefined" @click="selectModule('production')">出片</button>
          <button type="button" :class="{ active: activeModule === 'projects' }" :aria-current="activeModule === 'projects' ? 'page' : undefined" @click="selectModule('projects')">项目</button>
        </nav>
        <div class="toon-user">
          <template v-if="isAuthenticated">
            <span>{{ username || "已登录" }}</span>
            <button type="button" @click="emit('logout')">退出</button>
          </template>
          <template v-else>
            <button type="button" @click="emit('login')">登录</button>
            <button type="button" class="toon-button toon-button--dark" @click="emit('register')">创建账号</button>
          </template>
        </div>
      </header>

      <section v-if="!isAuthenticated" class="toon-card toon-card--empty">
        <h2>登录后开始项目制创作</h2>
        <p>界面按 Toonflow 的项目工作台组织：先建项目，再在编剧、资产和出片之间切换。</p>
        <div class="toon-actions">
          <button type="button" class="toon-button toon-button--dark" @click="emit('register')">创建账号</button>
          <button type="button" class="toon-button" @click="emit('login')">登录</button>
        </div>
      </section>

      <section v-else-if="currentView === 'projectCreate'" class="toon-create toon-card">
        <div class="toon-create__head">
          <p>New Project</p>
          <h2>新建项目</h2>
          <span>只保留项目必要信息。后续剧本、资产和视频都在同一个工作台里推进。</span>
        </div>
        <form class="toon-create__form" @submit.prevent="emit('submit-create')">
          <label>
            <span>项目标题</span>
            <input :value="form.title" maxlength="120" autocomplete="off" placeholder="例如：贪官之女，败家千金" @input="emit('update:title', ($event.target as HTMLInputElement).value)" />
          </label>
          <label>
            <span>题材 / 风格</span>
            <input :value="form.genre" maxlength="80" autocomplete="off" placeholder="短剧 / 漫剧 / 青春奇幻 / 都市" @input="emit('update:genre', ($event.target as HTMLInputElement).value)" />
          </label>
          <label>
            <span>原著或故事资料</span>
            <textarea :value="form.world_brief" rows="8" placeholder="粘贴原著梗概、角色关系、世界观或你想改编的剧情方向。" @input="emit('update:world-brief', ($event.target as HTMLTextAreaElement).value)" />
          </label>
          <label>
            <span>改编要求</span>
            <textarea :value="form.writing_rules" rows="5" placeholder="例如：更强反转、更短场景、每集结尾留钩子、角色更贴近原创。" @input="emit('update:writing-rules', ($event.target as HTMLTextAreaElement).value)" />
          </label>
          <div class="toon-actions">
            <button type="submit" class="toon-button toon-button--dark" :disabled="loading">{{ loading ? "创建中..." : "创建项目" }}</button>
            <button class="toon-button" type="button" @click="emit('go', 'studio')">取消</button>
          </div>
        </form>
      </section>

      <section v-else-if="activeModule === 'projects'" class="toon-projects">
        <div class="toon-section-head">
          <div>
            <p>Projects</p>
            <h2>我的项目</h2>
          </div>
          <div class="toon-toolbar">
            <label class="toon-search">
              <span>搜索项目</span>
              <input :value="workspaceSearch" placeholder="搜索项目..." @input="emit('update:workspace-search', ($event.target as HTMLInputElement).value)" />
            </label>
            <button type="button" class="toon-button toon-button--dark" @click="emit('open-project-create', 'manual')">+ 新建项目</button>
          </div>
        </div>
        <div v-if="visibleProjects.length" class="toon-project-grid">
          <article v-for="project in visibleProjects" :key="project.id" class="toon-project-card" tabindex="0" role="button" :aria-label="`打开项目：${project.title}`" @click="openProject(project.id)" @keydown.enter.prevent="openProject(project.id)" @keydown.space.prevent="openProject(project.id)">
            <div>
              <strong>{{ project.title }}</strong>
              <span>{{ project.genre || "未设置风格" }}</span>
            </div>
            <p>{{ project.world_brief || project.writing_rules || "打开项目后继续导入原著、生成剧本、整理资产和出片。" }}</p>
            <footer>
              <span>{{ formatProjectCode(project.id) }}</span>
              <span>{{ formatDateTime(project.updated_at) }}</span>
              <button type="button" @click.stop="emit('delete-project', project.id)">删除</button>
            </footer>
          </article>
        </div>
        <div v-else class="toon-card toon-card--empty">
          <h2>还没有项目</h2>
          <p>点击“新建项目”，导入原著或一句话设定。后面的编剧、资产、分镜和视频不会再拆成互相独立的入口。</p>
        </div>
      </section>

      <section v-else-if="activeModule === 'trash'" class="toon-projects">
        <div class="toon-section-head">
          <div>
            <p>Trash</p>
            <h2>回收站</h2>
          </div>
          <div class="toon-status-row">
            <span>项目 {{ trashSummary.project }}</span>
            <span>资产 {{ trashSummary.media_asset }}</span>
          </div>
        </div>
        <div v-if="trashItems.length" class="toon-project-grid">
          <article v-for="item in trashItems" :key="`${item.item_type}-${item.item_id}`" class="toon-project-card">
            <strong>{{ [itemCode(item), item.title].filter(Boolean).join(" · ") }}</strong>
            <p>{{ item.subtitle || item.item_type }}</p>
            <footer>
              <span>{{ formatDateTime(item.deleted_at) }}</span>
              <button type="button" @click="emit('restore-trash', item)">恢复</button>
            </footer>
          </article>
        </div>
        <div v-else class="toon-card toon-card--empty">回收站目前是空的。</div>
      </section>

      <section v-else class="toon-workbench">
        <aside class="toon-inspector toon-card">
          <div v-if="projects.length" class="toon-select">
            <label>当前项目</label>
            <select :value="selectedProject?.id || ''" @change="openProject(Number(($event.target as HTMLSelectElement).value))">
              <option value="" disabled>选择项目</option>
              <option v-for="project in projects" :key="project.id" :value="project.id">{{ project.title }}</option>
            </select>
          </div>
          <div class="toon-batch">
            <strong>批量生产设置</strong>
            <p>批量选择、资产提取和生产队列需要接入后端任务后再开放，当前只展示项目状态。</p>
            <div class="toon-next-actions" aria-label="待接入能力">
              <span>全选</span>
              <span>提取资产</span>
              <span>生成提示词</span>
              <span>开始生产</span>
            </div>
          </div>
          <div class="toon-status-row">
            <span>人物 {{ characterCards.length }}</span>
            <span>章节 {{ chapterCount }}</span>
            <span>草稿 {{ scriptCount }}</span>
            <span>资产 {{ mediaAssets.length }}</span>
          </div>
        </aside>

        <div class="toon-canvas" :class="`toon-canvas--${activeModule}`" :aria-label="`${moduleLabels[activeModule]}画布`">
          <article v-if="!selectedProject && activeModule !== 'settings'" class="toon-node toon-node--empty">
            <h3>先打开一个项目</h3>
            <span>从左侧或顶部切回“项目”，选择项目后再进入编剧、资产和出片画布。</span>
          </article>

          <template v-else-if="activeModule === 'script'">
            <article class="toon-node toon-node--document">
              <p>故事骨架</p>
              <h3>{{ selectedProject?.title || "未选择项目" }}</h3>
              <span>{{ selectedProject?.world_brief || "导入原著后，事件图谱和改编策略会在这里展开。" }}</span>
            </article>
            <article class="toon-node toon-node--table">
              <p>改编策略</p>
              <h3>ScriptAgent</h3>
              <span>{{ selectedProject?.writing_rules || "生成剧本前先写清节奏、删改边界和角色保留策略。" }}</span>
            </article>
            <article class="toon-node toon-node--table">
              <p>剧本</p>
              <h3>{{ scriptCount }} 个草稿</h3>
              <span>正文、分集脚本和可出片文本会在这里沉淀。</span>
            </article>
          </template>

          <template v-else-if="activeModule === 'assets'">
            <article v-for="asset in mediaAssets.slice(0, 12)" :key="asset.id" class="toon-asset-card">
              <div class="toon-asset-card__preview">
                <img v-if="/^https?:|^data:|\\.(png|jpg|jpeg|webp|gif)$/i.test(asset.uri)" :src="asset.uri" :alt="`${assetKindLabel(asset.asset_type)}素材预览`" loading="lazy" decoding="async" />
                <span v-else>{{ assetKindLabel(asset.asset_type) }}</span>
              </div>
              <strong>{{ assetKindLabel(asset.asset_type) }} {{ asset.id }}</strong>
              <span class="toon-asset-card__candidate">{{ assetCandidateLabel(asset) }}</span>
              <p>{{ asset.prompt || asset.status || "素材已归档到项目。" }}</p>
              <div class="toon-asset-card__actions" aria-label="候选资产状态">
                <button v-if="!assetIsLocked(asset)" type="button" :disabled="loading" @click="emit('update-media-asset', asset.id, assetLockMeta(true))">设为采用</button>
                <button v-else type="button" :disabled="loading" @click="emit('update-media-asset', asset.id, assetLockMeta(false))">取消采用</button>
                <button type="button" :disabled="loading" @click="emit('delete-media-asset', asset.id)">删除候选</button>
              </div>
            </article>
            <article v-if="!mediaAssets.length" class="toon-node toon-node--empty">
              <h3>等待生成资产</h3>
              <span>角色三视图、场景图、首帧和音频会以卡片形式铺在这里。</span>
            </article>
          </template>

          <template v-else-if="activeModule === 'production'">
            <article v-for="track in productionTracks" :key="track.title" class="toon-track">
              <p>{{ track.meta }}</p>
              <h3>{{ track.title }}</h3>
              <span>{{ track.detail }}</span>
              <footer>
                <button type="button" :disabled="loading || hasActiveVideoTask(track.tasks)" @click="emit('create-video-task', track.storyboard.id)">
                  {{ hasActiveVideoTask(track.tasks) ? "生产中" : "创建视频任务" }}
                </button>
              </footer>
              <div v-if="track.tasks.length" class="toon-track__tasks" aria-label="视频任务">
                <article v-for="task in track.tasks" :key="task.id">
                  <strong>生产任务 {{ task.id }}</strong>
                  <span>{{ productionTaskLabel(task) }}</span>
                  <a v-if="task.output_uri" :href="task.output_uri" target="_blank" rel="noreferrer">查看输出</a>
                  <button type="button" :disabled="loading || task.task_status === 'running'" @click="emit('delete-video-task', task.id)">删除任务</button>
                </article>
              </div>
            </article>
            <article v-for="track in fallbackProductionTracks()" v-if="!productionTracks.length" :key="track.title" class="toon-track">
              <p>{{ track.meta }}</p>
              <h3>{{ track.title }}</h3>
              <span>{{ track.detail }}</span>
            </article>
          </template>

          <template v-else-if="activeModule === 'settings'">
            <article v-if="!selectedProject" class="toon-node toon-node--empty">
              <h3>先打开一个项目</h3>
              <span>选择项目后才能保存项目级设定。</span>
            </article>
            <form v-else class="toon-settings toon-node toon-node--document" @submit.prevent="saveProjectSettings()">
              <p>项目设置</p>
              <h3>{{ selectedProject.title }}</h3>
              <label>
                <span>项目标题</span>
                <input v-model="settingsDraft.title" maxlength="120" autocomplete="off" />
              </label>
              <label>
                <span>题材 / 风格</span>
                <input v-model="settingsDraft.genre" maxlength="80" autocomplete="off" />
              </label>
              <label>
                <span>故事资料</span>
                <textarea v-model="settingsDraft.world_brief" rows="6" />
              </label>
              <label>
                <span>改编要求</span>
                <textarea v-model="settingsDraft.writing_rules" rows="5" />
              </label>
              <footer>
                <button type="submit" :disabled="loading">{{ loading ? "保存中..." : "保存设置" }}</button>
              </footer>
            </form>
          </template>
        </div>

        <aside class="toon-agent toon-card">
          <strong><span></span>{{ selectedProject?.title || "项目 Agent" }}</strong>
          <ul>
            <li>策划：从原著或简报建立事件图谱。</li>
            <li>编剧：生成故事骨架、改编策略和剧本。</li>
            <li>资产：提取角色、场景、道具并生成图像。</li>
            <li>出片：组织分镜、首帧、配音和视频任务。</li>
          </ul>
          <div class="toon-agent__status" aria-label="项目状态摘要">
            <span>章节 {{ chapterCount }}</span>
            <span>分镜 {{ storyboardCount }}</span>
            <span>视频任务 {{ videoTaskCount }}</span>
          </div>
        </aside>
      </section>
    </main>
  </div>
</template>

<style scoped>
.toon-shell {
  min-height: calc(100vh - 44px);
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr);
  gap: 16px;
  --toon-ink: color-mix(in oklab, var(--ink) 92%, oklch(20% 0.026 18));
  --toon-ink-muted: color-mix(in oklab, var(--ink-soft) 88%, var(--rose-strong));
  --toon-line: rgba(20, 16, 20, 0.1);
  --toon-surface: rgba(255, 255, 255, 0.64);
}

.toon-rail,
.toon-stage,
.toon-card {
  border: 1px solid rgba(255, 255, 255, 0.82);
  background: rgba(255, 255, 255, 0.62);
  box-shadow: 0 22px 52px rgba(240, 111, 155, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.toon-rail {
  position: sticky;
  top: 22px;
  min-height: calc(100vh - 44px);
  display: grid;
  grid-template-rows: auto repeat(4, 48px) 1fr repeat(2, 48px);
  gap: 10px;
  padding: 14px;
  border-radius: 24px;
}

.toon-rail__brand,
.toon-rail button {
  display: grid;
  place-items: center;
  border-radius: 16px;
  font-weight: 800;
}

.toon-rail__brand {
  height: 48px;
  color: white;
  background: linear-gradient(135deg, color-mix(in oklab, var(--rose-strong) 86%, white), color-mix(in oklab, var(--rose) 68%, white));
}

.toon-rail button {
  border: 0;
  background: transparent;
  color: color-mix(in oklab, var(--rose-strong) 42%, var(--ink));
  transition: background-color 160ms ease, color 160ms ease, transform 160ms ease;
}

.toon-rail svg {
  width: 23px;
  height: 23px;
  overflow: visible;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.toon-rail button.active,
.toon-topbar nav button.active {
  color: white;
  background: color-mix(in oklab, var(--toon-ink) 92%, var(--rose-strong));
}

.toon-rail button:hover,
.toon-topbar nav button:hover,
.toon-user button:hover,
.toon-button:hover,
.toon-project-card footer button:hover,
.toon-asset-card__actions button:hover,
.toon-track button:hover,
.toon-settings button:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.86);
}

.toon-rail button.active:hover,
.toon-topbar nav button.active:hover {
  background: color-mix(in oklab, var(--toon-ink) 92%, var(--rose-strong));
}

.toon-rail button:focus-visible,
.toon-topbar nav button:focus-visible,
.toon-user button:focus-visible,
.toon-button:focus-visible,
.toon-project-card:focus-visible,
.toon-project-card footer button:focus-visible,
.toon-asset-card__actions button:focus-visible,
.toon-track button:focus-visible,
.toon-settings button:focus-visible,
.toon-create input:focus-visible,
.toon-create textarea:focus-visible,
.toon-settings input:focus-visible,
.toon-settings textarea:focus-visible,
.toon-select select:focus-visible,
.toon-toolbar input:focus-visible {
  outline: 3px solid color-mix(in oklab, var(--rose-strong) 28%, white);
  outline-offset: 3px;
}

.toon-stage {
  min-width: 0;
  min-height: calc(100vh - 44px);
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 18px;
  padding: 28px;
  border-radius: 28px;
}

.toon-topbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 18px;
  align-items: center;
}

.toon-topbar p,
.toon-section-head p,
.toon-create__head p {
  margin: 0 0 4px;
  color: var(--ink-soft);
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.toon-topbar h1,
.toon-section-head h2,
.toon-create__head h2 {
  margin: 0;
  color: #181216;
  font-family: var(--font-body);
  font-size: clamp(1.5rem, 2.4vw, 2.2rem);
  font-weight: 850;
  letter-spacing: -0.04em;
}

.toon-topbar nav,
.toon-user,
.toon-actions,
.toon-toolbar,
.toon-status-row {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.toon-topbar nav button,
.toon-button,
.toon-user button,
.toon-project-card footer button,
.toon-asset-card__actions button,
.toon-track button,
.toon-settings button,
.toon-batch button {
  min-height: 42px;
  border: 1px solid rgba(20, 16, 20, 0.1);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.64);
  color: #191318;
  padding: 0 14px;
  font-weight: 700;
  transition: background-color 160ms ease, border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}

.toon-button--dark,
.toon-batch .toon-button--dark {
  color: white;
  background: color-mix(in oklab, var(--toon-ink) 92%, var(--rose-strong));
}

.toon-button:disabled {
  cursor: wait;
  opacity: 0.62;
  transform: none;
}

.toon-projects,
.toon-create {
  display: grid;
  gap: 18px;
  align-content: start;
}

.toon-section-head {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: end;
}

.toon-search {
  display: grid;
  gap: 6px;
}

.toon-search span {
  font-size: 0.78rem;
  color: var(--ink-soft);
}

.toon-toolbar input {
  width: min(360px, 42vw);
  min-height: 42px;
  border: 1px solid rgba(20, 16, 20, 0.1);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.72);
  padding: 0 12px;
}

.toon-project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px;
}

.toon-project-card {
  min-height: 180px;
  display: grid;
  gap: 16px;
  align-content: start;
  padding: 20px;
  border: 1px solid rgba(20, 16, 20, 0.1);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.58);
  cursor: pointer;
  transition: background-color 160ms ease, border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}

.toon-project-card:hover,
.toon-project-card:focus-visible {
  border-color: color-mix(in oklab, var(--rose-strong) 22%, white);
  background: rgba(255, 255, 255, 0.76);
  box-shadow: 0 18px 42px rgba(240, 111, 155, 0.12);
  transform: translateY(-2px);
}

.toon-project-card strong,
.toon-project-card span,
.toon-project-card p {
  display: block;
}

.toon-project-card strong {
  color: #181216;
  font-size: 1.12rem;
}

.toon-project-card span,
.toon-project-card p,
.toon-create__head span {
  color: var(--ink-soft);
  line-height: 1.55;
}

.toon-project-card p {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.toon-project-card footer {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
}

.toon-card {
  border-radius: 16px;
  padding: 20px;
}

.toon-card--empty {
  min-height: 260px;
  align-content: center;
}

.toon-create {
  grid-template-columns: minmax(220px, 0.5fr) minmax(0, 1fr);
  padding: clamp(24px, 4vw, 48px);
}

.toon-create__form {
  display: grid;
  gap: 14px;
}

.toon-create label,
.toon-select {
  display: grid;
  gap: 8px;
}

.toon-create input,
.toon-create textarea,
.toon-settings input,
.toon-settings textarea,
.toon-select select {
  width: 100%;
  border: 1px solid rgba(20, 16, 20, 0.1);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.72);
  padding: 12px;
  color: var(--toon-ink);
}

.toon-create textarea {
  resize: vertical;
  line-height: 1.65;
}

.toon-settings {
  width: min(720px, 100%);
}

.toon-settings label {
  display: grid;
  gap: 8px;
}

.toon-settings textarea {
  resize: vertical;
  line-height: 1.65;
}

.toon-settings footer {
  display: flex;
  justify-content: flex-start;
}

.toon-settings button:disabled {
  cursor: wait;
  opacity: 0.58;
  transform: none;
}

.toon-workbench {
  min-height: 0;
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr) 360px;
  gap: 14px;
}

.toon-inspector,
.toon-agent {
  align-content: start;
  display: grid;
  gap: 18px;
}

.toon-batch {
  display: grid;
  gap: 10px;
}

.toon-batch p {
  margin: 0;
  color: var(--ink-soft);
  font-size: 0.9rem;
  line-height: 1.6;
}

.toon-next-actions {
  display: grid;
  gap: 8px;
}

.toon-next-actions span {
  min-height: 38px;
  display: grid;
  align-items: center;
  border: 1px dashed rgba(20, 16, 20, 0.12);
  border-radius: 10px;
  padding: 0 12px;
  color: color-mix(in oklab, var(--ink-soft) 78%, white);
  background: rgba(255, 255, 255, 0.42);
}

.toon-status-row span {
  padding: 0.28rem 0.56rem;
  border-radius: 999px;
  background: rgba(255, 239, 246, 0.74);
  color: color-mix(in oklab, var(--rose-strong) 52%, var(--ink));
  font-size: 0.8rem;
}

.toon-canvas {
  position: relative;
  min-height: 680px;
  overflow: auto;
  border-radius: 16px;
  border: 1px solid rgba(20, 16, 20, 0.08);
  background:
    radial-gradient(circle, rgba(20, 16, 20, 0.12) 1px, transparent 1px) 0 0 / 22px 22px,
    rgba(255, 255, 255, 0.36);
  padding: 34px;
  contain: layout paint;
}

.toon-node,
.toon-track,
.toon-asset-card {
  border: 1px solid rgba(20, 16, 20, 0.11);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 14px 30px rgba(20, 16, 20, 0.06);
}

.toon-node {
  width: min(360px, 100%);
  min-height: 190px;
  display: grid;
  gap: 10px;
  align-content: start;
  margin-bottom: 28px;
  padding: 18px;
}

.toon-node:nth-child(2) {
  margin-left: min(260px, 28%);
}

.toon-node:nth-child(3) {
  margin-left: min(120px, 14%);
}

.toon-node p,
.toon-track p {
  margin: 0;
  color: var(--ink-soft);
}

.toon-node h3,
.toon-track h3 {
  margin: 0;
  color: #181216;
}

.toon-node span,
.toon-track span,
.toon-agent li {
  color: var(--ink-soft);
  line-height: 1.62;
}

.toon-canvas--assets {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  align-content: start;
  gap: 14px;
}

.toon-asset-card {
  display: grid;
  gap: 10px;
  padding: 12px;
  content-visibility: auto;
  contain-intrinsic-size: 250px;
}

.toon-asset-card__preview {
  aspect-ratio: 16 / 10;
  display: grid;
  place-items: center;
  overflow: hidden;
  border-radius: 10px;
  background: rgba(246, 240, 244, 0.9);
  color: var(--ink-soft);
}

.toon-asset-card__preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.toon-asset-card p {
  display: -webkit-box;
  min-height: 3.1em;
  margin: 0;
  overflow: hidden;
  color: var(--ink-soft);
  font-size: 0.84rem;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.toon-asset-card__candidate {
  color: color-mix(in oklab, var(--rose-strong) 52%, var(--ink));
  font-size: 0.8rem;
  font-weight: 700;
}

.toon-asset-card__actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.toon-asset-card__actions button {
  min-height: 34px;
  display: inline-grid;
  align-items: center;
  border: 1px solid rgba(20, 16, 20, 0.1);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.66);
  color: color-mix(in oklab, var(--ink-soft) 82%, white);
  padding: 0 10px;
  font-size: 0.76rem;
}

.toon-asset-card__actions button:disabled {
  cursor: wait;
  opacity: 0.58;
  transform: none;
}

.toon-canvas--production {
  display: grid;
  align-content: start;
  gap: 16px;
}

.toon-track {
  min-height: 130px;
  display: grid;
  gap: 12px;
  padding: 18px;
}

.toon-track footer {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.toon-track button:disabled {
  cursor: wait;
  opacity: 0.58;
  transform: none;
}

.toon-track__tasks {
  display: grid;
  gap: 8px;
}

.toon-track__tasks article {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 8px;
  align-items: center;
  border: 1px solid rgba(20, 16, 20, 0.08);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.54);
  padding: 10px;
}

.toon-track__tasks a {
  color: color-mix(in oklab, var(--rose-strong) 58%, var(--ink));
  font-weight: 700;
  text-decoration: none;
}

.toon-agent strong {
  display: flex;
  gap: 8px;
  align-items: center;
}

.toon-agent strong span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #1ec25b;
}

.toon-agent ul {
  display: grid;
  gap: 12px;
  margin: 0;
  padding-left: 20px;
}

.toon-agent__status {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: auto;
  border: 1px solid rgba(20, 16, 20, 0.1);
  border-radius: 14px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.62);
}

.toon-agent__status span {
  border-radius: 999px;
  background: rgba(255, 239, 246, 0.72);
  color: color-mix(in oklab, var(--rose-strong) 52%, var(--ink));
  padding: 0.28rem 0.56rem;
  font-size: 0.8rem;
  font-weight: 700;
}

@media (max-width: 1180px) {
  .toon-workbench {
    grid-template-columns: 280px minmax(0, 1fr);
  }

  .toon-agent {
    grid-column: 1 / -1;
  }
}

@media (max-width: 820px) {
  .toon-shell {
    grid-template-columns: minmax(0, 1fr);
  }

  .toon-rail {
    position: static;
    min-height: auto;
    grid-template-columns: repeat(7, minmax(0, 1fr));
    grid-template-rows: auto;
    padding: 10px;
    border-radius: 20px;
  }

  .toon-stage,
  .toon-topbar,
  .toon-create,
  .toon-workbench,
  .toon-section-head {
    grid-template-columns: minmax(0, 1fr);
  }

  .toon-toolbar input {
    width: 100%;
  }

  .toon-stage {
    padding: 18px;
  }

  .toon-canvas {
    min-height: 520px;
    padding: 20px;
  }

  .toon-project-card footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .toon-project-card footer button,
  .toon-asset-card__actions button,
  .toon-track button,
  .toon-settings button {
    width: 100%;
  }

  .toon-track__tasks article {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 560px) {
  .toon-rail {
    grid-template-columns: repeat(4, minmax(44px, 1fr));
  }

  .toon-rail span {
    display: none;
  }

  .toon-topbar nav,
  .toon-user,
  .toon-actions,
  .toon-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .toon-topbar nav button,
  .toon-user button,
  .toon-button {
    width: 100%;
  }
}
</style>
