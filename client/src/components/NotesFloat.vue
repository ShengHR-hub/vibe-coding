<template>
  <div class="nf-root" :style="{ left: pos.x + 'px', top: pos.y + 'px' }">
    <button
      class="nf-fab"
      :class="{ dragging }"
      title="闪念便签 (Ctrl+Shift+N) · 按住可拖动"
      @pointerdown="onDown"
    >
      记
    </button>
    <div v-if="open" class="nf-panel">
      <div class="nf-head">
        <span class="nf-title">闪念便签</span>
        <button class="nf-close" @click="open = false">✕</button>
      </div>
      <div class="nf-list">
        <div v-for="n in notes" :key="n.note_id" class="nf-item">
          <p class="nf-text">{{ n.content }}</p>
          <div class="nf-item-foot">
            <span class="nf-time">{{ (n.updated_at || '').slice(5, 16) }}</span>
            <button class="nf-del" @click="del(n.note_id)">删除</button>
          </div>
        </div>
        <p v-if="!notes.length" class="nf-empty">想到什么好点子，随手记在这里——不怕忘。</p>
      </div>
      <div class="nf-input-row">
        <textarea v-model="draft" rows="2" class="nf-input" placeholder="记一个闪念…（Enter 保存，Shift+Enter 换行）" @keydown.enter.exact.prevent="add"></textarea>
        <button class="nf-add" :disabled="!draft.trim() || saving" @click="add">记下</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { api } from '../api/index.js'

const open = ref(false)
const notes = ref([])
const draft = ref('')
const saving = ref(false)

// ---- 拖动位置（记忆到 localStorage） ----
const POS_KEY = 'inkstone_notes_pos'
const pos = ref(loadPos())
const dragging = ref(false)
let downX = 0, downY = 0, baseX = 0, baseY = 0, moved = false

function loadPos() {
  try {
    const raw = localStorage.getItem(POS_KEY)
    if (raw) {
      const p = JSON.parse(raw)
      if (typeof p.x === 'number' && typeof p.y === 'number') return p
    }
  } catch { /* 忽略 */ }
  // 默认右下角（避开浏览器底部边距）
  const w = window.innerWidth, h = window.innerHeight
  return { x: w - 78, y: h - 92 }
}

function clamp(v, max) { return Math.min(Math.max(v, 8), max) }

function onDown(e) {
  moved = false
  downX = e.clientX; downY = e.clientY
  baseX = pos.value.x; baseY = pos.value.y
  dragging.value = true
  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
}

function onMove(e) {
  if (!dragging.value) return
  const dx = e.clientX - downX, dy = e.clientY - downY
  if (Math.abs(dx) + Math.abs(dy) > 4) moved = true
  pos.value.x = clamp(baseX + dx, window.innerWidth - 70)
  pos.value.y = clamp(baseY + dy, window.innerHeight - 70)
}

function onUp() {
  if (!dragging.value) return
  dragging.value = false
  window.removeEventListener('pointermove', onMove)
  window.removeEventListener('pointerup', onUp)
  try { localStorage.setItem(POS_KEY, JSON.stringify(pos.value)) } catch { /* 忽略 */ }
  if (!moved) toggle() // 没拖才算点击
}

async function load() {
  const res = await api.get('/api/notes')
  if (res.code === 0) notes.value = res.data.items || []
}

async function add() {
  const text = draft.value.trim()
  if (!text || saving.value) return
  saving.value = true
  const res = await api.post('/api/notes', { content: text })
  saving.value = false
  if (res.code === 0) {
    draft.value = ''
    await load()
  }
}

async function del(noteId) {
  await api.delete(`/api/notes/${noteId}`)
  await load()
}

function toggle() {
  open.value = !open.value
  if (open.value) load()
}

function onShortcut(e) {
  if (e.ctrlKey && e.shiftKey && e.key === 'N') {
    e.preventDefault()
    toggle()
  }
}

onMounted(() => window.addEventListener('keydown', onShortcut))
onUnmounted(() => {
  window.removeEventListener('keydown', onShortcut)
  window.removeEventListener('pointermove', onMove)
  window.removeEventListener('pointerup', onUp)
})
</script>

<style scoped>
.nf-root { position: fixed; z-index: 800; }
.nf-fab {
  width: 46px; height: 46px; border-radius: 50%; border: none; cursor: grab;
  background: linear-gradient(135deg, var(--accent-primary, #c4a35a), #9b7d3c);
  color: #14161c; font-family: var(--font-serif, serif); font-size: 1.15rem; font-weight: 700;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4), 0 0 20px rgba(196, 163, 90, 0.18);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  user-select: none; -webkit-user-select: none; touch-action: none;
}
.nf-fab:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45), 0 0 26px rgba(196, 163, 90, 0.26); }
.nf-fab.dragging { cursor: grabbing; transform: scale(1.06); }
.nf-panel {
  position: absolute; right: 0; bottom: 56px; width: min(320px, 84vw);
  background: var(--bg-panel, rgba(20, 22, 30, 0.92));
  border: 1px solid rgba(196, 163, 90, 0.25);
  border-radius: var(--radius-lg, 14px); overflow: hidden;
  box-shadow: var(--shadow-lg, 0 10px 34px rgba(0, 0, 0, 0.5));
  backdrop-filter: blur(14px);
  display: flex; flex-direction: column;
}
.nf-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.6rem 0.9rem;
  border-bottom: 1px solid rgba(196, 163, 90, 0.12);
  background: rgba(196, 163, 90, 0.05);
}
.nf-title { font-family: var(--font-serif); font-weight: 600; font-size: 0.92rem; color: var(--text-primary); }
.nf-close {
  width: 24px; height: 24px; border-radius: 50%;
  background: none; border: none; color: var(--text-muted);
  cursor: pointer; font-size: 0.8rem; line-height: 1;
  transition: all 0.2s;
}
.nf-close:hover { color: var(--text-primary); background: rgba(255, 255, 255, 0.08); }
.nf-list { max-height: 260px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; padding: 0.8rem 0.9rem; }
.nf-item {
  padding: 8px 10px; border-radius: var(--radius-md, 8px);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(196, 163, 90, 0.1);
  transition: border-color 0.2s;
}
.nf-item:hover { border-color: rgba(196, 163, 90, 0.28); }
.nf-text { margin: 0; font-size: 0.85rem; line-height: 1.7; color: var(--text-primary); white-space: pre-wrap; word-break: break-word; }
.nf-item-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; }
.nf-time { color: var(--text-muted); font-size: 0.7rem; }
.nf-del { background: none; border: none; color: var(--accent-red, #e0556a); font-size: 0.75rem; cursor: pointer; }
.nf-del:hover { text-decoration: underline; }
.nf-empty { color: var(--text-muted); font-size: 0.8rem; text-align: center; padding: 14px 0; }
.nf-input-row {
  display: flex; gap: 8px; align-items: flex-end;
  padding: 0.7rem 0.9rem;
  border-top: 1px solid rgba(196, 163, 90, 0.1);
}
.nf-input {
  flex: 1; background: rgba(255, 255, 255, 0.04); color: var(--text-primary);
  border: 1px solid rgba(196, 163, 90, 0.2); border-radius: var(--radius-md, 8px);
  padding: 8px 10px; font-size: 0.85rem; resize: none; font-family: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.nf-input:focus { outline: none; border-color: rgba(196, 163, 90, 0.4); box-shadow: 0 0 0 3px rgba(196, 163, 90, 0.06); }
.nf-add {
  background: linear-gradient(135deg, var(--accent-primary, #c4a35a), #9b7d3c);
  color: #14161c; border: none;
  padding: 8px 14px; border-radius: var(--radius-md, 8px);
  cursor: pointer; font-weight: 600; font-size: 0.82rem;
  transition: opacity 0.2s, transform 0.2s;
}
.nf-add:hover:not(:disabled) { transform: translateY(-1px); }
.nf-add:disabled { opacity: 0.45; cursor: not-allowed; }
</style>