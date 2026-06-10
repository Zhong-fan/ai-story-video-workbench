<script setup lang="ts">
import { computed, ref } from "vue";
import type { LongformState, Project, ProjectCreateDraft, ProjectDetailResponse, TrashItem } from "../../types";

type CreationMode = "upload" | "ai" | "manual";
type WorkbenchModule = "projects" | "script" | "assets" | "production" | "settings" | "trash";

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
  (e: "update:workspace-search", value: string): void;
  (e: "update:title", value: string): void;
  (e: "update:genre", value: string): void;
  (e: "update:world-brief", value: string): void;
  (e: "update:writing-rules", value: string): void;
  (e: "submit-create"): void;
}>();

const activeModule = ref<WorkbenchModule>("projects");

const visibleProjects = computed(() => {
  const keyword = props.workspaceSearch.trim().toLowerCase();
  if (!keyword) return props.projects;
  return props.projects.filter((project) =>
    [project.title, project.genre, project.world_brief, project.writing_rules].join(" ").toLowerCase().includes(keyword),
  );
});

const selectedProject = computed(() => props.activeProject?.project ?? props.projects[0] ?? null);
const characterCards = computed(() => props.activeProject?.character_cards ?? []);
const chapterCount = computed(() => props.activeProject?.project_chapters.length ?? 0);
const scriptCount = computed(() => props.longformState.draft_versions.length);
const storyboardCount = computed(() => props.longformState.storyboards.length);
const mediaAssets = computed(() => props.longformState.media_assets);
const videoTaskCount = computed(() => props.longformState.video_tasks.length);

const productionTracks = computed(() => {
  const storyboards = props.longformState.storyboards.slice(0, 3);
  if (storyboards.length) {
    return storyboards.map((storyboard, index) => ({
      title: storyboard.title || `Storyboard ${index + 1}`,
      meta: `${storyboard.shots.length} 镜头 · ${storyboard.status || "待生产"}`,
      detail: storyboard.summary || "分镜已进入生产画布，可继续补首帧、配音和视频任务。",
    }));
  }
  return [
    { title: "Track 1 · 文本拆镜", meta: "等待剧本", detail: "生成或导入剧本后，这里会形成可拖拽的镜头轨道。" },
    { title: "Track 2 · 角色资产", meta: `${characterCards.value.length} 人物`, detail: "人物三视图、服装、表情和声音会挂到镜头节点上。" },
    { title: "Track 3 · 视频出片", meta: `${videoTaskCount.value} 任务`, detail: "首帧、旁白和视频任务会在同一张生产画布里串起来。" },
  ];
});

function selectModule(module: WorkbenchModule) {
  activeModule.value = module;
  if (module === "trash") emit("go", "trash");
  else if (module === "assets") emit("go", "assetLibrary");
  else emit("go", "studio");
}

function openProject(projectId: number) {
  activeModule.value = "script";
  emit("open-project", projectId);
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

function itemCode(item: TrashItem) {
  if (item.item_type === "media_asset") return `M${String(item.item_id).padStart(6, "0")}`;
  if (item.item_type === "project") return formatProjectCode(item.item_id);
  return "";
}
</script>

<template>
  <div class="toon-shell">
    <aside class="toon-rail" aria-label="ToonFlow style navigation">
      <div class="toon-rail__brand">CF</div>
      <button :class="{ active: activeModule === 'projects' }" title="项目" @click="selectModule('projects')">□</button>
      <button :class="{ active: activeModule === 'script' }" title="编剧" @click="selectModule('script')">文</button>
      <button :class="{ active: activeModule === 'assets' }" title="资产" @click="selectModule('assets')">图</button>
      <button :class="{ active: activeModule === 'production' }" title="出片" @click="selectModule('production')">▶</button>
      <span></span>
      <button :class="{ active: activeModule === 'settings' }" title="设置" @click="selectModule('settings')">⚙</button>
      <button :class="{ active: activeModule === 'trash' }" title="回收站" @click="selectModule('trash')">⌫</button>
    </aside>

    <main class="toon-stage">
      <header class="toon-topbar">
        <div>
          <p>ChenFlow</p>
          <h1>{{ selectedProject?.title || "我的项目" }}</h1>
        </div>
        <nav aria-label="Project modules">
          <button :class="{ active: activeModule === 'script' }" @click="selectModule('script')">编剧</button>
          <button :class="{ active: activeModule === 'assets' }" @click="selectModule('assets')">资产</button>
          <button :class="{ active: activeModule === 'production' }" @click="selectModule('production')">出片</button>
          <button :class="{ active: activeModule === 'projects' }" @click="selectModule('projects')">项目</button>
        </nav>
        <div class="toon-user">
          <template v-if="isAuthenticated">
            <span>{{ username || "已登录" }}</span>
            <button @click="emit('logout')">退出</button>
          </template>
          <template v-else>
            <button @click="emit('login')">登录</button>
            <button class="toon-button toon-button--dark" @click="emit('register')">创建账号</button>
          </template>
        </div>
      </header>

      <section v-if="!isAuthenticated" class="toon-card toon-card--empty">
        <h2>登录后开始项目制创作</h2>
        <p>界面按 Toonflow 的项目工作台组织：先建项目，再在编剧、资产和出片之间切换。</p>
        <div class="toon-actions">
          <button class="toon-button toon-button--dark" @click="emit('register')">创建账号</button>
          <button class="toon-button" @click="emit('login')">登录</button>
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
            <input :value="form.title" maxlength="120" placeholder="例如：贪官之女，败家千金" @input="emit('update:title', ($event.target as HTMLInputElement).value)" />
          </label>
          <label>
            <span>题材 / 风格</span>
            <input :value="form.genre" maxlength="80" placeholder="短剧 / 漫剧 / 青春奇幻 / 都市" @input="emit('update:genre', ($event.target as HTMLInputElement).value)" />
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
            <button class="toon-button toon-button--dark" :disabled="loading">创建项目</button>
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
            <input :value="workspaceSearch" placeholder="搜索项目..." @input="emit('update:workspace-search', ($event.target as HTMLInputElement).value)" />
            <button class="toon-button toon-button--dark" @click="emit('open-project-create', 'manual')">+ 新建项目</button>
          </div>
        </div>
        <div v-if="visibleProjects.length" class="toon-project-grid">
          <article v-for="project in visibleProjects" :key="project.id" class="toon-project-card" @click="openProject(project.id)">
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
          <div class="toon-select">
            <label>当前项目</label>
            <select :value="selectedProject?.id || ''" @change="openProject(Number(($event.target as HTMLSelectElement).value))">
              <option v-for="project in projects" :key="project.id" :value="project.id">{{ project.title }}</option>
            </select>
          </div>
          <div class="toon-batch">
            <strong>批量生产设置</strong>
            <button>全选</button>
            <button>提取资产</button>
            <button>生成提示词</button>
            <button class="toon-button--dark">开始生产</button>
          </div>
          <div class="toon-status-row">
            <span>人物 {{ characterCards.length }}</span>
            <span>章节 {{ chapterCount }}</span>
            <span>草稿 {{ scriptCount }}</span>
            <span>资产 {{ mediaAssets.length }}</span>
          </div>
        </aside>

        <div class="toon-canvas" :class="`toon-canvas--${activeModule}`">
          <template v-if="activeModule === 'script'">
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
                <img v-if="/^https?:|^data:|\\.(png|jpg|jpeg|webp|gif)$/i.test(asset.uri)" :src="asset.uri" alt="" />
                <span v-else>{{ assetKindLabel(asset.asset_type) }}</span>
              </div>
              <strong>{{ assetKindLabel(asset.asset_type) }} {{ asset.id }}</strong>
              <span class="toon-asset-card__candidate">{{ assetCandidateLabel(asset) }}</span>
              <p>{{ asset.prompt || asset.status || "素材已归档到项目。" }}</p>
              <div class="toon-asset-card__actions">
                <button type="button">设为采用</button>
                <button type="button">取消采用</button>
                <button type="button">删除候选</button>
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
            </article>
          </template>

          <template v-else>
            <article class="toon-node toon-node--document">
              <p>项目设置</p>
              <h3>{{ selectedProject?.title || "未选择项目" }}</h3>
              <span>这里保留项目级信息。更细的旧表单不会再作为主界面出现。</span>
            </article>
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
          <div class="toon-agent__input">输入生产指令...</div>
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
  background: linear-gradient(135deg, rgba(240, 111, 155, 0.92), rgba(248, 182, 200, 0.88));
}

.toon-rail button {
  border: 0;
  background: transparent;
  color: color-mix(in oklab, var(--rose-strong) 42%, var(--ink));
}

.toon-rail button.active,
.toon-topbar nav button.active {
  color: white;
  background: #141014;
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
.toon-batch button {
  min-height: 38px;
  border: 1px solid rgba(20, 16, 20, 0.1);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.64);
  color: #191318;
  padding: 0 14px;
  font-weight: 700;
}

.toon-button--dark,
.toon-batch .toon-button--dark {
  color: white;
  background: #141014;
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

.toon-toolbar input {
  width: min(360px, 42vw);
  min-height: 38px;
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
.toon-select select {
  width: 100%;
  border: 1px solid rgba(20, 16, 20, 0.1);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.72);
  padding: 12px;
}

.toon-create textarea {
  resize: vertical;
  line-height: 1.65;
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
  min-height: 28px;
  border: 1px solid rgba(20, 16, 20, 0.1);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.66);
  color: #191318;
  font-size: 0.76rem;
}

.toon-canvas--production {
  display: grid;
  align-content: start;
  gap: 16px;
}

.toon-track {
  min-height: 130px;
  padding: 18px;
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

.toon-agent__input {
  min-height: 86px;
  display: grid;
  align-items: end;
  margin-top: auto;
  border: 1px solid rgba(20, 16, 20, 0.1);
  border-radius: 14px;
  padding: 14px;
  color: color-mix(in oklab, var(--ink-soft) 74%, white);
  background: rgba(255, 255, 255, 0.62);
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
}
</style>
