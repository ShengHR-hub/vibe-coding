<template>
  <div class="rg3d" ref="mountEl">
    <div v-if="!relations.length" class="rg-empty">还没有关系边——先添加：A → 关系 → B</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'

const props = defineProps({
  relations: { type: Array, default: () => [] },
  characters: { type: Array, default: () => [] },
})
const emit = defineEmits(['select-node'])

const mountEl = ref(null)
let renderer, scene, camera, controls, raycaster, pointer
let nodeObjs = []   // { mesh, label, name, relations, degree }
let edgeObjs = []   // { line, name, source, target, relation }
let hoveredNode = null, animId = null
let disposed = false
let downX = 0, downY = 0

/* ---------- 力导向布局：生成 3D 坐标（斥力+弹簧+向心，蛛网状） ---------- */
function buildLayout(relations) {
  const names = []
  const nameIdx = new Map()
  const edges = []
  for (const r of relations) {
    if (!nameIdx.has(r.source)) { nameIdx.set(r.source, names.length); names.push(r.source) }
    if (!nameIdx.has(r.target)) { nameIdx.set(r.target, names.length); names.push(r.target) }
    edges.push({ s: nameIdx.get(r.source), t: nameIdx.get(r.target), relation: r.relation })
  }
  const n = names.length
  // 随机球面初值
  const pos = names.map((_, i) => {
    const u = Math.random(), v = Math.random()
    const theta = 2 * Math.PI * u
    const phi = Math.acos(2 * v - 1)
    const rad = 5 + Math.random() * 2
    return new THREE.Vector3(
      rad * Math.sin(phi) * Math.cos(theta),
      rad * Math.sin(phi) * Math.sin(theta),
      rad * Math.cos(phi)
    )
  })
  const vel = names.map(() => new THREE.Vector3())
  const degree = new Array(n).fill(0)
  for (const e of edges) { degree[e.s]++; degree[e.t]++ }

  const tmpJ = new THREE.Vector3()
  const tmpDir = new THREE.Vector3()
  const springLen = Math.min(3.2, 9 / Math.sqrt(n || 1))  // 弹簧自然长度随节点数收缩
  const repK = 26
  const centerPull = (i) => 0.02 + degree[i] * 0.012      // 度高的节点更靠中心 → 主角在中心

  for (let step = 0; step < 260; step++) {
    const temp = 0.9 - (step / 260) * 0.6                  // 温度递减（模拟退火）
    // 斥力
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        tmpDir.subVectors(pos[i], pos[j])
        const d = Math.max(tmpDir.length(), 0.001)
        const f = Math.min(repK / (d * d), 6) * temp
        tmpDir.normalize().multiplyScalar(f)
        vel[i].add(tmpDir)
        vel[j].sub(tmpDir)
      }
    }
    // 弹簧：有边拉近
    for (const e of edges) {
      tmpDir.subVectors(pos[e.t], pos[e.s])
      const d = Math.max(tmpDir.length(), 0.001)
      const f = (d - springLen) * 0.09
      tmpDir.normalize().multiplyScalar(f)
      vel[e.s].add(tmpDir)
      vel[e.t].sub(tmpDir)
    }
    // 向心 + 积分 + 阻尼
    for (let i = 0; i < n; i++) {
      vel[i].add(tmpJ.copy(pos[i]).multiplyScalar(-centerPull(i)))
      vel[i].multiplyScalar(0.85)
      pos[i].add(vel[i])
    }
  }
  // 整体归一化到相机视野半径 ~7
  let maxD = 0
  for (const p of pos) maxD = Math.max(maxD, p.length())
  const scale = 7 / (maxD || 1)
  pos.forEach(p => p.multiplyScalar(scale))
  return { names, edges, pos, degree }
}

/* ---------- 场景搭建 ---------- */
function buildScene(layout) {
  scene = new THREE.Scene()
  scene.background = null

  camera = new THREE.PerspectiveCamera(55, 1, 0.1, 100)
  camera.position.set(0, 2, 13)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  mountEl.value.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.minDistance = 4
  controls.maxDistance = 26
  controls.rotateSpeed = 0.9
  controls.autoRotate = false

  raycaster = new THREE.Raycaster()
  pointer = new THREE.Vector2()

  renderer.domElement.addEventListener('pointerdown', onDown)
  renderer.domElement.addEventListener('click', onClick)
  renderer.domElement.addEventListener('pointermove', onMove)
  renderer.domElement.style.cursor = 'grab'

  // 节点小球 + 名字 + 后面半透明光晕圆
  const maxDeg = Math.max(1, ...layout.degree)
  layout.names.forEach((name, i) => {
    const deg = layout.degree[i]
    const size = 0.34 + (deg / maxDeg) * 0.22
    const group = new THREE.Group()
    group.position.copy(layout.pos[i])

    const mat = new THREE.MeshStandardMaterial({
      color: 0xc4a35a,
      emissive: 0x8a6d2f,
      emissiveIntensity: 0.35 + (deg / maxDeg) * 0.5,
      roughness: 0.35,
      metalness: 0.55,
    })
    const sphere = new THREE.Mesh(new THREE.SphereGeometry(size, 24, 24), mat)
    group.add(sphere)

    // 名字标签（Sprite）
    const canvas = document.createElement('canvas')
    canvas.width = 256; canvas.height = 64
    const ctx = canvas.getContext('2d')
    ctx.font = '600 30px "Noto Sans SC", "Microsoft YaHei", sans-serif'
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
    ctx.shadowColor = 'rgba(0,0,0,0.9)'; ctx.shadowBlur = 8
    ctx.fillStyle = deg === maxDeg ? '#f0dfae' : '#e6dfc8'
    ctx.fillText(name, 128, 32)
    const tex = new THREE.CanvasTexture(canvas)
    const label = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false }))
    label.scale.set(2.8, 0.7, 1)
    label.position.y = size + 0.55
    group.add(label)

    scene.add(group)
    nodeObjs.push({ mesh: sphere, label, name, relations: [], degree: deg, group })
  })

  // 连线（蛛网）
  for (const e of layout.edges) {
    const a = layout.pos[e.s], b = layout.pos[e.t]
    const geo = new THREE.BufferGeometry().setFromPoints([a, b])
    const mat = new THREE.LineBasicMaterial({
      color: 0xc4a35a,
      transparent: true,
      opacity: 0.42,
    })
    const line = new THREE.Line(geo, mat)
    scene.add(line)
    edgeObjs.push({ line, source: layout.names[e.s], target: layout.names[e.t], relation: e.relation })
    // 边中点放小星点
    const mid = a.clone().add(b).multiplyScalar(0.5)
    const dot = new THREE.Mesh(
      new THREE.SphereGeometry(0.06, 8, 8),
      new THREE.MeshBasicMaterial({ color: 0xc4a35a, transparent: true, opacity: 0.6 })
    )
    dot.position.copy(mid)
    scene.add(dot)
  }

  // 灯光
  scene.add(new THREE.AmbientLight(0xffffff, 0.55))
  const key = new THREE.DirectionalLight(0xfff2d6, 1.2)
  key.position.set(4, 6, 8)
  scene.add(key)
  const rim = new THREE.DirectionalLight(0x7ec8e3, 0.35)
  rim.position.set(-6, -2, -6)
  scene.add(rim)
}

/* ---------- 拾取 ---------- */
function pickNode(evt) {
  if (!renderer) return null
  const rect = renderer.domElement.getBoundingClientRect()
  pointer.x = ((evt.clientX - rect.left) / rect.width) * 2 - 1
  pointer.y = -((evt.clientY - rect.top) / rect.height) * 2 + 1
  raycaster.setFromCamera(pointer, camera)
  const hits = raycaster.intersectObjects(nodeObjs.map(o => o.mesh))
  return hits.length ? nodeObjs.find(o => o.mesh === hits[0].object) : null
}

function onDown(evt) {
  downX = evt.clientX; downY = evt.clientY
}

function onClick(evt) {
  // OrbitControls 拖动旋转后也会触发 click，位移过大视为拖拽不响应
  if (Math.abs(evt.clientX - downX) > 6 || Math.abs(evt.clientY - downY) > 6) return
  const n = pickNode(evt)
  if (n) {
    const rels = props.relations.filter(r => r.source === n.name || r.target === n.name)
    emit('select-node', { name: n.name, relations: rels })
  }
}

function onMove(evt) {
  const n = pickNode(evt)
  if (hoveredNode && hoveredNode !== n) {
    hoveredNode.mesh.scale.setScalar(1)
    hoveredNode = null
  }
  if (n) {
    hoveredNode = n
    n.mesh.scale.setScalar(1.25)
    renderer.domElement.style.cursor = 'pointer'
  } else {
    renderer.domElement.style.cursor = 'grab'
  }
}

function onResize() {
  if (!renderer || !mountEl.value) return
  const w = mountEl.value.clientWidth
  const h = mountEl.value.clientHeight
  renderer.setSize(w, h)
  camera.aspect = w / h
  camera.updateProjectionMatrix()
}

function animate() {
  if (disposed) return
  animId = requestAnimationFrame(animate)
  controls.update()
  renderer.render(scene, camera)
}

function disposeAll() {
  disposed = true
  if (animId) cancelAnimationFrame(animId)
  controls?.dispose()
  if (renderer) {
    renderer.domElement.removeEventListener('pointerdown', onDown)
    renderer.domElement.removeEventListener('click', onClick)
    renderer.domElement.removeEventListener('pointermove', onMove)
    renderer.dispose()
    renderer.domElement.remove()
    renderer = null
  }
  nodeObjs = []
  edgeObjs = []
}

async function rebuild() {
  disposeAll()
  disposed = false
  nodeObjs = []
  edgeObjs = []
  if (!mountEl.value || !props.relations.length) return
  await nextTick()
  const layout = buildLayout(props.relations)
  buildScene(layout)
  onResize()
  animate()
}

watch(() => props.relations, () => rebuild(), { deep: true })

onMounted(() => {
  window.addEventListener('resize', onResize)
  rebuild()
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  disposeAll()
})

defineExpose({ rebuild })
</script>

<style scoped>
.rg3d { width: 100%; height: 420px; position: relative; }
.rg-empty {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  color: var(--text-muted); font-size: 0.82rem; letter-spacing: 0.04em;
}
</style>