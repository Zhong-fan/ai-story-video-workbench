<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { ContextPack, Project } from "../../types";

const props = defineProps<{
  project?: Project | null;
  contextPack?: ContextPack | null;
  loading: boolean;
}>();

const emit = defineEmits<{
  (e: "build", value: { reference_mode: "style_reference" | "content_reference" | "hybrid_reference"; user_notes: string; confirm_after_build: boolean }): void;
  (e: "rebuild", value: { reference_mode: "style_reference" | "content_reference" | "hybrid_reference"; user_notes: string; confirm_after_build: boolean }): void;
  (e: "confirm"): void;
  (e: "save-decisions", value: Record<string, string>): void;
  (e: "update-todo", value: { task_id: string; status: string }): void;
  (e: "open-settings"): void;
  (e: "open-characters"): void;
}>();

const referenceMode = ref<"style_reference" | "content_reference" | "hybrid_reference">("hybrid_reference");
const userNotes = ref("");
const questionAnswers = ref<Record<string, string>>({});

watch(
  () => props.contextPack,
  (pack) => {
    referenceMode.value = (pack?.reference_mode as "style_reference" | "content_reference" | "hybrid_reference" | undefined) ?? "hybrid_reference";
    userNotes.value = pack?.user_notes ?? "";
    const decisions = (pack as { user_decisions?: Record<string, string> } | null)?.user_decisions ?? {};
    questionAnswers.value = { ...decisions };
  },
  { immediate: true },
);

const conflicts = computed(() => props.contextPack?.conflict_report ?? []);
const userGuidance = computed(() => props.contextPack?.user_guidance ?? []);
const choiceQuestions = computed(() => props.contextPack?.choice_questions ?? []);
const todoTasks = computed(() => props.contextPack?.todo_tasks ?? []);
const hardConstraints = computed(() => {
  const value = props.contextPack?.derived_constraints?.hard_constraints;
  return Array.isArray(value) ? value : [];
});
const softConstraints = computed(() => {
  const value = props.contextPack?.derived_constraints?.soft_constraints;
  return Array.isArray(value) ? value : [];
});
const storyFeed = computed<Record<string, unknown>>(() => {
  const value = props.contextPack?.feed_preview?.story_generation;
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
});
const videoFeed = computed<Record<string, unknown>>(() => {
  const value = props.contextPack?.feed_preview?.video_generation;
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
});

function asText(value: unknown) {
  if (typeof value === "string") return value;
  if (value == null) return "";
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function submitBuild(confirmAfterBuild: boolean) {
  const payload = {
    reference_mode: referenceMode.value,
    user_notes: userNotes.value,
    confirm_after_build: confirmAfterBuild,
    user_decisions: questionAnswers.value,
  };
  if (props.contextPack) {
    emit("rebuild", payload);
    return;
  }
  emit("build", payload);
}

function saveDecisions() {
  emit("save-decisions", questionAnswers.value);
}
</script>

<template>
  <main class="workspace workspace--single">
    <section class="panel panel--paper">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">生成前校对</p>
          <h2>{{ project?.title || "当前项目" }}</h2>
          <p class="panel-heading__desc">先把项目设定、人物卡和参考作品整理成一份可见、可确认的创作上下文包。后续概要、正文和视频都应以这份包为准。</p>
        </div>
        <div class="mode-switch">
          <button class="ghost-button ghost-button--small" type="button" @click="emit('open-settings')">项目设定</button>
          <button class="ghost-button ghost-button--small" type="button" @click="emit('open-characters')">人物卡</button>
        </div>
      </div>

      <div class="form-stack">
        <label class="field">
          <span>参考作品使用方式</span>
          <select v-model="referenceMode">
            <option value="style_reference">风格参考</option>
            <option value="content_reference">内容参考</option>
            <option value="hybrid_reference">内容和风格都参考</option>
          </select>
        </label>
        <label class="field">
          <span>本轮校对备注</span>
          <textarea v-model="userNotes" rows="4" maxlength="4000" placeholder="例如：优先校对人物姓名、男女主关系、是否符合原著气质。" />
        </label>
        <div class="hero__actions">
          <button class="primary-button" type="button" :disabled="loading" @click="submitBuild(false)">
            {{ contextPack ? "重建校对稿" : "生成校对稿" }}
          </button>
          <button class="ghost-button" type="button" :disabled="loading" @click="submitBuild(true)">
            生成并直接确认
          </button>
          <button v-if="contextPack && contextPack.status !== 'confirmed'" class="ghost-button" type="button" :disabled="loading" @click="emit('confirm')">确认当前上下文包</button>
        </div>
      </div>
    </section>

    <section class="panel panel--paper" v-if="contextPack">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">当前状态</p>
          <h2>Context Pack v{{ contextPack.version_no }}</h2>
          <p class="panel-heading__desc">状态：{{ contextPack.status }}<span v-if="contextPack.confirmed_at"> · 已确认于 {{ contextPack.confirmed_at }}</span></p>
        </div>
      </div>
      <div class="card-list">
        <article class="memory-card">
          <strong>硬约束</strong>
          <span v-for="(item, index) in hardConstraints" :key="`hard-${index}`">{{ item }}</span>
        </article>
        <article class="memory-card">
          <strong>软约束</strong>
          <span v-for="(item, index) in softConstraints" :key="`soft-${index}`">{{ item }}</span>
        </article>
      </div>
    </section>

    <section class="panel panel--paper" v-if="contextPack">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">风险与冲突</p>
          <h2>本轮校对发现的问题</h2>
        </div>
      </div>
      <div v-if="conflicts.length" class="card-list">
        <article v-for="item in conflicts" :key="`${item.code}-${item.title}`" class="memory-card">
          <strong>{{ item.title }}</strong>
          <span>等级：{{ item.severity }}</span>
          <em>{{ item.detail }}</em>
        </article>
      </div>
      <p v-else class="empty-text">当前没有发现明显冲突。</p>
    </section>

    <section class="panel panel--paper" v-if="contextPack && userGuidance.length">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">改进建议</p>
          <h2>建议用户先怎么改</h2>
        </div>
      </div>
      <div class="card-list">
        <article v-for="item in userGuidance" :key="`${item.title}-${item.suggested_action}`" class="memory-card">
          <strong>{{ item.title }}</strong>
          <span>{{ item.detail }}</span>
          <em>{{ item.suggested_action }}</em>
        </article>
      </div>
    </section>

    <section class="panel panel--paper" v-if="contextPack && choiceQuestions.length">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">版本选择</p>
          <h2>需要用户明确选哪一版</h2>
        </div>
      </div>
      <div class="card-list">
        <article v-for="item in choiceQuestions" :key="item.question" class="memory-card">
          <strong>{{ item.question }}</strong>
          <label class="field">
            <span>当前选择</span>
            <select v-model="questionAnswers[item.question_id]">
              <option value="">请选择</option>
              <option v-for="(option, index) in item.options" :key="`${item.question_id}-${index}`" :value="option">{{ option }}</option>
            </select>
          </label>
          <em>建议：{{ item.recommendation }}</em>
        </article>
      </div>
      <div class="hero__actions">
        <button class="primary-button" type="button" :disabled="loading" @click="saveDecisions()">保存这些版本选择</button>
      </div>
    </section>

    <section class="panel panel--paper" v-if="contextPack && todoTasks.length">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">待办任务</p>
          <h2>建议先处理这些项</h2>
        </div>
      </div>
      <div class="card-list">
        <article v-for="item in todoTasks" :key="`${item.title}-${item.detail}`" class="memory-card">
          <strong>{{ item.title }}</strong>
          <span>状态：{{ item.status }}</span>
          <em>{{ item.detail }}</em>
          <div class="hero__actions">
            <button class="ghost-button ghost-button--small" type="button" :disabled="loading || item.status === 'done'" @click="emit('update-todo', { task_id: item.task_id, status: 'done' })">标记已完成</button>
            <button class="ghost-button ghost-button--small" type="button" :disabled="loading || item.status === 'todo'" @click="emit('update-todo', { task_id: item.task_id, status: 'todo' })">标记待处理</button>
            <button class="ghost-button ghost-button--small" type="button" :disabled="loading || item.status === 'skipped'" @click="emit('update-todo', { task_id: item.task_id, status: 'skipped' })">标记跳过</button>
          </div>
        </article>
      </div>
    </section>

    <section class="panel panel--paper" v-if="contextPack">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">喂料预览</p>
          <h2>小说链路将收到的上下文</h2>
        </div>
      </div>
      <pre class="trace-pre">{{ asText(storyFeed) }}</pre>
    </section>

    <section class="panel panel--paper" v-if="contextPack">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">喂料预览</p>
          <h2>视频链路将收到的上下文</h2>
        </div>
      </div>
      <pre class="trace-pre">{{ asText(videoFeed) }}</pre>
    </section>
  </main>
</template>
