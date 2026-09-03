<template>
  <div class="panel">
    <!-- 分类选择 -->
    <div class="panel-input-area">
      <div class="mat-controls">
        <input v-model="searchQuery" placeholder="搜索素材..." @keydown.enter="doSearch" />
        <button class="btn btn-primary btn-sm" @click="doSearch">搜索</button>
      </div>
      <div class="cat-chips">
        <span
          v-for="cat in categories" :key="cat.category"
          class="cat-chip" :class="{ active: activeCategory === cat.category }"
          @click="selectCategory(cat.category)"
        >{{ catIcons[cat.category] || cat.category }}</span>
      </div>
    </div>

    <!-- 随机推荐 -->
    <div class="action-row">
      <button class="btn btn-ghost btn-sm" @click="loadRandom" :disabled="loading">
        {{ loading ? '加载中...' : ' 随机推荐' }}
      </button>
    </div>

    <!-- 结果列表 -->
    <div class="mat-list">
      <div v-if="materials.length === 0 && !loading" class="empty-state">
        <span class="empty-icon"> </span>
        <p class="empty-hint">选择分类或搜索素材</p>
      </div>

      <div v-for="(m, idx) in materials" :key="m.material_id || idx" class="mat-item" @click="toggleExpand(idx)">
        <div class="mat-head">
          <span class="mat-title">{{ m.title }}</span>
          <span class="mat-cat">{{ m.category }}</span>
        </div>
        <div v-if="expandedIdx === idx" class="mat-body">
          <div class="mat-content">{{ m.content }}</div>
          <div class="mat-actions">
            <button class="card-btn" @click.stop="$emit('insert', m.content)">插入编辑器</button>
            <button class="card-btn" @click.stop="toggleRef(m)">{{ isPicked(m.content) ? '✓ 已引用' : '＋ 引用' }}</button>
            <button class="card-btn" @click.stop="copyText(m.content)">复制</button>
          </div>
        </div>
        <div v-else class="mat-preview">{{ m.content.slice(0, 50) }}...</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/index.js'
import { useWritingStore } from '../../stores/writing.js'

defineEmits(['insert'])

const writingStore = useWritingStore()

const materials = ref([])
const categories = ref([])
const loading = ref(false)
const searchQuery = ref('')
const activeCategory = ref('')
const expandedIdx = ref(null)

const catIcons = {
  '成语典故': ' ',
  '名言金句': '✨',
  '景物描写': ' ',
  '人物外貌': ' ',
  '动作场面': '⚔️',
  '情感表达': ' ',
}

onMounted(async () => {
  const res = await api.get('/api/materials/categories')
  if (res.code === 0) categories.value = res.data.categories
  await loadRandom()
})

async function loadRandom() {
  loading.value = true
  const res = await api.get('/api/materials/random?count=5')
  if (res.code === 0) materials.value = res.data.materials
  loading.value = false
  activeCategory.value = ''
  searchQuery.value = ''
}

async function doSearch() {
  const q = searchQuery.value.trim()
  if (!q) return
  loading.value = true
  const res = await api.get(`/api/materials/search?q=${encodeURIComponent(q)}&page_size=10`)
  if (res.code === 0) materials.value = res.data.materials
  loading.value = false
  activeCategory.value = ''
}

async function selectCategory(cat) {
  activeCategory.value = activeCategory.value === cat ? '' : cat
  if (!activeCategory.value) { await loadRandom(); return }
  loading.value = true
  searchQuery.value = ''
  const res = await api.get(`/api/materials/?category=${encodeURIComponent(cat)}&page_size=10`)
  if (res.code === 0) materials.value = res.data.materials
  loading.value = false
}

function toggleExpand(idx) {
  expandedIdx.value = expandedIdx.value === idx ? null : idx
}

function isPicked(content) {
  return writingStore.pickedRefs.some(r => r.content === content)
}

function toggleRef(m) {
  writingStore.pickRef({ type: m.category || '素材', content: m.content })
}

async function copyText(text) {
  try { await navigator.clipboard.writeText(text) } catch {}
}
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.mat-controls {
  display: flex; gap: var(--space-sm); margin-bottom: var(--space-sm);
}
.mat-controls input { flex: 1; padding: 6px 10px; font-size: 0.85rem; }

.cat-chips { display: flex; flex-wrap: wrap; gap: 6px; }
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

.action-row { margin: var(--space-sm) 0; }

.mat-list { display: flex; flex-direction: column; gap: var(--space-sm); }

.empty-state { text-align: center; padding: var(--space-xl) 0; }
.empty-icon { font-size: 2rem; display: block; margin-bottom: var(--space-sm); }
.empty-hint { color: var(--text-muted); font-size: 0.85rem; }

.mat-item {
  padding: var(--space-md);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(196, 163, 90, 0.06);
  cursor: pointer; transition: all 0.2s;
}
.mat-item:hover {
  border-color: rgba(196, 163, 90, 0.15);
  background: rgba(196, 163, 90, 0.03);
}
.mat-head {
  display: flex; justify-content: space-between; align-items: baseline;
  margin-bottom: 4px;
}
.mat-title {
  font-family: var(--font-serif); font-size: 0.95rem;
  color: var(--text-primary); font-weight: 600;
}
.mat-cat { font-size: 0.7rem; color: var(--accent-primary); }
.mat-preview {
  font-size: 0.85rem; color: var(--text-muted);
  overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
}
.mat-body { margin-top: var(--space-sm); }
.mat-content {
  font-family: var(--font-serif);
  font-size: 0.88rem; line-height: 1.9;
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}
.mat-actions { display: flex; gap: var(--space-sm); }
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
