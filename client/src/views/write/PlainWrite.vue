<template>
  <div class="plain-root">
    <div class="plain-bar">
      <span class="plain-logo">墨池 · 纯净写作</span>
      <select v-model="workId" class="plain-select" @change="onOpenWork">
        <option :value="null" disabled>选择作品…</option>
        <option v-for="w in works" :key="w.work_id" :value="w.work_id">{{ w.title }}</option>
      </select>
      <button class="plain-btn" @click="onNewWork">＋ 新建</button>
      <span class="plain-spacer"></span>
      <button class="plain-btn" :disabled="!workId || saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
      <button class="plain-btn plain-btn-ghost" :disabled="!workId" @click="exportWork">导出</button>
    </div>

    <div class="plain-chapters" v-if="workId">
      <button
        v-for="ch in chapters" :key="ch.chapter_id"
        class="plain-ch" :class="{ active: ch.chapter_id === activeChapterId }"
        @click="onSwitchChapter(ch.chapter_id)"
      >{{ ch.title || `第${ch.chapter_no}章` }}</button>
      <button class="plain-ch plain-ch-add" @click="addChapter">＋ 章节</button>
    </div>

    <textarea
      v-if="workId" ref="editorRef" class="plain-editor"
      v-model="store.content"
      :placeholder="'在这里安静写作…（Ctrl+S 保存）'"
    ></textarea>
    <div v-else class="plain-empty">选择或新建一个作品开始写作</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { api } from '../../api/index.js'
import { useWritingStore } from '../../stores/writing.js'
import { useToast } from '../../composables/useToast.js'

const store = useWritingStore()
const toast = useToast()
const works = ref([])
const workId = ref(null)
const chapters = ref([])
const activeChapterId = ref(null)
const saving = ref(false)
const editorRef = ref(null)

async function loadWorks() {
  const res = await api.get('/api/works')
  if (res.code === 0) works.value = res.data.items || []
}

async function openWork() {
  if (!workId.value) return
  const res = await api.get(`/api/works/${workId.value}`)
  if (res.code !== 0) return
  store.title = res.data.work?.title || ''
  chapters.value = res.data.chapters || []
  store.chapters = chapters.value
  if (chapters.value.length) {
    activeChapterId.value = chapters.value[0].chapter_id
    store.activeChapterId = activeChapterId.value
    store.content = chapters.value[0].content || ''
  }
}

function onOpenWork() { openWork() }

async function onNewWork() {
  const title = window.prompt('作品标题', '未命名作品')
  if (title === null) return
  const res = await api.post('/api/works', { title: title || '未命名作品', type: 'novel', summary: '', content: '' })
  if (res.code === 0) {
    workId.value = res.data.work_id
    await loadWorks()
    await openWork()
  }
}

async function onSwitchChapter(chapterId) {
  await store.switchChapter(chapterId)
  activeChapterId.value = chapterId
  editorRef.value?.focus()
}

async function addChapter() {
  const ch = await store.addChapter()
  if (ch) {
    chapters.value = [...store.chapters]
    activeChapterId.value = ch.chapter_id
  }
}

async function save() {
  if (!workId.value) return
  saving.value = true
  const res = await api.post('/api/works/save', {
    work_id: workId.value,
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
  if (!workId.value) return
  await save()
  await api.download(`/api/works/${workId.value}/export`, `${store.title || '作品'}.txt`)
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
.plain-root { min-height: 100vh; display: flex; flex-direction: column; background: var(--bg-base, #10131a); }
.plain-bar {
  display: flex; align-items: center; gap: 10px; padding: 12px 20px;
  border-bottom: 1px solid rgba(196, 163, 90, 0.15);
}
.plain-logo { font-family: var(--font-serif); color: var(--accent-secondary); font-weight: 600; font-size: 0.92rem; }
.plain-select {
  background: var(--bg-glass); color: var(--text-primary); border: 1px solid rgba(196, 163, 90, 0.2);
  border-radius: 8px; padding: 6px 10px; font-size: 0.85rem;
}
.plain-spacer { flex: 1; }
.plain-btn {
  background: var(--accent-primary, #c4a35a); color: #14161c; border: none;
  padding: 7px 16px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 0.85rem;
}
.plain-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.plain-btn-ghost { background: transparent; color: var(--text-secondary); border: 1px solid rgba(196,163,90,0.3); }
.plain-chapters { display: flex; flex-wrap: wrap; gap: 6px; padding: 10px 20px; }
.plain-ch {
  background: var(--bg-glass); color: var(--text-secondary); border: 1px solid transparent;
  border-radius: 999px; padding: 5px 14px; font-size: 0.8rem; cursor: pointer;
}
.plain-ch.active { border-color: var(--accent-primary); color: var(--accent-primary); }
.plain-ch-add { border-style: dashed; }
.plain-editor {
  flex: 1; margin: 0 20px 20px; padding: 24px; resize: none; outline: none;
  background: var(--bg-panel, #161923); color: var(--text-primary);
  border: 1px solid rgba(196, 163, 90, 0.12); border-radius: 14px;
  font-family: var(--font-serif); font-size: 1.02rem; line-height: 2;
}
.plain-empty { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text-muted); }
</style>