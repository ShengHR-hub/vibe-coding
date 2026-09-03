<template>
  <div class="page-container">
    <ReadingNav />
    <!-- 头部 -->
    <div class="shelf-header">
      <div class="header-info">
        <h2>我的书架</h2>
        <p class="header-sub">管理你的阅读收藏</p>
      </div>
      <div class="header-actions">
        <router-link to="/library/upload" class="btn btn-ghost btn-sm">导入书籍</router-link>
        <button class="btn btn-ghost btn-sm" @click="exportBooks('json')">导出 JSON</button>
        <button class="btn btn-ghost btn-sm" @click="exportBooks('csv')">导出 CSV</button>
        <button class="btn btn-ghost btn-sm" @click="showFolderDialog = true">新建书单</button>
        <button class="btn btn-ghost btn-sm" @click="toggleBatchMode">
          {{ batchMode ? '取消批量' : '批量管理' }}
        </button>
        <router-link to="/library" class="btn btn-outline btn-sm">去书库找书</router-link>
      </div>
    </div>

    <!-- Tab 栏 -->
    <div class="tabs">
      <div v-for="tab in tabs" :key="tab.key"
           class="tab" :class="{ active: activeTab === tab.key }"
           @click="switchTab(tab.key)">
        {{ tab.label }}
        <span v-if="tab.count > 0" class="tab-count">{{ tab.count }}</span>
      </div>
    </div>

    <!-- 排序 -->
    <div class="sort-bar">
      <span class="sort-label">排序：</span>
      <button v-for="s in sortOptions" :key="s.key"
              class="sort-btn" :class="{ active: sortBy === s.key }"
              @click="sortBy = s.key; fetchAllBooks()">
        {{ s.label }}
      </button>
    </div>

    <!-- 加载 -->
    <div v-if="loading" class="books-grid">
      <div v-for="i in 4" :key="i" class="skeleton-card glass-card">
        <div class="sk-line sk-cover"></div>
        <div class="sk-line sk-title"></div>
        <div class="sk-line sk-meta"></div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="books.length === 0" class="empty-state">
      <span class="empty-icon">&#128218;</span>
      <p class="empty-title">{{ emptyText }}</p>
      <router-link to="/library" class="btn btn-primary" style="margin-top: var(--space-md)">去书库找书</router-link>
    </div>

    <!-- 书籍列表 -->
    <div v-else class="books-grid">
      <div v-for="book in books" :key="book.shelf_id"
           class="book-item glass-card" :class="{ selected: selectedBooks.has(book.shelf_id) }"
           @click="batchMode ? toggleSelect(book) : goDetail(book)">
        <div class="item-checkbox" v-if="batchMode" @click.stop>
          <input type="checkbox" :checked="selectedBooks.has(book.shelf_id)"
                 @change="toggleSelect(book)" />
        </div>
        <div class="item-cover" :class="coverClass(book.type)">
          <span class="cover-type">{{ typeLabel(book.type) }}</span>
        </div>
        <div class="item-body">
          <h4>{{ book.title || '未知书籍' }}</h4>
          <p class="item-author">{{ book.author || '未知作者' }}</p>
          <div class="item-progress" v-if="book.total_percent > 0">
            <div class="progress-track">
              <div class="progress-fill" :style="{ width: book.total_percent + '%' }"></div>
            </div>
            <span class="progress-text">{{ book.total_percent }}%</span>
          </div>
          <div class="item-meta">
            <span v-if="book.shelf_group" class="group-badge">{{ groupLabel(book.shelf_group) }}</span>
            <span v-if="book.rating > 0" class="rating">&#9733; {{ book.rating }}</span>
            <span v-if="book.last_read_at" class="last-read">{{ formatTime(book.last_read_at) }}</span>
          </div>
        </div>
        <div class="item-actions" v-if="!batchMode">
          <button class="btn btn-ghost btn-sm" @click.stop="removeBook(book)">移除</button>
        </div>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="batchMode && selectedBooks.size > 0" class="batch-bar glass-card">
      <span class="batch-count">已选 {{ selectedBooks.size }} 本</span>
      <div class="batch-actions">
        <select v-model="batchTarget" class="batch-select">
          <option value="">选择目标分组</option>
          <option value="reading">在读</option>
          <option value="completed">已读</option>
          <option value="want_read">想读</option>
        </select>
        <button class="btn btn-primary btn-sm" @click="batchMove" :disabled="!batchTarget">移动</button>
        <button class="btn btn-ghost btn-sm" @click="batchDelete">批量删除</button>
        <button class="btn btn-ghost btn-sm" @click="selectedBooks.clear()">清空选择</button>
      </div>
    </div>

    <!-- 新建书单弹窗 -->
    <div v-if="showFolderDialog" class="dialog-overlay" @click.self="showFolderDialog = false">
      <div class="dialog glass-card">
        <h3>新建书单</h3>
        <input v-model="newFolderName" placeholder="书单名称" @keydown.enter="createFolder" />
        <div class="dialog-actions">
          <button class="btn btn-ghost" @click="showFolderDialog = false">取消</button>
          <button class="btn btn-primary" @click="createFolder">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import ReadingNav from '../../components/ReadingNav.vue'

import { useToast } from '../../composables/useToast.js'
const toast = useToast()
const router = useRouter()
const books = ref([])
const allBooks = ref([])
const loading = ref(true)
const activeTab = ref('reading')
const sortBy = ref('recent')
const showFolderDialog = ref(false)
const newFolderName = ref('')
const folders = ref([])

// 批量操作
const batchMode = ref(false)
const selectedBooks = ref(new Set())
const batchTarget = ref('')

const tabs = computed(() => [
  { key: 'reading', label: '在读', count: allBooks.value.filter(b => b.shelf_group === 'reading').length },
  { key: 'completed', label: '已读', count: allBooks.value.filter(b => b.shelf_group === 'completed').length },
  { key: 'want_read', label: '想读', count: allBooks.value.filter(b => b.shelf_group === 'want_read').length },
  ...folders.value.map(f => ({ key: `folder:${f}`, label: f, count: allBooks.value.filter(b => b.folder_name === f).length })),
])

const sortOptions = [
  { key: 'recent', label: '最近阅读' },
  { key: 'progress', label: '阅读进度' },
  { key: 'rating', label: '评分' },
  { key: 'added', label: '加入时间' },
  { key: 'title', label: '书名排序' },
]

const emptyText = computed(() => {
  if (activeTab.value === 'reading') return '还没有在读书籍'
  if (activeTab.value === 'completed') return '还没有已读书籍'
  if (activeTab.value === 'want_read') return '还没有想读书籍'
  return '书单为空'
})

onMounted(async () => {
  await Promise.all([fetchAllBooks(), fetchFolders()])
})

async function fetchAllBooks() {
  loading.value = true
  const res = await api.get(`/api/bookshelf?sort=${sortBy.value}`)
  if (res.code === 0) {
    allBooks.value = res.data.items
    filterAndSort()
  }
  loading.value = false
}

function filterAndSort() {
  let filtered = [...allBooks.value]
  if (!activeTab.value.startsWith('folder:')) {
    filtered = filtered.filter(b => b.shelf_group === activeTab.value)
  } else {
    const folder = activeTab.value.replace('folder:', '')
    filtered = filtered.filter(b => b.folder_name === folder)
  }
  books.value = filtered
}

async function fetchFolders() {
  const res = await api.get('/api/bookshelf/folders')
  if (res.code === 0) folders.value = res.data.folders
}

function switchTab(key) {
  activeTab.value = key
  filterAndSort()
}

function goDetail(book) {
  router.push(`/library/${book.book_type}/${book.book_id}`)
}

async function removeBook(book) {
  if (!confirm(`确定将《${book.title}》从书架移除？`)) return
  const res = await api.delete(`/api/bookshelf/${book.shelf_id}`)
  if (res.code === 0) {
    allBooks.value = allBooks.value.filter(b => b.shelf_id !== book.shelf_id)
    filterAndSort()
  }
}

async function createFolder() {
  const name = newFolderName.value.trim()
  if (!name) return
  const res = await api.post('/api/bookshelf/folders', { name })
  if (res.code === 0) {
    folders.value.push(name)
    showFolderDialog.value = false
    newFolderName.value = ''
  } else {
    toast.info(res.msg)
  }
}

function typeLabel(t) {
  return { novel: '小说', poetry: '诗歌', essay: '散文', webfiction: '网文', script: '剧本' }[t] || t
}

function coverClass(t) {
  return t || 'default'
}

function groupLabel(g) {
  return { reading: '在读', completed: '已读', want_read: '想读' }[g] || g
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
  return d.toLocaleDateString()
}

function exportBooks(format) {
  const data = allBooks.value.map(b => ({
    title: b.title,
    author: b.author,
    type: typeLabel(b.type),
    group: groupLabel(b.shelf_group),
    progress: b.total_percent + '%',
    rating: b.rating || '',
    lastRead: b.last_read_at || '',
  }))

  if (format === 'json') {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    downloadBlob(blob, 'bookshelf.json')
  } else {
    const headers = ['书名', '作者', '类型', '分组', '进度', '评分', '最后阅读']
    const rows = data.map(d => [d.title, d.author, d.type, d.group, d.progress, d.rating, d.lastRead])
    const csv = [headers.join(','), ...rows.map(r => r.map(c => `"${c}"`).join(','))].join('\n')
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
    downloadBlob(blob, 'bookshelf.csv')
  }
  toast.success('导出成功')
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

// 批量操作
function toggleBatchMode() {
  batchMode.value = !batchMode.value
  if (!batchMode.value) {
    selectedBooks.value.clear()
    batchTarget.value = ''
  }
}

function toggleSelect(book) {
  const id = book.shelf_id
  if (selectedBooks.value.has(id)) {
    selectedBooks.value.delete(id)
  } else {
    selectedBooks.value.add(id)
  }
}

async function batchMove() {
  if (!batchTarget.value || selectedBooks.value.size === 0) return
  const res = await api.post('/api/bookshelf/batch', {
    shelf_ids: [...selectedBooks.value],
    updates: { shelf_group: batchTarget.value }
  })
  if (res.code === 0) {
    toast.success(res.msg)
    selectedBooks.value.clear()
    batchTarget.value = ''
    await fetchAllBooks()
  } else {
    toast.error(res.msg)
  }
}

async function batchDelete() {
  if (selectedBooks.value.size === 0) return
  if (!confirm(`确定删除选中的 ${selectedBooks.value.size} 本书吗？`)) return
  const res = await api.post('/api/bookshelf/batch-delete', {
    shelf_ids: [...selectedBooks.value]
  })
  if (res.code === 0) {
    toast.success(res.msg)
    selectedBooks.value.clear()
    await fetchAllBooks()
  } else {
    toast.error(res.msg)
  }
}
</script>

<style scoped>
.page-container { padding-top: 80px; }
/* ====== 头部 ====== */
.shelf-header {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: var(--space-xl); flex-wrap: wrap; gap: var(--space-lg);
}
.header-info h2 {
  font-family: var(--font-serif); font-size: 1.8rem; font-weight: 700;
  background: linear-gradient(135deg, #e8e6f0, #c4a35a);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; margin-bottom: 0.25rem;
}
.header-sub { font-size: 0.85rem; color: var(--text-muted); }
.header-actions { display: flex; gap: var(--space-sm); }

/* ====== Tab ====== */
.tabs {
  display: flex; gap: 4px; margin-bottom: var(--space-lg);
  border-bottom: 1px solid var(--border-glass); padding-bottom: var(--space-sm);
  overflow-x: auto;
}
.tab {
  display: flex; align-items: center; gap: 5px;
  padding: 7px 18px; font-size: 0.85rem; color: var(--text-muted);
  background: none; border-radius: var(--radius-full); cursor: pointer;
  transition: all 0.25s ease; white-space: nowrap;
}
.tab:hover { color: var(--text-primary); background: rgba(255,255,255,0.03); }
.tab.active { color: var(--accent-primary); background: rgba(196,163,90,0.08); }
.tab-count {
  font-size: 0.65rem; min-width: 16px; text-align: center;
  background: rgba(196,163,90,0.12); border-radius: var(--radius-full);
  padding: 0 4px; line-height: 16px;
}

/* ====== 排序 ====== */
.sort-bar { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-xl); }
.sort-label { font-size: 0.82rem; color: var(--text-muted); }
.sort-btn {
  font-size: 0.78rem; padding: 3px 12px; border-radius: var(--radius-full);
  background: none; color: var(--text-muted); cursor: pointer;
  transition: all 0.2s ease;
}
.sort-btn:hover { color: var(--text-primary); }
.sort-btn.active { color: var(--accent-primary); background: rgba(196,163,90,0.08); }

/* ====== 骨架屏 ====== */
.skeleton-card { padding: var(--space-lg); }
.sk-line { height: 12px; border-radius: var(--radius-sm); background: rgba(255,255,255,0.04); margin-bottom: var(--space-sm); }
.sk-cover { height: 100px; border-radius: var(--radius-md); margin-bottom: var(--space-md); }
.sk-title { width: 70%; }
.sk-meta { width: 50%; }

/* ====== 空状态 ====== */
.empty-state { text-align: center; padding: var(--space-2xl) 0; }
.empty-icon { font-size: 2.5rem; display: block; margin-bottom: var(--space-md); }
.empty-title { font-size: 1rem; color: var(--text-muted); }

/* ====== 书籍列表 ====== */
.books-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: var(--space-lg); }

.book-item {
  display: flex; gap: var(--space-md); padding: var(--space-md);
  cursor: pointer; transition: all 0.3s ease;
  border-left: 3px solid transparent;
}
.book-item:hover { border-left-color: var(--accent-primary); transform: translateY(-2px); }

.item-cover {
  width: 60px; height: 80px; flex-shrink: 0; border-radius: var(--radius-sm);
  background: linear-gradient(135deg, rgba(196,163,90,0.12), rgba(196,163,90,0.04));
  display: flex; align-items: flex-end; justify-content: center;
  padding: 4px; position: relative; overflow: hidden;
}
.item-cover::after {
  content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--accent-primary), transparent);
}
.item-cover.poetry { background: linear-gradient(135deg, rgba(167,139,250,0.12), rgba(167,139,250,0.04)); }
.item-cover.poetry::after { background: linear-gradient(90deg, var(--accent-purple), transparent); }
.item-cover.essay { background: linear-gradient(135deg, rgba(126,200,227,0.12), rgba(126,200,227,0.04)); }
.item-cover.webfiction { background: linear-gradient(135deg, rgba(244,132,95,0.12), rgba(244,132,95,0.04)); }
.cover-type { font-size: 0.6rem; color: var(--text-muted); z-index: 1; }

.item-body { flex: 1; min-width: 0; }
.item-body h4 { font-size: 0.92rem; margin-bottom: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.item-author { font-size: 0.78rem; color: var(--text-muted); margin-bottom: var(--space-sm); }

.item-progress { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-sm); }
.progress-track { flex: 1; height: 3px; background: rgba(255,255,255,0.06); border-radius: 2px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--accent-primary); border-radius: 2px; transition: width 0.3s ease; }
.progress-text { font-size: 0.7rem; color: var(--accent-primary); flex-shrink: 0; }

.item-meta { display: flex; gap: var(--space-sm); align-items: center; }
.group-badge {
  font-size: 0.65rem; padding: 1px 6px; border-radius: var(--radius-full);
  background: rgba(196,163,90,0.08); color: var(--accent-primary);
}
.rating { font-size: 0.72rem; color: var(--accent-primary); }
.last-read { font-size: 0.7rem; color: var(--text-muted); }

.item-actions { display: flex; align-items: center; flex-shrink: 0; }

/* ====== 批量操作 ====== */
.book-item.selected {
  border-left-color: var(--accent-primary);
  background: rgba(196, 163, 90, 0.08);
}

.item-checkbox {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.item-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--accent-primary);
  cursor: pointer;
}

.batch-bar {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  padding: var(--space-md) var(--space-xl);
  background: rgba(20, 20, 35, 0.95);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(196, 163, 90, 0.2);
  border-radius: var(--radius-xl);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.batch-count {
  font-size: 0.85rem;
  color: var(--accent-primary);
  font-weight: 600;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.batch-select {
  padding: 6px 12px;
  font-size: 0.85rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  outline: none;
}

.batch-select:focus {
  border-color: var(--accent-primary);
}

/* ====== 弹窗 ====== */
.dialog-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;
}
.dialog { padding: var(--space-xl); width: 360px; }
.dialog h3 { margin-bottom: var(--space-lg); }
.dialog input { width: 100%; margin-bottom: var(--space-lg); }
.dialog-actions { display: flex; gap: var(--space-sm); justify-content: flex-end; }

/* ====== 响应式 ====== */
@media (max-width: 768px) {
  .shelf-header { flex-direction: column; align-items: stretch; }
  .books-grid { grid-template-columns: 1fr; }
}
</style>
