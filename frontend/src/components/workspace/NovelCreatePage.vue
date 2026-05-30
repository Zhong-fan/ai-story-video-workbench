<script setup lang="ts">
import LongformPipelinePanel from "./LongformPipelinePanel.vue";
import type { CharacterCard, ContextPack, LongformState, NovelCard, NovelDetail, Project } from "../../types";

defineProps<{
  project?: Project | null;
  projectTitle?: string;
  loading: boolean;
  state: LongformState;
  contextPack?: ContextPack | null;
  characterCards: CharacterCard[];
  managedNovels: NovelCard[];
  currentNovel?: NovelDetail | null;
  preferredSeriesPlanId?: number | null;
  preferredDraftVersionId?: number | null;
}>();

const emit = defineEmits<{
  (e: "generate-plan", value: { target_chapter_count: number; user_brief: string }): void;
  (e: "submit-feedback", value: {
    target_type: "series" | "arc" | "chapter";
    target_id: number;
    feedback_text: string;
    feedback_type: string;
    priority: number;
  }): void;
  (e: "lock-plan", seriesPlanId: number): void;
  (e: "restore-plan-version", value: { seriesPlanId: number; versionId: number }): void;
  (e: "batch-generate", value: { series_plan_id: number; start_chapter_no: number; end_chapter_no: number }): void;
  (e: "retry-batch", jobId: number): void;
  (e: "pause-batch", jobId: number): void;
  (e: "resume-batch", jobId: number): void;
  (e: "cancel-batch", jobId: number): void;
  (e: "revise-draft", value: { draftVersionId: number; feedback_text: string }): void;
  (e: "canonicalize-draft", value: { draftVersionId: number; novel_id?: number | null; author_name: string; visibility: "public" | "private"; tagline: string }): void;
  (e: "update-outline", value: { outlineId: number; title: string; outline: Record<string, unknown>; status: string }): void;
}>();
</script>

<template>
  <div class="workspace workspace--single">
    <section class="panel panel--paper">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">小说创作</p>
          <h2>{{ projectTitle }}</h2>
          <p class="panel-heading__desc">这里现在只保留长篇小说主流程：概要、批量正文、章节修订和定稿。不再放旧的单章新建与单章生成路线。</p>
        </div>
      </div>
    </section>

    <LongformPipelinePanel
      mode="novel"
      :project="project"
      :project-title="projectTitle"
      :loading="loading"
      :state="state"
      :context-pack="contextPack"
      :character-cards="characterCards"
      :managed-novels="managedNovels"
      :current-novel="currentNovel"
      :preferred-series-plan-id="preferredSeriesPlanId"
      :preferred-draft-version-id="preferredDraftVersionId"
      @generate-plan="emit('generate-plan', $event)"
      @submit-feedback="emit('submit-feedback', $event)"
      @lock-plan="emit('lock-plan', $event)"
      @restore-plan-version="emit('restore-plan-version', $event)"
      @batch-generate="emit('batch-generate', $event)"
      @retry-batch="emit('retry-batch', $event)"
      @pause-batch="emit('pause-batch', $event)"
      @resume-batch="emit('resume-batch', $event)"
      @cancel-batch="emit('cancel-batch', $event)"
      @revise-draft="emit('revise-draft', $event)"
      @canonicalize-draft="emit('canonicalize-draft', $event)"
      @update-outline="emit('update-outline', $event)"
    />
  </div>
</template>
