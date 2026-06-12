<template>
  <div class="panel">
    <label>故事背景</label>
    <textarea v-model="storyContext" rows="4" placeholder="描述你的故事世界观或已有角色设定..."></textarea>
    <button class="btn btn-primary btn-full" @click="go" :disabled="loading">
      {{ loading ? '生成中...' : '生成角色' }}
    </button>
    <LoadingSpinner :visible="loading" />
    <div v-if="result" class="result markdown-body" v-html="result"></div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '../../api/index.js'
import LoadingSpinner from '../../components/LoadingSpinner.vue'

const storyContext = ref('')
const loading = ref(false)
const result = ref('')

async function go() {
  if (!storyContext.value.trim()) { alert('请提供故事背景'); return }
  loading.value = true
  result.value = ''
  const res = await api.post('/api/write/character', { story_context: storyContext.value })
  loading.value = false
  if (res.code === 0) {
    result.value = res.data.characters
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
