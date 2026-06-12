<template>
  <div ref="containerRef" class="shadertoy-container">
    <div
      v-if="props.noise && props.noise.opacity > 0"
      class="noise-overlay"
      :style="{
        backgroundSize: (props.noise.scale || 0) * 200 + '%',
        backgroundPosition: 'center',
        opacity: props.noise.opacity / 2,
      }"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from "vue"
import { InspiraShaderToy } from "./InspiraShaderToy"

const props = defineProps({
  mouseMode: { type: String, default: "click" },
  class: { type: String, default: "" },
  shaderCode: { type: String, required: true },
  hue: { type: Number, default: 0 },
  saturation: { type: Number, default: 1 },
  brightness: { type: Number, default: 1 },
  speed: { type: Number, default: 1 },
  mouseSensitivity: { type: Number, default: 1 },
  damping: { type: Number, default: 0 },
  noise: { type: Object, default: undefined },
})

const containerRef = ref(null)
let shader

onMounted(() => {
  if (!containerRef.value) return
  shader = new InspiraShaderToy(containerRef.value, props.mouseMode)

  const success = shader.setShader({ source: props.shaderCode })
  if (!success) { console.error("Failed to compile shader"); return }

  shader.setHSV({ hue: props.hue, saturation: props.saturation, brightness: props.brightness })
  shader.setSpeed(props.speed)
  shader.setMouseSensitivity(props.mouseSensitivity)
  shader.setMouseDamping(props.damping)
  shader.play()
})

onUnmounted(() => {
  shader?.dispose()
})

watch(() => props.hue, (v) => { if (v !== undefined && shader) shader.setHue(v) })
watch(() => props.saturation, (v) => { if (v !== undefined && shader) shader.setSaturation(v) })
watch(() => props.brightness, (v) => { if (v !== undefined && shader) shader.setBrightness(v) })
watch(() => props.speed, (v) => { if (v !== undefined && shader) shader.setSpeed(v) })
watch(() => props.mouseSensitivity, (v) => { if (v !== undefined && shader) shader.setMouseSensitivity(v) })
watch(() => props.damping, (v) => { if (v !== undefined && shader) shader.setMouseDamping(v) })
</script>

<style scoped>
.shadertoy-container {
  display: block;
  position: relative;
  height: 100%;
  width: 100%;
  pointer-events: none;
}

.shadertoy-container :deep(canvas) {
  display: block;
  max-width: 100%;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}

.noise-overlay {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 10;
  background-image: url(https://framerusercontent.com/images/g0QcWrxr87K0ufOxIUFBakwYA8.png);
  background-repeat: repeat;
  pointer-events: none;
}
</style>
