<template>
  <div class="page-container" v-if="work">
    <div class="detail-header">
      <button class="btn btn-ghost" @click="$router.back()">&larr; 返回</button>
      <div class="header-actions">
        <button class="btn btn-outline btn-sm" @click="$router.push(`/works/${work.work_id}/edit`)">编辑</button>
        <button v-if="work.type === 'novel'" class="btn btn-ghost btn-sm" @click="$router.push(`/works/${work.work_id}/volumes`)">卷管理</button>
        <button class="btn btn-ghost btn-sm" @click="$router.push(`/read/${work.work_id}`)">阅读</button>
        <button class="btn btn-ghost btn-sm" @click="sharePosterVisible = true">分享</button>
        <button class="btn btn-ghost btn-sm" @click="handleExport">导出</button>
        <button class="btn btn-ghost btn-sm" @click="confirmDelete">删除</button>
      </div>
    </div>

    <div class="detail-body">
      <div class="work-meta">
        <span class="type-badge">{{ typeLabel(work.type) }}</span>
        <span class="status-badge" :class="work.status">{{ statusLabel(work.status) }}</span>
      </div>
      <h1>{{ work.title || '未命名作品' }}</h1>
      <p v-if="work.summary" class="summary">{{ work.summary }}</p>
      <p v-if="work.tags" class="tags">
        <span v-for="t in work.tags.split(',')" :key="t" class="tag">{{ t.trim() }}</span>
      </p>
      <div class="stats">
        <span>{{ work.word_count || 0 }} 字</span>
        <span>{{ work.views || 0 }} 阅读</span>
        <span>{{ work.likes_count || 0 }} 赞</span>
        <span>{{ work.comments_count || 0 }} 评论</span>
      </div>

      <hr />

      <div v-if="chapters.length > 0" class="content-area">
        <div v-for="ch in chapters" :key="ch.chapter_id" class="chapter">
          <h3 v-if="ch.title">{{ ch.title }}</h3>
          <div class="chapter-content markdown-body" v-html="renderContent(ch.content)"></div>
        </div>
      </div>
      <div v-else class="empty">暂无内容</div>
    </div>
  </div>
  <div v-else-if="error" class="page-container center">{{ error }}</div>
  <SharePoster :visible="sharePosterVisible" :work-id="work?.work_id" @close="sharePosterVisible = false" />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import { renderParagraphs } from '../../utils/render.js'
import SharePoster from '../../components/SharePoster.vue'

import { useToast } from '../../composables/useToast.js'
const toast = useToast()
const route = useRoute()
const router = useRouter()
const work = ref(null)
const chapters = ref([])
const error = ref('')
const sharePosterVisible = ref(false)

onMounted(async () => {
  const res = await api.get(`/api/works/${route.params.id}`)
  if (res.code === 0) {
    work.value = res.data.work
    chapters.value = res.data.chapters || []
  } else {
    error.value = res.msg
  }
})

async function handleExport() {
  const res = await api.download(`/api/works/${work.value.work_id}/export`)
  if (res.code !== 0) toast.error(res.msg || '导出失败')
}

async function confirmDelete() {
  if (!confirm('确定删除这个作品吗？此操作不可撤销。')) return
  const res = await api.delete(`/api/works/${work.value.work_id}`)
  if (res.code === 0) {
    router.push('/works')
  } else {
    toast.info(res.msg)
  }
}

function renderContent(text) {
  return renderParagraphs(text)
}

function typeLabel(t) {
  return { novel: '小说', poetry: '诗歌', essay: '散文', script: '剧本' }[t] || t
}
function statusLabel(s) {
  return { draft: '草稿', published: '已发布', private: '私密' }[s] || s
}
</script>

<style scoped>
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-xl); }
.header-actions { display: flex; gap: var(--space-sm); }
.detail-body { max-width: 800px; margin: 0 auto; }
.work-meta { display: flex; gap: var(--space-sm); margin-bottom: var(--space-md); }
.type-badge { font-size: 0.75rem; color: var(--accent-primary); text-transform: uppercase; }
.status-badge { font-size: 0.75rem; padding: 1px 8px; border-radius: var(--radius-sm); }
.status-badge.draft { background: var(--text-muted); color: var(--bg-primary); }
.status-badge.published { background: var(--accent-green); color: var(--bg-primary); }
.status-badge.private { background: var(--accent-warm); color: var(--bg-primary); }
h1 { font-size: 2rem; margin-bottom: var(--space-md); }
.summary { color: var(--text-secondary); margin-bottom: var(--space-md); }
.tags { display: flex; gap: var(--space-sm); flex-wrap: wrap; margin-bottom: var(--space-md); }
.tag { font-size: 0.8rem; padding: 2px 10px; border-radius: var(--radius-full); background: var(--bg-glass); border: 1px solid var(--border-glass); color: var(--text-secondary); }
.stats { display: flex; gap: var(--space-lg); font-size: 0.85rem; color: var(--text-muted); margin-bottom: var(--space-md); }
hr { border: none; border-top: 1px solid var(--border-glass); margin: var(--space-xl) 0; }
.chapter { margin-bottom: var(--space-xl); }
.chapter h3 { margin-bottom: var(--space-md); font-size: 1.2rem; }
.chapter-content { font-family: var(--font-serif); font-size: 1.05rem; line-height: 1.9; }
.empty { text-align: center; color: var(--text-muted); padding: var(--space-2xl); }
.center { text-align: center; padding: var(--space-2xl); color: var(--text-muted); }
</style>
