<template>
  <div class="panel">
    <div class="panel-input-area">
      <label class="panel-label">润色模式</label>
      <select v-model="mode">
        <option v-for="m in modes" :key="m" :value="m">{{ m }}</option>
      </select>
      <label class="panel-label">待润色文字</label>
      <textarea v-model="text" rows="3" :placeholder="placeholder" ref="inputRef"></textarea>
      <button class="btn btn-primary btn-full" @click="go" :disabled="loading">
        <span v-if="loading" class="loading-dots">AI 正在润色<span class="dots"></span></span>
        <span v-else>开始润色 ♦</span>
      </button>
    </div>

    <!-- 加载骨架屏 -->
    <div class="loading-card" v-if="loading">
      <div class="lc-header"></div>
      <div class="lc-body">
        <div class="lc-line"></div>
        <div class="lc-line"></div>
        <div class="lc-line"></div>
      </div>
    </div>

    <div class="panel-results" v-if="!loading">
      <div class="empty-state" v-if="history.length === 0">
        <span class="empty-icon">&#10045;</span>
        <p class="empty-hint">AI 润色结果将显示在这里</p>
      </div>
      <div class="result-card" v-for="(item, idx) in history" :key="idx">
        <div class="card-header">
          <span class="card-badge">{{ item.mode }}模式</span>
          <span class="card-time">{{ item.time }}</span>
        </div>
        <!-- 对比模式 -->
        <div class="compare-block" v-if="item.original">
          <div class="compare-col">
            <span class="compare-label">原文</span>
            <p class="compare-text original">{{ item.original }}</p>
          </div>
          <div class="compare-col">
            <span class="compare-label">润色后</span>
            <p class="compare-text polished">{{ stripHtml(item.text) }}</p>
          </div>
        </div>
        <div class="card-body markdown-body" v-else v-html="renderParagraphBold(item.text)"></div>
        <div class="card-actions">
          <button class="card-btn" @click="$emit('insert', stripHtml(item.text), 'replace')">替换原文</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { api } from '../../api/index.js'
import { renderParagraphBold } from '../../utils/render.js'

const props = defineProps({ content: { type: String, default: '' }, tabKey: { type: String, default: '' } })
defineEmits(['insert'])

const mode = ref('流畅')
const text = ref('')
const loading = ref(false)
const history = ref([])
const inputRef = ref(null)
const modes = ['流畅', '文艺', '有力', '简洁']
const placeholder = props.content ? '将使用编辑器中文字...' : '粘贴需要润色的文字...'

watch(() => props.content, (v) => { if (!text.value) text.value = v })

function stripHtml(html) {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || ''
}

async function go() {
  const input = text.value || props.content
  if (!input.trim()) return
  const original = input
  loading.value = true
  const res = await api.post('/api/write/polish', { text: input, mode: mode.value })
  loading.value = false
  if (res.code === 0) {
    history.value.unshift({
      text: res.data.polished, original, mode: mode.value,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    })
  } else {
    history.value.unshift({ text: `<span class="error">${res.msg}</span>`, original: '', mode: '错误', time: '' })
  }
}

function onTrigger(e) { if (e.detail?.tab === props.tabKey) go() }
onMounted(() => window.addEventListener('inkstone:trigger-ai', onTrigger))
onUnmounted(() => window.removeEventListener('inkstone:trigger-ai', onTrigger))
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

/* 对比模式独有样式 */
.compare-block { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: var(--border-glass); }
.compare-col { padding: 0.75rem; background: rgba(255,255,255,0.03); }
.compare-label { font-size: 0.68rem; font-weight: 600; letter-spacing: 0.08em; color: var(--text-muted); text-transform: uppercase; display: block; margin-bottom: 0.5rem; }
.compare-text { font-size: 0.85rem; line-height: 1.8; color: var(--text-secondary); margin: 0; }
.compare-text.polished { color: var(--text-primary); }
</style>
