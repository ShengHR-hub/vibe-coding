<template>
  <div class="markdown-body" v-html="renderedHtml"></div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  content: { type: String, default: '' }
})

const renderedHtml = computed(() => {
  if (!props.content) return ''
  let html = props.content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
  return `<p>${html}</p>`
})
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
