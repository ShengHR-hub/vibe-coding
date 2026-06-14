<template>
  <div class="pomodoro" :class="{ running: state === 'running', break: mode === 'break' }">
    <!-- 紧凑模式：圆环 + 时间 -->
    <div class="pomo-ring-wrap" @click="expanded = !expanded">
      <svg class="pomo-ring" viewBox="0 0 36 36">
        <circle class="ring-bg" cx="18" cy="18" r="15.9" />
        <circle class="ring-fg" cx="18" cy="18" r="15.9"
          :stroke-dasharray="`${progress} 100`"
          :class="{ 'ring-break': mode === 'break' }" />
      </svg>
      <span class="pomo-time">{{ displayTime }}</span>
    </div>

    <!-- 展开控制面板 -->
    <transition name="pomo-panel">
      <div v-if="expanded" class="pomo-panel">
        <div class="pomo-label">{{ mode === 'focus' ? '专注' : '休息' }} · {{ state === 'idle' ? '就绪' : state === 'running' ? '进行中' : state === 'paused' ? '已暂停' : '完成' }}</div>
        <div class="pomo-controls">
          <button v-if="state === 'idle'" class="pomo-btn" @click="start">开始</button>
          <button v-else-if="state === 'running'" class="pomo-btn" @click="pause">暂停</button>
          <button v-else-if="state === 'paused'" class="pomo-btn" @click="resume">继续</button>
          <button class="pomo-btn pomo-btn-ghost" @click="reset" v-if="state !== 'idle'">重置</button>
          <button class="pomo-btn pomo-btn-ghost" @click="skip" v-if="state === 'running'">跳过</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted, watch } from 'vue'

const FOCUS_TIME = 25 * 60
const BREAK_TIME = 5 * 60

const mode = ref('focus')       // 'focus' | 'break'
const state = ref('idle')       // 'idle' | 'running' | 'paused' | 'completed'
const remaining = ref(FOCUS_TIME)
const expanded = ref(false)

let intervalId = null
let completeTimeoutId = null

const emit = defineEmits(['complete'])

const displayTime = computed(() => {
  const m = Math.floor(remaining.value / 60)
  const s = remaining.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

const progress = computed(() => {
  const total = mode.value === 'focus' ? FOCUS_TIME : BREAK_TIME
  return ((total - remaining.value) / total) * 100
})

function start() {
  state.value = 'running'
  clearInterval(intervalId)
  intervalId = setInterval(tick, 1000)
}

function pause() {
  state.value = 'paused'
  clearInterval(intervalId)
  intervalId = null
}

function resume() {
  state.value = 'running'
  clearInterval(intervalId)
  intervalId = setInterval(tick, 1000)
}

function reset() {
  clearInterval(intervalId)
  intervalId = null
  if (completeTimeoutId) { clearTimeout(completeTimeoutId); completeTimeoutId = null }
  state.value = 'idle'
  mode.value = 'focus'
  remaining.value = FOCUS_TIME
}

function skip() {
  clearInterval(intervalId)
  intervalId = null
  const total = mode.value === 'focus' ? FOCUS_TIME : BREAK_TIME
  remaining.value = 0
  onComplete(total)
}

function tick() {
  remaining.value = Math.max(0, remaining.value - 1)
  if (remaining.value <= 0) {
    onComplete()
  }
}

function onComplete(elapsed) {
  clearInterval(intervalId)
  intervalId = null
  state.value = 'completed'
  playChime()

  if (mode.value === 'focus') {
    const total = FOCUS_TIME
    const duration = elapsed != null ? elapsed : total
    emit('complete', { duration })
  }

  // 自动切换模式
  completeTimeoutId = setTimeout(() => {
    completeTimeoutId = null
    if (mode.value === 'focus') {
      mode.value = 'break'
      remaining.value = BREAK_TIME
    } else {
      mode.value = 'focus'
      remaining.value = FOCUS_TIME
    }
    state.value = 'idle'
  }, 1500)
}

function playChime() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const notes = [523.25, 659.25, 783.99] // C5, E5, G5
    notes.forEach((freq, i) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'sine'
      osc.frequency.value = freq
      gain.gain.setValueAtTime(0.15, ctx.currentTime + i * 0.2)
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.2 + 0.6)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(ctx.currentTime + i * 0.2)
      osc.stop(ctx.currentTime + i * 0.2 + 0.6)
    })
    setTimeout(() => ctx.close(), 2000)
  } catch {}
}

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
  if (completeTimeoutId) clearTimeout(completeTimeoutId)
})
</script>

<style scoped>
.pomodoro {
  position: relative;
  display: flex;
  align-items: center;
}

.pomo-ring-wrap {
  position: relative;
  width: 36px; height: 36px;
  cursor: pointer;
  transition: transform 0.2s ease;
}
.pomo-ring-wrap:hover { transform: scale(1.1); }

.pomo-ring {
  width: 100%; height: 100%;
  transform: rotate(-90deg);
}
.ring-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.06);
  stroke-width: 2.5;
}
.ring-fg {
  fill: none;
  stroke: var(--accent-primary);
  stroke-width: 2.5;
  stroke-linecap: round;
  transition: stroke-dasharray 0.5s ease;
}
.ring-fg.ring-break {
  stroke: var(--accent-green, #6bcf7f);
}

.pomo-time {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.55rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--text-secondary);
  letter-spacing: 0.02em;
}

/* 运行中脉冲 */
.pomodoro.running .pomo-ring-wrap {
  animation: pomoPulse 2s ease-in-out infinite;
}
@keyframes pomoPulse {
  0%, 100% { filter: drop-shadow(0 0 0 transparent); }
  50% { filter: drop-shadow(0 0 6px rgba(196, 163, 90, 0.3)); }
}

/* 展开面板 */
.pomo-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 180px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(15, 15, 26, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  z-index: 200;
}
.pomo-label {
  font-size: 0.72rem;
  color: var(--text-muted);
  text-align: center;
  margin-bottom: 10px;
  letter-spacing: 0.06em;
}
.pomo-controls {
  display: flex;
  gap: 6px;
  justify-content: center;
}
.pomo-btn {
  padding: 4px 12px;
  font-size: 0.72rem;
  border-radius: 16px;
  border: none;
  cursor: pointer;
  background: var(--accent-primary);
  color: #0f0f1a;
  font-weight: 600;
  transition: all 0.2s ease;
}
.pomo-btn:hover { opacity: 0.85; }
.pomo-btn-ghost {
  background: transparent;
  color: var(--text-muted);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.pomo-btn-ghost:hover {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

/* 面板动画 */
.pomo-panel-enter-active, .pomo-panel-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.pomo-panel-enter-from, .pomo-panel-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
