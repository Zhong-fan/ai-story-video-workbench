<script setup lang="ts">
import { computed } from "vue";
import type { Project } from "../../types";

type CreationMode = "upload" | "ai" | "manual";

type PipelineStep = {
  title: string;
  description: string;
  meta: string;
};

const props = defineProps<{
  workspaceSearch: string;
  projects: Project[];
  workspacePage: number;
  workspacePageSize: number;
  workspaceTotalPages: number;
  loading: boolean;
}>();

const emit = defineEmits<{
  (e: "update:workspace-search", value: string): void;
  (e: "start-create", mode: CreationMode): void;
  (e: "open-project", projectId: number): void;
  (e: "delete-project", projectId: number): void;
  (e: "previous-page"): void;
  (e: "next-page"): void;
}>();

const pipelineSteps: PipelineStep[] = [
  {
    title: "项目",
    description: "导入小说、剧本或从一句话简报开始，先建立统一项目。",
    meta: "入口",
  },
  {
    title: "设定",
    description: "整理世界观、人物、参考边界和视觉规则，形成可复用资产底座。",
    meta: "资产前置",
  },
  {
    title: "小说 / 剧本",
    description: "生成大纲、章节正文或短剧文本，所有内容都回到同一个项目里。",
    meta: "文本生产",
  },
  {
    title: "分镜 / 视频",
    description: "把文本拆成镜头，补角色图、首帧、配音和视频任务。",
    meta: "制作",
  },
];

const projectCountText = computed(() => `${props.projects.length} 个当前页项目`);
const emptyText = computed(() => "还没有项目。先从一个项目开始，后续小说、资产和视频都会挂在这个项目下面。");

function formatUpdatedAt(value: string) {
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
</script>

<template>
  <div class="workspace-home workspace-home--pipeline">
    <section class="studio-hero panel panel--paper">
      <div class="studio-hero__copy">
        <p class="panel-heading__kicker">项目制创作台</p>
        <h2>从一个项目开始，往下推进到小说、资产和视频。</h2>
        <p>
          不再让你先选“视频 / 小说 / 动画资产”。这些不是三个互相独立的产品，
          而是同一条创作流水线里的不同阶段。
        </p>
      </div>
      <div class="studio-hero__actions">
        <button class="primary-button" type="button" :disabled="loading" @click="emit('start-create', 'manual')">新建项目</button>
        <button class="ghost-button" type="button" :disabled="loading" @click="emit('start-create', 'upload')">导入已有文本</button>
        <button class="ghost-button" type="button" :disabled="loading" @click="emit('start-create', 'ai')">用 AI 生成底稿</button>
      </div>
    </section>

    <section class="pipeline-strip panel" aria-label="制作流水线">
      <article v-for="(step, index) in pipelineSteps" :key="step.title" class="pipeline-card">
        <span class="pipeline-card__index">{{ index + 1 }}</span>
        <div>
          <p>{{ step.meta }}</p>
          <h3>{{ step.title }}</h3>
          <span>{{ step.description }}</span>
        </div>
      </article>
    </section>

    <section class="project-shelf panel">
      <div class="project-shelf__head">
        <div>
          <p class="panel-heading__kicker">我的项目</p>
          <h2>继续制作</h2>
          <p class="project-shelf__summary">{{ projectCountText }}</p>
        </div>
        <div class="project-shelf__tools">
          <label class="field project-shelf__search">
            <span>搜索</span>
            <input
              :value="workspaceSearch"
              maxlength="120"
              placeholder="搜索项目标题、题材、设定"
              @input="emit('update:workspace-search', ($event.target as HTMLInputElement).value)"
            />
          </label>
        </div>
      </div>

      <div class="project-card-grid" v-if="projects.length">
        <article v-for="(project, index) in projects" :key="project.id" class="project-home-card">
          <button class="project-home-card__main" type="button" @click="emit('open-project', project.id)">
            <div class="project-home-card__thumb" :class="`project-home-card__thumb--${(index % 4) + 1}`">
              <span>{{ project.title.slice(0, 1) }}</span>
            </div>
            <div class="project-home-card__body">
              <strong>{{ formatProjectCode(project.id) }} · {{ project.title }}</strong>
              <span>{{ project.genre || "未设置题材" }}</span>
              <em>修改于 {{ formatUpdatedAt(project.updated_at) }}</em>
            </div>
          </button>
          <button class="ghost-button ghost-button--small project-home-card__delete" type="button" :disabled="loading" @click="emit('delete-project', project.id)">删除</button>
        </article>
      </div>
      <p v-else class="empty-text">{{ emptyText }}</p>

      <div class="pagination">
        <button class="ghost-button ghost-button--small" type="button" :disabled="loading || workspacePage <= 1" @click="emit('previous-page')">
          上一页
        </button>
        <span>{{ workspacePage }} / {{ workspaceTotalPages }}</span>
        <button class="ghost-button ghost-button--small" type="button" :disabled="loading || workspacePage >= workspaceTotalPages" @click="emit('next-page')">
          下一页
        </button>
      </div>
    </section>
  </div>
</template>
