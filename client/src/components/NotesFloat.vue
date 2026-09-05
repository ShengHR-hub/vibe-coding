<template>
  <div class="nf-root">
    <button class="nf-fab" title="闪念便签 (Ctrl+Shift+N)" @click="toggle">
      📝
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
onUnmounted(() => window.removeEventListener('keydown', onShortcut))
</script>

<style scoped>
.nf-root { position: fixed; right: 24px; bottom: 24px; z-index: 800; }
.nf-fab {
  width: 46px; height: 46px; border-radius: 50%; border: none; cursor: pointer;
  background: var(--accent-primary); color: #14161c; font-size: 1.2rem;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
}
.nf-panel {
  position: absolute; right: 0; bottom: 56px; width: min(320px, 84vw);
  background: var(--bg-panel, #1a1c24); border: 1px solid rgba(196, 163, 90, 0.25);
  border-radius: 14px; box-shadow: 0 10px 34px rgba(0, 0, 0, 0.5);
  padding: 12px 14px; display: flex; flex-direction: column; gap: 8px;
}
.nf-head { display: flex; justify-content: space-between; align-items: center; }
.nf-title { font-family: var(--font-serif); font-weight: 600; font-size: 0.95rem; }
.nf-close { background: none; border: none; color: var(--text-muted); cursor: pointer; }
.nf-list { max-height: 260px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
.nf-item {
  padding: 8px 10px; border-radius: 10px; background: var(--bg-glass);
  border: 1px solid rgba(196, 163, 90, 0.1);
}
.nf-text { margin: 0; font-size: 0.85rem; line-height: 1.7; color: var(--text-primary); white-space: pre-wrap; word-break: break-word; }
.nf-item-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; }
.nf-time { color: var(--text-muted); font-size: 0.7rem; }
.nf-del { background: none; border: none; color: var(--accent-red, #d66); font-size: 0.75rem; cursor: pointer; }
.nf-empty { color: var(--text-muted); font-size: 0.8rem; text-align: center; padding: 14px 0; }
.nf-input-row { display: flex; gap: 8px; align-items: flex-end; }
.nf-input {
  flex: 1; background: var(--bg-glass); color: var(--text-primary);
  border: 1px solid rgba(196, 163, 90, 0.2); border-radius: 8px; padding: 8px 10px;
  font-size: 0.85rem; resize: none; font-family: inherit;
}
.nf-add {
  background: var(--accent-primary); color: #14161c; border: none;
  padding: 8px 14px; border-radius: 8px; cursor: pointer; font-weight: 600;
}
.nf-add:disabled { opacity: 0.45; cursor: not-allowed; }
</style>