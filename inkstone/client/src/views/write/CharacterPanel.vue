<template>
  <div class="panel">
    <div class="panel-input-area">
      <label class="panel-label">故事背景</label>
      <textarea v-model="storyContext" rows="3" placeholder="描述你的故事世界观或已有角色设定..." ref="inputRef"></textarea>
      <button class="btn btn-primary btn-full" @click="go" :disabled="loading">
        <span v-if="loading" class="loading-dots">AI 正在创作<span class="dots"></span></span>
        <span v-else>生成角色 ♛</span>
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
        <p class="empty-hint">AI 角色设定将显示在这里</p>
      </div>
      <div class="result-card" v-for="(item, idx) in history" :key="idx">
        <div class="card-header">
          <span class="card-badge">角色设定</span>
          <span class="card-time">{{ item.time }}</span>
        </div>
        <div class="card-body markdown-body" v-html="item.text"></div>
        <div class="card-actions">
          <button class="card-btn" @click="$emit('insert', stripHtml(item.text))">插入编辑器</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { api } from '../../api/index.js'

const props = defineProps({ tabKey: { type: String, default: '' } })
defineEmits(['insert'])
const storyContext = ref('')
const loading = ref(false)
const history = ref([])
const inputRef = ref(null)

function stripHtml(html) {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || ''
}

async function go() {
  if (!storyContext.value.trim()) return
  loading.value = true
  const res = await api.post('/api/write/character', { story_context: storyContext.value })
  loading.value = false
  if (res.code === 0) {
    history.value.unshift({
      text: res.data.characters,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    })
  } else {
    history.value.unshift({ text: `<span class="error">${res.msg}</span>`, time: '' })
  }
}

function onTrigger(e) { if (e.detail?.tab === props.tabKey) go() }
onMounted(() => window.addEventListener('inkstone:trigger-ai', onTrigger))
onUnmounted(() => window.removeEventListener('inkstone:trigger-ai', onTrigger))
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';
</style>
