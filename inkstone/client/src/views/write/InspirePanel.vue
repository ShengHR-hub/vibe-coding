<template>
  <div class="panel">
    <label>输入关键词或主题</label>
    <input v-model="keywords" placeholder="例如：末日 爱情 背叛" @keydown.enter="go" />
    <button class="btn btn-primary btn-full" @click="go" :disabled="loading">
      {{ loading ? '生成中...' : '生成灵感' }}
    </button>
    <LoadingSpinner :visible="loading" />
    <div v-if="result" class="result markdown-body" v-html="result"></div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '../../api/index.js'
import LoadingSpinner from '../../components/LoadingSpinner.vue'

const keywords = ref('')
const loading = ref(false)
const result = ref('')

async function go() {
  if (!keywords.value.trim()) { alert('请输入关键词'); return }
  loading.value = true
  result.value = ''
  const res = await api.post('/api/write/inspire', { keywords: keywords.value })
  loading.value = false
  if (res.code === 0) {
    result.value = res.data.inspirations
  } else {
    result.value = `<span class="error">${res.msg}</span>`
  }
}
</script>

<style scoped>
.panel { display: flex; flex-direction: column; gap: 0.75rem; }
label { font-size: 0.8rem; color: var(--text-muted); }
input { width: 100%; padding: 8px 10px; font-size: 0.9rem; }
.btn-full { width: 100%; padding: 8px; }
.result { font-size: 0.92rem; line-height: 1.8; white-space: pre-wrap; }
.error { color: var(--accent-red); }
</style>
