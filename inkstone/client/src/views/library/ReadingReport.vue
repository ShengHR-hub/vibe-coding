<template>
  <div class="page-container" v-if="report">
    <ReadingNav />

    <!-- 封面 -->
    <section class="cover-section">
      <div class="cover-glow"></div>
      <div class="cover-content">
        <p class="cover-tag">ANNUAL REPORT</p>
        <h1 class="cover-title">{{ report.year }}<br>阅读报告</h1>
        <p class="cover-user">{{ userStore.user?.username || '读者' }} 的阅读之旅</p>
        <div class="cover-divider"></div>
        <p class="cover-hint">&darr; 向下滑动查看</p>
      </div>
    </section>

    <!-- 核心数据 -->
    <section class="report-section reveal-section">
      <p class="sec-tag">Overview <span class="tag-cn">总览</span></p>
      <h2 class="sec-heading">阅读总览</h2>
      <div class="stats-grid">
        <div class="stat-card glass-card" v-for="s in statCards" :key="s.label">
          <span class="stat-number">{{ s.value }}</span>
          <span class="stat-unit">{{ s.unit }}</span>
          <span class="stat-label">{{ s.label }}</span>
          <div class="card-shimmer"></div>
        </div>
      </div>
    </section>

    <!-- 阅读之最 -->
    <section class="report-section reveal-section" v-if="report.longest_book">
      <p class="sec-tag">Highlight <span class="tag-cn">之最</span></p>
      <h2 class="sec-heading">阅读之最</h2>
      <div class="record-card glass-card">
        <div class="record-icon-box">
          <span class="record-icon">&#128214;</span>
        </div>
        <div class="record-info">
          <span class="record-label">读过最长的书</span>
          <span class="record-value">{{ report.longest_book.title }}</span>
          <span class="record-meta">{{ formatWordCount(report.longest_book.word_count) }} 字</span>
        </div>
        <div class="card-shimmer"></div>
      </div>
    </section>

    <!-- 类型偏好 -->
    <section class="report-section reveal-section" v-if="report.type_distribution?.length">
      <p class="sec-tag">Preference <span class="tag-cn">偏好</span></p>
      <h2 class="sec-heading">类型偏好</h2>
      <div class="type-bars glass-card">
        <div v-for="(t, i) in report.type_distribution" :key="t.book_type" class="type-bar-item">
          <span class="type-label">{{ typeLabel(t.book_type) }}</span>
          <div class="type-bar-track">
            <div class="type-bar-fill" :style="{ width: barWidth(t) + '%', animationDelay: (i * 0.15) + 's' }"></div>
          </div>
          <span class="type-count">{{ t.cnt }} 本</span>
        </div>
        <div class="card-shimmer"></div>
      </div>
    </section>

    <!-- 月度曲线 -->
    <section class="report-section reveal-section" v-if="report.monthly_data?.length">
      <p class="sec-tag">Monthly <span class="tag-cn">月度</span></p>
      <h2 class="sec-heading">月度阅读</h2>
      <div class="chart-container glass-card">
        <div class="chart-bars">
          <div v-for="m in 12" :key="m" class="chart-col">
            <div class="chart-bar-wrap">
              <div class="chart-bar" :style="{ height: getMonthHeight(m) + '%' }"></div>
              <span class="chart-value" v-if="getMonthMinutes(m) > 0">{{ getMonthMinutes(m) }}</span>
            </div>
            <span class="chart-label">{{ m }}月</span>
          </div>
        </div>
        <div class="card-shimmer"></div>
      </div>
    </section>

    <!-- 阅读目标 -->
    <section class="report-section reveal-section">
      <p class="sec-tag">Goal <span class="tag-cn">目标</span></p>
      <h2 class="sec-heading">月度目标</h2>
      <div class="goal-card glass-card">
        <div v-if="!editingGoal && (goalData?.target_minutes || goalData?.target_books)">
          <div class="goal-progress-row">
            <div class="goal-item">
              <span class="goal-label">阅读时长</span>
              <div class="goal-bar-track">
                <div class="goal-bar-fill" :style="{ width: minutesProgress + '%' }"></div>
              </div>
              <span class="goal-text">{{ goalData?.current_minutes || 0 }}/{{ goalData?.target_minutes || 0 }} 分钟</span>
            </div>
            <div class="goal-item">
              <span class="goal-label">阅读本数</span>
              <div class="goal-bar-track">
                <div class="goal-bar-fill" :style="{ width: booksProgress + '%' }"></div>
              </div>
              <span class="goal-text">{{ goalData?.current_books || 0 }}/{{ goalData?.target_books || 0 }} 本</span>
            </div>
          </div>
          <button class="btn btn-ghost btn-sm" style="margin-top: var(--space-md)" @click="editingGoal = true">修改目标</button>
        </div>
        <div v-else-if="editingGoal">
          <div class="goal-form">
            <div class="goal-input-row">
              <label>每月阅读</label>
              <input v-model.number="goalForm.minutes" type="number" min="0" placeholder="分钟" />
              <span>分钟</span>
            </div>
            <div class="goal-input-row">
              <label>每月读书</label>
              <input v-model.number="goalForm.books" type="number" min="0" placeholder="本" />
              <span>本</span>
            </div>
            <div class="goal-actions">
              <button class="btn btn-primary btn-sm" @click="saveGoal">保存</button>
              <button class="btn btn-ghost btn-sm" @click="editingGoal = false">取消</button>
            </div>
          </div>
        </div>
        <div v-else class="goal-empty">
          <p>设定本月阅读目标，坚持打卡</p>
          <button class="btn btn-primary btn-sm" @click="editingGoal = true">设定目标</button>
        </div>
        <div class="card-shimmer"></div>
      </div>
    </section>

    <!-- 阅读统计 -->
    <section class="report-section reveal-section" v-if="extraStats">
      <p class="sec-tag">Stats <span class="tag-cn">统计</span></p>
      <h2 class="sec-heading">阅读统计</h2>
      <div class="extra-stats-grid">
        <div class="extra-stat-card glass-card">
          <span class="extra-icon">&#128293;</span>
          <span class="extra-value">{{ extraStats.max_streak }}</span>
          <span class="extra-unit">天</span>
          <span class="extra-label">最长连续打卡</span>
        </div>
        <div class="extra-stat-card glass-card">
          <span class="extra-icon">&#9889;</span>
          <span class="extra-value">{{ extraStats.reading_speed }}</span>
          <span class="extra-unit">字/分钟</span>
          <span class="extra-label">平均阅读速度</span>
        </div>
        <div class="extra-stat-card glass-card">
          <span class="extra-icon">&#128214;</span>
          <span class="extra-value">{{ formatNumber(extraStats.total_words_read) }}</span>
          <span class="extra-unit">字</span>
          <span class="extra-label">累计阅读字数</span>
        </div>
      </div>
    </section>

    <!-- 打卡日历 -->
    <section class="report-section reveal-section">
      <p class="sec-tag">Calendar <span class="tag-cn">日历</span></p>
      <h2 class="sec-heading">打卡日历</h2>
      <div class="calendar-card glass-card">
        <div class="calendar-header">
          <button class="btn btn-ghost btn-xs" @click="changeMonth(-1)">&larr;</button>
          <span>{{ calendarMonth }}</span>
          <button class="btn btn-ghost btn-xs" @click="changeMonth(1)">&rarr;</button>
        </div>
        <div class="calendar-weekdays">
          <span v-for="w in ['一','二','三','四','五','六','日']" :key="w">{{ w }}</span>
        </div>
        <div class="calendar-grid">
          <div v-for="(d, i) in calendarDays" :key="i"
               class="calendar-day" :class="{ checked: d.checked, today: d.isToday, empty: !d.day }">
            <span v-if="d.day">{{ d.day }}</span>
          </div>
        </div>
        <div class="calendar-legend">
          <span class="legend-item"><span class="legend-dot checked"></span> 已打卡</span>
          <span class="legend-item"><span class="legend-dot today"></span> 今天</span>
        </div>
        <div class="card-shimmer"></div>
      </div>
    </section>

    <!-- 阅读热力图 -->
    <section class="report-section reveal-section">
      <p class="sec-tag">Heatmap <span class="tag-cn">热力图</span></p>
      <h2 class="sec-heading">阅读活跃度</h2>
      <div class="heatmap-card glass-card">
        <ReadingHeatmap />
      </div>
    </section>

    <!-- 底部 -->
    <section class="report-section footer-section">
      <div class="footer-divider"></div>
      <p class="footer-text">墨池 &middot; 记录每一段阅读时光</p>
      <router-link to="/bookshelf" class="btn btn-primary">返回书架</router-link>
    </section>
  </div>

  <!-- 加载态 -->
  <div v-else class="page-container center">
    <div class="loading-spinner"></div>
    <p class="loading-text">正在生成报告...</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { api } from '../../api/index.js'
import { useUserStore } from '../../stores/user.js'
import ReadingNav from '../../components/ReadingNav.vue'
import ReadingHeatmap from '../../components/ReadingHeatmap.vue'

const userStore = useUserStore()
const report = ref(null)

// 阅读目标
const goalData = ref(null)
const editingGoal = ref(false)
const goalForm = ref({ minutes: 0, books: 0 })

// 打卡日历
const calendarYear = ref(new Date().getFullYear())
const calendarMonthNum = ref(new Date().getMonth() + 1)
const checkinDays = ref([])

// 阅读统计
const extraStats = ref(null)

onMounted(async () => {
  const res = await api.get('/api/reading/report/annual')
  if (res.code === 0) {
    report.value = res.data
    await nextTick()
    initReveal()
  }
  // 加载目标、日历、统计
  if (userStore.isLoggedIn) {
    loadGoal()
    loadCalendar()
    loadExtraStats()
  }
})

const statCards = computed(() => {
  if (!report.value) return []
  const r = report.value
  return [
    { value: formatNumber(r.total_minutes), unit: '分钟', label: '阅读时长' },
    { value: r.books_read, unit: '本', label: '读过的书' },
    { value: formatNumber(r.total_pages), unit: '页', label: '翻过的页' },
    { value: r.total_active_days, unit: '天', label: '活跃天数' },
  ]
})

const maxTypeCount = computed(() => {
  if (!report.value?.type_distribution?.length) return 1
  return Math.max(...report.value.type_distribution.map(t => t.cnt), 1)
})

function barWidth(t) {
  return (t.cnt / maxTypeCount.value) * 100
}

function getMonthHeight(month) {
  if (!report.value?.monthly_data?.length) return 0
  const entry = report.value.monthly_data.find(m => m.month === month)
  if (!entry) return 0
  const max = Math.max(...report.value.monthly_data.map(m => m.minutes), 1)
  return (entry.minutes / max) * 100
}

function getMonthMinutes(month) {
  if (!report.value?.monthly_data?.length) return 0
  const entry = report.value.monthly_data.find(m => m.month === month)
  return entry ? entry.minutes : 0
}

function formatNumber(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n.toLocaleString()
}

function formatWordCount(wc) {
  if (!wc) return '0'
  if (wc >= 10000) return (wc / 10000).toFixed(1) + '万'
  return wc.toLocaleString()
}

function typeLabel(t) {
  return { novel: '小说', poetry: '诗歌', essay: '散文', webfiction: '网文', script: '剧本' }[t] || t || '其他'
}

// 滚动渐显
function initReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('revealed')
        observer.unobserve(e.target)
      }
    })
  }, { threshold: 0.15 })
  document.querySelectorAll('.reveal-section').forEach(el => observer.observe(el))
}

// ====== 阅读目标 ======
async function loadGoal() {
  const res = await api.get('/api/reading/checkin/goals')
  if (res.code === 0) {
    goalData.value = res.data.goal
    if (goalData.value) {
      goalForm.value.minutes = goalData.value.target_minutes
      goalForm.value.books = goalData.value.target_books
    }
  }
}

async function loadExtraStats() {
  const res = await api.get('/api/reading/report/stats')
  if (res.code === 0) extraStats.value = res.data
}

async function saveGoal() {
  const res = await api.post('/api/reading/checkin/goals', {
    target_minutes: goalForm.value.minutes || 0,
    target_books: goalForm.value.books || 0,
  })
  if (res.code === 0) {
    editingGoal.value = false
    loadGoal()
  }
}

const minutesProgress = computed(() => {
  if (!goalData.value?.target_minutes) return 0
  return Math.min(100, (goalData.value.current_minutes / goalData.value.target_minutes) * 100)
})

const booksProgress = computed(() => {
  if (!goalData.value?.target_books) return 0
  return Math.min(100, (goalData.value.current_books / goalData.value.target_books) * 100)
})

// ====== 打卡日历 ======
const calendarMonth = computed(() => `${calendarYear.value}年${calendarMonthNum.value}月`)

async function loadCalendar() {
  const month = `${calendarYear.value}-${String(calendarMonthNum.value).padStart(2, '0')}`
  const res = await api.get(`/api/reading/checkin/calendar?month=${month}`)
  if (res.code === 0) {
    checkinDays.value = res.data.days.map(d => d.checkin_date)
  }
}

function changeMonth(delta) {
  calendarMonthNum.value += delta
  if (calendarMonthNum.value > 12) {
    calendarMonthNum.value = 1
    calendarYear.value++
  } else if (calendarMonthNum.value < 1) {
    calendarMonthNum.value = 12
    calendarYear.value--
  }
  loadCalendar()
}

const calendarDays = computed(() => {
  const year = calendarYear.value
  const month = calendarMonthNum.value
  const firstDay = new Date(year, month - 1, 1)
  const lastDay = new Date(year, month, 0)
  const daysInMonth = lastDay.getDate()
  const startWeekday = (firstDay.getDay() + 6) % 7 // 周一=0
  const today = new Date()
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

  const days = []
  // 填充空白
  for (let i = 0; i < startWeekday; i++) days.push({ day: 0, checked: false, isToday: false })
  // 填充日期
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    days.push({
      day: d,
      checked: checkinDays.value.includes(dateStr),
      isToday: dateStr === todayStr,
    })
  }
  return days
})
</script>

<style scoped>
.page-container { padding-top: 0; }

/* ====== 封面 ====== */
.cover-section {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  text-align: center; position: relative; overflow: hidden;
}
.cover-glow {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 500px; height: 500px; border-radius: 50%;
  background: radial-gradient(circle, rgba(196,163,90,0.06), transparent 70%);
  pointer-events: none;
}
.cover-content { position: relative; z-index: 1; animation: fadeInUp 0.8s ease-out; }
.cover-tag {
  font-family: var(--font-display); font-size: 0.75rem; font-weight: 600;
  letter-spacing: 0.35em; color: var(--accent-primary); text-transform: uppercase;
  opacity: 0.7; margin-bottom: 1.5rem;
}
.cover-title {
  font-family: var(--font-serif); font-size: clamp(2.5rem, 6vw, 4rem); font-weight: 700;
  color: var(--text-primary); line-height: 1.2; letter-spacing: 0.02em;
  margin-bottom: 1.5rem;
}
.cover-user { font-size: 1rem; color: var(--text-muted); letter-spacing: 0.06em; }
.cover-divider {
  width: 50px; height: 1px; background: var(--accent-primary);
  opacity: 0.4; margin: 2rem auto;
}
.cover-hint {
  font-size: 0.72rem; color: var(--text-muted); letter-spacing: 0.2em;
  opacity: 0.5; animation: bounce 2s ease-in-out infinite;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(8px); }
}

/* ====== 通用段落 ====== */
.report-section {
  max-width: 720px; margin: 0 auto;
  padding: var(--space-2xl) var(--space-lg);
}
.sec-tag {
  font-family: var(--font-display); font-size: 0.78rem; font-weight: 600;
  letter-spacing: 0.25em; color: var(--accent-primary); text-transform: uppercase;
  text-align: center; margin-bottom: 0.6rem; opacity: 0.7;
}
.tag-cn {
  font-family: var(--font-sans); font-size: 0.72rem; font-weight: 400;
  letter-spacing: 0.12em; color: var(--text-muted); margin-left: 0.4rem;
  text-transform: none;
}
.sec-heading {
  font-family: var(--font-serif); font-size: 1.6rem; font-weight: 700;
  color: var(--text-primary); text-align: center; margin-bottom: var(--space-xl);
  letter-spacing: 0.02em;
}

/* 滚动渐显 */
.reveal-section { opacity: 0; transform: translateY(40px); transition: all 0.7s cubic-bezier(0.16, 1, 0.3, 1); }
.reveal-section.revealed { opacity: 1; transform: translateY(0); }

/* ====== 核心数据 ====== */
.stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-lg); }
.stat-card {
  text-align: center; padding: var(--space-xl); position: relative; overflow: hidden;
  transition: all 0.35s ease;
}
.stat-card:hover {
  border-color: rgba(196,163,90,0.2);
  transform: translateY(-3px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.3);
}
.stat-number {
  display: block; font-size: 2.8rem; font-weight: 700;
  font-family: var(--font-serif); line-height: 1;
  background: linear-gradient(135deg, #e8e6f0, #c4a35a);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
.stat-unit { font-size: 0.82rem; color: var(--accent-primary); opacity: 0.7; }
.stat-label {
  display: block; font-size: 0.8rem; color: var(--text-muted);
  margin-top: var(--space-sm); letter-spacing: 0.04em;
}

/* ====== 阅读之最 ====== */
.record-card {
  display: flex; align-items: center; gap: var(--space-lg);
  padding: var(--space-xl); position: relative; overflow: hidden;
  transition: all 0.35s ease;
}
.record-card:hover { border-color: rgba(196,163,90,0.2); transform: translateY(-2px); }
.record-icon-box {
  width: 56px; height: 56px; border-radius: 50%; flex-shrink: 0;
  background: rgba(196,163,90,0.08); border: 1px solid rgba(196,163,90,0.15);
  display: flex; align-items: center; justify-content: center;
}
.record-icon { font-size: 1.5rem; }
.record-label { display: block; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px; }
.record-value { display: block; font-size: 1.1rem; font-weight: 600; color: var(--text-primary); margin-bottom: 2px; }
.record-meta { font-size: 0.8rem; color: var(--accent-primary); opacity: 0.8; }

/* ====== 类型偏好 ====== */
.type-bars { padding: var(--space-xl); position: relative; overflow: hidden; }
.type-bars:hover { border-color: rgba(196,163,90,0.15); }
.type-bar-item { display: flex; align-items: center; gap: var(--space-md); }
.type-bar-item + .type-bar-item { margin-top: var(--space-md); }
.type-label {
  font-size: 0.8rem; color: var(--text-secondary); width: 40px;
  text-align: right; flex-shrink: 0;
}
.type-bar-track {
  flex: 1; height: 8px; background: rgba(255,255,255,0.04);
  border-radius: 4px; overflow: hidden;
}
.type-bar-fill {
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, var(--accent-primary), rgba(196,163,90,0.3));
  animation: barGrow 0.8s ease-out both;
}
@keyframes barGrow {
  from { width: 0 !important; }
}
.type-count { font-size: 0.75rem; color: var(--text-muted); width: 40px; flex-shrink: 0; }

/* ====== 月度图表 ====== */
.chart-container { padding: var(--space-xl); position: relative; overflow: hidden; }
.chart-container:hover { border-color: rgba(196,163,90,0.15); }
.chart-bars { display: flex; align-items: flex-end; gap: 4px; height: 220px; padding-top: 24px; }
.chart-col {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  height: 100%; justify-content: flex-end;
}
.chart-bar-wrap {
  flex: 1; width: 100%; display: flex; flex-direction: column;
  align-items: center; justify-content: flex-end; position: relative;
}
.chart-bar {
  width: 100%; min-height: 2px; border-radius: 3px 3px 0 0;
  background: linear-gradient(180deg, var(--accent-primary), rgba(196,163,90,0.15));
  transition: height 0.6s ease;
}
.chart-value {
  font-size: 0.6rem; color: var(--accent-primary); opacity: 0.7;
  position: absolute; top: -18px; white-space: nowrap;
}
.chart-label { font-size: 0.65rem; color: var(--text-muted); margin-top: 8px; }

/* ====== 阅读目标 ====== */
.goal-card { padding: var(--space-xl); position: relative; overflow: hidden; }
.goal-card:hover { border-color: rgba(196,163,90,0.15); }
.goal-progress-row { display: flex; flex-direction: column; gap: var(--space-lg); }
.goal-item {}
.goal-label { display: block; font-size: 0.82rem; color: var(--text-muted); margin-bottom: var(--space-sm); }
.goal-bar-track { height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden; margin-bottom: 4px; }
.goal-bar-fill { height: 100%; background: linear-gradient(90deg, var(--accent-primary), var(--accent-warm)); border-radius: 4px; transition: width 0.6s ease; }
.goal-text { font-size: 0.78rem; color: var(--text-secondary); }
.goal-form { display: flex; flex-direction: column; gap: var(--space-md); }
.goal-input-row { display: flex; align-items: center; gap: var(--space-sm); }
.goal-input-row label { font-size: 0.85rem; color: var(--text-muted); width: 70px; }
.goal-input-row input {
  width: 80px; padding: 6px 10px; font-size: 0.85rem;
  background: rgba(255,255,255,0.06); color: var(--text-primary);
  border: 1px solid var(--border-glass); border-radius: var(--radius-sm); outline: none;
}
.goal-input-row input:focus { border-color: var(--accent-primary); }
.goal-input-row span { font-size: 0.82rem; color: var(--text-muted); }
.goal-actions { display: flex; gap: var(--space-sm); margin-top: var(--space-sm); }
.goal-empty { text-align: center; padding: var(--space-lg) 0; }
.goal-empty p { font-size: 0.85rem; color: var(--text-muted); margin-bottom: var(--space-md); }

/* ====== 阅读统计 ====== */
.extra-stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-lg); }
.extra-stat-card {
  text-align: center; padding: var(--space-xl); position: relative; overflow: hidden;
  transition: all 0.35s ease;
}
.extra-stat-card:hover { border-color: rgba(196,163,90,0.2); transform: translateY(-3px); }
.extra-icon { display: block; font-size: 1.8rem; margin-bottom: var(--space-sm); }
.extra-value {
  display: block; font-size: 2rem; font-weight: 700;
  font-family: var(--font-serif); line-height: 1;
  background: linear-gradient(135deg, #e8e6f0, #c4a35a);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
.extra-unit { font-size: 0.75rem; color: var(--accent-primary); opacity: 0.7; }
.extra-label {
  display: block; font-size: 0.78rem; color: var(--text-muted);
  margin-top: var(--space-sm); letter-spacing: 0.04em;
}

/* ====== 打卡日历 ====== */
.calendar-card { padding: var(--space-xl); position: relative; overflow: hidden; }
.calendar-card:hover { border-color: rgba(196,163,90,0.15); }
.calendar-header { display: flex; justify-content: center; align-items: center; gap: var(--space-lg); margin-bottom: var(--space-lg); }
.calendar-header span { font-size: 0.95rem; color: var(--text-primary); font-weight: 600; }
.calendar-weekdays { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; margin-bottom: var(--space-sm); }
.calendar-weekdays span { text-align: center; font-size: 0.72rem; color: var(--text-muted); padding: 4px 0; }
.calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
.calendar-day {
  aspect-ratio: 1; display: flex; align-items: center; justify-content: center;
  font-size: 0.82rem; color: var(--text-secondary); border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}
.calendar-day.checked {
  background: rgba(196,163,90,0.2); color: var(--accent-primary); font-weight: 600;
}
.calendar-day.today {
  border: 1px solid var(--accent-primary); color: var(--accent-primary);
}
.calendar-day.checked.today {
  background: var(--accent-primary); color: #1a1a2e;
}
.calendar-day.empty { visibility: hidden; }
.calendar-legend { display: flex; justify-content: center; gap: var(--space-lg); margin-top: var(--space-lg); }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.75rem; color: var(--text-muted); }
.legend-dot { width: 10px; height: 10px; border-radius: 2px; }
.legend-dot.checked { background: rgba(196,163,90,0.2); }
.legend-dot.today { border: 1px solid var(--accent-primary); }

/* ====== 底部 ====== */
.footer-section { text-align: center; padding: var(--space-xl) 0 5rem; }
.footer-divider {
  width: 40px; height: 1px; background: var(--border-glass);
  margin: 0 auto var(--space-xl);
}
.footer-text {
  font-size: 0.82rem; color: var(--text-muted); margin-bottom: var(--space-xl);
  letter-spacing: 0.08em;
}

/* ====== 加载态 ====== */
.center {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; min-height: 80vh;
}
.loading-spinner {
  width: 32px; height: 32px; border: 2px solid rgba(196,163,90,0.15);
  border-top-color: var(--accent-primary); border-radius: 50%;
  animation: spin 0.8s linear infinite; margin-bottom: var(--space-md);
}
@keyframes spin { to { transform: rotate(360deg); } }
.loading-text { font-size: 0.85rem; color: var(--text-muted); }

/* ====== 流光 ====== */
.card-shimmer {
  position: absolute; top: 0; left: -100%; width: 60%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.02), transparent);
  transform: skewX(-20deg); transition: left 0.7s ease;
  pointer-events: none; z-index: 0;
}
.glass-card:hover .card-shimmer { left: 150%; }

/* ====== 热力图卡片 ====== */
.heatmap-card {
  padding: 0;
  overflow: hidden;
}

/* ====== 响应式 ====== */
@media (max-width: 768px) {
  .stats-grid { gap: var(--space-md); }
  .stat-number { font-size: 2rem; }
  .cover-title { font-size: 2.2rem; }
  .chart-bars { height: 160px; }
  .chart-value { display: none; }
}
</style>
