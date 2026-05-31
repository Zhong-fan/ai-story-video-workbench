<script setup lang="ts">
import ProjectCreateWizard from "./ProjectCreateWizard.vue";
import type { ProjectCreateDraft, ReferenceWorkResolved } from "../../types";

type StyleProfileOption = { value: string; label: string; description: string; bullets?: string[] };
type GenreOptionCard = { value: string; label: string; description: string };
type SuggestionKind = "world_brief" | "writing_rules";
type WizardStep = 1 | 2 | 3;

defineProps<{
  loading: boolean;
  step: WizardStep;
  form: ProjectCreateDraft;
  genreOptionCards: GenreOptionCard[];
  styleProfileOptions: StyleProfileOption[];
  referenceWorkInput: string;
  referenceWorkResolved: ReferenceWorkResolved | null;
  assistantLoadingKind?: SuggestionKind | "reference_work" | null;
  assistantSeedWorld: string;
  assistantSeedWriting: string;
  worldSuggestions: string[];
  writingSuggestions: string[];
}>();

const emit = defineEmits<{
  (e: "update:step", value: WizardStep): void;
  (e: "submit"): void;
  (e: "update:title", value: string): void;
  (e: "update:genre", value: string): void;
  (e: "update:reference-work-input", value: string): void;
  (e: "resolve-reference-work"): void;
  (e: "confirm-reference-work"): void;
  (e: "clear-reference-work"): void;
  (e: "update:world-brief", value: string): void;
  (e: "update:writing-rules", value: string): void;
  (e: "update:style-profile", value: string): void;
  (e: "update:assistant-seed-world", value: string): void;
  (e: "update:assistant-seed-writing", value: string): void;
  (e: "generate-suggestion", kind: SuggestionKind): void;
  (e: "use-suggestion", payload: { kind: SuggestionKind; text: string; mode: "replace" | "append" }): void;
}>();
</script>

<template>
  <main class="workspace workspace--single">
    <section class="panel panel--paper">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">新建项目</p>
          <h2>先把小说的核心设定立住</h2>
          <p class="panel-heading__desc">项目层只放长期有效的信息：题材、世界设定、写作偏好和文风。具体剧情前提留到章节里写。</p>
        </div>
      </div>
      <ProjectCreateWizard
        :loading="loading"
        :step="step"
        :form="form"
        :genre-option-cards="genreOptionCards"
        :style-profile-options="styleProfileOptions"
        :reference-work-input="referenceWorkInput"
        :reference-work-resolved="referenceWorkResolved"
        :reference-work-confirmed="form.reference_work_confirmed"
        :assistant-loading-kind="assistantLoadingKind"
        :assistant-seed-world="assistantSeedWorld"
        :assistant-seed-writing="assistantSeedWriting"
        :world-suggestions="worldSuggestions"
        :writing-suggestions="writingSuggestions"
        @update:step="emit('update:step', $event)"
        @submit="emit('submit')"
        @submit-quick="emit('submit')"
        @update:title="emit('update:title', $event)"
        @update:genre="emit('update:genre', $event)"
        @update:reference-work-input="emit('update:reference-work-input', $event)"
        @resolve-reference-work="emit('resolve-reference-work')"
        @confirm-reference-work="emit('confirm-reference-work')"
        @clear-reference-work="emit('clear-reference-work')"
        @update:world-brief="emit('update:world-brief', $event)"
        @update:writing-rules="emit('update:writing-rules', $event)"
        @update:style-profile="emit('update:style-profile', $event)"
        @update:assistant-seed-world="emit('update:assistant-seed-world', $event)"
        @update:assistant-seed-writing="emit('update:assistant-seed-writing', $event)"
        @generate-suggestion="emit('generate-suggestion', $event)"
        @use-suggestion="emit('use-suggestion', $event)"
      />
    </section>
  </main>
</template>
