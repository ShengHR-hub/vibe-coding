<template>
  <div class="featured-carousel" ref="carouselRef" @mouseenter="pauseAuto" @mouseleave="resumeAuto">
    <!-- 3D 场景 -->
    <div class="carousel-scene" :class="{ 'mobile-scene': isMobile }">
      <template v-if="isMobile">
        <!-- 移动端：水平滑动 -->
        <div class="mobile-track" ref="mobileTrack">
          <div
            v-for="(poem, idx) in poems"
            :key="poem.poem_id || idx"
            class="poem-card glass-card mobile-card"
            :class="{ active: idx === activeIndex }"
          >
            <div class="card-dynasty">{{ poem.dynasty || '经典' }}</div>
            <h3 class="card-title">{{ poem.title }}</h3>
            <p class="card-author">{{ poem.author }}</p>
            <div class="card-content">{{ previewLines(poem.content) }}</div>
            <div class="card-category">{{ poem.category }}</div>
          </div>
        </div>
      </template>
      <template v-else>
        <!-- 桌面端：3D 圆柱 -->
        <div class="carousel-ring" :style="ringStyle">
          <div
            v-for="(poem, idx) in poems"
            :key="poem.poem_id || idx"
            class="poem-card glass-card"
            :class="{ 'card-active': idx === activeIndex }"
            :style="cardStyle(idx)"
            @click="goTo(idx)"
          >
            <div class="card-dynasty">{{ poem.dynasty || '经典' }}</div>
            <h3 class="card-title">{{ poem.title }}</h3>
            <p class="card-author">{{ poem.author }}</p>
            <div class="card-content">{{ previewLines(poem.content) }}</div>
            <div class="card-category">{{ poem.category }}</div>
          </div>
        </div>
      </template>
    </div>

    <!-- 导航箭头 -->
    <button class="nav-arrow nav-prev" @click="prev" aria-label="上一首">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M12 4l-6 6 6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </button>
    <button class="nav-arrow nav-next" @click="next" aria-label="下一首">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M8 4l6 6-6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </button>

    <!-- 圆点指示器 -->
    <div class="carousel-dots">
      <span
        v-for="(_, idx) in poems"
        :key="idx"
        class="dot"
        :class="{ active: idx === activeIndex }"
        @click="goTo(idx)"
      ></span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import gsap from 'gsap'

const props = defineProps({
  poems: { type: Array, default: () => [] },
})

const carouselRef = ref(null)
const mobileTrack = ref(null)
const activeIndex = ref(0)
const isMobile = ref(false)
let autoTimer = null
let tween = null

const cardCount = computed(() => props.poems.length)
const angleStep = computed(() => 360 / Math.max(cardCount.value, 1))
const radius = computed(() => Math.max(280, cardCount.value * 55))
const currentAngle = ref(0)

const ringStyle = computed(() => ({
  transform: `rotateY(${currentAngle.value}deg)`,
}))

function cardStyle(idx) {
  const angle = idx * angleStep.value
  return {
    transform: `rotateY(${angle}deg) translateZ(${radius.value}px)`,
  }
}

// 累积角度驱动，自然成环
function rotateBy(delta) {
  if (tween) tween.kill()
  tween = gsap.to(currentAngle, {
    value: currentAngle.value + delta,
    duration: 0.8,
    ease: 'power3.inOut',
  })
}

function previewLines(content) {
  if (!content) return ''
  return content.split('\n').filter(Boolean).slice(0, 4).join('\n')
}

function updateMobile() {
  isMobile.value = window.innerWidth < 768
}

function goTo(idx) {
  if (!cardCount.value) return
  let diff = idx - activeIndex.value
  if (diff === 0) return
  // 走最短路径：超过半圈就反向
  const half = cardCount.value / 2
  if (diff > half) diff -= cardCount.value
  if (diff < -half) diff += cardCount.value
  activeIndex.value = idx
  rotateBy(-diff * angleStep.value)
  // 移动端滚动
  if (isMobile.value && mobileTrack.value) {
    const card = mobileTrack.value.children[idx]
    if (card) {
      card.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
    }
  }
}

function next() {
  if (!cardCount.value) return
  activeIndex.value = (activeIndex.value + 1) % cardCount.value
  rotateBy(-angleStep.value)
}

function prev() {
  if (!cardCount.value) return
  activeIndex.value = (activeIndex.value - 1 + cardCount.value) % cardCount.value
  rotateBy(angleStep.value)
}

function startAuto() {
  stopAuto()
  autoTimer = setInterval(() => { next() }, 4000)
}

function stopAuto() {
  if (autoTimer) { clearInterval(autoTimer); autoTimer = null }
}

function pauseAuto() { stopAuto() }
function resumeAuto() { startAuto() }

onMounted(() => {
  updateMobile()
  window.addEventListener('resize', updateMobile)
  if (props.poems.length) startAuto()
})

onUnmounted(() => {
  stopAuto()
  window.removeEventListener('resize', updateMobile)
  if (tween) tween.kill()
})

watch(() => props.poems, (val) => {
  if (val.length) {
    activeIndex.value = 0
    startAuto()
  }
})
</script>

<style scoped>
.featured-carousel {
  position: relative;
  width: 100%;
  padding: 2rem 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* ====== 3D 场景 ====== */
.carousel-scene {
  width: 100%;
  height: 380px;
  perspective: 1200px;
  perspective-origin: 50% 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
}

.carousel-ring {
  position: relative;
  width: 300px;
  height: 340px;
  transform-style: preserve-3d;
  transition: transform 0.05s linear;
}

/* ====== 诗词卡片 ====== */
.poem-card {
  position: absolute;
  top: 0;
  left: 0;
  width: 300px;
  height: 340px;
  padding: 2rem 1.8rem;
  border-radius: 18px;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: box-shadow 0.4s ease, border-color 0.4s ease;
  will-change: transform;

  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow:
    0 0 2px 1px color-mix(in oklch, canvastext, #0000 90%) inset,
    0 0 10px 4px color-mix(in oklch, canvastext, #0000 95%) inset,
    0 4px 16px rgba(17, 17, 26, 0.05),
    0 8px 24px rgba(17, 17, 26, 0.05);
}

/* 毛玻璃背景层，不影响文字清晰度 */
.poem-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(20px) saturate(1.2);
  -webkit-backdrop-filter: blur(20px) saturate(1.2);
  z-index: -1;
}

.poem-card.card-active {
  border-color: rgba(196, 163, 90, 0.25);
  box-shadow:
    0 0 2px 1px color-mix(in oklch, canvastext, #0000 90%) inset,
    0 0 10px 4px color-mix(in oklch, canvastext, #0000 95%) inset,
    0 8px 40px rgba(196, 163, 90, 0.1),
    0 0 60px rgba(196, 163, 90, 0.04);
}

.poem-card:hover {
  border-color: rgba(196, 163, 90, 0.3);
}

.card-dynasty {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.2em;
  color: var(--accent-primary);
  opacity: 0.7;
  margin-bottom: 0.8rem;
  padding: 2px 10px;
  border: 1px solid rgba(196, 163, 90, 0.2);
  border-radius: 20px;
  align-self: flex-start;
}

.card-title {
  font-family: var(--font-serif);
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.4rem;
  letter-spacing: 0.06em;
  line-height: 1.4;
}

.card-author {
  font-size: 0.82rem;
  color: var(--text-muted);
  margin: 0 0 1.2rem;
  letter-spacing: 0.04em;
}

.card-content {
  font-family: var(--font-serif);
  font-size: 0.88rem;
  line-height: 2;
  color: var(--text-secondary);
  white-space: pre-line;
  flex: 1;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 5;
  -webkit-box-orient: vertical;
}

.card-category {
  font-size: 0.7rem;
  color: var(--text-muted);
  letter-spacing: 0.1em;
  margin-top: auto;
  padding-top: 0.8rem;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  text-align: right;
}

/* ====== 导航箭头 ====== */
.nav-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  z-index: 10;
}
.nav-arrow:hover {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
  background: rgba(196, 163, 90, 0.08);
}
.nav-prev { left: 0; }
.nav-next { right: 0; }

/* ====== 圆点指示器 ====== */
.carousel-dots {
  display: flex;
  gap: 8px;
  margin-top: 1.5rem;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
  cursor: pointer;
  transition: all 0.4s ease;
}
.dot.active {
  background: var(--accent-primary);
  box-shadow: 0 0 8px rgba(196, 163, 90, 0.5);
  transform: scale(1.3);
}

/* ====== 移动端 ====== */
.mobile-scene {
  height: auto;
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
}
.mobile-scene::-webkit-scrollbar { display: none; }

.mobile-track {
  display: flex;
  gap: 16px;
  padding: 0 2rem;
}

.mobile-card {
  flex: 0 0 280px;
  position: relative;
  scroll-snap-align: center;
  height: 300px;
}

@media (max-width: 768px) {
  .carousel-scene { height: auto; min-height: 340px; }
  .nav-arrow { display: none; }
  .poem-card { width: 280px; height: 300px; padding: 1.5rem; }
  .card-title { font-size: 1.15rem; }
  .card-content { font-size: 0.82rem; -webkit-line-clamp: 4; }
}
</style>
