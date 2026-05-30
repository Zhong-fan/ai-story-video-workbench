<script setup lang="ts">
import LongformPipelinePanel from "./LongformPipelinePanel.vue";
import type { CharacterCard, CharacterReferenceProfile, ContextPack, CreateStoryboardPayload, LongformState, NovelCard, NovelDetail, Project } from "../../types";

defineProps<{
  project?: Project | null;
  projectTitle?: string;
  loading: boolean;
  state: LongformState;
  contextPack?: ContextPack | null;
  characterCards: CharacterCard[];
  characterReferenceProfiles?: CharacterReferenceProfile[];
  managedNovels: NovelCard[];
  currentNovel?: NovelDetail | null;
  preferredSeriesPlanId?: number | null;
  preferredDraftVersionId?: number | null;
  preferredStoryboardId?: number | null;
  preferredVideoTaskId?: number | null;
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
  (e: "open-novel", novelId: number): void;
  (e: "create-storyboard", value: CreateStoryboardPayload): void;
  (e: "revise-draft", value: { draftVersionId: number; feedback_text: string }): void;
  (e: "canonicalize-draft", value: { draftVersionId: number; novel_id?: number | null; author_name: string; visibility: "public" | "private"; tagline: string }): void;
  (e: "create-video-task", storyboardId: number): void;
  (e: "update-outline", value: { outlineId: number; title: string; outline: Record<string, unknown>; status: string }): void;
  (e: "update-shot", value: {
    storyboardId: number;
    shotId: number;
    narration_text: string;
    visual_prompt: string;
    character_refs: unknown[];
    scene_refs: unknown[];
    audio_script: Record<string, unknown>;
    duration_seconds: number;
    status: string;
  }): void;
  (e: "update-asset", value: { assetId: number; uri: string; status: string; meta: Record<string, unknown> }): void;
  (e: "delete-asset", value: { assetId: number }): void;
  (e: "generate-character-turnaround", value: { character_card_id: number; chapter_no?: number | null; prompt_note: string }): void;
  (e: "generate-shot-first-frame", value: { storyboardId: number; shotId: number }): void;
  (e: "generate-audio-scripts", storyboardId: number): void;
  (e: "generate-storyboard-voice", storyboardId: number): void;
  (e: "prepare-video-production", storyboardId: number): void;
  (e: "generate-shot-voice", value: {
    storyboardId: number;
    shotId: number;
    voice_role?: "narrator" | "dialogue";
    character_card_id?: number | null;
    dialogue_text?: string;
    voice_profile?: string;
    emotion?: string;
  }): void;
  (e: "create-shot", value: {
    storyboardId: number;
    shot_no?: number | null;
    narration_text: string;
    visual_prompt: string;
    character_refs: unknown[];
    scene_refs: unknown[];
    audio_script: Record<string, unknown>;
    duration_seconds: number;
    status: string;
  }): void;
  (e: "delete-shot", value: { storyboardId: number; shotId: number }): void;
  (e: "delete-video-task", value: { taskId: number }): void;
  (e: "delete-storyboard", value: { storyboardId: number }): void;
  (e: "reorder-shots", value: { storyboardId: number; shot_ids: number[] }): void;
  (e: "update-video-task", value: { taskId: number; task_status: string; output_uri: string; progress: Record<string, unknown>; error_message: string }): void;
  (e: "update-visual-style", value: {
    locked: boolean;
    medium: string;
    artists: string[];
    positive: string[];
    negative: string[];
    notes: string;
  }): void;
}>();
</script>

<template>
  <div class="workspace workspace--single">
    <section class="panel panel--paper">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">视频创作</p>
          <h2>{{ projectTitle }}</h2>
          <p class="panel-heading__desc">只处理视频化相关内容：定稿章节选章、视觉约束、角色三视图、分镜、预检、视频任务与成片。</p>
        </div>
      </div>
    </section>

    <LongformPipelinePanel
      mode="video"
      :project="project"
      :project-title="projectTitle"
      :loading="loading"
      :state="state"
      :context-pack="contextPack"
      :character-cards="characterCards"
      :character-reference-profiles="characterReferenceProfiles"
      :managed-novels="managedNovels"
      :current-novel="currentNovel"
      :preferred-series-plan-id="preferredSeriesPlanId"
      :preferred-draft-version-id="preferredDraftVersionId"
      :preferred-storyboard-id="preferredStoryboardId"
      :preferred-video-task-id="preferredVideoTaskId"
      @generate-plan="emit('generate-plan', $event)"
      @submit-feedback="emit('submit-feedback', $event)"
      @lock-plan="emit('lock-plan', $event)"
      @restore-plan-version="emit('restore-plan-version', $event)"
      @batch-generate="emit('batch-generate', $event)"
      @retry-batch="emit('retry-batch', $event)"
      @pause-batch="emit('pause-batch', $event)"
      @resume-batch="emit('resume-batch', $event)"
      @cancel-batch="emit('cancel-batch', $event)"
      @open-novel="emit('open-novel', $event)"
      @create-storyboard="emit('create-storyboard', $event)"
      @revise-draft="emit('revise-draft', $event)"
      @canonicalize-draft="emit('canonicalize-draft', $event)"
      @create-video-task="emit('create-video-task', $event)"
      @update-outline="emit('update-outline', $event)"
    @update-shot="emit('update-shot', $event)"
    @update-asset="emit('update-asset', $event)"
    @delete-asset="emit('delete-asset', $event)"
    @generate-character-turnaround="emit('generate-character-turnaround', $event)"
      @generate-shot-first-frame="emit('generate-shot-first-frame', $event)"
      @generate-audio-scripts="emit('generate-audio-scripts', $event)"
      @generate-storyboard-voice="emit('generate-storyboard-voice', $event)"
      @prepare-video-production="emit('prepare-video-production', $event)"
      @generate-shot-voice="emit('generate-shot-voice', $event)"
    @create-shot="emit('create-shot', $event)"
    @delete-shot="emit('delete-shot', $event)"
    @delete-video-task="emit('delete-video-task', $event)"
    @delete-storyboard="emit('delete-storyboard', $event)"
    @reorder-shots="emit('reorder-shots', $event)"
      @update-video-task="emit('update-video-task', $event)"
      @update-visual-style="emit('update-visual-style', $event)"
    />
  </div>
</template>
