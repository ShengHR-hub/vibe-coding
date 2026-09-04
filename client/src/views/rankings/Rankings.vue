<template>
  <div class="page-container">
    <div class="rk-header">
      <h2>作品排行</h2>
      <p class="header-sub">发现最受欢迎的作品和作者</p>
    </div>

    <!-- 排行榜类型切换 -->
    <div class="rk-tabs">
      <button
        v-for="tab in tabs" :key="tab.key"
        class="rk-tab" :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span>{{ tab.label }}</span>
      </button>
    </div>

    <!-- 综合热度排序 -->
    <div v-if="activeTab === 'works'" class="rk-section">
      <div class="metric-bar">
        <button
          v-for="m in metrics" :key="m.key"
          class="metric-btn" :class="{ active: metric === m.key }"
          @click="changeMetric(m.key)"
        >{{ m.label }}</button>
      </div>

      <div v-if="loading" class="loading-list">
        <div v-for="i in 5" :key="i" class="sk-item glass-card">
          <div class="sk-rank"></div>
          <div class="sk-body"><div class="sk-line w60"></div><div class="sk-line w40"></div></div>
        </div>
      </div>

      <div v-else class="rank-list">
        <div v-for="(w, idx) in works" :key="w.work_id" class="rank-item glass-card" @click="goWork(w.work_id)">
          <div class="rank-badge" :class="rankClass(idx)">{{ idx + 1 }}</div>
          <div class="rank-body">
            <div class="rank-title">{{ w.title }}</div>
            <div class="rank-meta">
              <router-link :to="`/profile/${w.user_id}`" class="rank-author" @click.stop>{{ w.username }}</router-link>
              <span class="rank-type">{{ typeLabel(w.type) }}</span>
              <span class="rank-words">{{ formatNum(w.word_count) }} 字</span>
            </div>
            <div class="rank-stats">
              <span class="stat">  {{ formatNum(w.views) }}</span>
              <span class="stat">❤️ {{ formatNum(w.likes_count) }}</span>
              <span class="stat">  {{ formatNum(w.comments_count) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 本周热门 -->
    <div v-else-if="activeTab === 'weekly'" class="rk-section">
      <div v-if="loading" class="loading-list">
        <div v-for="i in 5" :key="i" class="sk-item glass-card"><div class="sk-rank"></div><div class="sk-body"><div class="sk-line w60"></div></div></div>
      </div>
      <div v-else class="rank-list">
        <div v-for="(w, idx) in weekly" :key="w.work_id" class="rank-item glass-card" @click="goWork(w.work_id)">
          <div class="rank-badge" :class="rankClass(idx)">{{ idx + 1 }}</div>
          <div class="rank-body">
            <div class="rank-title">{{ w.title }}</div>
            <div class="rank-meta">
              <router-link :to="`/profile/${w.user_id}`" class="rank-author" @click.stop>{{ w.username }}</router-link>
              <span class="rank-type">{{ typeLabel(w.type) }}</span>
            </div>
            <div class="rank-stats">
              <span class="stat hot">  本周 +{{ w.recent_likes || 0 }}</span>
              <span class="stat hot">  本周 +{{ w.recent_comments || 0 }}</span>
              <span class="stat">  {{ formatNum(w.views) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新作榜 -->
    <div v-else-if="activeTab === 'new'" class="rk-section">
      <div v-if="loading" class="loading-list">
        <div v-for="i in 5" :key="i" class="sk-item glass-card"><div class="sk-rank"></div><div class="sk-body"><div class="sk-line w60"></div></div></div>
      </div>
      <div v-else class="rank-list">
        <div v-for="(w, idx) in newWorks" :key="w.work_id" class="rank-item glass-card" @click="goWork(w.work_id)">
          <div class="rank-badge new">{{ idx + 1 }}</div>
          <div class="rank-body">
            <div class="rank-title">{{ w.title }}</div>
            <div class="rank-meta">
              <router-link :to="`/profile/${w.user_id}`" class="rank-author" @click.stop>{{ w.username }}</router-link>
              <span class="rank-type">{{ typeLabel(w.type) }}</span>
              <span class="rank-time">{{ fmtDate(w.created_at) }}</span>
            </div>
            <div class="rank-stats">
              <span class="stat">  {{ formatNum(w.views) }}</span>
              <span class="stat">❤️ {{ formatNum(w.likes_count) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 作者榜 -->
    <div v-else-if="activeTab === 'authors'" class="rk-section">
      <div v-if="loading" class="loading-list">
        <div v-for="i in 5" :key="i" class="sk-item glass-card"><div class="sk-rank"></div><div class="sk-body"><div class="sk-line w60"></div></div></div>
      </div>
      <div v-else class="rank-list">
        <div v-for="(a, idx) in authors" :key="a.user_id" class="rank-item glass-card author-item" @click="goProfile(a.user_id)">
          <div class="rank-badge" :class="rankClass(idx)">{{ idx + 1 }}</div>
          <div class="rank-avatar">{{ a.username?.charAt(0) }}</div>
          <div class="rank-body">
            <div class="rank-title">{{ a.username }}</div>
            <div class="rank-meta" v-if="a.bio">{{ a.bio }}</div>
            <div class="rank-stats">
              <span class="stat">Lv.{{ a.level }}</span>
              <span class="stat">  {{ a.work_count }} 部作品</span>
              <span class="stat">  {{ formatNum(a.total_views) }}</span>
              <span class="stat">❤️ {{ formatNum(a.total_likes) }}</span>
            </div>
          </div>
          <div class="author-exp">{{ formatNum(a.exp) }} EXP</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../api/index.js'

const router = useRouter()
const activeTab = ref('works')
const metric = ref('hot')
const loading = ref(true)

const works = ref([])
const weekly = ref([])
const newWorks = ref([])
const authors = ref([])

const tabs = [
  { key: 'works', label: '综合榜', icon: ' ' },
  { key: 'weekly', label: '本周热门', icon: ' ' },
  { key: 'new', label: '新作榜', icon: '✨' },
  { key: 'authors', label: '作者榜', icon: ' ' },
]

const metrics = [
  { key: 'hot', label: '综合热度' },
  { key: 'views', label: '最多浏览' },
  { key: 'likes', label: '最多点赞' },
  { key: 'comments', label: '最多评论' },
]

onMounted(() => {
  loadWorks()
})

async function switchTab(tab) {
  activeTab.value = tab
  loading.value = true
  if (tab === 'works') await loadWorks()
  else if (tab === 'weekly') await loadWeekly()
  else if (tab === 'new') await loadNew()
  else if (tab === 'authors') await loadAuthors()
  loading.value = false
}

async function loadWorks() {
  loading.value = true
  const res = await api.get(`/api/rankings/works?metric=${metric.value}&limit=30`)
  if (res.code === 0) works.value = res.data.works
  loading.value = false
}

async function changeMetric(m) {
  metric.value = m
  await loadWorks()
}

async function loadWeekly() {
  const res = await api.get('/api/rankings/weekly?limit=20')
  if (res.code === 0) weekly.value = res.data.works
}

async function loadNew() {
  const res = await api.get('/api/rankings/new?limit=20')
  if (res.code === 0) newWorks.value = res.data.works
}

async function loadAuthors() {
  const res = await api.get('/api/rankings/authors?limit=20')
  if (res.code === 0) authors.value = res.data.authors
}

function goWork(id) { router.push(`/work/${id}`) }
function goProfile(id) { router.push(`/profile/${id}`) }

function rankClass(idx) {
  if (idx === 0) return 'gold'
  if (idx === 1) return 'silver'
  if (idx === 2) return 'bronze'
  return ''
}

function typeLabel(t) {
  return { novel: '小说', essay: '散文', poetry: '诗歌', script: '剧本', article: '随笔' }[t] || t
}

function formatNum(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return n
}

function fmtDate(d) {
  if (!d) return ''
  return d.slice(0, 10)
}
</script>

<style scoped>
.rk-header {
  margin-bottom: var(--space-xl);
}
.rk-header h2 { font-size: 1.8rem; margin-bottom: 4px; }
.header-sub { color: var(--text-muted); font-size: 0.9rem; }

/* Tab 切换 */
.rk-tabs {
  display: flex; gap: var(--space-sm);
  margin-bottom: var(--space-xl);
  flex-wrap: wrap;
}
.rk-tab {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 18px; font-size: 0.88rem;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-glass);
  color: var(--text-muted);
  cursor: pointer; transition: all 0.25s;
}
.rk-tab:hover {
  color: var(--text-primary);
  border-color: rgba(196, 163, 90, 0.2);
}
.rk-tab.active {
  background: rgba(196, 163, 90, 0.1);
  border-color: rgba(196, 163, 90, 0.3);
  color: var(--accent-primary);
}
.tab-icon { font-size: 1rem; }

/* 指标切换 */
.metric-bar {
  display: flex; gap: var(--space-sm);
  margin-bottom: var(--space-lg);
  flex-wrap: wrap;
}
.metric-btn {
  padding: 5px 14px; font-size: 0.8rem;
  border-radius: var(--radius-full);
  background: none; border: 1px solid var(--border-glass);
  color: var(--text-muted); cursor: pointer;
  transition: all 0.2s;
}
.metric-btn:hover { color: var(--text-primary); }
.metric-btn.active {
  background: rgba(196, 163, 90, 0.1);
  border-color: rgba(196, 163, 90, 0.3);
  color: var(--accent-primary);
}

/* 排行列表 */
.rank-list {
  display: flex; flex-direction: column; gap: var(--space-md);
}
.rank-item {
  display: flex; align-items: center; gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  cursor: pointer; transition: all 0.25s;
}
.rank-item:hover {
  border-color: rgba(196, 163, 90, 0.25);
  transform: translateX(4px);
}

.rank-badge {
  width: 32px; height: 32px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border-radius: 8px; font-size: 0.85rem; font-weight: 700;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-muted);
}
.rank-badge.gold {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(255, 180, 0, 0.1));
  color: #ffd700; border: 1px solid rgba(255, 215, 0, 0.3);
}
.rank-badge.silver {
  background: linear-gradient(135deg, rgba(192, 192, 192, 0.15), rgba(160, 160, 160, 0.08));
  color: #c0c0c0; border: 1px solid rgba(192, 192, 192, 0.25);
}
.rank-badge.bronze {
  background: linear-gradient(135deg, rgba(205, 127, 50, 0.15), rgba(180, 100, 30, 0.08));
  color: #cd7f32; border: 1px solid rgba(205, 127, 50, 0.25);
}
.rank-badge.new {
  background: rgba(100, 180, 255, 0.1);
  color: #6eb4ff;
}

.rank-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--accent-primary); color: var(--bg-primary);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.8rem; font-weight: 700; flex-shrink: 0;
}

.rank-body { flex: 1; min-width: 0; }
.rank-title {
  font-size: 0.95rem; font-weight: 600;
  color: var(--text-primary); margin-bottom: 2px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.rank-meta {
  display: flex; align-items: center; gap: var(--space-sm);
  font-size: 0.78rem; color: var(--text-muted);
  margin-bottom: 4px; flex-wrap: wrap;
}
.rank-author {
  color: var(--accent-primary); text-decoration: none;
}
.rank-author:hover { text-decoration: underline; }
.rank-type {
  padding: 1px 6px; border-radius: 4px;
  background: rgba(100, 180, 255, 0.08);
  color: #6eb4ff; font-size: 0.72rem;
}
.rank-words { font-size: 0.75rem; }
.rank-time { font-size: 0.75rem; }

.rank-stats {
  display: flex; gap: var(--space-md); flex-wrap: wrap;
}
.stat {
  font-size: 0.78rem; color: var(--text-muted);
}
.stat.hot { color: var(--accent-warm); }

.author-exp {
  font-family: var(--font-display);
  font-size: 0.85rem; font-weight: 600;
  color: var(--accent-primary); flex-shrink: 0;
  background: rgba(196, 163, 90, 0.08);
  padding: 4px 12px; border-radius: var(--radius-full);
}

/* Loading */
.loading-list { display: flex; flex-direction: column; gap: var(--space-md); }
.sk-item {
  display: flex; align-items: center; gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
}
.sk-rank {
  width: 32px; height: 32px; border-radius: 8px;
  background: var(--bg-glass);
}
.sk-body { flex: 1; display: flex; flex-direction: column; gap: 6px; }
.sk-line { height: 14px; border-radius: 6px; background: var(--bg-glass); }
.sk-line.w60 { width: 60%; }
.sk-line.w40 { width: 40%; }

@media (max-width: 640px) {
  .rank-item { padding: var(--space-sm) var(--space-md); }
  .rank-stats { gap: var(--space-sm); }
  .author-exp { display: none; }
}
</style>
