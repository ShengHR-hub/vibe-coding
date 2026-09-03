<template>
  <div class="reader-container" v-if="work" :class="`bg-${settings.bgTheme}`" @click="handleContainerClick">
    <!-- 背景粒子装饰 -->
    <div class="reader-particles" v-if="settings.bgTheme !== 'light' && settings.bgTheme !== 'sepia' && settings.bgTheme !== 'black'"></div>
    <!-- 阅读进度条 -->
    <div class="reading-progress-bar">
      <div class="reading-progress-fill" :style="{ width: scrollPercent + '%' }"></div>
    </div>

    <!-- 沉浸式工具栏 -->
    <transition name="toolbar">
      <div v-show="toolbarVisible" class="reader-toolbar" @click.stop>
        <div class="toolbar-top">
          <button class="btn btn-ghost btn-sm" @click="$router.push('/library?from=reading')">&larr; 返回</button>
          <span class="toolbar-title">{{ work.title }}</span>
          <div class="toolbar-actions">
            <!-- 常用按钮 -->
            <button class="btn btn-ghost btn-sm" @click="toggleChapterPanel">&#128214; 目录</button>
            <button class="btn btn-ghost btn-sm" @click="toggleSearch">&#128269; 搜索</button>
            <button class="btn btn-ghost btn-sm" @click="toggleSettings">&#9881; 设置</button>
            <button v-if="userStore.isLoggedIn" class="btn btn-ghost btn-sm" @click="toggleBookmarkPanel">&#128278; 书签</button>
            <button v-if="bookType === 'work'" class="btn btn-ghost btn-sm" @click="toggleLike" :class="{ active: liked }">
              {{ liked ? '&#10084;&#65039;' : '&#129293;' }} {{ work.likes_count || 0 }}
            </button>
            <button v-if="bookType === 'work'" class="btn btn-ghost btn-sm" @click="toggleFavorite" :class="{ active: favorited }">
              {{ favorited ? '&#11088;' : '&#9734;' }} 收藏
            </button>
            <button class="btn btn-ghost btn-sm" @click="toggleShelf" :class="{ active: onShelf }">
              {{ onShelf ? '&#128218;' : '&#128214;' }}
            </button>
            <!-- 更多按钮 -->
            <div class="toolbar-more" @click.stop="showMoreMenu = !showMoreMenu">
              <button class="btn btn-ghost btn-sm">···</button>
              <transition name="fade">
                <div v-if="showMoreMenu" class="more-menu glass-card">
                  <button v-if="userStore.isLoggedIn" class="more-item" @click="toggleAnnotationPanel">&#128221; 批注</button>
                  <button v-if="userStore.isLoggedIn" class="more-item" @click="generateSummary">&#129504; AI 摘要</button>
                  <button v-if="bookType === 'work' && userStore.isLoggedIn" class="more-item" @click="goToGraph()">  图谱</button>
                  <button v-if="bookType === 'work' && userStore.isLoggedIn" class="more-item" @click="goToReview()">  书评</button>
                  <button class="more-item" @click="sharePosterVisible = true">  分享</button>
                  <button v-if="bookType === 'work'" class="more-item" @click="handleExport">  导出</button>
                  <button v-if="bookType === 'work' && userStore.isLoggedIn && work.user_id === userStore.user?.user_id" class="more-item" @click="$router.push(`/works/${work.work_id}/volumes`)">  卷管理</button>
                  <button v-if="bookType === 'work' && userStore.isLoggedIn" class="more-item" @click="$router.push(`/rp/${work.work_id}`)">  角色扮演</button>
                </div>
              </transition>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 设置面板 -->
    <transition name="settings">
      <div v-if="showSettings" class="settings-panel glass-card" @click.stop>
        <div class="setting-group">
          <label>字体大小</label>
          <div class="setting-row">
            <input type="range" v-model.number="settings.fontSize" min="14" max="26" step="1" />
            <span class="setting-value">{{ settings.fontSize }}px</span>
          </div>
        </div>
        <div class="setting-group">
          <label>行间距</label>
          <div class="setting-options">
            <button v-for="lh in [1.6, 1.8, 2.0, 2.4]" :key="lh"
                    class="opt-btn" :class="{ active: settings.lineHeight === lh }"
                    @click="settings.lineHeight = lh">{{ lh }}</button>
          </div>
        </div>
        <div class="setting-group">
          <label>字体</label>
          <div class="setting-options">
            <button v-for="f in fontOptions" :key="f.value"
                    class="opt-btn" :class="{ active: settings.fontFamily === f.value }"
                    @click="settings.fontFamily = f.value">{{ f.label }}</button>
          </div>
        </div>
        <div class="setting-group">
          <label>背景</label>
          <div class="setting-options">
            <button v-for="b in bgOptions" :key="b.value"
                    class="opt-btn bg-opt" :class="{ active: settings.bgTheme === b.value }"
                    :style="{ background: b.color }"
                    @click="settings.bgTheme = b.value">{{ b.label }}</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 搜索面板 -->
    <transition name="settings">
      <div v-if="showSearch" class="search-panel glass-card" @click.stop>
        <div class="search-input-row">
          <input
            ref="searchInputRef"
            v-model="searchQuery"
            type="text"
            placeholder="搜索当前章节..."
            class="search-input"
            @keydown.enter="searchNext"
            @keydown.escape="showSearch = false"
          />
          <span class="search-count" v-if="searchQuery">
            {{ searchMatchIndex + 1 }}/{{ searchMatchCount }}
          </span>
          <button class="btn btn-ghost btn-xs" @click="searchPrev">&#9650;</button>
          <button class="btn btn-ghost btn-xs" @click="searchNext">&#9660;</button>
          <button class="btn btn-ghost btn-xs" @click="clearSearch">&#10005;</button>
        </div>
      </div>
    </transition>

    <!-- 书签面板 -->
    <transition name="settings">
      <div v-if="showBookmarkPanel" class="side-panel glass-card" @click.stop>
        <div class="panel-header">
          <h3>书签</h3>
          <button class="btn btn-ghost btn-xs" @click="showBookmarkPanel = false">&#10005;</button>
        </div>
        <button class="btn btn-primary btn-sm" style="width:100%;margin-bottom:0.75rem" @click="addBookmark">
          + 添加书签
        </button>
        <div v-if="bookmarks.length === 0" class="panel-empty">暂无书签</div>
        <div v-for="bm in bookmarks" :key="bm.bookmark_id" class="panel-item" @click="jumpToBookmark(bm)">
          <div class="panel-item-title">{{ bm.selected_text || `第${bm.chapter_no}章` }}</div>
          <div class="panel-item-meta">
            第{{ bm.chapter_no }}章
            <span class="panel-item-del" @click.stop="deleteBookmark(bm)">&#10005;</span>
          </div>
          <div v-if="bm.note" class="panel-item-note">{{ bm.note }}</div>
        </div>
      </div>
    </transition>

    <!-- 批注面板 -->
    <transition name="settings">
      <div v-if="showAnnotationPanel" class="side-panel glass-card" @click.stop>
        <div class="panel-header">
          <h3>批注</h3>
          <button class="btn btn-ghost btn-xs" @click="showAnnotationPanel = false">&#10005;</button>
        </div>
        <div v-if="chapterAnnotations.length === 0" class="panel-empty">本章暂无批注</div>
        <div v-for="ann in chapterAnnotations" :key="ann.annotation_id" class="panel-item annotation-item">
          <div class="panel-item-quote">"{{ ann.selected_text }}"</div>
          <div class="panel-item-content">{{ ann.content }}</div>
          <div class="panel-item-meta">
            {{ ann.username }}
            <span v-if="!ann.is_public" class="badge-private">私密</span>
            <span v-if="ann.user_id === userStore.user?.user_id" class="panel-item-del" @click="deleteAnnotationLocal(ann)">&#10005;</span>
          </div>
        </div>
      </div>
    </transition>

    <!-- 章节目录面板 -->
    <transition name="settings">
      <div v-if="showChapterPanel" class="side-panel glass-card chapter-panel" @click.stop>
        <div class="panel-header">
          <h3>目录 ({{ chapters.length }}章)</h3>
          <button class="btn btn-ghost btn-xs" @click="showChapterPanel = false">&#10005;</button>
        </div>
        <div class="chapter-list">
          <div v-for="(ch, i) in chapters" :key="ch.chapter_id"
               class="chapter-item" :class="{ active: i === activeChapterIdx }"
               @click="jumpToChapter(i)">
            <span class="chapter-num">{{ i + 1 }}</span>
            <span class="chapter-title">{{ ch.title || `第${ch.chapter_no || i + 1}章` }}</span>
            <span class="chapter-wc" v-if="ch.word_count">{{ ch.word_count }}字</span>
          </div>
        </div>
      </div>
    </transition>

    <!-- 选中文字浮动操作栏 -->
    <transition name="fade">
      <div v-if="selectionBar.visible" class="selection-bar glass-card" :style="{ top: selectionBar.y + 'px', left: selectionBar.x + 'px' }" @click.stop>
        <button class="sel-btn" @click="startAnnotation">&#128221; 批注</button>
        <button class="sel-btn" @click="markHighlight">&#10024; 好句</button>
        <button class="sel-btn" @click="copySelection">&#128203; 复制</button>
      </div>
    </transition>

    <!-- 批注输入弹窗 -->
    <div v-if="annotationDialog.visible" class="dialog-overlay" @click.self="annotationDialog.visible = false">
      <div class="dialog glass-card" @click.stop>
        <h3>添加批注</h3>
        <p class="dialog-quote">"{{ annotationDialog.selectedText }}"</p>
        <textarea v-model="annotationDialog.content" rows="3" placeholder="写下你的批注..."></textarea>
        <div class="dialog-toggle">
          <label><input type="checkbox" v-model="annotationDialog.isPublic" /> 公开批注</label>
        </div>
        <div class="dialog-actions">
          <button class="btn btn-ghost" @click="annotationDialog.visible = false">取消</button>
          <button class="btn btn-primary" @click="submitAnnotation" :disabled="!annotationDialog.content.trim()">提交</button>
        </div>
      </div>
    </div>

    <!-- AI 摘要弹窗 -->
    <div v-if="showSummaryDialog" class="dialog-overlay" @click.self="showSummaryDialog = false">
      <div class="dialog glass-card summary-dialog" @click.stop>
        <h3>AI 章节摘要</h3>
        <div v-if="summaryLoading" class="summary-loading">
          <div class="loading-spinner"></div>
          <span>正在生成摘要...</span>
        </div>
        <div v-else class="summary-content">
          {{ summaryContent }}
        </div>
        <div class="dialog-actions">
          <button class="btn btn-ghost" @click="showSummaryDialog = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- 阅读内容 -->
    <div class="reader-content"
         :style="{ fontSize: settings.fontSize + 'px', lineHeight: settings.lineHeight, fontFamily: settings.fontFamily }"
         @click.stop>
      <!-- 章节导航 -->
      <div v-if="chapters.length > 0" class="chapter-nav" ref="chapterNavRef">
        <div class="chapter-select" @click="chapterDropdownOpen = !chapterDropdownOpen">
          <span>{{ chapters[activeChapterIdx]?.title || `第${activeChapterIdx + 1}章` }}</span>
          <span class="dropdown-arrow">{{ chapterDropdownOpen ? '&#9650;' : '&#9660;' }}</span>
        </div>
        <div v-if="chapterDropdownOpen" class="dropdown-list">
          <div v-for="(ch, i) in chapters" :key="ch.chapter_id"
               class="dropdown-item" :class="{ active: i === activeChapterIdx }"
               @click="switchChapter(i)">
            {{ ch.title || `第${ch.chapter_no || i + 1}章` }}
          </div>
        </div>
      </div>

      <h1 class="work-title">{{ work.title }}</h1>
      <div class="work-info">
        <span>{{ authorName }}</span>
        <span>{{ typeLabel(work.type) }}</span>
        <span>{{ work.word_count || 0 }} 字</span>
      </div>

      <div class="chapter-content" v-html="renderedContent" @mouseup="handleTextSelection"></div>

      <!-- 章节翻页 -->
      <div v-if="chapters.length > 1" class="chapter-pager">
        <button class="btn btn-ghost" :disabled="activeChapterIdx <= 0" @click="switchChapter(activeChapterIdx - 1)">上一章</button>
        <span class="pager-info">{{ activeChapterIdx + 1 }} / {{ chapters.length }}</span>
        <button class="btn btn-ghost" :disabled="activeChapterIdx >= chapters.length - 1" @click="switchChapter(activeChapterIdx + 1)">下一章</button>
      </div>

      <hr />

      <!-- 评论（仅限 works，默认折叠） -->
      <div v-if="bookType === 'work'" class="comments-section">
        <h3 class="comments-toggle" @click="commentsExpanded = !commentsExpanded">
          <span>评论 ({{ comments.length }})</span>
          <span class="toggle-arrow">{{ commentsExpanded ? '▲' : '▼' }}</span>
        </h3>
        <div v-show="commentsExpanded">
        <div v-if="userStore.isLoggedIn" class="comment-form">
          <textarea v-model="newComment" rows="2" placeholder="写下你的评论..."></textarea>
          <button class="btn btn-primary btn-sm" @click="submitComment(null)" :disabled="!newComment.trim() || submitting">发表</button>
        </div>
        <div v-else class="muted">请<router-link to="/login">登录</router-link>后发表评论</div>
        <div v-if="comments.length === 0" class="muted" style="margin-top:1rem">暂无评论</div>
        <div v-for="c in comments" :key="c.comment_id" class="comment">
          <div class="comment-header">
            <span class="comment-avatar">{{ c.username?.charAt(0) }}</span>
            <strong>{{ c.username }}</strong>
            <span class="muted">{{ fmt(c.created_at) }}</span>
          </div>
          <p>{{ c.content }}</p>
          <button v-if="userStore.isLoggedIn" class="btn btn-ghost btn-xs" @click="replyingTo = replyingTo === c.comment_id ? null : c.comment_id">回复</button>
          <div v-if="replyingTo === c.comment_id" class="comment-form reply-form">
            <textarea v-model="replyContent" rows="2" placeholder="写下回复..."></textarea>
            <button class="btn btn-primary btn-xs" @click="submitComment(c.comment_id)" :disabled="!replyContent.trim()">回复</button>
          </div>
          <div v-if="c.replies?.length" class="replies">
            <div v-for="r in c.replies" :key="r.comment_id" class="comment reply">
              <div class="comment-header">
                <span class="comment-avatar">{{ r.username?.charAt(0) }}</span>
                <strong>{{ r.username }}</strong>
                <span class="muted">{{ fmt(r.created_at) }}</span>
              </div>
              <p>{{ r.content }}</p>
            </div>
          </div>
        </div>
        </div>
      </div>
    </div>

    <!-- 底部信息栏 -->
    <transition name="toolbar">
      <div v-show="toolbarVisible" class="reader-bottom" @click.stop>
        <span>{{ chapters[activeChapterIdx]?.title || '' }}</span>
        <span v-if="chapters.length > 0">{{ activeChapterIdx + 1 }}/{{ chapters.length }}</span>
      </div>
    </transition>
  </div>
  <div v-else-if="errorMsg" class="page-container center">{{ errorMsg }}</div>
  <div v-else class="page-container center">加载中...</div>
  <SharePoster v-if="bookType === 'work'" :visible="sharePosterVisible" :work-id="work?.work_id" @close="sharePosterVisible = false" />
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import { useUserStore } from '../../stores/user.js'
import SharePoster from '../../components/SharePoster.vue'

import { useToast } from '../../composables/useToast.js'
const toast = useToast()
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const work = ref(null)
const chapters = ref([])
const comments = ref([])
const errorMsg = ref('')
const liked = ref(false)
const favorited = ref(false)
const onShelf = ref(false)
const shelfId = ref(null)
const activeChapterIdx = ref(0)
const newComment = ref('')
const replyContent = ref('')
const replyingTo = ref(null)
const submitting = ref(false)
const sharePosterVisible = ref(false)
const chapterDropdownOpen = ref(false)
const chapterNavRef = ref(null)
const showMoreMenu = ref(false)
const commentsExpanded = ref(false)

// 书签
const showBookmarkPanel = ref(false)
const bookmarks = ref([])

// 批注
const showAnnotationPanel = ref(false)
const chapterAnnotations = ref([])
const annotationDialog = ref({ visible: false, selectedText: '', paragraphIndex: 0, content: '', isPublic: true })

// 章节目录
const showChapterPanel = ref(false)

// 选中文字浮动栏
const selectionBar = ref({ visible: false, x: 0, y: 0, text: '', paragraphIndex: 0 })

// 书内搜索
const showSearch = ref(false)
const searchQuery = ref('')
const searchMatchCount = ref(0)
const searchMatchIndex = ref(0)
const searchInputRef = ref(null)
let searchMatches = []

// 沉浸式工具栏
const toolbarVisible = ref(false)
const showSettings = ref(false)
let hideTimer = null

// 阅读设置（存入 localStorage）
const defaultSettings = { fontSize: 16, lineHeight: 2.0, fontFamily: 'inherit', bgTheme: 'dark' }
let savedSettings = {}
try { savedSettings = JSON.parse(localStorage.getItem('reader-settings') || '{}') } catch {}
const settings = reactive({ ...defaultSettings, ...savedSettings })

watch(settings, (v) => localStorage.setItem('reader-settings', JSON.stringify(v)), { deep: true })

// 阅读计时（含活跃检测，累计活跃秒数，卸载时一次性提交）
let activeSeconds = 0
let lastActiveTime = Date.now()
let progressTimer = null
let tickingTimer = null
const scrollPercent = ref(0)
function markActive() { lastActiveTime = Date.now() }
function trackScroll() {
  const scrollTop = window.scrollY || document.documentElement.scrollTop
  const docHeight = document.documentElement.scrollHeight - window.innerHeight
  scrollPercent.value = docHeight > 0 ? Math.min(100, Math.round((scrollTop / docHeight) * 100)) : 0
}

const fontOptions = [
  { value: 'inherit', label: '默认' },
  { value: 'serif', label: '宋体' },
  { value: '"KaiTi", serif', label: '楷体' },
  { value: '"SimHei", sans-serif', label: '黑体' },
]
const bgOptions = [
  { value: 'dark', label: '暗色', color: 'linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16162a 100%)' },
  { value: 'green', label: '护眼', color: 'linear-gradient(135deg, #0f1a0f 0%, #1a2e1a 50%, #162a16 100%)' },
  { value: 'paper', label: '羊皮纸', color: 'linear-gradient(135deg, #1a1610 0%, #2e2a1a 50%, #2a2616 100%)' },
  { value: 'light', label: '亮色', color: 'linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 50%, #f0f0f0 100%)' },
  { value: 'black', label: '纯黑', color: '#000' },
  { value: 'sepia', label: '护眼绿', color: 'linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 50%, #dcedc8 100%)' },
]

// 来源判断（用 ref 而非 computed，避免 onUnmounted 时路由已变导致值丢失）
const bookType = ref(route.params.type || route.query.source || 'work')
const bookId = ref(route.params.id)
const authorName = computed(() => bookType.value === 'library' ? (work.value?.author || '') : (work.value?.username || ''))

const renderedContent = computed(() => {
  const ch = chapters.value[activeChapterIdx.value]
  if (!ch?.content) return '<p class="muted">暂无内容</p>'
  return '<p>' + ch.content
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>') + '</p>'
})

function handleContainerClick() {
  toolbarVisible.value = !toolbarVisible.value
  showSettings.value = false
  showBookmarkPanel.value = false
  showAnnotationPanel.value = false
  selectionBar.value.visible = false
  showMoreMenu.value = false
  clearTimeout(hideTimer)
}

function resetHideTimer() {
  clearTimeout(hideTimer)
  // 有面板打开时不自动隐藏
  if (toolbarVisible.value && !showSettings.value && !showBookmarkPanel.value && !showAnnotationPanel.value) {
    hideTimer = setTimeout(() => { toolbarVisible.value = false }, 5000)
  }
}

function onDocClick(e) {
  if (chapterNavRef.value && !chapterNavRef.value.contains(e.target)) {
    chapterDropdownOpen.value = false
  }
}

function onKeydown(e) {
  // Ctrl+F 触发搜索
  if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
    e.preventDefault()
    toggleSearch()
  }
  // 左右箭头翻章（无面板打开时）
  if (!showSettings.value && !showBookmarkPanel.value && !showAnnotationPanel.value && !showChapterPanel.value && !showSearch.value) {
    if (e.key === 'ArrowLeft') {
      e.preventDefault()
      switchChapter(activeChapterIdx.value - 1)
    } else if (e.key === 'ArrowRight') {
      e.preventDefault()
      switchChapter(activeChapterIdx.value + 1)
    }
  }
  // Escape 关闭面板
  if (e.key === 'Escape') {
    showMoreMenu.value = false
    showSettings.value = false
    showBookmarkPanel.value = false
    showAnnotationPanel.value = false
    showChapterPanel.value = false
    showSearch.value = false
  }
}

onMounted(async () => {
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onKeydown)
  document.addEventListener('mousemove', markActive)
  document.addEventListener('keydown', markActive)
  document.addEventListener('scroll', markActive)
  document.addEventListener('scroll', trackScroll)
  document.addEventListener('visibilitychange', onVisibilityChange)
  await loadBook()
  // 每秒累计活跃时间
  lastActiveTime = Date.now()
  tickingTimer = setInterval(() => {
    if (document.hidden) return
    if (Date.now() - lastActiveTime > 120000) return // 超过2分钟无操作不计时
    activeSeconds++
  }, 1000)
  // 每 2 分钟自动保存阅读进度
  progressTimer = setInterval(() => {
    if (userStore.isLoggedIn) saveProgress()
  }, 120000)
  window.addEventListener('beforeunload', onBeforeUnload)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onKeydown)
  document.removeEventListener('mousemove', markActive)
  document.removeEventListener('keydown', markActive)
  document.removeEventListener('scroll', markActive)
  document.removeEventListener('scroll', trackScroll)
  document.removeEventListener('visibilitychange', onVisibilityChange)
  window.removeEventListener('beforeunload', onBeforeUnload)
  clearTimeout(hideTimer)
  clearInterval(tickingTimer)
  clearInterval(progressTimer)
  flushReadingTime()
  saveProgress()
})

async function loadBook() {
  let res
  if (bookType.value === 'library') {
    res = await api.get(`/api/library/${bookId.value}?source=library`)
  } else {
    res = await api.get(`/api/works/public/${bookId.value}`)
  }
  if (res.code === 0) {
    if (bookType.value === 'library') {
      work.value = res.data.book
      chapters.value = res.data.chapters || []
      onShelf.value = res.data.on_shelf || false
      shelfId.value = res.data.shelf_id || null
    } else {
      work.value = res.data.work
      chapters.value = res.data.chapters || []
      liked.value = res.data.liked || false
      favorited.value = res.data.favorited || false
      await loadComments()
    }
    await restoreProgress()
    const targetChapter = route.query.chapter
    if (targetChapter) {
      const idx = chapters.value.findIndex(ch => String(ch.chapter_id) === String(targetChapter))
      if (idx >= 0) activeChapterIdx.value = idx
    }
    if (userStore.isLoggedIn) {
      loadBookmarks()
      loadChapterAnnotations()
      autoAddToShelf()
    }
  } else {
    errorMsg.value = res.msg
  }
}

async function restoreProgress() {
  if (!userStore.isLoggedIn) return
  try {
    const res = await api.get(`/api/reading/progress/${bookType.value}/${bookId.value}`)
    if (res.code === 0 && res.data.progress) {
      const p = res.data.progress
      if (p.chapter_no > 0 && p.chapter_no <= chapters.value.length) {
        const savedIdx = p.chapter_no - 1
        if (savedIdx !== activeChapterIdx.value) {
          activeChapterIdx.value = savedIdx
          toast.info(`已恢复到第 ${p.chapter_no} 章`)
        }
      }
    }
  } catch {}
}

let saveProgressTimer = null
async function saveProgress() {
  if (!userStore.isLoggedIn || !work.value) return
  clearTimeout(saveProgressTimer)
  saveProgressTimer = setTimeout(async () => {
    const ch = chapters.value[activeChapterIdx.value]
    if (!ch) return
    await api.put(`/api/reading/progress/${bookType.value}/${bookId.value}`, {
      chapter_id: ch.chapter_id,
      chapter_no: ch.chapter_no || activeChapterIdx.value + 1,
      scroll_percent: scrollPercent.value,
    })
  }, 300)
}

function switchChapter(idx) {
  if (idx < 0 || idx >= chapters.value.length) return
  activeChapterIdx.value = idx
  chapterDropdownOpen.value = false
  saveProgress()
  window.scrollTo({ top: 0, behavior: 'smooth' })
  if (userStore.isLoggedIn) loadChapterAnnotations()
}

async function autoAddToShelf() {
  if (!userStore.isLoggedIn || onShelf.value) return
  try {
    const res = await api.post('/api/bookshelf', {
      book_type: bookType.value,
      book_id: Number(bookId.value),
      shelf_group: 'reading',
    })
    if (res.code === 0) {
      onShelf.value = true
      shelfId.value = res.data.shelf_id
    }
  } catch {}
}

async function toggleShelf() {
  if (!userStore.isLoggedIn) { toast.error('请先登录'); return }
  if (onShelf.value) {
    if (!shelfId.value) return
    const res = await api.delete(`/api/bookshelf/${shelfId.value}`)
    if (res.code === 0) { onShelf.value = false; shelfId.value = null }
  } else {
    const res = await api.post('/api/bookshelf', {
      book_type: bookType.value,
      book_id: Number(bookId.value),
      shelf_group: 'reading',
    })
    if (res.code === 0) { onShelf.value = true; shelfId.value = res.data.shelf_id }
  }
}

async function loadComments() {
  const res = await api.get(`/api/interactions/comments/${bookId.value}`)
  if (res.code === 0) comments.value = res.data.comments
}

async function toggleLike() {
  if (!userStore.isLoggedIn) { toast.error('请先登录'); return }
  const res = await api.post('/api/interactions/like', { work_id: work.value.work_id })
  if (res.code === 0) {
    liked.value = res.data.liked
    work.value.likes_count = (work.value.likes_count || 0) + (res.data.liked ? 1 : -1)
  }
}

async function toggleFavorite() {
  if (!userStore.isLoggedIn) { toast.error('请先登录'); return }
  const res = await api.post('/api/interactions/favorite', { work_id: work.value.work_id })
  if (res.code === 0) favorited.value = res.data.favorited
}

async function submitComment(parentId) {
  const content = parentId ? replyContent.value.trim() : newComment.value.trim()
  if (!content) return
  submitting.value = true
  const res = await api.post('/api/interactions/comments', { work_id: work.value.work_id, content, parent_id: parentId })
  if (res.code === 0) {
    if (parentId) { replyContent.value = ''; replyingTo.value = null } else { newComment.value = '' }
    await loadComments()
    work.value.comments_count = (work.value.comments_count || 0) + 1
  } else { toast.info(res.msg) }
  submitting.value = false
}

function goToGraph() { if (work.value) router.push(`/graph/${work.value.work_id}`) }
function goToReview() { if (work.value) router.push(`/review/${work.value.work_id}`) }
async function handleExport() {
  const res = await api.download(`/api/works/${work.value.work_id}/export`)
  if (res.code !== 0) toast.error(res.msg || '导出失败')
}
function typeLabel(t) {
  return { novel: '小说', poetry: '诗歌', essay: '散文', webfiction: '网文', script: '剧本' }[t] || t
}
function fmt(d) { if (!d) return ''; return d.slice(0, 16).replace('T', ' ') }

// ====== 书签 ======
function toggleBookmarkPanel() {
  showBookmarkPanel.value = !showBookmarkPanel.value
  showAnnotationPanel.value = false
  showSettings.value = false
  if (showBookmarkPanel.value) loadBookmarks()
  resetHideTimer()
}

async function loadBookmarks() {
  if (!userStore.isLoggedIn) return
  const res = await api.get(`/api/bookmarks?book_type=${bookType.value}&book_id=${bookId.value}`)
  if (res.code === 0) bookmarks.value = res.data.items
}

async function addBookmark() {
  const ch = chapters.value[activeChapterIdx.value]
  if (!ch) return
  const sel = window.getSelection()
  const selectedText = sel ? sel.toString().trim().slice(0, 200) : ''
  const res = await api.post('/api/bookmarks', {
    book_type: bookType.value,
    book_id: Number(bookId.value),
    chapter_id: ch.chapter_id,
    chapter_no: ch.chapter_no || activeChapterIdx.value + 1,
    selected_text: selectedText,
  })
  if (res.code === 0) {
    await loadBookmarks()
  } else {
    toast.info(res.msg)
  }
}

async function deleteBookmark(bm) {
  const res = await api.delete(`/api/bookmarks/${bm.bookmark_id}`)
  if (res.code === 0) bookmarks.value = bookmarks.value.filter(b => b.bookmark_id !== bm.bookmark_id)
}

function jumpToBookmark(bm) {
  const idx = chapters.value.findIndex(ch => ch.chapter_id === bm.chapter_id)
  if (idx >= 0) {
    activeChapterIdx.value = idx
    showBookmarkPanel.value = false
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

// ====== 批注 ======
function toggleAnnotationPanel() {
  showAnnotationPanel.value = !showAnnotationPanel.value
  showBookmarkPanel.value = false
  showSettings.value = false
  showChapterPanel.value = false
  if (showAnnotationPanel.value) loadChapterAnnotations()
  resetHideTimer()
}

function toggleChapterPanel() {
  showChapterPanel.value = !showChapterPanel.value
  showBookmarkPanel.value = false
  showSettings.value = false
  showAnnotationPanel.value = false
  resetHideTimer()
}

function jumpToChapter(idx) {
  switchChapter(idx)
  showChapterPanel.value = false
}

// AI 摘要
const showSummaryDialog = ref(false)
const summaryContent = ref('')
const summaryLoading = ref(false)

async function generateSummary() {
  const ch = chapters.value[activeChapterIdx.value]
  if (!ch || !ch.content) {
    toast.info('当前章节没有内容')
    return
  }
  if (ch.content.length < 100) {
    toast.info('内容太短，无法生成摘要')
    return
  }

  summaryLoading.value = true
  showSummaryDialog.value = true
  summaryContent.value = ''

  try {
    const res = await api.post('/api/write/summary', {
      title: ch.title || `第${activeChapterIdx.value + 1}章`,
      content: ch.content
    })
    if (res.code === 0) {
      summaryContent.value = res.data.summary
    } else {
      toast.error(res.msg)
      showSummaryDialog.value = false
    }
  } catch (e) {
    toast.error('摘要生成失败')
    showSummaryDialog.value = false
  } finally {
    summaryLoading.value = false
  }
}

function toggleSettings() {
  showSettings.value = !showSettings.value
  showBookmarkPanel.value = false
  showAnnotationPanel.value = false
  resetHideTimer()
}

async function loadChapterAnnotations() {
  if (!userStore.isLoggedIn) return
  const ch = chapters.value[activeChapterIdx.value]
  if (!ch) return
  const res = await api.get(`/api/annotations/${bookType.value}/${bookId.value}/${ch.chapter_id}`)
  if (res.code === 0) chapterAnnotations.value = res.data.annotations
}

async function submitAnnotation() {
  const ch = chapters.value[activeChapterIdx.value]
  if (!ch) return
  const res = await api.post('/api/annotations', {
    book_type: bookType.value,
    book_id: Number(bookId.value),
    chapter_id: ch.chapter_id,
    chapter_no: ch.chapter_no || activeChapterIdx.value + 1,
    paragraph_index: annotationDialog.value.paragraphIndex,
    selected_text: annotationDialog.value.selectedText,
    content: annotationDialog.value.content.trim(),
    is_public: annotationDialog.value.isPublic,
  })
  if (res.code === 0) {
    annotationDialog.value.visible = false
    annotationDialog.value.content = ''
    await loadChapterAnnotations()
  } else {
    toast.info(res.msg)
  }
}

async function deleteAnnotationLocal(ann) {
  const res = await api.delete(`/api/annotations/${ann.annotation_id}`)
  if (res.code === 0) chapterAnnotations.value = chapterAnnotations.value.filter(a => a.annotation_id !== ann.annotation_id)
}

// ====== 选中文字操作 ======
function handleTextSelection(e) {
  const sel = window.getSelection()
  const text = sel ? sel.toString().trim() : ''
  if (!text || text.length < 2) {
    selectionBar.value.visible = false
    return
  }
  const range = sel.getRangeAt(0)
  const rect = range.getBoundingClientRect()
  const barWidth = 180
  let x = rect.left + rect.width / 2 - barWidth / 2
  let y = rect.top - 40 + window.scrollY
  // 边界检测
  x = Math.max(8, Math.min(x, window.innerWidth - barWidth - 8))
  if (y < window.scrollY + 8) y = rect.bottom + 8 + window.scrollY
  selectionBar.value = {
    visible: true,
    x,
    y,
    text: text.slice(0, 500),
    paragraphIndex: 0,
  }
  resetHideTimer()
}

function startAnnotation() {
  annotationDialog.value = {
    visible: true,
    selectedText: selectionBar.value.text,
    paragraphIndex: selectionBar.value.paragraphIndex,
    content: '',
    isPublic: true,
  }
  selectionBar.value.visible = false
}

function copySelection() {
  navigator.clipboard.writeText(selectionBar.value.text).catch(() => {
    // 降级：用 execCommand 兜底
    const ta = document.createElement('textarea')
    ta.value = selectionBar.value.text
    ta.style.cssText = 'position:fixed;left:-9999px'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    ta.remove()
  })
  selectionBar.value.visible = false
}

// ====== 书内搜索 ======
function toggleSearch() {
  showSearch.value = !showSearch.value
  showSettings.value = false
  showBookmarkPanel.value = false
  showAnnotationPanel.value = false
  if (showSearch.value) {
    nextTick(() => searchInputRef.value?.focus())
  } else {
    clearSearch()
  }
}

watch(searchQuery, (q) => {
  if (!q) {
    clearSearch()
    return
  }
  highlightMatches(q)
})

function highlightMatches(query) {
  // 清除旧高亮
  document.querySelectorAll('.reader-content .search-highlight').forEach(el => {
    el.replaceWith(el.textContent)
  })
  searchMatches = []
  searchMatchIndex.value = 0
  searchMatchCount.value = 0

  if (!query) return

  const contentEl = document.querySelector('.chapter-content')
  if (!contentEl) return

  const walker = document.createTreeWalker(contentEl, NodeFilter.SHOW_TEXT)
  const textNodes = []
  while (walker.nextNode()) textNodes.push(walker.currentNode)

  const regex = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi')

  textNodes.forEach(node => {
    const text = node.textContent
    if (!regex.test(text)) return
    regex.lastIndex = 0

    const fragment = document.createDocumentFragment()
    let lastIdx = 0
    let match

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIdx) {
        fragment.appendChild(document.createTextNode(text.slice(lastIdx, match.index)))
      }
      const mark = document.createElement('mark')
      mark.className = 'search-highlight'
      mark.textContent = match[0]
      fragment.appendChild(mark)
      searchMatches.push(mark)
      lastIdx = regex.lastIndex
    }
    if (lastIdx < text.length) {
      fragment.appendChild(document.createTextNode(text.slice(lastIdx)))
    }
    node.replaceWith(fragment)
  })

  searchMatchCount.value = searchMatches.length
  if (searchMatches.length > 0) {
    searchMatches[0].classList.add('search-current')
    searchMatches[0].scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

function searchNext() {
  if (searchMatches.length === 0) return
  searchMatches[searchMatchIndex.value]?.classList.remove('search-current')
  searchMatchIndex.value = (searchMatchIndex.value + 1) % searchMatches.length
  searchMatches[searchMatchIndex.value].classList.add('search-current')
  searchMatches[searchMatchIndex.value].scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function searchPrev() {
  if (searchMatches.length === 0) return
  searchMatches[searchMatchIndex.value]?.classList.remove('search-current')
  searchMatchIndex.value = (searchMatchIndex.value - 1 + searchMatches.length) % searchMatches.length
  searchMatches[searchMatchIndex.value].classList.add('search-current')
  searchMatches[searchMatchIndex.value].scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function clearSearch() {
  document.querySelectorAll('.reader-content .search-highlight').forEach(el => {
    el.replaceWith(el.textContent)
  })
  searchMatches = []
  searchMatchCount.value = 0
  searchMatchIndex.value = 0
  searchQuery.value = ''
}

async function markHighlight() {
  if (!userStore.isLoggedIn) { toast.error('请先登录'); return }
  const ch = chapters.value[activeChapterIdx.value]
  if (!ch) return
  const res = await api.post('/api/highlights', {
    book_type: bookType.value,
    book_id: Number(bookId.value),
    chapter_id: ch.chapter_id,
    chapter_no: ch.chapter_no || activeChapterIdx.value + 1,
    selected_text: selectionBar.value.text,
  })
  selectionBar.value.visible = false
  if (res.code === 0) {
    toast.success('已标记好句')
  } else {
    toast.info(res.msg)
  }
}

// ====== 阅读计时 ======
function flushReadingTime() {
  if (!userStore.isLoggedIn) return
  const minutes = Math.floor(activeSeconds / 60)
  if (minutes > 0) {
    api.post('/api/reading/checkin', {
      read_minutes: minutes,
      book_type: bookType.value,
      book_id: Number(bookId.value)
    })
    activeSeconds -= minutes * 60 // 保留余数
  }
}

function onVisibilityChange() {
  if (document.hidden) {
    // 页面切后台时刷一次
    flushReadingTime()
  } else {
    lastActiveTime = Date.now()
  }
}

function onBeforeUnload() {
  flushReadingTime()
}
</script>

<style scoped>
/* ====== 阅读进度条 ====== */
.reading-progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 99;
  background: rgba(255, 255, 255, 0.03);
}
.reading-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-primary), #a78bfa, var(--accent-warm));
  transition: width 0.15s ease-out;
  box-shadow: 0 0 12px rgba(196, 163, 90, 0.5);
  border-radius: 0 2px 2px 0;
}

/* ====== 阅读容器 ====== */
.reader-container {
  min-height: 100vh;
  transition: all 0.6s cubic-bezier(0.16,1,0.3,1);
  position: relative;
  z-index: 1;
  overflow-x: hidden;
  /* 光晕效果通过 background-image 叠加在背景色之上 */
  background-image:
    radial-gradient(ellipse 800px 600px at 10% 15%, rgba(196, 163, 90, 0.15) 0%, transparent 60%),
    radial-gradient(ellipse 600px 600px at 90% 80%, rgba(167, 139, 250, 0.1) 0%, transparent 60%),
    radial-gradient(ellipse 500px 400px at 50% 50%, rgba(196, 163, 90, 0.06) 0%, transparent 60%);
  background-size: 100% 100%;
  animation: bgDrift 20s ease-in-out infinite alternate;
}
@keyframes bgDrift {
  0% { background-position: 0% 0%; }
  50% { background-position: 3% 2%; }
  100% { background-position: -2% -1%; }
}

/* 浮动装饰粒子 - 用独立的 fixed 层 */
.reader-particles {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(3px 3px at 15% 25%, rgba(196,163,90,0.25), transparent),
    radial-gradient(3px 3px at 85% 65%, rgba(196,163,90,0.2), transparent),
    radial-gradient(2px 2px at 35% 75%, rgba(167,139,250,0.18), transparent),
    radial-gradient(2px 2px at 65% 15%, rgba(196,163,90,0.15), transparent),
    radial-gradient(2px 2px at 50% 50%, rgba(167,139,250,0.12), transparent),
    radial-gradient(4px 4px at 25% 60%, rgba(196,163,90,0.1), transparent),
    radial-gradient(3px 3px at 75% 40%, rgba(167,139,250,0.08), transparent);
  animation: particleFloat 15s ease-in-out infinite alternate;
}
@keyframes particleFloat {
  0% { opacity: 0.5; transform: translateY(0); }
  50% { opacity: 1; transform: translateY(-10px); }
  100% { opacity: 0.6; transform: translateY(5px); }
}

.reader-container.bg-dark {
  background-color: #0e0e1a;
  color: #d8d8e8;
}
.reader-container.bg-green {
  background-color: #0a120a;
  color: #c8e6c9;
}
.reader-container.bg-paper {
  background-color: #14120e;
  color: #d7ccc8;
}
.reader-container.bg-light {
  background-color: #f5f5f5;
  background-image:
    radial-gradient(ellipse 600px 400px at 15% 20%, rgba(196, 163, 90, 0.04) 0%, transparent 70%),
    radial-gradient(ellipse 500px 500px at 85% 70%, rgba(167, 139, 250, 0.03) 0%, transparent 70%);
  color: #2a2a2a;
}
.reader-container.bg-black {
  background-color: #000;
  background-image: none;
  color: #888;
}
.reader-container.bg-sepia {
  background-color: #e0f0e2;
  background-image:
    radial-gradient(ellipse 600px 400px at 15% 20%, rgba(196, 163, 90, 0.03) 0%, transparent 70%);
  color: #2e5a2e;
}

/* ====== 工具栏 ====== */
.reader-toolbar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  background: rgba(10,10,18,0.75);
  backdrop-filter: blur(32px) saturate(200%);
  -webkit-backdrop-filter: blur(32px) saturate(200%);
  border-bottom: 1px solid rgba(196,163,90,0.1);
  padding: 0.6rem 1.5rem;
  box-shadow: 0 4px 40px rgba(0,0,0,0.4), inset 0 -1px 0 rgba(196,163,90,0.05);
}
.toolbar-top { display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; }
.toolbar-title {
  font-size: 0.88rem; color: var(--text-primary);
  max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  font-weight: 500; letter-spacing: 0.04em;
  opacity: 0.8;
}
.toolbar-actions { display: flex; gap: 4px; align-items: center; flex-wrap: wrap; }
.toolbar-actions .btn {
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 0.78rem;
  transition: all 0.2s ease;
  color: var(--text-muted);
}
.toolbar-actions .btn:hover {
  background: rgba(196,163,90,0.12);
  color: var(--text-primary);
  transform: translateY(-1px);
}
.toolbar-actions .active { color: var(--accent-warm); background: rgba(196,163,90,0.1); }

/* 更多菜单 */
.toolbar-more { position: relative; }
.more-menu {
  position: absolute; top: calc(100% + 8px); right: 0;
  min-width: 160px; padding: 6px;
  background: rgba(20,20,35,0.95);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(196,163,90,0.2);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  z-index: 200;
}
.more-item {
  display: block; width: 100%; text-align: left;
  padding: 8px 12px; font-size: 0.82rem;
  color: var(--text-secondary); background: none; border: none;
  cursor: pointer; border-radius: 6px; transition: all 0.15s;
}
.more-item:hover { background: rgba(196,163,90,0.12); color: var(--text-primary); }

/* 工具栏动画 */
.toolbar-enter-active, .toolbar-leave-active { transition: all 0.3s ease; }
.toolbar-enter-from, .toolbar-leave-to { opacity: 0; transform: translateY(-100%); }

/* ====== 搜索面板 ====== */
.search-panel {
  position: fixed; top: 60px; right: 20px; z-index: 101;
  width: 360px; padding: var(--space-lg);
  background: rgba(10,10,18,0.92);
  backdrop-filter: blur(40px) saturate(200%);
  -webkit-backdrop-filter: blur(40px) saturate(200%);
  border: 1px solid rgba(196,163,90,0.1);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.search-input-row {
  display: flex; align-items: center; gap: var(--space-md);
}
.search-input {
  flex: 1; padding: 8px 14px; font-size: 0.88rem;
  background: rgba(255,255,255,0.06); color: var(--text-primary);
  border: 1px solid rgba(196,163,90,0.2);
  border-radius: var(--radius-md);
  outline: none;
  transition: all 0.2s ease;
}
.search-input:focus {
  border-color: var(--accent-primary);
  background: rgba(255,255,255,0.08);
  box-shadow: 0 0 12px rgba(196,163,90,0.2);
}
.search-count {
  font-size: 0.78rem; color: var(--text-muted);
  white-space: nowrap; font-weight: 500;
}

:deep(.search-highlight) {
  background: rgba(196, 163, 90, 0.25);
  color: inherit;
  border-radius: 3px;
  padding: 2px 0;
  transition: all 0.2s ease;
}
:deep(.search-highlight.search-current) {
  background: rgba(196, 163, 90, 0.6);
  box-shadow: 0 0 8px rgba(196, 163, 90, 0.4);
  transform: scale(1.02);
}

/* ====== 设置面板 ====== */
.settings-panel {
  position: fixed; top: 60px; right: 20px; z-index: 101;
  width: 300px; padding: var(--space-xl);
  background: rgba(10,10,18,0.92);
  backdrop-filter: blur(40px) saturate(200%);
  -webkit-backdrop-filter: blur(40px) saturate(200%);
  border: 1px solid rgba(196,163,90,0.1);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.setting-group { margin-bottom: var(--space-lg); }
.setting-group label {
  display: block; font-size: 0.82rem; color: var(--text-muted);
  margin-bottom: var(--space-sm); font-weight: 500;
}
.setting-row { display: flex; align-items: center; gap: var(--space-md); }
.setting-row input[type="range"] {
  flex: 1; accent-color: var(--accent-primary);
  height: 4px;
}
.setting-value {
  font-size: 0.82rem; color: var(--text-secondary);
  min-width: 40px; text-align: right; font-weight: 500;
}
.setting-options { display: flex; gap: 6px; flex-wrap: wrap; }
.opt-btn {
  padding: 6px 14px; font-size: 0.8rem; border-radius: var(--radius-full);
  background: rgba(255,255,255,0.05); color: var(--text-muted);
  cursor: pointer; transition: all 0.2s ease;
  border: 1px solid transparent;
}
.opt-btn:hover {
  color: var(--text-primary);
  background: rgba(255,255,255,0.08);
  border-color: rgba(196,163,90,0.2);
}
.opt-btn.active {
  color: var(--accent-primary);
  background: rgba(196,163,90,0.15);
  border-color: rgba(196,163,90,0.3);
}
.bg-opt {
  width: 40px; height: 30px; border-radius: 8px; padding: 0; font-size: 0;
  border: 2px solid rgba(255,255,255,0.05);
  transition: all 0.25s cubic-bezier(0.16,1,0.3,1);
  position: relative;
}
.bg-opt:hover { transform: scale(1.15); border-color: rgba(255,255,255,0.15); }
.bg-opt.active {
  border-color: var(--accent-primary);
  box-shadow: 0 0 16px rgba(196,163,90,0.4), 0 2px 8px rgba(0,0,0,0.3);
  transform: scale(1.1);
}

.settings-enter-active, .settings-leave-active { transition: all 0.25s ease; }
.settings-enter-from, .settings-leave-to { opacity: 0; transform: translateY(-10px); }

/* ====== 底部信息栏 ====== */
.reader-bottom {
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 100;
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.5rem 1.5rem;
  background: rgba(10,10,18,0.7);
  backdrop-filter: blur(32px) saturate(200%);
  -webkit-backdrop-filter: blur(32px) saturate(200%);
  border-top: 1px solid rgba(196,163,90,0.08);
  font-size: 0.78rem; color: var(--text-muted);
  box-shadow: 0 -4px 40px rgba(0,0,0,0.3);
  letter-spacing: 0.05em;
}

/* ====== 阅读内容 ====== */
.reader-content {
  max-width: 700px; margin: 0 auto; padding: 5rem 2rem 10rem;
  min-height: 100vh;
  position: relative;
}

/* 左右装饰线 */
.reader-content::before,
.reader-content::after {
  content: '';
  position: absolute;
  top: 5rem;
  bottom: 5rem;
  width: 1px;
  pointer-events: none;
}
.reader-content::before {
  left: -2rem;
  background: linear-gradient(to bottom, transparent, rgba(196,163,90,0.06) 20%, rgba(196,163,90,0.06) 80%, transparent);
}
.reader-content::after {
  right: -2rem;
  background: linear-gradient(to bottom, transparent, rgba(196,163,90,0.06) 20%, rgba(196,163,90,0.06) 80%, transparent);
}

.chapter-nav { margin-bottom: var(--space-xl); position: relative; }
.chapter-select {
  padding: 10px 16px; font-size: 0.88rem; width: 100%;
  background: rgba(15,15,25,0.6);
  backdrop-filter: blur(16px);
  color: var(--text-primary);
  border: 1px solid rgba(196, 163, 90, 0.1);
  border-radius: var(--radius-md);
  cursor: pointer;
  display: flex; justify-content: space-between; align-items: center;
  transition: all 0.25s ease;
  letter-spacing: 0.04em;
}
.chapter-select:hover {
  border-color: rgba(196, 163, 90, 0.25);
  background: rgba(15,15,25,0.8);
}
.dropdown-arrow { font-size: 0.65rem; opacity: 0.4; }
.dropdown-list {
  position: absolute; top: calc(100% + 6px); left: 0; right: 0;
  max-height: 400px; overflow-y: auto; z-index: 100;
  background: rgba(12,12,20,0.95);
  backdrop-filter: blur(32px) saturate(200%);
  border: 1px solid rgba(196, 163, 90, 0.12);
  border-radius: var(--radius-md);
  box-shadow: 0 12px 40px rgba(0,0,0,0.5);
}
.dropdown-item {
  padding: 10px 16px; font-size: 0.85rem; color: var(--text-secondary);
  cursor: pointer; transition: all 0.15s;
  border-bottom: 1px solid rgba(255,255,255,0.02);
  letter-spacing: 0.03em;
}
.dropdown-item:hover { background: rgba(196, 163, 90, 0.08); color: var(--text-primary); }
.dropdown-item.active { color: var(--accent-primary); font-weight: 600; background: rgba(196, 163, 90, 0.06); }

.work-title {
  font-size: 2rem; margin-bottom: var(--space-md);
  font-family: var(--font-serif); letter-spacing: 0.08em;
  background: linear-gradient(135deg, var(--text-primary) 30%, var(--accent-primary));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  text-align: center;
  padding-bottom: var(--space-lg);
  position: relative;
}
.work-title::after {
  content: '';
  position: absolute;
  bottom: 0; left: 50%;
  transform: translateX(-50%);
  width: 60px; height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
  border-radius: 1px;
}
.work-info {
  display: flex; gap: var(--space-lg); font-size: 0.82rem;
  color: var(--text-muted); margin-bottom: var(--space-2xl);
  flex-wrap: wrap; justify-content: center;
  padding-bottom: var(--space-xl);
  letter-spacing: 0.04em;
}
.chapter-content {
  line-height: 2.1;
  letter-spacing: 0.03em;
}
.chapter-content :deep(p) {
  margin-bottom: 1.3em;
  text-indent: 2em;
  font-size: inherit;
}
hr {
  border: none;
  margin: var(--space-2xl) 0;
  position: relative;
  height: 20px;
}
hr::before {
  content: '· · ·';
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  color: var(--accent-primary);
  opacity: 0.3;
  letter-spacing: 0.8em;
  font-size: 0.9rem;
}

/* ====== 章节翻页 ====== */
.chapter-pager {
  display: flex; justify-content: center; align-items: stretch; gap: 0;
  margin-top: var(--space-2xl);
  border-top: 1px solid rgba(196,163,90,0.06);
}
.chapter-pager .btn {
  flex: 1;
  padding: 1.2rem 2rem;
  font-size: 0.9rem;
  border: none;
  background: transparent;
  color: var(--text-muted);
  transition: all 0.3s cubic-bezier(0.16,1,0.3,1);
  position: relative;
  letter-spacing: 0.04em;
}
.chapter-pager .btn::before {
  content: '';
  position: absolute;
  top: 0; bottom: 0;
  width: 0;
  background: linear-gradient(90deg, transparent, rgba(196,163,90,0.06));
  transition: width 0.4s ease;
}
.chapter-pager .btn:first-child::before { left: 0; }
.chapter-pager .btn:last-child::before { right: 0; background: linear-gradient(-90deg, transparent, rgba(196,163,90,0.06)); }
.chapter-pager .btn:hover:not(:disabled)::before { width: 100%; }
.chapter-pager .btn:hover:not(:disabled) {
  color: var(--accent-primary);
  transform: none;
}
.chapter-pager .btn:disabled {
  opacity: 0.2;
  cursor: not-allowed;
}
.pager-info {
  font-size: 0.82rem; color: var(--text-muted);
  font-weight: 400;
  letter-spacing: 0.15em;
  display: flex; align-items: center;
  padding: 0 1.5rem;
  opacity: 0.5;
}

/* 评论 */
.comments-section h3 { margin-bottom: var(--space-lg); color: var(--accent-primary); }
.comments-toggle {
  display: flex; justify-content: space-between; align-items: center;
  cursor: pointer; padding: 0.5rem 0;
  user-select: none;
}
.comments-toggle:hover { opacity: 0.8; }
.toggle-arrow { font-size: 0.75rem; opacity: 0.5; }
.comment-form { display: flex; gap: var(--space-sm); margin-bottom: var(--space-lg); }
.comment-form textarea {
  flex: 1; padding: 10px; font-size: 0.9rem; resize: vertical;
  background: transparent; color: inherit;
  border: 1px solid var(--border-glass); border-radius: var(--radius-sm); outline: none;
}
.comment-form textarea:focus { border-color: var(--accent-primary); }
.reply-form { margin: var(--space-sm) 0 var(--space-sm) var(--space-xl); }
.comment { padding: var(--space-md) 0; border-bottom: 1px solid var(--border-glass); }
.comment.reply { margin-left: var(--space-xl); }
.comment-header { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-sm); font-size: 0.85rem; }
.comment-avatar { width: 26px; height: 26px; border-radius: 50%; background: var(--accent-purple); color: white; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; }
.comment p { font-size: 0.9rem; }
.replies { margin-top: var(--space-sm); }
.muted { color: var(--text-muted); font-size: 0.85rem; }
.center { text-align: center; padding: var(--space-2xl); color: var(--text-muted); }
.btn-xs { padding: 2px 8px; font-size: 0.7rem; }
.btn-sm { padding: 4px 12px; font-size: 0.85rem; }

/* ====== 侧边面板（书签/批注） ====== */
.side-panel {
  position: fixed; top: 60px; right: 20px; z-index: 101;
  width: 340px; max-height: calc(100vh - 100px); overflow-y: auto;
  padding: var(--space-xl);
  background: rgba(10,10,18,0.92);
  backdrop-filter: blur(40px) saturate(200%);
  -webkit-backdrop-filter: blur(40px) saturate(200%);
  border: 1px solid rgba(196,163,90,0.1);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid rgba(196,163,90,0.1);
}
.panel-header h3 {
  font-size: 1rem; color: var(--accent-primary); margin: 0;
  font-weight: 600; letter-spacing: 0.02em;
}
.panel-empty {
  font-size: 0.85rem; color: var(--text-muted);
  text-align: center; padding: var(--space-xl) 0;
}
.panel-item {
  padding: var(--space-md) var(--space-lg); margin-bottom: var(--space-sm);
  border-radius: var(--radius-md); cursor: pointer;
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
  background: rgba(255,255,255,0.02);
}
.panel-item:hover {
  background: rgba(196,163,90,0.08);
  border-left-color: var(--accent-primary);
  transform: translateX(4px);
}
.panel-item-title {
  font-size: 0.88rem; color: var(--text-primary);
  margin-bottom: 4px; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap;
  font-weight: 500;
}
.panel-item-meta {
  font-size: 0.75rem; color: var(--text-muted);
  display: flex; align-items: center; gap: var(--space-sm);
}
.panel-item-note {
  font-size: 0.8rem; color: var(--text-secondary);
  margin-top: 6px; font-style: italic;
  opacity: 0.8;
}
.panel-item-del {
  cursor: pointer; margin-left: auto;
  opacity: 0.4; transition: all 0.2s;
  width: 20px; height: 20px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 50%;
}
.panel-item-del:hover {
  opacity: 1; color: #ef4444;
  background: rgba(239,68,68,0.1);
}

/* 批注项 */
.annotation-item { cursor: default; }
.panel-item-quote { font-size: 0.78rem; color: var(--accent-primary); opacity: 0.7; margin-bottom: 4px; font-style: italic; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.panel-item-content { font-size: 0.85rem; color: var(--text-primary); margin-bottom: 4px; }
.badge-private { font-size: 0.6rem; padding: 1px 5px; border-radius: var(--radius-full); background: rgba(239,68,68,0.12); color: #ef4444; }

/* ====== 选中文字浮动栏 ====== */
.selection-bar {
  position: absolute; z-index: 200;
  display: flex; gap: 2px; padding: 4px;
  background: rgba(15,15,26,0.95); backdrop-filter: blur(16px);
  border: 1px solid rgba(196,163,90,0.2);
  border-radius: var(--radius-sm);
  box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}
.sel-btn {
  padding: 5px 12px; font-size: 0.78rem; color: var(--text-secondary);
  background: none; border: none; cursor: pointer; border-radius: 3px;
  transition: all 0.15s ease; white-space: nowrap;
}
.sel-btn:hover { background: rgba(196,163,90,0.12); color: var(--accent-primary); }

/* ====== 批注输入弹窗 ====== */
.dialog-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;
}
.dialog { padding: var(--space-xl); width: 400px; }
.dialog h3 { margin-bottom: var(--space-md); }
.dialog-quote { font-size: 0.82rem; color: var(--accent-primary); font-style: italic; margin-bottom: var(--space-md); opacity: 0.8; max-height: 60px; overflow: hidden; }
.dialog textarea {
  width: 100%; padding: 10px; font-size: 0.9rem; resize: vertical;
  background: transparent; color: inherit; margin-bottom: var(--space-md);
  border: 1px solid var(--border-glass); border-radius: var(--radius-sm); outline: none;
}
.dialog textarea:focus { border-color: var(--accent-primary); }
.dialog-toggle { margin-bottom: var(--space-lg); font-size: 0.82rem; color: var(--text-muted); }
.dialog-toggle input { margin-right: 6px; }
.dialog-actions { display: flex; gap: var(--space-sm); justify-content: flex-end; }

/* ====== AI 摘要弹窗 ====== */
.summary-dialog {
  width: 500px;
  max-width: 90vw;
}

.summary-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-xl) 0;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 2px solid rgba(196, 163, 90, 0.15);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.summary-content {
  padding: var(--space-md) 0;
  font-size: 0.9rem;
  line-height: 1.8;
  color: var(--text-secondary);
  max-height: 400px;
  overflow-y: auto;
}

/* ====== 章节目录面板 ====== */
.chapter-panel {
  width: 360px;
}

.chapter-list {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.chapter-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

.chapter-item:hover {
  background: rgba(196, 163, 90, 0.08);
  border-left-color: var(--accent-primary);
  transform: translateX(4px);
}

.chapter-item.active {
  background: rgba(196, 163, 90, 0.12);
  border-left-color: var(--accent-primary);
}

.chapter-num {
  font-size: 0.75rem;
  color: var(--accent-primary);
  opacity: 0.5;
  min-width: 20px;
  font-weight: 600;
}

.chapter-item.active .chapter-num {
  opacity: 1;
}

.chapter-title {
  flex: 1;
  font-size: 0.88rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chapter-item.active .chapter-title {
  color: var(--text-primary);
  font-weight: 500;
}

.chapter-wc {
  font-size: 0.7rem;
  color: var(--text-muted);
  flex-shrink: 0;
}

/* ====== 浮动栏动画 ====== */
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
