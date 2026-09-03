<template>
  <div class="panel">
    <div class="panel-input-area">
      <label class="panel-label">AI 文字诊断</label>
      <p class="diag-desc">AI 将从节奏、用词、对话、结构、情感等维度全面分析你的文字</p>
      <button class="btn btn-primary btn-full" @click="go" :disabled="loading || !content">
        <span v-if="loading" class="loading-dots">AI 正在诊断<span class="dots"></span></span>
        <span v-else>开始诊断 ⚕</span>
      </button>
    </div>

    <!-- 加载骨架屏 -->
    <div class="loading-card" v-if="loading">
      <div class="lc-header"></div>
      <div class="lc-body">
        <div class="lc-line"></div>
        <div class="lc-line"></div>
        <div class="lc-line"></div>
        <div class="lc-line"></div>
        <div class="lc-line"></div>
      </div>
    </div>

    <!-- 结果 -->
    <div class="panel-results" v-if="!loading">
      <div class="empty-state" v-if="!result">
        <span class="empty-icon">⚕</span>
        <p class="empty-hint">AI 将分析你的文字，给出专业的改进建议</p>
      </div>
      <div class="result-card" v-if="result">
        <div class="card-header">
          <span class="card-badge">诊断报告</span>
          <span class="card-time">{{ resultTime }}</span>
        </div>
        <div class="card-body diagnosis-body" v-html="renderDiagnosis(result)"></div>
        <div class="card-actions">
          <button class="card-btn" @click="$emit('insert', '\n\n---\n【AI 诊断报告】\n' + result)">插入到文末</button>
          <button class="card-btn ghost" @click="result = ''">清除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { api } from '../../api/index.js'

const props = defineProps({ content: { type: String, default: '' }, tabKey: { type: String, default: '' } })
defineEmits(['insert'])

const loading = ref(false)
const result = ref('')
const resultTime = ref('')

function renderDiagnosis(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>')
}

async function go() {
  if (!props.content || props.content.length < 50) {
    result.value = '⚠ 内容太短，至少需要50字才能进行诊断'
    resultTime.value = ''
    return
  }
  loading.value = true
  result.value = ''
  const res = await api.post('/api/write/diagnose', { content: props.content })
  loading.value = false
  if (res.code === 0) {
    result.value = res.data.diagnosis
    resultTime.value = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else {
    result.value = `⚠ ${res.msg}`
  }
}

function onTrigger(e) { if (e.detail?.tab === props.tabKey) go() }
onMounted(() => window.addEventListener('inkstone:trigger-ai', onTrigger))
onUnmounted(() => window.removeEventListener('inkstone:trigger-ai', onTrigger))
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.diag-desc {
  font-size: 0.78rem;
  color: var(--text-muted);
  line-height: 1.6;
  margin: 0;
}

.diagnosis-body :deep(strong) {
  color: var(--accent-primary);
  font-weight: 600;
}

.diagnosis-body :deep(p) {
  margin-bottom: 0.6em;
}
</style>
