<template>
  <div class="page-container">
    <!-- 头部 -->
    <div class="challenge-top">
      <div class="challenge-header">
        <h2>写作挑战</h2>
        <p class="header-sub">以挑战为炉，淬炼文字之火</p>
      </div>
      <div class="header-deco">
        <span class="deco-icon">&#9876;</span>
      </div>
    </div>

    <!-- 标签栏 -->
    <div class="tabs">
      <button v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }" @click="switchTab(tab.key)">
        <span class="tab-dot" :class="tab.key"></span>
        {{ tab.label }}
      </button>
    </div>

    <!-- 加载骨架屏 -->
    <div v-if="loading" class="challenge-list">
      <div v-for="i in 3" :key="i" class="skeleton-card glass-card">
        <div class="sk-row">
          <div class="sk-line sk-title"></div>
          <div class="sk-line sk-badge"></div>
        </div>
        <div class="sk-line sk-desc"></div>
        <div class="sk-line sk-meta"></div>
      </div>
    </div>

    <!-- 错误 -->
    <div v-else-if="errorMsg" class="center error">{{ errorMsg }} <button class="btn btn-ghost btn-sm" @click="fetchData">重试</button></div>

    <!-- 空状态 -->
    <div v-else-if="challenges.length === 0" class="empty-state">
      <span class="empty-icon">&#9876;</span>
      <p class="empty-title">暂无挑战</p>
      <p class="empty-hint">新的写作挑战即将到来</p>
    </div>

    <!-- 挑战列表 -->
    <div v-else class="challenge-list">
      <div v-for="c in challenges" :key="c.challenge_id" class="challenge-card glass-card" :class="{ expanded: expandedId === c.challenge_id }">
        <div class="challenge-main" @click="toggleExpand(c.challenge_id)">
          <div class="challenge-info">
            <div class="challenge-top-row">
              <h3>{{ c.title }}</h3>
              <span class="status-badge" :class="c.status">{{ statusLabel(c.status) }}</span>
            </div>
            <p class="challenge-desc">{{ c.description }}</p>
            <div class="challenge-meta">
              <span class="meta-chip">&#128197; {{ fmtDate(c.start_date) }} — {{ fmtDate(c.end_date) }}</span>
              <span class="meta-chip">&#128101; {{ c.participant_count || 0 }} 人参加</span>
              <span v-if="c.min_words" class="meta-chip">&#9998; 最低 {{ c.min_words }} 字/天</span>
            </div>
            <!-- 进度条 -->
            <div v-if="c.is_joined && c.status === 'active'" class="progress-bar-wrap">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: progressPercent(c) + '%' }"></div>
              </div>
              <span class="progress-text">{{ progressText(c) }}</span>
            </div>
          </div>
          <div class="challenge-action" @click.stop>
            <button v-if="!userStore.isLoggedIn" class="btn btn-ghost btn-sm" @click="$router.push('/login')">登录后参加</button>
            <button v-else-if="c.is_joined" class="btn btn-ghost btn-sm joined-btn" disabled>已参加 &#10003;</button>
            <button v-else-if="c.status !== 'ended'" class="btn btn-primary btn-sm" @click="join(c.challenge_id)">参加挑战</button>
            <span class="expand-icon" :class="{ expanded: expandedId === c.challenge_id }">&#9662;</span>
          </div>
        </div>

        <!-- 展开详情 -->
        <div v-if="expandedId === c.challenge_id" class="challenge-detail">
          <div v-if="!userStore.isLoggedIn" class="center muted">登录后查看详情</div>
          <template v-else-if="c.is_joined">
            <!-- 今日打卡 -->
            <div class="detail-section">
              <h4>今日打卡</h4>
              <div class="checkin-form">
                <div class="checkin-inputs">
                  <input v-model.number="getCheckin(c.challenge_id).wordCount" type="number" placeholder="今日字数" min="0" class="input-sm" />
                  <input v-model="getCheckin(c.challenge_id).note" placeholder="打卡备注" class="input-sm" />
                </div>
                <button class="btn btn-primary btn-sm" @click="doCheckin(c.challenge_id)">打卡</button>
              </div>
              <p v-if="getCheckin(c.challenge_id).msg" class="checkin-msg" :class="{ error: getCheckin(c.challenge_id).msg.includes('失败') }">{{ getCheckin(c.challenge_id).msg }}</p>
            </div>

            <!-- 打卡日历 -->
            <div class="detail-section">
              <h4>打卡记录</h4>
              <div v-if="getCheckin(c.challenge_id).loading" class="center" style="padding:1rem"><LoadingSpinner /></div>
              <div v-else-if="getCheckin(c.challenge_id).dates.length === 0" class="center muted" style="padding:1rem">暂无打卡记录</div>
              <div v-else class="checkin-calendar">
                <div v-for="d in getCheckin(c.challenge_id).dates" :key="d.date" class="calendar-day" :class="dayClass(d)" :title="d.date + (d.checked ? ' | ' + d.word_count + '字' : '')">
                  <span class="day-num">{{ d.date.slice(8) }}</span>
                </div>
              </div>
            </div>
          </template>

          <!-- 接力写作 -->
          <div class="detail-section">
            <h4>接力写作</h4>
            <div v-if="getRelay(c.challenge_id).loading" class="center" style="padding:1rem"><LoadingSpinner /></div>
            <div v-else-if="getRelay(c.challenge_id).segments.length === 0" class="center muted" style="padding:1rem">暂无接力段落，来做第一个接力者吧</div>
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
              <textarea v-model="getRelay(c.challenge_id).content" placeholder="续写下一段，让故事延续..." rows="3"></textarea>
              <button class="btn btn-primary btn-sm" @click="doRelay(c.challenge_id)" :disabled="!getRelay(c.challenge_id).content.trim()">提交接力</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination">
      <button class="btn btn-ghost" :disabled="page <= 1" @click="page--; fetchData()">上一页</button>
      <span class="page-info">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
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

import { useToast } from '../../composables/useToast.js'
const toast = useToast()
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
    toast.info(res.msg)
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

function progressPercent(c) {
  if (!c.start_date || !c.end_date) return 0
  const start = new Date(c.start_date)
  const end = new Date(c.end_date)
  const now = new Date()
  if (now < start) return 0
  if (now > end) return 100
  return Math.round(((now - start) / (end - start)) * 100)
}

function progressText(c) {
  const pct = progressPercent(c)
  if (pct >= 100) return '已结束'
  if (pct === 0) return '即将开始'
  return `进行中 ${pct}%`
}

function dayClass(d) {
  if (d.checked) {
    const wc = d.word_count || 0
    if (wc >= 1000) return 'checked intense'
    if (wc >= 500) return 'checked medium'
    return 'checked light'
  }
  return ''
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
    toast.info(res.msg)
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
/* ====== 头部 ====== */
.challenge-top {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: var(--space-xl); flex-wrap: wrap; gap: var(--space-md);
}
.challenge-header h2 {
  font-family: var(--font-serif);
  font-size: 1.8rem; font-weight: 700;
  background: linear-gradient(135deg, #e8e6f0, #c4a35a);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.25rem;
}
.header-sub { font-size: 0.85rem; color: var(--text-muted); letter-spacing: 0.04em; }
.header-deco {
  width: 48px; height: 48px; border-radius: 50%;
  background: rgba(196,163,90,0.06);
  border: 1px solid rgba(196,163,90,0.12);
  display: flex; align-items: center; justify-content: center;
}
.deco-icon { font-size: 1.3rem; color: var(--accent-primary); opacity: 0.6; }

/* ====== 标签 ====== */
.tabs { display: flex; gap: 4px; margin-bottom: var(--space-xl); border-bottom: 1px solid var(--border-glass); padding-bottom: var(--space-sm); }
.tab {
  display: flex; align-items: center; gap: 6px;
  padding: 7px 20px; font-size: 0.85rem; color: var(--text-muted);
  background: none; border-radius: var(--radius-full);
  transition: all 0.25s ease;
}
.tab:hover { color: var(--text-primary); background: rgba(255,255,255,0.03); }
.tab.active { color: var(--accent-primary); background: rgba(196,163,90,0.08); }
.tab-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--text-muted); transition: background 0.25s ease;
}
.tab-dot.active { background: var(--accent-green); }
.tab-dot.upcoming { background: var(--accent-purple); }
.tab-dot.ended { background: var(--text-muted); }

/* ====== 挑战列表 ====== */
.challenge-list { display: flex; flex-direction: column; gap: var(--space-lg); }

.challenge-card {
  overflow: hidden; transition: all 0.3s ease;
  border-top: 3px solid rgba(196,163,90,0.08);
}
.challenge-card.expanded { border-top-color: rgba(196,163,90,0.25); }

.challenge-main {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: var(--space-lg); cursor: pointer;
  transition: background 0.2s ease;
}
.challenge-main:hover { background: rgba(255,255,255,0.01); }
.challenge-info { flex: 1; min-width: 0; }
.challenge-top-row { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-sm); flex-wrap: wrap; }
.challenge-top-row h3 { font-size: 1.1rem; }

.status-badge {
  font-size: 0.7rem; padding: 3px 10px; border-radius: var(--radius-full);
  font-weight: 600; letter-spacing: 0.04em; flex-shrink: 0;
}
.status-badge.active { background: rgba(107, 207, 127, 0.12); color: var(--accent-green); }
.status-badge.upcoming { background: rgba(167, 139, 250, 0.12); color: var(--accent-purple); }
.status-badge.ended { background: rgba(107, 103, 128, 0.12); color: var(--text-muted); }

.challenge-desc { font-size: 0.9rem; color: var(--text-secondary); margin-bottom: var(--space-sm); line-height: 1.6; }
.challenge-meta { display: flex; gap: var(--space-md); flex-wrap: wrap; margin-bottom: var(--space-sm); }
.meta-chip {
  font-size: 0.78rem; color: var(--text-muted);
  display: flex; align-items: center; gap: 4px;
}

/* 进度条 */
.progress-bar-wrap { display: flex; align-items: center; gap: var(--space-sm); margin-top: var(--space-sm); }
.progress-bar {
  flex: 1; height: 5px; border-radius: 3px;
  background: rgba(255,255,255,0.05); overflow: hidden;
  max-width: 200px;
}
.progress-fill {
  height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, var(--accent-primary), var(--accent-green));
  transition: width 0.5s ease;
}
.progress-text { font-size: 0.72rem; color: var(--text-muted); flex-shrink: 0; }

/* 操作区 */
.challenge-action { display: flex; align-items: center; gap: var(--space-sm); flex-shrink: 0; margin-left: var(--space-md); }
.joined-btn { color: var(--accent-green) !important; opacity: 0.7; }
.expand-icon {
  font-size: 0.9rem; color: var(--text-muted);
  transition: transform 0.3s ease;
}
.expand-icon.expanded { transform: rotate(180deg); }

/* 详情区 */
.challenge-detail {
  padding: 0 var(--space-lg) var(--space-lg);
  border-top: 1px solid var(--border-glass);
  margin-top: 0;
  animation: slideDown 0.25s ease;
}
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.detail-section { margin-top: var(--space-lg); }
.detail-section h4 {
  font-size: 0.85rem; font-weight: 600; color: var(--text-secondary);
  letter-spacing: 0.04em; margin-bottom: var(--space-sm);
  display: flex; align-items: center; gap: 6px;
}
.detail-section h4::before {
  content: ''; width: 3px; height: 14px; border-radius: 2px;
  background: var(--accent-primary); opacity: 0.5;
}

/* 打卡表单 */
.checkin-form { display: flex; gap: var(--space-sm); align-items: flex-start; flex-wrap: wrap; }
.checkin-inputs { display: flex; gap: var(--space-sm); flex-wrap: wrap; }
.input-sm {
  padding: 8px 12px; font-size: 0.85rem;
  border: 1px solid var(--border-glass); border-radius: var(--radius-sm);
  background: rgba(255,255,255,0.03); color: var(--text-primary);
  width: 150px; transition: border-color 0.2s ease;
}
.input-sm:focus { border-color: rgba(196,163,90,0.4); outline: none; }
.checkin-msg { font-size: 0.85rem; color: var(--accent-green); margin-top: var(--space-xs); }
.checkin-msg.error { color: var(--accent-red); }

/* 打卡日历 */
.checkin-calendar { display: grid; grid-template-columns: repeat(10, 1fr); gap: 5px; }
.calendar-day {
  aspect-ratio: 1; border-radius: 4px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.65rem; color: var(--text-muted);
  transition: all 0.2s ease;
}
.calendar-day.checked { border-color: transparent; color: var(--bg-primary); }
.calendar-day.checked.light   { background: rgba(107, 207, 127, 0.35); }
.calendar-day.checked.medium  { background: rgba(107, 207, 127, 0.65); }
.calendar-day.checked.intense { background: var(--accent-green); }
.calendar-day:hover:not(.checked) { border-color: rgba(255,255,255,0.1); }
.day-num { line-height: 1; }

/* 接力 */
.relay-list { display: flex; flex-direction: column; gap: var(--space-md); }
.relay-segment {
  padding: var(--space-md); background: rgba(255,255,255,0.02);
  border-radius: var(--radius-md); border: 1px solid var(--border-glass);
  transition: border-color 0.2s ease;
}
.relay-segment:hover { border-color: rgba(196,163,90,0.12); }
.relay-meta { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-sm); }
.avatar-dot {
  width: 24px; height: 24px; border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  color: var(--bg-primary); display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; font-weight: 700;
}
.relay-author { font-size: 0.85rem; color: var(--text-primary); font-weight: 600; }
.relay-order { font-size: 0.75rem; color: var(--text-muted); }
.relay-content { font-size: 0.9rem; color: var(--text-secondary); line-height: 1.7; }

.relay-form { margin-top: var(--space-md); display: flex; flex-direction: column; gap: var(--space-sm); }
.relay-form textarea {
  padding: 10px 12px; font-size: 0.9rem;
  border: 1px solid var(--border-glass); border-radius: var(--radius-sm);
  background: rgba(255,255,255,0.03); color: var(--text-primary);
  resize: vertical; transition: border-color 0.2s ease;
}
.relay-form textarea:focus { border-color: rgba(196,163,90,0.4); outline: none; }

/* ====== 加载骨架屏 ====== */
.skeleton-card { padding: var(--space-lg); }
.sk-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-md); }
.sk-line {
  height: 13px; border-radius: 4px;
  background: rgba(196,163,90,0.05);
  animation: skPulse 1.4s ease-in-out infinite;
}
.sk-title { width: 55%; }
.sk-badge { width: 60px; height: 22px; border-radius: 12px; }
.sk-desc { width: 80%; margin-bottom: var(--space-sm); }
.sk-meta { width: 45%; }
@keyframes skPulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

/* ====== 空状态 ====== */
.empty-state {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 3rem 1rem; gap: 0.5rem;
}
.empty-icon { font-size: 2rem; color: var(--accent-primary); opacity: 0.25; }
.empty-title { font-size: 0.95rem; color: var(--text-secondary); font-weight: 600; letter-spacing: 0.04em; }
.empty-hint { font-size: 0.82rem; color: var(--text-muted); }

/* ====== 分页 ====== */
.center { display: flex; justify-content: center; padding: var(--space-2xl); }
.error { color: var(--accent-red); }
.muted { color: var(--text-muted); }
.pagination { display: flex; justify-content: center; align-items: center; gap: var(--space-md); margin-top: var(--space-xl); }
.page-info { font-size: 0.85rem; color: var(--text-muted); font-variant-numeric: tabular-nums; }

@media (max-width: 640px) {
  .challenge-main { flex-direction: column; gap: var(--space-md); }
  .challenge-action { margin-left: 0; width: 100%; justify-content: space-between; }
  .checkin-form { flex-direction: column; }
  .checkin-inputs { flex-direction: column; }
  .input-sm { width: 100%; }
  .checkin-calendar { grid-template-columns: repeat(6, 1fr); }
}
</style>
