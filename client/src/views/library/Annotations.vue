<template>
  <div class="page-container">
    <ReadingNav />
    <!-- 头部 -->
    <div class="ann-header">
      <div class="header-info">
        <h2>我的批注</h2>
        <p class="header-sub">所有阅读批注一览</p>
      </div>
      <div class="header-actions">
        <div class="filter-tabs">
          <button class="filter-tab" :class="{ active: visibility === '' }" @click="visibility = ''; fetchAnnotations()">全部</button>
          <button class="filter-tab" :class="{ active: visibility === 'public' }" @click="visibility = 'public'; fetchAnnotations()">公开</button>
          <button class="filter-tab" :class="{ active: visibility === 'private' }" @click="visibility = 'private'; fetchAnnotations()">私密</button>
        </div>
      </div>
    </div>

    <!-- 加载 -->
    <div v-if="loading" class="loading-hint">加载中...</div>

    <!-- 空状态 -->
    <div v-else-if="annotations.length === 0" class="empty-state">
      <span class="empty-icon">&#128221;</span>
      <p class="empty-title">暂无批注</p>
      <p class="empty-hint">阅读时选中文字即可添加批注</p>
    </div>

    <!-- 批注列表 -->
    <div v-else class="ann-list">
      <div v-for="ann in annotations" :key="ann.annotation_id" class="ann-item glass-card">
        <div class="ann-book" @click="goToRead(ann)">
          <span class="ann-book-title">{{ ann.book_title || '未知书籍' }}</span>
          <span class="ann-chapter">第{{ ann.chapter_no }}章</span>
          <span v-if="!ann.is_public" class="badge-private">私密</span>
        </div>
        <div class="ann-quote">"{{ ann.selected_text }}"</div>
        <div class="ann-content">{{ ann.content }}</div>
        <div class="ann-footer">
          <span class="ann-time">{{ formatTime(ann.created_at) }}</span>
          <button class="btn btn-ghost btn-xs" @click="deleteAnn(ann)">删除</button>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination">
      <button class="btn btn-ghost" :disabled="page <= 1" @click="page--; fetchAnnotations()">上一页</button>
      <span class="page-info">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button class="btn btn-ghost" :disabled="page >= Math.ceil(total / pageSize)" @click="page++; fetchAnnotations()">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import ReadingNav from '../../components/ReadingNav.vue'

const router = useRouter()
const annotations = ref([])
const loading = ref(true)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const visibility = ref('')

onMounted(() => fetchAnnotations())

async function fetchAnnotations() {
  loading.value = true
  const params = new URLSearchParams({ page: page.value, page_size: pageSize })
  if (visibility.value) params.set('visibility', visibility.value)
  const res = await api.get(`/api/annotations/mine?${params}`)
  if (res.code === 0) {
    annotations.value = res.data.items
    total.value = res.data.total
  }
  loading.value = false
}

async function deleteAnn(ann) {
  if (!confirm('确定删除这条批注？')) return
  const res = await api.delete(`/api/annotations/${ann.annotation_id}`)
  if (res.code === 0) {
    annotations.value = annotations.value.filter(a => a.annotation_id !== ann.annotation_id)
    total.value--
  }
}

function goToRead(ann) {
  const type = ann.book_type
  const id = ann.book_id
  const query = ann.chapter_id ? `?chapter=${ann.chapter_id}` : ''
  router.push(`/reader/${type}/${id}${query}`)
}

function formatTime(ts) {
  if (!ts) return ''
  return ts.slice(0, 16).replace('T', ' ')
}
</script>

<style scoped>
.page-container { padding-top: 80px; }
/* ====== 头部 ====== */
.ann-header {
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
.filter-tabs { display: flex; gap: 4px; }
.filter-tab {
  padding: 5px 14px; font-size: 0.8rem; color: var(--text-muted);
  background: none; border-radius: var(--radius-full); cursor: pointer;
  transition: all 0.2s ease;
}
.filter-tab:hover { color: var(--text-primary); background: rgba(255,255,255,0.03); }
.filter-tab.active { color: var(--accent-primary); background: rgba(196,163,90,0.08); }

/* ====== 空状态 ====== */
.empty-state { text-align: center; padding: var(--space-2xl) 0; }
.empty-icon { font-size: 2.5rem; display: block; margin-bottom: var(--space-md); }
.empty-title { font-size: 1.1rem; color: var(--text-primary); margin-bottom: var(--space-sm); }
.empty-hint { font-size: 0.85rem; color: var(--text-muted); }
.loading-hint { text-align: center; padding: var(--space-2xl) 0; color: var(--text-muted); }

/* ====== 批注列表 ====== */
.ann-list { display: flex; flex-direction: column; gap: var(--space-md); }
.ann-item {
  padding: var(--space-lg); border-left: 3px solid rgba(196,163,90,0.2);
  transition: all 0.2s ease;
}
.ann-item:hover { border-left-color: var(--accent-primary); }
.ann-book {
  display: flex; align-items: center; gap: var(--space-sm);
  margin-bottom: var(--space-sm); cursor: pointer;
}
.ann-book-title { font-size: 0.82rem; color: var(--accent-primary); font-weight: 500; }
.ann-book-title:hover { text-decoration: underline; }
.ann-chapter { font-size: 0.72rem; color: var(--text-muted); }
.badge-private { font-size: 0.6rem; padding: 1px 5px; border-radius: var(--radius-full); background: rgba(239,68,68,0.12); color: #ef4444; }
.ann-quote {
  font-size: 0.82rem; color: var(--text-muted); font-style: italic;
  margin-bottom: var(--space-sm); padding-left: var(--space-md);
  border-left: 2px solid rgba(196,163,90,0.15);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.ann-content { font-size: 0.9rem; color: var(--text-primary); margin-bottom: var(--space-sm); line-height: 1.6; }
.ann-footer { display: flex; justify-content: space-between; align-items: center; }
.ann-time { font-size: 0.72rem; color: var(--text-muted); }

/* ====== 分页 ====== */
.pagination {
  display: flex; justify-content: center; align-items: center; gap: var(--space-lg);
  margin-top: var(--space-2xl); padding-top: var(--space-lg);
  border-top: 1px solid var(--border-glass);
}
.page-info { font-size: 0.85rem; color: var(--text-muted); }

/* ====== 响应式 ====== */
@media (max-width: 768px) {
  .ann-header { flex-direction: column; align-items: stretch; }
}
</style>
