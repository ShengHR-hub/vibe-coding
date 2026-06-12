<template>
  <div class="panel">
    <label>润色模式</label>
    <select v-model="mode">
      <option v-for="m in modes" :key="m" :value="m">{{ m }}</option>
    </select>
    <label>待润色文字</label>
    <textarea v-model="text" rows="4" :placeholder="props.content ? '使用编辑器中文字...' : '粘贴需要润色的文字...'"></textarea>
    <button class="btn btn-primary btn-full" @click="go" :disabled="loading">
      {{ loading ? '润色中...' : '开始润色' }}
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
const mode = ref('流畅')
const text = ref('')
const loading = ref(false)
const result = ref('')

const modes = ['流畅', '文艺', '有力', '简洁']

watch(() => props.content, (v) => { if (!text.value) text.value = v })

async function go() {
  const input = text.value || props.content
  if (!input.trim()) { alert('请提供需要润色的文字'); return }
  loading.value = true
  result.value = ''
  const res = await api.post('/api/write/polish', { text: input, mode: mode.value })
  loading.value = false
  if (res.code === 0) {
    result.value = res.data.polished
  } else {
    result.value = `<span class="error">${res.msg}</span>`
  }
}
</script>

<style scoped>
.panel { display: flex; flex-direction: column; gap: 0.75rem; }
label { font-size: 0.8rem; color: var(--text-muted); }
select, textarea { width: 100%; padding: 8px 10px; font-size: 0.9rem; border-radius: var(--radius-sm); background: var(--bg-glass); border: 1px solid var(--border-glass); color: var(--text-primary); resize: vertical; }
.btn-full { width: 100%; padding: 8px; }
.result { font-size: 0.92rem; line-height: 1.8; white-space: pre-wrap; }
.error { color: var(--accent-red); }
</style>
