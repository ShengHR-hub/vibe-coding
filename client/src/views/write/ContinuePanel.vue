<template>
  <div class="panel">
    <div class="panel-input-area">
      <label class="panel-label">写作风格</label>
      <select v-model="style">
        <option v-for="s in styles" :key="s" :value="s">{{ s }}</option>
      </select>
      <label class="panel-label">续写上文</label>
      <textarea v-model="inputContent" rows="3" :placeholder="placeholder" ref="inputRef"></textarea>
      <button class="btn btn-primary btn-full" @click="go" :disabled="loading">
        <span v-if="loading" class="loading-dots">AI 正在续写<span class="dots"></span></span>
        <span v-else>开始续写 →</span>
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

    <!-- 结果卡片 -->
    <div class="panel-results" v-if="!loading">
      <div class="empty-state" v-if="history.length === 0">
        <span class="empty-icon">&#10045;</span>
        <p class="empty-hint">AI 续写结果将显示在这里</p>
      </div>
      <div class="result-card" v-for="(item, idx) in history" :key="idx">
        <div class="card-header">
          <span class="card-badge">{{ item.style }}</span>
          <span class="card-time">{{ item.time }}</span>
        </div>
        <div class="card-body markdown-body" v-html="renderParagraphBold(item.text)"></div>
        <div class="card-actions">
          <button class="card-btn" @click="$emit('insert', stripHtml(item.text))">插入编辑器</button>
          <button class="card-btn ghost" @click="$emit('insert', item.text)">替换为当前</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { api } from '../../api/index.js'
import { renderParagraphBold } from '../../utils/render.js'
import { useWritingStore } from '../../stores/writing.js'

const props = defineProps({ content: { type: String, default: '' }, tabKey: { type: String, default: '' } })
defineEmits(['insert'])

const writingStore = useWritingStore()

const style = ref('现代')
const inputContent = ref('')
const loading = ref(false)
const history = ref([])
const inputRef = ref(null)

const styles = ['现代', '古风', '科幻', '悬疑', '言情', '武侠', '奇幻', '现实主义']
const placeholder = props.content ? '将使用编辑器中内容作为上文...' : '粘贴或输入需要续写的内容...'

watch(() => props.content, (v) => { if (!inputContent.value) inputContent.value = v })

function stripHtml(html) {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || ''
}

function go() {
  const text = inputContent.value || props.content
  if (!text) return
  loading.value = true
  let result = ''
  api.stream('/api/write/continue', { content: text, style: style.value, work_id: writingStore.currentWorkId || null },
    (chunk) => {
      try { const data = JSON.parse(chunk); result += data.chunk } catch {}
    },
    () => {
      loading.value = false
      if (result) {
        history.value.unshift({
          text: result, style: style.value,
          time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        })
      }
    },
    (err) => { loading.value = false; history.value.unshift({ text: `<span class="error">${err}</span>`, style: '错误', time: '' }) }
  )
}

function onTrigger(e) { if (e.detail?.tab === props.tabKey) go() }

onMounted(() => window.addEventListener('inkstone:trigger-ai', onTrigger))
onUnmounted(() => window.removeEventListener('inkstone:trigger-ai', onTrigger))
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';
</style>
