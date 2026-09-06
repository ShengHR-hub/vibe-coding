<template>
  <div class="studio-root nb-root">
    <!-- ====== 顶部信息栏（与老手系统同款） ====== -->
    <header class="studio-header">
      <div class="header-left">
        <span class="title-accent">✦</span>
        <span class="nb-mode-tag">新手系统</span>
        <select class="nb-select" v-model="store.currentWorkId" @change="onOpenWork">
          <option :value="null" disabled>选择作品…</option>
          <option v-for="w in works" :key="w.work_id" :value="w.work_id">{{ w.title }}</option>
        </select>
        <button class="nb-add-btn" @click="onNewWork">＋ 新建</button>
        <span class="save-badge" :class="saveStatus">
          <span class="save-dot"></span>
          {{ saveLabel }}
        </span>
      </div>
      <div class="header-right">
        <span class="word-badge">{{ store.wordCount }}<small> 字</small></span>
        <button class="header-btn" title="使用说明" @click="openGuide">?</button>
        <button class="header-btn save-btn" @click="save" :disabled="saving || !store.currentWorkId">
          保存
        </button>
        <button class="header-btn save-btn header-btn-ghost" @click="exportWork" :disabled="!store.currentWorkId">
          导出
        </button>
      </div>
    </header>

    <!-- ====== 主体：章节侧边栏 + 编辑器 + 创作工坊面板 ====== -->
    <div class="studio-body">
      <!-- 章节侧边栏 -->
      <aside class="chapter-sidebar glass-card">
        <div class="sidebar-header">
          <span class="sidebar-title">章节</span>
        </div>
        <div class="sidebar-list" v-if="store.currentWorkId">
          <div
            v-for="(ch, idx) in chapters" :key="ch.chapter_id"
            class="chapter-item"
            :class="{ active: ch.chapter_id === store.activeChapterId }"
            @click="onSwitchChapter(ch.chapter_id)"
          >
            <span class="ch-num">{{ idx + 1 }}</span>
            <span class="ch-title">{{ ch.title || `第${idx + 1}章` }}</span>
            <span class="ch-status" :class="ch.status === 'formal' ? 'is-formal' : ''" :title="ch.status === 'formal' ? '正式稿' : '草稿'"></span>
            <span class="ch-wc">{{ ch.word_count || 0 }}</span>
          </div>
          <button class="add-chapter-btn" @click="addChapter">+ 新增章节</button>
        </div>
        <div v-else class="nb-sidebar-empty">选一本书开始，<br>或先在右侧立框架</div>
      </aside>

      <!-- 编辑器 -->
      <div class="editor-panel">
        <div class="chapter-title-bar" v-if="store.chapters.length > 0">
          <input
            class="chapter-title-input"
            :value="store.getActiveChapterTitle()"
            @input="store.setActiveChapterTitle($event.target.value)"
            placeholder="章节标题"
          />
          <button
            class="formal-toggle"
            :class="{ 'is-formal': activeChapterFormal }"
            @click="onToggleFormal"
            :title="activeChapterFormal ? '当前为正式稿，点击改回草稿' : '标记本章为正式稿（交付只导正式稿）'"
          >
            {{ activeChapterFormal ? '正式稿 ✓' : '标为正式稿' }}
          </button>
        </div>
        <textarea
          ref="editorRef"
          class="editor-area"
          v-model="store.content"
          :placeholder="store.currentWorkId ? '在这里安静写作…（Ctrl+S 保存）' : '先选择或新建一个作品；也可以在右侧先把灵感 → 主线 → 大纲 → 主角立起来'"
        ></textarea>
      </div>

      <!-- 创作工坊面板（右侧，与老手系统 AI 面板同位） -->
      <div class="ai-panel glass-card nb-shop-panel">
        <WorkshopPanel />
      </div>
    </div>
  </div>

  <!-- 闪念便签（右下角悬浮，Ctrl+Shift+N，与老手系统一致） -->
  <NotesFloat />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api/index.js'
import { useWritingStore } from '../../stores/writing.js'
import { useToast } from '../../composables/useToast.js'
import WorkshopPanel from './WorkshopPanel.vue'
import NotesFloat from '../../components/NotesFloat.vue'

const store = useWritingStore()
const toast = useToast()
const route = useRoute()
const works = ref([])
const chapters = ref([])
const saving = ref(false)
const saveStatus = ref('unsaved')
const editorRef = ref(null)

const saveLabel = computed(() => ({
  saved: '已保存',
  saving: '保存中…',
  unsaved: '',
}[saveStatus.value] || ''))

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
  saveStatus.value = 'saved'
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
  if (chapterId === store.activeChapterId) return
  // 先保存当前章节，防止切换丢失
  if (store.activeChapterId && store.content.trim()) await save()
  await store.switchChapter(chapterId)
  chapters.value = [...store.chapters]
  editorRef.value?.focus()
}

async function addChapter() {
  const ch = await store.addChapter()
  if (ch) chapters.value = [...store.chapters]
}

async function save(status) {
  if (!store.currentWorkId || saving.value) return
  saving.value = true
  saveStatus.value = 'saving'
  const payload = {
    work_id: store.currentWorkId,
    title: store.title || '未命名作品',
    chapter_id: store.activeChapterId,
    chapter_title: store.getActiveChapterTitle() || '',
    content: store.content,
  }
  if (status === 'formal' || status === 'draft') payload.status = status
  const res = await api.post('/api/works/save', payload)
  saving.value = false
  if (res.code === 0) {
    saveStatus.value = 'saved'
    if (status === 'formal' || status === 'draft') {
      const ch = store.chapters.find(c => c.chapter_id === store.activeChapterId)
      if (ch) ch.status = status
      chapters.value = [...store.chapters]
    }
    toast.success('已保存')
  } else {
    saveStatus.value = 'unsaved'
    toast.error(res.msg)
  }
}

// P6-C1：当前激活章节是否为正式稿
const activeChapterFormal = computed(() => {
  const ch = store.chapters.find(c => c.chapter_id === store.activeChapterId)
  return ch?.status === 'formal'
})

// P6-C1：切换章节草稿/正式稿状态（立即保存）
async function onToggleFormal() {
  if (!store.activeChapterId) return
  await save(activeChapterFormal.value ? 'draft' : 'formal')
}

async function exportWork() {
  if (!store.currentWorkId) return
  await save()
  await api.download(`/api/works/${store.currentWorkId}/export?formal=1`, `${store.title || '作品'}-正式稿.txt`)
}

function openGuide() {
  window.dispatchEvent(new CustomEvent('inkstone:open-guide'))
}

function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    if (store.currentWorkId) save()
  }
}

onMounted(() => {
  loadWorks()
  window.addEventListener('keydown', onKeydown)
  // 与老手系统一致：支持 /write/new?work=ID 直达已有作品（从作品列表「编辑」进入）
  const qw = route.query.work
  if (qw && !store.currentWorkId) {
    store.currentWorkId = Number(qw)
    openWork()
  }
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
/* ====== 与老手系统 WriteStudio 同款布局骨架 ====== */
.studio-root {
  display: flex; flex-direction: column;
  height: calc(100vh - 80px);
  max-width: 1400px; margin: 0 auto;
  padding: 0.75rem 1rem;
  position: relative; z-index: 1;
}

/* ====== 顶部信息栏 ====== */
.studio-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.6rem 1rem;
  flex-shrink: 0; z-index: 10;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(196, 163, 90, 0.08);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}
.header-left, .header-right {
  display: flex; align-items: center; gap: 0.75rem;
}
.title-accent {
  color: var(--accent-primary);
  opacity: 0.4;
  font-size: 0.8rem;
  transform: rotate(-15deg);
}
.nb-mode-tag {
  font-family: var(--font-serif);
  font-size: 1rem; font-weight: 600;
  color: var(--accent-primary);
  opacity: 0.85;
  white-space: nowrap;
}
.nb-select {
  font-family: var(--font-serif);
  font-size: 1rem; font-weight: 600;
  color: var(--text-primary);
  background: transparent; border: none;
  border-bottom: 1px solid transparent;
  padding: 2px 0; outline: none;
  max-width: 220px;
  cursor: pointer;
  transition: border-color 0.2s ease;
}
.nb-select:focus { border-bottom-color: var(--accent-primary); }
.nb-select option { color: var(--text-primary); background: var(--bg-panel, #161923); }
.nb-add-btn {
  background: none; border: 1px dashed rgba(196, 163, 90, 0.3);
  color: var(--text-muted); font-size: 0.75rem;
  padding: 4px 10px; border-radius: 6px;
  cursor: pointer; transition: all 0.2s;
}
.nb-add-btn:hover {
  color: var(--accent-primary);
  border-color: var(--accent-primary);
  background: rgba(196, 163, 90, 0.06);
}

.save-badge {
  display: flex; align-items: center; gap: 5px;
  font-size: 0.72rem; color: var(--text-muted);
  letter-spacing: 0.04em;
  transition: color 0.3s ease;
}
.save-badge.saved { color: var(--accent-green, #4ade80); }
.save-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--text-muted);
  transition: background 0.3s ease;
}
.save-badge.saved .save-dot { background: var(--accent-green, #4ade80); }
.save-badge.saving .save-dot { background: var(--accent-warm, #f59e0b); animation: savePulse 0.8s infinite; }
.save-badge.unsaved .save-dot { background: var(--accent-primary); }
@keyframes savePulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.word-badge {
  font-family: var(--font-display, var(--font-serif));
  font-size: 0.9rem; color: var(--text-secondary);
  letter-spacing: 0.02em;
  background: rgba(196, 163, 90, 0.06);
  border: 1px solid rgba(196, 163, 90, 0.1);
  border-radius: 20px;
  padding: 3px 14px;
}
.word-badge small { font-size: 0.65rem; color: var(--text-muted); }

.header-btn {
  background: none; border: none;
  color: var(--text-muted); font-size: 0.9rem;
  padding: 6px 10px; border-radius: 6px;
  cursor: pointer; transition: all 0.2s ease;
  display: flex; align-items: center;
}
.header-btn:hover { color: var(--text-primary); background: rgba(255,255,255,0.04); }
.save-btn {
  color: var(--accent-primary);
  border: 1px solid rgba(196,163,90,0.15);
  border-radius: 6px; padding: 5px 14px;
  font-size: 0.8rem; font-weight: 600;
  letter-spacing: 0.04em;
  transition: all 0.25s ease;
}
.save-btn:hover {
  background: rgba(196,163,90,0.12);
  border-color: rgba(196,163,90,0.35);
  box-shadow: 0 0 16px rgba(196,163,90,0.08);
}
.save-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.header-btn-ghost { color: var(--text-secondary); }

/* ====== 主体 ====== */
.studio-body {
  flex: 1; display: flex; gap: 0.75rem;
  min-height: 0; overflow: hidden;
}

/* ====== 章节侧边栏（与老手同款） ====== */
.chapter-sidebar {
  width: 200px; flex-shrink: 0;
  display: flex; flex-direction: column;
  overflow: hidden;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(196, 163, 90, 0.08);
  background: rgba(255, 255, 255, 0.025);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
.sidebar-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.5rem 0.6rem;
  border-bottom: 1px solid rgba(196, 163, 90, 0.08);
  flex-shrink: 0;
}
.sidebar-title {
  font-size: 0.75rem; font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.sidebar-list {
  flex: 1; overflow-y: auto; padding: 0.35rem;
}
.chapter-item {
  display: flex; align-items: center; gap: 0.4rem;
  padding: 0.45rem 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 2px;
}
.chapter-item:hover { background: rgba(196, 163, 90, 0.06); }
.chapter-item.active {
  background: rgba(196, 163, 90, 0.1);
  border-left: 2px solid var(--accent-primary);
}
.ch-num {
  font-size: 0.65rem; font-weight: 700;
  color: var(--accent-primary); opacity: 0.5;
  min-width: 14px;
}
.chapter-item.active .ch-num { opacity: 1; }
.ch-title {
  flex: 1; font-size: 0.78rem;
  color: var(--text-secondary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.chapter-item.active .ch-title { color: var(--text-primary); }
.ch-status {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--text-muted); opacity: 0.45;
  flex-shrink: 0; margin: 0 6px;
}
.ch-status.is-formal {
  background: var(--accent-green); opacity: 1;
  box-shadow: 0 0 6px rgba(107, 207, 127, 0.6);
}
.ch-wc {
  font-size: 0.6rem; color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}
.add-chapter-btn {
  width: 100%;
  padding: 0.45rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  background: none; border: 1px dashed rgba(196, 163, 90, 0.15);
  border-radius: 6px;
  cursor: pointer;
  margin-top: 0.3rem;
  transition: all 0.2s;
}
.add-chapter-btn:hover {
  color: var(--accent-primary);
  border-color: rgba(196, 163, 90, 0.3);
  background: rgba(196, 163, 90, 0.04);
}
.nb-sidebar-empty {
  flex: 1; display: flex; align-items: center; justify-content: center;
  color: var(--text-muted); font-size: 0.75rem; line-height: 1.9;
  text-align: center; padding: 1rem;
}

/* ====== 章节标题栏 + 编辑器（与老手同款） ====== */
.chapter-title-bar {
  padding: 0.3rem 0;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}
.chapter-title-input {
  flex: 1;
  font-family: var(--font-serif);
  font-size: 0.95rem; font-weight: 600;
  color: var(--text-primary);
  background: transparent; border: none;
  border-bottom: 1px solid transparent;
  padding: 4px 0; outline: none;
  transition: border-color 0.2s;
}
.chapter-title-input:focus { border-bottom-color: rgba(196, 163, 90, 0.3); }
.chapter-title-input::placeholder { color: var(--text-muted); }

/* P6-C1：草稿/正式稿切换按钮 */
.formal-toggle {
  flex-shrink: 0;
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.04);
  border: 1px dashed rgba(196, 163, 90, 0.25);
  border-radius: 20px;
  padding: 3px 12px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.formal-toggle:hover {
  color: var(--accent-green);
  border-color: rgba(107, 207, 127, 0.5);
}
.formal-toggle.is-formal {
  color: var(--accent-green);
  border: 1px solid rgba(107, 207, 127, 0.45);
  background: rgba(107, 207, 127, 0.08);
}

.editor-panel {
  flex: 1; display: flex; flex-direction: column;
  min-width: 0; position: relative;
}
.editor-area {
  flex: 1; width: 100%; resize: none;
  padding: 1.5rem;
  font-family: var(--font-serif);
  font-size: 1.05rem; line-height: 2;
  border-radius: var(--radius-lg);
  background:
    linear-gradient(
      175deg,
      rgba(255, 255, 255, 0.04) 0%,
      rgba(255, 255, 255, 0.025) 40%,
      rgba(255, 255, 255, 0.03) 100%
    );
  border: 1px solid rgba(196, 163, 90, 0.1);
  border-left: 2px solid rgba(196, 163, 90, 0.15);
  color: #d4d0c8;
  letter-spacing: 0.02em;
  box-shadow:
    inset 0 0 120px rgba(196, 163, 90, 0.015),
    inset 0 0 4px rgba(0, 0, 0, 0.3),
    0 4px 32px rgba(0, 0, 0, 0.25);
  transition: border-color 0.4s ease, box-shadow 0.4s ease, font-size 0.3s ease;
}
.editor-area::placeholder {
  color: rgba(196, 163, 90, 0.22);
  font-style: italic;
  letter-spacing: 0.04em;
}
.editor-area:focus {
  border-color: rgba(196, 163, 90, 0.35);
  border-left-color: var(--accent-primary);
  box-shadow:
    inset 0 0 120px rgba(196, 163, 90, 0.025),
    inset 0 0 4px rgba(0, 0, 0, 0.3),
    0 4px 32px rgba(0, 0, 0, 0.25),
    0 0 0 4px rgba(196, 163, 90, 0.05);
}

/* ====== 右侧创作工坊面板（与老手 AI 面板同位同宽） ====== */
.nb-shop-panel {
  width: 420px; display: flex; flex-direction: column;
  overflow-y: auto;
  box-shadow: -4px 0 32px rgba(0, 0, 0, 0.3);
  border-left: 1px solid rgba(196, 163, 90, 0.06);
  padding: 1rem 1.1rem;
}

@media (max-width: 1100px) {
  .nb-shop-panel { width: 360px; }
  .chapter-sidebar { width: 160px; }
}
</style>