<template>
  <teleport to="body">
    <transition name="poster-fade">
      <div v-if="visible" class="poster-overlay" @click.self="$emit('close')">
        <div class="poster-dialog">
          <button class="poster-close" @click="$emit('close')">&times;</button>

          <h3 class="poster-title">分享海报</h3>

          <!-- 加载中 -->
          <div v-if="loading" class="poster-loading">
            <div class="loading-spinner"></div>
            <span>正在生成海报...</span>
          </div>

          <!-- 预览 -->
          <div v-else-if="posterUrl" class="poster-preview">
            <img :src="posterUrl" alt="分享海报" />
          </div>

          <!-- 操作按钮 -->
          <div v-if="posterUrl" class="poster-actions">
            <button class="btn btn-primary" @click="download">
              保存图片
            </button>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { api } from '../api/index.js'
import { generatePoster } from '../utils/posterGenerator.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
  workId: { type: [Number, String], default: null },
})

defineEmits(['close'])

const loading = ref(false)
const posterUrl = ref('')
let buildToken = 0

watch(() => props.visible, async (val) => {
  if (val && props.workId) {
    await buildPoster()
  } else {
    revokeUrl()
  }
})

function revokeUrl() {
  if (posterUrl.value) {
    URL.revokeObjectURL(posterUrl.value)
    posterUrl.value = ''
  }
}

async function buildPoster() {
  loading.value = true
  revokeUrl()

  const token = ++buildToken

  try {
    const res = await api.get(`/api/works/public/${props.workId}`)
    if (token !== buildToken) return

    if (res.code !== 0) {
      loading.value = false
      return
    }

    const { work, chapters } = res.data
    if (!work) {
      loading.value = false
      return
    }

    const firstContent = chapters?.[0]?.content || ''
    const preview = firstContent.slice(0, 200).replace(/\n/g, ' ')

    const blob = await generatePoster({
      title: work.title,
      author: work.username || '佚名',
      type: work.type,
      summary: work.summary || '',
      content: preview,
      wordCount: work.word_count || 0,
      likes: work.likes_count || 0,
      tags: work.tags || '',
    })

    if (token !== buildToken) return
    posterUrl.value = URL.createObjectURL(blob)
  } catch (e) {
    console.error('[SharePoster] 海报生成失败:', e)
  }

  loading.value = false
}

function download() {
  if (!posterUrl.value) return
  const a = document.createElement('a')
  a.href = posterUrl.value
  a.download = `墨池分享_${Date.now()}.png`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

onUnmounted(() => {
  buildToken++
  revokeUrl()
})
</script>

<style scoped>
.poster-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.poster-dialog {
  position: relative;
  max-width: 400px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  border-radius: 20px;
  background: rgba(15, 15, 26, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 2rem;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.5);
}

.poster-close {
  position: absolute;
  top: 16px; right: 16px;
  background: none; border: none;
  font-size: 1.5rem; color: var(--text-muted);
  cursor: pointer; transition: color 0.2s;
}
.poster-close:hover { color: var(--text-primary); }

.poster-title {
  font-size: 1.1rem;
  color: var(--text-primary);
  margin-bottom: 1.5rem;
  text-align: center;
  letter-spacing: 0.08em;
}

.poster-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem 0;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.loading-spinner {
  width: 32px; height: 32px;
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.poster-preview {
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.poster-preview img {
  width: 100%;
  display: block;
}

.poster-actions {
  display: flex;
  justify-content: center;
}
.poster-actions .btn {
  padding: 10px 32px;
  border-radius: 24px;
  font-size: 0.9rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  background: linear-gradient(135deg, #c4a35a, #9b7d3c);
  color: #0f0f1a;
  transition: all 0.3s ease;
}
.poster-actions .btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(196, 163, 90, 0.3);
}

/* 动画 */
.poster-fade-enter-active, .poster-fade-leave-active {
  transition: opacity 0.25s ease;
}
.poster-fade-enter-from, .poster-fade-leave-to {
  opacity: 0;
}
</style>
