<template>
  <div class="panel">
    <p class="hint" v-if="!workId">💡 保存作品后即可在这里收尾交付：导出整书。</p>
    <template v-else>
      <div class="checklist">
        <div class="cli" :class="{ done: hasBlueprint }"><span>{{ hasBlueprint ? '✓' : '○' }}</span> 已立项（一句话命题/读者/字数）</div>
        <div class="cli" :class="{ done: hasOutline }"><span>{{ hasOutline ? '✓' : '○' }}</span> 大纲已就位（{{ outlineCount }} 章）</div>
        <div class="cli" :class="{ done: allDrafted }"><span>{{ allDrafted ? '✓' : '○' }}</span> 正文已写（{{ draftChapters }}/{{ chapterCount }} 章 ≥200 字）</div>
        <div class="cli" :class="{ done: allFormal }"><span>{{ allFormal ? '✓' : '○' }}</span> 全部标为正式稿（{{ formalChapters }}/{{ chapterCount }} 章）</div>
        <div class="cli" :class="{ done: noTodo }"><span>{{ noTodo ? '✓' : '○' }}</span> [TODO] 已清零（{{ todoCount }} 处）</div>
      </div>

      <button class="btn btn-primary btn-full" @click="exportBook" :disabled="exporting">
        {{ exporting ? '导出中…' : '⬇ 一键导出正式稿' }}
      </button>
      <p class="formal-hint" v-if="formalChapters < chapterCount">仅导出已标为「正式稿」的章节（当前 {{ formalChapters }}/{{ chapterCount }} 章），草稿不进入交付稿。</p>

      <div class="later">
        <p class="b-label">交付增强（下一阶段）</p>
        <p class="later-text">结构审校报告 · 逐章润色队列 · 前言/后记/封面文案 AI 生成 · 出版规格检查（字数区间）</p>
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
const plan = ref(null)
const exporting = ref(false)

const TODO_RE = /\[(TODO|待补)\s*[:：]?/g

const hasBlueprint = computed(() => !!plan.value?.logline)
const hasOutline = computed(() => flatChapterCount(plan.value?.outline) > 0)
const outlineCount = computed(() => flatChapterCount(plan.value?.outline))
const chapterCount = computed(() => writingStore.chapters.length)
const draftChapters = computed(() => writingStore.chapters.filter(c => (c.content || '').replace(/\s/g, '').length >= 200).length)
const allDrafted = computed(() => chapterCount.value > 0 && draftChapters.value === chapterCount.value)

// P6-C1：正式稿统计 + 全部正式判定（交付只导正式稿）
const formalChapters = computed(() => writingStore.chapters.filter(c => c.status === 'formal').length)
const allFormal = computed(() => chapterCount.value > 0 && formalChapters.value === chapterCount.value)
const todoCount = computed(() => {
  let n = 0
  for (const c of writingStore.chapters) {
    const body = c.content || ''
    TODO_RE.lastIndex = 0
    while (TODO_RE.exec(body)) n += 1
  }
  return n
})
const noTodo = computed(() => todoCount.value === 0)

function flatChapterCount(nodes) {
  let n = 0
  for (const node of nodes || []) {
    if (node.kind === 'chapter') n += 1
    else n += flatChapterCount(node.children)
  }
  return n
}

async function load() {
  if (!workId.value) return
  const res = await api.get(`/api/plan/${workId.value}`)
  if (res.code === 0) plan.value = res.data.plan || null
}

async function exportBook() {
  exporting.value = true
  // P6-C1：交付只导正式稿（草稿章节不进入交付）
  const res = await api.download(`/api/works/${workId.value}/export?formal=1`, '作品-正式稿.txt')
  exporting.value = false
  if (res.code !== 0 && res.msg) toast.error(res.msg)
}

onMounted(load)
watch(workId, () => load())
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.hint { font-size: 0.8rem; color: var(--text-muted); line-height: 1.8; }
.checklist { display: flex; flex-direction: column; gap: 6px; margin: 4px 0 14px; }
.cli { font-size: 0.85rem; color: var(--text-muted); }
.cli.done { color: var(--text-secondary); }
.cli span { margin-right: 6px; color: var(--accent-primary); }
.formal-hint {
  font-size: 0.76rem; color: var(--text-muted); line-height: 1.7;
  margin: 8px 0 0;
}
.later { margin-top: 14px; border-top: 1px dashed rgba(196,163,90,0.15); padding-top: 10px; }
.b-label { font-size: 0.74rem; color: var(--text-muted); margin: 0 0 4px; }
.later-text { font-size: 0.8rem; color: var(--text-secondary); line-height: 1.8; margin: 0; }
</style>
