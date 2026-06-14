<script setup>
import { onMounted, onUnmounted, ref, computed } from 'vue'

const props = defineProps({
  texts: { type: Array, required: true },
  morphTime: { type: Number, default: 1.5 },
  coolDownTime: { type: Number, default: 0.5 },
})

const filterId = computed(() => `morph-threshold-${Math.random().toString(36).slice(2, 8)}`)
const textCount = computed(() => Math.max(props.texts.length, 1))

const textIndex = ref(0)
const morph = ref(0)
const coolDown = ref(0)
const time = ref(new Date())

const text1Ref = ref()
const text2Ref = ref()

function setStyles(fraction) {
  if (!text1Ref.value || !text2Ref.value || !props.texts.length) return

  const safeFraction = Math.max(fraction, 0.001)
  const safeInverse = Math.max(1 - fraction, 0.001)

  text2Ref.value.style.filter = `blur(${Math.min(8 / safeFraction - 8, 100)}px)`
  text2Ref.value.style.opacity = `${fraction ** 0.4 * 100}%`

  text1Ref.value.style.filter = `blur(${Math.min(8 / safeInverse - 8, 100)}px)`
  text1Ref.value.style.opacity = `${(1 - fraction) ** 0.4 * 100}%`

  text1Ref.value.textContent = props.texts[textIndex.value % textCount.value]
  text2Ref.value.textContent = props.texts[(textIndex.value + 1) % textCount.value]
}

function doMorph() {
  morph.value -= coolDown.value
  coolDown.value = 0

  let fraction = morph.value / props.morphTime

  if (fraction > 1) {
    coolDown.value = props.coolDownTime
    fraction = 1
  }

  setStyles(fraction)

  if (fraction >= 1) {
    textIndex.value = (textIndex.value + 1) % textCount.value
  }
}

function doCoolDown() {
  morph.value = 0

  if (text1Ref.value && text2Ref.value) {
    text2Ref.value.style.filter = 'none'
    text2Ref.value.style.opacity = '100%'
    text1Ref.value.style.filter = 'none'
    text1Ref.value.style.opacity = '0%'
  }
}

let animationFrameId = 0
function animate() {
  animationFrameId = requestAnimationFrame(animate)

  const newTime = new Date()
  const dt = Math.min((newTime.getTime() - time.value.getTime()) / 1000, 0.1)
  time.value = newTime

  coolDown.value -= dt

  if (coolDown.value <= 0) {
    doMorph()
  } else {
    doCoolDown()
  }
}

onMounted(() => {
  if (!props.texts.length) return
  animate()
})
onUnmounted(() => { cancelAnimationFrame(animationFrameId) })
</script>

<template>
  <div class="morphing-container" :style="{ filter: `url(#${filterId}) blur(0.6px)` }">
    <span ref="text1Ref" class="morphing-text" />
    <span ref="text2Ref" class="morphing-text" />

    <svg class="morphing-filter" preserveAspectRatio="xMidYMid slice">
      <defs>
        <filter :id="filterId">
          <feColorMatrix
            in="SourceGraphic"
            type="matrix"
            values="1 0 0 0 0
                    0 1 0 0 0
                    0 0 1 0 0
                    0 0 0 255 -140"
          />
        </filter>
      </defs>
    </svg>
  </div>
</template>

<style scoped>
.morphing-container {
  position: relative;
  margin-inline: auto;
  width: 100%;
  text-align: center;
  font-family: var(--font-calligraphy);
  font-size: clamp(3rem, 7vw, 5.5rem);
  font-weight: 400;
  line-height: 1;
  letter-spacing: 0.12em;
  height: 1.2em;
}

.morphing-text {
  position: absolute;
  inset-inline: 0;
  top: 0;
  margin: auto;
  display: inline-block;
  width: 100%;
  background: linear-gradient(160deg, #f5f0e0 0%, #e8d5a3 25%, #c4a35a 50%, #a07d3a 75%, #7a5c28 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.morphing-filter {
  position: fixed;
  width: 0;
  height: 0;
}
</style>
