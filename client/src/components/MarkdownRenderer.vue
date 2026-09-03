<template>
  <div class="markdown-body" v-html="renderedHtml"></div>
</template>

<script setup>
import { computed } from 'vue'
import { renderMarkdownBlock } from '../utils/render.js'

const props = defineProps({
  content: { type: String, default: '' }
})

const renderedHtml = computed(() => renderMarkdownBlock(props.content))
</script>

<style scoped>
.markdown-body {
  line-height: 1.8;
  word-break: break-word;
}
.markdown-body :deep(h1) { font-size: 1.5rem; margin: 1em 0 0.5em; }
.markdown-body :deep(h2) { font-size: 1.3rem; margin: 1em 0 0.5em; }
.markdown-body :deep(h3) { font-size: 1.1rem; margin: 1em 0 0.5em; }
.markdown-body :deep(p) { margin: 0.5em 0; }
.markdown-body :deep(code) {
  background: var(--bg-glass);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}
.markdown-body :deep(strong) { font-weight: 600; color: var(--accent-secondary); }
</style>
