<script setup lang="ts">
import { onBeforeUnmount, watch } from "vue";

type PreviewKind = "image" | "audio" | "video";

const props = defineProps<{
  open: boolean;
  title: string;
  kind: PreviewKind;
  url: string;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

let previousBodyOverflow = "";

function close() {
  emit("close");
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === "Escape" && props.open) {
    close();
  }
}

function lockBodyScroll() {
  if (typeof document === "undefined") return;
  previousBodyOverflow = document.body.style.overflow;
  document.body.style.overflow = "hidden";
}

function unlockBodyScroll() {
  if (typeof document === "undefined") return;
  document.body.style.overflow = previousBodyOverflow;
}

watch(
  () => props.open,
  (open) => {
    if (typeof document === "undefined") return;
    document.removeEventListener("keydown", handleKeydown);
    if (!open) {
      unlockBodyScroll();
      return;
    }
    document.addEventListener("keydown", handleKeydown);
    lockBodyScroll();
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  if (typeof document !== "undefined") {
    document.removeEventListener("keydown", handleKeydown);
  }
  unlockBodyScroll();
});
</script>

<template>
  <div v-if="open" class="asset-modal" role="dialog" aria-modal="true" :aria-label="title" @click.self="close">
    <div class="asset-modal__body">
      <div class="panel-heading">
        <div><p class="panel-heading__kicker">预览</p><h2>{{ title }}</h2></div>
        <button class="ghost-button ghost-button--small" type="button" @click="close">关闭</button>
      </div>
      <img v-if='kind === "image"' class="asset-preview asset-preview--image" :src="url" alt="" />
      <audio v-else-if='kind === "audio"' class="asset-preview asset-preview--audio" :src="url" controls />
      <video v-else class="asset-preview asset-preview--video" :src="url" controls playsinline />
    </div>
  </div>
</template>
