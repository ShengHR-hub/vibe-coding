<template>
  <div class="page-container" v-if="workTitle">
    <div class="review-header">
      <button class="btn btn-ghost btn-sm" @click="$router.back()">&larr; 返回</button>
      <h2>{{ workTitle }}</h2>
      <span class="type-badge">{{ typeLabel }}</span>
    </div>

    <!-- 生成书评 -->
    <section class="section glass-card">
      <div class="section-header">
        <h3>AI 书评</h3>
        <button class="btn btn-primary btn-sm" @click="generateReview" :disabled="reviewLoading">
          {{ reviewLoading ? '生成中...' : reviewText ? '重新生成' : '生成书评' }}
        </button>
      </div>
      <div v-if="reviewLoading" class="center"><LoadingSpinner /></div>
      <div v-else-if="reviewError" class="center error">{{ reviewError }}</div>
      <div v-else-if="reviewText" class="review-content">{{ reviewText }}</div>
      <div v-else class="center muted">点击"生成书评"让 AI 为这部作品撰写专业书评</div>
    </section>

    <!-- 相似作品 -->
    <section class="section glass-card">
      <h3>相似作品</h3>
      <div v-if="simLoading" class="center"><LoadingSpinner /></div>
      <div v-else-if="simError" class="center error">{{ simError }}</div>
      <div v-else-if="similarWorks.length === 0" class="center muted">暂无相似作品</div>
      <div v-else class="works-grid">
        <div v-for="w in similarWorks" :key="w.work_id" class="work-card glass-card" @click="$router.push(`/work/${w.work_id}`)">
          <div class="card-type">{{ typeLabelMap[w.type] || w.type }}</div>
          <h4>{{ w.title }}</h4>
          <p v-if="w.summary" class="card-summary">{{ w.summary }}</p>
          <div class="card-meta">
            <span class="author"><span class="avatar-dot">{{ w.username?.charAt(0) }}</span>{{ w.username }}</span>
            <span>{{ w.word_count || 0 }} 字</span>
            <span>{{ w.likes_count || 0 }} 赞</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 为您推荐 -->
    <section class="section glass-card">
      <h3>为您推荐</h3>
      <div v-if="recLoading" class="center"><LoadingSpinner /></div>
      <div v-else-if="recError" class="center error">{{ recError }}</div>
      <div v-else-if="recItems.length === 0" class="center muted">暂无推荐</div>
      <div v-else>
        <p v-if="recReason" class="rec-reason">{{ recReason }}</p>
        <div class="works-grid">
          <div v-for="w in recItems" :key="w.work_id" class="work-card glass-card" @click="$router.push(`/work/${w.work_id}`)">
            <div class="card-type">{{ typeLabelMap[w.type] || w.type }}</div>
            <h4>{{ w.title }}</h4>
            <p v-if="w.summary" class="card-summary">{{ w.summary }}</p>
            <div class="card-meta">
              <span class="author"><span class="avatar-dot">{{ w.username?.charAt(0) }}</span>{{ w.username }}</span>
              <span>{{ w.word_count || 0 }} 字</span>
              <span>{{ w.likes_count || 0 }} 赞</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api/index.js'
import LoadingSpinner from '../../components/LoadingSpinner.vue'

const route = useRoute()
const workId = route.params.work_id
const workTitle = ref('')
const typeLabel = ref('')

const reviewLoading = ref(false)
const reviewError = ref('')
const reviewText = ref('')

const simLoading = ref(false)
const simError = ref('')
const similarWorks = ref([])

const recLoading = ref(false)
const recError = ref('')
const recItems = ref([])
const recReason = ref('')

const typeLabelMap = { novel: '小说', poetry: '诗歌', essay: '散文', script: '剧本' }

onMounted(() => {
  fetchWorkInfo()
  loadSimilar()
  loadRecommend()
})

async function fetchWorkInfo() {
  const res = await api.get(`/api/works/public/${workId}`)
  if (res.code === 0) {
    workTitle.value = res.data.work?.title || res.data.title || ''
    typeLabel.value = typeLabelMap[res.data.work?.type || res.data.type] || ''
  }
}

async function generateReview() {
  reviewLoading.value = true
  reviewError.value = ''
  const res = await api.post('/api/review/generate', { work_id: parseInt(workId) })
  if (res.code === 0) {
    reviewText.value = res.data.review
    if (!workTitle.value) workTitle.value = res.data.work_title || ''
  } else {
    reviewError.value = res.msg || '生成失败'
  }
  reviewLoading.value = false
}

async function loadSimilar() {
  simLoading.value = true
  const res = await api.get(`/api/review/similar/${workId}`)
  if (res.code === 0) {
    similarWorks.value = res.data.items
  } else {
    simError.value = res.msg
  }
  simLoading.value = false
}

async function loadRecommend() {
  recLoading.value = true
  const res = await api.get('/api/review/recommend')
  if (res.code === 0) {
    recItems.value = res.data.items
    recReason.value = res.data.reason || ''
  } else {
    recError.value = res.msg
  }
  recLoading.value = false
}
</script>

<style scoped>
.review-header { display: flex; align-items: center; gap: var(--space-md); margin-bottom: var(--space-xl); flex-wrap: wrap; }
.review-header h2 { flex: 1; min-width: 0; }
.type-badge { font-size: 0.75rem; padding: 3px 10px; border-radius: var(--radius-full); background: rgba(196,163,90,0.15); color: var(--accent-primary); }

.section { padding: var(--space-lg); margin-bottom: var(--space-lg); }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-md); }
.section h3 { font-size: 1rem; color: var(--text-secondary); }

.review-content { font-size: 0.95rem; line-height: 1.9; color: var(--text-secondary); white-space: pre-wrap; }

.works-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: var(--space-md); }
.work-card { padding: var(--space-md); cursor: pointer; transition: all var(--transition-fast); }
.work-card:hover { border-color: var(--accent-primary); transform: translateY(-2px); }
.card-type { font-size: 0.65rem; color: var(--accent-primary); text-transform: uppercase; margin-bottom: var(--space-xs); }
.work-card h4 { margin-bottom: var(--space-sm); font-size: 0.95rem; }
.card-summary { font-size: 0.8rem; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: var(--space-sm); }
.card-meta { display: flex; gap: var(--space-md); font-size: 0.75rem; color: var(--text-muted); align-items: center; flex-wrap: wrap; }
.author { display: flex; align-items: center; gap: var(--space-xs); }
.avatar-dot { width: 18px; height: 18px; border-radius: 50%; background: var(--accent-primary); color: var(--bg-primary); display: flex; align-items: center; justify-content: center; font-size: 0.6rem; font-weight: 700; }

.rec-reason { font-size: 0.85rem; color: var(--accent-secondary); margin-bottom: var(--space-md); font-style: italic; }

.center { display: flex; justify-content: center; padding: var(--space-2xl); }
.error { color: var(--accent-red); }
.muted { color: var(--text-muted); }
</style>
