<template>
  <div class="heatmap-container">
    <div class="heatmap-header">
      <h3>阅读热力图</h3>
      <div class="heatmap-stats">
        <span class="stat">过去一年活跃 <strong>{{ activeDays }}</strong> 天</span>
        <span class="stat">累计阅读 <strong>{{ totalMinutes }}</strong> 分钟</span>
      </div>
    </div>

    <div class="heatmap-grid">
      <!-- 星期标签 -->
      <div class="weekday-labels">
        <span>一</span>
        <span>三</span>
        <span>五</span>
      </div>

      <!-- 月份标签 -->
      <div class="month-labels">
        <span v-for="m in monthLabels" :key="m.key" :style="{ left: m.left }">
          {{ m.label }}
        </span>
      </div>

      <!-- 热力图格子 -->
      <div class="cells-wrapper">
        <div v-for="(week, wi) in weeks" :key="wi" class="week-column">
          <div
            v-for="(day, di) in week"
            :key="di"
            class="heat-cell"
            :class="`level-${day.level}`"
            :title="`${day.date}: ${day.minutes} 分钟`"
          />
        </div>
      </div>
    </div>

    <!-- 图例 -->
    <div class="heatmap-legend">
      <span class="legend-label">少</span>
      <div class="heat-cell level-0"></div>
      <div class="heat-cell level-1"></div>
      <div class="heat-cell level-2"></div>
      <div class="heat-cell level-3"></div>
      <div class="heat-cell level-4"></div>
      <span class="legend-label">多</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api/index.js'

const heatmapData = ref([])
const activeDays = ref(0)
const totalMinutes = ref(0)

onMounted(async () => {
  const res = await api.get('/api/reading/checkin/heatmap')
  if (res.code === 0) {
    heatmapData.value = res.data.heatmap
    activeDays.value = res.data.active_days
    totalMinutes.value = res.data.total_minutes
  }
})

// 将数据按周分组（每列7天）
const weeks = computed(() => {
  if (heatmapData.value.length === 0) return []

  const result = []
  let currentWeek = []

  // 找到第一天是星期几（0=周日，1=周一...）
  const firstDate = new Date(heatmapData.value[0].date)
  let dayOfWeek = firstDate.getDay()
  // 转换为周一开始（0=周一，6=周日）
  dayOfWeek = dayOfWeek === 0 ? 6 : dayOfWeek - 1

  // 填充第一周的空白
  for (let i = 0; i < dayOfWeek; i++) {
    currentWeek.push({ date: '', minutes: 0, level: -1 })
  }

  for (const day of heatmapData.value) {
    currentWeek.push(day)
    if (currentWeek.length === 7) {
      result.push(currentWeek)
      currentWeek = []
    }
  }

  // 填充最后一周
  if (currentWeek.length > 0) {
    while (currentWeek.length < 7) {
      currentWeek.push({ date: '', minutes: 0, level: -1 })
    }
    result.push(currentWeek)
  }

  return result
})

// 月份标签
const monthLabels = computed(() => {
  if (heatmapData.value.length === 0) return []

  const labels = []
  const monthNames = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']

  let lastMonth = -1
  weeks.value.forEach((week, wi) => {
    const firstDay = week.find(d => d.date)
    if (firstDay && firstDay.date) {
      const month = new Date(firstDay.date).getMonth()
      if (month !== lastMonth) {
        labels.push({
          key: firstDay.date,
          label: monthNames[month],
          left: `${wi * 14}px`
        })
        lastMonth = month
      }
    }
  })

  return labels
})
</script>

<style scoped>
.heatmap-container {
  padding: var(--space-lg);
}

.heatmap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
  flex-wrap: wrap;
  gap: var(--space-md);
}

.heatmap-header h3 {
  font-size: 1rem;
  color: var(--text-primary);
  margin: 0;
}

.heatmap-stats {
  display: flex;
  gap: var(--space-lg);
}

.stat {
  font-size: 0.82rem;
  color: var(--text-muted);
}

.stat strong {
  color: var(--accent-primary);
  font-weight: 600;
}

.heatmap-grid {
  display: flex;
  gap: 4px;
  position: relative;
  padding-left: 24px;
  padding-top: 20px;
}

.weekday-labels {
  position: absolute;
  left: 0;
  top: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: calc(7 * 14px);
  font-size: 0.65rem;
  color: var(--text-muted);
}

.month-labels {
  position: absolute;
  top: 0;
  left: 24px;
  right: 0;
  height: 16px;
  font-size: 0.65rem;
  color: var(--text-muted);
}

.month-labels span {
  position: absolute;
}

.cells-wrapper {
  display: flex;
  gap: 3px;
  overflow-x: auto;
}

.week-column {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.heat-cell {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.03);
  transition: all 0.2s ease;
}

.heat-cell:hover {
  transform: scale(1.3);
  box-shadow: 0 0 8px rgba(196, 163, 90, 0.3);
}

.heat-cell.level-0 {
  background: rgba(255, 255, 255, 0.03);
}

.heat-cell.level-1 {
  background: rgba(196, 163, 90, 0.2);
}

.heat-cell.level-2 {
  background: rgba(196, 163, 90, 0.4);
}

.heat-cell.level-3 {
  background: rgba(196, 163, 90, 0.6);
}

.heat-cell.level-4 {
  background: rgba(196, 163, 90, 0.9);
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: var(--space-md);
  justify-content: flex-end;
}

.legend-label {
  font-size: 0.65rem;
  color: var(--text-muted);
  margin: 0 4px;
}

/* 响应式 */
@media (max-width: 768px) {
  .heatmap-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .heatmap-stats {
    flex-direction: column;
    gap: var(--space-sm);
  }
}
</style>
