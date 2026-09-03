<template>
  <div class="page-container">
    <ReadingNav />

    <!-- 头部 -->
    <div class="records-header">
      <h2>我的记录</h2>
      <p class="header-sub">好句收藏 · 阅读足迹</p>
    </div>

    <!-- Tab 切换 -->
    <div class="tabs">
      <div class="tab" :class="{ active: activeTab === 'history' }" @click="activeTab = 'history'">
        阅读记录
      </div>
      <div class="tab" :class="{ active: activeTab === 'highlights' }" @click="activeTab = 'highlights'">
        我的好句
        <span v-if="highlights.length" class="tab-count">{{ highlights.length }}</span>
      </div>
    </div>

    <!-- 阅读记录 -->
    <div v-if="activeTab === 'history'">
      <div v-if="loadingHistory" class="loading-hint">加载中...</div>
      <div v-else-if="history.length === 0" class="empty-state">
        <span class="empty-icon">&#128214;</span>
        <p class="empty-title">还没有阅读记录</p>
        <router-link to="/library" class="btn btn-primary btn-sm" style="margin-top: var(--space-md)">去书库找书</router-link>
      </div>
      <div v-else class="history-list">
        <div v-for="book in history" :key="book.book_type + '-' + book.book_id"
             class="history-item glass-card" @click="goRead(book)">
          <div class="history-cover"></div>
          <div class="history-info">
            <h4>{{ book.title || '未知书籍' }}</h4>
            <p class="history-author">{{ book.author || '未知作者' }}</p>
            <div class="history-meta">
              <span>第{{ book.chapter_no }}章</span>
              <span class="meta-dot">·</span>
              <span>{{ book.total_percent }}%</span>
              <span class="meta-dot">·</span>
              <span>{{ formatTime(book.updated_at) }}</span>
            </div>
            <div class="history-progress">
              <div class="progress-track">
                <div class="progress-fill" :style="{ width: book.total_percent + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 我的好句 -->
    <div v-if="activeTab === 'highlights'">
      <div v-if="loadingHighlights" class="loading-hint">加载中...</div>
      <div v-else-if="highlights.length === 0" class="empty-state">
        <span class="empty-icon">&#10024;</span>
        <p class="empty-title">还没有收藏好句</p>
        <p class="empty-hint">阅读时选中文字即可标记好句</p>
      </div>
      <div v-else class="highlights-list">
        <div v-for="hl in highlights" :key="hl.highlight_id" class="highlight-item glass-card">
          <div class="hl-quote">{{ hl.selected_text }}</div>
          <div class="hl-footer">
            <span class="hl-source" @click="goReadHighlight(hl)">
              {{ hl.book_title || '未知书籍' }}
              <span v-if="hl.chapter_no"> · 第{{ hl.chapter_no }}章</span>
            </span>
            <div class="hl-actions">
              <button class="btn btn-ghost btn-sm" @click="syncHighlight(hl)" :disabled="hl.synced_to_material">
                {{ hl.synced_to_material ? '已同步' : '同步素材' }}
              </button>
              <button class="btn btn-ghost btn-sm" @click="deleteHighlight(hl)">删除</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import ReadingNav from '../../components/ReadingNav.vue'

const router = useRouter()
const activeTab = ref('history')

const history = ref([])
const loadingHistory = ref(true)

const highlights = ref([])
const loadingHighlights = ref(true)

onMounted(async () => {
  await Promise.all([fetchHistory(), fetchHighlights()])
})

async function fetchHistory() {
  loadingHistory.value = true
  const res = await api.get('/api/reading/history?limit=50')
  if (res.code === 0) history.value = res.data.items
  loadingHistory.value = false
}

async function fetchHighlights() {
  loadingHighlights.value = true
  const res = await api.get('/api/highlights?page_size=50')
  if (res.code === 0) highlights.value = res.data.items
  loadingHighlights.value = false
}

function goRead(book) {
  router.push(`/reader/${book.book_type}/${book.book_id}`)
}

function goReadHighlight(hl) {
  router.push(`/reader/${hl.book_type}/${hl.book_id}`)
}

async function syncHighlight(hl) {
  if (hl.synced_to_material) return
  const res = await api.post(`/api/highlights/${hl.highlight_id}/sync`)
  if (res.code === 0) hl.synced_to_material = true
}

async function deleteHighlight(hl) {
  if (!confirm('确定删除这条好句？')) return
  const res = await api.delete(`/api/highlights/${hl.highlight_id}`)
  if (res.code === 0) {
    highlights.value = highlights.value.filter(h => h.highlight_id !== hl.highlight_id)
  }
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
</script>

<style scoped>
.page-container { padding-top: 80px; }

/* ====== 头部 ====== */
.records-header {
  text-align: center; margin-bottom: var(--space-xl);
  padding: var(--space-lg) 0;
}
.records-header h2 {
  font-family: var(--font-serif); font-size: 1.8rem; font-weight: 700;
  background: linear-gradient(135deg, #e8e6f0, #c4a35a);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; margin-bottom: 0.25rem;
}
.header-sub { font-size: 0.85rem; color: var(--text-muted); }

/* ====== Tab ====== */
.tabs {
  display: flex; gap: 4px; margin-bottom: var(--space-xl);
  border-bottom: 1px solid var(--border-glass); padding-bottom: var(--space-sm);
}
.tab {
  display: flex; align-items: center; gap: 5px;
  padding: 7px 18px; font-size: 0.85rem; color: var(--text-muted);
  background: none; border-radius: var(--radius-full); cursor: pointer;
  transition: all 0.25s ease;
}
.tab:hover { color: var(--text-primary); background: rgba(255,255,255,0.03); }
.tab.active { color: var(--accent-primary); background: rgba(196,163,90,0.08); }
.tab-count {
  font-size: 0.65rem; min-width: 16px; text-align: center;
  background: rgba(196,163,90,0.12); border-radius: var(--radius-full);
  padding: 0 4px; line-height: 16px;
}

/* ====== 空状态 ====== */
.empty-state { text-align: center; padding: var(--space-2xl) 0; }
.empty-icon { font-size: 2.5rem; display: block; margin-bottom: var(--space-md); }
.empty-title { font-size: 1rem; color: var(--text-muted); margin-bottom: 4px; }
.empty-hint { font-size: 0.82rem; color: var(--text-muted); opacity: 0.7; }

/* ====== 阅读记录 ====== */
.history-list { display: flex; flex-direction: column; gap: var(--space-md); }
.history-item {
  display: flex; gap: var(--space-lg); padding: var(--space-lg);
  cursor: pointer; transition: all 0.3s ease;
  border-left: 3px solid transparent;
}
.history-item:hover { border-left-color: var(--accent-primary); transform: translateY(-2px); }
.history-cover {
  width: 48px; height: 64px; flex-shrink: 0; border-radius: var(--radius-sm);
  background: linear-gradient(135deg, rgba(196,163,90,0.12), rgba(196,163,90,0.04));
  position: relative; overflow: hidden;
}
.history-cover::after {
  content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--accent-primary), transparent);
}
.history-info { flex: 1; min-width: 0; }
.history-info h4 { font-size: 0.95rem; margin-bottom: 2px; }
.history-author { font-size: 0.78rem; color: var(--text-muted); margin-bottom: var(--space-sm); }
.history-meta { font-size: 0.75rem; color: var(--text-muted); margin-bottom: var(--space-sm); display: flex; align-items: center; gap: 4px; }
.meta-dot { opacity: 0.4; }
.history-progress { display: flex; align-items: center; gap: var(--space-sm); }
.progress-track { flex: 1; height: 3px; background: rgba(255,255,255,0.06); border-radius: 2px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--accent-primary); border-radius: 2px; }

/* ====== 好句 ====== */
.highlights-list { display: flex; flex-direction: column; gap: var(--space-md); }
.highlight-item { padding: var(--space-lg); }
.hl-quote {
  font-family: var(--font-serif); font-size: 0.95rem; line-height: 1.7;
  color: var(--text-primary); margin-bottom: var(--space-md);
  padding-left: var(--space-md);
  border-left: 3px solid var(--accent-primary);
}
.hl-footer { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--space-sm); }
.hl-source {
  font-size: 0.78rem; color: var(--text-muted); cursor: pointer;
  transition: color 0.2s;
}
.hl-source:hover { color: var(--accent-primary); }
.hl-actions { display: flex; gap: var(--space-sm); }

/* ====== 通用 ====== */
.loading-hint { text-align: center; padding: var(--space-2xl); color: var(--text-muted); }

/* ====== 响应式 ====== */
@media (max-width: 768px) {
  .history-item { flex-direction: column; gap: var(--space-sm); }
  .history-cover { width: 100%; height: 4px; }
}
</style>
