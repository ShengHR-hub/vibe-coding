# P6-B5 创作工坊融进写作台 改造计划（反死板 + 去 emoji）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 废弃独立全屏向导 `/workshop`，把创作工坊功能改造成写作台右侧面板内的一个工具「创作工坊」（左编辑右面板的同构体验）：无步骤条、无顺序强制、每个功能独立区块、AI 仅作按钮辅助；同步清理二期新增 UI 中的全部 emoji。

**Architecture:** 写作台已有「三阶段 × 工具」面板体系（`tools` 数组 + `activeTab`/`activeComponent` 切换 + `inkstone:goto-tool` 事件）。改造：新建 `WorkshopPanel.vue`（复用 P6-B3 的全部数据逻辑：灵感→主线→卷级大纲→主角，产出落 plan/lore），注册为 plan 阶段第一个工具；删除 `/workshop` 路由与 `WorkshopView.vue`；OnboardingModal「跟随引导」改为跳 `/write?tool=workshop`，写作台 onMounted 读 query 自动切到该工具并清 query。所有新增 UI（OnboardingModal 三卡图标、我的灵感页签、任务卡 AI 区、卡壳了按钮、NotesFloat 悬浮钮、工坊面板）统一去 emoji，改文字/中性符号。老手系统既有 tools 图标（🧭☆≡ 等）保留不动（用户认可老手形态）。

**Tech Stack:** Vue3 + Pinia + vue-router + api 封装；无后端改动。

**Spec:** 用户反馈（2026-09-06）："工坊太死板太单一、AI 只是辅助不要强制、页面孤立在系统外、不要 emoji"。

---

## 文件结构

| 文件 | 动作 | 职责 |
|---|---|---|
| `client/src/views/write/WorkshopPanel.vue` | Create | 右侧面板工具「创作工坊」：四区块（灵感/主线/卷级大纲/主角），无步骤无强制，AI 按钮辅助，随改随存 |
| `client/src/views/write/WriteStudio.vue` | Modify | tools 注册 workshop 工具（plan 阶段首位）；onMounted 处理 `?tool=workshop` 自动切入；删 WorkshopView import |
| `client/src/router/index.js` | Modify | 删除 `/workshop` 路由 |
| `client/src/views/write/WorkshopView.vue` | Delete | 被 WorkshopPanel.vue 取代 |
| `client/src/components/OnboardingModal.vue` | Modify | guide → `/write?tool=workshop`；三卡图标去 emoji |
| `client/src/components/NotesFloat.vue` | Modify | FAB 去 emoji（📝→文字） |
| `client/src/views/Inspire.vue` | Modify | 我的灵感三区标题去 emoji |
| `client/src/views/write/TaskCardPanel.vue` | Modify | AI 搭把手区去 emoji |
| `client/src/views/write/WriteStudio.vue` | Modify | 卡壳了按钮去 emoji |

---

## Task 1: WorkshopPanel.vue——面板化工坊（全部核心）

**Files:**
- Create: `client/src/views/write/WorkshopPanel.vue`

- [ ] **Step 1: 模板——四独立区块 + 无作品引导，零 emoji**

```vue
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
          {{ saving ? '保存中…' : '保存主线' }}（写入书立项）
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
          {{ savingProto ? '保存中…' : '保存主角设定' }}（写进设定库）
        </button>
      </section>
    </template>
  </div>
</template>
```

- [ ] **Step 2: script——复用 P6-B3 全部逻辑（面板版）**

```vue
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
    loadPlanning()
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
  const savedMainline = mainline.value
  await loadPlanning()
  if (!savedMainline) mainline.value = mainline.value // 保持读取
  const lore = await api.get(`/api/works/${workId.value}/lore`)
  if (lore.code === 0 && workId.value) {
    const proto = (lore.data.items || []).find(i => (i.title || '').startsWith('主角：'))
    if (proto) {
      protagonist.value = (proto.title || '').replace(/^主角：/, '').trim()
      protagonistDesc.value = proto.content || ''
    }
  }
})

watch(workId, (v) => { if (v) { loadPlanning() } })
</script>
```

> onMounted 中 lore 读取依赖 workId 就绪：若无作品则跳过（`if (lore.code === 0 && workId.value)` 内已判空）；`watch(workId)` 在切换作品时重载。loadPlanning 里 notes 与作品无关，仅在 mainline 加载时顺带。

- [ ] **Step 3: 样式**

```css
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
```

- [ ] **Step 4: Build 验证**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

预期：`✓ built`，exit 0。

---

## Task 2: WriteStudio 注册工具 + ?tool= 自动切入 + 删旧 import

**Files:**
- Modify: `client/src/views/write/WriteStudio.vue`

- [ ] **Step 1: import 替换**

`import WorkshopView from './WorkshopView.vue'`（不存在则跳过）→ 新增：

```js
import WorkshopPanel from './WorkshopPanel.vue'
```

- [ ] **Step 2: tools 数组——plan 阶段首位加 workshop**

```js
const tools = [
  // ① 定目标
  { key: 'workshop', stage: 'plan', label: '创作工坊', icon: '工', comp: WorkshopPanel },
  { key: 'blueprint', stage: 'plan', label: '立项蓝图', icon: '🧭', comp: BlueprintPanel },
  ...
```

- [ ] **Step 3: onMounted 处理 ?tool=**

在 `onMounted(() => { window.addEventListener('inkstone:goto-tool', onGotoTool) ... })` 中，弹窗逻辑之后加：

```js
  const t = route.query.tool
  if (t && tools.find(x => x.key === t)) {
    const tool = tools.find(x => x.key === t)
    activeStage.value = tool.stage
    switchTool(t)
    router.replace({ query: {} })  // 清掉 query，避免刷新重复触发
  }
```

> 确认 WriteStudio 已有 `router`（useRoute 有，useRouter 需确认存在；若无则补 `const router = useRouter()`）。

- [ ] **Step 4: 卡壳了按钮去 emoji**

模板中 `😮‍💨` 改掉：

```html
<button class="float-unstick-btn" title="写不下去了？让 AI 给你接下去的方向" @click="openUnstick" :disabled="unstickLoading || !writingStore.content.trim()">
  <span class="ffb-ico">?</span>{{ unstickLoading ? 'AI 思考中…' : '卡壳了' }}
</button>
```

模态标题 `😮‍💨 卡壳了？接下来可以写…` → `卡壳了？接下来可以写…`。

- [ ] **Step 5: Build 验证 + Commit**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

```bash
git add client/src/views/write/WriteStudio.vue
git commit -m "refactor(ui): 创作工坊注册为写作台右侧工具并支持 ?tool=workshop 直达（P6-B5）"
```

---

## Task 3: 删 /workshop 路由与 WorkshopView.vue

**Files:**
- Modify: `client/src/router/index.js`
- Delete: `client/src/views/write/WorkshopView.vue`

- [ ] **Step 1: 删除路由**

```js
  // 删除：{ path: '/workshop', name: 'Workshop', component: () => import('../views/write/WorkshopView.vue'), meta: { auth: true } },
```

- [ ] **Step 2: 删除文件**

```powershell
Remove-Item client/src/views/write/WorkshopView.vue
```

- [ ] **Step 3: OnboardingModal guide → /write?tool=workshop + 三卡去 emoji**

```js
  } else if (mode === 'guide') {
    router.push('/write?tool=workshop')
  }
```

三卡图标（ob-opt-ico）emoji 改为中性文字/符号：

```html
<button class="ob-opt" @click="choose('guide')">
  <span class="ob-opt-ico">导</span>
  <span class="ob-opt-name">跟随引导（新手）</span>
  <span class="ob-opt-sub">在写作台右侧一步步完成灵感 → 主线 → 大纲 → 动笔</span>
</button>
<button class="ob-opt" @click="choose('pro')">
  <span class="ob-opt-ico">✍</span>
  ...
```

> ✍ 非 emoji（打字符号）可保留；🌙 也是符号类——若用户反感，统一改为单个汉字（导/写/静）。实现时尽量全用汉字/符号，不用彩色 emoji。

- [ ] **Step 4: Build 验证 + Commit**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

```bash
git add client/src/router/index.js client/src/views/write/WorkshopView.vue client/src/components/OnboardingModal.vue
git commit -m "refactor(ui): 移除 /workshop 独立页——新手卡改跳写作台 ?tool=workshop，弹窗去 emoji（P6-B5）"
```

---

## Task 4: 其余新增 UI 去 emoji

**Files:**
- Modify: `client/src/components/NotesFloat.vue`
- Modify: `client/src/views/Inspire.vue`
- Modify: `client/src/views/write/TaskCardPanel.vue`

- [ ] **Step 1: NotesFloat FAB**

FAB 按钮内容 `📝` → 汉字「记」（或 保持简单）；面板标题内 emoji 一并清理。读文件后按实际情况替换。

- [ ] **Step 2: Inspire 我的灵感三区标题**

`✨ 闪念便签` → `闪念便签`；`🧭 AI 主线` → `AI 主线`；`💛 我的收藏` → `我的收藏`；页面内其他新增 emoji（Ai 按钮文案等）一并去。

- [ ] **Step 3: TaskCardPanel AI 区**

`🤖 AI 搭把手` → `AI 搭把手`；`✨ 生成本章剧情` → `生成本章剧情`；`📋 写完提取要点` → `写完提取要点`。

- [ ] **Step 4: Build 验证 + Commit**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

```bash
git add client/src/components/NotesFloat.vue client/src/views/Inspire.vue client/src/views/write/TaskCardPanel.vue
git commit -m "style(ui): 二期新增 UI 统一去 emoji（便签/我的灵感/任务卡）（P6-B5）"
```

---

## Task 5: 全量验证 + 台账

- [ ] **Step 1: pytest 全量（后端零改动）**

```powershell
cd server; python -m pytest tests -q -p no:cacheprovider
```

预期：**129 passed**，exit 0。

- [ ] **Step 2: build 全量**

```powershell
cd client; npm run build
```

预期：`✓ built`。

- [ ] **Step 3: 人肉冒烟**

1. 弹窗选「跟随引导」→ 落到写作台 → 右侧自动切到「创作工坊」工具（?tool=workshop）
2. 无作品时面板给「创建这本书」→ 创建后 writingStore 打开，四区块可用
3. 灵感→AI 生成主线→保存；主线→AI 卷级大纲→保存后到「大纲规划」看树
4. 主角保存 → 「设定库」出现「主角：X」
5. 切走再切回工坊：已有主线/大纲文本回显（从 plan 读回）
6. 全页面无新增 emoji（工坊/便签/我的灵感/任务卡/卡壳了/弹窗）

- [ ] **Step 4: 台账登记**

P6-B 批次5：工坊面板化融合 + 去 emoji ✅；冒烟待体验。

---

## Self-Review 结论

- **覆盖用户反馈**：死板→右侧面板工具（无步骤条无强制）✅；孤立→融进写作台本体（左编辑右面板同构）✅；AI 辅助→全部按钮化、可手动 ✅；emoji→二期新增 UI 全部清理 ✅；老手系统既有 icon 保留。
- **占位符扫描**：无 TBD；各处"读文件后按实际替换"为适配核对项。
- **类型一致性**：`?tool=workshop` 在 OnboardingModal/WriteStudio 两端一致；plan/lore/works 端点契约与既有实现一致；`outlineToText/parseOutlineTree` 互逆，与 OutlineTreePanel 结构一致。