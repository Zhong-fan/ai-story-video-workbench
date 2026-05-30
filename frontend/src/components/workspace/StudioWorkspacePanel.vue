<script setup lang="ts">
import type { Project } from "../../types";

defineProps<{
  workspaceSearch: string;
  projects: Project[];
  workspacePage: number;
  workspacePageSize: number;
  workspaceTotalPages: number;
  loading: boolean;
}>();

const emit = defineEmits<{
  (e: "update:workspace-search", value: string): void;
  (e: "open-project-create"): void;
  (e: "open-project", projectId: number): void;
  (e: "delete-project", projectId: number): void;
  (e: "previous-page"): void;
  (e: "next-page"): void;
}>();
</script>

<template>
  <div class="workspace workspace--single">
    <section class="panel panel--paper">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">工作台</p>
          <h2>项目</h2>
        </div>
        <button class="primary-button" type="button" :disabled="loading" @click="emit('open-project-create')">新建项目</button>
      </div>
      <label class="field">
        <span>搜索</span>
        <input
          :value="workspaceSearch"
          maxlength="120"
          @input="emit('update:workspace-search', ($event.target as HTMLInputElement).value)"
        />
      </label>
    </section>

    <section class="panel">
      <div class="card-list" v-if="projects.length">
        <article v-for="project in projects" :key="project.id" class="memory-card">
          <button class="card-button" type="button" @click="emit('open-project', project.id)">
            <strong>{{ project.title }}</strong>
            <span>{{ project.genre }}</span>
          </button>
          <button class="ghost-button ghost-button--small" type="button" :disabled="loading" @click="emit('delete-project', project.id)">
            删除
          </button>
        </article>
      </div>
      <p v-else class="empty-text">还没有项目。</p>
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
