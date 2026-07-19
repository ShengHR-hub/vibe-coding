<template>
  <div class="page-container">
    <ReadingNav v-if="from === 'reading'" />
    <NavBar v-else />
    <!-- 头部 -->
    <div class="library-top">
      <div class="library-header">
        <h2>墨池书库</h2>
        <p class="header-sub">探索万千作品，沉浸阅读世界</p>
      </div>
      <div class="search-bar">
        <span class="search-icon">&#9906;</span>
        <input v-model="searchQuery" placeholder="搜索书名、作者..." @keydown.enter="doSearch" />
        <select v-model="filterType" class="type-select" @change="onTypeChange">
          <option value="">全部类型</option>
          <option v-for="t in categories.types" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
        <button class="btn btn-primary btn-sm" @click="doSearch">搜索</button>
      </div>
    </div>

    <!-- 精选推荐 -->
    <section v-if="featured.length" class="section-featured">
      <h3 class="section-title">精选推荐</h3>
      <div class="featured-scroll">
        <div v-for="(book, fIdx) in featured" :key="book.source + '-' + book.book_id"
             class="featured-card glass-card" @click="goDetail(book)">
          <div class="featured-cover" :class="coverClass(book.type)">
            <span class="featured-rank">{{ fIdx + 1 }}</span>
          </div>
          <div class="featured-info">
            <h4>{{ book.title }}</h4>
            <p class="featured-author">{{ book.author }}</p>
            <div class="featured-meta">
              <span>{{ formatWordCount(book.word_count) }}</span>
              <span v-if="book.rating_avg > 0">&#9733; {{ book.rating_avg }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 排行榜 -->
    <section class="section-rankings">
      <div class="section-header">
        <h3 class="section-title">排行榜</h3>
        <div class="rank-tabs">
          <button v-for="tab in rankTabs" :key="tab.key"
                  class="rank-tab" :class="{ active: rankSort === tab.key }"
                  @click="rankSort = tab.key; fetchRankings()">
            {{ tab.label }}
          </button>
        </div>
      </div>
      <div v-if="rankings.length" class="rank-list">
        <div v-for="(book, idx) in rankings" :key="book.source + '-' + book.book_id"
             class="rank-item glass-card" @click="goDetail(book)">
          <span class="rank-num" :class="{ top: idx < 3 }">{{ idx + 1 }}</span>
          <div class="rank-info">
            <h4>{{ book.title }}</h4>
            <span class="rank-author">{{ book.author }}</span>
          </div>
          <div class="rank-stats">
            <span class="stat-views">{{ formatWordCount(book.views) }} 阅读</span>
            <span v-if="book.rating_avg > 0" class="stat-rating">&#9733; {{ book.rating_avg }}</span>
          </div>
        </div>
      </div>
      <div v-else class="empty-hint">暂无排行数据</div>
    </section>

    <!-- 标签筛选 -->
    <div class="tabs">
      <div class="tab" :class="{ active: activeSort === 'hot' }" @click="switchSort('hot')">热门</div>
      <div class="tab" :class="{ active: activeSort === 'new' }" @click="switchSort('new')">最新</div>
      <div class="tab" :class="{ active: activeSort === 'rating' }" @click="switchSort('rating')">评分</div>
    </div>

    <!-- 加载骨架屏 -->
    <div v-if="loading" class="books-grid">
      <div v-for="i in 6" :key="i" class="skeleton-card glass-card">
        <div class="sk-line sk-cover"></div>
        <div class="sk-line sk-title"></div>
        <div class="sk-line sk-meta"></div>
      </div>
    </div>

    <!-- 错误 -->
    <div v-else-if="errorMsg" class="center error">{{ errorMsg }}</div>

    <!-- 空状态 -->
    <div v-else-if="books.length === 0" class="empty-state">
      <span class="empty-icon">&#128214;</span>
      <p class="empty-title">暂无书籍</p>
      <p class="empty-hint">书库正在建设中，敬请期待</p>
    </div>

    <!-- 书籍网格 -->
    <div v-else class="books-grid">
      <div v-for="book in books" :key="book.source + '-' + book.book_id"
           class="book-card glass-card" :class="`type-${book.type}`" @click="goDetail(book)">
        <div class="card-cover" :class="coverClass(book.type)"></div>
        <div class="card-body">
          <div class="card-type">{{ typeLabel(book.type) }}</div>
          <h3>{{ book.title }}</h3>
          <p class="card-author">{{ book.author }}</p>
          <p v-if="book.summary" class="card-summary">{{ book.summary }}</p>
          <div class="card-meta">
            <span class="meta-item">{{ formatWordCount(book.word_count) }} 字</span>
            <span class="meta-item">{{ book.chapter_count || 0 }} 章</span>
            <span v-if="book.rating_avg > 0" class="meta-item">&#9733; {{ book.rating_avg }}</span>
            <span class="meta-item">&#9825; {{ book.favorites_count || 0 }}</span>
          </div>
        </div>
        <div class="card-source-badge" v-if="book.source === 'work'">原创</div>
        <button v-if="userStore.isLoggedIn && book.owner_id === userStore.user?.user_id"
                class="card-delete-btn" @mousedown.stop @click.stop="confirmDelete(book, $event)" title="删除">&#10005;</button>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
      <div class="modal glass-card">
        <h3>确认删除</h3>
        <p>确定要删除「{{ deleteTarget?.title }}」吗？此操作不可撤销。</p>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showDeleteConfirm = false">取消</button>
          <button class="btn btn-danger" @click="doDelete" :disabled="deleting">{{ deleting ? '删除中...' : '确认删除' }}</button>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination">
      <button class="btn btn-ghost" :disabled="page <= 1" @click="page--; fetchBooks()">上一页</button>
      <span class="page-info">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button class="btn btn-ghost" :disabled="page >= Math.ceil(total / pageSize)" @click="page++; fetchBooks()">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import { useUserStore } from '../../stores/user.js'
import { useToast } from '../../composables/useToast.js'
import NavBar from '../../components/NavBar.vue'
import ReadingNav from '../../components/ReadingNav.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const toast = useToast()
const from = computed(() => route.query.from || 'write')

// 数据
const books = ref([])
const featured = ref([])
const rankings = ref([])
const categories = ref({ tags: [], types: [] })
const loading = ref(true)
const errorMsg = ref('')
const total = ref(0)

// 筛选
const page = ref(1)
const pageSize = 12
const activeSort = ref('hot')
const filterType = ref('')
const searchQuery = ref('')
const rankSort = ref('hot')

// 删除
const showDeleteConfirm = ref(false)
const deleteTarget = ref(null)
const deleting = ref(false)

const rankTabs = [
  { key: 'hot', label: '热度' },
  { key: 'rating', label: '评分' },
  { key: 'new', label: '新书' },
]

onMounted(async () => {
  await Promise.all([
    fetchBooks(),
    fetchFeatured(),
    fetchRankings(),
    fetchCategories(),
  ])
})

async function fetchBooks() {
  loading.value = true
  errorMsg.value = ''
  const params = new URLSearchParams({
    page: page.value,
    page_size: pageSize,
    sort: activeSort.value,
  })
  if (filterType.value) params.set('type', filterType.value)
  const res = await api.get(`/api/library?${params}`)
  if (res.code === 0) {
    books.value = res.data.items
    total.value = res.data.total
  } else {
    errorMsg.value = res.msg || '加载失败'
  }
  loading.value = false
}

async function fetchFeatured() {
  const res = await api.get('/api/library/featured')
  if (res.code === 0) featured.value = res.data.items
}

async function fetchRankings() {
  const res = await api.get(`/api/library/rankings?sort=${rankSort.value}&limit=8`)
  if (res.code === 0) {
    // 合并两个来源，按热度/评分/时间重新排序取前8
    const combined = [...(res.data.library || []), ...(res.data.works || [])]
    if (rankSort.value === 'hot') {
      combined.sort((a, b) => (b.views || 0) - (a.views || 0))
    } else if (rankSort.value === 'rating') {
      combined.sort((a, b) => (b.rating_avg || 0) - (a.rating_avg || 0))
    } else {
      combined.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
    }
    rankings.value = combined.slice(0, 8)
  }
}

async function fetchCategories() {
  const res = await api.get('/api/library/categories')
  if (res.code === 0) categories.value = res.data
}

async function doSearch() {
  const q = searchQuery.value.trim()
  if (!q) { switchSort('hot'); return }
  loading.value = true
  errorMsg.value = ''
  page.value = 1
  const params = new URLSearchParams({ q, page: 1, page_size: pageSize })
  if (filterType.value) params.set('type', filterType.value)
  const res = await api.get(`/api/library/search?${params}`)
  if (res.code === 0) {
    books.value = res.data.items
    total.value = res.data.total
  } else {
    errorMsg.value = res.msg || '未找到结果'
  }
  loading.value = false
}

function switchSort(sort) {
  activeSort.value = sort
  page.value = 1
  searchQuery.value = ''
  fetchBooks()
}

function onTypeChange() {
  page.value = 1
  if (searchQuery.value.trim()) {
    doSearch()
  } else {
    fetchBooks()
  }
}

function goDetail(book) {
  router.push(`/library/${book.source}/${book.book_id}?from=${from.value}`)
}

function typeLabel(t) {
  return { novel: '小说', poetry: '诗歌', essay: '散文', webfiction: '网文', script: '剧本' }[t] || t
}

function coverClass(t) {
  return t || 'default'
}

function confirmDelete(book, event) {
  if (event) {
    event.stopPropagation()
    event.preventDefault()
  }
  deleteTarget.value = book
  showDeleteConfirm.value = true
}

async function doDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  const book = deleteTarget.value
  const res = await api.delete(`/api/library/${book.book_id}?source=${book.source}`)
  deleting.value = false
  showDeleteConfirm.value = false
  if (res.code === 0) {
    toast.success('已删除')
    fetchBooks()
  } else {
    toast.error(res.msg || '删除失败')
  }
}

function formatWordCount(wc) {
  if (!wc) return '0'
  if (wc >= 10000) return (wc / 10000).toFixed(1) + '万'
  return wc.toLocaleString()
}
</script>

<style scoped>
.page-container { }
/* ====== 头部 ====== */
.library-top {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: var(--space-xl); flex-wrap: wrap; gap: var(--space-lg);
}
.library-header h2 {
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
  padding: 9px 12px; font-size: 0.9rem; width: 180px;
  background: transparent; border: none; color: var(--text-primary);
  outline: none;
}
.search-bar input::placeholder { color: var(--text-muted); }
.type-select {
  padding: 9px 10px; font-size: 0.82rem; width: auto;
  background: rgba(255,255,255,0.03); border: none; border-left: 1px solid rgba(196,163,90,0.1);
  border-radius: 0; color: var(--text-secondary); cursor: pointer;
}
.type-select option { background: var(--bg-primary); color: var(--text-primary); }
.search-bar .btn { border-radius: 0 var(--radius-full) var(--radius-full) 0; white-space: nowrap; padding: 9px 20px; }

/* ====== 精选推荐 ====== */
.section-featured { margin-bottom: var(--space-2xl); }
.section-title {
  font-family: var(--font-serif); font-size: 1.15rem; font-weight: 600;
  color: var(--text-primary); margin-bottom: var(--space-lg);
  padding-left: var(--space-md);
  border-left: 3px solid var(--accent-primary);
}
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-lg); }
.section-header .section-title { margin-bottom: 0; }

.featured-scroll {
  display: flex; gap: var(--space-lg); overflow-x: auto;
  padding-bottom: var(--space-sm); scroll-snap-type: x mandatory;
  -ms-overflow-style: none; scrollbar-width: none;
}
.featured-scroll::-webkit-scrollbar { display: none; }

.featured-card {
  flex: 0 0 260px; scroll-snap-align: start;
  display: flex; gap: var(--space-md); padding: var(--space-md);
  cursor: pointer; transition: all 0.3s ease;
}
.featured-card:hover { transform: translateY(-2px); border-color: rgba(196,163,90,0.3); }

.featured-cover {
  width: 60px; height: 80px; border-radius: var(--radius-sm);
  background: linear-gradient(135deg, rgba(196,163,90,0.15), rgba(196,163,90,0.05));
  flex-shrink: 0; display: flex; align-items: flex-start; justify-content: flex-end;
  padding: 4px; position: relative; overflow: hidden;
}
.featured-cover::after {
  content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--accent-primary), transparent);
}
.featured-cover.poetry { background: linear-gradient(135deg, rgba(167,139,250,0.15), rgba(167,139,250,0.05)); }
.featured-cover.poetry::after { background: linear-gradient(90deg, var(--accent-purple), transparent); }
.featured-cover.essay { background: linear-gradient(135deg, rgba(126,200,227,0.15), rgba(126,200,227,0.05)); }
.featured-cover.essay::after { background: linear-gradient(90deg, var(--accent-cool), transparent); }

.featured-rank {
  font-size: 0.7rem; font-weight: 700; color: var(--accent-primary);
  background: rgba(0,0,0,0.4); border-radius: 50%; width: 20px; height: 20px;
  display: flex; align-items: center; justify-content: center;
}
.featured-info { flex: 1; min-width: 0; }
.featured-info h4 {
  font-size: 0.92rem; font-weight: 600; margin-bottom: 2px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.featured-author { font-size: 0.78rem; color: var(--text-muted); margin-bottom: 4px; }
.featured-meta { font-size: 0.72rem; color: var(--text-muted); display: flex; gap: 8px; }

/* ====== 排行榜 ====== */
.section-rankings { margin-bottom: var(--space-2xl); }
.rank-tabs { display: flex; gap: 4px; }
.rank-tab {
  padding: 4px 14px; font-size: 0.78rem; color: var(--text-muted);
  background: none; border-radius: var(--radius-full); cursor: pointer;
  transition: all 0.2s ease;
}
.rank-tab:hover { color: var(--text-primary); background: rgba(255,255,255,0.03); }
.rank-tab.active { color: var(--accent-primary); background: rgba(196,163,90,0.08); }

.rank-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: var(--space-sm); }
.rank-item {
  display: flex; align-items: center; gap: var(--space-md);
  padding: var(--space-sm) var(--space-md); cursor: pointer;
  transition: all 0.25s ease; border-left: 3px solid transparent;
}
.rank-item:hover { border-left-color: var(--accent-primary); background: rgba(196,163,90,0.03); }
.rank-num {
  font-size: 0.85rem; font-weight: 700; color: var(--text-muted);
  width: 24px; text-align: center; flex-shrink: 0;
}
.rank-num.top { color: var(--accent-primary); }
.rank-info { flex: 1; min-width: 0; }
.rank-info h4 { font-size: 0.88rem; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rank-author { font-size: 0.75rem; color: var(--text-muted); }
.rank-stats { text-align: right; flex-shrink: 0; }
.stat-views { font-size: 0.72rem; color: var(--text-muted); display: block; }
.stat-rating { font-size: 0.72rem; color: var(--accent-primary); }

.empty-hint { font-size: 0.85rem; color: var(--text-muted); text-align: center; padding: var(--space-xl) 0; }

/* ====== 标签 ====== */
.tabs {
  display: flex; gap: 4px; margin-bottom: var(--space-xl);
  border-bottom: 1px solid var(--border-glass); padding-bottom: var(--space-sm);
}
.tab {
  padding: 7px 18px; font-size: 0.85rem; color: var(--text-muted);
  background: none; border-radius: var(--radius-full); cursor: pointer;
  transition: all 0.25s ease; white-space: nowrap;
}
.tab:hover { color: var(--text-primary); background: rgba(255,255,255,0.03); }
.tab.active { color: var(--accent-primary); background: rgba(196,163,90,0.08); }

/* ====== 骨架屏 ====== */
.skeleton-card { padding: var(--space-lg); }
.sk-line { height: 12px; border-radius: var(--radius-sm); background: rgba(255,255,255,0.04); margin-bottom: var(--space-sm); }
.sk-cover { height: 140px; border-radius: var(--radius-md); margin-bottom: var(--space-md); }
.sk-title { width: 70%; }
.sk-meta { width: 50%; }

/* ====== 空状态 ====== */
.empty-state { text-align: center; padding: var(--space-2xl) 0; }
.empty-icon { font-size: 2.5rem; display: block; margin-bottom: var(--space-md); }
.empty-title { font-size: 1.1rem; color: var(--text-primary); margin-bottom: var(--space-sm); }

/* ====== 书籍网格 ====== */
.books-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--space-lg); }

.book-card {
  position: relative; overflow: hidden; cursor: pointer;
  transition: all 0.35s cubic-bezier(0.16,1,0.3,1);
  border-left: 3px solid rgba(196,163,90,0.15);
}
.book-card.type-novel  { border-left-color: rgba(196,163,90,0.15); }
.book-card.type-poetry { border-left-color: rgba(167,139,250,0.2); }
.book-card.type-essay  { border-left-color: rgba(126,200,227,0.2); }
.book-card.type-webfiction { border-left-color: rgba(244,132,95,0.2); }

.book-card:hover {
  border-left-color: var(--accent-primary);
  transform: translateY(-3px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.35), 0 0 0 1px rgba(196,163,90,0.1);
}

.card-cover {
  height: 4px;
  background: linear-gradient(90deg, var(--accent-primary), rgba(196,163,90,0.1));
}
.card-cover.poetry { background: linear-gradient(90deg, var(--accent-purple), rgba(167,139,250,0.1)); }
.card-cover.essay  { background: linear-gradient(90deg, var(--accent-cool), rgba(126,200,227,0.1)); }
.card-cover.webfiction { background: linear-gradient(90deg, var(--accent-warm), rgba(244,132,95,0.1)); }

.card-body { padding: var(--space-lg); position: relative; z-index: 1; }
.card-type {
  display: inline-block; font-size: 0.68rem; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--accent-primary); opacity: 0.7;
  margin-bottom: var(--space-sm);
}
.book-card h3 { font-size: 1.05rem; margin-bottom: 4px; line-height: 1.4; }
.card-author { font-size: 0.82rem; color: var(--text-muted); margin-bottom: var(--space-sm); }
.card-summary {
  font-size: 0.82rem; color: var(--text-secondary); line-height: 1.5;
  overflow: hidden; text-overflow: ellipsis; display: -webkit-box;
  -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  margin-bottom: var(--space-md);
}
.card-meta { display: flex; gap: var(--space-md); flex-wrap: wrap; }
.meta-item { font-size: 0.75rem; color: var(--text-muted); }

.card-source-badge {
  position: absolute; top: var(--space-md); right: var(--space-md);
  font-size: 0.6rem; font-weight: 600; letter-spacing: 0.06em;
  color: var(--accent-primary); background: rgba(196,163,90,0.1);
  padding: 2px 8px; border-radius: var(--radius-full);
  border: 1px solid rgba(196,163,90,0.2);
}
.card-delete-btn {
  position: absolute; top: var(--space-md); left: var(--space-md);
  width: 28px; height: 28px; border-radius: 50%;
  background: rgba(239,68,68,0.15); color: #ef4444;
  border: 1px solid rgba(239,68,68,0.3);
  font-size: 0.75rem; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: all 0.2s ease;
  z-index: 10;
}
.book-card:hover .card-delete-btn { opacity: 1; }
.card-delete-btn:hover {
  background: rgba(239,68,68,0.3); transform: scale(1.1);
}

/* 删除弹窗 */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 200;
}
.modal {
  width: 400px; padding: var(--space-xl);
  display: flex; flex-direction: column; gap: var(--space-md);
}
.modal h3 { margin-bottom: var(--space-sm); }
.modal p { font-size: 0.9rem; color: var(--text-secondary); line-height: 1.6; }
.modal-actions { display: flex; justify-content: flex-end; gap: var(--space-md); }
.btn-danger { background: var(--accent-red); color: #fff; border: none; padding: 8px 20px; border-radius: var(--radius-sm); cursor: pointer; }
.btn-danger:hover { opacity: 0.85; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }

/* ====== 分页 ====== */
.pagination {
  display: flex; justify-content: center; align-items: center; gap: var(--space-lg);
  margin-top: var(--space-2xl); padding-top: var(--space-lg);
  border-top: 1px solid var(--border-glass);
}
.page-info { font-size: 0.85rem; color: var(--text-muted); }
.center { text-align: center; padding: var(--space-2xl) 0; }
.error { color: #ef4444; }

/* ====== 响应式 ====== */
@media (max-width: 768px) {
  .library-top { flex-direction: column; align-items: stretch; }
  .search-bar { flex-wrap: wrap; border-radius: var(--radius-md); }
  .search-bar input { width: 100%; }
  .type-select { border-left: none; border-top: 1px solid rgba(196,163,90,0.1); }
  .featured-card { flex: 0 0 220px; }
  .rank-list { grid-template-columns: 1fr; }
  .books-grid { grid-template-columns: 1fr; }
}
</style>
