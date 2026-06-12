<template>
  <div class="page-container">
    <div class="challenge-header">
      <h2>写作挑战</h2>
    </div>

    <div class="tabs">
      <button v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }" @click="switchTab(tab.key)">
        {{ tab.label }}
      </button>
    </div>

    <div v-if="loading" class="center"><LoadingSpinner /></div>
    <div v-else-if="errorMsg" class="center error">{{ errorMsg }} <button class="btn btn-ghost btn-sm" @click="fetchData">重试</button></div>
    <div v-else-if="challenges.length === 0" class="center muted">暂无挑战</div>

    <div v-else class="challenge-list">
      <div v-for="c in challenges" :key="c.challenge_id" class="challenge-card glass-card">
        <div class="challenge-main" @click="toggleExpand(c.challenge_id)">
          <div class="challenge-info">
            <div class="challenge-top">
              <h3>{{ c.title }}</h3>
              <span class="status-badge" :class="c.status">{{ statusLabel(c.status) }}</span>
            </div>
            <p class="challenge-desc">{{ c.description }}</p>
            <div class="challenge-meta">
              <span>{{ fmtDate(c.start_date) }} — {{ fmtDate(c.end_date) }}</span>
              <span>{{ c.participant_count || 0 }} 人参加</span>
              <span v-if="c.min_words">最低 {{ c.min_words }} 字/天</span>
            </div>
          </div>
          <div class="challenge-action" @click.stop>
            <button v-if="!userStore.isLoggedIn" class="btn btn-ghost btn-sm" @click="$router.push('/login')">登录后参加</button>
            <button v-else-if="c.is_joined" class="btn btn-ghost btn-sm" disabled>已参加 ✓</button>
            <button v-else-if="c.status !== 'ended'" class="btn btn-primary btn-sm" @click="join(c.challenge_id)">参加挑战</button>
            <span class="expand-icon" :class="{ expanded: expandedId === c.challenge_id }">▾</span>
          </div>
        </div>

        <div v-if="expandedId === c.challenge_id" class="challenge-detail">
          <div v-if="!userStore.isLoggedIn" class="center muted">登录后查看详情</div>
          <template v-else-if="c.is_joined">
            <div class="detail-section">
              <h4>今日打卡</h4>
              <div class="checkin-form">
                <input v-model.number="getCheckin(c.challenge_id).wordCount" type="number" placeholder="今日字数" min="0" class="input-sm" />
                <input v-model="getCheckin(c.challenge_id).note" placeholder="打卡备注（可选）" class="input-sm" />
                <button class="btn btn-primary btn-sm" @click="doCheckin(c.challenge_id)">打卡</button>
              </div>
              <p v-if="getCheckin(c.challenge_id).msg" class="checkin-msg">{{ getCheckin(c.challenge_id).msg }}</p>
            </div>

            <div class="detail-section">
              <h4>打卡记录</h4>
              <div v-if="getCheckin(c.challenge_id).loading" class="center"><LoadingSpinner /></div>
              <div v-else-if="getCheckin(c.challenge_id).dates.length === 0" class="center muted">暂无打卡记录</div>
              <div v-else class="checkin-calendar">
                <div v-for="d in getCheckin(c.challenge_id).dates" :key="d.date" class="calendar-day" :class="{ checked: d.checked }" :title="d.date + (d.checked ? ' | ' + d.word_count + '字' : '')"></div>
              </div>
            </div>
          </template>

          <div class="detail-section">
            <h4>接力写作</h4>
            <div v-if="getRelay(c.challenge_id).loading" class="center"><LoadingSpinner /></div>
            <div v-else-if="getRelay(c.challenge_id).segments.length === 0" class="center muted">暂无接力段落</div>
            <div v-else class="relay-list">
              <div v-for="seg in getRelay(c.challenge_id).segments" :key="seg.segment_id" class="relay-segment">
                <div class="relay-meta">
                  <span class="avatar-dot">{{ seg.username?.charAt(0) }}</span>
                  <span class="relay-author">{{ seg.username }}</span>
                  <span class="relay-order">第 {{ seg.segment_order }} 段</span>
                </div>
                <p class="relay-content">{{ seg.content }}</p>
              </div>
            </div>
            <div v-if="userStore.isLoggedIn && c.status !== 'ended'" class="relay-form">
              <textarea v-model="getRelay(c.challenge_id).content" placeholder="续写下一段..." rows="3"></textarea>
              <button class="btn btn-primary btn-sm" @click="doRelay(c.challenge_id)" :disabled="!getRelay(c.challenge_id).content.trim()">提交接力</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="total > pageSize" class="pagination">
      <button class="btn btn-ghost" :disabled="page <= 1" @click="page--; fetchData()">上一页</button>
      <span>{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button class="btn btn-ghost" :disabled="page >= Math.ceil(total / pageSize)" @click="page++; fetchData()">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import { useUserStore } from '../../stores/user.js'
import LoadingSpinner from '../../components/LoadingSpinner.vue'

const router = useRouter()
const userStore = useUserStore()

const challenges = ref([])
const loading = ref(true)
const errorMsg = ref('')
const page = ref(1)
const total = ref(0)
const pageSize = 12
const activeTab = ref('active')
const expandedId = ref(null)

// Per-challenge state maps
const checkinMap = reactive({})
const relayMap = reactive({})

function getCheckin(id) {
  if (!checkinMap[id]) {
    checkinMap[id] = { wordCount: 0, note: '', msg: '', loading: false, dates: [] }
  }
  return checkinMap[id]
}

function getRelay(id) {
  if (!relayMap[id]) {
    relayMap[id] = { loading: false, segments: [], content: '' }
  }
  return relayMap[id]
}

const tabs = [
  { key: 'active', label: '进行中' },
  { key: 'upcoming', label: '即将开始' },
  { key: 'ended', label: '已结束' },
]

onMounted(fetchData)

async function fetchData() {
  loading.value = true
  errorMsg.value = ''
  const res = await api.get(`/api/challenges?status=${activeTab.value}&page=${page.value}&page_size=${pageSize}`)
  if (res.code === 0) {
    challenges.value = res.data.items
    total.value = res.data.total
  } else {
    errorMsg.value = res.msg || '加载失败'
  }
  loading.value = false
}

function switchTab(key) {
  activeTab.value = key
  page.value = 1
  expandedId.value = null
  fetchData()
}

async function join(id) {
  const res = await api.post(`/api/challenges/${id}/join`)
  if (res.code === 0) {
    fetchData()
  } else {
    alert(res.msg)
  }
}

function toggleExpand(id) {
  if (expandedId.value === id) {
    expandedId.value = null
  } else {
    expandedId.value = id
    loadCheckins(id)
    loadRelay(id)
  }
}

async function loadCheckins(challengeId) {
  const st = getCheckin(challengeId)
  st.loading = true
  const res = await api.get(`/api/challenges/${challengeId}/checkins`)
  if (res.code === 0) {
    const checkedDates = new Map()
    for (const item of res.data.items) {
      const d = item.checkin_date?.slice(0, 10)
      if (d) checkedDates.set(d, item.word_count)
    }
    const today = new Date()
    const dates = []
    for (let i = 29; i >= 0; i--) {
      const d = new Date(today)
      d.setDate(d.getDate() - i)
      const key = d.toISOString().slice(0, 10)
      dates.push({ date: key, checked: checkedDates.has(key), word_count: checkedDates.get(key) || 0 })
    }
    st.dates = dates
  }
  st.loading = false
}

async function doCheckin(challengeId) {
  const st = getCheckin(challengeId)
  st.msg = ''
  const res = await api.post(`/api/challenges/${challengeId}/checkin`, {
    word_count: st.wordCount,
    note: st.note
  })
  if (res.code === 0) {
    st.msg = res.msg
    st.wordCount = 0
    st.note = ''
    loadCheckins(challengeId)
  } else {
    st.msg = res.msg
  }
}

async function loadRelay(challengeId) {
  const st = getRelay(challengeId)
  st.loading = true
  const res = await api.get(`/api/challenges/${challengeId}/relay`)
  if (res.code === 0) {
    st.segments = res.data.items
  }
  st.loading = false
}

async function doRelay(challengeId) {
  const st = getRelay(challengeId)
  const res = await api.post(`/api/challenges/${challengeId}/relay`, { content: st.content })
  if (res.code === 0) {
    st.content = ''
    loadRelay(challengeId)
  } else {
    alert(res.msg)
  }
}

function statusLabel(s) {
  return { active: '进行中', upcoming: '即将开始', ended: '已结束' }[s] || s
}

function fmtDate(d) {
  if (!d) return ''
  return d.slice(0, 10)
}
</script>

<style scoped>
.challenge-header { margin-bottom: var(--space-lg); }

.tabs { display: flex; gap: var(--space-sm); margin-bottom: var(--space-xl); border-bottom: 1px solid var(--border-glass); padding-bottom: var(--space-sm); }
.tab { padding: 6px 16px; font-size: 0.9rem; color: var(--text-muted); background: none; border-radius: var(--radius-sm); transition: all var(--transition-fast); }
.tab:hover { color: var(--text-secondary); }
.tab.active { color: var(--accent-primary); background: var(--bg-glass); }

.challenge-list { display: flex; flex-direction: column; gap: var(--space-lg); }

.challenge-main { display: flex; justify-content: space-between; align-items: flex-start; padding: var(--space-lg); cursor: pointer; }
.challenge-info { flex: 1; }
.challenge-top { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-sm); }
.challenge-top h3 { font-size: 1.1rem; }
.status-badge { font-size: 0.7rem; padding: 2px 8px; border-radius: var(--radius-full); }
.status-badge.active { background: rgba(107, 207, 127, 0.15); color: var(--accent-green); }
.status-badge.upcoming { background: rgba(164, 139, 250, 0.15); color: var(--accent-purple); }
.status-badge.ended { background: rgba(107, 103, 128, 0.15); color: var(--text-muted); }

.challenge-desc { font-size: 0.9rem; color: var(--text-secondary); margin-bottom: var(--space-sm); line-height: 1.5; }
.challenge-meta { display: flex; gap: var(--space-lg); font-size: 0.8rem; color: var(--text-muted); flex-wrap: wrap; }

.challenge-action { display: flex; align-items: center; gap: var(--space-sm); flex-shrink: 0; margin-left: var(--space-md); }
.expand-icon { font-size: 1.2rem; color: var(--text-muted); transition: transform var(--transition-fast); }
.expand-icon.expanded { transform: rotate(180deg); }

.challenge-detail { padding: 0 var(--space-lg) var(--space-lg); border-top: 1px solid var(--border-glass); margin-top: var(--space-md); }
.detail-section { margin-top: var(--space-lg); }
.detail-section h4 { font-size: 0.9rem; color: var(--text-secondary); margin-bottom: var(--space-sm); }

.checkin-form { display: flex; gap: var(--space-sm); align-items: center; flex-wrap: wrap; }
.input-sm { padding: 5px 10px; font-size: 0.85rem; border: 1px solid var(--border-glass); border-radius: var(--radius-sm); background: var(--bg-glass); color: var(--text-primary); width: 140px; }
.checkin-msg { font-size: 0.85rem; color: var(--accent-green); margin-top: var(--space-xs); }

.checkin-calendar { display: grid; grid-template-columns: repeat(15, 1fr); gap: 4px; }
.calendar-day { aspect-ratio: 1; border-radius: 3px; background: var(--bg-glass); border: 1px solid var(--border-glass); }
.calendar-day.checked { background: var(--accent-green); border-color: var(--accent-green); }

.relay-list { display: flex; flex-direction: column; gap: var(--space-md); }
.relay-segment { padding: var(--space-md); background: var(--bg-glass); border-radius: var(--radius-sm); border: 1px solid var(--border-glass); }
.relay-meta { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-sm); }
.avatar-dot { width: 22px; height: 22px; border-radius: 50%; background: var(--accent-primary); color: var(--bg-primary); display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; }
.relay-author { font-size: 0.85rem; color: var(--text-primary); }
.relay-order { font-size: 0.75rem; color: var(--text-muted); }
.relay-content { font-size: 0.9rem; color: var(--text-secondary); line-height: 1.6; }

.relay-form { margin-top: var(--space-md); display: flex; flex-direction: column; gap: var(--space-sm); }
.relay-form textarea { padding: 10px; font-size: 0.9rem; border: 1px solid var(--border-glass); border-radius: var(--radius-sm); background: var(--bg-glass); color: var(--text-primary); resize: vertical; }
.relay-form textarea:focus { border-color: var(--accent-primary); outline: none; }

.center { display: flex; justify-content: center; padding: var(--space-2xl); }
.error { color: var(--accent-red); }
.muted { color: var(--text-muted); }
.pagination { display: flex; justify-content: center; align-items: center; gap: var(--space-md); margin-top: var(--space-xl); }
</style>
