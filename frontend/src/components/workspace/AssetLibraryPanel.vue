<script setup lang="ts">
import { computed } from "vue";
import type { MediaAsset, Project } from "../../types";

const props = defineProps<{
  projects: Project[];
  mediaAssets: MediaAsset[];
  loading: boolean;
}>();

const imageTypes = [
  { label: "角色图片", note: "正脸、半身、全身、固定服装" },
  { label: "背景图片", note: "卧室、街道、公司、夜景等场景" },
  { label: "通用图片", note: "可跨项目复用的角色、背景、道具" },
];

const videoTypes = [
  { label: "生成片段", note: "按分镜保存，即梦输出后归档" },
  { label: "参考视频", note: "用于风格、节奏、运镜参考" },
  { label: "成片", note: "项目最终视频或阶段版本" },
];

function isImageAsset(asset: MediaAsset) {
  const value = asset.asset_type.toLowerCase();
  return ["image", "frame", "first_frame", "key_image", "turnaround", "reference"].some((key) => value.includes(key));
}

function isVideoAsset(asset: MediaAsset) {
  const value = asset.asset_type.toLowerCase();
  return ["video", "clip", "movie", "shot_video"].some((key) => value.includes(key));
}

function isGlobalAsset(asset: MediaAsset) {
  return Boolean(asset.meta?.is_global || asset.meta?.global || asset.meta?.scope === "global");
}

const globalImageCount = computed(() => props.mediaAssets.filter((asset) => isImageAsset(asset) && isGlobalAsset(asset)).length);
const globalVideoCount = computed(() => props.mediaAssets.filter((asset) => isVideoAsset(asset) && isGlobalAsset(asset)).length);

function projectAssetStats(projectId: number) {
  const scoped = props.mediaAssets.filter((asset) => asset.project_id === projectId);
  return {
    images: scoped.filter(isImageAsset).length,
    videos: scoped.filter(isVideoAsset).length,
    global: scoped.filter(isGlobalAsset).length,
  };
}
</script>

<template>
  <div class="asset-library-page">
    <section class="asset-library-hero panel panel--paper">
      <div>
        <p class="panel-heading__kicker">资产库</p>
        <h2>按项目管理图片和视频资产</h2>
        <p>角色图、背景图和上一段尾帧会进入即梦生成链路；通用图片可以被多个项目复用。</p>
      </div>
      <div class="asset-global-strip__stats">
        <span>项目 {{ projects.length }}</span>
        <span>素材 {{ mediaAssets.length }}</span>
      </div>
    </section>

    <section class="asset-library-grid">
      <article class="asset-type-panel">
        <div class="asset-type-panel__head">
          <span class="asset-type-panel__icon asset-type-panel__icon--image">图</span>
          <div>
            <h3>图片</h3>
            <p>用于约束角色、背景、道具和关键分镜。</p>
          </div>
        </div>
        <div class="asset-type-list">
          <div v-for="item in imageTypes" :key="item.label" class="asset-type-row">
            <strong>{{ item.label }}</strong>
            <span>{{ item.note }}</span>
          </div>
        </div>
      </article>

      <article class="asset-type-panel">
        <div class="asset-type-panel__head">
          <span class="asset-type-panel__icon asset-type-panel__icon--video">影</span>
          <div>
            <h3>视频</h3>
            <p>用于管理生成片段、参考视频和最终成片。</p>
          </div>
        </div>
        <div class="asset-type-list">
          <div v-for="item in videoTypes" :key="item.label" class="asset-type-row">
            <strong>{{ item.label }}</strong>
            <span>{{ item.note }}</span>
          </div>
        </div>
      </article>
    </section>

    <section class="asset-global-strip panel">
      <div>
        <p class="panel-heading__kicker">通用资产</p>
        <h2>跨项目复用</h2>
      </div>
      <div class="asset-global-strip__stats">
        <span>通用图片 {{ globalImageCount }}</span>
        <span>通用视频 {{ globalVideoCount }}</span>
      </div>
    </section>

    <section class="panel">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">项目分类</p>
          <h2>项目资产分组</h2>
        </div>
      </div>
      <div v-if="projects.length" class="asset-project-list">
        <article v-for="project in projects" :key="project.id" class="asset-project-card">
          <div class="asset-project-card__cover">
            <span>{{ project.title.slice(0, 1) }}</span>
          </div>
          <div>
            <strong>{{ project.title }}</strong>
            <span>{{ project.genre }}</span>
          </div>
          <div class="asset-project-card__stats">
            <span>图片 {{ projectAssetStats(project.id).images }}</span>
            <span>视频 {{ projectAssetStats(project.id).videos }}</span>
            <span>通用 {{ projectAssetStats(project.id).global }}</span>
          </div>
        </article>
      </div>
      <p v-else class="empty-text">还没有项目资产。先创建项目后，角色图片、背景图片和生成视频会按项目归档。</p>
    </section>
  </div>
</template>
