<template>
  <div ref="liquidGlassRoot" class="liquid-glass-effect" :style="baseStyle">
    <div class="liquid-slot">
      <slot />
    </div>
    <svg class="liquid-filter-svg" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <filter id="displacementFilter" color-interpolation-filters="sRGB">
          <feImage x="0" y="0" width="100%" height="100%" :href="displacementDataUri" result="map" />
          <feDisplacementMap id="redchannel" in="SourceGraphic" in2="map" :xChannelSelector="xChannel" :yChannelSelector="yChannel" :scale="scale + rOffset" result="dispRed" />
          <feColorMatrix in="dispRed" type="matrix" values="1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0" result="red" />
          <feDisplacementMap id="greenchannel" in="SourceGraphic" in2="map" :xChannelSelector="xChannel" :yChannelSelector="yChannel" :scale="scale + gOffset" result="dispGreen" />
          <feColorMatrix in="dispGreen" type="matrix" values="0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 1 0" result="green" />
          <feDisplacementMap id="bluechannel" in="SourceGraphic" in2="map" :xChannelSelector="xChannel" :yChannelSelector="yChannel" :scale="scale + bOffset" result="dispBlue" />
          <feColorMatrix in="dispBlue" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 1 0" result="blue" />
          <feBlend in="red" in2="green" mode="screen" result="rg" />
          <feBlend in="rg" in2="blue" mode="screen" result="output" />
          <feGaussianBlur :stdDeviation="displace" />
        </filter>
      </defs>
    </svg>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, reactive } from "vue"

const props = defineProps({
  radius: { type: Number, default: 16 },
  border: { type: Number, default: 0.07 },
  lightness: { type: Number, default: 50 },
  displace: { type: Number, default: 0 },
  blend: { type: String, default: "difference" },
  xChannel: { type: String, default: "R" },
  yChannel: { type: String, default: "B" },
  alpha: { type: Number, default: 0.93 },
  blur: { type: Number, default: 11 },
  rOffset: { type: Number, default: 0 },
  gOffset: { type: Number, default: 10 },
  bOffset: { type: Number, default: 20 },
  scale: { type: Number, default: -180 },
  frost: { type: Number, default: 0.05 },
})

const liquidGlassRoot = ref(null)
const dimensions = reactive({ width: 0, height: 0 })
let observer = null

const baseStyle = computed(() => ({
  "--frost": props.frost,
  "border-radius": `${props.radius}px`,
}))

const displacementImage = computed(() => {
  const border = Math.min(dimensions.width, dimensions.height) * (props.border * 0.5)
  const yBorder = Math.min(dimensions.width, dimensions.height) * (props.border * 0.5)
  const w = dimensions.width
  const h = dimensions.height
  return `<svg viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="red" x1="100%" y1="0%" x2="0%" y2="0%">
        <stop offset="0%" stop-color="#0000"/><stop offset="100%" stop-color="red"/>
      </linearGradient>
      <linearGradient id="blue" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#0000"/><stop offset="100%" stop-color="blue"/>
      </linearGradient>
    </defs>
    <rect x="0" y="0" width="${w}" height="${h}" fill="black"/>
    <rect x="0" y="0" width="${w}" height="${h}" rx="${props.radius}" fill="url(#red)"/>
    <rect x="0" y="0" width="${w}" height="${h}" rx="${props.radius}" fill="url(#blue)" style="mix-blend-mode: ${props.blend}"/>
    <rect x="${border}" y="${yBorder}" width="${w - border * 2}" height="${h - border * 2}" rx="${props.radius}" fill="hsl(0 0% ${props.lightness}% / ${props.alpha})" style="filter:blur(${props.blur}px)"/>
  </svg>`
})

const displacementDataUri = computed(() => {
  return `data:image/svg+xml,${encodeURIComponent(displacementImage.value)}`
})

onMounted(() => {
  if (!liquidGlassRoot.value) return
  observer = new ResizeObserver((entries) => {
    const entry = entries[0]
    if (!entry) return
    let width = 0, height = 0
    if (entry.borderBoxSize && entry.borderBoxSize.length) {
      width = entry.borderBoxSize[0].inlineSize
      height = entry.borderBoxSize[0].blockSize
    } else if (entry.contentRect) {
      width = entry.contentRect.width
      height = entry.contentRect.height
    }
    dimensions.width = width
    dimensions.height = height
  })
  observer.observe(liquidGlassRoot.value)
})

onUnmounted(() => {
  observer?.disconnect()
})
</script>

<style scoped>
.liquid-glass-effect {
  position: relative;
  display: block;
  opacity: 1;
  border-radius: inherit;
  color-scheme: dark;
  backdrop-filter: url(#displacementFilter);
  background: hsl(0 0% 0% / var(--frost, 0.05));
  box-shadow:
    0 0 2px 1px color-mix(in oklch, canvastext, #0000 90%) inset,
    0 0 10px 4px color-mix(in oklch, canvastext, #0000 95%) inset,
    0px 4px 16px rgba(17, 17, 26, 0.05),
    0px 8px 24px rgba(17, 17, 26, 0.05),
    0px 16px 56px rgba(17, 17, 26, 0.05),
    0px 4px 16px rgba(17, 17, 26, 0.05) inset,
    0px 8px 24px rgba(17, 17, 26, 0.05) inset,
    0px 16px 56px rgba(17, 17, 26, 0.05) inset;
}

.liquid-slot {
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: inherit;
}

.liquid-filter-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
</style>
