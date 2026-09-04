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

        <button class="btn btn-primary btn-full" @click="gotoContinue">✍ 去续写本章</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../../api/index.js'
import { useWritingStore } from '../../stores/writing.js'

const writingStore = useWritingStore()

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
  if (p.code === 0) planOutline.value = p.data.plan?.outline || []
  if (l.code === 0) loreNames.value = (l.data.items || []).slice(0, 5).map(i => i.title)
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
</style>
