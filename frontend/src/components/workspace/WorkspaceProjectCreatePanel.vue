<script setup lang="ts">
import { computed } from "vue";
import ProjectCreateWizard from "./ProjectCreateWizard.vue";
import type { ProjectAIBriefDraftPayload, ProjectCreateDraft, ReferenceWorkResolved } from "../../types";

type StyleProfileOption = { value: string; label: string; description: string; bullets?: string[] };
type GenreOptionCard = { value: string; label: string; description: string };
type SuggestionKind = "world_brief" | "writing_rules";
type WizardStep = 1 | 2 | 3;
type CreationMode = "upload" | "ai" | "manual";
type AgentKey = "shortDrama" | "novel" | "anime";

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
  (e: "update:import-draft-text", value: string): void;
  (e: "update:import-draft-filename", value: string): void;
  (e: "update:ai-draft-brief", value: Partial<ProjectAIBriefDraftPayload>): void;
  (e: "load-imported-draft"): void;
  (e: "load-ai-draft"): void;
  (e: "generate-suggestion", kind: SuggestionKind): void;
  (e: "use-suggestion", payload: { kind: SuggestionKind; text: string; mode: "replace" | "append" }): void;
}>();

const props = defineProps<{
  loading: boolean;
  activeAgent: AgentKey;
  creationMode: CreationMode;
  step: WizardStep;
  form: ProjectCreateDraft;
  genreOptionCards: GenreOptionCard[];
  styleProfileOptions: StyleProfileOption[];
  referenceWorkInput: string;
  referenceWorkResolved: ReferenceWorkResolved | null;
  assistantLoadingKind?: SuggestionKind | "reference_work" | null;
  assistantSeedWorld: string;
  assistantSeedWriting: string;
  importDraftText: string;
  importDraftFilename: string;
  aiDraftBrief: ProjectAIBriefDraftPayload;
  worldSuggestions: string[];
  writingSuggestions: string[];
}>();

const createHeaderCopies: Record<AgentKey, Record<CreationMode, { kicker: string; title: string; description: string }>> = {
  shortDrama: {
    upload: {
      kicker: "上传剧本建项目",
      title: "把已有剧本整理成可生产项目",
      description: "先录入剧本标题、题材和原始梗概；创建后继续拆章节、做分镜和视频资产。",
    },
    ai: {
      kicker: "AI 生成剧本",
      title: "先定义方向，再让 AI 扩写剧本",
      description: "用题材、人设、参考作品和视觉风格搭好项目底座；创建后进入小说或短剧生成链路。",
    },
    manual: {
      kicker: "自主输入",
      title: "先把项目核心设定立住",
      description: "项目层只放长期有效的信息：题材、世界设定、写作偏好和文风。具体剧情前提留到章节里写。",
    },
  },
  novel: {
    upload: {
      kicker: "小说导入",
      title: "把已有正文整理成可续写项目",
      description: "先导入正文、章节梗概或人物关系；创建后继续生成大纲、正文草稿和定稿章节。",
    },
    ai: {
      kicker: "AI 生成小说",
      title: "先定义长篇方向，再生成项目底稿",
      description: "用主角、核心冲突、读者定位和文风搭好小说项目底座。",
    },
    manual: {
      kicker: "手动建书",
      title: "先把小说核心设定立住",
      description: "项目层只放长期有效的信息：题材、世界观、人物关系和写作规则。",
    },
  },
  anime: {
    upload: {
      kicker: "上传参考素材",
      title: "把已有设定整理成动画项目",
      description: "导入角色设定、场景说明、分镜草稿或素材清单，再进入资产生产。",
    },
    ai: {
      kicker: "分镜资产企划",
      title: "先生成动画项目底稿",
      description: "用简报生成角色、场景、视觉风格和分镜生产方向。",
    },
    manual: {
      kicker: "动画项目设定",
      title: "先建立角色、场景和视觉约束",
      description: "从视觉风格、角色资产和场景规则开始，后续再进入分镜和视频生成。",
    },
  },
};

const createHeader = computed(() => createHeaderCopies[props.activeAgent][props.creationMode]);
</script>

<template>
  <main class="workspace workspace--single">
    <section class="panel panel--paper">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">{{ createHeader.kicker }}</p>
          <h2>{{ createHeader.title }}</h2>
          <p class="panel-heading__desc">{{ createHeader.description }}</p>
        </div>
      </div>
      <ProjectCreateWizard
        :loading="loading"
        :active-agent="activeAgent"
        :creation-mode="creationMode"
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
        :import-draft-text="importDraftText"
        :import-draft-filename="importDraftFilename"
        :ai-draft-brief="aiDraftBrief"
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
        @update:import-draft-text="emit('update:import-draft-text', $event)"
        @update:import-draft-filename="emit('update:import-draft-filename', $event)"
        @update:ai-draft-brief="emit('update:ai-draft-brief', $event)"
        @load-imported-draft="emit('load-imported-draft')"
        @load-ai-draft="emit('load-ai-draft')"
        @generate-suggestion="emit('generate-suggestion', $event)"
        @use-suggestion="emit('use-suggestion', $event)"
      />
    </section>
  </main>
</template>
