<template>
  <div class="panel">
    <p class="hint" v-if="!workId">💡 保存作品后，这里对照「大纲 vs 正文」做第一轮结构审校。</p>
    <template v-else>
      <div class="stat-row">
        <div class="stat"><b>{{ planChapterCount }}</b><span>大纲章数</span></div>
        <div class="stat"><b>{{ chapterCount }}</b><span>正文章数</span></div>
        <div class="stat"><b>{{ draftCount }}</b><span>已写章节</span></div>
        <div class="stat"><b>{{ shortCount }}</b><span>过短章节</span></div>
      </div>

      <div v-if="problems.length" class="problem-list">
        <div v-for="(p, i) in problems" :key="i" class="problem">
          <span class="p-mark">{{ p.mark }}</span>
          <span class="p-text">{{ p.text }}</span>
        </div>
      </div>
      <p v-else class="ok">✓ 目前没有明显结构问题（大纲数量与正文基本一致、无过短章节）</p>

      <div class="ai-block">
        <button class="btn btn-primary btn-sm" @click="aiReview" :disabled="reviewing">
          {{ reviewing ? '审校中…' : '⚡ 生成 AI 结构审校报告' }}
        </button>
        <p v-if="reportErr" class="err">{{ reportErr }}</p>
        <div v-if="report" class="report" v-html="renderParagraphBold(report)"></div>
      </div>

      <div class="check-block">
        <p class="b-label">第一轮 · 结构审校自查清单（对照大纲逐项看）</p>
        <ul class="check-list">
          <li>章节顺序是否最合理、可否合并/调换</li>
          <li>是否有冗余、跑题或与大纲脱节的章节</li>
          <li>各章篇幅是否平衡（过长拆、过短补）</li>
          <li>伏笔与呼应：前面埋的线索后面是否兑现</li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../../api/index.js'
import { useWritingStore } from '../../stores/writing.js'
import { useToast } from '../../composables/useToast.js'
import { renderParagraphBold } from '../../utils/render.js'

const writingStore = useWritingStore()
const toast = useToast()
const workId = computed(() => writingStore.currentWorkId)
const planOutline = ref([])
const report = ref('')
const reviewing = ref(false)
const reportErr = ref('')

function flatChapters(nodes, out = []) {
  for (const n of nodes || []) {
    if (n.kind === 'chapter') out.push(n)
    else if (n.children) flatChapters(n.children, out)
  }
  return out
}

const chapterCount = computed(() => writingStore.chapters.length)
const planChapterCount = computed(() => flatChapters(planOutline.value).length)

const draftCount = computed(() => writingStore.chapters.filter(c => (c.content || '').replace(/\s/g, '').length > 200).length)

const shortList = computed(() => writingStore.chapters
  .filter(c => (c.content || '').replace(/\s/g, '').length > 0 && (c.content || '').replace(/\s/g, '').length < 200))

const shortCount = computed(() => shortList.value.length)

const problems = computed(() => {
  const out = []
  if (planChapterCount.value && Math.abs(planChapterCount.value - chapterCount.value) >= 2) {
    out.push({ mark: '结构', text: `大纲 ${planChapterCount.value} 章，正文 ${chapterCount.value} 章，数量偏差较大，检查是否有遗漏或多余章节。` })
  }
  for (const s of shortList.value) {
    out.push({ mark: '篇幅', text: `「${s.title || '第' + s.chapter_no + '章'}」正文不足 200 字，可能只是骨架。` })
  }
  return out
})

async function aiReview() {
  if (!workId.value) return
  reviewing.value = true
  reportErr.value = ''
  const res = await api.post('/api/write/struct', { work_id: workId.value })
  reviewing.value = false
  if (res.code === 0) {
    report.value = res.data.report
  } else {
    reportErr.value = res.msg || '生成失败'
  }
}

async function load() {
  if (!workId.value) return
  const res = await api.get(`/api/plan/${workId.value}`)
  if (res.code === 0) planOutline.value = res.data.plan?.outline || []
}

onMounted(load)
watch([workId, () => writingStore.activeChapterId], () => load())
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.hint { font-size: 0.8rem; color: var(--text-muted); line-height: 1.8; }
.stat-row { display: flex; justify-content: space-between; margin: 6px 0 12px; }
.stat { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.stat b { font-size: 1.2rem; color: var(--accent-primary); }
.stat span { font-size: 0.68rem; color: var(--text-muted); }
.problem-list { display: flex; flex-direction: column; gap: 6px; }
.problem { display: flex; gap: 8px; padding: 8px 10px; background: rgba(224,113,107,0.06); border: 1px solid rgba(224,113,107,0.2); border-radius: var(--radius-sm); }
.p-mark { color: var(--accent-red); font-weight: 700; font-size: 0.78rem; flex-shrink: 0; }
.p-text { font-size: 0.84rem; color: var(--text-secondary); line-height: 1.6; }
.ok { font-size: 0.86rem; color: var(--accent-green); margin: 6px 0; }
.ai-block { margin: 12px 0 4px; }
.report { margin-top: 10px; padding: 10px 12px; background: rgba(196,163,90,0.05); border: 1px solid rgba(196,163,90,0.12); border-radius: var(--radius-md); font-size: 0.86rem; color: var(--text-secondary); line-height: 1.85; }
.err { font-size: 0.8rem; color: var(--accent-red); margin-top: 6px; }
.check-block { margin-top: 14px; }
.b-label { font-size: 0.74rem; color: var(--text-muted); margin: 0 0 6px; }
.check-list { margin: 0; padding-left: 1.2rem; font-size: 0.84rem; color: var(--text-secondary); line-height: 2; }
</style>
