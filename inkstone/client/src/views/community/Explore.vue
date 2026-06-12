<template>
  <div class="page-container">
    <div class="explore-header">
      <h2>社区广场</h2>
      <div class="search-bar">
        <input v-model="searchQuery" placeholder="搜索作品、作者..." @keydown.enter="doSearch" />
        <button class="btn btn-primary btn-sm" @click="doSearch">搜索</button>
      </div>
    </div>

    <div class="tabs">
      <button v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }" @click="switchTab(tab.key)">
        {{ tab.label }}
      </button>
    </div>

    <div v-if="loading" class="center"><LoadingSpinner /></div>
    <div v-else-if="errorMsg" class="center error">{{ errorMsg }}</div>
    <div v-else-if="works.length === 0" class="center muted">暂无作品</div>

    <div v-else class="works-grid">
      <div v-for="w in works" :key="w.work_id" class="work-card glass-card" @click="$router.push(`/read/${w.work_id}`)">
        <div class="card-type">{{ typeLabel(w.type) }}</div>
        <h3>{{ w.title }}</h3>
        <p v-if="w.summary" class="card-summary">{{ w.summary }}</p>
        <div class="card-meta">
          <span class="author">
            <span class="avatar-dot">{{ w.username?.charAt(0) }}</span>
            {{ w.username }}
          </span>
          <span>{{ w.word_count || 0 }} 字</span>
          <span>{{ w.likes_count || 0 }} 赞</span>
        </div>
      </div>
    </div>

    <div v-if="total > pageSize" class="pagination">
      <button class="btn btn-ghost" :disabled="page <= 1" @click="page--; fetchData()">上一页</button>
      <span>{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button class="btn btn-ghost" :disabled="page >= Math.ceil(total / pageSize)" @click="page++; fetchData()">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import LoadingSpinner from '../../components/LoadingSpinner.vue'

const router = useRouter()
const works = ref([])
const loading = ref(true)
const errorMsg = ref('')
const page = ref(1)
const total = ref(0)
const pageSize = 12
const activeTab = ref('hot')
const searchQuery = ref('')

const tabs = [
  { key: 'hot', label: '推荐' },
  { key: 'new', label: '最新' },
  { key: 'novel', label: '小说' },
  { key: 'poetry', label: '诗歌' },
  { key: 'essay', label: '散文' },
  { key: 'script', label: '剧本' },
]

onMounted(fetchData)

async function fetchData() {
  loading.value = true
  errorMsg.value = ''
  let url
  if (activeTab.value === 'hot' || activeTab.value === 'new') {
    url = `/api/community/feed?sort=${activeTab.value}&page=${page.value}&page_size=${pageSize}`
  } else {
    url = `/api/community/category/${activeTab.value}?page=${page.value}&page_size=${pageSize}`
  }
  const res = await api.get(url)
  if (res.code === 0) {
    works.value = res.data.items
    total.value = res.data.total
  } else {
    errorMsg.value = res.msg || '加载失败'
  }
  loading.value = false
}

async function doSearch() {
  const q = searchQuery.value.trim()
  if (!q) { switchTab('hot'); return }
  loading.value = true
  errorMsg.value = ''
  page.value = 1
  activeTab.value = ''
  const res = await api.get(`/api/community/search?q=${encodeURIComponent(q)}&page=${page.value}&page_size=${pageSize}`)
  if (res.code === 0) {
    works.value = res.data.items
    total.value = res.data.total
  } else {
    errorMsg.value = res.msg || '未找到结果'
  }
  loading.value = false
}

function switchTab(key) {
  activeTab.value = key
  page.value = 1
  searchQuery.value = ''
  fetchData()
}

function typeLabel(t) {
  return { novel: '小说', poetry: '诗歌', essay: '散文', script: '剧本' }[t] || t
}
</script>

<style scoped>
.explore-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-xl); flex-wrap: wrap; gap: var(--space-md); }
.search-bar { display: flex; gap: var(--space-sm); }
.search-bar input { padding: 6px 12px; font-size: 0.9rem; width: 240px; }
.tabs { display: flex; gap: var(--space-sm); margin-bottom: var(--space-xl); border-bottom: 1px solid var(--border-glass); padding-bottom: var(--space-sm); }
.tab { padding: 6px 16px; font-size: 0.9rem; color: var(--text-muted); background: none; border-radius: var(--radius-sm); transition: all var(--transition-fast); }
.tab:hover { color: var(--text-secondary); }
.tab.active { color: var(--accent-primary); background: var(--bg-glass); }
.works-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: var(--space-lg); }
.work-card { padding: var(--space-lg); cursor: pointer; transition: all var(--transition-fast); }
.work-card:hover { border-color: var(--accent-primary); transform: translateY(-2px); }
.card-type { font-size: 0.7rem; color: var(--accent-primary); text-transform: uppercase; margin-bottom: var(--space-sm); }
.work-card h3 { margin-bottom: var(--space-sm); font-size: 1.1rem; }
.card-summary { font-size: 0.85rem; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: var(--space-md); }
.card-meta { display: flex; gap: var(--space-md); font-size: 0.8rem; color: var(--text-muted); align-items: center; }
.author { display: flex; align-items: center; gap: var(--space-xs); }
.avatar-dot { width: 20px; height: 20px; border-radius: 50%; background: var(--accent-primary); color: var(--bg-primary); display: flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 700; }
.center { display: flex; justify-content: center; padding: var(--space-2xl); }
.error { color: var(--accent-red); }
.muted { color: var(--text-muted); }
.pagination { display: flex; justify-content: center; align-items: center; gap: var(--space-md); margin-top: var(--space-xl); }
</style>
