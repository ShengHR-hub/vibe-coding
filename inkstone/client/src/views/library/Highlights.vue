<template>
  <div class="page-container">
    <ReadingNav />
    <!-- 头部 -->
    <div class="hl-header">
      <div class="header-info">
        <h2>我的好句</h2>
        <p class="header-sub">阅读中收藏的精彩句子</p>
      </div>
    </div>

    <!-- 加载 -->
    <div v-if="loading" class="loading-hint">加载中...</div>

    <!-- 空状态 -->
    <div v-else-if="highlights.length === 0" class="empty-state">
      <span class="empty-icon">&#10024;</span>
      <p class="empty-title">暂无好句</p>
      <p class="empty-hint">阅读时选中文字，点击"好句"即可标记</p>
    </div>

    <!-- 好句列表 -->
    <div v-else class="hl-list">
      <div v-for="hl in highlights" :key="hl.highlight_id" class="hl-item glass-card">
        <div class="hl-quote">"{{ hl.selected_text }}"</div>
        <div class="hl-meta">
          <span class="hl-book" @click="goToRead(hl)">{{ hl.book_title || '未知书籍' }}</span>
          <span v-if="hl.chapter_no" class="hl-chapter">第{{ hl.chapter_no }}章</span>
          <span class="hl-time">{{ formatTime(hl.created_at) }}</span>
        </div>
        <div class="hl-actions">
          <button v-if="!hl.synced_to_material" class="btn btn-primary btn-xs" @click="syncHighlight(hl)">同步到素材库</button>
          <span v-else class="hl-synced">已同步</span>
          <button class="btn btn-ghost btn-xs" @click="deleteHL(hl)">删除</button>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination">
      <button class="btn btn-ghost" :disabled="page <= 1" @click="page--; fetchHighlights()">上一页</button>
      <span class="page-info">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button class="btn btn-ghost" :disabled="page >= Math.ceil(total / pageSize)" @click="page++; fetchHighlights()">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import ReadingNav from '../../components/ReadingNav.vue'

import { useToast } from '../../composables/useToast.js'
const toast = useToast()
const router = useRouter()
const highlights = ref([])
const loading = ref(true)
const total = ref(0)
const page = ref(1)
const pageSize = 20

onMounted(() => fetchHighlights())

async function fetchHighlights() {
  loading.value = true
  const res = await api.get(`/api/highlights?page=${page.value}&page_size=${pageSize}`)
  if (res.code === 0) {
    highlights.value = res.data.items
    total.value = res.data.total
  }
  loading.value = false
}

async function syncHighlight(hl) {
  const res = await api.post(`/api/highlights/${hl.highlight_id}/sync`)
  if (res.code === 0) {
    hl.synced_to_material = true
  } else {
    toast.info(res.msg)
  }
}

async function deleteHL(hl) {
  if (!confirm('确定删除这条好句？')) return
  const res = await api.delete(`/api/highlights/${hl.highlight_id}`)
  if (res.code === 0) {
    highlights.value = highlights.value.filter(h => h.highlight_id !== hl.highlight_id)
    total.value--
  }
}

function goToRead(hl) {
  const query = hl.chapter_id ? `?chapter=${hl.chapter_id}` : ''
  router.push(`/reader/${hl.book_type}/${hl.book_id}${query}`)
}

function formatTime(ts) {
  if (!ts) return ''
  return ts.slice(0, 16).replace('T', ' ')
}
</script>

<style scoped>
.page-container { padding-top: 80px; }
/* ====== 头部 ====== */
.hl-header {
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

/* ====== 空状态 ====== */
.empty-state { text-align: center; padding: var(--space-2xl) 0; }
.empty-icon { font-size: 2.5rem; display: block; margin-bottom: var(--space-md); }
.empty-title { font-size: 1.1rem; color: var(--text-primary); margin-bottom: var(--space-sm); }
.empty-hint { font-size: 0.85rem; color: var(--text-muted); }
.loading-hint { text-align: center; padding: var(--space-2xl) 0; color: var(--text-muted); }

/* ====== 好句列表 ====== */
.hl-list { display: flex; flex-direction: column; gap: var(--space-md); }
.hl-item {
  padding: var(--space-lg); border-left: 3px solid rgba(196,163,90,0.2);
  transition: all 0.2s ease;
}
.hl-item:hover { border-left-color: var(--accent-primary); }
.hl-quote {
  font-size: 1rem; color: var(--text-primary); line-height: 1.7;
  margin-bottom: var(--space-md); font-family: var(--font-serif);
  padding-left: var(--space-md); border-left: 2px solid rgba(196,163,90,0.15);
}
.hl-meta {
  display: flex; align-items: center; gap: var(--space-sm);
  margin-bottom: var(--space-sm); font-size: 0.78rem; color: var(--text-muted);
}
.hl-book { color: var(--accent-primary); cursor: pointer; }
.hl-book:hover { text-decoration: underline; }
.hl-chapter { opacity: 0.7; }
.hl-time { margin-left: auto; }
.hl-actions { display: flex; align-items: center; gap: var(--space-sm); }
.hl-synced { font-size: 0.72rem; color: var(--accent-green, #4ade80); }

/* ====== 分页 ====== */
.pagination {
  display: flex; justify-content: center; align-items: center; gap: var(--space-lg);
  margin-top: var(--space-2xl); padding-top: var(--space-lg);
  border-top: 1px solid var(--border-glass);
}
.page-info { font-size: 0.85rem; color: var(--text-muted); }

/* ====== 响应式 ====== */
@media (max-width: 768px) {
  .hl-header { flex-direction: column; align-items: stretch; }
}
</style>
