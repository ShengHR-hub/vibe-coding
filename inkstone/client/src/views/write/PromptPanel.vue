<template>
  <div class="panel">
    <label>当前卡文情节</label>
    <textarea v-model="context" rows="4" :placeholder="props.content ? '使用编辑器中内容...' : '描述你卡在什么地方...'"></textarea>
    <button class="btn btn-primary btn-full" @click="go" :disabled="loading">
      {{ loading ? '生成中...' : '获取写作建议' }}
    </button>
    <LoadingSpinner :visible="loading" />
    <div v-if="result" class="result markdown-body" v-html="result"></div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { api } from '../../api/index.js'
import LoadingSpinner from '../../components/LoadingSpinner.vue'

const props = defineProps({ content: { type: String, default: '' } })
const context = ref('')
const loading = ref(false)
const result = ref('')

watch(() => props.content, (v) => { if (!context.value) context.value = v })

async function go() {
  const input = context.value || props.content
  if (!input.trim()) { alert('请描述当前情节'); return }
  loading.value = true
  result.value = ''
  const res = await api.post('/api/write/prompt', { context: input })
  loading.value = false
  if (res.code === 0) {
    result.value = res.data.suggestions
  } else {
    result.value = `<span class="error">${res.msg}</span>`
  }
}
</script>

<style scoped>
.panel { display: flex; flex-direction: column; gap: 0.75rem; }
label { font-size: 0.8rem; color: var(--text-muted); }
textarea { width: 100%; padding: 8px 10px; font-size: 0.9rem; resize: vertical; border-radius: var(--radius-sm); background: var(--bg-glass); border: 1px solid var(--border-glass); color: var(--text-primary); }
.btn-full { width: 100%; padding: 8px; }
.result { font-size: 0.92rem; line-height: 1.8; white-space: pre-wrap; }
.error { color: var(--accent-red); }
</style>
