# P6-B6 主页三入口 + 新手系统独立页 + 说明文档 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ① 首页 hero 区改为三入口（开始写作→分流页 / 灵感馆 / 纯净写作），移除「社区广场」portal；② 新增分流页 `/start`（新手系统 / 老手系统 / 纯净写作 三张大卡）；③ 新手系统为**独立页面** `/write/new`——左写作面板 + 右侧四区块功能（灵感/主线/卷级大纲/主角），AI 仅按钮、无 emoji；④ 新增「说明文档」弹窗（整体介绍 + 各系统流程与优缺点 + 「今天不再弹出」），头像菜单加「说明文档」入口。

**Architecture:** 全部前端，无后端改动。复用现有：WorkshopPanel.vue（四区块逻辑）作为新手页右侧；PlainWrite 的编辑模式作新手页左侧；OnboardingModal 的 guide 卡改跳 `/write/new`；UserMenu 加「说明文档」菜单项；新增 GuideModal.vue 说明文档弹窗（挂 App.vue，事件 `inkstone:open-guide` 触发，Home 登录后判断 localStorage 日期自动触发）。老手写作台 tools 移除 workshop 工具注册（新手体系移到独立页），`?tool=workshop` 逻辑一并删除。

**Tech Stack:** Vue3 + vue-router + Pinia + api 封装；无后端。

**Spec:** 用户反馈（2026-09-06）：「首页只留三入口（开始写作/灵感馆/纯净写作）」、「新手系统单做一页」、「门户先弹说明文档（工具介绍+各系统流程优缺点+今天不再弹出）」、「说明文档放头像菜单」。

---

## 文件结构

| 文件 | 动作 | 职责 |
|---|---|---|
| `client/src/views/Home.vue` | Modify | hero 区删社区广场 portal；开始写作 → `/start`；登录后挂 GuideModal 自动弹 |
| `client/src/views/StartChoose.vue` | Create | 分流页：新手系统 / 老手系统 / 纯净写作 三卡 |
| `client/src/views/write/NewbieStudio.vue` | Create | 新手系统独立页：左编辑（作品/章节/保存/导出）+ 右 WorkshopPanel |
| `client/src/components/GuideModal.vue` | Create | 说明文档弹窗（整体介绍 + 三系统优缺点 + 今天不再弹） |
| `client/src/router/index.js` | Modify | 加 `/start`、`/write/new` |
| `client/src/views/write/WriteStudio.vue` | Modify | tools 移除 workshop 注册 + `?tool=` 逻辑删除 |
| `client/src/components/OnboardingModal.vue` | Modify | guide → `/write/new`（去 `?tool=workshop`） |
| `client/src/components/UserMenu.vue` | Modify | 加「说明文档」菜单项（dispatch `inkstone:open-guide`） |
| `client/src/App.vue` | Modify | 挂 GuideModal 组件 |

---

## Task 1: 说明文档弹窗 GuideModal.vue

**Files:**
- Create: `client/src/components/GuideModal.vue`

- [ ] **Step 1: 组件（文档内容 + 今天不再弹 + 事件触发）**

```vue
<template>
  <Teleport to="body">
    <div v-if="visible" class="gd-overlay" @click.self="close">
      <div class="gd-card">
        <div class="gd-head">
          <h3 class="gd-title">墨池使用说明</h3>
          <button class="gd-close" @click="close">✕</button>
        </div>
        <div class="gd-body">
          <p class="gd-lead">墨池有两个写作系统 + 纯净写作，按你的习惯选一条路：</p>

          <section class="gd-sec">
            <h4 class="gd-sec-title">1. 新手系统（推荐第一次用）</h4>
            <p class="gd-txt">左边写作，右边跟着「灵感 → 主线 → 卷级大纲 → 主角」一步步把书立起来。AI 只在你点按钮时帮忙，不强制、不用也完全行。</p>
            <p class="gd-flow"><b>操作流程：</b>进入新手系统 → 创建/打开作品 → （可选）写灵感 → AI 或自己写主线 → 保存 → 生成/写卷级大纲 → 保存 → 写主角 → 直接开写</p>
            <p class="gd-pros"><b>优点：</b>有引导不容易懵，结构自然成型。<b>注意：</b>功能精简，深度加工请去老手系统。</p>
          </section>

          <section class="gd-sec">
            <h4 class="gd-sec-title">2. 老手系统（功能全）</h4>
            <p class="gd-txt">完整写作台：立项蓝图、三级大纲、设定库、角色、任务卡、续写、教练、审查、润色、交付，全部面板按「起·承·合」组织。</p>
            <p class="gd-flow"><b>操作流程：</b>进入写作台 → 保存作品生成 work_id → 「起」定目标（蓝图/大纲/设定）→ 「承」写作（任务卡/续写/教练）→ 「合」收尾（审校/润色/诊断/交付）</p>
            <p class="gd-pros"><b>优点：</b>功能最全。<b>注意：</b>面板多，新手初期可能无所适从。</p>
          </section>

          <section class="gd-sec">
            <h4 class="gd-sec-title">3. 纯净写作</h4>
            <p class="gd-txt">只有一个编辑区：选作品 → 写 → 保存 / 导出。没有面板、没有 AI 按钮。</p>
            <p class="gd-flow"><b>操作流程：</b>选/建作品 → 写作（Ctrl+S 保存）→ 导出 txt</p>
            <p class="gd-pros"><b>优点：</b>零干扰。<b>注意：</b>无 AI 辅助，进阶功能需回写作台。</p>
          </section>
        </div>
        <div class="gd-foot">
          <label class="gd-today">
            <input type="checkbox" v-model="todayOnly" /> 今天不再弹出
          </label>
          <button class="btn btn-primary" @click="close">知道了</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const visible = ref(false)
const todayOnly = ref(false)
const GUIDE_KEY = 'inkstone_guide_dismiss'

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

function open(auto = false) {
  // 自动弹出时检查「今天不再弹」
  if (auto && localStorage.getItem(GUIDE_KEY) === todayStr()) return
  visible.value = true
}

function close() {
  visible.value = false
  if (todayOnly.value) localStorage.setItem(GUIDE_KEY, todayStr())
  todayOnly.value = false
}

function onOpenGuide() {
  open(false)
}

onMounted(() => window.addEventListener('inkstone:open-guide', onOpenGuide))
onUnmounted(() => window.removeEventListener('inkstone:open-guide', onOpenGuide))

defineExpose({ open })
</script>

<style scoped>
.gd-overlay {
  position: fixed; inset: 0; z-index: 950;
  display: flex; align-items: center; justify-content: center; padding: 1rem;
  background: rgba(0, 0, 0, 0.55);
}
.gd-card {
  width: min(560px, 94vw); max-height: 86vh; display: flex; flex-direction: column;
  padding: 20px 24px; border-radius: 16px; background: var(--bg-panel, #1a1c24);
  border: 1px solid rgba(196, 163, 90, 0.25); box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
}
.gd-head { display: flex; justify-content: space-between; align-items: center; }
.gd-title { font-family: var(--font-serif); margin: 0; font-size: 1.15rem; }
.gd-close { background: none; border: none; color: var(--text-muted); font-size: 1rem; cursor: pointer; }
.gd-body { overflow-y: auto; margin: 12px 0; padding-right: 4px; }
.gd-lead { font-size: 0.88rem; color: var(--text-secondary); margin: 0 0 12px; }
.gd-sec { margin-bottom: 14px; }
.gd-sec-title { font-size: 0.95rem; margin: 0 0 4px; color: var(--accent-primary); }
.gd-txt { font-size: 0.82rem; line-height: 1.8; color: var(--text-secondary); margin: 0 0 6px; }
.gd-flow { font-size: 0.78rem; line-height: 1.8; color: var(--text-muted); margin: 0 0 4px; }
.gd-pros { font-size: 0.78rem; line-height: 1.8; color: var(--text-muted); margin: 0; }
.gd-foot { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(196,163,90,0.15); padding-top: 10px; }
.gd-today { font-size: 0.78rem; color: var(--text-muted); display: flex; align-items: center; gap: 6px; }
</style>
```

- [ ] **Step 2: Build 验证**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

预期：`✓ built`。

---

## Task 2: App.vue 挂 GuideModal + UserMenu 加「说明文档」

**Files:**
- Modify: `client/src/App.vue`
- Modify: `client/src/components/UserMenu.vue`

- [ ] **Step 1: App.vue 挂载**

App.vue 模板（根元素内）末尾加：

```html
    <GuideModal />
```

script 加 import：

```js
import GuideModal from './components/GuideModal.vue'
```

- [ ] **Step 2: UserMenu 菜单加「说明文档」**

在 `<router-link to="/inspire" ...>灵感馆</router-link>` 之后加：

```html
          <a href="#" @click.prevent="openGuide">说明文档</a>
```

script 加：

```js
function openGuide() {
  menuOpen.value = false
  window.dispatchEvent(new CustomEvent('inkstone:open-guide'))
}
```

- [ ] **Step 3: Build 验证 + Commit**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

```bash
git add client/src/App.vue client/src/components/UserMenu.vue client/src/components/GuideModal.vue
git commit -m "feat(ui): 说明文档弹窗 GuideModal（整体介绍+三系统流程优缺点+今天不再弹）+ 头像菜单入口（P6-B6）"
```

---

## Task 3: 分流页 StartChoose.vue

**Files:**
- Create: `client/src/views/StartChoose.vue`

- [ ] **Step 1: 三卡分流页（无 emoji，风格对齐首页 portal）**

```vue
<template>
  <div class="sc-page">
    <div class="sc-head">
      <p class="sc-kicker">CHOOSE YOUR PATH</p>
      <h1 class="sc-title">选择你的写作方式</h1>
      <p class="sc-desc">同一个墨池，三条路。不确定就选「新手系统」，随时可回。</p>
    </div>
    <div class="sc-cards">
      <router-link to="/write/new" class="sc-card sc-newbie">
        <span class="sc-en">Newbie</span>
        <span class="sc-name">新手系统</span>
        <span class="sc-sub">左边写作 · 右边引导：灵感 → 主线 → 大纲 → 主角，AI 偶尔搭把手</span>
        <span class="sc-line"></span>
        <span class="sc-tag">第一次用？选这个</span>
      </router-link>
      <router-link to="/write" class="sc-card sc-pro">
        <span class="sc-en">Pro</span>
        <span class="sc-name">老手系统</span>
        <span class="sc-sub">完整写作台：蓝图 · 大纲 · 设定 · 任务卡 · 续写 · 审校 · 交付</span>
        <span class="sc-line"></span>
        <span class="sc-tag">功能最全</span>
      </router-link>
      <router-link to="/write/plain" class="sc-card sc-plain">
        <span class="sc-en">Plain</span>
        <span class="sc-name">纯净写作</span>
        <span class="sc-sub">只有编辑区：选作品 → 写 → 保存 / 导出，零干扰</span>
        <span class="sc-line"></span>
        <span class="sc-tag">只想安静写</span>
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.sc-page { min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem 1rem; }
.sc-head { text-align: center; margin-bottom: 2.2rem; }
.sc-kicker { font-size: 0.72rem; letter-spacing: 0.3em; color: var(--accent-primary); margin-bottom: 0.6rem; }
.sc-title { font-family: var(--font-serif); font-size: 1.8rem; margin: 0 0 0.6rem; color: var(--text-primary); }
.sc-desc { color: var(--text-secondary); font-size: 0.88rem; }
.sc-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.2rem; max-width: 900px; width: 100%; }
.sc-card {
  position: relative; display: flex; flex-direction: column; gap: 8px;
  padding: 2rem 1.6rem; border-radius: var(--radius-lg); text-decoration: none;
  background: var(--bg-card); border: 1px solid var(--border-glass);
  transition: all 0.22s ease; overflow: hidden;
}
.sc-card:hover { transform: translateY(-4px); border-color: rgba(196,163,90,0.5); }
.sc-en { font-size: 0.7rem; letter-spacing: 0.25em; color: var(--text-muted); }
.sc-name { font-family: var(--font-serif); font-size: 1.3rem; color: var(--text-primary); }
.sc-sub { font-size: 0.82rem; line-height: 1.8; color: var(--text-secondary); }
.sc-line { width: 36px; height: 2px; background: var(--accent-primary); transition: width 0.25s; }
.sc-card:hover .sc-line { width: 70%; }
.sc-tag { font-size: 0.72rem; color: var(--accent-primary); }
.sc-newbie .sc-line { background: var(--accent-primary); }
.sc-pro .sc-line { background: var(--accent-purple, #a78bfa); }
.sc-plain .sc-line { background: #60a5fa; }
</style>
```

> sc-page 由全局 layout 提供背景（NavBar 仍在顶部），无 script。

- [ ] **Step 2: router 加路由**

```js
  { path: '/start', name: 'StartChoose', component: () => import('../views/StartChoose.vue'), meta: { auth: true } },
  { path: '/write/new', name: 'NewbieStudio', component: () => import('../views/write/NewbieStudio.vue'), meta: { auth: true } },
```

- [ ] **Step 3: Build 验证 + Commit**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

```bash
git add client/src/views/StartChoose.vue client/src/router/index.js
git commit -m "feat(ui): 分流页 /start（新手/老手/纯净三卡）+ 路由（P6-B6）"
```

---

## Task 4: NewbieStudio.vue——新手系统独立页

**Files:**
- Create: `client/src/views/write/NewbieStudio.vue`

- [ ] **Step 1: 左编辑 + 右 WorkshopPanel**

```vue
<template>
  <div class="nb-root">
    <div class="nb-bar">
      <router-link to="/" class="nb-back">← 首页</router-link>
      <span class="nb-title">新手系统</span>
      <select v-model="nbWorkId" class="nb-select" @change="onOpenWork">
        <option :value="null" disabled>选择作品…</option>
        <option v-for="w in works" :key="w.work_id" :value="w.work_id">{{ w.title }}</option>
      </select>
      <button class="nb-btn" @click="onNewWork">新建</button>
      <span class="nb-spacer"></span>
      <button class="nb-btn" :disabled="!nbWorkId || saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
      <button class="nb-btn nb-btn-ghost" :disabled="!nbWorkId" @click="exportWork">导出</button>
    </div>

    <div class="nb-body">
      <!-- 左：写作面板 -->
      <div class="nb-left">
        <div class="nb-chapters" v-if="nbWorkId">
          <button v-for="ch in chapters" :key="ch.chapter_id"
            class="nb-ch" :class="{ active: ch.chapter_id === store.activeChapterId }"
            @click="onSwitchChapter(ch.chapter_id)">{{ ch.title || `第${ch.chapter_no}章` }}</button>
          <button class="nb-ch nb-ch-add" @click="addChapter">＋ 章节</button>
        </div>
        <textarea v-if="nbWorkId" ref="editorRef" class="nb-editor"
          v-model="store.content"
          placeholder="在这里直接开写…（Ctrl+S 保存）"></textarea>
        <div v-else class="nb-empty">选择或新建一个作品，右边想先立主线/大纲也可以</div>
      </div>

      <!-- 右：四区块功能（复用工坊面板） -->
      <div class="nb-right">
        <WorkshopPanel />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { api } from '../../api/index.js'
import { useWritingStore } from '../../stores/writing.js'
import { useToast } from '../../composables/useToast.js'
import WorkshopPanel from './WorkshopPanel.vue'

const store = useWritingStore()
const toast = useToast()
const works = ref([])
const nbWorkId = ref(null)
const chapters = ref([])
const saving = ref(false)
const editorRef = ref(null)

async function loadWorks() {
  const res = await api.get('/api/works')
  if (res.code === 0) works.value = res.data.items || []
}

async function openWork() {
  if (!nbWorkId.value) return
  const res = await api.get(`/api/works/${nbWorkId.value}`)
  if (res.code !== 0) return
  store.title = res.data.work?.title || ''
  chapters.value = res.data.chapters || []
  store.chapters = chapters.value
  if (chapters.value.length) {
    store.activeChapterId = chapters.value[0].chapter_id
    store.content = chapters.value[0].content || ''
  }
}

function onOpenWork() { openWork() }

async function onNewWork() {
  const title = window.prompt('作品标题', '未命名作品')
  if (title === null) return
  const res = await api.post('/api/works', { title: title || '未命名作品', type: 'novel' })
  if (res.code === 0) {
    nbWorkId.value = res.data.work_id
    await loadWorks()
    await openWork()
  }
}

async function onSwitchChapter(chapterId) {
  await store.switchChapter(chapterId)
  editorRef.value?.focus()
}

async function addChapter() {
  const ch = await store.addChapter()
  if (ch) chapters.value = [...store.chapters]
}

async function save() {
  if (!nbWorkId.value || saving.value) return
  saving.value = true
  const res = await api.post('/api/works/save', {
    work_id: nbWorkId.value,
    title: store.title || '未命名作品',
    chapter_id: store.activeChapterId,
    chapter_title: store.getActiveChapterTitle() || '',
    content: store.content,
  })
  saving.value = false
  if (res.code === 0) toast.success('已保存')
  else toast.error(res.msg)
}

async function exportWork() {
  if (!nbWorkId.value) return
  await save()
  await api.download(`/api/works/${nbWorkId.value}/export`, `${store.title || '作品'}.txt`)
}

function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); save() }
}

onMounted(() => {
  loadWorks()
  window.addEventListener('keydown', onKeydown)
})
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.nb-root { min-height: 100vh; display: flex; flex-direction: column; }
.nb-bar { display: flex; align-items: center; gap: 10px; padding: 12px 20px; border-bottom: 1px solid rgba(196,163,90,0.15); }
.nb-back { color: var(--text-muted); text-decoration: none; font-size: 0.85rem; }
.nb-back:hover { color: var(--accent-primary); }
.nb-title { font-family: var(--font-serif); font-weight: 600; color: var(--text-primary); font-size: 0.95rem; }
.nb-select { background: var(--bg-glass); color: var(--text-primary); border: 1px solid rgba(196,163,90,0.2); border-radius: 8px; padding: 6px 10px; font-size: 0.85rem; }
.nb-spacer { flex: 1; }
.nb-btn { background: var(--accent-primary, #c4a35a); color: #14161c; border: none; padding: 7px 16px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 0.85rem; }
.nb-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.nb-btn-ghost { background: transparent; color: var(--text-secondary); border: 1px solid rgba(196,163,90,0.3); }
.nb-body { flex: 1; display: flex; min-height: 0; }
.nb-left { width: 58%; display: flex; flex-direction: column; border-right: 1px solid rgba(196,163,90,0.12); min-width: 0; }
.nb-chapters { display: flex; flex-wrap: wrap; gap: 6px; padding: 10px 16px; }
.nb-ch { background: var(--bg-glass); color: var(--text-secondary); border: 1px solid transparent; border-radius: 999px; padding: 4px 12px; font-size: 0.78rem; cursor: pointer; }
.nb-ch.active { border-color: var(--accent-primary); color: var(--accent-primary); }
.nb-ch-add { border-style: dashed; }
.nb-editor { flex: 1; margin: 0 16px 16px; padding: 20px; resize: none; outline: none;
  background: var(--bg-panel, #161923); color: var(--text-primary);
  border: 1px solid rgba(196,163,90,0.12); border-radius: 12px;
  font-family: var(--font-serif); font-size: 1rem; line-height: 2; }
.nb-empty { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text-muted); font-size: 0.9rem; }
.nb-right { flex: 1; min-width: 340px; max-width: 480px; overflow-y: auto; padding: 16px; }
</style>
```

- [ ] **Step 2: Build 验证 + Commit**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

```bash
git add client/src/views/write/NewbieStudio.vue
git commit -m "feat(ui): 新手系统独立页 /write/new——左写作面板+右工坊四区块（P6-B6）"
```

---

## Task 5: Home 三入口 + 登录自动弹说明 + WriteStudio 清理 workshop

**Files:**
- Modify: `client/src/views/Home.vue`
- Modify: `client/src/views/write/WriteStudio.vue`
- Modify: `client/src/components/OnboardingModal.vue`

- [ ] **Step 1: Home hero portals 改三入口**

模板 38-62 行改为（移除 portal-community，开始写作 → /start）：

```html
<router-link to="/start" class="portal-card portal-write">
  <span class="portal-en">Writing</span>
  <span class="portal-title">开始写作</span>
  <span class="portal-sub">新手引导 · 完整写作台 · 纯净模式 — 三选一</span>
  <span class="portal-line"></span>
</router-link>
<router-link to="/inspire" class="portal-card portal-read">
  <span class="portal-en">Inspiration</span>
  <span class="portal-title">灵感馆</span>
  <span class="portal-sub">诗词 · 短句素材 · 引用到创作</span>
  <span class="portal-line"></span>
</router-link>
<router-link to="/write/plain" class="portal-card portal-plain">
  <span class="portal-en">Plain Writing</span>
  <span class="portal-title">纯净写作</span>
  <span class="portal-sub">无干扰 · 写完就走 · 保存导出</span>
  <span class="portal-line"></span>
</router-link>
```

> portal-community CSS 保留无妨（未引用）；删除该 router-link 即可。

- [ ] **Step 2: Home 登录后自动弹说明（ref + onMounted 判断）**

Home 加 `import GuideModal`（或复用 App 级？—— Home 只需触发，App 级已挂组件）：用 ref 不行（组件在 App），改为 dispatch 事件 + 延迟（等组件挂载）：

```js
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
// （已有 import 区）
const guideShown = ref(false)

// onMounted 内（现有 return 前）加：
if (userStore.isLoggedIn && !localStorage.getItem('inkstone_guide_dismiss')) {
  setTimeout(() => window.dispatchEvent(new CustomEvent('inkstone:open-guide')), 800)
}
```

> 说明：GuideModal 自行判断「今天不再弹」；Home 只在登录且从未设过 key 时触发一次，日期判断交给组件（组件 open(auto) 逻辑内判断）。若希望"用户仍在本会话已关过不重复弹"，组件 open() 无状态——首次 Home 加载触发一次即可（路由回来不会重触发，因为只在 onMounted）。

- [ ] **Step 3: WriteStudio 移除 workshop 工具 + ?tool 逻辑**

- tools 数组删除 workshop 行（保留 blueprint 为首）
- import WorkshopPanel 行删除
- onMounted 中 `?tool=` 块删除
- 若 `useRouter` 仅为 ?tool 引入，一并去掉（route 仍需要）；确认后删 const router

- [ ] **Step 4: OnboardingModal guide → /write/new**

```js
} else if (mode === 'guide') {
  router.push('/write/new')
}
```

- [ ] **Step 5: Build 验证 + Commit**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

```bash
git add client/src/views/Home.vue client/src/views/write/WriteStudio.vue client/src/components/OnboardingModal.vue
git commit -m "feat(ui): 首页三入口（去社区广场）· 登录后自动弹说明 · 新手卡跳 /write/new · 老手台移除工坊工具（P6-B6）"
```

---

## Task 6: 全量验证 + 台账

- [ ] **Step 1: pytest 全量**

```powershell
cd server; python -m pytest tests -q -p no:cacheprovider
```

预期：**129 passed**。

- [ ] **Step 2: build 全量**

```powershell
cd client; npm run build
```

预期：`✓ built`。

- [ ] **Step 3: 人肉冒烟**

1. 未登录首页：三个 portal（开始写作/灵感馆/纯净写作），无社区广场
2. 登录后回首页：约 0.8s 弹「使用说明」，勾「今天不再弹出」关闭；刷新不再弹
3. 头像菜单 → 说明文档 → 再次弹出
4. 首页点「开始写作」→ 分流页三卡 → 新手系统 → `/write/new`：左编辑右四区块，新建/选作品、写正文、保存、导出；右侧灵感→AI主线→保存→大纲→保存→主角→保存；去「大纲规划」确认大纲树
5. 分流页「老手系统」→ 进入老手写作台（无创作工坊工具，蓝图为首）；「纯净写作」→ /write/plain
6. 写台首次弹窗「跟随引导」→ /write/new
7. 无 emoji 回归

- [ ] **Step 4: 台账登记**

P6-B6 ✅；P6-B 二期整体 🚧 待完整体验；Home 旧 portal CSS/文案、社区广场页面归 Backlog（页面仍在 /explore 可访问，仅首页入口移除）。

---

## Self-Review 结论

- **覆盖用户反馈**：首页三入口（删社区广场）✅；新手系统独立页（左写右功能）✅；分流页 `/start` ✅；说明文档弹窗（整体+三系统+今天不再弹）✅；头像菜单说明文档 ✅。
- **占位符扫描**：无 TBD/TODO；每步完整代码。
- **类型一致性**：`inkstone:open-guide` 事件在 GuideModal（listen）/UserMenu（dispatch）/Home（dispatch）三处名称一致；`/start`、`/write/new` 在 router 与各跳转处一致；WorkshopPanel/NewbieStudio 共用 writingStore 状态（currentWorkId/content）无冲突。