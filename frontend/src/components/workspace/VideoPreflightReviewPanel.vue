<script setup lang="ts">
import { computed } from "vue";
import type { StoryboardPreflightSummary } from "../../types";

const props = defineProps<{
  summary: StoryboardPreflightSummary | null;
}>();

const emit = defineEmits<{
  (e: "focus-preflight-issue", value: { sectionKey: string; item: string }): void;
}>();

const sections = computed(() => {
  const summary = props.summary;
  if (!summary) return [];
  return [
    { key: "blocked", title: "阻断项", items: summary.blocked_reasons ?? [] },
    { key: "warning", title: "风险提示", items: summary.risk_warnings ?? [] },
    { key: "generated", title: "本次补齐", items: summary.generated_character_turnarounds ?? [] },
    { key: "skipped", title: "复用锁定资产", items: summary.skipped_locked_character_turnarounds ?? [] },
    { key: "gates", title: "质量门禁", items: summary.quality_gate_failures ?? [] },
  ].filter((section) => section.items.length);
});

const readinessTone = computed(() => {
  const readiness = props.summary?.readiness ?? "ready";
  if (readiness === "blocked") return "blocked";
  if (readiness === "warning") return "warning";
  return "ready";
});

function readinessLabel(readiness: StoryboardPreflightSummary["readiness"]) {
  switch (readiness) {
    case "blocked":
      return "已阻断";
    case "warning":
      return "需人工确认";
    case "ready":
    default:
      return "可以继续";
  }
}
</script>

<template>
  <section class="panel panel--paper preflight-shell">
    <div class="panel-heading">
      <div>
        <p class="panel-heading__kicker">视频预检</p>
        <h2>渲染前检查</h2>
        <p class="panel-heading__desc">预检先判断能不能继续，再把阻断项、风险项和已复用的锁定资产拆开给用户看，不用读后台事件猜状态。</p>
      </div>
    </div>

    <template v-if="summary">
      <div class="preflight-topline" :class="`preflight-topline--${readinessTone}`">
        <div>
          <strong>预检状态</strong>
          <h3>{{ readinessLabel(summary.readiness) }}</h3>
          <p>readiness：{{ summary.readiness }}</p>
        </div>
        <div class="preflight-metrics">
          <span>阻断 {{ summary.blocked_reasons?.length ?? 0 }}</span>
          <span>风险 {{ summary.risk_warnings?.length ?? 0 }}</span>
          <span>门禁 {{ summary.quality_gate_failures?.length ?? 0 }}</span>
        </div>
      </div>

      <div v-if="sections.length" class="preflight-grid">
        <article v-for="section in sections" :key="section.key" class="memory-card preflight-card">
          <strong>{{ section.title }}</strong>
          <button
            v-for="item in section.items"
            :key="`${section.key}-${item}`"
            class="preflight-item"
            type="button"
            @click="emit('focus-preflight-issue', { sectionKey: section.key, item })"
          >
            {{ item }}
          </button>
        </article>
      </div>
      <p v-else class="empty-text">当前没有阻断项或额外风险提示。</p>
    </template>

    <p v-else class="empty-text">还没有预检结果。点击预检后，这里会展示阻断原因、风险提示和自动补齐的依赖项。</p>
  </section>
</template>

<style scoped>
.preflight-shell {
  display: grid;
  gap: 18px;
}

.preflight-topline {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 18px;
  padding: 18px 20px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.88);
  background:
    radial-gradient(circle at top right, rgba(240, 111, 155, 0.08), transparent 40%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(255, 247, 250, 0.8));
}

.preflight-topline h3,
.preflight-topline p {
  margin: 0;
}

.preflight-topline h3 {
  margin-top: 6px;
  font-size: 1.5rem;
}

.preflight-topline p {
  margin-top: 6px;
  color: var(--ink-soft);
}

.preflight-topline--blocked h3 {
  color: #b91c1c;
}

.preflight-topline--warning h3 {
  color: #b45309;
}

.preflight-topline--ready h3 {
  color: #166534;
}

.preflight-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preflight-metrics span {
  padding: 0.42rem 0.72rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.86);
  font-size: 0.82rem;
}

.preflight-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.preflight-card {
  gap: 8px;
  padding: 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.76);
}

.preflight-item {
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  color: inherit;
  font: inherit;
  cursor: pointer;
  line-height: 1.6;
}

.preflight-item:hover,
.preflight-item:focus-visible {
  color: color-mix(in oklab, var(--rose-strong) 52%, var(--ink));
  outline: none;
}

@media (max-width: 760px) {
  .preflight-topline {
    display: grid;
    align-items: stretch;
  }
}
</style>
