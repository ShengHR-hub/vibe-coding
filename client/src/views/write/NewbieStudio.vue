<template>
  <div class="nb-root">
    <div class="nb-bar">
      <router-link to="/" class="nb-back">← 首页</router-link>
      <span class="nb-title">新手系统</span>
      <select v-model="store.currentWorkId" class="nb-select" @change="onOpenWork">
        <option :value="null" disabled>选择作品…</option>
        <option v-for="w in works" :key="w.work_id" :value="w.work_id">{{ w.title }}</option>
      </select>
      <button class="nb-btn" @click="onNewWork">新建</button>
      <span class="nb-spacer"></span>
      <button class="nb-btn" :disabled="!store.currentWorkId || saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
      <button class="nb-btn nb-btn-ghost" :disabled="!store.currentWorkId" @click="exportWork">导出</button>
    </div>

    <div class="nb-body">
      <!-- 左：写作面板 -->
      <div class="nb-left">
        <div class="nb-chapters" v-if="store.currentWorkId">
          <button
            v-for="ch in chapters" :key="ch.chapter_id"
            class="nb-ch" :class="{ active: ch.chapter_id === store.activeChapterId }"
            @click="onSwitchChapter(ch.chapter_id)"
          >{{ ch.title || `第${ch.chapter_no}章` }}</button>
          <button class="nb-ch nb-ch-add" @click="addChapter">＋ 章节</button>
        </div>
        <textarea v-if="store.currentWorkId" ref="editorRef" class="nb-editor"
          v-model="store.content"
          :placeholder="'在这里安静写作…（Ctrl+S 保存）'"></textarea>
        <div v-else class="nb-empty">选择或新建一个作品，或先在右边立主线 / 大纲 / 主角</div>
      </div>

      <!-- 右：四区块功能（创作工坊面板） -->
      <div class="nb-right">
        <WorkshopPanel />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { api } from '../../api/index.js'
import { useWritingStore } from '../../stores/writing.js'
import { useToast } from '../../composables/useToast.js'
import WorkshopPanel from './WorkshopPanel.vue'

const store = useWritingStore()
const toast = useToast()
const works = ref([])
const chapters = ref([])
const saving = ref(false)
const editorRef = ref(null)

async function loadWorks() {
  const res = await api.get('/api/works')
  if (res.code === 0) works.value = res.data.items || []
}

async function openWork() {
  const wid = store.currentWorkId
  if (!wid) return
  const res = await api.get(`/api/works/${wid}`)
  if (res.code !== 0) return
  store.title = res.data.work?.title || ''
  chapters.value = res.data.chapters || []
  store.chapters = chapters.value
  if (chapters.value.length) {
    store.activeChapterId = chapters.value[0].chapter_id
    store.content = chapters.value[0].content || ''
  }
}

function onOpenWork() { openWork() }

async function onNewWork() {
  const title = window.prompt('作品标题', '未命名作品')
  if (title === null) return
  const res = await api.post('/api/works', { title: title || '未命名作品', type: 'novel' })
  if (res.code === 0) {
    store.currentWorkId = res.data.work_id
    await loadWorks()
    await openWork()
  }
}

async function onSwitchChapter(chapterId) {
  // 先保存当前章节，防止切换丢失
  if (store.activeChapterId) await save()
  await store.switchChapter(chapterId)
  chapters.value = [...store.chapters]
  editorRef.value?.focus()
}

async function addChapter() {
  const ch = await store.addChapter()
  if (ch) chapters.value = [...store.chapters]
}

async function save() {
  if (!store.currentWorkId || saving.value) return
  saving.value = true
  const res = await api.post('/api/works/save', {
    work_id: store.currentWorkId,
    title: store.title || '未命名作品',
    chapter_id: store.activeChapterId,
    chapter_title: store.getActiveChapterTitle() || '',
    content: store.content,
  })
  saving.value = false
  if (res.code === 0) {
    toast.success('已保存')
  } else {
    toast.error(res.msg)
  }
}

async function exportWork() {
  if (!store.currentWorkId) return
  await save()
  await api.download(`/api/works/${store.currentWorkId}/export`, `${store.title || '作品'}.txt`)
}

function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    save()
  }
}

onMounted(() => {
  loadWorks()
  window.addEventListener('keydown', onKeydown)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.nb-root { min-height: 100vh; display: flex; flex-direction: column; }
.nb-bar { display: flex; align-items: center; gap: 10px; padding: 12px 20px; border-bottom: 1px solid rgba(196, 163, 90, 0.15); }
.nb-back { color: var(--text-muted); text-decoration: none; font-size: 0.85rem; }
.nb-back:hover { color: var(--accent-primary); }
.nb-title { font-family: var(--font-serif); font-weight: 600; color: var(--text-primary); font-size: 0.95rem; }
.nb-select { background: var(--bg-glass); color: var(--text-primary); border: 1px solid rgba(196, 163, 90, 0.2); border-radius: 8px; padding: 6px 10px; font-size: 0.85rem; }
.nb-spacer { flex: 1; }
.nb-btn { background: var(--accent-primary, #c4a35a); color: #14161c; border: none; padding: 7px 16px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 0.85rem; }
.nb-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.nb-btn-ghost { background: transparent; color: var(--text-secondary); border: 1px solid rgba(196, 163, 90, 0.3); }
.nb-body { flex: 1; display: flex; min-height: 0; }
.nb-left { width: 56%; display: flex; flex-direction: column; border-right: 1px solid rgba(196, 163, 90, 0.12); min-width: 0; }
.nb-chapters { display: flex; flex-wrap: wrap; gap: 6px; padding: 10px 16px; }
.nb-ch { background: var(--bg-glass); color: var(--text-secondary); border: 1px solid transparent; border-radius: 999px; padding: 4px 12px; font-size: 0.78rem; cursor: pointer; }
.nb-ch.active { border-color: var(--accent-primary); color: var(--accent-primary); }
.nb-ch-add { border-style: dashed; }
.nb-editor { flex: 1; margin: 0 16px 16px; padding: 20px; resize: none; outline: none;
  background: var(--bg-panel, #161923); color: var(--text-primary);
  border: 1px solid rgba(196, 163, 90, 0.12); border-radius: 12px;
  font-family: var(--font-serif); font-size: 1rem; line-height: 2; }
.nb-empty { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text-muted); font-size: 0.9rem; }
.nb-right { flex: 1; min-width: 340px; max-width: 480px; overflow-y: auto; padding: 16px; }
</style>