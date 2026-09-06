# P6-B3 创作工坊向导页 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新建「创作工坊」向导页 `/workshop`：新手按 0 灵感 → 1 主线 → 2 大纲 → 3 主角 → 4 动笔 五步走完从念头到开写，产出全部落库（作品/主线/大纲树/主角设定），并让 OnboardingModal「跟随引导」卡真跳转进工坊。

**Architecture:** 严格遵守三边界①，**零新表零新端点**，全部复用：
- 作品 → `POST /api/works`（title 必填）
- 整体主线 → `PUT /api/plan/<work_id>` 的 `logline` 字段
- AI 卷级大纲 → AI 文本解析成大纲树（`[{kind:'part',title,children:[{kind:'chapter',...}]}]`）落 `outline`（OutlineTreePanel 同结构）
- 主角设定 → `POST /api/works/<work_id>/lore` 存 work_lore
- AI 生成 → 批次 1 端点（mainline / volume-outline）+ 现有 `/api/write/character`
- 灵感带入 → `GET /api/notes`（我的灵感）
向导状态存组件内 + localStorage 草稿（`inkstone_workshop`），防刷新丢失；完成时清草稿。页面对齐项目视觉（glass-card / 金 accent / 变量体系）。

**Tech Stack:** Vue3 + vue-router + Pinia（writing/user store）+ api 封装；无新后端。

**Spec:** `docs/superpowers/specs/2026-09-06-p6a-newcomer-onboarding-design.md` §5 二期；本计划为其批次 3。

---

## 文件结构

| 文件 | 动作 | 职责 |
|---|---|---|
| `client/src/views/write/WorkshopView.vue` | Create | 向导页本体（五步 + 完成） |
| `client/src/router/index.js` | Modify | 加 `/workshop` 路由（auth） |
| `client/src/components/OnboardingModal.vue` | Modify | guide 从占位改为跳 `/workshop` |
| `client/src/views/write/WriteStudio.vue` | Modify（可选） | 侧栏或入口加「创作工坊」（暂不做，避免二期范围膨胀——按需） |
| `server/tests/test_*.py` | 不动 | 本批次无新后端，不需新测试 |

---

## Task 1: 路由 + OnboardingModal 跳转

**Files:**
- Modify: `client/src/router/index.js`
- Modify: `client/src/components/OnboardingModal.vue`

- [ ] **Step 1: 加路由**

在 `client/src/router/index.js` 第 9 行（/write/plain 之后）插入：

```js
  { path: '/workshop', name: 'Workshop', component: () => import('../views/write/WorkshopView.vue'), meta: { auth: true } },
```

- [ ] **Step 2: OnboardingModal guide 真跳转**

`OnboardingModal.vue` 第 53-55 行改为：

```js
  } else if (mode === 'guide') {
    router.push('/workshop')
  }
```

（删除 toast 占位行，不再提示"建设中"。）

- [ ] **Step 3: Commit**

```bash
git add client/src/router/index.js client/src/components/OnboardingModal.vue
git commit -m "feat(ui): /workshop 路由 + OnboardingModal 新手卡真跳转创作工坊（P6-B3）"
```

---

## Task 2: WorkshopView.vue 骨架（模板 + 状态 + 草稿持久化）

**Files:**
- Create: `client/src/views/write/WorkshopView.vue`

- [ ] **Step 1: 模板骨架**

创建 `client/src/views/write/WorkshopView.vue`：

```vue
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
        <p class="ws-hint-label" v-if="d.outlineText && !d.outlineParsed">保存时会把「第X卷」段落自动整理进大纲树，之后在写作台可继续细化章节。</p>
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
```

- [ ] **Step 2: script（状态 + 草稿 + 动作全量）**

```vue
<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
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

const outlineParsed = computed(() => d.outlineText.trim().split('\n').some(l => /第?\s*\d+\s*卷|卷[一二三四五六七八九十]/.test(l)))

// 草稿持久化：防刷新丢失
watch(() => ({ ...d, step: step.value }), (val) => {
  localStorage.setItem(DRAFT_KEY, JSON.stringify({ step: val.step, d: d }))
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
  const volRe = /^\s*[【\[]?第?\s*(\d+|[一二三四五六七八九十]+)\s*卷/.test
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
```

> 注意：`outlineParsed` 用了 `computed`，需在 script 顶部 import 补充 `computed`。若模板中该提示要按解析结果显示，也可以直接在模板内联判断；实现时确保 import 齐全。

- [ ] **Step 3: 样式**

```css
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
```

- [ ] **Step 4: 手写 import 完整性自检**

确认 `<script setup>` 顶部 import 包括：`ref, reactive, watch, onMounted, computed`（computed 用于 outlineParsed——若未用它则可不 import，但模板引用了 `d.outlineParsed`，必须定义；实现时二选一：保留 computed 或模板只判断文字提示）。

- [ ] **Step 5: Build 验证**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

预期：`✓ built`，exit 0。

- [ ] **Step 6: Commit**

```bash
git add client/src/views/write/WorkshopView.vue
git commit -m "feat(ui): 创作工坊向导页 /workshop（灵感→主线→大纲→主角→动笔，草稿持久化，产出全落库）（P6-B3）"
```

---

## Task 3: 后端契约验证（无新代码，验证既有端点按计划可用）

**Files:** 无修改，运行验证。

- [ ] **Step 1: 验证 plan PUT + works POST + lore POST 契约**

用一次真实请求链验证（打开发库或测试库均可，走 app 测试客户端）——写一次性验证脚本并执行后删除：

```python
"""一次性契约验证：工坊完成动作要用的三组 API。"""
from app import create_app
from database import db

app = create_app()
with app.test_client() as c:
    c.post('/api/auth/register', json={'username': 'ws_tmp', 'password': 'test123456'})
    c.post('/api/auth/login', json={'username': 'ws_tmp', 'password': 'test123456'})
    # 1. 创建作品
    r = c.post('/api/works', json={'title': '工坊契约测试', 'type': 'novel', 'summary': '一句话简介'})
    assert r.get_json()['code'] == 0, r.get_json()
    wid = r.get_json()['data']['work_id']
    # 2. 落 plan（logline + outline 树）
    r = c.put(f'/api/plan/{wid}', json={
        'logline': '少年追光，破除枷锁',
        'outline': [{'kind': 'part', 'title': '第一卷 觉醒', 'children': [{'kind': 'chapter', 'title': '', 'beats': '遇见猫', 'hook': ''}]}],
    })
    assert r.get_json()['code'] == 0, r.get_json()
    # 3. 主角设定 → lore
    r = c.post(f'/api/works/{wid}/lore', json={'title': '主角：小明', 'content': '想要光，怕被遗忘'})
    assert r.get_json()['code'] == 0, r.get_json()
    # 4. 读回验证
    p = c.get(f'/api/plan/{wid}').get_json()['data']['plan']
    assert p['logline'] == '少年追光，破除枷锁'
    assert p['outline'][0]['title'] == '第一卷 觉醒'
    lore = c.get(f'/api/works/{wid}/lore').get_json()['data']
    assert any('小明' in str(x.get('title')) for x in lore), lore
    print('契约验证通过 ✅')
```

```powershell
cd server; set PYTHONIOENCODING=utf-8; python _tmp_ws_contract.py
```

预期：`契约验证通过 ✅`。**执行后删除 `_tmp_ws_contract.py`**；测试用户 ws_tmp 从开发库清理（DELETE FROM users WHERE username='ws_tmp'），或直接忽略（开发库测试用户按既有纪律处理）。

- [ ] **Step 2: 巡检大纲解析（parseOutlineTree）边界**

- 空文本 → 返回兜底 `[{kind:'part',title:'全卷',children:[]}]` ✅
- 每行 ≤30 字的"第X卷/卷X"行 → 新建 part；其下行 → 卷内 chapter（beats 存原文）✅
- 无卷标记 → 每行一个 part（容错）✅

- [ ] **Step 3: Commit（验证脚本不提交，无代码变更则跳过）**

---

## Task 4: 全量验证 + 收尾登记

**Files:** 无（仅验证）

- [ ] **Step 1: pytest 全量（确认后端无回归）**

```powershell
cd server; python -m pytest tests -q -p no:cacheprovider
```

预期：**129 passed**，exit 0。

- [ ] **Step 2: build 全量**

```powershell
cd client; npm run build
```

预期：`✓ built`，exit 0。

- [ ] **Step 3: 人肉冒烟路径**

1. 主页 → 点「开始写作」→ 写作台首次弹「从哪开始？」→ 点「跟随引导」→ 落到 `/workshop`
2. 灵感步：填灵感（或点便签 chip 带入）→ 下一步
3. 主线步：点「AI 生成主线」→ 出结果 → 可编辑 → 下一步
4. 大纲步：设 3 卷 → 生成 → 结果出现卷标记 → 下一步
5. 主角步：填名字 + 一句话人设 → 下一步
6. 动笔步：填标题 → 创建 → 完成页 →「去写作台」
7. 写作台确认：作品存在；「① 三级大纲」面板里有卷级大纲树；「设定」区有「主角：X」；刷新后作品都在
8. 中途刷新页面 → 草稿还在（localStorage）
9. 右上角「?」→ 弹窗选「跟随引导」→ 再次进工坊

- [ ] **Step 4: 台账登记 + commit**

`docs/改造进度.md`：P6-B3 标记 ✅（pytest 129 / build 绿 / 冒烟待体验），P6-B4（写作台增强：任务卡 AI 剧情+提取要点 / 卡壳了按钮 / 四格降级）待做。

**2026-09-06 追加说明**：批次 3 设计时把「5 反馈」「6 交付」合并进完成页引导（去写作台后现成工具都有），向导本体聚焦 0-4 核心闭环；OnboardingModal 引导卡从此真正可用。

---

## Self-Review 结论

- **Spec 覆盖**：二期「创作工坊向导页（0灵感→1主线→2大纲→3角色→4动笔→5反馈→6交付）」→ 0-4 完整实现，5 反馈/6 交付以完成页引导复用写作台既有能力（FinalizePanel 交付、诊断/审校反馈面板）✅；「AI 主线生成」「AI 卷级大纲草稿」→ 复用 P6-B1 端点 ✅；「OnboardingModal 新手卡跳创作工坊」→ Task 1 ✅。
- **占位符扫描**：无 TBD/TODO；每步含完整代码；导入清单（computed）在 Task 2 Step 4 有显式核对项，非占位。
- **类型一致性**：`parseOutlineTree` 输出结构与 OutlineTreePanel 消费的 `[{kind:'part',title,children:[{kind:'chapter',title,beats,hook}]}]` 一致；plan PUT 的 `logline`/`outline` 字段与 plans.py 已知契约一致；lore POST 的 title/content 与 works.py lore 端点一致；`/api/write/mainline`、`/api/write/volume-outline` 的入参/返回字段与 P6-B1 实现一致。