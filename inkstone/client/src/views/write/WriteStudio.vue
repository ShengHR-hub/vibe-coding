<template>
  <div class="studio-root" :class="{ 'focus-mode': isFocusMode }">
    <!-- 静态装饰元素 -->
    <div class="studio-decor" aria-hidden="true">
      <span class="sd-orb"></span>
      <span class="sd-ring"></span>
    </div>

    <!-- ====== 顶部信息栏 ====== -->
    <header class="studio-header" v-show="!isFocusMode">
      <div class="header-left">
        <span class="title-accent">&#x2731;</span>
        <input
          class="work-title"
          v-model="writingStore.title"
          placeholder="未命名作品"
          @blur="onTitleBlur"
        />
        <span class="save-badge" :class="saveStatus">
          <span class="save-dot"></span>
          {{ saveLabel }}
        </span>
      </div>
      <div class="header-right">
        <span class="word-badge">{{ writingStore.wordCount }}<small> 字</small></span>
        <PomodoroTimer @complete="onPomodoroComplete" />
        <button class="header-btn" @click="toggleFocus" title="专注模式">
          <span class="hbtn-icon">⛶</span>
        </button>
        <button class="header-btn save-btn" @click="saveDraft" :disabled="saveStatus === 'saving'">
          保存
        </button>
      </div>
    </header>

    <!-- ====== 主体：章节栏 + 编辑器 + AI 面板 ====== -->
    <div class="studio-body">
      <!-- 章节侧边栏 -->
      <aside class="chapter-sidebar glass-card" :class="{ collapsed: sidebarCollapsed }" v-show="!isFocusMode">
        <div class="sidebar-header">
          <span class="sidebar-title" v-if="!sidebarCollapsed">章节</span>
          <button class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed" :title="sidebarCollapsed ? '展开' : '折叠'">
            {{ sidebarCollapsed ? '»' : '«' }}
          </button>
        </div>
        <div class="sidebar-list" v-if="!sidebarCollapsed">
          <div
            v-for="(ch, idx) in writingStore.chapters"
            :key="ch.chapter_id"
            class="chapter-item"
            :class="{ active: ch.chapter_id === writingStore.activeChapterId }"
            draggable="true"
            @click="onChapterClick(ch.chapter_id)"
            @dragstart="onDragStart(idx)"
            @dragover.prevent
            @drop="onDrop(idx)"
            @contextmenu.prevent="onChapterContext($event, ch)"
          >
            <span class="ch-num">{{ idx + 1 }}</span>
            <span class="ch-title">{{ ch.title || `第${idx + 1}章` }}</span>
            <span class="ch-wc">{{ ch.word_count || 0 }}</span>
          </div>
          <button class="add-chapter-btn" @click="onAddChapter">+ 新增章节</button>
        </div>
        <!-- 右键菜单 -->
        <div v-if="contextMenu.visible" class="context-menu" :style="{ top: contextMenu.y + 'px', left: contextMenu.x + 'px' }" @click.stop>
          <div class="ctx-item" @click="startRename">重命名</div>
          <div class="ctx-item ctx-danger" @click="onDeleteChapter">删除</div>
        </div>
      </aside>

      <!-- 编辑器 -->
      <div class="editor-panel">
        <!-- 章节标题 -->
        <div class="chapter-title-bar" v-if="writingStore.chapters.length > 0">
          <input
            class="chapter-title-input"
            :value="writingStore.getActiveChapterTitle()"
            @input="onChapterTitleInput($event.target.value)"
            @blur="onChapterTitleBlur"
            placeholder="章节标题"
          />
        </div>
        <textarea
          ref="editorRef"
          class="editor-area"
          v-model="writingStore.content"
          :placeholder="placeholderText"
          @keydown="onEditorKeydown"
        ></textarea>
        <!-- 专注模式退出提示 -->
        <div class="focus-hint" v-if="isFocusMode">
          按 <kbd>Esc</kbd> 退出专注模式
        </div>
      </div>

      <!-- AI 面板 -->
      <div class="ai-panel glass-card" :class="{ 'mobile-open': mobilePanelOpen }" v-show="!isFocusMode">
        <div class="ai-tabs">
          <button
            v-for="tab in tabs" :key="tab.key"
            class="ai-tab"
            :class="{ active: activeTab === tab.key }"
            @click="switchTab(tab.key)"
          >
            <span class="tab-icon">{{ tab.icon }}</span>
            <span class="tab-label">{{ tab.label }}</span>
          </button>
        </div>
        <div class="ai-content">
          <transition :name="tabTransitionName" mode="out-in" @before-enter="onTabBeforeEnter" @enter="onTabEnter">
            <component
              :is="activeComponent"
              :key="activeTab"
              :tab-key="activeTab"
              :content="writingStore.content"
              @insert="insertToEditor"
            />
          </transition>
        </div>
      </div>
    </div>

    <!-- 移动端 AI 浮动按钮 -->
    <button class="mobile-toggle" v-if="!isFocusMode" @click="mobilePanelOpen = !mobilePanelOpen">
      <span>{{ mobilePanelOpen ? '✕' : '✦' }}</span>
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, onActivated, onDeactivated, watch, nextTick } from 'vue'
import { useWritingStore } from '../../stores/writing.js'
import { api } from '../../api/index.js'
import gsap from 'gsap'
import ContinuePanel from './ContinuePanel.vue'
import InspirePanel from './InspirePanel.vue'
import OutlinePanel from './OutlinePanel.vue'
import CharacterPanel from './CharacterPanel.vue'
import PolishPanel from './PolishPanel.vue'
import PromptPanel from './PromptPanel.vue'
import PoemPanel from './PoemPanel.vue'
import ChatPanel from './ChatPanel.vue'
import MaterialPanel from './MaterialPanel.vue'
import DiagnosePanel from './DiagnosePanel.vue'
import PomodoroTimer from '../../components/PomodoroTimer.vue'

import { useToast } from '../../composables/useToast.js'
const toast = useToast()
const writingStore = useWritingStore()

// ---- Tab 状态 ----
const activeTab = ref('continue')
const tabTransitionName = ref('tab-slide-right')

const tabs = [
  { key: 'continue', label: '续写', icon: '→' },
  { key: 'inspire', label: '灵感', icon: '☆' },
  { key: 'outline', label: '大纲', icon: '≡' },
  { key: 'character', label: '角色', icon: '♛' },
  { key: 'polish', label: '润色', icon: '♦' },
  { key: 'chat', label: '对话', icon: ' ' },
  { key: 'poem', label: '诗词', icon: ' ' },
  { key: 'material', label: '素材', icon: ' ' },
  { key: 'prompt', label: '提示', icon: '✎' },
  { key: 'diagnose', label: '诊断', icon: '⚕' },
]

const componentMap = {
  continue: ContinuePanel,
  inspire: InspirePanel,
  outline: OutlinePanel,
  character: CharacterPanel,
  polish: PolishPanel,
  chat: ChatPanel,
  poem: PoemPanel,
  material: MaterialPanel,
  prompt: PromptPanel,
  diagnose: DiagnosePanel,
}
const activeComponent = computed(() => componentMap[activeTab.value])

function switchTab(key) {
  const newIdx = tabs.findIndex(t => t.key === key)
  const oldIdx = tabs.findIndex(t => t.key === activeTab.value)
  tabTransitionName.value = newIdx > oldIdx ? 'tab-slide-left' : 'tab-slide-right'
  activeTab.value = key
}

function onTabBeforeEnter(el) {
  gsap.set(el, { opacity: 0, x: tabTransitionName.value === 'tab-slide-left' ? 40 : -40 })
}
function onTabEnter(el) {
  gsap.to(el, { opacity: 1, x: 0, duration: 0.3, ease: 'power2.out' })
}

// ---- 章节管理 ----
const sidebarCollapsed = ref(false)
const contextMenu = ref({ visible: false, x: 0, y: 0, chapter: null })
let dragIdx = null

async function onChapterClick(chapterId) {
  if (chapterId === writingStore.activeChapterId) return
  // 先保存当前章节到服务器，防止切换后丢失修改
  if (writingStore.activeChapterId && writingStore.content !== lastSavedContent) {
    await saveDraft()
  }
  await writingStore.switchChapter(chapterId)
  lastSavedContent = writingStore.content
}

function onDragStart(idx) { dragIdx = idx }
function onDrop(idx) {
  if (dragIdx === null || dragIdx === idx) return
  const ids = writingStore.chapters.map(c => c.chapter_id)
  const [moved] = ids.splice(dragIdx, 1)
  ids.splice(idx, 0, moved)
  writingStore.reorderChapters(ids)
  dragIdx = null
}

async function onAddChapter() {
  await writingStore.addChapter()
}

function onChapterContext(e, ch) {
  contextMenu.value = { visible: true, x: e.clientX, y: e.clientY, chapter: ch }
  document.addEventListener('click', closeContextMenu, { once: true })
}

function closeContextMenu() {
  contextMenu.value.visible = false
}

function startRename() {
  const ch = contextMenu.value.chapter
  if (!ch) return
  const newTitle = prompt('章节标题', ch.title)
  if (newTitle !== null && newTitle.trim()) {
    ch.title = newTitle.trim()
    if (ch.chapter_id === writingStore.activeChapterId) {
      saveDraft()
    }
  }
  closeContextMenu()
}

async function onDeleteChapter() {
  const ch = contextMenu.value.chapter
  if (!ch) return
  if (writingStore.chapters.length <= 1) {
    toast.info('至少保留一个章节')
    closeContextMenu()
    return
  }
  if (!confirm(`确定删除「${ch.title}」吗？`)) {
    closeContextMenu()
    return
  }
  await writingStore.removeChapter(ch.chapter_id)
  closeContextMenu()
}

function onChapterTitleInput(val) {
  writingStore.setActiveChapterTitle(val)
}

function onChapterTitleBlur() {
  if (writingStore.activeChapterId) {
    saveDraft()
  }
}

// ---- 编辑器 ----
const editorRef = ref(null)
const isFocusMode = ref(false)

const prompts = [
  '开始书写你的故事...',
  '今天想写点什么？一个关于远方、关于遗憾、关于重逢的故事...',
  '用一句话开始：那是我第一次见到...',
  '写下你最想写却一直没写的那段文字',
  '灵感往往藏在第一个字之后，写下点什么吧',
]
const promptIdx = ref(Math.floor(Math.random() * prompts.length))
const placeholderText = computed(() => prompts[promptIdx.value])

function insertToEditor(text) {
  const el = editorRef.value
  if (!el) {
    writingStore.content += '\n' + text
    return
  }
  const start = el.selectionStart
  const end = el.selectionEnd
  const before = writingStore.content.slice(0, start)
  const after = writingStore.content.slice(end)
  writingStore.content = before + text + after
  nextTick(() => {
    el.focus()
    const pos = start + text.length
    el.setSelectionRange(pos, pos)
  })
}

function toggleFocus() {
  isFocusMode.value = !isFocusMode.value
  if (isFocusMode.value) {
    nextTick(() => editorRef.value?.focus())
  }
}

function onEditorKeydown(e) {
  // Ctrl+S 保存
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    saveDraft()
  }
  // Ctrl+Enter 触发 AI
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault()
    triggerActivePanel()
  }
  // Esc 退出专注模式
  if (e.key === 'Escape' && isFocusMode.value) {
    isFocusMode.value = false
  }
}

// 触发当前活跃面板的 AI 操作
function triggerActivePanel() {
  // 通过派发自定义事件，让面板组件监听
  window.dispatchEvent(new CustomEvent('inkstone:trigger-ai', { detail: { tab: activeTab.value } }))
}

// ---- 保存 ----
const saveStatus = ref('saved') // saved | saving | unsaved
const saveLabel = computed(() => {
  return { saved: '已保存', saving: '保存中...', unsaved: '未保存' }[saveStatus.value]
})
let saveTimer = null
let lastSavedContent = ''
let lastSavedTitle = ''

watch(() => writingStore.content, () => {
  if (writingStore.content !== lastSavedContent) {
    saveStatus.value = 'unsaved'
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => saveDraft(true), 3000)
  }
})

function onTitleBlur() {
  if (writingStore.title === lastSavedTitle) return
  saveDraft()
}

async function saveDraft() {
  if (saveStatus.value === 'saving') return
  saveStatus.value = 'saving'
  try {
    const payload = {
      title: writingStore.title || '未命名作品',
      content: writingStore.content,
      work_id: writingStore.currentWorkId || null,
      chapter_id: writingStore.activeChapterId || null,
      chapter_title: writingStore.getActiveChapterTitle() || '',
    }
    const res = await api.post('/api/works/save', payload)
    if (res.code === 0) {
      writingStore.currentWorkId = res.data?.work_id || writingStore.currentWorkId
      lastSavedContent = writingStore.content
      lastSavedTitle = writingStore.title
      // 更新当前章节的字数
      if (writingStore.activeChapterId) {
        const ch = writingStore.chapters.find(c => c.chapter_id === writingStore.activeChapterId)
        if (ch) ch.word_count = writingStore.content.replace(/\s/g, '').length
      }
      saveStatus.value = 'saved'
    } else {
      saveStatus.value = 'unsaved'
    }
  } catch {
    saveStatus.value = 'unsaved'
  }
  if (saveTimer) clearTimeout(saveTimer)
}

// ---- 响应式 ----
const mobilePanelOpen = ref(false)
const isMobile = ref(false)
function checkMobile() {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) mobilePanelOpen.value = false
}

// ---- 全局键盘监听（非编辑器内） ----
function onGlobalKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault()
    triggerActivePanel()
  }
  if (e.key === 'Escape' && isFocusMode.value) {
    isFocusMode.value = false
  }
}

// ---- 生命周期 ----
let statsTimer = null
let lastSentCount = 0
let lastTick = 0

function startStatsTimer() {
  lastSentCount = writingStore.wordCount
  lastTick = Date.now()
  if (statsTimer) clearInterval(statsTimer)
  statsTimer = setInterval(() => {
    const now = Date.now()
    const delta = writingStore.wordCount - lastSentCount
    const duration = Math.round((now - lastTick) / 1000)
    lastSentCount = writingStore.wordCount
    lastTick = now
    if (delta > 0) {
      api.post('/api/stats/session', {
        work_id: writingStore.currentWorkId || null,
        word_count: delta,
        duration,
      }).catch(() => {})
    }
  }, 60000)
}

function flushStats() {
  if (statsTimer) clearInterval(statsTimer)
  const now = Date.now()
  const delta = writingStore.wordCount - lastSentCount
  const duration = Math.round((now - lastTick) / 1000)
  if (delta > 0) {
    api.post('/api/stats/session', {
      work_id: writingStore.currentWorkId || null,
      word_count: delta,
      duration,
    }).catch(() => {})
  }
}

function onPomodoroComplete({ duration }) {
  flushStats()
  lastTick = Date.now()
  lastSentCount = writingStore.wordCount
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  window.addEventListener('keydown', onGlobalKeydown)
  startStatsTimer()
  // 如果已有作品ID，加载章节列表
  if (writingStore.currentWorkId) {
    await writingStore.loadChapters(writingStore.currentWorkId)
  }
})

// 监听 currentWorkId 变化，首次保存后自动加载章节
watch(() => writingStore.currentWorkId, async (newId) => {
  if (newId && writingStore.chapters.length === 0) {
    await writingStore.loadChapters(newId)
  }
})

onActivated(() => {
  startStatsTimer()
})

onDeactivated(() => {
  flushStats()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
  window.removeEventListener('keydown', onGlobalKeydown)
  flushStats()
  if (saveTimer) clearTimeout(saveTimer)
})
</script>

<style scoped>
.studio-root {
  display: flex; flex-direction: column;
  height: calc(100vh - 80px);
  max-width: 1400px; margin: 0 auto;
  padding: 0.75rem 1rem;
  transition: padding 0.3s ease;
  position: relative; z-index: 1;
}

/* ====== 静态装饰 ====== */
.studio-decor {
  position: fixed; inset: 0; z-index: 1; pointer-events: none; overflow: hidden;
}
.sd-orb {
  position: absolute;
  width: 500px; height: 500px;
  top: 20%; left: -150px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(196,163,90,0.04), transparent 70%);
}
.sd-ring {
  position: absolute;
  width: 320px; height: 320px;
  top: 15%; right: 120px;
  border-radius: 50%;
  border: 1px solid rgba(196,163,90,0.04);
  transform: rotate(15deg);
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
.work-title {
  font-family: var(--font-serif);
  font-size: 1.1rem; font-weight: 600;
  color: var(--text-primary);
  background: transparent; border: none;
  border-bottom: 1px solid transparent;
  padding: 2px 0; outline: none;
  width: 200px;
  transition: border-color 0.2s ease;
}
.work-title:focus { border-bottom-color: var(--accent-primary); }
.work-title::placeholder { color: var(--text-muted); }

.save-badge {
  display: flex; align-items: center; gap: 5px;
  font-size: 0.72rem; color: var(--text-muted);
  letter-spacing: 0.04em;
  transition: color 0.3s ease;
}
.save-badge.saved { color: var(--accent-green); }
.save-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--text-muted);
  transition: background 0.3s ease;
}
.save-badge.saved .save-dot { background: var(--accent-green); }
.save-badge.saving .save-dot { background: var(--accent-warm); animation: savePulse 0.8s infinite; }
.save-badge.unsaved .save-dot { background: var(--accent-primary); }
@keyframes savePulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.word-badge {
  font-family: var(--font-display);
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
.hbtn-icon { font-size: 1.1rem; }
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

/* ====== 主体 ====== */
.studio-body {
  flex: 1; display: flex; gap: 0.75rem;
  min-height: 0; overflow: hidden;
}

/* ====== 章节侧边栏 ====== */
.chapter-sidebar {
  width: 200px; flex-shrink: 0;
  display: flex; flex-direction: column;
  overflow: hidden;
  transition: width 0.3s ease;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(196, 163, 90, 0.08);
  background: rgba(255, 255, 255, 0.025);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
.chapter-sidebar.collapsed { width: 40px; }

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
.sidebar-toggle {
  background: none; border: none;
  color: var(--text-muted); font-size: 0.8rem;
  cursor: pointer; padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.2s;
}
.sidebar-toggle:hover {
  color: var(--accent-primary);
  background: rgba(196, 163, 90, 0.08);
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
.chapter-item:hover {
  background: rgba(196, 163, 90, 0.06);
}
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

/* 右键菜单 */
.context-menu {
  position: fixed;
  background: rgba(20, 20, 35, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 4px;
  z-index: 999;
  min-width: 120px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}
.ctx-item {
  padding: 6px 12px;
  font-size: 0.78rem;
  color: var(--text-secondary);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}
.ctx-item:hover {
  background: rgba(196, 163, 90, 0.1);
  color: var(--text-primary);
}
.ctx-danger:hover {
  background: rgba(220, 60, 60, 0.12);
  color: #e55;
}

/* 章节标题栏 */
.chapter-title-bar {
  padding: 0.3rem 0;
  flex-shrink: 0;
}
.chapter-title-input {
  width: 100%;
  font-family: var(--font-serif);
  font-size: 0.95rem; font-weight: 600;
  color: var(--text-primary);
  background: transparent; border: none;
  border-bottom: 1px solid transparent;
  padding: 4px 0; outline: none;
  transition: border-color 0.2s;
}
.chapter-title-input:focus {
  border-bottom-color: rgba(196, 163, 90, 0.3);
}
.chapter-title-input::placeholder { color: var(--text-muted); }

/* 编辑器 */
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
  color: rgba(196, 163, 90, 0.2);
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

/* AI 面板 */
.ai-panel {
  width: 420px; display: flex; flex-direction: column;
  overflow: hidden; flex-shrink: 0;
  box-shadow: -4px 0 32px rgba(0, 0, 0, 0.3);
  border-left: 1px solid rgba(196, 163, 90, 0.06);
}
.ai-tabs {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  border-bottom: 1px solid rgba(196, 163, 90, 0.08);
  padding: 0.25rem; flex-shrink: 0;
  background: rgba(255, 255, 255, 0.02);
  gap: 2px;
}
.ai-tab {
  display: flex; align-items: center; justify-content: center; gap: 4px;
  padding: 7px 6px; font-size: 0.78rem;
  color: var(--text-muted); background: none;
  border: none; border-bottom: 2px solid transparent;
  border-radius: 6px 6px 0 0;
  cursor: pointer; transition: all 0.25s ease;
  white-space: nowrap;
  position: relative;
}
.ai-tab:hover {
  color: var(--text-primary);
  background: rgba(196, 163, 90, 0.04);
}
.ai-tab.active {
  color: var(--accent-primary);
  background: rgba(196, 163, 90, 0.05);
  border-bottom-color: var(--accent-primary);
}
.ai-tab.active::after {
  content: '';
  position: absolute; bottom: -1px; left: 50%;
  transform: translateX(-50%);
  width: 20px; height: 2px;
  border-radius: 1px;
  background: var(--accent-primary);
  box-shadow: 0 0 8px rgba(196, 163, 90, 0.4);
}
.tab-icon { font-size: 0.85rem; }
.tab-label { letter-spacing: 0.04em; }

.ai-content {
  flex: 1; overflow-y: auto; overflow-x: hidden;
  padding: 1rem; position: relative;
  background: rgba(255, 255, 255, 0.02);
}

/* ====== 专注模式 ====== */
.focus-mode { padding: 0; }
.focus-mode .studio-body { gap: 0; }
.focus-mode .chapter-sidebar { display: none; }
.focus-mode .editor-panel { padding: 0; }
.focus-mode .editor-area {
  border-radius: 0; border: none;
  border-left: 1px solid rgba(196, 163, 90, 0.06);
  font-size: 1.15rem; line-height: 2.3;
  padding: 4rem 6rem;
  background: transparent;
  box-shadow: none;
}
/* Focus vignette */
.focus-mode::after {
  content: '';
  position: fixed; inset: 0;
  pointer-events: none; z-index: 50;
  background: radial-gradient(ellipse at center, transparent 60%, rgba(0, 0, 0, 0.4) 100%);
}
.focus-hint {
  position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%);
  font-size: 0.8rem; color: var(--text-muted);
  pointer-events: none; z-index: 200;
  animation: hintFade 3s ease-in-out forwards;
  opacity: 0;
}
@keyframes hintFade {
  0% { opacity: 0; }
  10% { opacity: 0.6; }
  80% { opacity: 0.6; }
  100% { opacity: 0; }
}
.focus-hint kbd {
  display: inline-block;
  padding: 1px 6px; border-radius: 3px;
  border: 1px solid var(--border-glass);
  font-family: var(--font-sans); font-size: 0.75rem;
}

/* ====== 移动端按钮 ====== */
.mobile-toggle {
  display: none; position: fixed;
  bottom: 24px; right: 24px;
  width: 48px; height: 48px; border-radius: 50%;
  background: linear-gradient(135deg, #c4a35a, #9b7d3c);
  color: #0f0f1a; font-size: 1.2rem;
  box-shadow: 0 4px 24px rgba(196,163,90,0.35);
  z-index: 99; align-items: center; justify-content: center;
  cursor: pointer; border: none;
}

/* ====== 响应式 ====== */
@media (max-width: 900px) {
  .ai-panel { width: 360px; }
}
@media (max-width: 768px) {
  .ai-panel {
    position: fixed; right: 0; top: 80px; bottom: 0;
    width: 380px; max-width: 90vw;
    transform: translateX(105%);
    transition: transform 0.35s cubic-bezier(0.16,1,0.3,1);
    z-index: 80; border-radius: 16px 0 0 16px;
  }
  .ai-panel.mobile-open { transform: translateX(0); }
  .mobile-toggle { display: flex; }
  .work-title { width: 120px; }
  .chapter-sidebar { display: none; }
  .focus-mode .editor-area { padding: 2rem 1.5rem; font-size: 1.05rem; }
}
@media (max-width: 480px) {
  .studio-header { flex-wrap: wrap; gap: 0.5rem; }
  .header-left, .header-right { width: 100%; justify-content: space-between; }
}
</style>
