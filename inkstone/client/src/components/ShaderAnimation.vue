<template>
  <canvas ref="canvas" class="shader-canvas"></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'

const canvas = ref(null)
let renderer, scene, camera, material, clock, animationId

const vertexShader = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`

const fragmentShader = /* glsl */ `
  varying vec2 vUv;
  uniform float uTime;
  uniform vec2 uResolution;

  void main() {
    vec2 center = vUv - 0.5;
    float dist = length(center);
    float angle = atan(center.y, center.x);

    // Ripple rings
    float rings = sin(dist * 12.0 - uTime * 0.8) * 0.5 + 0.5;
    float rings2 = sin(dist * 8.0 + uTime * 0.5) * 0.5 + 0.5;
    float rings3 = cos(dist * 15.0 - uTime * 0.3) * 0.5 + 0.5;

    // Spiral wave
    float spiral = sin(dist * 10.0 + angle * 3.0 - uTime * 0.6) * 0.5 + 0.5;

    // Blend ripples
    float ripple = rings * 0.4 + rings2 * 0.3 + rings3 * 0.2 + spiral * 0.1;

    // Rich glowing ripple
    vec3 dark  = vec3(0.059, 0.059, 0.102);   // bg-primary
    vec3 gold  = vec3(0.769, 0.639, 0.353);   // accent gold
    vec3 purple= vec3(0.659, 0.545, 0.980);   // accent purple
    vec3 blue  = vec3(0.314, 0.502, 0.890);   // cool accent

    float t = ripple;

    // Edge fade
    float edgeFade = 1.0 - smoothstep(0.25, 0.75, dist);
    t *= edgeFade;

    // Brighter color mixing
    vec3 col = dark;
    col = mix(col, gold, t * 0.6);
    col = mix(col, purple, t * t * 0.35);
    col = mix(col, blue, rings3 * edgeFade * 0.25);

    // Center glow
    float glow = exp(-dist * 2.5) * 0.4;
    col += gold * glow;

    // Outer ring highlight
    float ringHighlight = (1.0 - abs(rings - 0.5) * 2.0) * edgeFade * 0.12;
    col += gold * ringHighlight;

    // Vignette
    float vignette = 1.0 - dist * 0.9;
    col *= vignette;

    gl_FragColor = vec4(col, 1.0);
  }
`

function init() {
  const el = canvas.value
  renderer = new THREE.WebGLRenderer({ canvas: el, alpha: true, antialias: false })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

  scene = new THREE.Scene()
  camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1)

  clock = new THREE.Clock()

  const geometry = new THREE.PlaneGeometry(2, 2)
  material = new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms: {
      uTime: { value: 0 },
      uResolution: { value: new THREE.Vector2() }
    }
  })

  const mesh = new THREE.Mesh(geometry, material)
  scene.add(mesh)

  resize()
  window.addEventListener('resize', resize)
}

function resize() {
  const el = canvas.value
  const w = el.clientWidth
  const h = el.clientHeight
  renderer.setSize(w, h, false)
  material.uniforms.uResolution.value.set(w, h)
}

function animate() {
  animationId = requestAnimationFrame(animate)
  material.uniforms.uTime.value = clock.getElapsedTime()
  renderer.render(scene, camera)
}

onMounted(() => {
  init()
  animate()
})

onUnmounted(() => {
  cancelAnimationFrame(animationId)
  window.removeEventListener('resize', resize)
  renderer?.dispose()
  material?.dispose()
})
</script>

<style scoped>
.shader-canvas {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  pointer-events: none;
}
</style>
