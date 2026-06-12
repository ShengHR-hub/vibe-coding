<template>
  <div class="panel">
    <label>写作风格</label>
    <select v-model="style">
      <option v-for="s in styles" :key="s" :value="s">{{ s }}</option>
    </select>
    <label>当前内容（用于续写上文）</label>
    <textarea v-model="inputContent" rows="4" :placeholder="props.content ? '使用编辑器中内容...' : '粘贴需要续写的内容...'"></textarea>
    <button class="btn btn-primary btn-full" @click="go" :disabled="loading">
      {{ loading ? 'AI 正在续写...' : '开始续写' }}
    </button>
    <div v-if="result" class="result markdown-body" v-html="result"></div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { api } from '../../api/index.js'

const props = defineProps({ content: { type: String, default: '' } })
const style = ref('现代')
const inputContent = ref('')
const loading = ref(false)
const result = ref('')

const styles = ['现代', '古风', '科幻', '悬疑', '言情', '武侠', '奇幻', '现实主义']

watch(() => props.content, (v) => { if (!inputContent.value) inputContent.value = v })

function go() {
  const text = inputContent.value || props.content
  if (!text) { alert('请先输入内容'); return }
  loading.value = true
  result.value = ''
  api.stream('/api/write/continue', { content: text, style: style.value }, (chunk) => {
    try {
      const data = JSON.parse(chunk)
      result.value += data.chunk
    } catch {}
  }, () => { loading.value = false }, (err) => {
    loading.value = false
    result.value = `<span class="error">${err}</span>`
  })
}
</script>

<style scoped>
.panel { display: flex; flex-direction: column; gap: 0.75rem; }
label { font-size: 0.8rem; color: var(--text-muted); }
select, textarea {
  width: 100%;
  padding: 8px 10px;
  font-size: 0.9rem;
  border-radius: var(--radius-sm);
  background: var(--bg-glass);
  border: 1px solid var(--border-glass);
  color: var(--text-primary);
  resize: vertical;
}
.btn-full { width: 100%; padding: 8px; }
.result { white-space: pre-wrap; font-size: 0.92rem; line-height: 1.8; }
.error { color: var(--accent-red); }
</style>
