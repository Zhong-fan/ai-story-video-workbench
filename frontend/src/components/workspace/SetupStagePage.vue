<script setup lang="ts">
import { computed } from "vue";
import type { CharacterCard, ContextPack, Project, ProjectChapter, StoryBoundaryRule } from "../../types";

const props = defineProps<{
  project?: Project | null;
  characterCards: CharacterCard[];
  projectChapters: ProjectChapter[];
  contextPack?: ContextPack | null;
}>();

const emit = defineEmits<{
  (e: "open-settings"): void;
  (e: "open-characters"): void;
  (e: "open-context-review"): void;
  (e: "open-library"): void;
}>();

const activeRules = computed<StoryBoundaryRule[]>(() => props.project?.story_boundary_rules ?? []);
const confirmedContext = computed(() => props.contextPack?.status === "confirmed");
const hardConstraints = computed(() => {
  const raw = props.contextPack?.derived_constraints?.hard_constraints;
  return Array.isArray(raw) ? raw.map((item) => String(item)).filter(Boolean).slice(0, 6) : [];
});
</script>

<template>
  <main class="workspace workspace--single stage-page">
    <section class="panel panel--paper">
      <div class="panel-heading">
        <div>
          <p class="panel-heading__kicker">设定阶段</p>
          <h2>{{ project?.title || "当前项目" }}</h2>
          <p class="panel-heading__desc">项目设定、人物、故事边界和生成前校对集中在这里。</p>
        </div>
        <div class="mode-switch">
          <button class="ghost-button ghost-button--small" type="button" @click="emit('open-library')">内容库</button>
        </div>
      </div>
    </section>

    <section class="stage-grid">
      <article class="panel stage-card">
        <div class="panel-heading">
          <div>
            <p class="panel-heading__kicker">项目核心</p>
            <h2>{{ project?.genre || "未设置题材" }}</h2>
          </div>
          <button class="ghost-button ghost-button--small" type="button" @click="emit('open-settings')">编辑设定</button>
        </div>
        <p class="empty-text">{{ project?.world_brief || "还没有项目世界设定。" }}</p>
      </article>

      <article class="panel stage-card">
        <div class="panel-heading">
          <div>
            <p class="panel-heading__kicker">故事边界</p>
            <h2>{{ activeRules.length }} 条硬规则</h2>
          </div>
          <button class="ghost-button ghost-button--small" type="button" @click="emit('open-settings')">确认规则</button>
        </div>
        <div class="card-list" v-if="activeRules.length">
          <div v-for="rule in activeRules.slice(0, 4)" :key="rule.rule_id" class="memory-card">
            <strong>{{ rule.scope_type === "chapter_range" ? `第 ${rule.start_chapter_no}-${rule.end_chapter_no} 章` : "全书" }}</strong>
            <span>{{ rule.instruction || rule.predicate }}</span>
          </div>
        </div>
        <p v-else class="empty-text">还没有确认跨章节硬边界。</p>
      </article>

      <article class="panel stage-card">
        <div class="panel-heading">
          <div>
            <p class="panel-heading__kicker">主要人物</p>
            <h2>{{ characterCards.length }} 张人物卡</h2>
          </div>
          <button class="ghost-button ghost-button--small" type="button" @click="emit('open-characters')">维护人物</button>
        </div>
        <div class="library-chip-row" v-if="characterCards.length">
          <span v-for="card in characterCards.slice(0, 8)" :key="card.id" class="library-chip">{{ card.name }}</span>
        </div>
        <p v-else class="empty-text">还没有主要人物卡。</p>
      </article>

      <article class="panel stage-card">
        <div class="panel-heading">
          <div>
            <p class="panel-heading__kicker">生成前校对</p>
            <h2>{{ confirmedContext ? "已确认" : "待确认" }}</h2>
          </div>
          <button class="ghost-button ghost-button--small" type="button" @click="emit('open-context-review')">打开校对</button>
        </div>
        <p class="empty-text">章节草案 {{ projectChapters.length }} 个；Context Pack {{ contextPack ? `v${contextPack.version_no}` : "尚未生成" }}。</p>
        <div class="card-list" v-if="hardConstraints.length">
          <div v-for="item in hardConstraints" :key="item" class="memory-card">
            <span>{{ item }}</span>
          </div>
        </div>
      </article>
    </section>
  </main>
</template>
