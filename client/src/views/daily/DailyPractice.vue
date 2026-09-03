<template>
  <div class="page-container">
    <!-- 头部 -->
    <div class="dp-header">
      <div class="header-left">
        <h2>每日一练</h2>
        <p class="header-sub">每天一个写作练习，磨炼你的创作功力</p>
      </div>
      <div v-if="userStore.isLoggedIn && streakData" class="streak-info">
        <div class="streak-num">{{ streakData.streak }}</div>
        <div class="streak-label">连续打卡</div>
      </div>
    </div>

    <!-- 今日题目 -->
    <div v-if="todayPrompt" class="today-card glass-card">
      <div class="today-top">
        <span class="today-badge">今日练习</span>
        <span class="type-badge">{{ typeLabel(todayPrompt.type) }}</span>
        <span class="diff-badge" :class="todayPrompt.difficulty">{{ diffLabel(todayPrompt.difficulty) }}</span>
        <span class="word-range">{{ todayPrompt.word_min }}-{{ todayPrompt.word_max }} 字</span>
      </div>
      <h3 class="today-title">{{ todayPrompt.title }}</h3>
      <p class="today-desc">{{ todayPrompt.description }}</p>

      <!-- 已提交 -->
      <div v-if="submitted" class="submitted-area">
        <div class="submitted-badge">  已完成</div>
        <div class="submitted-content">{{ mySubmission?.content }}</div>
        <div class="submitted-meta">{{ mySubmission?.word_count }} 字 · {{ fmtTime(mySubmission?.created_at) }}</div>
      </div>

      <!-- 提交表单 -->
      <div v-else-if="userStore.isLoggedIn" class="submit-area">
        <textarea v-model="submitContent" rows="6" placeholder="写下你的练习作品..." class="submit-input"></textarea>
        <div class="submit-bar">
          <span class="word-count" :class="{ over: submitContent.length > todayPrompt.word_max }">
            {{ submitContent.length }} / {{ todayPrompt.word_max }} 字
          </span>
          <button class="btn btn-primary btn-sm" @click="handleSubmit" :disabled="!submitContent.trim() || submitting">
            {{ submitting ? '提交中...' : '提交作品' }}
          </button>
        </div>
      </div>

      <div v-else class="login-hint">
        请<router-link to="/login">登录</router-link>后提交练习
      </div>
    </div>

    <!-- 加载 -->
    <div v-else-if="loading" class="loading-card glass-card">
      <div class="sk-line" style="width:40%;height:20px"></div>
      <div class="sk-line" style="width:100%;height:60px;margin-top:12px"></div>
    </div>

    <!-- 他人作品 -->
    <div v-if="submissions.length > 0" class="section">
      <div class="section-header">
        <h3>佳作展示</h3>
        <div class="sort-tabs">
          <span class="sort-tab" :class="{ active: sort === 'hot' }" @click="changeSort('hot')">最热</span>
          <span class="sort-tab" :class="{ active: sort === 'new' }" @click="changeSort('new')">最新</span>
        </div>
      </div>

      <div class="submissions-list">
        <div v-for="s in submissions" :key="s.submission_id" class="sub-card glass-card">
          <div class="sub-header">
            <div class="sub-user">
              <span class="sub-avatar">{{ s.username?.charAt(0) }}</span>
              <router-link :to="`/profile/${s.user_id}`" class="sub-name">{{ s.username }}</router-link>
            </div>
            <span class="sub-time">{{ fmtTime(s.created_at) }}</span>
          </div>
          <div class="sub-content">{{ s.content }}</div>
          <div class="sub-footer">
            <span class="sub-words">{{ s.word_count }} 字</span>
            <button class="like-btn" :class="{ liked: s._liked }" @click="toggleLike(s)">
              {{ s._liked ? '❤️' : ' ' }} {{ s.likes_count || 0 }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="subTotal > submissions.length" class="load-more">
        <button class="btn btn-ghost btn-sm" @click="loadMore">加载更多</button>
      </div>
    </div>

    <!-- 历史题目 -->
    <div class="section">
      <h3>往期练习</h3>
      <div class="history-grid">
        <div v-for="p in history" :key="p.prompt_id" class="hist-card glass-card" @click="viewPrompt(p)">
          <div class="hist-top">
            <span class="type-badge small">{{ typeLabel(p.type) }}</span>
            <span class="hist-count">{{ p.submission_count || 0 }} 份作品</span>
          </div>
          <h4 class="hist-title">{{ p.title }}</h4>
          <p class="hist-date">{{ p.active_date }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/index.js'
import { useUserStore } from '../../stores/user.js'
import { useToast } from '../../composables/useToast.js'
const toast = useToast()
const userStore = useUserStore()

const todayPrompt = ref(null)
const submitted = ref(false)
const mySubmission = ref(null)
const submitContent = ref('')
const submitting = ref(false)
const loading = ref(true)
const streakData = ref(null)

const submissions = ref([])
const subTotal = ref(0)
const sort = ref('hot')
const subPage = ref(1)

const history = ref([])

onMounted(async () => {
  await Promise.all([loadToday(), loadHistory()])
  if (userStore.isLoggedIn) {
    await loadStreak()
  }
})

async function loadToday() {
  loading.value = true
  const res = await api.get('/api/daily/today')
  if (res.code === 0) {
    todayPrompt.value = res.data.prompt
    submitted.value = res.data.submitted
    mySubmission.value = res.data.submission
    await loadSubmissions()
  }
  loading.value = false
}

async function loadSubmissions() {
  if (!todayPrompt.value) return
  const res = await api.get(`/api/daily/submissions/${todayPrompt.value.prompt_id}?sort=${sort.value}&page=${subPage.value}`)
  if (res.code === 0) {
    submissions.value = res.data.submissions
    subTotal.value = res.data.total
  }
}

async function loadMore() {
  subPage.value++
  const res = await api.get(`/api/daily/submissions/${todayPrompt.value.prompt_id}?sort=${sort.value}&page=${subPage.value}`)
  if (res.code === 0) submissions.value.push(...res.data.submissions)
}

function changeSort(s) {
  sort.value = s
  subPage.value = 1
  loadSubmissions()
}

async function handleSubmit() {
  if (!submitContent.value.trim()) return
  submitting.value = true
  const res = await api.post('/api/daily/submit', {
    prompt_id: todayPrompt.value.prompt_id,
    content: submitContent.value,
  })
  submitting.value = false
  if (res.code === 0) {
    submitted.value = true
    mySubmission.value = { content: submitContent.value, word_count: submitContent.value.length, created_at: new Date().toISOString() }
    submitContent.value = ''
    await loadSubmissions()
    await loadStreak()
  } else {
    toast.info(res.msg)
  }
}

async function toggleLike(s) {
  if (!userStore.isLoggedIn) { toast.error('请先登录'); return }
  const res = await api.post('/api/daily/like', { submission_id: s.submission_id })
  if (res.code === 0) {
    s._liked = res.data.liked
    s.likes_count += res.data.liked ? 1 : -1
  }
}

async function loadStreak() {
  const res = await api.get('/api/daily/streak')
  if (res.code === 0) streakData.value = res.data
}

async function loadHistory() {
  const res = await api.get('/api/daily/history?page_size=12')
  if (res.code === 0) history.value = res.data.prompts
}

async function viewPrompt(p) {
  loading.value = true
  const res = await api.get(`/api/daily/prompt/${p.prompt_id}`)
  if (res.code === 0) {
    todayPrompt.value = res.data.prompt
    submitted.value = res.data.submitted
    mySubmission.value = res.data.submission
    subPage.value = 1
    await loadSubmissions()
  }
  loading.value = false
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function typeLabel(t) {
  return { micro_fiction: '微小说', poetry: '诗歌', dialogue: '对话', description: '描写', continuation: '续写' }[t] || t
}
function diffLabel(d) {
  return { easy: '入门', medium: '进阶', hard: '挑战' }[d] || d
}
function fmtTime(d) {
  if (!d) return ''
  return d.slice(0, 16).replace('T', ' ')
}
</script>

<style scoped>
.dp-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: var(--space-xl);
}
.header-left h2 { font-size: 1.8rem; margin-bottom: 4px; }
.header-sub { color: var(--text-muted); font-size: 0.9rem; }

.streak-info {
  text-align: center; padding: 8px 20px;
  background: rgba(196, 163, 90, 0.08);
  border: 1px solid rgba(196, 163, 90, 0.15);
  border-radius: var(--radius-lg);
}
.streak-num {
  font-family: var(--font-display);
  font-size: 2rem; font-weight: 700;
  color: var(--accent-primary);
  line-height: 1;
}
.streak-label { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }

/* 今日题目卡 */
.today-card {
  padding: var(--space-xl); margin-bottom: var(--space-2xl);
}
.today-top {
  display: flex; gap: var(--space-sm); align-items: center;
  margin-bottom: var(--space-md); flex-wrap: wrap;
}
.today-badge {
  font-size: 0.8rem; font-weight: 700;
  color: var(--accent-primary);
  padding: 2px 10px;
  background: rgba(196, 163, 90, 0.12);
  border-radius: var(--radius-full);
}
.type-badge {
  font-size: 0.75rem; padding: 2px 8px;
  border-radius: var(--radius-full);
  background: rgba(100, 180, 255, 0.1);
  color: #6eb4ff;
}
.type-badge.small { font-size: 0.7rem; padding: 1px 6px; }
.diff-badge {
  font-size: 0.7rem; padding: 2px 8px;
  border-radius: var(--radius-full);
}
.diff-badge.easy { background: rgba(100, 200, 100, 0.1); color: #6bc86b; }
.diff-badge.medium { background: rgba(255, 200, 50, 0.1); color: #ffc832; }
.diff-badge.hard { background: rgba(255, 100, 100, 0.1); color: #ff6464; }
.word-range { font-size: 0.75rem; color: var(--text-muted); }

.today-title {
  font-family: var(--font-serif);
  font-size: 1.3rem; margin-bottom: var(--space-sm);
}
.today-desc {
  font-size: 0.95rem; line-height: 1.8;
  color: var(--text-secondary);
  margin-bottom: var(--space-lg);
}

/* 已提交 */
.submitted-area {
  padding: var(--space-lg);
  background: rgba(100, 200, 100, 0.04);
  border: 1px solid rgba(100, 200, 100, 0.15);
  border-radius: var(--radius-md);
}
.submitted-badge {
  font-size: 0.85rem; color: #6bc86b;
  margin-bottom: var(--space-sm);
}
.submitted-content {
  font-family: var(--font-serif);
  font-size: 0.95rem; line-height: 1.9;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}
.submitted-meta { font-size: 0.8rem; color: var(--text-muted); }

/* 提交表单 */
.submit-area { margin-top: var(--space-md); }
.submit-input {
  width: 100%; resize: vertical;
  padding: 12px; font-size: 0.95rem; line-height: 1.8;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(196, 163, 90, 0.1);
  color: var(--text-primary);
  font-family: var(--font-serif);
}
.submit-input:focus { border-color: rgba(196, 163, 90, 0.25); outline: none; }
.submit-input::placeholder { color: var(--text-muted); }
.submit-bar {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: var(--space-sm);
}
.word-count { font-size: 0.8rem; color: var(--text-muted); }
.word-count.over { color: #ff6464; }

.login-hint {
  font-size: 0.9rem; color: var(--text-muted);
  margin-top: var(--space-md);
}
.login-hint a { color: var(--accent-primary); }

.loading-card { padding: var(--space-xl); }
.sk-line { border-radius: 6px; background: var(--bg-glass); }

/* 他人作品 */
.section { margin-bottom: var(--space-2xl); }
.section-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: var(--space-lg);
}
.section-header h3 { font-size: 1.2rem; }
.sort-tabs { display: flex; gap: var(--space-sm); }
.sort-tab {
  font-size: 0.82rem; padding: 4px 12px;
  border-radius: var(--radius-full);
  cursor: pointer; transition: all 0.2s;
  color: var(--text-muted);
}
.sort-tab:hover { color: var(--text-primary); }
.sort-tab.active {
  background: rgba(196, 163, 90, 0.1);
  color: var(--accent-primary);
}

.submissions-list {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-lg);
}
.sub-card { padding: var(--space-lg); }
.sub-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: var(--space-md);
}
.sub-user { display: flex; align-items: center; gap: var(--space-sm); }
.sub-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--accent-primary); color: var(--bg-primary);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; font-weight: 700;
}
.sub-name {
  font-size: 0.85rem; color: var(--text-primary);
  text-decoration: none;
}
.sub-name:hover { color: var(--accent-primary); }
.sub-time { font-size: 0.75rem; color: var(--text-muted); }
.sub-content {
  font-family: var(--font-serif);
  font-size: 0.92rem; line-height: 1.9;
  color: var(--text-secondary);
  margin-bottom: var(--space-md);
}
.sub-footer {
  display: flex; justify-content: space-between; align-items: center;
}
.sub-words { font-size: 0.78rem; color: var(--text-muted); }
.like-btn {
  font-size: 0.8rem; padding: 2px 10px;
  border-radius: var(--radius-full);
  background: none; border: 1px solid var(--border-glass);
  color: var(--text-muted); cursor: pointer;
  transition: all 0.2s;
}
.like-btn:hover { border-color: rgba(255, 100, 100, 0.3); }
.like-btn.liked { color: #ff6464; border-color: rgba(255, 100, 100, 0.3); }

.load-more { text-align: center; margin-top: var(--space-lg); }

/* 历史题目 */
.history-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-md);
}
.hist-card {
  padding: var(--space-md); cursor: pointer;
  transition: all 0.25s ease;
}
.hist-card:hover {
  transform: translateY(-2px);
  border-color: rgba(196, 163, 90, 0.2);
}
.hist-top {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: var(--space-sm);
}
.hist-count { font-size: 0.72rem; color: var(--text-muted); }
.hist-title {
  font-size: 0.95rem; color: var(--text-primary);
  margin-bottom: 4px;
}
.hist-date { font-size: 0.75rem; color: var(--text-muted); }
</style>
