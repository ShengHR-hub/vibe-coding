<template>
  <Teleport to="body">
    <!-- 划词快捷操作工具栏（像输入法候选框一样浮在选区旁） -->
    <transition name="sp-pop">
      <div
        v-if="menuVisible"
        class="sp-menu glass-card"
        :style="{ left: pos.x + 'px', top: pos.y + 'px' }"
        @mousedown.prevent
      >
        <button class="sp-btn" :title="'润色选中内容'" @click="runAction('polish')">
          <span class="sp-ico">♦</span>润色
        </button>
        <button class="sp-btn" :title="'检查错别字与病句'" @click="runAction('fix')">
          <span class="sp-ico">✓</span>查错
        </button>
        <button class="sp-btn" :title="'翻译 / 解释这句'" @click="runAction('interpret')">
          <span class="sp-ico">文</span>翻译
        </button>
        <button class="sp-btn" :title="'按这句的意境找更多句子'" @click="runAction('find')">
          <span class="sp-ico">✦</span>找句
        </button>
      </div>
    </transition>

    <!-- 结果卡片 -->
    <transition name="sp-pop">
      <div
        v-if="resultVisible"
        class="sp-result glass-card"
        :style="{ left: resultPos.x + 'px', top: resultPos.y + 'px' }"
        @mousedown.prevent
      >
        <div class="sp-result-head">
          <span class="sp-result-title">{{ resultTitle }}</span>
          <button class="sp-close" @click="closeResult">✕</button>
        </div>

        <!-- 加载骨架 -->
        <div v-if="loading" class="sp-loading">
          <span class="sp-loading-dots">AI 思考中<span class="dots"></span></span>
        </div>

        <template v-else-if="error">
          <p class="sp-error">{{ error }}</p>
        </template>

        <!-- 查错：结构化列表 -->
        <template v-else-if="action === 'fix' && fixes.length">
          <div class="sp-fix-list">
            <div v-for="(f, i) in fixes" :key="i" class="sp-fix-item">
              <div class="sp-fix-line">
                <span class="sp-fix-del">{{ f.original }}</span>
                <span class="sp-fix-arrow">→</span>
                <span class="sp-fix-ins">{{ f.suggestion }}</span>
              </div>
              <p class="sp-fix-reason">{{ f.reason || '建议修改' }}</p>
            </div>
          </div>
          <button class="sp-apply" @click="applyFixAll">全部替换</button>
        </template>

        <!-- 润色 / 翻译 / AI找句意图：文本结果 -->
        <template v-else>
          <p class="sp-text" v-if="resultText">{{ resultText }}</p>
        </template>

        <div class="sp-result-actions" v-if="!loading && !error && (resultText || fixes.length)">
          <button class="sp-ghost" @click="copyResult">复制</button>
          <button
            v-if="action === 'polish' || action === 'fix'"
            class="sp-apply"
            @click="applyToEditor"
          >替换选中文字</button>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { api } from '../api/index.js'

const props = defineProps({
  editor: { type: Object, default: null }, // textarea DOM 元素
})
const emit = defineEmits(['find'])

// ---- 选区与定位 ----
const menuVisible = ref(false)
const resultVisible = ref(false)
const pos = ref({ x: 0, y: 0 })
const resultPos = ref({ x: 0, y: 0 })
let selStart = 0
let selEnd = 0
let selText = ''

// ---- 动作状态 ----
const action = ref('')
const loading = ref(false)
const error = ref('')
const resultText = ref('')
const fixes = ref([])

const resultTitle = computed(() => ({
  polish: '润色结果',
  fix: '检查结果',
  interpret: '翻译 / 解释',
  find: '按意境找句',
})[action.value] || 'AI 结果')

function selectedText() {
  const el = props.editor
  if (!el) return ''
  return el.value.substring(el.selectionStart, el.selectionEnd).trim()
}

function getRangeRect() {
  const el = props.editor
  if (!el) return null
  const r = document.createRange()
  r.setStart(el, 0)
  r.setEnd(el, el.selectionEnd)
  const rects = r.getClientRects()
  if (!rects.length) return null
  return rects[rects.length - 1]
}

function updateMenu() {
  const el = props.editor
  if (!el) return
  const text = selectedText()
  const len = text.replace(/\s/g, '').length
  // 2-2000 字才弹菜单
  if (len < 2 || len > 2000) {
    menuVisible.value = false
    resultVisible.value = false
    return
  }
  selStart = el.selectionStart
  selEnd = el.selectionEnd
  selText = text
  const rect = getRangeRect()
  if (!rect) return
  // 浮在选区下方
  const pad = 8
  let x = rect.left
  let y = rect.bottom + pad
  if (y + 44 > window.innerHeight) y = rect.top - 36 - pad
  if (x + 300 > window.innerWidth) x = Math.max(8, window.innerWidth - 300)
  pos.value = { x: Math.max(8, x), y: Math.max(8, y) }
  menuVisible.value = true
}

// ---- 动作执行 ----
async function runAction(kind) {
  if (!selText) return
  action.value = kind
  loading.value = true
  error.value = ''
  resultText.value = ''
  fixes.value = []
  resultVisible.value = true
  menuVisible.value = false
  // 结果卡片定位在选区上方偏右，避免与菜单重叠
  const rect = getRangeRect()
  let x = rect ? rect.left : pos.value.x
  let y = rect ? rect.top - 20 : pos.value.y
  if (y < 8) y = 8
  if (x + 380 > window.innerWidth) x = Math.max(8, window.innerWidth - 380)
  resultPos.value = { x, y }

  if (kind === 'polish') {
    const res = await api.post('/api/write/polish', { text: selText, mode: '流畅' })
    if (res.code === 0) resultText.value = res.data.polished
    else error.value = res.msg
  } else if (kind === 'fix') {
    const res = await api.post('/api/write/fix', { text: selText })
    if (res.code === 0) fixes.value = res.data.fixes || []
    else error.value = res.msg
    if (!fixes.value.length) resultText.value = '没有发现明显的错别字或病句 ✓'
  } else if (kind === 'interpret') {
    const res = await api.post('/api/write/interpret', { text: selText })
    if (res.code === 0) resultText.value = res.data.explanation
    else error.value = res.msg
  } else if (kind === 'find') {
    loading.value = false
    resultVisible.value = false
    emit('find', selText)
    return
  }
  loading.value = false
}

// ---- 结果应用 ----
function applyToEditor() {
  const el = props.editor
  if (!el) return
  let replaceText = ''
  if (action.value === 'polish') replaceText = resultText.value
  if (action.value === 'fix') replaceText = selText
  // fix：逐个替换
  for (const f of fixes.value) {
    replaceText = replaceText.split(f.original).join(f.suggestion)
  }
  if (!replaceText) return
  const start = Math.min(selStart, el.value.length)
  const end = Math.min(selEnd, el.value.length)
  el.setRangeText(replaceText, start, end, 'end')
  el.dispatchEvent(new Event('input', { bubbles: true }))
  closeResult()
  el.focus()
}

function applyFixAll() {
  applyToEditor()
}

function copyResult() {
  const text = action.value === 'fix'
    ? fixes.value.map(f => `${f.original} → ${f.suggestion}`).join('；')
    : resultText.value
  navigator.clipboard?.writeText(text || '').catch(() => {})
}

function closeResult() {
  resultVisible.value = false
  action.value = ''
}

// ---- 全局监听 ----
function onDocMouseup() {
  const el = props.editor
  if (!el) return
  const sel = document.getSelection()
  // 编辑器内选中才显示
  const inEditor = sel && sel.anchorNode && el.contains(sel.anchorNode)
  if (inEditor) {
    updateMenu()
  } else {
    // 点击弹窗/结果卡片内部不隐藏
    menuVisible.value = false
  }
}

function onDocScroll() {
  // 滚动时刷新位置
  if (menuVisible.value) updateMenu()
}

function onEditorKeyup(e) {
  // 键盘选区（shift+方向键）也触发
  if (e.shiftKey || e.key === 'ArrowLeft' || e.key === 'ArrowRight') updateMenu()
  // Esc 关闭
  if (e.key === 'Escape') {
    menuVisible.value = false
    resultVisible.value = false
  }
}

onMounted(() => {
  window.addEventListener('mouseup', onDocMouseup)
  window.addEventListener('scroll', onDocScroll, true)
  props.editor?.addEventListener('keyup', onEditorKeyup)
})
onUnmounted(() => {
  window.removeEventListener('mouseup', onDocMouseup)
  window.removeEventListener('scroll', onDocScroll, true)
  props.editor?.removeEventListener('keyup', onEditorKeyup)
})
</script>

<style scoped>
.sp-menu {
  position: fixed; z-index: 500;
  display: flex; gap: 4px; padding: 6px;
  border-radius: 12px;
  box-shadow: var(--shadow-lg);
}
.sp-btn {
  display: flex; align-items: center; gap: 4px;
  padding: 6px 10px; font-size: 0.8rem;
  border-radius: 8px; background: var(--bg-glass);
  border: 1px solid transparent; color: var(--text-primary);
  cursor: pointer; white-space: nowrap; transition: all 0.15s;
}
.sp-btn:hover { background: rgba(196, 163, 90, 0.15); border-color: rgba(196, 163, 90, 0.4); }
.sp-ico { color: var(--accent-primary); font-size: 0.78rem; }

.sp-result {
  position: fixed; z-index: 501;
  width: min(380px, 92vw);
  padding: 12px 14px;
  border-radius: 14px;
  box-shadow: var(--shadow-lg);
  display: flex; flex-direction: column; gap: 10px;
}
.sp-result-head { display: flex; justify-content: space-between; align-items: center; }
.sp-result-title { font-family: var(--font-serif); font-size: 0.9rem; color: var(--accent-secondary); }
.sp-close {
  background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 0.9rem;
}
.sp-close:hover { color: var(--text-primary); }

.sp-loading { padding: 10px 0; text-align: center; }
.sp-loading-dots { color: var(--text-muted); font-size: 0.85rem; }
.sp-error { color: var(--accent-red); font-size: 0.85rem; margin: 0; }
.sp-text {
  font-size: 0.9rem; line-height: 1.8; color: var(--text-primary);
  white-space: pre-wrap; word-break: break-word; margin: 0;
  max-height: 260px; overflow-y: auto;
}

.sp-fix-list { display: flex; flex-direction: column; gap: 8px; max-height: 240px; overflow-y: auto; }
.sp-fix-item {
  padding: 7px 10px; border-radius: 8px; background: var(--bg-glass);
  border: 1px solid var(--border-glass);
}
.sp-fix-line { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.sp-fix-del { color: var(--accent-red); text-decoration: line-through; font-size: 0.86rem; }
.sp-fix-arrow { color: var(--text-muted); font-size: 0.8rem; }
.sp-fix-ins { color: var(--accent-green); font-size: 0.86rem; }
.sp-fix-reason { font-size: 0.74rem; color: var(--text-muted); margin: 4px 0 0; }

.sp-result-actions { display: flex; justify-content: flex-end; gap: 8px; }
.sp-apply {
  padding: 7px 14px; font-size: 0.82rem; border-radius: 8px;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  color: #1a1a2e; font-weight: 600; border: none; cursor: pointer;
}
.sp-ghost {
  padding: 7px 14px; font-size: 0.82rem; border-radius: 8px;
  background: var(--bg-glass); border: 1px solid var(--border-glass);
  color: var(--text-secondary); cursor: pointer;
}
.sp-ghost:hover { color: var(--text-primary); }

.sp-pop-enter-active, .sp-pop-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.sp-pop-enter-from, .sp-pop-leave-to { opacity: 0; transform: translateY(-4px); }
</style>