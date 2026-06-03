<script setup lang="ts">
import { computed } from "vue";
import type { Project } from "../../types";

type AgentKey = "shortDrama" | "novel" | "anime";
type CreationMode = "upload" | "ai" | "manual";

const props = defineProps<{
  activeAgent: AgentKey;
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

const agentProfiles: Record<AgentKey, { title: string; subtitle: string; continuity: string[] }> = {
  shortDrama: {
    title: "短剧Agent",
    subtitle: "围绕即梦 jimeng_v30 做连续短剧生产：剧本、分镜、角色图、背景图、首尾帧按镜头绑定。",
    continuity: ["jimeng_v30", "首尾帧图生视频", "上一段尾帧继承"],
  },
  novel: {
    title: "小说Agent",
    subtitle: "从设定、人物、章节大纲到正文草稿，保持人物关系和剧情因果连续。",
    continuity: ["章节大纲", "人物状态", "长文草稿"],
  },
  anime: {
    title: "动漫Agent",
    subtitle: "面向角色立绘、场景图和分镜画面组织，先稳定视觉资产，再进入动画化生产。",
    continuity: ["角色立绘", "场景资产", "分镜画面"],
  },
};

const activeProfile = computed(() => agentProfiles[props.activeAgent]);

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
</script>

<template>
  <div class="workspace-home">
    <section class="agent-home-hero panel panel--paper">
      <div class="agent-home-hero__title">
        <p class="panel-heading__kicker">当前创作类型</p>
        <h2>{{ activeProfile.title }}</h2>
        <p>{{ activeProfile.subtitle }}</p>
        <div class="agent-home-hero__chips">
          <span v-for="item in activeProfile.continuity" :key="item">{{ item }}</span>
        </div>
      </div>

      <div class="script-entry-grid" aria-label="创作入口">
        <button class="script-entry-card script-entry-card--upload" type="button" :disabled="loading" @click="emit('start-create', 'upload')">
          <strong>上传剧本</strong>
          <span>导入已有剧本，拆成章节、分镜和镜头任务。</span>
        </button>
        <button class="script-entry-card script-entry-card--ai" type="button" :disabled="loading" @click="emit('start-create', 'ai')">
          <strong>AI生成剧本</strong>
          <span>从题材、人设和目标风格生成短剧初稿。</span>
        </button>
        <button class="script-entry-card script-entry-card--manual" type="button" :disabled="loading" @click="emit('start-create', 'manual')">
          <strong>自主输入</strong>
          <span>直接输入故事梗概、分集大纲或镜头说明。</span>
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
          <button class="primary-button primary-button--compact" type="button" :disabled="loading" @click="emit('start-create', 'manual')">新建项目</button>
        </div>
      </div>

      <div class="project-card-grid" v-if="projects.length">
        <article v-for="(project, index) in projects" :key="project.id" class="project-home-card">
          <button class="project-home-card__main" type="button" @click="emit('open-project', project.id)">
            <div class="project-home-card__thumb" :class="`project-home-card__thumb--${(index % 4) + 1}`">
              <span>{{ project.title.slice(0, 1) }}</span>
            </div>
            <div class="project-home-card__body">
              <strong>{{ project.title }}</strong>
              <span>{{ project.genre || "未设置题材" }}</span>
              <em>修改于 {{ formatUpdatedAt(project.updated_at) }}</em>
            </div>
          </button>
          <button class="ghost-button ghost-button--small project-home-card__delete" type="button" :disabled="loading" @click="emit('delete-project', project.id)">删除</button>
        </article>
      </div>
      <p v-else class="empty-text">还没有项目。可以先上传剧本、让 AI 生成剧本，或者进入自主输入模式创建第一个项目。</p>

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
