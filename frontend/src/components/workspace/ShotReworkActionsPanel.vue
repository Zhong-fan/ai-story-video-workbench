<script setup lang="ts">
import { computed } from "vue";
import type { ReviewFinding } from "../../types";

type ReworkLevel = ReviewFinding["recommended_rework_level"];

const props = withDefaults(defineProps<{
  findings?: ReviewFinding[];
  disabled?: boolean;
}>(), {
  findings: () => [],
  disabled: false,
});

const emit = defineEmits<{
  (e: "start-shot-rework", finding: ReviewFinding): void;
  (e: "start-storyboard-rework", finding: ReviewFinding): void;
  (e: "start-local-fix", finding: ReviewFinding): void;
}>();

const groupedFindings = computed(() => {
  const groups: Array<{
    level: ReworkLevel;
    title: string;
    description: string;
    actionLabel: string;
    findings: ReviewFinding[];
  }> = [
    {
      level: "shot",
      title: "单镜头返工",
      description: "适合连续性、角色一致性和单镜头执行失败。",
      actionLabel: "按镜头返工",
      findings: props.findings.filter((item) => item.recommended_rework_level === "shot"),
    },
    {
      level: "storyboard",
      title: "分镜层返工",
      description: "适合节奏、叙事结构和镜头组织问题。",
      actionLabel: "回到分镜层",
      findings: props.findings.filter((item) => item.recommended_rework_level === "storyboard"),
    },
    {
      level: "local_fix",
      title: "局部修正",
      description: "适合局部画面瑕疵，先尝试低成本修补。",
      actionLabel: "尝试局部修正",
      findings: props.findings.filter((item) => item.recommended_rework_level === "local_fix"),
    },
  ];
  return groups.filter((group) => group.findings.length);
});

function trigger(level: ReworkLevel, finding: ReviewFinding) {
  if (level === "storyboard") {
    emit("start-storyboard-rework", finding);
    return;
  }
  if (level === "local_fix") {
    emit("start-local-fix", finding);
    return;
  }
  emit("start-shot-rework", finding);
}
</script>

<template>
  <section class="panel panel--paper rework-shell">
    <div class="panel-heading">
      <div>
        <p class="panel-heading__kicker">返工入口</p>
        <h2>按问题类型回退</h2>
        <p class="panel-heading__desc">先分清应该回到单镜头、分镜层还是局部修补，再进入下一步，不要一上来就整段重跑。</p>
      </div>
    </div>

    <div v-if="groupedFindings.length" class="rework-group-list">
      <article v-for="group in groupedFindings" :key="group.level" class="memory-card rework-group-card">
        <div class="rework-group-card__head">
          <strong>{{ group.title }}</strong>
          <span>{{ group.findings.length }} 项</span>
        </div>
        <p class="rework-group-card__desc">{{ group.description }}</p>
        <div class="rework-pill-row">
          <span v-for="finding in group.findings" :key="finding.finding_id" class="rework-pill">{{ finding.title }}</span>
        </div>
        <div class="mode-switch rework-action-grid">
          <button
            v-for="finding in group.findings"
            :key="`${group.level}-${finding.finding_id}`"
            class="ghost-button ghost-button--small"
            type="button"
            :disabled="disabled"
            @click="trigger(group.level, finding)"
          >
            {{ group.actionLabel }}：{{ finding.title }}
          </button>
        </div>
      </article>
    </div>

    <p v-else class="empty-text">当前没有可路由的返工建议。等复核结果写回后，这里会按问题类型给出可执行入口。</p>
  </section>
</template>

<style scoped>
.rework-shell {
  display: grid;
  gap: 18px;
}

.rework-group-list {
  display: grid;
  gap: 14px;
}

.rework-group-card {
  gap: 14px;
  padding: 16px;
  border-radius: 16px;
  background:
    radial-gradient(circle at top right, rgba(240, 111, 155, 0.06), transparent 36%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(255, 247, 250, 0.76));
}

.rework-group-card__head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.rework-group-card__head span {
  font-size: 0.8rem;
  color: var(--ink-soft);
}

.rework-group-card__desc {
  margin: 0;
  color: var(--ink-soft);
}

.rework-pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.rework-pill {
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 999px;
  font-size: 12px;
  padding: 4px 10px;
}

.rework-action-grid {
  justify-content: start;
}
</style>
