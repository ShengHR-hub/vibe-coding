<script setup>
import { cn } from "@inspira-ui/plugins";
import { Color, Mesh, Program, Renderer, Triangle } from "ogl";
import { onMounted, onUnmounted, ref } from "vue";

const props = defineProps({
  class: { type: String, default: "" },
});

const ctnDom = ref(null);

let animateId;
let renderer;
let gl;
let mesh;

// Vertex Shader
const vert = `
  attribute vec2 uv;
  attribute vec2 position;

  varying vec2 vUv;

  void main() {
      vUv = uv;
      gl_Position = vec4(position, 0, 1);
  }
`;

// Fragment Shader — 金色亮纹在深紫底色上流动
const frag = `
  precision highp float;

  uniform float uTime;
  uniform vec3 uColor;
  uniform vec3 uResolution;

  varying vec2 vUv;

  void main() {
      float mr = min(uResolution.x, uResolution.y);
      vec2 uv = (vUv.xy * 2.0 - 1.0) * uResolution.xy / mr;

      float d = -uTime * 1.2;
      float a = 0.0;
      for (float i = 0.0; i < 8.0; ++i) {
          a += cos(i - d - a * uv.x);
          d += sin(uv.y * i + a);
      }
      d += uTime * 1.0;

      // 原始色彩生成（液态扰动）
      vec3 raw = vec3(cos(uv * vec2(d, a)) * 0.6 + 0.4, cos(a + d) * 0.5 + 0.5);
      raw = cos(raw * cos(vec3(d, a, 2.5)) * 0.5 + 0.5);

      // 深紫色底色（主体）
      vec3 deepPurple = vec3(0.08, 0.03, 0.15);
      vec3 midPurple  = vec3(0.18, 0.08, 0.30);
      // 金色亮纹（少量点缀）
      vec3 gold = vec3(0.77, 0.64, 0.35);

      // 紫色层次：基于扰动在两层紫色间渐变
      float luminance = dot(raw, vec3(0.299, 0.587, 0.114));
      vec3 col = mix(deepPurple, midPurple, smoothstep(0.2, 0.6, luminance));

      // 金色亮纹：仅在高亮处极细地渗出，像颜料在水中扩散
      float goldVein = smoothstep(0.72, 0.85, luminance);
      col = mix(col, gold, goldVein * 0.45);

      // 微弱金色辉光
      float glow = pow(luminance, 5.0) * 0.15;
      col += gold * glow;

      // 暗角加深边缘紫色
      vec2 center = vUv - 0.5;
      float vignette = 1.0 - dot(center, center) * 1.0;
      col *= vignette;

      gl_FragColor = vec4(col, 1.0);
  }
`;

function resize() {
  if (!ctnDom.value) return;
  const scale = 1;
  renderer.setSize(
    ctnDom.value.offsetWidth * scale,
    ctnDom.value.offsetHeight * scale
  );
  if (mesh) {
    mesh.program.uniforms.uResolution.value = [
      gl.canvas.width,
      gl.canvas.height,
      gl.canvas.width / gl.canvas.height,
    ];
  }
}

function update(t) {
  animateId = requestAnimationFrame(update);
  if (mesh) {
    mesh.program.uniforms.uTime.value = t * 0.001;
    renderer.render({ scene: mesh });
  }
}

onMounted(() => {
  if (!ctnDom.value) return;

  renderer = new Renderer();
  gl = renderer.gl;
  gl.clearColor(1, 1, 1, 1);

  window.addEventListener("resize", resize, false);
  resize();

  const geometry = new Triangle(gl);

  const program = new Program(gl, {
    vertex: vert,
    fragment: frag,
    uniforms: {
      uTime: { value: 0 },
      uColor: { value: new Color(0.77, 0.64, 0.35) },
      uResolution: {
        value: [
          gl.canvas.width,
          gl.canvas.height,
          gl.canvas.width / gl.canvas.height,
        ],
      },
    },
  });

  mesh = new Mesh(gl, { geometry, program });
  animateId = requestAnimationFrame(update);

  ctnDom.value.appendChild(gl.canvas);
});

onUnmounted(() => {
  cancelAnimationFrame(animateId);
  window.removeEventListener("resize", resize);
  if (ctnDom.value && gl?.canvas) {
    ctnDom.value.removeChild(gl.canvas);
  }
  gl?.getExtension("WEBGL_lose_context")?.loseContext();
});
</script>

<template>
  <div
    ref="ctnDom"
    :class="cn('block size-full', props.class)"
  />
</template>

<style scoped>
div :deep(canvas) {
  display: block;
  width: 100% !important;
  height: 100% !important;
}
</style>
