<script setup lang="ts">
import type { DraftVersion, GenerationItem, NovelCard, NovelDetail, ProjectChapter } from "../../types";

defineProps<{
  managedNovels: NovelCard[];
  draftVersions: DraftVersion[];
  novel?: NovelDetail | null;
  selectedProjectChapter?: ProjectChapter | null;
  selectedDraftGeneration?: GenerationItem | null;
  selectedChapter?: { id: number; title: string; summary: string; content: string; chapter_no: number } | null;
  sortedChapters: Array<{ id: number; title: string; chapter_no: number }>;
  manageTitle: string;
  manageAuthorName: string;
  manageSummary: string;
  manageTagline: string;
  manageVisibility: "public" | "private";
  chapterTitle: string;
  chapterSummary: string;
  chapterContent: string;
  chapterNo: number;
  appendTitle: string;
  appendSummary: string;
  appendContent: string;
  appendChapterNo: number;
  loading: boolean;
}>();

const emit = defineEmits<{
  (e: "open-novel", novelId: number): void;
  (e: "open-published-reader"): void;
  (e: "open-draft-reader", draftVersionId: number): void;
  (e: "open-novel-create"): void;
  (e: "update:manageTitle", value: string): void;
  (e: "update:manageAuthorName", value: string): void;
  (e: "update:manageSummary", value: string): void;
  (e: "update:manageTagline", value: string): void;
  (e: "update:manageVisibility", value: "public" | "private"): void;
  (e: "update:chapterTitle", value: string): void;
  (e: "update:chapterSummary", value: string): void;
  (e: "update:chapterContent", value: string): void;
  (e: "update:chapterNo", value: number): void;
  (e: "update:appendTitle", value: string): void;
  (e: "update:appendSummary", value: string): void;
  (e: "update:appendContent", value: string): void;
  (e: "update:appendChapterNo", value: number): void;
  (e: "select-chapter", value: number | string): void;
  (e: "save-novel"): void;
  (e: "delete-novel"): void;
  (e: "save-chapter"): void;
  (e: "append-chapter"): void;
  (e: "back"): void;
}>();

function formatDateTime(value: string | undefined) {
  if (!value) return "-";
  return new Date(value).toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
</script>

<template>
  <section class="novel-editor">
    <section class="panel panel--paper published-works">
      <div class="section-head">
        <div>
          <p class="panel-heading__kicker">作品管理</p>
          <h2>草稿与已发布作品统一管理</h2>
          <p class="panel-heading__desc">这里同时管理未发布草稿和已发布作品。任何一项都可以直接进入沉浸式阅读。</p>
        </div>
        <div class="hero__actions">
          <button class="ghost-button ghost-button--small" type="button" @click="emit('open-novel-create')">回到小说创作</button>
        </div>
      </div>

      <div v-if="draftVersions.length" class="published-works__grid">
        <button
          v-for="item in draftVersions"
          :key="item.id"
          class="published-work-card"
          type="button"
          @click="emit('open-draft-reader', item.id)"
        >
          <div class="published-work-card__topline">
            <span class="published-work-card__type">草稿</span>
            <span class="published-work-card__meta">v{{ item.version_no }}</span>
          </div>
          <strong>{{ item.title }}</strong>
          <span>{{ item.status }} / {{ item.created_at }}</span>
          <span class="published-work-card__summary">{{ item.summary || "点击阅读这份草稿。" }}</span>
          <em>{{ item.revision_reason || "长篇流水线章节草稿" }}</em>
        </button>
      </div>
      <p v-else class="empty-text">当前项目还没有长篇草稿。</p>

      <div v-if="managedNovels.length" class="published-works__grid">
        <button
          v-for="item in managedNovels"
          :key="item.id"
          class="published-work-card"
          :class="{ 'published-work-card--active': item.id === novel?.id }"
          type="button"
          @click="emit('open-novel', item.id)"
        >
          <div class="published-work-card__topline">
            <span class="published-work-card__type">已发布作品</span>
            <span class="published-work-card__meta">{{ item.chapters_count }} 章</span>
          </div>
          <strong>{{ item.title }}</strong>
          <span>{{ item.genre }} / {{ item.author }}</span>
          <span class="published-work-card__summary">{{ item.summary || item.tagline || "点击管理或阅读这部作品。" }}</span>
          <em>{{ formatDateTime(item.updated_at) }}</em>
        </button>
      </div>
      <p v-else class="empty-text">当前项目还没有已发布作品。</p>
    </section>

    <template v-if="novel">
      <section class="panel panel--paper panel-note">
        <strong>当前正在管理《{{ novel.title }}》</strong>
        <span>这里可以编辑作品资料、修改已发布章节，也可以从下方直接进入阅读。</span>
        <div class="hero__actions">
          <button class="ghost-button ghost-button--small" type="button" @click="emit('open-published-reader')">阅读这部作品</button>
        </div>
      </section>

      <section class="editor-grid">
        <section class="panel panel--paper">
          <div class="section-head"><div><p class="panel-heading__kicker">作品资料</p><h2>{{ novel.title }}</h2></div></div>
          <form class="form-stack" @submit.prevent="emit('save-novel')">
            <label class="field"><span>作品标题</span><input :value="manageTitle" @input="emit('update:manageTitle', ($event.target as HTMLInputElement).value)" /></label>
            <label class="field"><span>作者名</span><input :value="manageAuthorName" @input="emit('update:manageAuthorName', ($event.target as HTMLInputElement).value)" /></label>
            <label class="field"><span>宣传语</span><input :value="manageTagline" @input="emit('update:manageTagline', ($event.target as HTMLInputElement).value)" /></label>
            <label class="field"><span>作品简介</span><textarea :value="manageSummary" rows="4" @input="emit('update:manageSummary', ($event.target as HTMLTextAreaElement).value)" /></label>
            <label class="field"><span>谁可以看</span><select :value="manageVisibility" @change="emit('update:manageVisibility', ($event.target as HTMLSelectElement).value as 'public' | 'private')"><option value="public">公开</option><option value="private">仅自己可见</option></select></label>
            <div class="hero__actions">
              <button class="primary-button" :disabled="loading">保存作品信息</button>
              <button class="ghost-button" type="button" @click="emit('delete-novel')">删除作品</button>
            </div>
          </form>
        </section>

        <section class="panel">
          <div class="section-head"><div><p class="panel-heading__kicker">章节编辑</p><h2>修改这部作品里的现有章节</h2></div></div>
          <label v-if="sortedChapters.length" class="field">
            <span>选择章节</span>
            <select :value="selectedChapter?.id" @change="emit('select-chapter', ($event.target as HTMLSelectElement).value)">
              <option v-for="chapter in sortedChapters" :key="chapter.id" :value="chapter.id">第 {{ chapter.chapter_no }} 章 / {{ chapter.title }}</option>
            </select>
          </label>
          <p v-else class="empty-text">这部作品还没有章节。可以先从下面把一份草稿追加为第一章。</p>
          <form v-if="selectedChapter" class="form-stack" @submit.prevent="emit('save-chapter')">
            <label class="field"><span>章节序号</span><input :value="chapterNo" type="number" min="1" @input="emit('update:chapterNo', Number(($event.target as HTMLInputElement).value))" /></label>
            <label class="field"><span>章节标题</span><input :value="chapterTitle" @input="emit('update:chapterTitle', ($event.target as HTMLInputElement).value)" /></label>
            <label class="field"><span>章节摘要</span><textarea :value="chapterSummary" rows="3" @input="emit('update:chapterSummary', ($event.target as HTMLTextAreaElement).value)" /></label>
            <label class="field"><span>正文内容</span><textarea :value="chapterContent" rows="16" @input="emit('update:chapterContent', ($event.target as HTMLTextAreaElement).value)" /></label>
            <div class="hero__actions">
              <button class="primary-button" :disabled="loading">保存章节</button>
              <button class="ghost-button" type="button" @click="emit('open-published-reader')">阅读当前章节</button>
            </div>
          </form>
        </section>
      </section>

      <section class="panel">
        <div class="section-head"><div><p class="panel-heading__kicker">追加章节</p><h2>把草稿写进《{{ novel.title }}》</h2></div></div>
        <div class="panel panel--paper panel-note">
          <strong v-if="selectedProjectChapter">来源章节：第 {{ selectedProjectChapter.chapter_no }} 章 / {{ selectedProjectChapter.title }}</strong>
          <strong v-else>先回到小说创作页，选中当前章节</strong>
          <span v-if="selectedDraftGeneration">这里只会使用当前章节草稿箱里已选中的草稿：{{ selectedDraftGeneration.title || "未命名草稿" }}。</span>
          <span v-else>这里不再跨项目或跨章节选草稿。先在当前章节草稿箱里选中一份草稿。</span>
        </div>
        <form class="form-stack draft-editor" @submit.prevent="emit('append-chapter')">
          <label class="field"><span>章节序号</span><input :value="appendChapterNo" type="number" min="1" @input="emit('update:appendChapterNo', Number(($event.target as HTMLInputElement).value))" /></label>
          <label class="field"><span>章节标题</span><input :value="appendTitle" @input="emit('update:appendTitle', ($event.target as HTMLInputElement).value)" /></label>
          <label class="field"><span>章节摘要</span><textarea :value="appendSummary" rows="3" @input="emit('update:appendSummary', ($event.target as HTMLTextAreaElement).value)" /></label>
          <label class="field"><span>正文内容</span><textarea :value="appendContent" rows="16" @input="emit('update:appendContent', ($event.target as HTMLTextAreaElement).value)" /></label>
          <button class="primary-button" :disabled="loading || !selectedProjectChapter || !selectedDraftGeneration">保存为新章节</button>
        </form>
      </section>
    </template>
  </section>
</template>
