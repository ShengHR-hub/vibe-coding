<template>
  <div class="page-container">
    <div class="graph-header">
      <h2>{{ workTitle || '知识图谱' }}</h2>
    </div>

    <div class="tabs">
      <button class="tab" :class="{ active: activeTab === 'characters' }" @click="activeTab = 'characters'">角色关系</button>
      <button class="tab" :class="{ active: activeTab === 'timeline' }" @click="activeTab = 'timeline'">剧情时间线</button>
    </div>

    <!-- 角色关系图 -->
    <div v-if="activeTab === 'characters'">
      <div v-if="charLoading" class="center"><LoadingSpinner /></div>
      <div v-else-if="charError" class="center error">{{ charError }}</div>
      <div v-else-if="!graphData" class="center muted">暂无角色数据</div>
      <div v-else ref="graphRef" class="graph-box glass-card"></div>
    </div>

    <!-- 时间线 -->
    <div v-if="activeTab === 'timeline'">
      <div v-if="tlLoading" class="center"><LoadingSpinner /></div>
      <div v-else-if="tlError" class="center error">{{ tlError }}</div>
      <div v-else-if="!timelineData || timelineData.length === 0" class="center muted">暂无时间线数据</div>
      <div v-else class="timeline">
        <div v-for="(ch, ci) in timelineData" :key="ci" class="tl-chapter">
          <div class="tl-node">
            <div class="tl-dot"></div>
            <div class="tl-chapter-title">第{{ ch.chapter }}章 {{ ch.title }}</div>
          </div>
          <div v-for="(ev, ei) in ch.events" :key="ei" class="tl-event glass-card" :class="{ left: ei % 2 === 0, right: ei % 2 === 1 }">
            <div class="tl-event-title">{{ ev.event }}</div>
            <div class="tl-event-detail">{{ ev.detail }}</div>
            <div class="tl-event-time">{{ ev.time_label }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api/index.js'
import LoadingSpinner from '../../components/LoadingSpinner.vue'

const route = useRoute()
const workId = route.params.work_id

const activeTab = ref('characters')
const workTitle = ref('')

const charLoading = ref(false)
const charError = ref('')
const graphData = ref(null)
const graphRef = ref(null)

const tlLoading = ref(false)
const tlError = ref('')
const timelineData = ref(null)

let tlLoaded = false
onMounted(() => {
  loadCharacters()
})

watch(activeTab, async (tab) => {
  if (tab === 'characters') {
    await nextTick()
    if (graphData.value) renderGraph()
  }
  if (tab === 'timeline' && !tlLoaded) {
    tlLoaded = true
    loadTimeline()
  }
})

async function loadCharacters() {
  charLoading.value = true
  charError.value = ''
  const res = await api.get(`/api/graph/${workId}/characters`)
  if (res.code === 0) {
    graphData.value = res.data.graph
    workTitle.value = res.data.work_title || ''
    await nextTick()
    renderGraph()
  } else {
    charError.value = res.msg || '加载失败'
  }
  charLoading.value = false
}

async function loadTimeline() {
  tlLoading.value = true
  tlError.value = ''
  const res = await api.get(`/api/graph/${workId}/timeline`)
  if (res.code === 0) {
    timelineData.value = res.data.timeline
    workTitle.value = workTitle.value || res.data.work_title || ''
  } else {
    tlError.value = res.msg || '加载失败'
  }
  tlLoading.value = false
}

function renderGraph() {
  if (!graphRef.value || !graphData.value) return
  if (typeof echarts === 'undefined') {
    console.warn('echarts CDN not loaded')
    return
  }
  try {
    const el = graphRef.value
    const old = echarts.getInstanceByDom(el)
    if (old) old.dispose()
    const chart = echarts.init(el)

    const categories = [
      { name: '主角', itemStyle: { color: '#c4a35a' } },
      { name: '配角', itemStyle: { color: '#a0a0b0' } },
      { name: '反派', itemStyle: { color: '#e0556a' } },
    ]

    chart.setOption({
      tooltip: {
        formatter: (p) => p.dataType === 'node'
          ? `<b>${p.name}</b><br/>${p.data.description || ''}<br/>类别: ${p.data.category}`
          : `${p.data.source} → ${p.data.target}<br/>${p.data.label || ''}`
      },
      legend: [{ data: categories.map(c => c.name), textStyle: { color: '#9b97b0' } }],
      series: [{
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        categories,
        data: graphData.value.nodes.map(n => ({
          name: n.name,
          category: n.category || '配角',
          description: n.description || '',
          symbolSize: n.category === '主角' ? 40 : 28,
        })),
        edges: graphData.value.edges.map(e => ({
          source: e.source,
          target: e.target,
          label: { show: true, formatter: e.label || '', color: '#6b6780', fontSize: 11 },
        })),
        force: { repulsion: 300, edgeLength: [100, 250] },
        label: { show: true, color: '#e8e6f0', fontSize: 12 },
        lineStyle: { color: 'rgba(196,163,90,0.3)', curveness: 0.2 },
      }],
      backgroundColor: 'transparent',
    })
    window.addEventListener('resize', () => chart.resize())
  } catch (e) {
    console.error('Graph render failed:', e)
  }
}
</script>

<style scoped>
.graph-header { margin-bottom: var(--space-lg); }

.tabs { display: flex; gap: var(--space-sm); margin-bottom: var(--space-xl); border-bottom: 1px solid var(--border-glass); padding-bottom: var(--space-sm); }
.tab { padding: 6px 16px; font-size: 0.9rem; color: var(--text-muted); background: none; border-radius: var(--radius-sm); transition: all var(--transition-fast); }
.tab:hover { color: var(--text-secondary); }
.tab.active { color: var(--accent-primary); background: var(--bg-glass); }

.graph-box { width: 100%; height: 550px; padding: var(--space-md); }

/* Timeline */
.timeline { position: relative; padding-left: 30px; margin-top: var(--space-lg); }
.timeline::before { content: ''; position: absolute; left: 14px; top: 0; bottom: 0; width: 2px; background: var(--border-glass); }

.tl-chapter { position: relative; margin-bottom: var(--space-xl); }
.tl-node { display: flex; align-items: center; gap: var(--space-md); margin-bottom: var(--space-md); }
.tl-dot { width: 14px; height: 14px; border-radius: 50%; background: var(--accent-primary); border: 3px solid var(--bg-primary); z-index: 1; margin-left: -36px; }
.tl-chapter-title { font-size: 1rem; font-weight: 600; color: var(--accent-primary); }

.tl-event { padding: var(--space-md); margin-bottom: var(--space-md); max-width: 600px; }
.tl-event.left { margin-left: 0; }
.tl-event.right { margin-left: 40px; }
.tl-event-title { font-size: 0.9rem; font-weight: 600; color: var(--text-primary); margin-bottom: var(--space-xs); }
.tl-event-detail { font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; margin-bottom: var(--space-xs); }
.tl-event-time { font-size: 0.75rem; color: var(--accent-warm); }

.center { display: flex; justify-content: center; padding: var(--space-2xl); }
.error { color: var(--accent-red); }
.muted { color: var(--text-muted); }
</style>
