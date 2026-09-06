<template>
  <div class="panel">
    <template v-if="!workId">
      <p class="hint">💡 保存作品后，这里会显示「本章任务卡」：本章目标、前情、相关设定。</p>
    </template>
    <template v-else>
      <div class="card task-card">
        <div class="card-head">
          <span class="badge">本章任务卡</span>
          <span class="ch-title">{{ chapterTitle || '当前章节' }}</span>
        </div>

        <template v-if="chapterTask">
          <div class="block">
            <p class="b-label">本章要点 / Beats</p>
            <p class="b-text">{{ chapterTask.beats || '（未填写要点）' }}</p>
          </div>
          <div class="block">
            <p class="b-label">本章钩子 / Hook</p>
            <p class="b-text">{{ chapterTask.hook || '（未填写钩子）' }}</p>
          </div>
        </template>
        <p v-else class="hint">
          大纲里还没有本章的 beats/钩子。可先到「③ 按蓝图续写」直接动笔，
          或在「① 三级大纲」完善后再回来，AI 会按本章任务续写。
        </p>

        <div class="block" v-if="prevTail">
          <p class="b-label">前情提要（上一章末尾）</p>
          <p class="b-text prev">{{ prevTail }}…</p>
        </div>

        <div class="block" v-if="loreNames.length">
          <p class="b-label">相关设定（可注入）</p>
          <p class="b-text">{{ loreNames.join(' · ') }}</p>
        </div>

        <div class="ai-zone">
          <div class="ai-zone-head">
            <span class="ai-zone-label">AI 搭把手</span>
            <button class="btn btn-ghost btn-sm" @click="genPlot" :disabled="plotLoading">{{ plotLoading ? '生成中…' : '生成本章剧情' }}</button>
            <button class="btn btn-ghost btn-sm" @click="extractPoints" :disabled="extractLoading || !writingStore.content.trim()">{{ extractLoading ? '提取中…' : '写完提取要点' }}</button>
          </div>

          <div v-if="aiResult" class="ai-result">
            <p class="ai-result-text">{{ aiResult }}</p>
            <div class="ai-result-actions">
              <button v-if="aiMode === 'extract'" class="btn btn-primary btn-sm" @click="saveBeats" :disabled="savingBeats">{{ savingBeats ? '保存中…' : '保存为本章 Beats' }}</button>
              <button class="btn btn-ghost btn-sm" @click="aiResult = ''">关闭</button>
            </div>
          </div>
        </div>

        <button class="btn btn-primary btn-full" @click="gotoContinue">✍ 去续写本章</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../../api/index.js'
import { useWritingStore } from '../../stores/writing.js'
import { useToast } from '../../composables/useToast.js'

const writingStore = useWritingStore()
const toast = useToast()

const workId = computed(() => writingStore.currentWorkId)
const planOutline = ref([])
const loreNames = ref([])

const chapterTitle = computed(() => writingStore.getActiveChapterTitle() || `第${writingStore.activeChapterId ? '' : ''}章`)

const chapterNo = computed(() => {
  const ch = writingStore.chapters.find(c => c.chapter_id === writingStore.activeChapterId)
  return ch ? ch.chapter_no : 0
})

function flatChapters(nodes, out = []) {
  for (const n of nodes || []) {
    if (n.kind === 'chapter') out.push(n)
    else if (n.children) flatChapters(n.children, out)
  }
  return out
}

const chapterTask = computed(() => {
  const list = flatChapters(planOutline.value)
  return list[chapterNo.value - 1] || null
})

const prevTail = computed(() => {
  const chs = writingStore.chapters
  const idx = chs.findIndex(c => c.chapter_id === writingStore.activeChapterId)
  if (idx <= 0) return ''
  const prev = chs[idx - 1]?.content || ''
  return prev.replace(/\s+/g, ' ').slice(-180)
})

async function load() {
  if (!workId.value) return
  const [p, l] = await Promise.all([
    api.get(`/api/plan/${workId.value}`),
    api.get(`/api/works/${workId.value}/lore`),
  ])
  if (p.code === 0) {
    planOutline.value = p.data.plan?.outline || []
    planMainline.value = p.data.plan?.logline || ''
  }
  if (l.code === 0) loreNames.value = (l.data.items || []).slice(0, 5).map(i => i.title)
}

// ---- P6-B4：任务卡 AI 搭把手 ----
const plotLoading = ref(false)
const extractLoading = ref(false)
const savingBeats = ref(false)
const aiResult = ref('')
const aiMode = ref('')  // 'plot' | 'extract'
const planMainline = ref('')

async function genPlot() {
  if (!workId.value) return
  plotLoading.value = true
  const res = await api.post('/api/write/chapter-plot', {
    work_id: workId.value,
    inspiration: '',
    mainline: planMainline.value,
    chapter_no: chapterNo.value || 0,
  })
  plotLoading.value = false
  if (res.code === 0) { aiMode.value = 'plot'; aiResult.value = res.data.plot }
  else { toast.error(res.msg) }
}

async function extractPoints() {
  if (!workId.value) return
  const content = writingStore.content.trim()
  if (!content) return
  extractLoading.value = true
  const res = await api.post('/api/write/extract-points', {
    content,
    chapter_title: writingStore.getActiveChapterTitle(),
  })
  extractLoading.value = false
  if (res.code === 0) { aiMode.value = 'extract'; aiResult.value = res.data.points }
  else { toast.error(res.msg) }
}

/** 把提取结果整段存为本章 Beats（写回 outline 树对应章节点） */
async function saveBeats() {
  if (!aiResult.value.trim()) return
  const idx = chapterNo.value - 1
  const list = flatChapters(planOutline.value)
  if (idx < 0 || idx >= list.length) { toast.info('大纲里还没有本章节点，先在「① 三级大纲」加章节'); return }
  const target = list[idx]
  target.beats = aiResult.value.trim()
  savingBeats.value = true
  const res = await api.put(`/api/plan/${workId.value}`, { outline: planOutline.value })
  savingBeats.value = false
  if (res.code === 0) { toast.success('已保存为本章 Beats'); aiResult.value = ''; load() }
  else toast.error(res.msg)
}

function gotoContinue() {
  window.dispatchEvent(new CustomEvent('inkstone:goto-tool', { detail: { tool: 'continue' } }))
}

onMounted(load)
watch([workId, () => writingStore.activeChapterId], () => load())
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.hint { font-size: 0.8rem; color: var(--text-muted); line-height: 1.8; }
.card { padding: 12px; border: 1px solid rgba(196,163,90,0.12); border-radius: var(--radius-md); }
.card-head { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.badge { font-size: 0.7rem; color: var(--accent-primary); background: rgba(196,163,90,0.12); padding: 2px 10px; border-radius: 999px; }
.ch-title { font-family: var(--font-serif); font-weight: 600; font-size: 0.95rem; }
.block { margin: 8px 0; }
.b-label { font-size: 0.74rem; color: var(--text-muted); margin: 0 0 3px; }
.b-text { font-size: 0.85rem; color: var(--text-secondary); line-height: 1.75; margin: 0; white-space: pre-wrap; }
.b-text.prev { color: var(--text-muted); }

.ai-zone { margin-top: 10px; padding-top: 10px; border-top: 1px dashed rgba(196,163,90,0.25); }
.ai-zone-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.ai-zone-label { font-size: 0.74rem; color: var(--accent-primary); }
.ai-result { padding: 10px 12px; border-radius: 10px; background: rgba(196,163,90,0.08); border: 1px solid rgba(196,163,90,0.25); }
.ai-result-text { font-size: 0.82rem; line-height: 1.8; color: var(--text-secondary); margin: 0 0 8px; white-space: pre-wrap; }
.ai-result-actions { display: flex; justify-content: flex-end; gap: 8px; }
</style>
