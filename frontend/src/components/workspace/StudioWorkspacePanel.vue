<script setup lang="ts">
import { computed } from "vue";
import type { Project } from "../../types";

type AgentKey = "shortDrama" | "novel" | "anime";
type CreationMode = "upload" | "ai" | "manual";
type WorkflowCard = {
  agent: AgentKey;
  mode: CreationMode;
  title: string;
  description: string;
  chips: string[];
  variant: "upload" | "ai" | "manual";
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
  (e: "start-create", value: { agent: AgentKey; mode: CreationMode }): void;
  (e: "open-project", projectId: number): void;
  (e: "delete-project", projectId: number): void;
  (e: "previous-page"): void;
  (e: "next-page"): void;
}>();

const workflowCards: WorkflowCard[] = [
  {
    agent: "shortDrama",
    mode: "upload",
    variant: "upload",
    title: "视频创作",
    description: "从剧本或梗概开始，整理为分镜、角色图、首帧和视频任务。",
    chips: ["剧本导入", "分镜", "视频任务"],
  },
  {
    agent: "novel",
    mode: "manual",
    variant: "manual",
    title: "小说创作",
    description: "先建立世界观、人物关系和写作规则，再进入大纲与正文生成。",
    chips: ["世界观", "章节大纲", "正文草稿"],
  },
  {
    agent: "anime",
    mode: "manual",
    variant: "ai",
    title: "动画资产",
    description: "先锁定角色、场景、视觉风格和资产约束，再服务分镜与视频。",
    chips: ["角色立绘", "场景资产", "视觉约束"],
  },
];

const emptyText = computed(() => "还没有项目。先选择上方一个创作入口，建立视频、小说或动画资产项目。");

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
  <div class="workspace-home">
    <section class="agent-home-hero panel panel--paper">
      <div class="agent-home-hero__title">
        <p class="panel-heading__kicker">创作入口</p>
        <h2>先选你现在要完成的事</h2>
        <p>不要先理解 Agent。直接选择视频、小说或动画资产入口，项目创建后再进入对应生产流程。</p>
      </div>

      <div class="script-entry-grid" aria-label="创作入口">
        <button
          v-for="entry in workflowCards"
          :key="entry.title"
          class="script-entry-card"
          :class="`script-entry-card--${entry.variant}`"
          type="button"
          :disabled="loading"
          @click="emit('start-create', { agent: entry.agent, mode: entry.mode })"
        >
          <strong>{{ entry.title }}</strong>
          <span>{{ entry.description }}</span>
          <span class="script-entry-card__chips">
            <em v-for="chip in entry.chips" :key="chip">{{ chip }}</em>
          </span>
        </button>
      </div>
    </section>

    <section class="project-shelf panel">
      <div class="project-shelf__head">
        <div>
          <p class="panel-heading__kicker">我的项目</p>
          <h2>最近创作</h2>
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
          <button class="primary-button primary-button--compact" type="button" :disabled="loading" @click="emit('start-create', { agent: 'shortDrama', mode: 'upload' })">新建视频项目</button>
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
