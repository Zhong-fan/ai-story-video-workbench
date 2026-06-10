<script setup lang="ts">
import { computed } from "vue";
import type { ProjectAIBriefDraftPayload, ProjectPayload, ReferenceWorkResolved } from "../../types";

type StyleProfileOption = { value: string; label: string; description: string; bullets?: string[] };
type GenreOptionCard = { value: string; label: string; description: string };
type SuggestionKind = "world_brief" | "writing_rules";
type WizardStep = 1 | 2 | 3;
type CreationMode = "upload" | "ai" | "manual";
type AgentKey = "shortDrama" | "novel" | "anime";

const props = defineProps<{
  loading: boolean;
  activeAgent: AgentKey;
  creationMode: CreationMode;
  step: WizardStep;
  form: ProjectPayload;
  genreOptionCards: GenreOptionCard[];
  styleProfileOptions: StyleProfileOption[];
  referenceWorkInput: string;
  referenceWorkResolved: ReferenceWorkResolved | null;
  referenceWorkConfirmed: boolean;
  assistantLoadingKind?: SuggestionKind | "reference_work" | null;
  assistantSeedWorld: string;
  assistantSeedWriting: string;
  importDraftText: string;
  importDraftFilename: string;
  aiDraftBrief: ProjectAIBriefDraftPayload;
  worldSuggestions: string[];
  writingSuggestions: string[];
}>();

const emit = defineEmits<{
  (e: "update:step", value: WizardStep): void;
  (e: "submit"): void;
  (e: "submitQuick"): void;
  (e: "update:title", value: string): void;
  (e: "update:genre", value: string): void;
  (e: "update:referenceWorkInput", value: string): void;
  (e: "resolveReferenceWork"): void;
  (e: "confirmReferenceWork"): void;
  (e: "clearReferenceWork"): void;
  (e: "update:worldBrief", value: string): void;
  (e: "update:writingRules", value: string): void;
  (e: "update:styleProfile", value: string): void;
  (e: "update:assistantSeedWorld", value: string): void;
  (e: "update:assistantSeedWriting", value: string): void;
  (e: "update:importDraftText", value: string): void;
  (e: "update:importDraftFilename", value: string): void;
  (e: "update:aiDraftBrief", value: Partial<ProjectAIBriefDraftPayload>): void;
  (e: "loadImportedDraft"): void;
  (e: "loadAiDraft"): void;
  (e: "generateSuggestion", kind: SuggestionKind): void;
  (e: "useSuggestion", payload: { kind: SuggestionKind; text: string; mode: "replace" | "append" }): void;
}>();

function nextStep() {
  if (props.step < 3) emit("update:step", (props.step + 1) as WizardStep);
}

function previousStep() {
  if (props.step > 1) emit("update:step", (props.step - 1) as WizardStep);
}

const creationModeCopies: Record<AgentKey, Record<CreationMode, {
  titleLabel: string;
  titlePlaceholder: string;
  worldHint: string;
  uploadPanelTitle: string;
  uploadPanelDescription: string;
  importFilenamePlaceholder: string;
  importTextLabel: string;
  importTextPlaceholder: string;
  aiPanelTitle: string;
  aiPanelDescription: string;
  protagonistPlaceholder: string;
  conflictPlaceholder: string;
  audiencePlaceholder: string;
  tonePlaceholder: string;
}>> = {
  shortDrama: {
    upload: {
      titleLabel: "上传剧本建项目",
      titlePlaceholder: "例如：已有剧本标题 / 第一季短剧项目",
      worldHint: "导入草稿会先写入这里；你也可以继续补充人物、场次和分集说明。",
      uploadPanelTitle: "导入已有剧本",
      uploadPanelDescription: "先粘贴剧本正文或梗概，系统会整理成可编辑项目草稿；确认后才会创建项目。",
      importFilenamePlaceholder: "例如：第一版剧本.txt / 粘贴自飞书文档",
      importTextLabel: "剧本正文或梗概",
      importTextPlaceholder: "粘贴已有剧本、分集梗概、场次说明或主要人物关系。",
      aiPanelTitle: "创作简报",
      aiPanelDescription: "回答几个关键问题，先生成一份可编辑项目草稿，再确认创建。",
      protagonistPlaceholder: "例如：被家族放弃的女律师",
      conflictPlaceholder: "例如：七天内证明遗嘱被篡改",
      audiencePlaceholder: "例如：喜欢强反转和女性成长的短剧观众",
      tonePlaceholder: "例如：高压、克制、每集结尾有反转",
    },
    ai: {
      titleLabel: "AI 生成剧本",
      titlePlaceholder: "例如：雨夜重逢 / 逆袭短剧企划",
      worldHint: "AI 简报草稿会先写入这里；确认后再进入生成前校对。",
      uploadPanelTitle: "导入已有剧本",
      uploadPanelDescription: "先粘贴剧本正文或梗概，系统会整理成可编辑项目草稿；确认后才会创建项目。",
      importFilenamePlaceholder: "例如：第一版剧本.txt / 粘贴自飞书文档",
      importTextLabel: "剧本正文或梗概",
      importTextPlaceholder: "粘贴已有剧本、分集梗概、场次说明或主要人物关系。",
      aiPanelTitle: "创作简报",
      aiPanelDescription: "回答几个关键问题，先生成一份可编辑项目草稿，再确认创建。",
      protagonistPlaceholder: "例如：被家族放弃的女律师",
      conflictPlaceholder: "例如：七天内证明遗嘱被篡改",
      audiencePlaceholder: "例如：喜欢强反转和女性成长的短剧观众",
      tonePlaceholder: "例如：高压、克制、每集结尾有反转",
    },
    manual: {
      titleLabel: "自主输入",
      titlePlaceholder: "先给项目一个能区分的工作标题",
      worldHint: "写清世界观、长期规则、主角状态、关系基线和不可变设定。",
      uploadPanelTitle: "导入已有剧本",
      uploadPanelDescription: "先粘贴剧本正文或梗概，系统会整理成可编辑项目草稿；确认后才会创建项目。",
      importFilenamePlaceholder: "例如：第一版剧本.txt / 粘贴自飞书文档",
      importTextLabel: "剧本正文或梗概",
      importTextPlaceholder: "粘贴已有剧本、分集梗概、场次说明或主要人物关系。",
      aiPanelTitle: "创作简报",
      aiPanelDescription: "回答几个关键问题，先生成一份可编辑项目草稿，再确认创建。",
      protagonistPlaceholder: "例如：被家族放弃的女律师",
      conflictPlaceholder: "例如：七天内证明遗嘱被篡改",
      audiencePlaceholder: "例如：喜欢强反转和女性成长的短剧观众",
      tonePlaceholder: "例如：高压、克制、每集结尾有反转",
    },
  },
  novel: {
    upload: {
      titleLabel: "小说导入",
      titlePlaceholder: "例如：长篇第一卷 / 已有正文整理",
      worldHint: "导入草稿会先写入这里；你也可以继续补充人物关系、章节线索和世界规则。",
      uploadPanelTitle: "导入已有小说",
      uploadPanelDescription: "粘贴正文、章节梗概或人物关系，系统会整理成可续写项目草稿。",
      importFilenamePlaceholder: "例如：第一卷正文.txt / 章节大纲.md",
      importTextLabel: "正文、章节梗概或人物关系",
      importTextPlaceholder: "粘贴已有正文、章节梗概、人物关系或世界观资料。",
      aiPanelTitle: "小说企划简报",
      aiPanelDescription: "回答长篇方向问题，先生成可编辑小说项目草稿。",
      protagonistPlaceholder: "例如：被旧案困住的高中生",
      conflictPlaceholder: "例如：必须在毕业前查清十年前失踪真相",
      audiencePlaceholder: "例如：喜欢青春悬疑和人物成长的读者",
      tonePlaceholder: "例如：克制、细腻、慢热但每章有钩子",
    },
    ai: {
      titleLabel: "AI 生成小说",
      titlePlaceholder: "例如：雨城来信 / 失落天台",
      worldHint: "AI 小说企划会先写入这里；确认后再进入大纲与正文生产。",
      uploadPanelTitle: "导入已有小说",
      uploadPanelDescription: "粘贴正文、章节梗概或人物关系，系统会整理成可续写项目草稿。",
      importFilenamePlaceholder: "例如：第一卷正文.txt / 章节大纲.md",
      importTextLabel: "正文、章节梗概或人物关系",
      importTextPlaceholder: "粘贴已有正文、章节梗概、人物关系或世界观资料。",
      aiPanelTitle: "小说企划简报",
      aiPanelDescription: "回答长篇方向问题，先生成可编辑小说项目草稿。",
      protagonistPlaceholder: "例如：被旧案困住的高中生",
      conflictPlaceholder: "例如：必须在毕业前查清十年前失踪真相",
      audiencePlaceholder: "例如：喜欢青春悬疑和人物成长的读者",
      tonePlaceholder: "例如：克制、细腻、慢热但每章有钩子",
    },
    manual: {
      titleLabel: "手动建书",
      titlePlaceholder: "先给小说一个工作标题",
      worldHint: "写清世界观、人物关系、长期伏笔和写作边界。",
      uploadPanelTitle: "导入已有小说",
      uploadPanelDescription: "粘贴正文、章节梗概或人物关系，系统会整理成可续写项目草稿。",
      importFilenamePlaceholder: "例如：第一卷正文.txt / 章节大纲.md",
      importTextLabel: "正文、章节梗概或人物关系",
      importTextPlaceholder: "粘贴已有正文、章节梗概、人物关系或世界观资料。",
      aiPanelTitle: "小说企划简报",
      aiPanelDescription: "回答长篇方向问题，先生成可编辑小说项目草稿。",
      protagonistPlaceholder: "例如：被旧案困住的高中生",
      conflictPlaceholder: "例如：必须在毕业前查清十年前失踪真相",
      audiencePlaceholder: "例如：喜欢青春悬疑和人物成长的读者",
      tonePlaceholder: "例如：克制、细腻、慢热但每章有钩子",
    },
  },
  anime: {
    upload: {
      titleLabel: "上传参考素材",
      titlePlaceholder: "例如：角色设定集 / 分镜草案",
      worldHint: "导入草稿会先写入这里；重点补充视觉风格、角色资产和场景规则。",
      uploadPanelTitle: "导入已有设定",
      uploadPanelDescription: "粘贴角色设定、场景说明、分镜草稿或素材清单，整理成动画资产项目。",
      importFilenamePlaceholder: "例如：角色设定.md / 分镜说明.txt",
      importTextLabel: "设定、分镜或素材说明",
      importTextPlaceholder: "粘贴角色设定、场景说明、视觉风格、分镜草稿或素材清单。",
      aiPanelTitle: "动画资产简报",
      aiPanelDescription: "回答视觉和生产方向问题，先生成可编辑动画项目草稿。",
      protagonistPlaceholder: "例如：会修理旧相机的少女主角",
      conflictPlaceholder: "例如：她必须拍到城市消失前最后一道光",
      audiencePlaceholder: "例如：喜欢青春奇幻和精致视觉资产的观众",
      tonePlaceholder: "例如：清透、柔和、雨后城市、少量奇幻感",
    },
    ai: {
      titleLabel: "分镜资产企划",
      titlePlaceholder: "例如：雨后街角动画短片",
      worldHint: "AI 资产企划会先写入这里；确认后再补角色、场景和分镜约束。",
      uploadPanelTitle: "导入已有设定",
      uploadPanelDescription: "粘贴角色设定、场景说明、分镜草稿或素材清单，整理成动画资产项目。",
      importFilenamePlaceholder: "例如：角色设定.md / 分镜说明.txt",
      importTextLabel: "设定、分镜或素材说明",
      importTextPlaceholder: "粘贴角色设定、场景说明、视觉风格、分镜草稿或素材清单。",
      aiPanelTitle: "动画资产简报",
      aiPanelDescription: "回答视觉和生产方向问题，先生成可编辑动画项目草稿。",
      protagonistPlaceholder: "例如：会修理旧相机的少女主角",
      conflictPlaceholder: "例如：她必须拍到城市消失前最后一道光",
      audiencePlaceholder: "例如：喜欢青春奇幻和精致视觉资产的观众",
      tonePlaceholder: "例如：清透、柔和、雨后城市、少量奇幻感",
    },
    manual: {
      titleLabel: "角色与场景设定",
      titlePlaceholder: "先给动画资产项目一个工作标题",
      worldHint: "写清视觉风格、角色设定、场景规则和后续视频生成边界。",
      uploadPanelTitle: "导入已有设定",
      uploadPanelDescription: "粘贴角色设定、场景说明、分镜草稿或素材清单，整理成动画资产项目。",
      importFilenamePlaceholder: "例如：角色设定.md / 分镜说明.txt",
      importTextLabel: "设定、分镜或素材说明",
      importTextPlaceholder: "粘贴角色设定、场景说明、视觉风格、分镜草稿或素材清单。",
      aiPanelTitle: "动画资产简报",
      aiPanelDescription: "回答视觉和生产方向问题，先生成可编辑动画项目草稿。",
      protagonistPlaceholder: "例如：会修理旧相机的少女主角",
      conflictPlaceholder: "例如：她必须拍到城市消失前最后一道光",
      audiencePlaceholder: "例如：喜欢青春奇幻和精致视觉资产的观众",
      tonePlaceholder: "例如：清透、柔和、雨后城市、少量奇幻感",
    },
  },
};

const creationModeCopy = computed(() => creationModeCopies[props.activeAgent][props.creationMode]);
</script>

<template>
  <div class="project-wizard">
    <section class="process-panel">
      <article class="process-step" :class="{ 'process-step--done': step > 1, 'process-step--pending': step === 1 }">
        <strong>1. 基础方向</strong>
        <span>标题、题材、参考作品和文风。</span>
      </article>
      <article class="process-step" :class="{ 'process-step--done': step > 2, 'process-step--pending': step === 2 }">
        <strong>2. 内容设定</strong>
        <span>世界观、写作偏好和 AI 扩写。</span>
      </article>
      <article class="process-step" :class="{ 'process-step--pending': step === 3 }">
        <strong>3. 确认创建</strong>
        <span>最后检查，再创建项目。</span>
      </article>
    </section>

    <section v-if="step === 1" class="panel panel--paper">
      <div class="form-stack">
        <section v-if="creationMode === 'upload'" class="assistant-panel creation-mode-panel">
          <div class="assistant-panel__header">
            <div>
              <strong>{{ creationModeCopy.uploadPanelTitle }}</strong>
              <p>{{ creationModeCopy.uploadPanelDescription }}</p>
            </div>
            <button class="primary-button" type="button" :disabled="loading || importDraftText.trim().length < 8" @click="emit('loadImportedDraft')">
              生成项目草稿
            </button>
          </div>
          <label class="field">
            <span>文件名或来源</span>
            <input :value="importDraftFilename" maxlength="255" :placeholder="creationModeCopy.importFilenamePlaceholder" @input="emit('update:importDraftFilename', ($event.target as HTMLInputElement).value)" />
          </label>
          <label class="field">
            <span>{{ creationModeCopy.importTextLabel }}</span>
            <textarea :value="importDraftText" rows="7" maxlength="200000" :placeholder="creationModeCopy.importTextPlaceholder" @input="emit('update:importDraftText', ($event.target as HTMLTextAreaElement).value)" />
          </label>
        </section>

        <section v-else-if="creationMode === 'ai'" class="assistant-panel creation-mode-panel">
          <div class="assistant-panel__header">
            <div>
              <strong>{{ creationModeCopy.aiPanelTitle }}</strong>
              <p>{{ creationModeCopy.aiPanelDescription }}</p>
            </div>
            <button class="primary-button" type="button" :disabled="loading || !aiDraftBrief.protagonist.trim() || !aiDraftBrief.core_conflict.trim()" @click="emit('loadAiDraft')">
              生成项目草稿
            </button>
          </div>
          <div class="assistant-trait-grid">
            <label class="field">
              <span>主角</span>
              <input :value="aiDraftBrief.protagonist" maxlength="500" :placeholder="creationModeCopy.protagonistPlaceholder" @input="emit('update:aiDraftBrief', { protagonist: ($event.target as HTMLInputElement).value })" />
            </label>
            <label class="field">
              <span>核心冲突</span>
              <input :value="aiDraftBrief.core_conflict" maxlength="1000" :placeholder="creationModeCopy.conflictPlaceholder" @input="emit('update:aiDraftBrief', { core_conflict: ($event.target as HTMLInputElement).value })" />
            </label>
          </div>
          <div class="assistant-trait-grid">
            <label class="field">
              <span>目标观众</span>
              <input :value="aiDraftBrief.audience" maxlength="500" :placeholder="creationModeCopy.audiencePlaceholder" @input="emit('update:aiDraftBrief', { audience: ($event.target as HTMLInputElement).value })" />
            </label>
            <label class="field">
              <span>节奏和语气</span>
              <input :value="aiDraftBrief.tone" maxlength="500" :placeholder="creationModeCopy.tonePlaceholder" @input="emit('update:aiDraftBrief', { tone: ($event.target as HTMLInputElement).value })" />
            </label>
          </div>
          <div class="assistant-trait-grid">
            <label class="field">
              <span>预计集数</span>
              <input :value="aiDraftBrief.episode_count ?? ''" type="number" min="1" max="200" @input="emit('update:aiDraftBrief', { episode_count: Number(($event.target as HTMLInputElement).value) || null })" />
            </label>
            <label class="field">
              <span>参考作品</span>
              <input :value="aiDraftBrief.reference_work" maxlength="255" placeholder="可选，例如：黑暗荣耀" @input="emit('update:aiDraftBrief', { reference_work: ($event.target as HTMLInputElement).value })" />
            </label>
          </div>
        </section>

        <label class="field">
          <span>{{ creationModeCopy.titleLabel }}</span>
          <input :value="form.title" maxlength="255" :placeholder="creationModeCopy.titlePlaceholder" @input="emit('update:title', ($event.target as HTMLInputElement).value)" />
        </label>

        <label class="field">
          <span>题材类型</span>
          <small class="field-hint">先按“故事主要发生在哪里、冲突靠什么推进”来选，不用追求绝对准确。拿不准时，优先选最接近的那一类，后面还能改。</small>
          <div class="genre-card-grid">
            <button
              v-for="option in genreOptionCards"
              :key="`wizard-genre-${option.value}`"
              class="choice-card genre-card"
              :class="{ 'choice-card--active': form.genre === option.value }"
              type="button"
              @click="emit('update:genre', option.value)"
            >
              <strong>{{ option.label }}</strong>
              <span>{{ option.description }}</span>
            </button>
          </div>
          <div class="inline-row inline-row--tight">
            <input
              :value="genreOptionCards.some((item) => item.value === form.genre) ? '' : form.genre"
              maxlength="100"
              placeholder="自定义题材"
              @input="emit('update:genre', ($event.target as HTMLInputElement).value)"
            />
          </div>
        </label>

        <label class="field">
          <span>参考作品</span>
          <div class="inline-row inline-row--tight">
            <input
              :value="referenceWorkInput"
              maxlength="255"
              placeholder="例如：天气之子 / 三体 / 你的名字"
              @input="emit('update:referenceWorkInput', ($event.target as HTMLInputElement).value)"
            />
            <button class="ghost-button ghost-button--small" type="button" :disabled="loading || assistantLoadingKind === 'reference_work' || !referenceWorkInput.trim()" @click="emit('resolveReferenceWork')">
              {{ assistantLoadingKind === "reference_work" ? "识别中..." : "识别参考作品" }}
            </button>
          </div>
          <small class="field-hint">先确认 AI 理解的是哪部作品，后面的扩写和续写才会引用它。</small>
        </label>

        <article v-if="referenceWorkResolved" class="assistant-suggestion assistant-suggestion--reference">
          <div class="assistant-panel__header">
            <div>
              <strong>{{ referenceWorkResolved.canonical_title }}</strong>
              <p>{{ referenceWorkResolved.creator }} / {{ referenceWorkResolved.medium }}</p>
            </div>
            <span class="reference-status" :class="{ 'reference-status--confirmed': referenceWorkConfirmed }">
              {{ referenceWorkConfirmed ? "已确认" : "待确认" }}
            </span>
          </div>
          <p>{{ referenceWorkResolved.synopsis }}</p>
          <div class="assistant-trait-grid">
            <div>
              <strong>基础风格特征</strong>
              <ul class="choice-card__bullets">
                <li v-for="item in referenceWorkResolved.style_traits" :key="item">{{ item }}</li>
              </ul>
            </div>
            <div>
              <strong>世界特征</strong>
              <ul class="choice-card__bullets">
                <li v-for="item in referenceWorkResolved.world_traits" :key="item">{{ item }}</li>
              </ul>
            </div>
          </div>
          <div class="assistant-trait-grid">
            <div>
              <strong>可迁移文风</strong>
              <ul class="choice-card__bullets">
                <li v-for="item in referenceWorkResolved.writing_style" :key="item">{{ item }}</li>
              </ul>
            </div>
            <div>
              <strong>写作约束</strong>
              <ul class="choice-card__bullets">
                <li v-for="item in referenceWorkResolved.writing_constraints" :key="item">{{ item }}</li>
              </ul>
            </div>
          </div>
          <div class="assistant-trait-grid">
            <div>
              <strong>视频风格</strong>
              <ul class="choice-card__bullets">
                <li v-for="item in referenceWorkResolved.visual_style" :key="item">{{ item }}</li>
              </ul>
            </div>
            <div>
              <strong>镜头与画面约束</strong>
              <ul class="choice-card__bullets">
                <li v-for="item in referenceWorkResolved.video_constraints" :key="item">{{ item }}</li>
              </ul>
            </div>
          </div>
          <div class="project-meta">
            <div><span>建议画面媒介</span><strong>{{ referenceWorkResolved.visual_medium || "未给出" }}</strong></div>
            <div><span>建议风格参考</span><strong>{{ referenceWorkResolved.visual_artists.join(" / ") || "未给出" }}</strong></div>
          </div>
          <div v-if="referenceWorkResolved.narrative_constraints.length">
            <strong>叙事约束</strong>
            <ul class="choice-card__bullets">
              <li v-for="item in referenceWorkResolved.narrative_constraints" :key="item">{{ item }}</li>
            </ul>
          </div>
          <p class="field-hint">{{ referenceWorkResolved.confidence_note }}</p>
          <div class="hero__actions">
            <button class="ghost-button ghost-button--small" type="button" @click="emit('confirmReferenceWork')">就是这部</button>
            <button class="ghost-button ghost-button--small" type="button" @click="emit('clearReferenceWork')">识别错了</button>
          </div>
        </article>

        <article v-if="referenceWorkConfirmed" class="assistant-suggestion assistant-suggestion--reference">
          <div class="assistant-panel__header">
            <div>
              <strong>已根据参考作品自动补全基础设定</strong>
              <p>系统已经把这部作品拆成世界特征、写作约束和视频风格约束，并写入项目可编辑字段。你可以直接创建，也可以继续微调。</p>
            </div>
          </div>
          <div class="project-meta">
            <div><span>题材</span><strong>{{ form.genre || "未填写" }}</strong></div>
            <div><span>文风</span><strong>{{ styleProfileOptions.find((item) => item.value === form.style_profile)?.label || form.style_profile }}</strong></div>
            <div><span>画面媒介</span><strong>{{ form.visual_style_medium || "未填写" }}</strong></div>
          </div>
          <div class="hero__actions">
            <button class="primary-button" type="button" :disabled="loading || !form.title.trim()" @click="emit('submitQuick')">直接创建项目</button>
            <button class="ghost-button" type="button" @click="nextStep()">高级编辑</button>
          </div>
        </article>

        <label class="field">
          <span>文风预设</span>
          <div class="choice-cards">
            <button
              v-for="option in styleProfileOptions"
              :key="`wizard-style-${option.value}`"
              class="choice-card"
              :class="{ 'choice-card--active': form.style_profile === option.value }"
              type="button"
              @click="emit('update:styleProfile', option.value)"
            >
              <strong>{{ option.label }}</strong>
              <span>{{ option.description }}</span>
              <ul v-if="option.bullets?.length" class="choice-card__bullets">
                <li v-for="bullet in option.bullets" :key="bullet">{{ bullet }}</li>
              </ul>
            </button>
          </div>
        </label>
      </div>
    </section>

    <section v-else-if="step === 2" class="panel panel--paper">
      <div class="form-stack">
        <label class="field">
          <span>世界观</span>
          <textarea :value="form.world_brief" rows="6" maxlength="4000" :placeholder="creationModeCopy.worldHint" @input="emit('update:worldBrief', ($event.target as HTMLTextAreaElement).value)" />
        </label>
        <section class="assistant-panel">
          <div class="assistant-panel__header">
            <div>
              <strong>AI 世界观扩写</strong>
              <p>会结合你的短输入、题材和已确认参考作品生成参考草案。</p>
            </div>
            <button class="ghost-button ghost-button--small" type="button" :disabled="loading || assistantLoadingKind === 'world_brief' || !assistantSeedWorld.trim()" @click="emit('generateSuggestion', 'world_brief')">
              {{ assistantLoadingKind === "world_brief" ? "生成中..." : "扩写世界观" }}
            </button>
          </div>
          <textarea :value="assistantSeedWorld" rows="3" maxlength="600" placeholder="先写一句核心想法" @input="emit('update:assistantSeedWorld', ($event.target as HTMLTextAreaElement).value)" />
          <div v-if="worldSuggestions.length" class="assistant-suggestions">
            <article v-for="suggestion in worldSuggestions" :key="suggestion" class="assistant-suggestion">
              <p>{{ suggestion }}</p>
              <div class="hero__actions">
                <button class="ghost-button ghost-button--small" type="button" @click="emit('useSuggestion', { kind: 'world_brief', text: suggestion, mode: 'replace' })">替换</button>
                <button class="ghost-button ghost-button--small" type="button" @click="emit('useSuggestion', { kind: 'world_brief', text: suggestion, mode: 'append' })">追加</button>
              </div>
            </article>
          </div>
        </section>

        <label class="field">
          <span>写作偏好</span>
          <textarea :value="form.writing_rules" rows="5" maxlength="2000" @input="emit('update:writingRules', ($event.target as HTMLTextAreaElement).value)" />
        </label>
        <section class="assistant-panel">
          <div class="assistant-panel__header">
            <div>
              <strong>AI 写作偏好扩写</strong>
              <p>会把你的一句想法扩成可执行写法约束。</p>
            </div>
            <button class="ghost-button ghost-button--small" type="button" :disabled="loading || assistantLoadingKind === 'writing_rules' || !assistantSeedWriting.trim()" @click="emit('generateSuggestion', 'writing_rules')">
              {{ assistantLoadingKind === "writing_rules" ? "生成中..." : "扩写写作偏好" }}
            </button>
          </div>
          <textarea :value="assistantSeedWriting" rows="3" maxlength="600" placeholder="先写一句写法方向" @input="emit('update:assistantSeedWriting', ($event.target as HTMLTextAreaElement).value)" />
          <div v-if="writingSuggestions.length" class="assistant-suggestions">
            <article v-for="suggestion in writingSuggestions" :key="suggestion" class="assistant-suggestion">
              <p>{{ suggestion }}</p>
              <div class="hero__actions">
                <button class="ghost-button ghost-button--small" type="button" @click="emit('useSuggestion', { kind: 'writing_rules', text: suggestion, mode: 'replace' })">替换</button>
                <button class="ghost-button ghost-button--small" type="button" @click="emit('useSuggestion', { kind: 'writing_rules', text: suggestion, mode: 'append' })">追加</button>
              </div>
            </article>
          </div>
        </section>
      </div>
    </section>

    <section v-else class="panel panel--paper">
      <div class="form-stack">
        <div class="project-meta">
          <div><span>标题</span><strong>{{ form.title || "未填写" }}</strong></div>
          <div><span>题材</span><strong>{{ form.genre || "未填写" }}</strong></div>
          <div><span>文风</span><strong>{{ styleProfileOptions.find((item) => item.value === form.style_profile)?.label || form.style_profile }}</strong></div>
        </div>
        <article v-if="form.reference_work" class="assistant-suggestion assistant-suggestion--reference">
          <div class="assistant-panel__header">
            <div>
              <strong>已确认参考作品</strong>
              <p>{{ form.reference_work }} / {{ form.reference_work_creator || "创作者未填写" }} / {{ form.reference_work_medium || "载体未填写" }}</p>
            </div>
          </div>
          <p>{{ form.reference_work_synopsis || "简介未填写。" }}</p>
          <div class="assistant-trait-grid">
            <div>
              <strong>写作风格线索</strong>
              <ul class="choice-card__bullets">
                <li v-for="item in form.reference_work_style_traits" :key="item">{{ item }}</li>
              </ul>
            </div>
            <div>
              <strong>世界特征</strong>
              <ul class="choice-card__bullets">
                <li v-for="item in form.reference_work_world_traits" :key="item">{{ item }}</li>
              </ul>
            </div>
          </div>
          <div v-if="form.reference_work_narrative_constraints.length">
            <strong>写作与改编约束</strong>
            <ul class="choice-card__bullets">
              <li v-for="item in form.reference_work_narrative_constraints" :key="item">{{ item }}</li>
            </ul>
          </div>
          <p v-if="form.reference_work_confidence_note" class="field-hint">{{ form.reference_work_confidence_note }}</p>
        </article>
        <label class="field">
          <span>最终世界观</span>
          <textarea :value="form.world_brief" rows="7" maxlength="4000" @input="emit('update:worldBrief', ($event.target as HTMLTextAreaElement).value)" />
        </label>
        <label class="field">
          <span>最终写作偏好</span>
          <textarea :value="form.writing_rules" rows="6" maxlength="2000" @input="emit('update:writingRules', ($event.target as HTMLTextAreaElement).value)" />
        </label>
      </div>
    </section>

    <div class="wizard-actions">
      <button v-if="step > 1" class="ghost-button" type="button" @click="previousStep()">上一步</button>
      <div class="wizard-actions__spacer" />
      <button v-if="step < 3" class="primary-button" type="button" @click="nextStep()">下一步</button>
      <button v-else class="primary-button" type="button" :disabled="loading" @click="emit('submit')">创建项目</button>
    </div>
  </div>
</template>
