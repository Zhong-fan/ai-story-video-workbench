<script setup lang="ts">
import type { TrashItem } from "../../types";

defineProps<{
  trashItems: TrashItem[];
  trashSummary: Record<TrashItem["item_type"], number>;
}>();

const emit = defineEmits<{
  (e: "restore", item: TrashItem): void;
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
  <section class="section-banner panel panel--paper">
    <div>
      <p class="panel-heading__kicker">回收站</p>
      <h2>已删除内容</h2>
    </div>
    <div class="hero__stats">
      <span>项目 {{ trashSummary.project }}</span>
      <span>作品 {{ trashSummary.novel }}</span>
      <span>人物卡 {{ trashSummary.character_card }}</span>
      <span>脏演化 {{ trashSummary.dirty_evolution }}</span>
    </div>
  </section>

  <section class="panel">
    <div class="card-list" v-if="trashItems.length">
      <article v-for="item in trashItems" :key="`${item.item_type}-${item.item_id}`" class="memory-card">
        <strong>{{ item.title }}</strong>
        <span>{{ item.subtitle || item.item_type }}</span>
        <em>{{ formatDateTime(item.deleted_at) }}</em>
        <button class="ghost-button ghost-button--small" type="button" @click="emit('restore', item)">恢复</button>
      </article>
    </div>
    <p v-else class="empty-text">回收站目前是空的。</p>
  </section>
</template>
