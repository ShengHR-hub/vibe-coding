<template>
  <div class="panel">
    <p v-if="!workId" class="hint">💡 保存作品后即可规划本书的三级大纲（卷 → 章），每章可写要点 beats 与钩子。</p>
    <template v-else>
      <div class="toolbar">
        <button class="btn btn-ghost btn-sm" @click="addPart">＋ 卷</button>
        <button class="btn btn-ghost btn-sm" @click="addChapterToLast">＋ 章节</button>
        <span class="flex"></span>
        <button class="btn btn-ghost btn-sm" :disabled="loading" @click="load">重载</button>
        <button class="btn btn-primary btn-sm" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存大纲' }}</button>
      </div>

      <div v-if="!outline.length" class="empty">
        还没有卷/章。点「＋ 卷」添加第一卷，再在卷内添加章节；
        每章填写【要点 Beats】与【钩子 Hook】，写作阶段 AI 会照着写。
      </div>

      <div v-for="(part, pi) in outline" :key="pi" class="part">
        <div class="part-head">
          <input v-model="part.title" class="part-title" :placeholder="`第 ${pi + 1} 卷 名称`" />
          <button class="mini" @click="addChapter(pi)">＋章</button>
          <button class="mini danger" @click="removePart(pi)">删卷</button>
        </div>
        <div v-for="(ch, ci) in part.children" :key="ci" class="chapter">
          <div class="ch-head">
            <input v-model="ch.title" class="ch-title" :placeholder="`${part.title || '卷'} 第 ${ci + 1} 章 标题`" />
            <button class="mini" @click="removeChapter(pi, ci)">删</button>
          </div>
          <textarea v-model="ch.beats" rows="2" placeholder="本章要点 Beats（核心事件 200-500 字要点）"></textarea>
          <input v-model="ch.hook" class="ch-hook" placeholder="本章钩子 Hook（章尾悬念 / 承上启下）" />
        </div>
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
const outline = ref([])
const loading = ref(false)
const saving = ref(false)

function emptyChapter() { return { kind: 'chapter', title: '', beats: '', hook: '' } }
function emptyPart() { return { kind: 'part', title: '', children: [] } }

async function load() {
  if (!workId.value) return
  loading.value = true
  const res = await api.get(`/api/plan/${workId.value}`)
  if (res.code === 0 && res.data.plan?.outline?.length) {
    outline.value = res.data.plan.outline
  } else {
    outline.value = []
  }
  loading.value = false
}

function addPart() { outline.value.push(emptyPart()) }
function addChapterToLast() {
  if (!outline.value.length) outline.value.push(emptyPart())
  addChapter(outline.value.length - 1)
}
function addChapter(pi) {
  if (!outline.value[pi].children) outline.value[pi].children = []
  outline.value[pi].children.push(emptyChapter())
}
function removePart(pi) { outline.value.splice(pi, 1) }
function removeChapter(pi, ci) { outline.value[pi].children.splice(ci, 1) }

async function save() {
  if (!workId.value) return
  saving.value = true
  const res = await api.put(`/api/plan/${workId.value}`, { outline: outline.value })
  saving.value = false
  if (res.code === 0) toast.success('大纲已保存（任务卡/续写将按此执行）')
  else toast.error(res.msg)
}

onMounted(load)
watch(workId, () => load())
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.hint { font-size: 0.8rem; color: var(--text-muted); line-height: 1.8; }
.toolbar { display: flex; gap: 6px; align-items: center; margin-bottom: 10px; flex-wrap: wrap; }
.flex { flex: 1; }
.empty { font-size: 0.8rem; color: var(--text-muted); line-height: 1.8; border: 1px dashed rgba(196,163,90,0.2); padding: 12px; border-radius: var(--radius-sm); }
.part { margin-bottom: 12px; border: 1px solid rgba(196,163,90,0.12); border-radius: var(--radius-md); padding: 8px 10px; }
.part-head { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.part-title { flex: 1; font-weight: 600; font-size: 0.9rem; }
.chapter { margin: 6px 0 8px 6px; padding-left: 8px; border-left: 2px solid rgba(196,163,90,0.18); display: flex; flex-direction: column; gap: 4px; }
.ch-head { display: flex; gap: 6px; align-items: center; }
.ch-title { flex: 1; font-size: 0.85rem; }
.mini { font-size: 0.7rem; padding: 2px 8px; border-radius: var(--radius-sm); background: rgba(196,163,90,0.08); border: 1px solid rgba(196,163,90,0.2); color: var(--accent-primary); cursor: pointer; }
.mini.danger { color: #e0716b; }
.panel input, .panel textarea {
  width: 100%; box-sizing: border-box; padding: 6px 8px; font-size: 0.84rem;
  border-radius: var(--radius-sm); background: var(--bg-glass);
  border: 1px solid var(--border-glass); color: var(--text-primary);
}
.ch-hook { font-size: 0.8rem; color: var(--text-secondary); }
</style>
