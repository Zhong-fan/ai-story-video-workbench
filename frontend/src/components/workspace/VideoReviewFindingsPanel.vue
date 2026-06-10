<script setup lang="ts">
import { computed } from "vue";
import type { ReviewFinding } from "../../types";

const props = withDefaults(defineProps<{
  findings?: ReviewFinding[];
}>(), {
  findings: () => [],
});

const emit = defineEmits<{
  (e: "focus-finding", finding: ReviewFinding): void;
}>();

const blockingCount = computed(() => props.findings.filter((item) => item.severity === "blocking").length);
const advisoryCount = computed(() => props.findings.filter((item) => item.severity === "advisory").length);
const dominantRoute = computed(() => {
  const levels = props.findings.map((item) => item.recommended_rework_level);
  if (!levels.length) return "none";
  const score = new Map<string, number>();
  for (const level of levels) score.set(level, (score.get(level) ?? 0) + 1);
  return [...score.entries()].sort((a, b) => b[1] - a[1])[0][0];
});

function severityLabel(severity: ReviewFinding["severity"]) {
  return severity === "blocking" ? "阻断问题" : "建议处理";
}

function categoryLabel(category: ReviewFinding["category"]) {
  switch (category) {
    case "continuity":
      return "连续性";
    case "pacing":
      return "节奏叙事";
    case "local_defect":
      return "局部缺陷";
    case "dependency":
    default:
      return "依赖问题";
  }
}

function reworkLabel(level: ReviewFinding["recommended_rework_level"]) {
  switch (level) {
    case "storyboard":
      return "回到分镜层";
    case "local_fix":
      return "先尝试局部修正";
    case "shot":
    default:
      return "回到单镜头";
  }
}

function routeSummary(value: string) {
  if (value === "storyboard") return "当前问题更偏向分镜层调整。";
  if (value === "local_fix") return "当前问题更偏向局部修补。";
  if (value === "shot") return "当前问题更偏向单镜头返工。";
  return "等待复核结果。";
}
</script>

<template>
  <section class="panel panel--paper review-shell">
    <div class="panel-heading">
      <div>
        <p class="panel-heading__kicker">复核结果</p>
        <h2>质量问题与返工方向</h2>
        <p class="panel-heading__desc">先把阻断问题和建议处理的问题分开，再给出当前更适合回退到哪一层，减少用户盲目重跑。</p>
      </div>
    </div>

    <template v-if="findings.length">
      <div class="review-summary-grid">
        <article class="memory-card review-summary-card review-summary-card--blocking">
          <strong>阻断问题</strong>
          <span>{{ blockingCount }}</span>
          <em>必须先处理</em>
        </article>
        <article class="memory-card review-summary-card review-summary-card--advisory">
          <strong>建议处理</strong>
          <span>{{ advisoryCount }}</span>
          <em>可人工判断是否返工</em>
        </article>
        <article class="memory-card review-summary-card">
          <strong>主建议回退层级</strong>
          <span>{{ reworkLabel(dominantRoute as ReviewFinding["recommended_rework_level"]) }}</span>
          <em>{{ routeSummary(dominantRoute) }}</em>
        </article>
      </div>

      <div class="review-findings-list">
        <article
          v-for="finding in findings"
          :key="finding.finding_id"
          class="memory-card review-finding-card"
          role="button"
          tabindex="0"
          @click="emit('focus-finding', finding)"
          @keydown.enter.prevent="emit('focus-finding', finding)"
          @keydown.space.prevent="emit('focus-finding', finding)"
        >
          <div class="review-finding-card__head">
            <strong>{{ finding.title }}</strong>
            <span class="review-severity" :class="`review-severity--${finding.severity}`">{{ severityLabel(finding.severity) }}</span>
          </div>
          <span class="review-meta-line">问题类型：{{ categoryLabel(finding.category) }}</span>
          <span>{{ finding.detail }}</span>
          <em>建议回退层级：{{ reworkLabel(finding.recommended_rework_level) }}</em>
        </article>
      </div>
    </template>

    <p v-else class="empty-text">当前还没有结构化复核结果。视频任务写回质量结论后，这里会展示问题分类和推荐返工层级。</p>
  </section>
</template>

<style scoped>
.review-shell {
  display: grid;
  gap: 18px;
}

.review-summary-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.review-summary-card {
  gap: 6px;
  padding: 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.78);
}

.review-summary-card span {
  font-size: 1.5rem;
  font-weight: 800;
  line-height: 1.1;
}

.review-summary-card--blocking span {
  color: #b91c1c;
}

.review-summary-card--advisory span {
  color: #b45309;
}

.review-findings-list {
  display: grid;
  gap: 14px;
}

.review-finding-card {
  gap: 10px;
  padding: 16px;
  border-radius: 16px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(255, 247, 250, 0.76));
  cursor: pointer;
  transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
}

.review-finding-card:hover,
.review-finding-card:focus-visible {
  transform: translateY(-1px);
  box-shadow: 0 16px 28px rgba(240, 111, 155, 0.1);
  outline: none;
}

.review-finding-card__head {
  align-items: center;
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.review-severity {
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 0.76rem;
  font-weight: 700;
}

.review-severity--blocking {
  background: rgba(254, 242, 242, 0.94);
  color: #b91c1c;
}

.review-severity--advisory {
  background: rgba(255, 251, 235, 0.94);
  color: #b45309;
}

.review-meta-line {
  color: var(--ink-soft);
}
</style>
