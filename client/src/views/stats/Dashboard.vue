<template>
  <div class="page-container">
    <h2>写作数据洞察</h2>

    <div v-if="loading" class="center"><LoadingSpinner /></div>
    <div v-else-if="errorMsg" class="center error">{{ errorMsg }} <button class="btn btn-ghost btn-sm" @click="fetchAll">重试</button></div>
    <template v-else>
      <div class="overview-cards">
        <div class="stat-card glass-card" v-for="card in cards" :key="card.label">
          <span class="stat-value">{{ card.value }}</span>
          <span class="stat-label">{{ card.label }}</span>
        </div>
      </div>

      <div class="comparison-row" v-if="overview">
        <span v-if="overview.comparison.week_change >= 0" class="comp up">本周 +{{ overview.comparison.week_change }} 字</span>
        <span v-else class="comp down">本周 {{ overview.comparison.week_change }} 字</span>
        <span v-if="overview.comparison.month_change >= 0" class="comp up">本月 +{{ overview.comparison.month_change }} 字</span>
        <span v-else class="comp down">本月 {{ overview.comparison.month_change }} 字</span>
      </div>

      <section class="chart-section glass-card">
        <h3>月度写作量</h3>
        <div v-if="barData.length === 0" class="center muted">暂无数据，开始写作后将自动记录</div>
        <div v-else ref="barRef" class="chart-box"></div>
      </section>

      <section class="chart-section glass-card">
        <h3>写作日历</h3>
        <div v-if="heatmapData.length === 0" class="center muted">暂无数据</div>
        <div v-else class="heatmap-wrap">
          <div class="heatmap-grid">
            <div v-for="d in heatmapData" :key="d.date" class="heat-day" :class="heatClass(d.count)" :title="d.date + ': ' + d.count + '字'"></div>
          </div>
          <div class="heatmap-legend">
            <span class="legend-label">少</span>
            <span class="legend-block l0"></span>
            <span class="legend-block l1"></span>
            <span class="legend-block l2"></span>
            <span class="legend-block l3"></span>
            <span class="legend-block l4"></span>
            <span class="legend-label">多</span>
          </div>
        </div>
      </section>

      <section class="chart-section glass-card" v-if="styleData">
        <h3>写作风格分析</h3>
        <div ref="radarRef" class="chart-box"></div>
      </section>
      <div v-else class="chart-section glass-card">
        <h3>写作风格分析</h3>
        <p class="center muted">作品内容不足，多写一些后再来分析</p>
      </div>

      <section class="chart-section glass-card" v-if="reportText">
        <h3>月度写作报告</h3>
        <div class="report-content">{{ reportText }}</div>
      </section>

      <section class="chart-section glass-card" v-if="sessions.length">
        <h3>写作记录</h3>
        <div class="sessions-list">
          <div v-for="s in sessions" :key="s.session_id" class="session-row">
            <span class="session-date">{{ fmtDate(s.session_date) }}</span>
            <span class="session-work">{{ s.work_title || '未关联作品' }}</span>
            <span class="session-words">{{ s.word_count }} 字</span>
            <span class="session-dur">{{ s.duration }} 分钟</span>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { api } from '../../api/index.js'
import LoadingSpinner from '../../components/LoadingSpinner.vue'

const loading = ref(true)
const errorMsg = ref('')
const overview = ref(null)
const barData = ref([])
const heatmapData = ref([])
const styleData = ref(null)
const reportText = ref('')
const sessions = ref([])

const barRef = ref(null)
const radarRef = ref(null)

const cards = computed(() => {
  if (!overview.value) return []
  const o = overview.value
  return [
    { label: '总字数', value: (o.total_words || 0).toLocaleString() },
    { label: '作品数', value: o.total_works || 0 },
    { label: '写作次数', value: o.total_sessions || 0 },
    { label: '日均', value: (o.avg_daily || 0) + '字' },
    { label: '连续天数', value: (o.streak_days || 0) + '天' },
    { label: '今日', value: (o.today_words || 0) + '字' },
  ]
})

onMounted(fetchAll)

async function fetchAll() {
  loading.value = true
  errorMsg.value = ''
  try {
    const [ov, bar, heat, sess] = await Promise.all([
      api.get('/api/stats/overview'),
      api.get('/api/stats/overview/bar'),
      api.get('/api/stats/heatmap'),
      api.get('/api/stats/sessions?page_size=10'),
    ])
    if (ov.code === 0) overview.value = ov.data
    if (bar.code === 0) { barData.value = bar.data.months; console.log('月度写作量 API:', bar.data.months) }
    else { console.warn('月度写作量 API error:', bar.code, bar.msg) }
    if (heat.code === 0) heatmapData.value = heat.data.days
    if (sess.code === 0) sessions.value = sess.data.items
    loading.value = false
    await nextTick()
    renderBarChart()
  } catch {
    errorMsg.value = '加载失败'
    loading.value = false
  }

  loadStyle()
  loadReport()
}

async function loadStyle() {
  const res = await api.get('/api/stats/style')
  if (res.code === 0) {
    styleData.value = res.data.style
    await nextTick()
    renderRadarChart()
  }
}

async function loadReport() {
  const res = await api.get('/api/stats/report')
  if (res.code === 0) reportText.value = res.data.report
}

function renderBarChart() {
  if (!barRef.value || !barData.value.length) return
  if (typeof echarts === 'undefined') {
    console.warn('echarts CDN not loaded')
    return
  }
  try {
    const el = barRef.value
    const chart = echarts.init(el)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '3%', top: 10, bottom: 20 },
      xAxis: { type: 'category', data: barData.value.map(d => d.month), axisLabel: { color: '#9b97b0' } },
      yAxis: { type: 'value', axisLabel: { color: '#9b97b0' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } } },
      series: [{
        type: 'bar', data: barData.value.map(d => d.words),
        itemStyle: { color: '#c4a35a', borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 32,
      }],
      backgroundColor: 'transparent',
    })
    window.addEventListener('resize', () => chart.resize())
  } catch (e) {
    console.error('Bar chart render failed:', e)
  }
}

function renderRadarChart() {
  if (!radarRef.value || !styleData.value) return
  const el = radarRef.value
  const chart = echarts.init(el)
  const keys = Object.keys(styleData.value)
  const vals = Object.values(styleData.value)
  chart.setOption({
    tooltip: {},
    radar: {
      indicator: keys.map(k => ({ name: k, max: 100 })),
      axisName: { color: '#9b97b0' },
      splitArea: { areaStyle: { color: ['rgba(196,163,90,0.02)', 'rgba(196,163,90,0.04)'] } },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
    },
    series: [{
      type: 'radar',
      data: [{ value: vals, name: '风格画像', areaStyle: { color: 'rgba(196,163,90,0.2)' } }],
      itemStyle: { color: '#c4a35a' },
      lineStyle: { color: '#c4a35a' },
    }],
    backgroundColor: 'transparent',
  })
  window.addEventListener('resize', () => chart.resize())
}

function heatClass(count) {
  if (!count) return 'l0'
  if (count <= 200) return 'l1'
  if (count <= 800) return 'l2'
  if (count <= 2000) return 'l3'
  return 'l4'
}

function fmtDate(d) {
  if (!d) return ''
  return d.slice(0, 10)
}
</script>

<style scoped>
.overview-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: var(--space-md); margin-bottom: var(--space-lg); }
.stat-card { padding: var(--space-md) var(--space-lg); text-align: center; }
.stat-value { display: block; font-size: 1.5rem; font-weight: 700; color: var(--accent-primary); margin-bottom: var(--space-xs); }
.stat-label { font-size: 0.8rem; color: var(--text-muted); }

.comparison-row { display: flex; gap: var(--space-lg); margin-bottom: var(--space-lg); flex-wrap: wrap; }
.comp { font-size: 0.85rem; padding: 4px 12px; border-radius: var(--radius-full); }
.comp.up { background: rgba(107,207,127,0.1); color: var(--accent-green); }
.comp.down { background: rgba(224,85,106,0.1); color: var(--accent-red); }

.chart-section { padding: var(--space-lg); margin-bottom: var(--space-lg); }
.chart-section h3 { font-size: 1rem; margin-bottom: var(--space-md); color: var(--text-secondary); }
.chart-box { width: 100%; height: 280px; }

.heatmap-wrap { overflow-x: auto; }
.heatmap-grid { display: grid; grid-template-columns: repeat(53, 1fr); gap: 3px; min-width: 750px; margin-bottom: var(--space-sm); }
.heat-day { aspect-ratio: 1; border-radius: 2px; min-width: 10px; }
.heat-day.l0 { background: var(--bg-glass); border: 1px solid var(--border-glass); }
.heat-day.l1 { background: rgba(107,207,127,0.15); }
.heat-day.l2 { background: rgba(107,207,127,0.35); }
.heat-day.l3 { background: rgba(107,207,127,0.6); }
.heat-day.l4 { background: var(--accent-green); }
.heatmap-legend { display: flex; align-items: center; gap: 4px; justify-content: flex-end; margin-top: var(--space-sm); }
.legend-label { font-size: 0.7rem; color: var(--text-muted); }
.legend-block { width: 14px; height: 14px; border-radius: 2px; }
.legend-block.l0 { background: var(--bg-glass); border: 1px solid var(--border-glass); }
.legend-block.l1 { background: rgba(107,207,127,0.15); }
.legend-block.l2 { background: rgba(107,207,127,0.35); }
.legend-block.l3 { background: rgba(107,207,127,0.6); }
.legend-block.l4 { background: var(--accent-green); }

.report-content { font-size: 0.95rem; line-height: 1.8; color: var(--text-secondary); white-space: pre-wrap; }

.sessions-list { display: flex; flex-direction: column; gap: 2px; }
.session-row { display: flex; align-items: center; gap: var(--space-md); padding: var(--space-sm) var(--space-md); font-size: 0.85rem; border-radius: var(--radius-sm); }
.session-row:hover { background: var(--bg-glass); }
.session-date { color: var(--text-muted); width: 90px; flex-shrink: 0; }
.session-work { flex: 1; color: var(--text-primary); min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-words { color: var(--accent-primary); width: 70px; text-align: right; flex-shrink: 0; }
.session-dur { color: var(--text-muted); width: 70px; text-align: right; flex-shrink: 0; }

.center { display: flex; justify-content: center; padding: var(--space-2xl); }
.error { color: var(--accent-red); }
.muted { color: var(--text-muted); }
</style>
