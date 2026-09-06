<template>
  <div class="page-container">
    <section class="ws-hero glass-card">
      <p class="ws-kicker">CREATION WORKSHOP · 创作工坊</p>
      <h1 class="ws-title">一本书，从接住一个念头开始</h1>
      <p class="ws-desc">跟着走五步：灵感 → 主线 → 大纲 → 主角 → 动笔。每一步 AI 都可以搭把手，也可以全自己写。</p>
      <div class="ws-steps">
        <div v-for="s in steps" :key="s.key" class="ws-step" :class="{ done: step > s.no, active: step === s.no }">
          <span class="ws-step-no">{{ step > s.no ? '✓' : s.no }}</span>
          <span class="ws-step-label">{{ s.label }}</span>
        </div>
      </div>
    </section>

    <section class="ws-body glass-card">
      <!-- 步 0：灵感 -->
      <div v-if="step === 0" class="ws-pane">
        <h2 class="ws-pane-title">0 · 接住你的念头</h2>
        <p class="ws-pane-desc">别管完不完整，把心里那个想写的东西倒出来。一段话、几个词都行。</p>
        <textarea v-model="d.inspiration" class="ws-input ws-textarea" rows="6"
                  placeholder="例：一个女孩在雨夜捡到一只会说话的猫，猫说：'我能帮你实现愿望，但每实现一个，你会忘记一件重要的事。'" />
        <div class="ws-hint" v-if="notes.length">
          <span class="ws-hint-label">从「我的灵感」里带入：</span>
          <button v-for="n in notes" :key="n.note_id" class="ws-chip"
                  @click="d.inspiration = d.inspiration ? d.inspiration + '\n' + n.content : n.content">
            {{ n.content.slice(0, 18) }}…
          </button>
        </div>
        <div class="ws-nav">
          <button class="btn btn-primary" :disabled="!d.inspiration.trim()" @click="next">下一步 →</button>
        </div>
      </div>

      <!-- 步 1：主线 -->
      <div v-else-if="step === 1" class="ws-pane">
        <h2 class="ws-pane-title">1 · 定整体主线</h2>
        <p class="ws-pane-desc">让 AI 把灵感整合成一条主线（谁 + 想要什么 + 拦着什么），或自己写。</p>
        <button class="btn btn-primary btn-sm" :disabled="mainlineLoading || !d.inspiration.trim()" @click="genMainline">
          {{ mainlineLoading ? 'AI 思考中…' : (d.mainline ? '⟳ 重新生成主线' : '✨ AI 生成主线') }}
        </button>
        <textarea v-model="d.mainline" class="ws-input ws-textarea" rows="7"
                  placeholder="整体主线：核心命题 / 主角 / 目标 / 障碍 / 冲突弧…" />
        <div class="ws-nav">
          <button class="btn btn-ghost" @click="step = 0">← 上一步</button>
          <button class="btn btn-primary" :disabled="!d.mainline.trim()" @click="next">下一步 →</button>
        </div>
      </div>

      <!-- 步 2：大纲 -->
      <div v-else-if="step === 2" class="ws-pane">
        <h2 class="ws-pane-title">2 · 卷级大纲草稿</h2>
        <p class="ws-pane-desc">先定卷的走向（卷级故事曲线），章节到时边写边细化，别把大纲写死。</p>
        <div class="ws-row">
          <input v-model.number="volumeCount" type="number" min="2" max="6" class="ws-input ws-num" />
          <span class="ws-hint-label">卷</span>
          <button class="btn btn-primary btn-sm" :disabled="outlineLoading || !d.mainline.trim()" @click="genOutline">
            {{ outlineLoading ? 'AI 思考中…' : (d.outlineText ? '⟳ 重新生成本大纲' : '✨ AI 生成卷级大纲') }}
          </button>
        </div>
        <textarea v-model="d.outlineText" class="ws-input ws-textarea" rows="9"
                  placeholder="分卷大纲：每卷的目标 / 转折 / 结尾钩子…（可直接编辑 AI 结果）" />
        <p class="ws-hint-label" v-if="outlineParsed">保存时会把「第X卷」段落自动整理进大纲树，之后在写作台可继续细化章节。</p>
        <div class="ws-nav">
          <button class="btn btn-ghost" @click="step = 1">← 上一步</button>
          <button class="btn btn-primary" :disabled="!d.outlineText.trim()" @click="next">下一步 →</button>
        </div>
      </div>

      <!-- 步 3：主角 -->
      <div v-else-if="step === 3" class="ws-pane">
        <h2 class="ws-pane-title">3 · 认识你的主角</h2>
        <p class="ws-pane-desc">主角是故事的心脏。先定主角和一句人设，其他角色写到哪补到哪。</p>
        <input v-model="d.protagonist" class="ws-input" maxlength="100" placeholder="主角名字…" />
        <textarea v-model="d.protagonistDesc" class="ws-input ws-textarea" rows="4" maxlength="1000"
                  placeholder="一句话人设：他是谁、想要什么、怕什么…" />
        <div class="ws-nav">
          <button class="btn btn-ghost" @click="step = 2">← 上一步</button>
          <button class="btn btn-primary" :disabled="!d.protagonist.trim()" @click="next">下一步 →</button>
        </div>
      </div>

      <!-- 步 4：动笔 -->
      <div v-else-if="step === 4" class="ws-pane">
        <h2 class="ws-pane-title">4 · 起个书名，开写</h2>
        <p class="ws-pane-desc">给作品起标题（可以先随便起，后面随时改），然后创建作品进入写作台。</p>
        <input v-model="d.workTitle" class="ws-input" maxlength="50" placeholder="作品标题…" />
        <div class="ws-nav">
          <button class="btn btn-ghost" @click="step = 3">← 上一步</button>
          <button class="btn btn-primary" :disabled="creating || !d.workTitle.trim()" @click="finish">
            {{ creating ? '创建中…' : '🚀 创建作品，开始写作' }}
          </button>
        </div>
      </div>

      <!-- 完成 -->
      <div v-else class="ws-pane ws-done">
        <h2 class="ws-pane-title">🎉 开工！</h2>
        <p class="ws-pane-desc">作品已创建，主线 / 大纲 / 主角设定都已就位。接下来去写作台动笔吧。</p>
        <div class="ws-done-actions">
          <button class="btn btn-primary" @click="$router.push('/write')">✍ 去写作台动笔</button>
          <button class="btn btn-ghost" @click="$router.push('/works')">📚 查看我的作品</button>
          <button class="btn btn-ghost" @click="restart">🔄 再开一个工坊</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import { useUserStore } from '../../stores/user.js'
import { useToast } from '../../composables/useToast.js'

const router = useRouter()
const userStore = useUserStore()
const toast = useToast()

const DRAFT_KEY = 'inkstone_workshop'

const steps = [
  { no: 0, key: 'insp', label: '灵感' },
  { no: 1, key: 'main', label: '主线' },
  { no: 2, key: 'out', label: '大纲' },
  { no: 3, key: 'char', label: '主角' },
  { no: 4, key: 'go', label: '动笔' },
]

const step = ref(0)
const d = reactive({ inspiration: '', mainline: '', outlineText: '', protagonist: '', protagonistDesc: '', workTitle: '' })
const volumeCount = ref(3)
const mainlineLoading = ref(false)
const outlineLoading = ref(false)
const creating = ref(false)
const notes = ref([])

const outlineParsed = computed(() => (d.outlineText || '').split('\n').some(l => /第?\s*\d+\s*卷|卷[一二三四五六七八九十]/.test(l)))

// 草稿持久化：防刷新丢失
watch(() => ({ ...d, step: step.value }), () => {
  localStorage.setItem(DRAFT_KEY, JSON.stringify({ step: step.value, d: d }))
}, { deep: true })

function next() { step.value += 1 }

function restart() {
  Object.assign(d, { inspiration: '', mainline: '', outlineText: '', protagonist: '', protagonistDesc: '', workTitle: '' })
  step.value = 0
  localStorage.removeItem(DRAFT_KEY)
}

async function genMainline() {
  mainlineLoading.value = true
  const res = await api.post('/api/write/mainline', { inspiration: d.inspiration.trim() })
  mainlineLoading.value = false
  if (res.code === 0) d.mainline = res.data.mainline
  else toast.error(res.msg)
}

async function genOutline() {
  outlineLoading.value = true
  const res = await api.post('/api/write/volume-outline', { mainline: d.mainline.trim(), volume_count: volumeCount.value || 3 })
  outlineLoading.value = false
  if (res.code === 0) d.outlineText = res.data.outline
  else toast.error(res.msg)
}

/** 把卷级大纲文本解析成大纲树 parts（与 OutlineTreePanel 同结构） */
function parseOutlineTree(text) {
  const lines = (text || '').split('\n').map(l => l.trim()).filter(Boolean)
  const parts = []
  let cur = null
  for (const line of lines) {
    if (/第?\s*\d+\s*卷|卷[一二三四五六七八九十]/.test(line) && line.length <= 30) {
      cur = { kind: 'part', title: line.replace(/^[【\[]|[\】\]]$/g, '').slice(0, 60), children: [] }
      parts.push(cur)
    } else if (cur) {
      cur.children.push({ kind: 'chapter', title: '', beats: line.slice(0, 200), hook: '' })
    } else {
      parts.push({ kind: 'part', title: line.slice(0, 60), children: [] })
    }
  }
  return parts.length ? parts : [{ kind: 'part', title: '全卷', children: [] }]
}

async function finish() {
  if (creating.value) return
  creating.value = true
  try {
    // 1. 创建作品
    const res = await api.post('/api/works', { title: d.workTitle.trim(), type: 'novel', summary: d.mainline.trim().slice(0, 200) })
    if (res.code !== 0) { toast.error(res.msg); return }
    const workId = res.data.work_id

    // 2. 落 plan：logline = 主线，outline = 解析后的大纲树
    await api.put(`/api/plan/${workId}`, {
      logline: d.mainline.trim(),
      outline: parseOutlineTree(d.outlineText),
    })

    // 3. 主角设定 → work_lore
    if (d.protagonist.trim()) {
      await api.post(`/api/works/${workId}/lore`, {
        title: `主角：${d.protagonist.trim()}`,
        content: d.protagonistDesc.trim() || '（暂无设定）',
      })
    }

    localStorage.removeItem(DRAFT_KEY)
    step.value = 5  // 完成页
    toast.success('作品创建成功')
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  // 恢复草稿
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (raw) {
      const saved = JSON.parse(raw)
      if (saved && typeof saved.step === 'number' && saved.step >= 0 && saved.step <= 4) {
        Object.assign(d, saved.d || {})
        step.value = saved.step
      }
    }
  } catch (e) { /* 草稿损坏忽略 */ }
  // 我的灵感（便签）供带入
  if (userStore.isLoggedIn) {
    const r = await api.get('/api/notes')
    if (r.code === 0) notes.value = (r.data.items || []).filter(i => i.kind === 'note')
  }
})
</script>

<style scoped>
.page-container { max-width: 860px; margin: 0 auto; padding: 1.5rem 1rem 3rem; }
.ws-hero { padding: 2rem 2.2rem; margin-bottom: 1.2rem; border-radius: var(--radius-lg);
  background: linear-gradient(135deg, rgba(196,163,90,0.12), rgba(196,163,90,0.02)); }
.ws-kicker { font-size: 0.72rem; letter-spacing: 0.3em; color: var(--accent-primary); margin-bottom: 0.5rem; }
.ws-title { font-family: var(--font-serif); font-size: 1.6rem; margin: 0 0 0.6rem; color: var(--text-primary); }
.ws-desc { color: var(--text-secondary); font-size: 0.88rem; line-height: 1.8; margin: 0 0 1.2rem; }
.ws-steps { display: flex; gap: 8px; flex-wrap: wrap; }
.ws-step { display: flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: var(--radius-full);
  border: 1px solid var(--border-glass); background: var(--bg-glass); color: var(--text-muted); font-size: 0.8rem; }
.ws-step.done { color: var(--accent-primary); border-color: rgba(196,163,90,0.4); }
.ws-step.active { color: var(--accent-primary); border-color: rgba(196,163,90,0.6); background: rgba(196,163,90,0.12); font-weight: 600; }
.ws-step-no { font-weight: 700; }
.ws-body { padding: 1.8rem 2rem; }
.ws-pane-title { font-family: var(--font-serif); font-size: 1.25rem; margin: 0 0 0.4rem; color: var(--text-primary); }
.ws-pane-desc { color: var(--text-secondary); font-size: 0.85rem; line-height: 1.8; margin: 0 0 1.1rem; }
.ws-input { background: var(--bg-glass); color: var(--text-primary); border: 1px solid rgba(196,163,90,0.2);
  border-radius: 10px; padding: 10px 14px; font-size: 0.9rem; width: 100%; box-sizing: border-box; margin-bottom: 10px; }
.ws-textarea { resize: vertical; line-height: 1.8; }
.ws-num { width: 80px; }
.ws-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 4px; }
.ws-hint { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 2px 0 12px; }
.ws-hint-label { color: var(--text-muted); font-size: 0.78rem; }
.ws-chip { font-size: 0.78rem; padding: 4px 12px; border-radius: var(--radius-full); background: var(--bg-glass);
  border: 1px solid var(--border-glass); color: var(--text-secondary); cursor: pointer; }
.ws-chip:hover { border-color: var(--accent-primary); color: var(--accent-primary); }
.ws-nav { display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px; }
.ws-done { text-align: center; padding: 1rem 0; }
.ws-done-actions { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-top: 1rem; }
</style>