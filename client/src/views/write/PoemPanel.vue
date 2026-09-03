<template>
  <div class="panel">
    <!-- 搜索与分类 -->
    <div class="panel-input-area">
      <div class="poem-controls">
        <input v-model="searchQuery" placeholder="搜索诗词、作者..." @keydown.enter="doSearch" />
        <button class="btn btn-primary btn-sm" @click="doSearch">搜索</button>
      </div>
      <div class="cat-chips">
        <span
          v-for="cat in categories" :key="cat.category"
          class="cat-chip" :class="{ active: activeCategory === cat.category }"
          @click="selectCategory(cat.category)"
        >{{ cat.category }}</span>
      </div>
    </div>

    <!-- 随机推荐 -->
    <div class="random-area">
      <button class="btn btn-ghost btn-sm" @click="loadRandom" :disabled="loading">
        {{ loading ? '加载中...' : ' 随机推荐' }}
      </button>
      <button class="btn btn-ghost btn-sm realtime-btn" @click="fetchRealtime" :disabled="loading">
        {{ loading ? '加载中...' : '⚡ 实时推荐' }}
      </button>
    </div>

    <!-- 结果列表 -->
    <div class="poem-list">
      <div v-if="poems.length === 0 && !loading" class="empty-state">
        <span class="empty-icon"> </span>
        <p class="empty-hint">搜索或选择分类查看诗词</p>
      </div>

      <div v-for="(poem, idx) in poems" :key="poem.poem_id || `rt-${idx}`" class="poem-item" :class="{ 'realtime-item': poem._realtime }" @click="toggleExpand(poem, idx)">
        <div class="poem-head">
          <span class="poem-title">{{ poem.title }}</span>
          <span class="poem-meta" v-if="poem.dynasty">〔{{ poem.dynasty }}〕{{ poem.author }}</span>
          <span class="poem-meta" v-else>{{ poem.author }}</span>
        </div>
        <div v-if="expandedIdx === idx" class="poem-body">
          <div class="poem-content">{{ poem.content }}</div>
          <div class="poem-actions">
            <button class="card-btn" @click.stop="insertFull(poem)">插入全文</button>
            <button class="card-btn" @click.stop="insertFirst(poem)">插入首句</button>
            <button class="card-btn" @click.stop="toggleRef(poem)">{{ isPicked(poem.content) ? '✓ 已引用' : '＋ 引用' }}</button>
          </div>
        </div>
        <div v-else class="poem-preview">{{ firstLine(poem.content) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/index.js'
import { useWritingStore } from '../../stores/writing.js'

const emit = defineEmits(['insert'])

const writingStore = useWritingStore()

const poems = ref([])
const categories = ref([])
const loading = ref(false)
const searchQuery = ref('')
const activeCategory = ref('')
const expandedIdx = ref(null)

function isPicked(content) {
  return writingStore.pickedRefs.some(r => r.content === content)
}

function toggleRef(poem) {
  writingStore.pickRef({ type: '诗词', content: poem.content })
}

onMounted(async () => {
  const res = await api.get('/api/poems/categories')
  if (res.code === 0) categories.value = res.data.categories
  await loadRandom()
})

async function loadRandom() {
  loading.value = true
  const res = await api.get('/api/poems/random?count=5')
  if (res.code === 0) poems.value = res.data.poems
  loading.value = false
  activeCategory.value = ''
  searchQuery.value = ''
}

async function doSearch() {
  const q = searchQuery.value.trim()
  if (!q) return
  loading.value = true
  const res = await api.get(`/api/poems/search?q=${encodeURIComponent(q)}&page_size=10`)
  if (res.code === 0) poems.value = res.data.poems
  loading.value = false
  activeCategory.value = ''
}

async function selectCategory(cat) {
  activeCategory.value = activeCategory.value === cat ? '' : cat
  if (!activeCategory.value) { await loadRandom(); return }
  loading.value = true
  searchQuery.value = ''
  const res = await api.get(`/api/poems/?category=${encodeURIComponent(cat)}&page_size=10`)
  if (res.code === 0) poems.value = res.data.poems
  loading.value = false
}

async function fetchRealtime() {
  loading.value = true
  activeCategory.value = ''
  searchQuery.value = ''
  const res = await api.get('/api/poems/realtime?count=5')
  if (res.code === 0) {
    poems.value = res.data.poems.map(p => ({ ...p, _realtime: true }))
  }
  loading.value = false
}

function toggleExpand(poem, idx) {
  expandedIdx.value = expandedIdx.value === idx ? null : idx
}

function firstLine(content) {
  if (!content) return ''
  return content.split('\n')[0]
}

function insertFull(poem) {
  const authorLine = poem.dynasty ? `〔${poem.dynasty}〕${poem.author}` : poem.author
  const text = `「${poem.title}」${authorLine}\n${poem.content}`
  emit('insert', text)
}

function insertFirst(poem) {
  const first = poem.content?.split('\n')[0] || ''
  emit('insert', first)
}
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.poem-controls {
  display: flex; gap: var(--space-sm); margin-bottom: var(--space-sm);
}
.poem-controls input {
  flex: 1; padding: 6px 10px; font-size: 0.85rem;
}

.cat-chips {
  display: flex; flex-wrap: wrap; gap: 6px;
}
.cat-chip {
  font-size: 0.75rem; padding: 3px 10px;
  border-radius: var(--radius-full);
  background: var(--bg-glass); border: 1px solid var(--border-glass);
  cursor: pointer; transition: all 0.2s;
}
.cat-chip:hover { border-color: var(--accent-primary); }
.cat-chip.active {
  background: rgba(196, 163, 90, 0.15);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.random-area {
  margin: var(--space-sm) 0;
  display: flex; gap: var(--space-sm);
}
.realtime-btn {
  color: #ff8c32;
  border-color: rgba(255, 140, 50, 0.2);
}
.realtime-btn:hover {
  background: rgba(255, 140, 50, 0.08);
  border-color: rgba(255, 140, 50, 0.4);
}

.poem-list {
  display: flex; flex-direction: column; gap: var(--space-sm);
}

.empty-state {
  text-align: center; padding: var(--space-xl) 0;
}
.empty-icon { font-size: 2rem; display: block; margin-bottom: var(--space-sm); }
.empty-hint { color: var(--text-muted); font-size: 0.85rem; }

.poem-item {
  padding: var(--space-md);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(196, 163, 90, 0.06);
  cursor: pointer; transition: all 0.2s;
}
.poem-item:hover {
  border-color: rgba(196, 163, 90, 0.15);
  background: rgba(196, 163, 90, 0.03);
}
.realtime-item {
  border-color: rgba(255, 140, 50, 0.1);
}
.realtime-item:hover {
  border-color: rgba(255, 140, 50, 0.3);
  background: rgba(255, 140, 50, 0.03);
}
.poem-head {
  display: flex; justify-content: space-between; align-items: baseline;
  margin-bottom: 4px;
}
.poem-title {
  font-family: var(--font-serif); font-size: 0.95rem;
  color: var(--text-primary); font-weight: 600;
}
.poem-meta {
  font-size: 0.75rem; color: var(--text-muted);
}
.poem-preview {
  font-family: var(--font-serif);
  font-size: 0.85rem; color: var(--text-muted);
  overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
}
.poem-body {
  margin-top: var(--space-sm);
}
.poem-content {
  font-family: var(--font-serif);
  font-size: 0.9rem; line-height: 2;
  color: var(--text-secondary);
  white-space: pre-line;
  margin-bottom: var(--space-sm);
}
.poem-actions {
  display: flex; gap: var(--space-sm);
}
.card-btn {
  font-size: 0.75rem; padding: 3px 10px;
  border-radius: var(--radius-sm);
  background: rgba(196, 163, 90, 0.08);
  border: 1px solid rgba(196, 163, 90, 0.15);
  color: var(--accent-primary);
  cursor: pointer; transition: all 0.2s;
}
.card-btn:hover {
  background: rgba(196, 163, 90, 0.15);
  border-color: rgba(196, 163, 90, 0.3);
}
</style>
