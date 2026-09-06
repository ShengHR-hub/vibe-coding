<template>
  <div class="panel workshop-panel">
    <!-- 无作品：先建书 -->
    <template v-if="!workId">
      <p class="hint">先创建/打开一本书，才能在这里定主线、写大纲、设主角。</p>
      <input v-model="newTitle" class="ws-input" maxlength="50" placeholder="作品标题（可稍后改）" />
      <button class="btn btn-primary btn-full" :disabled="creating || !newTitle.trim()" @click="createBook">
        {{ creating ? '创建中…' : '创建这本书' }}
      </button>
    </template>

    <template v-else>
      <!-- 区块 1：灵感 -->
      <section class="ws-sec">
        <h3 class="ws-sec-title">灵感</h3>
        <p class="ws-sec-desc">把脑子里那个模糊的念头倒在这里；写主线时可以一键带入。</p>
        <textarea v-model="inspiration" class="ws-input ws-textarea" rows="3"
                  placeholder="一段话、几个词都行，不用完整…" />
        <div v-if="notes.length" class="ws-hint">
          <span class="ws-hint-label">我的灵感：</span>
          <button v-for="n in notes" :key="n.note_id" class="ws-chip"
                  @click="inspiration = inspiration ? inspiration + '\n' + n.content : n.content">
            {{ n.content.slice(0, 14) }}…
          </button>
        </div>
      </section>

      <!-- 区块 2：整体主线 -->
      <section class="ws-sec">
        <h3 class="ws-sec-title">整体主线</h3>
        <p class="ws-sec-desc">谁 + 想要什么 + 拦着什么 → 冲突弧。AI 可先打草稿，你再改。</p>
        <button class="btn btn-ghost btn-sm" :disabled="mainlineLoading" @click="genMainline">
          {{ mainlineLoading ? '生成中…' : 'AI 生成主线草稿' }}
        </button>
        <textarea v-model="mainline" class="ws-input ws-textarea" rows="6"
                  placeholder="整体主线（直接想好了也可以自己写）…" />
        <button class="btn btn-primary btn-full" :disabled="saving" @click="saveMainline">
          {{ saving ? '保存中…' : '保存主线（写入书立项）' }}
        </button>
      </section>

      <!-- 区块 3：卷级大纲 -->
      <section class="ws-sec">
        <h3 class="ws-sec-title">卷级大纲</h3>
        <p class="ws-sec-desc">先定卷的走向，章节边写边细化。保存后可在「大纲规划」面板继续。</p>
        <div class="ws-row">
          <input v-model.number="volumeCount" type="number" min="2" max="6" class="ws-input ws-num" />
          <span class="ws-hint-label">卷</span>
          <button class="btn btn-ghost btn-sm" :disabled="outlineLoading" @click="genOutline">
            {{ outlineLoading ? '生成中…' : 'AI 生成卷级大纲草稿' }}
          </button>
        </div>
        <textarea v-model="outlineText" class="ws-input ws-textarea" rows="7"
                  placeholder="分卷大纲：每卷目标 / 转折 / 结尾钩子（AI 结果可直接改）…" />
        <button class="btn btn-primary btn-full" :disabled="savingOutline" @click="saveOutline">
          {{ savingOutline ? '保存中…' : '保存到大纲树' }}
        </button>
        <p class="ws-hint-label" v-if="outlineParsed">保存时按「第X卷」自动整理进大纲树，之后在「大纲规划」里可细化章节。</p>
      </section>

      <!-- 区块 4：主角 -->
      <section class="ws-sec">
        <h3 class="ws-sec-title">主角</h3>
        <p class="ws-sec-desc">主角是心脏：名字 + 一句话人设。其他角色写到哪补到哪。</p>
        <input v-model="protagonist" class="ws-input" maxlength="100" placeholder="主角名字…" />
        <textarea v-model="protagonistDesc" class="ws-input ws-textarea" rows="3" maxlength="1000"
                  placeholder="一句话人设：他是谁、想要什么、怕什么…" />
        <button class="btn btn-primary btn-full" :disabled="savingProto" @click="saveProtagonist">
          {{ savingProto ? '保存中…' : '保存主角设定（写进设定库）' }}
        </button>
      </section>
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

const newTitle = ref('')
const creating = ref(false)
const notes = ref([])

const inspiration = ref('')
const mainline = ref('')
const outlineText = ref('')
const volumeCount = ref(3)
const protagonist = ref('')
const protagonistDesc = ref('')

const mainlineLoading = ref(false)
const outlineLoading = ref(false)
const saving = ref(false)
const savingOutline = ref(false)
const savingProto = ref(false)

const outlineParsed = computed(() => (outlineText.value || '').split('\n').some(l => /第?\s*\d+\s*卷|卷[一二三四五六七八九十]/.test(l)))

async function createBook() {
  if (creating.value) return
  creating.value = true
  const res = await api.post('/api/works', { title: newTitle.value.trim(), type: 'novel' })
  creating.value = false
  if (res.code === 0) {
    toast.success('作品已创建，去写第一章吧')
    await writingStore.openWork(res.data.work_id)
  } else toast.error(res.msg)
}

async function loadPlanning() {
  if (!workId.value) return
  const [p, n] = await Promise.all([
    api.get(`/api/plan/${workId.value}`),
    api.get('/api/notes'),
  ])
  if (p.code === 0 && p.data.plan) {
    mainline.value = p.data.plan.logline || ''
    outlineText.value = outlineToText(p.data.plan.outline || [])
  }
  if (n.code === 0) notes.value = (n.data.items || []).filter(i => i.kind === 'note')
}

/** 大纲树 → 可编辑文本（part.title 行 + 卷内子行） */
function outlineToText(tree) {
  const lines = []
  for (const part of tree || []) {
    lines.push(part.title || '')
    for (const ch of part.children || []) {
      lines.push((ch.title ? ch.title + '：' : '') + (ch.beats || ch.hook || ''))
    }
  }
  return lines.join('\n').trim()
}

/** 可编辑文本 → 大纲树（同 P6-B3） */
function parseOutlineTree(text) {
  const lines = (text || '').split('\n').map(l => l.trim()).filter(Boolean)
  const parts = []
  let cur = null
  for (const line of lines) {
    if (/第?\s*\d+\s*卷|卷[一二三四五六七八九十]/.test(line) && line.length <= 30) {
      cur = { kind: 'part', title: line.replace(/^[【\[]|[\】\]]$/g, '').slice(0, 60), children: [] }
      parts.push(cur)
    } else if (cur) {
      const sep = line.indexOf('：')
      const title = sep > 0 ? line.slice(0, sep).slice(0, 40) : ''
      const beats = sep > 0 ? line.slice(sep + 1) : line
      cur.children.push({ kind: 'chapter', title, beats: beats.slice(0, 200), hook: '' })
    } else {
      parts.push({ kind: 'part', title: line.slice(0, 60), children: [] })
    }
  }
  return parts.length ? parts : [{ kind: 'part', title: '全卷', children: [] }]
}

async function genMainline() {
  if (!inspiration.value.trim()) { toast.info('先写点灵感，AI 才好给你主线草稿'); return }
  mainlineLoading.value = true
  const res = await api.post('/api/write/mainline', { inspiration: inspiration.value.trim() })
  mainlineLoading.value = false
  if (res.code === 0) mainline.value = res.data.mainline
  else toast.error(res.msg)
}

async function saveMainline() {
  if (!workId.value || saving.value) return
  saving.value = true
  const res = await api.put(`/api/plan/${workId.value}`, { logline: mainline.value.trim() })
  saving.value = false
  if (res.code === 0) toast.success('主线已保存')
  else toast.error(res.msg)
}

async function genOutline() {
  if (!mainline.value.trim()) { toast.info('先有主线，再生成卷级大纲'); return }
  outlineLoading.value = true
  const res = await api.post('/api/write/volume-outline', { mainline: mainline.value.trim(), volume_count: volumeCount.value || 3 })
  outlineLoading.value = false
  if (res.code === 0) outlineText.value = res.data.outline
  else toast.error(res.msg)
}

async function saveOutline() {
  if (!workId.value || savingOutline.value) return
  savingOutline.value = true
  const res = await api.put(`/api/plan/${workId.value}`, { outline: parseOutlineTree(outlineText.value) })
  savingOutline.value = false
  if (res.code === 0) toast.success('已保存到大纲树')
  else toast.error(res.msg)
}

async function saveProtagonist() {
  if (!workId.value || savingProto.value) return
  if (!protagonist.value.trim()) { toast.info('先填主角名字'); return }
  savingProto.value = true
  const res = await api.post(`/api/works/${workId.value}/lore`, {
    title: `主角：${protagonist.value.trim()}`,
    content: protagonistDesc.value.trim() || '（暂无设定）',
  })
  savingProto.value = false
  if (res.code === 0) toast.success('主角设定已写进设定库')
  else toast.error(res.msg)
}

onMounted(async () => {
  await loadPlanning()
  if (!workId.value) return
  const lore = await api.get(`/api/works/${workId.value}/lore`)
  if (lore.code === 0) {
    const proto = (lore.data.items || []).find(i => (i.title || '').startsWith('主角：'))
    if (proto) {
      protagonist.value = (proto.title || '').replace(/^主角：/, '').trim()
      protagonistDesc.value = proto.content || ''
    }
  }
})

watch(workId, (v) => {
  if (v) {
    loadPlanning()
    api.get(`/api/works/${v}/lore`).then((lore) => {
      if (lore.code === 0) {
        const proto = (lore.data.items || []).find(i => (i.title || '').startsWith('主角：'))
        protagonist.value = proto ? (proto.title || '').replace(/^主角：/, '').trim() : ''
        protagonistDesc.value = proto ? proto.content || '' : ''
      }
    })
  }
})
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.ws-sec { padding: 12px 0 6px; }
.ws-sec + .ws-sec { border-top: 1px dashed rgba(196,163,90,0.2); }
.ws-sec-title { font-family: var(--font-serif); font-size: 0.95rem; margin: 0 0 4px; color: var(--text-primary); }
.ws-sec-desc { font-size: 0.76rem; color: var(--text-muted); line-height: 1.7; margin: 0 0 8px; }
.hint { font-size: 0.8rem; color: var(--text-muted); line-height: 1.8; }
.ws-input { background: var(--bg-glass); color: var(--text-primary); border: 1px solid rgba(196,163,90,0.2);
  border-radius: 8px; padding: 8px 12px; font-size: 0.85rem; width: 100%; box-sizing: border-box; margin: 4px 0 8px; }
.ws-textarea { resize: vertical; line-height: 1.75; }
.ws-num { width: 70px; }
.ws-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.ws-hint { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin: 2px 0 8px; }
.ws-hint-label { color: var(--text-muted); font-size: 0.72rem; }
.ws-chip { font-size: 0.72rem; padding: 3px 10px; border-radius: 999px; background: var(--bg-glass);
  border: 1px solid var(--border-glass); color: var(--text-secondary); cursor: pointer; }
.ws-chip:hover { border-color: var(--accent-primary); color: var(--accent-primary); }
</style>