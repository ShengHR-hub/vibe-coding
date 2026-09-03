<template>
  <div class="page-container">
    <!-- 头部 -->
    <div class="poems-header">
      <div class="header-left">
        <h2>诗词库</h2>
        <p class="header-sub">精选古典诗词，写作灵感源泉</p>
      </div>
      <div class="search-bar">
        <span class="search-icon">&#9906;</span>
        <input v-model="searchQuery" placeholder="搜索诗词、作者..." @keydown.enter="doSearch" />
        <button class="btn btn-primary btn-sm" @click="doSearch">搜索</button>
      </div>
    </div>

    <!-- 分类标签 -->
    <div class="category-tabs">
      <div class="cat-tab realtime-tab" :class="{ active: isRealtime }" @click="fetchRealtime">
        <span class="cat-icon">⚡</span>
        <span class="cat-name">实时推荐</span>
      </div>
      <div
        v-for="cat in categories"
        :key="cat.category"
        class="cat-tab"
        :class="{ active: activeCategory === cat.category }"
        @click="selectCategory(cat.category)"
      >
        <span class="cat-icon">{{ catIcons[cat.category] || ' ' }}</span>
        <span class="cat-name">{{ cat.category }}</span>
        <span class="cat-count">{{ cat.count }}</span>
      </div>
    </div>

    <!-- 加载 -->
    <div v-if="loading" class="poems-grid">
      <div v-for="i in 8" :key="i" class="skeleton-card glass-card">
        <div class="sk-line sk-title"></div>
        <div class="sk-line sk-author"></div>
        <div class="sk-line sk-content"></div>
      </div>
    </div>

    <!-- 搜索结果提示 -->
    <div v-else-if="searchKeyword" class="search-result-info">
      <span>搜索 "{{ searchKeyword }}" 的结果（{{ total }} 首）</span>
      <button class="btn btn-ghost btn-sm" @click="clearSearch">清除搜索</button>
    </div>

    <!-- 诗词列表 -->
    <div v-else-if="poems.length > 0" class="poems-grid">
      <div v-for="(poem, idx) in poems" :key="poem.poem_id || `rt-${idx}`" class="poem-card glass-card" :class="{ 'realtime-card': poem._realtime }" @click="openDetail(poem)">
        <div class="poem-category-badge" :class="{ 'realtime-badge': poem._realtime }">{{ poem._realtime ? '实时' : poem.category }}</div>
        <h3 class="poem-title">{{ poem.title }}</h3>
        <p class="poem-author" v-if="poem.dynasty">〔{{ poem.dynasty }}〕{{ poem.author }}</p>
        <p class="poem-author" v-else>{{ poem.author }}</p>
        <div class="poem-preview">{{ previewText(poem.content) }}</div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <span class="empty-icon"> </span>
      <p class="empty-title">暂无诗词</p>
      <p class="empty-hint">换个关键词试试</p>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination">
      <button class="btn btn-ghost btn-sm" :disabled="page <= 1" @click="changePage(page - 1)">上一页</button>
      <span class="page-info">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button class="btn btn-ghost btn-sm" :disabled="page >= Math.ceil(total / pageSize)" @click="changePage(page + 1)">下一页</button>
    </div>

    <!-- 详情弹窗 -->
    <teleport to="body">
      <transition name="fade">
        <div v-if="detailPoem" class="poem-overlay" @click.self="detailPoem = null">
          <div class="poem-detail glass-card">
            <button class="close-btn" @click="detailPoem = null">&times;</button>
            <div class="detail-category">{{ detailPoem._realtime ? '实时推荐 · ' + detailPoem.category : detailPoem.category }}</div>
            <h2 class="detail-title">{{ detailPoem.title }}</h2>
            <p class="detail-author" v-if="detailPoem.dynasty">〔{{ detailPoem.dynasty }}〕{{ detailPoem.author }}</p>
            <p class="detail-author" v-else>{{ detailPoem.author }}</p>
            <div class="detail-content">{{ detailPoem.content }}</div>
            <div class="detail-actions">
              <button class="btn btn-outline btn-sm" @click="copyPoem(detailPoem)">复制全文</button>
              <button v-if="detailPoem._realtime" class="btn btn-primary btn-sm" @click="saveRealtime(detailPoem)" :disabled="saving">
                {{ saving ? '保存中...' : '收藏到诗词库' }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/index.js'

import { useToast } from '../../composables/useToast.js'
const toast = useToast()
const poems = ref([])
const categories = ref([])
const loading = ref(true)
const activeCategory = ref('')
const searchQuery = ref('')
const searchKeyword = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)
const detailPoem = ref(null)
const isRealtime = ref(false)
const saving = ref(false)

const catIcons = {
  '写景': ' ',
  '写人': ' ',
  '离别': ' ',
  '思乡': ' ',
  '战争': '⚔️',
  '咏物': ' ',
}

onMounted(async () => {
  await Promise.all([loadCategories(), loadPoems()])
})

async function loadCategories() {
  const res = await api.get('/api/poems/categories')
  if (res.code === 0) categories.value = res.data.categories
}

async function loadPoems() {
  loading.value = true
  let url = `/api/poems?page=${page.value}&page_size=${pageSize}`
  if (activeCategory.value) url += `&category=${encodeURIComponent(activeCategory.value)}`
  const res = await api.get(url)
  if (res.code === 0) {
    poems.value = res.data.poems
    total.value = res.data.total
  }
  loading.value = false
}

async function doSearch() {
  const q = searchQuery.value.trim()
  if (!q) return
  searchKeyword.value = q
  page.value = 1
  loading.value = true
  const res = await api.get(`/api/poems/search?q=${encodeURIComponent(q)}&page=1&page_size=${pageSize}`)
  if (res.code === 0) {
    poems.value = res.data.poems
    total.value = res.data.total
  }
  loading.value = false
}

function clearSearch() {
  searchQuery.value = ''
  searchKeyword.value = ''
  page.value = 1
  loadPoems()
}

function selectCategory(cat) {
  activeCategory.value = activeCategory.value === cat ? '' : cat
  searchKeyword.value = ''
  searchQuery.value = ''
  isRealtime.value = false
  page.value = 1
  loadPoems()
}

async function fetchRealtime() {
  if (isRealtime.value) {
    // Already in realtime mode, fetch another batch
  }
  isRealtime.value = true
  activeCategory.value = ''
  searchKeyword.value = ''
  searchQuery.value = ''
  loading.value = true
  const res = await api.get('/api/poems/realtime?count=8')
  if (res.code === 0) {
    poems.value = res.data.poems.map(p => ({ ...p, _realtime: true }))
    total.value = poems.value.length
  } else {
    toast.error(res.msg || '获取实时诗词失败')
  }
  loading.value = false
}

async function saveRealtime(poem) {
  saving.value = true
  const res = await api.post('/api/poems/save', {
    title: poem.title,
    author: poem.author,
    content: poem.content,
    category: poem.category,
  })
  saving.value = false
  if (res.code === 0) {
    toast.success(res.data.msg || '已收藏')
    poem._realtime = false
    poem.poem_id = res.data.poem_id
  } else {
    toast.error(res.msg || '收藏失败')
  }
}

function changePage(p) {
  page.value = p
  if (searchKeyword.value) {
    doSearch()
  } else {
    loadPoems()
  }
}

function openDetail(poem) {
  detailPoem.value = poem
}

function previewText(content) {
  if (!content) return ''
  const lines = content.split('\n')
  return lines.slice(0, 3).join('；') + (lines.length > 3 ? '……' : '')
}

async function copyPoem(poem) {
  const authorLine = poem.dynasty ? `〔${poem.dynasty}〕${poem.author}` : poem.author
  const text = `${poem.title}\n${authorLine}\n\n${poem.content}`
  try {
    await navigator.clipboard.writeText(text)
    toast.success('已复制到剪贴板')
  } catch {
    toast.error('复制失败，请手动选择复制')
  }
}
</script>

<style scoped>
.poems-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: var(--space-xl); flex-wrap: wrap; gap: var(--space-md);
}
.header-left h2 { font-size: 1.8rem; margin-bottom: 4px; }
.header-sub { color: var(--text-muted); font-size: 0.9rem; }

.search-bar {
  display: flex; align-items: center; gap: var(--space-sm);
  background: var(--bg-glass); border: 1px solid var(--border-glass);
  border-radius: var(--radius-full); padding: 4px 12px;
}
.search-icon { color: var(--text-muted); font-size: 0.9rem; }
.search-bar input {
  background: none; border: none; outline: none;
  color: var(--text-primary); font-size: 0.9rem;
  width: 200px; padding: 6px 4px;
}

.category-tabs {
  display: flex; gap: var(--space-sm); margin-bottom: var(--space-xl);
  overflow-x: auto; padding-bottom: var(--space-sm);
}
.cat-tab {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 16px; border-radius: var(--radius-full);
  background: var(--bg-glass); border: 1px solid var(--border-glass);
  cursor: pointer; transition: all 0.25s ease;
  white-space: nowrap; font-size: 0.85rem;
}
.cat-tab:hover { border-color: var(--accent-primary); color: var(--text-primary); }
.cat-tab.active {
  background: rgba(196, 163, 90, 0.15);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}
.cat-icon { font-size: 1rem; }
.cat-count { font-size: 0.75rem; color: var(--text-muted); }
.realtime-tab {
  border-color: rgba(255, 140, 50, 0.3);
  background: rgba(255, 140, 50, 0.06);
}
.realtime-tab.active {
  background: rgba(255, 140, 50, 0.15);
  border-color: #ff8c32;
  color: #ff8c32;
}

.search-result-info {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: var(--space-lg); font-size: 0.9rem; color: var(--text-secondary);
}

.poems-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-lg);
}
.skeleton-card { height: 160px; padding: var(--space-lg); }
.sk-line { height: 12px; border-radius: 6px; background: var(--bg-glass); margin-bottom: var(--space-sm); }
.sk-title { width: 60%; }
.sk-author { width: 40%; }
.sk-content { width: 90%; }

.poem-card {
  padding: var(--space-lg); cursor: pointer;
  transition: all 0.3s ease; position: relative;
}
.poem-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(196, 163, 90, 0.12);
  border-color: rgba(196, 163, 90, 0.3);
}
.poem-category-badge {
  position: absolute; top: var(--space-md); right: var(--space-md);
  font-size: 0.7rem; padding: 2px 8px;
  border-radius: var(--radius-full);
  background: rgba(196, 163, 90, 0.1);
  color: var(--accent-primary);
}
.realtime-card {
  border-color: rgba(255, 140, 50, 0.15);
}
.realtime-card:hover {
  border-color: rgba(255, 140, 50, 0.4);
  box-shadow: 0 8px 32px rgba(255, 140, 50, 0.1);
}
.realtime-badge {
  background: rgba(255, 140, 50, 0.12);
  color: #ff8c32;
}
.poem-title {
  font-family: var(--font-serif);
  font-size: 1.15rem; margin-bottom: var(--space-xs);
  color: var(--text-primary);
}
.poem-author {
  font-size: 0.82rem; color: var(--text-muted);
  margin-bottom: var(--space-md);
}
.poem-preview {
  font-family: var(--font-serif);
  font-size: 0.9rem; line-height: 1.8;
  color: var(--text-secondary);
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.empty-state {
  text-align: center; padding: var(--space-2xl) 0;
}
.empty-icon { font-size: 3rem; display: block; margin-bottom: var(--space-md); }
.empty-title { font-size: 1.2rem; color: var(--text-primary); margin-bottom: var(--space-xs); }
.empty-hint { color: var(--text-muted); font-size: 0.9rem; }

.pagination {
  display: flex; justify-content: center; align-items: center;
  gap: var(--space-lg); margin-top: var(--space-2xl);
}
.page-info { font-size: 0.85rem; color: var(--text-muted); }

/* 详情弹窗 */
.poem-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
  padding: var(--space-xl);
}
.poem-detail {
  max-width: 560px; width: 100%;
  padding: var(--space-2xl);
  position: relative;
  max-height: 80vh; overflow-y: auto;
}
.close-btn {
  position: absolute; top: var(--space-md); right: var(--space-md);
  background: none; border: none; font-size: 1.5rem;
  color: var(--text-muted); cursor: pointer;
  transition: color 0.2s;
}
.close-btn:hover { color: var(--text-primary); }
.detail-category {
  font-size: 0.8rem; color: var(--accent-primary);
  margin-bottom: var(--space-sm);
}
.detail-title {
  font-family: var(--font-serif);
  font-size: 1.6rem; margin-bottom: var(--space-sm);
}
.detail-author {
  font-size: 0.9rem; color: var(--text-muted);
  margin-bottom: var(--space-xl);
}
.detail-content {
  font-family: var(--font-serif);
  font-size: 1.1rem; line-height: 2.2;
  color: var(--text-primary);
  white-space: pre-line;
  margin-bottom: var(--space-xl);
}
.detail-actions {
  display: flex; justify-content: flex-end;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
