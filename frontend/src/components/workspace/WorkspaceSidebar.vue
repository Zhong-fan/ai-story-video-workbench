<script setup lang="ts">
import type { ViewKey } from "../../types";

type AgentKey = "shortDrama" | "novel" | "anime";

defineProps<{
  currentView: ViewKey;
  activeAgent: AgentKey;
  isAuthenticated: boolean;
  username?: string | null;
  mobileOpen: boolean;
}>();

const emit = defineEmits<{
  (e: "go", view: ViewKey): void;
  (e: "select-agent", agent: AgentKey): void;
  (e: "open-project-create"): void;
  (e: "login"): void;
  (e: "register"): void;
  (e: "logout"): void;
}>();
</script>

<template>
  <aside id="primary-sidebar" class="sidebar panel panel--paper" :class="{ 'sidebar--mobile-open': mobileOpen }">
    <div class="brand brand--sidebar">
      <div class="brand-logo" aria-hidden="true">CF</div>
      <div>
        <p class="eyebrow">创作工作台</p>
        <h1>Chen Flow</h1>
      </div>
    </div>

    <nav class="sidebar-nav" aria-label="Primary">
      <button class="sidebar-nav__item sidebar-nav__item--main" :class="{ 'sidebar-nav__item--active': currentView === 'studio' && activeAgent === 'shortDrama' }" @click="emit('select-agent', 'shortDrama')">短剧Agent</button>
      <button class="sidebar-nav__item" :class="{ 'sidebar-nav__item--active': currentView === 'studio' && activeAgent === 'novel' }" @click="emit('select-agent', 'novel')">小说Agent</button>
      <button class="sidebar-nav__item" :class="{ 'sidebar-nav__item--active': currentView === 'studio' && activeAgent === 'anime' }" @click="emit('select-agent', 'anime')">动漫Agent</button>
      <button class="sidebar-nav__item" :class="{ 'sidebar-nav__item--active': currentView === 'assetLibrary' }" @click="emit('go', 'assetLibrary')">资产</button>
      <button class="sidebar-nav__item" :class="{ 'sidebar-nav__item--active': currentView === 'projectCreate' }" @click="emit('open-project-create')">新建项目</button>
      <button class="sidebar-nav__item" :class="{ 'sidebar-nav__item--active': currentView === 'trash' }" @click="emit('go', 'trash')">回收站</button>
    </nav>

    <div class="sidebar__footer">
      <template v-if="isAuthenticated">
        <div class="sidebar-user">
          <div class="sidebar-user__avatar">{{ (username?.slice(0, 1) ?? "U").toUpperCase() }}</div>
          <div class="sidebar-user__meta">
            <strong>{{ username }}</strong>
          </div>
        </div>
        <button class="ghost-button ghost-button--small" @click="emit('logout')">退出</button>
      </template>
      <template v-else>
        <button class="ghost-button ghost-button--small" @click="emit('login')">登录</button>
        <button class="primary-button primary-button--compact" @click="emit('register')">创建账号</button>
      </template>
    </div>
  </aside>
</template>
