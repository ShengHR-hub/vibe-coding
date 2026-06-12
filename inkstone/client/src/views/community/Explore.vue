<template>
  <div class="page-container">
    <!-- 头部 -->
    <div class="explore-top">
      <div class="explore-header">
        <h2>社区广场</h2>
        <p class="header-sub">发现精彩创作，遇见同好作者</p>
      </div>
      <div class="search-bar">
        <span class="search-icon">&#9906;</span>
        <input v-model="searchQuery" placeholder="搜索作品、作者..." @keydown.enter="doSearch" />
        <button class="btn btn-primary btn-sm" @click="doSearch">搜索</button>
      </div>
    </div>

    <!-- 标签栏 -->
    <div class="tabs">
      <div v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }" @click="switchTab(tab.key)">
        <span class="tab-icon" v-html="tab.icon"></span>
        {{ tab.label }}
      </div>
    </div>

    <!-- 加载骨架屏 -->
    <div v-if="loading" class="works-grid">
      <div v-for="i in 6" :key="i" class="skeleton-card glass-card">
        <div class="sk-line sk-type"></div>
        <div class="sk-line sk-title"></div>
        <div class="sk-line sk-summary"></div>
        <div class="sk-line sk-meta"></div>
      </div>
    </div>

    <!-- 错误 -->
    <div v-else-if="errorMsg" class="center error">{{ errorMsg }}</div>

    <!-- 空状态 -->
    <div v-else-if="works.length === 0" class="empty-state">
      <span class="empty-icon">&#9733;</span>
      <p class="empty-title">暂无作品</p>
      <p class="empty-hint">成为第一个分享创作的人吧</p>
    </div>

    <!-- 作品网格 -->
    <div v-else class="works-grid">
      <div v-for="w in works" :key="w.work_id" class="work-card glass-card" :class="`type-${w.type}`" @click="$router.push(`/read/${w.work_id}`)">
        <div class="card-cover" :class="coverClass(w.type)"></div>
        <div class="card-body">
          <div class="card-type">{{ typeLabel(w.type) }}</div>
          <h3>{{ w.title }}</h3>
          <p v-if="w.summary" class="card-summary">{{ w.summary }}</p>
          <div class="card-meta">
            <span class="author">
              <span class="avatar-dot">{{ w.username?.charAt(0) }}</span>
              {{ w.username }}
            </span>
            <div class="meta-stats">
              <span class="meta-item">{{ (w.word_count || 0).toLocaleString() }} 字</span>
              <span class="meta-item">&#9825; {{ w.likes_count || 0 }}</span>
            </div>
          </div>
        </div>
        <div class="card-shimmer"></div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination">
      <button class="btn btn-ghost" :disabled="page <= 1" @click="page--; fetchData()">上一页</button>
      <span class="page-info">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
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
  { key: 'hot', label: '推荐', icon: '&#9733;' },
  { key: 'new', label: '最新', icon: '&#8635;' },
  { key: 'novel', label: '小说', icon: '&#9776;' },
  { key: 'poetry', label: '诗歌', icon: '&#10077;' },
  { key: 'essay', label: '散文', icon: '&#9998;' },
  { key: 'script', label: '剧本', icon: '&#9654;' },
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
  console.log('[Explore] switchTab:', key)
  activeTab.value = key
  page.value = 1
  searchQuery.value = ''
  fetchData()
}

function typeLabel(t) {
  return { novel: '小说', poetry: '诗歌', essay: '散文', script: '剧本' }[t] || t
}

function coverClass(t) {
  return t || 'default'
}
</script>

<style scoped>
/* ====== 头部 ====== */
.explore-top {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: var(--space-xl); flex-wrap: wrap; gap: var(--space-lg);
}
.explore-header h2 {
  font-family: var(--font-serif);
  font-size: 1.8rem; font-weight: 700;
  background: linear-gradient(135deg, #e8e6f0, #c4a35a);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.25rem;
}
.header-sub { font-size: 0.85rem; color: var(--text-muted); letter-spacing: 0.04em; }

.search-bar {
  display: flex; align-items: center; gap: 0;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(196,163,90,0.1);
  border-radius: var(--radius-full);
  overflow: hidden; transition: border-color 0.25s ease;
}
.search-bar:focus-within { border-color: rgba(196,163,90,0.35); box-shadow: 0 0 0 3px rgba(196,163,90,0.05); }
.search-icon { padding: 0 0 0 14px; color: var(--text-muted); font-size: 0.9rem; flex-shrink: 0; }
.search-bar input {
  padding: 9px 12px; font-size: 0.9rem; width: 220px;
  background: transparent; border: none; color: var(--text-primary);
  outline: none;
}
.search-bar input::placeholder { color: var(--text-muted); }
.search-bar .btn { border-radius: 0 var(--radius-full) var(--radius-full) 0; white-space: nowrap; padding: 9px 20px; }

/* ====== 标签 ====== */
.tabs { display: flex; gap: 4px; margin-bottom: var(--space-xl); border-bottom: 1px solid var(--border-glass); padding-bottom: var(--space-sm); overflow-x: auto; }
.tab {
  display: flex; align-items: center; gap: 5px;
  padding: 7px 18px; font-size: 0.85rem; color: var(--text-muted);
  background: none; border-radius: var(--radius-full); cursor: pointer;
  transition: all 0.25s ease; white-space: nowrap;
}
.tab:hover { color: var(--text-primary); background: rgba(255,255,255,0.03); }
.tab.active { color: var(--accent-primary); background: rgba(196,163,90,0.08); }
.tab-icon { font-size: 0.8rem; }

/* ====== 作品网格 ====== */
.works-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: var(--space-lg); }

.work-card {
  position: relative; overflow: hidden; cursor: pointer;
  transition: all 0.35s cubic-bezier(0.16,1,0.3,1);
  transform-style: preserve-3d;
  border-left: 3px solid rgba(196,163,90,0.15);
}
.work-card.type-novel  { border-left-color: rgba(196,163,90,0.15); }
.work-card.type-poetry { border-left-color: rgba(167, 139, 250, 0.2); }
.work-card.type-essay  { border-left-color: rgba(126, 200, 227, 0.2); }
.work-card.type-script { border-left-color: rgba(244, 132, 95, 0.2); }

.work-card:hover {
  border-left-color: var(--accent-primary);
  transform: translateY(-3px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.35), 0 0 0 1px rgba(196,163,90,0.1);
}

/* 卡片顶部色带 */
.card-cover {
  height: 4px;
  background: linear-gradient(90deg, var(--accent-primary), rgba(196,163,90,0.1));
}
.card-cover.poetry { background: linear-gradient(90deg, var(--accent-purple), rgba(167,139,250,0.1)); }
.card-cover.essay  { background: linear-gradient(90deg, var(--accent-cool), rgba(126,200,227,0.1)); }
.card-cover.script { background: linear-gradient(90deg, var(--accent-warm), rgba(244,132,95,0.1)); }

.card-body { padding: var(--space-lg); position: relative; z-index: 1; }
.card-type {
  display: inline-block; font-size: 0.68rem; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--accent-primary); opacity: 0.7;
  margin-bottom: var(--space-sm);
}
.work-card h3 { font-size: 1.05rem; margin-bottom: var(--space-sm); line-height: 1.4; }
.card-summary {
  font-size: 0.85rem; color: var(--text-secondary); line-height: 1.6;
  overflow: hidden; text-overflow: ellipsis; display: -webkit-box;
  -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  margin-bottom: var(--space-md);
}
.card-meta { display: flex; justify-content: space-between; align-items: center; }
.author { display: flex; align-items: center; gap: 6px; font-size: 0.82rem; color: var(--text-muted); }
.avatar-dot {
  width: 22px; height: 22px; border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  color: var(--bg-primary); display: flex; align-items: center; justify-content: center;
  font-size: 0.65rem; font-weight: 700;
}
.meta-stats { display: flex; gap: var(--space-md); font-size: 0.78rem; color: var(--text-muted); }
.meta-item { display: flex; align-items: center; gap: 3px; }

/* Shimmer 效果 */
.card-shimmer {
  position: absolute; top: 0; left: -100%;
  width: 60%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.015), transparent);
  transform: skewX(-20deg);
  transition: left 0.6s ease;
  pointer-events: none; z-index: 0;
}
.work-card:hover .card-shimmer { left: 150%; }

/* ====== 加载骨架屏 ====== */
.skeleton-card { padding: 0; overflow: hidden; }
.sk-line {
  height: 14px; border-radius: 4px;
  background: rgba(196,163,90,0.05);
  animation: skPulse 1.4s ease-in-out infinite;
  margin: 0 var(--space-lg);
}
.sk-type { width: 50px; margin-top: var(--space-lg); margin-bottom: var(--space-md); height: 10px; }
.sk-title { width: 70%; margin-bottom: var(--space-sm); }
.sk-summary { width: 90%; margin-bottom: var(--space-sm); }
.sk-meta { width: 55%; margin-bottom: var(--space-lg); }
@keyframes skPulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

/* ====== 空状态 ====== */
.empty-state {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 3rem 1rem; gap: 0.5rem;
}
.empty-icon { font-size: 2rem; color: var(--accent-primary); opacity: 0.25; }
.empty-title { font-size: 0.95rem; color: var(--text-secondary); font-weight: 600; letter-spacing: 0.04em; }
.empty-hint { font-size: 0.82rem; color: var(--text-muted); }

/* ====== 分页 ====== */
.center { display: flex; justify-content: center; padding: var(--space-2xl); }
.error { color: var(--accent-red); }
.pagination { display: flex; justify-content: center; align-items: center; gap: var(--space-md); margin-top: var(--space-xl); }
.page-info { font-size: 0.85rem; color: var(--text-muted); font-variant-numeric: tabular-nums; }

@media (max-width: 640px) {
  .explore-top { flex-direction: column; align-items: stretch; }
  .search-bar input { width: 100%; }
  .works-grid { grid-template-columns: 1fr; }
}
</style>
