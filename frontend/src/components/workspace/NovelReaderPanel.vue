<script setup lang="ts">
import type { ReaderEntry } from "../../types";

defineProps<{
  workTitle: string;
  chapter: ReaderEntry;
  chapters: ReaderEntry[];
  previousChapter?: ReaderEntry | null;
  nextChapter?: ReaderEntry | null;
  hasNavigation: boolean;
  chapterJumpNo: number;
}>();

const emit = defineEmits<{
  (e: "back"): void;
  (e: "select-chapter", chapterId: string): void;
  (e: "jump"): void;
  (e: "update:chapterJumpNo", value: number): void;
}>();
</script>

<template>
  <section class="reader-page">
    <section class="novel-reader">
      <header class="novel-reader__header">
        <p class="novel-reader__chapter-no">第 {{ chapter.chapter_no }} 章</p>
        <h2>{{ chapter.title }}</h2>
      </header>
      <article class="novel-reader__content">{{ chapter.content }}</article>
      <div class="chapter-nav chapter-nav--bottom">
        <button v-if="previousChapter" class="ghost-button ghost-button--small" type="button" @click="emit('select-chapter', previousChapter.id)">上一章</button>
        <label class="field chapter-nav__select">
          <span>目录</span>
          <select :value="chapter.id" @change="emit('select-chapter', ($event.target as HTMLSelectElement).value)">
            <option v-for="item in chapters" :key="item.id" :value="item.id">第 {{ item.chapter_no }} 章 / {{ item.title }}</option>
          </select>
        </label>
        <form class="chapter-jump" @submit.prevent="emit('jump')">
          <label class="field"><span>跳到</span><input :value="chapterJumpNo" type="number" min="1" @input="emit('update:chapterJumpNo', Number(($event.target as HTMLInputElement).value))" /></label>
          <button class="ghost-button ghost-button--small">跳转</button>
        </form>
        <button class="ghost-button ghost-button--small" type="button" @click="emit('back')">返回目录</button>
        <button v-if="nextChapter" class="ghost-button ghost-button--small" type="button" @click="emit('select-chapter', nextChapter.id)">下一章</button>
      </div>
    </section>
  </section>
</template>
