<template>
  <div class="page-container">
    <!-- 头部 -->
    <div class="ml-header">
      <div class="header-left">
        <h2>素材库</h2>
        <p class="header-sub">成语典故、名言金句、场景描写，写作素材一站获取</p>
      </div>
      <div class="search-bar">
        <span class="search-icon">&#9906;</span>
        <input v-model="searchQuery" placeholder="搜索素材..." @keydown.enter="doSearch" />
        <button class="btn btn-primary btn-sm" @click="doSearch">搜索</button>
      </div>
    </div>

    <!-- 分类标签 -->
    <div class="category-tabs">
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
    <div v-if="loading" class="materials-grid">
      <div v-for="i in 6" :key="i" class="skeleton-card glass-card">
        <div class="sk-line sk-title"></div>
        <div class="sk-line sk-content"></div>
        <div class="sk-line sk-content"></div>
      </div>
    </div>

    <!-- 搜索结果提示 -->
    <div v-else-if="searchKeyword" class="search-info">
      <span>搜索 "{{ searchKeyword }}" 的结果（{{ total }} 条）</span>
      <button class="btn btn-ghost btn-sm" @click="clearSearch">清除搜索</button>
    </div>

    <!-- 素材列表 -->
    <div v-else-if="materials.length > 0" class="materials-grid">
      <div v-for="m in materials" :key="m.material_id" class="mat-card glass-card" @click="openDetail(m)">
        <div class="mat-badge">{{ m.category }}</div>
        <h3 class="mat-title">{{ m.title }}</h3>
        <p class="mat-preview">{{ m.content.slice(0, 80) }}{{ m.content.length > 80 ? '...' : '' }}</p>
        <div class="mat-tags" v-if="m.tags">
          <span v-for="t in m.tags.split(',').slice(0, 3)" :key="t" class="mat-tag">{{ t.trim() }}</span>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <span class="empty-icon"> </span>
      <p class="empty-title">暂无素材</p>
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
        <div v-if="detailMat" class="mat-overlay" @click.self="detailMat = null">
          <div class="mat-detail glass-card">
            <button class="close-btn" @click="detailMat = null">&times;</button>
            <div class="detail-badge">{{ detailMat.category }}</div>
            <h2 class="detail-title">{{ detailMat.title }}</h2>
            <div class="detail-content">{{ detailMat.content }}</div>
            <div class="detail-tags" v-if="detailMat.tags">
              <span v-for="t in detailMat.tags.split(',')" :key="t" class="mat-tag">{{ t.trim() }}</span>
            </div>
            <div class="detail-actions">
              <button class="btn btn-outline btn-sm" @click="copyMat(detailMat)">复制全文</button>
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

const materials = ref([])
const categories = ref([])
const loading = ref(true)
const activeCategory = ref('')
const searchQuery = ref('')
const searchKeyword = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)
const detailMat = ref(null)

const catIcons = {
  '成语典故': ' ',
  '名言金句': '✨',
  '景物描写': ' ',
  '人物外貌': ' ',
  '动作场面': '⚔️',
  '情感表达': ' ',
}

onMounted(async () => {
  await Promise.all([loadCategories(), loadMaterials()])
})

async function loadCategories() {
  const res = await api.get('/api/materials/categories')
  if (res.code === 0) categories.value = res.data.categories
}

async function loadMaterials() {
  loading.value = true
  let url = `/api/materials/?page=${page.value}&page_size=${pageSize}`
  if (activeCategory.value) url += `&category=${encodeURIComponent(activeCategory.value)}`
  const res = await api.get(url)
  if (res.code === 0) {
    materials.value = res.data.materials
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
  const res = await api.get(`/api/materials/search?q=${encodeURIComponent(q)}&page=1&page_size=${pageSize}`)
  if (res.code === 0) {
    materials.value = res.data.materials
    total.value = res.data.total
  }
  loading.value = false
}

function clearSearch() {
  searchQuery.value = ''
  searchKeyword.value = ''
  page.value = 1
  loadMaterials()
}

function selectCategory(cat) {
  activeCategory.value = activeCategory.value === cat ? '' : cat
  searchKeyword.value = ''
  searchQuery.value = ''
  page.value = 1
  loadMaterials()
}

function changePage(p) {
  page.value = p
  if (searchKeyword.value) doSearch()
  else loadMaterials()
}

function openDetail(m) { detailMat.value = m }

async function copyMat(m) {
  try {
    await navigator.clipboard.writeText(m.content)
    alert('已复制到剪贴板')
  } catch { alert('复制失败') }
}
</script>

<style scoped>
.ml-header {
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

.search-info {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: var(--space-lg); font-size: 0.9rem; color: var(--text-secondary);
}

.materials-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--space-lg);
}
.skeleton-card { height: 140px; padding: var(--space-lg); }
.sk-line { height: 12px; border-radius: 6px; background: var(--bg-glass); margin-bottom: var(--space-sm); }
.sk-title { width: 50%; }
.sk-content { width: 90%; }

.mat-card {
  padding: var(--space-lg); cursor: pointer;
  transition: all 0.3s ease; position: relative;
}
.mat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 28px rgba(196, 163, 90, 0.1);
  border-color: rgba(196, 163, 90, 0.25);
}
.mat-badge {
  position: absolute; top: var(--space-md); right: var(--space-md);
  font-size: 0.7rem; padding: 2px 8px;
  border-radius: var(--radius-full);
  background: rgba(196, 163, 90, 0.1);
  color: var(--accent-primary);
}
.mat-title {
  font-family: var(--font-serif);
  font-size: 1.1rem; margin-bottom: var(--space-sm);
  color: var(--text-primary);
}
.mat-preview {
  font-size: 0.88rem; line-height: 1.7;
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}
.mat-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.mat-tag {
  font-size: 0.7rem; padding: 2px 8px;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-glass);
  color: var(--text-muted);
}

.empty-state { text-align: center; padding: var(--space-2xl) 0; }
.empty-icon { font-size: 3rem; display: block; margin-bottom: var(--space-md); }
.empty-title { font-size: 1.2rem; color: var(--text-primary); }

.pagination {
  display: flex; justify-content: center; align-items: center;
  gap: var(--space-lg); margin-top: var(--space-2xl);
}
.page-info { font-size: 0.85rem; color: var(--text-muted); }

.mat-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
  padding: var(--space-xl);
}
.mat-detail {
  max-width: 560px; width: 100%;
  padding: var(--space-2xl);
  position: relative; max-height: 80vh; overflow-y: auto;
}
.close-btn {
  position: absolute; top: var(--space-md); right: var(--space-md);
  background: none; border: none; font-size: 1.5rem;
  color: var(--text-muted); cursor: pointer;
}
.close-btn:hover { color: var(--text-primary); }
.detail-badge {
  font-size: 0.8rem; color: var(--accent-primary);
  margin-bottom: var(--space-sm);
}
.detail-title {
  font-family: var(--font-serif);
  font-size: 1.5rem; margin-bottom: var(--space-lg);
}
.detail-content {
  font-family: var(--font-serif);
  font-size: 1.05rem; line-height: 2;
  color: var(--text-primary);
  margin-bottom: var(--space-lg);
}
.detail-tags {
  display: flex; gap: 6px; flex-wrap: wrap;
  margin-bottom: var(--space-lg);
}
.detail-actions { display: flex; justify-content: flex-end; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
