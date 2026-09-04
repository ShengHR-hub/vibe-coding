<template>
  <div class="page-container">
    <div class="notif-header">
      <h2>消息中心</h2>
      <button v-if="unread > 0" class="btn btn-ghost btn-sm" @click="markAllRead">全部标为已读</button>
    </div>

    <div v-if="loading" class="center"><LoadingSpinner /></div>
    <div v-else-if="errorMsg" class="center error">{{ errorMsg }} <button class="btn btn-ghost btn-sm" @click="fetchData">重试</button></div>
    <div v-else-if="items.length === 0" class="center muted">暂无消息</div>

    <div v-else class="notif-list">
      <div v-for="n in items" :key="n.notification_id" class="notif-item" :class="{ unread: !n.is_read }" @click="handleClick(n)">
        <span class="notif-icon">{{ typeIcon(n.type) }}</span>
        <div class="notif-body">
          <p class="notif-content">{{ n.content }}</p>
          <span class="notif-time">{{ fmtTime(n.created_at) }}</span>
        </div>
        <span v-if="!n.is_read" class="unread-dot"></span>
        <button v-if="!n.is_read" class="btn btn-ghost btn-xs mark-btn" @click.stop="markOne(n)">标为已读</button>
      </div>
    </div>

    <div v-if="total > pageSize" class="pagination">
      <button class="btn btn-ghost" :disabled="page <= 1" @click="changePage(-1)">上一页</button>
      <span>{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button class="btn btn-ghost" :disabled="page >= Math.ceil(total / pageSize)" @click="changePage(1)">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import { useUserStore } from '../../stores/user.js'
import LoadingSpinner from '../../components/LoadingSpinner.vue'

const router = useRouter()
const userStore = useUserStore()

const items = ref([])
const loading = ref(true)
const errorMsg = ref('')
const page = ref(1)
const total = ref(0)
const unread = ref(0)
const pageSize = 20

onMounted(fetchData)

function changePage(delta) {
  page.value += delta
  fetchData()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function fetchData() {
  loading.value = true
  errorMsg.value = ''
  const res = await api.get(`/api/notifications?page=${page.value}&page_size=${pageSize}`)
  if (res.code === 0) {
    items.value = res.data.items
    total.value = res.data.total
    unread.value = res.data.unread
  } else {
    errorMsg.value = res.msg || '加载失败'
  }
  loading.value = false
}

async function handleClick(n) {
  if (!n.is_read) {
    await markOne(n)
  }
  if (n.type === 'achievement') {
    if (userStore.user?.user_id) router.push({ path: `/profile/${userStore.user.user_id}`, query: { tab: 'achievements' } })
  } else if (n.related_id) {
    const routes = { follow: 'profile', comment: 'work', reply: 'work', like: 'work', favorite: 'work' }
    const path = routes[n.type] || 'work'
    router.push(path === 'profile' ? `/profile/${n.related_id}` : `/work/${n.related_id}`)
  }
}

async function markOne(n) {
  const res = await api.post('/api/notifications/mark-read', { notification_id: n.notification_id })
  if (res.code === 0) {
    n.is_read = true
    unread.value = Math.max(0, unread.value - 1)
  }
}

async function markAllRead() {
  const res = await api.post('/api/notifications/mark-read', { mark_all: true })
  if (res.code === 0) {
    for (const n of items.value) n.is_read = true
    unread.value = 0
  }
}

function typeIcon(t) {
  return { comment: '💬', reply: '↩️', like: '❤️', follow: '👤', favorite: '⭐', achievement: '🏆' }[t] || '🔔'
}

function fmtTime(t) {
  if (!t) return ''
  const d = new Date(t)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
  return d.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.notif-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-xl); }

.notif-list { display: flex; flex-direction: column; gap: 2px; }

.notif-item { display: flex; align-items: center; gap: var(--space-md); padding: var(--space-md); border-radius: var(--radius-sm); cursor: pointer; transition: background var(--transition-fast); position: relative; }
.notif-item:hover { background: var(--bg-glass); }
.notif-item.unread { background: rgba(196, 163, 90, 0.06); }

.notif-icon { font-size: 1.2rem; flex-shrink: 0; width: 32px; text-align: center; }
.notif-body { flex: 1; min-width: 0; }
.notif-content { font-size: 0.9rem; color: var(--text-primary); margin-bottom: 2px; line-height: 1.4; }
.notif-time { font-size: 0.75rem; color: var(--text-muted); }

.unread-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent-primary); flex-shrink: 0; }
.mark-btn { font-size: 0.7rem; opacity: 0; transition: opacity var(--transition-fast); }
.notif-item:hover .mark-btn { opacity: 1; }

.center { display: flex; justify-content: center; padding: var(--space-2xl); }
.error { color: var(--accent-red); }
.muted { color: var(--text-muted); }
.pagination { display: flex; justify-content: center; align-items: center; gap: var(--space-md); margin-top: var(--space-xl); }
</style>
