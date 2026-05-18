<script setup lang="ts">
import { computed } from "vue";
import type { BatchGenerationJob, GenerationProgress, LongformState, Storyboard, TaskEvent, VideoTask } from "../../types";

const props = defineProps<{
  projectTitle?: string;
  chapterTitle?: string;
  loading: boolean;
  progress: GenerationProgress;
  longformState?: LongformState | null;
  longformRequestState?: {
    active: boolean;
    stage: string;
    message: string;
    target?: Record<string, unknown>;
  } | null;
}>();

const trace = computed<Record<string, unknown>>(() => props.progress.trace ?? {});
const requestInfo = computed<Record<string, unknown>>(() => {
  const value = trace.value.request;
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
});
const contextInfo = computed<Record<string, unknown>>(() => {
  const value = trace.value.context;
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
});
const contextPackSummary = computed(() => {
  const contextPackId = contextInfo.value.context_pack_id;
  const contextPackVersion = contextInfo.value.context_pack_version;
  const referenceMode = contextInfo.value.context_pack_reference_mode;
  if (!contextPackId && !contextPackVersion && !referenceMode) return null;
  return {
    contextPackId,
    contextPackVersion,
    referenceMode,
  };
});
const stepsInfo = computed<Record<string, unknown>>(() => {
  const value = trace.value.steps;
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
});
const progressLogs = computed(() => props.progress.logs ?? []);
const requestState = computed(() => props.longformRequestState ?? { active: false, stage: "idle", message: "", target: {} });
const longform = computed<LongformState>(() => props.longformState ?? {
  series_plans: [],
  draft_versions: [],
  batch_jobs: [],
  storyboards: [],
  media_assets: [],
  video_tasks: [],
});
const latestBatchJob = computed<BatchGenerationJob | null>(() => longform.value.batch_jobs[0] ?? null);
const latestStoryboard = computed<Storyboard | null>(() => longform.value.storyboards[0] ?? null);
const latestVideoTask = computed<VideoTask | null>(() => longform.value.video_tasks[0] ?? null);
const longformEvents = computed<TaskEvent[]>(() => {
  const events = [
    ...(latestBatchJob.value?.events ?? []),
    ...(latestStoryboard.value?.events ?? []),
    ...(latestVideoTask.value?.events ?? []),
  ];
  return [...events].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 10);
});
const longformStages = computed(() => [
  {
    label: "长篇概要 / 批量正文",
    active: Boolean(latestBatchJob.value),
    status: latestBatchJob.value?.job_status ?? "idle",
    detail: latestBatchJob.value
      ? `当前任务状态：${latestBatchJob.value.job_status}，章节范围 ${latestBatchJob.value.start_chapter_no}-${latestBatchJob.value.end_chapter_no}`
      : "当前没有批量正文任务。",
  },
  {
    label: "分镜任务",
    active: Boolean(latestStoryboard.value),
    status: latestStoryboard.value?.status ?? "idle",
    detail: latestStoryboard.value
      ? `当前分镜：${latestStoryboard.value.title}，镜头数 ${latestStoryboard.value.shots.length}`
      : "当前没有分镜任务。",
  },
  {
    label: "视频任务",
    active: Boolean(latestVideoTask.value),
    status: latestVideoTask.value?.task_status ?? "idle",
    detail: latestVideoTask.value
      ? `当前视频状态：${latestVideoTask.value.task_status}`
      : "当前没有视频任务。",
  },
]);

function asText(value: unknown) {
  if (typeof value === "string") return value;
  if (value == null) return "";
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}
</script>

<template>
  <main class="workspace workspace--single">
    <section class="panel panel--paper">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">生成过程</p>
          <h2>{{ projectTitle || "当前项目" }}<span v-if="chapterTitle"> · {{ chapterTitle }}</span></h2>
          <p class="panel-heading__desc">这里同时展示单章写作 trace 和长篇/视频任务状态。用户不需要翻日志，也能知道流程现在卡在哪一步。</p>
        </div>
      </div>
      <section class="generation-progress generation-progress--trace" aria-live="polite">
        <div>
          <strong>{{ progress.message || "等待后端进度" }}</strong>
          <span>阶段：{{ progress.stage || "idle" }}{{ loading ? " · 正在执行" : "" }}</span>
        </div>
        <div class="generation-progress__bar"><span /></div>
        <ol v-if="progressLogs.length" class="generation-log-list">
          <li v-for="(item, index) in progressLogs" :key="`${item.timestamp}-${index}`" :class="`generation-log-list__item generation-log-list__item--${item.level}`">
            <time>{{ item.timestamp }}</time>
            <strong>{{ item.message }}</strong>
            <span>{{ item.stage }}</span>
            <pre v-if="item.details && Object.keys(item.details).length">{{ asText(item.details) }}</pre>
          </li>
        </ol>
      </section>
    </section>

    <section class="panel panel--paper" v-if="contextPackSummary">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">上下文版本</p>
          <h2>本次生成使用的 Context Pack</h2>
        </div>
      </div>
      <div class="card-list">
        <article class="memory-card">
          <strong>Context Pack</strong>
          <span>ID：{{ contextPackSummary.contextPackId || "-" }}</span>
          <span>版本：{{ contextPackSummary.contextPackVersion || "-" }}</span>
          <em>模式：{{ contextPackSummary.referenceMode || "-" }}</em>
        </article>
      </div>
    </section>

    <section class="panel panel--paper" v-if="requestState.active">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">当前请求</p>
          <h2>前端已发出，等待后端响应</h2>
          <p class="panel-heading__desc">这里只显示真实前端请求状态，不伪造生成流程。只要后端开始返回长篇/视频任务状态，下方任务面板就会接管显示。</p>
        </div>
      </div>
      <section class="generation-progress generation-progress--trace">
        <div>
          <strong>{{ requestState.message }}</strong>
          <span>阶段：{{ requestState.stage }}</span>
        </div>
        <div class="generation-progress__bar"><span /></div>
        <pre v-if="requestState.target && Object.keys(requestState.target).length" class="trace-pre">{{ asText(requestState.target) }}</pre>
      </section>
    </section>

    <section class="panel panel--paper">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">长篇与视频任务</p>
          <h2>当前流程进度</h2>
        </div>
      </div>
      <div class="card-list">
        <article v-for="item in longformStages" :key="item.label" class="memory-card">
          <strong>{{ item.label }}</strong>
          <span>状态：{{ item.status }}</span>
          <em>{{ item.detail }}</em>
        </article>
      </div>
      <div v-if="longformEvents.length" class="card-list">
        <article v-for="event in longformEvents" :key="event.id" class="memory-card">
          <strong>{{ event.event_type }}</strong>
          <span>{{ event.message }}</span>
          <em>{{ event.created_at }}</em>
        </article>
      </div>
      <p v-else class="empty-text">当前还没有长篇或视频任务事件。开始批量正文、分镜或视频任务后，这里会持续刷新。</p>
    </section>

    <section class="panel panel--paper">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">提交内容</p>
          <h2>本次请求参数</h2>
        </div>
      </div>
      <pre class="trace-pre">{{ asText(requestInfo) }}</pre>
    </section>

    <section class="panel panel--paper">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">检索上下文</p>
          <h2>创作上下文摘要</h2>
        </div>
      </div>
      <pre class="trace-pre">{{ asText(contextInfo) }}</pre>
    </section>

    <section class="panel panel--paper">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">阶段输出</p>
          <h2>Draft / Refine / Intent Check</h2>
        </div>
      </div>
      <pre class="trace-pre">{{ asText(stepsInfo) }}</pre>
    </section>
  </main>
</template>
