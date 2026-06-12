<template>
  <div class="page-container">
    <div class="works-header">
      <h2>我的作品</h2>
      <button class="btn btn-primary" @click="showCreate = true">新建作品</button>
    </div>

    <div class="filters">
      <select v-model="filterType" @change="load">
        <option value="">全部类型</option>
        <option value="novel">小说</option>
        <option value="poetry">诗歌</option>
        <option value="essay">散文</option>
        <option value="script">剧本</option>
      </select>
      <select v-model="filterStatus" @change="load">
        <option value="">全部状态</option>
        <option value="draft">草稿</option>
        <option value="published">已发布</option>
        <option value="private">私密</option>
      </select>
    </div>

    <div v-if="loading" class="center"><LoadingSpinner /></div>

    <div v-else-if="errorMsg" class="empty error-msg">{{ errorMsg }} <button class="btn btn-ghost btn-sm" @click="load">重试</button></div>

    <div v-else-if="works.length === 0" class="empty">还没有作品，点击"新建作品"开始创作</div>

    <div v-else class="works-grid">
      <div v-for="w in works" :key="w.work_id" class="work-card glass-card" @click="$router.push(`/works/${w.work_id}`)">
        <div class="card-type">{{ typeLabel(w.type) }}</div>
        <h3>{{ w.title || '未命名作品' }}</h3>
        <p v-if="w.summary" class="card-summary">{{ w.summary }}</p>
        <div class="card-meta">
          <span>{{ w.word_count || 0 }} 字</span>
          <span class="status-tag" :class="w.status">{{ statusLabel(w.status) }}</span>
          <span>{{ fmt(w.updated_at) }}</span>
          <button class="btn btn-ghost btn-xs edit-link" @click.stop="$router.push(`/works/${w.work_id}/edit`)">编辑</button>
        </div>
      </div>
    </div>

    <div v-if="total > pageSize" class="pagination">
      <button class="btn btn-ghost" :disabled="page <= 1" @click="page--; load()">上一页</button>
      <span>{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button class="btn btn-ghost" :disabled="page >= Math.ceil(total / pageSize)" @click="page++; load()">下一页</button>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal glass-card">
        <h3>新建作品</h3>
        <input v-model="createTitle" placeholder="作品标题" />
        <select v-model="createType">
          <option value="novel">小说</option>
          <option value="poetry">诗歌</option>
          <option value="essay">散文</option>
          <option value="script">剧本</option>
        </select>
        <input v-model="createTags" placeholder="标签（用逗号分隔）" />
        <textarea v-model="createSummary" rows="2" placeholder="简介（可选）"></textarea>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showCreate = false">取消</button>
          <button class="btn btn-primary" @click="create" :disabled="creating">{{ creating ? '创建中...' : '创建' }}</button>
        </div>
      </div>
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
const filterType = ref('')
const filterStatus = ref('')

const showCreate = ref(false)
const createTitle = ref('')
const createType = ref('novel')
const createTags = ref('')
const createSummary = ref('')
const creating = ref(false)

onMounted(load)

async function load() {
  loading.value = true
  errorMsg.value = ''
  const params = new URLSearchParams({ page: page.value, page_size: pageSize })
  if (filterType.value) params.set('type', filterType.value)
  if (filterStatus.value) params.set('status', filterStatus.value)
  const res = await api.get(`/api/works?${params}`)
  if (res.code === 0) {
    works.value = res.data.items
    total.value = res.data.total
  } else {
    errorMsg.value = res.msg || '加载失败'
  }
  loading.value = false
}

async function create() {
  if (!createTitle.value.trim()) { alert('请输入标题'); return }
  creating.value = true
  const res = await api.post('/api/works', {
    title: createTitle.value,
    type: createType.value,
    tags: createTags.value,
    summary: createSummary.value
  })
  creating.value = false
  if (res.code === 0) {
    showCreate.value = false
    router.push(`/works/${res.data.work_id}/edit`)
  } else {
    alert(res.msg)
  }
}

function typeLabel(t) {
  return { novel: '小说', poetry: '诗歌', essay: '散文', script: '剧本' }[t] || t
}
function statusLabel(s) {
  return { draft: '草稿', published: '已发布', private: '私密' }[s] || s
}
function fmt(d) {
  if (!d) return ''
  return d.slice(0, 10)
}
</script>

<style scoped>
.works-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-xl); }
.filters { display: flex; gap: var(--space-md); margin-bottom: var(--space-xl); }
.filters select { padding: 6px 12px; font-size: 0.85rem; }
.works-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--space-lg); }
.work-card { padding: var(--space-lg); cursor: pointer; transition: all var(--transition-fast); }
.work-card:hover { border-color: var(--accent-primary); transform: translateY(-2px); }
.card-type { font-size: 0.75rem; color: var(--accent-primary); text-transform: uppercase; margin-bottom: var(--space-sm); }
.work-card h3 { margin-bottom: var(--space-sm); }
.card-summary { font-size: 0.85rem; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: var(--space-md); }
.card-meta { display: flex; gap: var(--space-md); font-size: 0.8rem; color: var(--text-muted); align-items: center; }
.status-tag { padding: 1px 8px; border-radius: var(--radius-sm); font-size: 0.75rem; }
.status-tag.draft { background: var(--text-muted); color: var(--bg-primary); }
.status-tag.published { background: var(--accent-green); color: var(--bg-primary); }
.status-tag.private { background: var(--accent-warm); color: var(--bg-primary); }
.empty { text-align: center; color: var(--text-muted); padding: var(--space-2xl); }
.error-msg { color: var(--accent-red); }
.edit-link { margin-left: auto; }
.btn-xs { padding: 2px 8px; font-size: 0.7rem; }
.center { display: flex; justify-content: center; padding: var(--space-2xl); }
.pagination { display: flex; justify-content: center; align-items: center; gap: var(--space-md); margin-top: var(--space-xl); }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 200; }
.modal { width: 440px; padding: var(--space-xl); display: flex; flex-direction: column; gap: var(--space-md); }
.modal h3 { margin-bottom: var(--space-sm); }
.modal-actions { display: flex; justify-content: flex-end; gap: var(--space-md); }
</style>
