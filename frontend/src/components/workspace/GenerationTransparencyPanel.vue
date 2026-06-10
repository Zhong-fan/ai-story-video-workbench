<script setup lang="ts">
import { computed, ref } from "vue";
import type { GenerationTraceStep } from "../../types";

const props = withDefaults(defineProps<{
  steps?: GenerationTraceStep[];
}>(), {
  steps: () => [],
});

const emit = defineEmits<{
  (e: "focus-render-source", value: { shotId: number; assetId: number; assetType: string }): void;
}>();

const expandedStep = ref<string | null>(null);

const normalizedSteps = computed(() => props.steps.filter((step) => step && typeof step === "object"));
const activeCount = computed(() => normalizedSteps.value.filter((step) => step.status === "completed" || step.status === "ready").length);
const blockedCount = computed(() => normalizedSteps.value.filter((step) => step.status === "blocked").length);
const warningCount = computed(() => normalizedSteps.value.filter((step) => step.status === "warning").length);

function toggleExpanded(stepKey: string) {
  expandedStep.value = expandedStep.value === stepKey ? null : stepKey;
}

function statusLabel(status: GenerationTraceStep["status"]) {
  switch (status) {
    case "completed":
      return "已完成";
    case "blocked":
      return "已阻断";
    case "warning":
      return "有风险";
    case "ready":
    default:
      return "已就绪";
  }
}

function asMultiline(value: unknown) {
  if (typeof value === "string") return value;
  if (value == null) return "";
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function compactLines(lines: string[]) {
  return lines.filter((line) => line.trim()).slice(0, 3);
}

function parameterEntries(step: GenerationTraceStep) {
  if (!step.parameters || typeof step.parameters !== "object") return [];
  return Object.entries(step.parameters).filter(([key, value]) => {
    if (key === "render_prompt_sources") return false;
    if (value == null) return false;
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === "object") return Object.keys(value as Record<string, unknown>).length > 0;
    return String(value).trim().length > 0;
  });
}

function renderPromptSources(step: GenerationTraceStep) {
  const raw = step.parameters?.render_prompt_sources;
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object")
    .map((item) => ({
      assetId: Number(item.asset_id || 0),
      assetType: String(item.asset_type || ""),
      shotId: Number(item.shot_id || 0),
      status: String(item.status || ""),
      prompt: String(item.prompt || "").trim(),
    }))
    .filter((item) => item.prompt);
}

function assetTypeLabel(value: string) {
  if (value === "video") return "视频片段";
  if (value === "image") return "镜头画面";
  if (value === "subtitle") return "字幕";
  return value || "资产";
}

function isRenderStep(step: GenerationTraceStep) {
  return step.step_key === "render";
}
</script>

<template>
  <section class="panel panel--paper transparency-shell">
    <div class="panel-heading">
      <div>
        <p class="panel-heading__kicker">生成透明度</p>
        <h2>本次生成用了什么</h2>
        <p class="panel-heading__desc">把来源、分镜、资产、预检和渲染拆开看。先读结论，再钻到具体 prompt 和参数，不需要自己翻日志猜。</p>
      </div>
    </div>

    <div v-if="normalizedSteps.length" class="transparency-overview">
      <article class="transparency-stat">
        <strong>链路步骤</strong>
        <span>{{ normalizedSteps.length }}</span>
        <em>当前可见的质量链路</em>
      </article>
      <article class="transparency-stat">
        <strong>可继续</strong>
        <span>{{ activeCount }}</span>
        <em>已完成或可继续推进</em>
      </article>
      <article class="transparency-stat">
        <strong>阻断</strong>
        <span>{{ blockedCount }}</span>
        <em>需要先修正的关键问题</em>
      </article>
      <article class="transparency-stat">
        <strong>风险</strong>
        <span>{{ warningCount }}</span>
        <em>建议人工复核的环节</em>
      </article>
    </div>

    <div v-if="normalizedSteps.length" class="transparency-sequence">
      <article v-for="(step, index) in normalizedSteps" :key="step.step_key" class="memory-card transparency-card">
        <div class="transparency-card__head">
          <div class="transparency-card__title">
            <span class="transparency-step-no">{{ String(index + 1).padStart(2, "0") }}</span>
            <div>
              <strong>{{ step.label }}</strong>
              <p v-if="step.source_mode" class="transparency-card__subline">来源模式：{{ step.source_mode }}</p>
            </div>
          </div>
          <span class="transparency-badge" :class="`transparency-badge--${step.status}`">{{ statusLabel(step.status) }}</span>
        </div>

        <div class="transparency-card__summary">
          <span v-for="line in compactLines(step.summary_lines)" :key="`${step.step_key}-${line}`">{{ line }}</span>
        </div>

        <div v-if="step.inherited_inputs?.length" class="transparency-pill-grid">
          <div v-for="input in step.inherited_inputs" :key="`${step.step_key}-${input.kind}-${input.label}`" class="transparency-pill-card">
            <strong>{{ input.label }}</strong>
            <span>{{ input.value }}</span>
          </div>
        </div>

        <div class="mode-switch transparency-actions">
          <button class="ghost-button ghost-button--small" type="button" @click="toggleExpanded(step.step_key)">
            {{ expandedStep === step.step_key ? "收起技术细节" : "展开技术细节" }}
          </button>
        </div>

        <div v-if="expandedStep === step.step_key" class="transparency-detail-stack">
          <div v-if="isRenderStep(step) && step.prompt_text" class="transparency-detail transparency-detail--hero">
            <strong>最终执行 Prompt</strong>
            <span class="transparency-detail__note">这是当前渲染阶段最接近实际执行输入的 Prompt，优先读这一块，再看下方来源和参数。</span>
            <pre class="trace-pre">{{ step.prompt_text }}</pre>
          </div>

          <div v-if="renderPromptSources(step).length" class="transparency-render-block">
            <div class="transparency-render-block__head">
              <strong>渲染 Prompt 来源</strong>
              <span>直接展示当前渲染阶段已经落库的 prompt，不用再从参数 JSON 里翻。</span>
            </div>
            <div class="transparency-render-grid">
              <article
                v-for="source in renderPromptSources(step)"
                :key="`${step.step_key}-${source.assetId}-${source.assetType}`"
                class="transparency-render-card"
                role="button"
                tabindex="0"
                @click="emit('focus-render-source', { shotId: source.shotId, assetId: source.assetId, assetType: source.assetType })"
                @keydown.enter.prevent="emit('focus-render-source', { shotId: source.shotId, assetId: source.assetId, assetType: source.assetType })"
                @keydown.space.prevent="emit('focus-render-source', { shotId: source.shotId, assetId: source.assetId, assetType: source.assetType })"
              >
                <div class="transparency-render-card__meta">
                  <strong>{{ assetTypeLabel(source.assetType) }}</strong>
                  <span>#{{ source.assetId }} · shot {{ source.shotId || "-" }}</span>
                  <em>{{ source.status }}</em>
                </div>
                <pre class="trace-pre">{{ source.prompt }}</pre>
              </article>
            </div>
          </div>

          <div v-if="parameterEntries(step).length" class="transparency-detail-grid">
            <article v-for="[key, value] in parameterEntries(step)" :key="`${step.step_key}-${key}`" class="transparency-detail-card">
              <strong>{{ key }}</strong>
              <pre class="trace-pre">{{ asMultiline(value) }}</pre>
            </article>
          </div>
          <div v-if="step.model" class="transparency-detail">
            <strong>模型</strong>
            <pre class="trace-pre">{{ step.model }}</pre>
          </div>
          <div v-if="step.prompt_text && !isRenderStep(step)" class="transparency-detail">
            <strong>Prompt / 输入正文</strong>
            <pre class="trace-pre">{{ step.prompt_text }}</pre>
          </div>
        </div>
      </article>
    </div>

    <p v-else class="empty-text">当前还没有结构化生成链路。开始分镜预检或视频流程后，这里会显示每一步实际喂给模型的内容。</p>
  </section>
</template>

<style scoped>
.transparency-shell {
  display: grid;
  gap: 18px;
}

.transparency-overview {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.transparency-stat {
  display: grid;
  gap: 6px;
  padding: 16px;
  border-radius: 16px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(255, 244, 249, 0.76));
  border: 1px solid rgba(255, 255, 255, 0.86);
  box-shadow: 0 14px 28px rgba(240, 111, 155, 0.1);
}

.transparency-stat strong,
.transparency-stat em {
  color: var(--ink-soft);
  font-style: normal;
}

.transparency-stat span {
  font-size: 1.8rem;
  line-height: 1;
  font-weight: 800;
  color: color-mix(in oklab, var(--rose-strong) 22%, #172033);
}

.transparency-sequence {
  display: grid;
  gap: 16px;
}

.transparency-card {
  gap: 14px;
  padding: 18px;
  border-radius: 18px;
  background:
    radial-gradient(circle at top right, rgba(240, 111, 155, 0.08), transparent 42%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(255, 248, 251, 0.78));
  border: 1px solid rgba(255, 255, 255, 0.88);
  box-shadow: 0 18px 34px rgba(240, 111, 155, 0.08);
}

.transparency-card__head {
  display: flex;
  gap: 18px;
  justify-content: space-between;
  align-items: start;
}

.transparency-card__title {
  display: flex;
  gap: 14px;
  align-items: start;
}

.transparency-step-no {
  width: 40px;
  height: 40px;
  display: inline-grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(255, 236, 243, 0.92);
  color: color-mix(in oklab, var(--rose-strong) 56%, var(--ink));
  font-size: 0.86rem;
  font-weight: 800;
  flex: 0 0 auto;
}

.transparency-card__subline {
  margin: 4px 0 0;
  color: var(--ink-soft);
  font-size: 0.88rem;
}

.transparency-badge {
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 700;
  padding: 5px 12px;
  white-space: nowrap;
  background: rgba(255, 255, 255, 0.74);
  color: color-mix(in oklab, var(--rose-strong) 36%, var(--ink));
}

.transparency-badge--completed {
  border-color: rgba(34, 197, 94, 0.24);
  background: rgba(240, 253, 244, 0.92);
  color: #166534;
}

.transparency-badge--blocked {
  border-color: rgba(239, 68, 68, 0.24);
  background: rgba(254, 242, 242, 0.92);
  color: #b91c1c;
}

.transparency-badge--warning {
  border-color: rgba(245, 158, 11, 0.24);
  background: rgba(255, 251, 235, 0.94);
  color: #b45309;
}

.transparency-card__summary {
  display: grid;
  gap: 6px;
  max-width: 72ch;
}

.transparency-pill-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.transparency-pill-card {
  display: grid;
  gap: 3px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(255, 255, 255, 0.82);
}

.transparency-pill-card strong {
  font-size: 0.78rem;
  color: var(--ink-soft);
}

.transparency-pill-card span {
  overflow-wrap: anywhere;
}

.transparency-actions {
  justify-content: start;
}

.transparency-detail-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.transparency-render-block {
  display: grid;
  gap: 12px;
}

.transparency-render-block__head {
  display: grid;
  gap: 4px;
}

.transparency-render-block__head span {
  color: var(--ink-soft);
  font-size: 0.88rem;
}

.transparency-render-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.transparency-render-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 14px;
  background:
    radial-gradient(circle at top right, rgba(132, 184, 217, 0.08), transparent 42%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.84), rgba(245, 250, 255, 0.78));
  border: 1px solid rgba(255, 255, 255, 0.86);
  cursor: pointer;
  transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
}

.transparency-render-card:hover,
.transparency-render-card:focus-visible {
  transform: translateY(-1px);
  box-shadow: 0 16px 28px rgba(132, 184, 217, 0.14);
  outline: none;
}

.transparency-render-card__meta {
  display: grid;
  gap: 2px;
}

.transparency-render-card__meta span,
.transparency-render-card__meta em {
  color: var(--ink-soft);
  font-size: 0.8rem;
  font-style: normal;
}

.transparency-detail-card {
  display: grid;
  gap: 8px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(255, 255, 255, 0.86);
}

.transparency-detail-stack {
  display: grid;
  gap: 12px;
}

.transparency-detail {
  display: grid;
  gap: 6px;
}

.transparency-detail--hero {
  padding: 14px;
  border-radius: 16px;
  background:
    radial-gradient(circle at top right, rgba(132, 184, 217, 0.1), transparent 40%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(242, 248, 255, 0.8));
  border: 1px solid rgba(255, 255, 255, 0.88);
}

.transparency-detail__note {
  color: var(--ink-soft);
  font-size: 0.88rem;
  line-height: 1.55;
}

@media (max-width: 760px) {
  .transparency-card__head,
  .transparency-card__title {
    display: grid;
  }

  .transparency-card__head {
    justify-content: stretch;
  }
}
</style>
