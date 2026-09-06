# P6-B4 写作台增强 实现计划（任务卡 AI + 卡壳了 + 四格降级）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 写作台三处增强：①任务卡支持「AI 生成本章剧情」+「写完提取要点（保存到本章 Beats）」；②编辑器加「卡壳了」按钮（读本章+作品上下文生成续写方向，可重新生成）；③立项蓝图四格降级为可选进阶（不再强制 Logline，次要字段收进「进阶设置」折叠区）。

**Architecture:** 纯前端接线，后端全部复用（批次 1 的 `/api/write/chapter-plot`、`/api/write/extract-points`、`/api/write/unstick`，以及现有 `/api/plan`、`/api/works`）。三个文件分别小改：
- `TaskCardPanel.vue`：加两个按钮 + AI 结果区 + 「保存为本章 Beats」写回 outline 树对应章节点（PUT /api/plan outline）
- `WriteStudio.vue`：编辑区加「卡壳了」浮动按钮 + 结果模态层（复用现有 find-modal 样式惯例）
- `BlueprintPanel.vue`：Logline 改非强制（提示"可稍后补"），audience/targetWords/deadline 收进折叠的「进阶设置」

**Tech Stack:** Vue3 + Pinia（writing store）+ api 封装；无后端改动。

**Spec:** `docs/superpowers/specs/2026-09-06-p6a-newcomer-onboarding-design.md` §5 二期；本计划为其批次 4（收官批）。

---

## 文件结构

| 文件 | 动作 | 职责 |
|---|---|---|
| `client/src/views/write/TaskCardPanel.vue` | Modify | AI 生成本章剧情 + 提取要点 + 保存到本章 Beats |
| `client/src/views/write/WriteStudio.vue` | Modify | 「卡壳了」按钮 + 结果模态 |
| `client/src/views/write/BlueprintPanel.vue` | Modify | 四格降级：Logline 可选 + 进阶折叠区 |

---

## Task 1: BlueprintPanel 四格降级可选进阶

**Files:**
- Modify: `client/src/views/write/BlueprintPanel.vue`

- [ ] **Step 1: 模板改——进阶设置折叠 + Logline 文案**

把模板 4-25 行替换为：

```html
      <p v-if="!workId" class="hint">💡 先在顶部「保存」一次作品（生成 work_id），即可为这本书立项。</p>
      <template v-else>
        <label class="field-label">一句话命题 Logline <span class="opt-tag">可稍后补</span></label>
        <textarea v-model="logline" rows="2" placeholder="例：一个少年为解开祖屋「灯的秘密」踏上旅程，最终发现光来自每一个被遗忘的人。"></textarea>
        <p class="hint small" v-if="!logline.trim()">没想好可以先跳过——写的过程中随时回来补。AI 续写/任务卡会在缺命题时更侧重你的实际文字。</p>

        <button class="btn btn-ghost btn-full" @click="advOpen = !advOpen">
          {{ advOpen ? '收起进阶设置 ▾' : '进阶设置 ▸（读者画像 / 字数 / 交稿日）' }}
        </button>
        <div v-if="advOpen" class="adv-box">
          <label class="field-label">目标读者画像</label>
          <input v-model="audience" placeholder="例：喜欢悬疑与家庭温情的中青年读者" />
          <div class="row">
            <div class="col">
              <label class="field-label">目标字数</label>
              <input v-model.number="targetWords" type="number" min="0" placeholder="80000" />
            </div>
            <div class="col">
              <label class="field-label">交稿日</label>
              <input v-model="deadline" type="date" />
            </div>
          </div>
        </div>

        <button class="btn btn-primary btn-full" @click="save" :disabled="saving">{{ saving ? '保存中…' : '保存立项蓝图' }}</button>
        <p class="hint small">之后到「三级大纲 / 设定库 / 角色设定」把骨架补全，大纲越具体，写作阶段 AI 越懂你想写什么。</p>
      </template>
```

- [ ] **Step 2: script 加 advOpen；save 不再强制 logline**

```js
const advOpen = ref(false)
```

`save()` 改为（原第 2 行校验删除，改为允许空保存）：

```js
async function save() {
  if (!workId.value) return
  saving.value = true
  const res = await api.put(`/api/plan/${workId.value}`, {
    logline: logline.value.trim(),
    audience: audience.value.trim(),
    target_words: targetWords.value || 0,
    deadline: deadline.value || null,
  })
  saving.value = false
  if (res.code === 0) toast.success('立项蓝图已保存')
  else toast.error(res.msg)
}
```

> `toast` 若不再使用需确认——save 成功后仍用 toast.success，保留 import 即可。

- [ ] **Step 3: 样式追加**

```css
.opt-tag { font-size: 0.7rem; color: var(--text-muted); border: 1px dashed var(--border-glass); padding: 1px 8px; border-radius: 999px; margin-left: 6px; font-weight: 400; }
.adv-box { margin: 4px 0 8px; padding: 4px 10px 8px; border: 1px dashed rgba(196,163,90,0.25); border-radius: 10px; }
```

- [ ] **Step 4: Build 验证**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

预期：`✓ built`，exit 0。

- [ ] **Step 5: Commit**

```bash
git add client/src/views/write/BlueprintPanel.vue
git commit -m "feat(ui): 立项蓝图四格降级可选进阶——Logline 可稍后补，读者/字数/交稿日收进折叠区（P6-B4）"
```

---

## Task 2: TaskCardPanel——AI 生成本章剧情 + 提取要点

**Files:**
- Modify: `client/src/views/write/TaskCardPanel.vue`

- [ ] **Step 1: 模板——在「去续写本章」按钮上方加 AI 区**

在第 38 行 `<button class="btn btn-primary btn-full" @click="gotoContinue">✍ 去续写本章</button>` 之前插入：

```html
        <div class="ai-zone">
          <div class="ai-zone-head">
            <span class="ai-zone-label">🤖 AI 搭把手</span>
            <button class="btn btn-ghost btn-sm" @click="genPlot" :disabled="plotLoading">{{ plotLoading ? '生成中…' : '✨ 生成本章剧情' }}</button>
            <button class="btn btn-ghost btn-sm" @click="extractPoints" :disabled="extractLoading || !writingStore.content.trim()">{{ extractLoading ? '提取中…' : '📋 写完提取要点' }}</button>
          </div>

          <div v-if="aiResult" class="ai-result">
            <p class="ai-result-text">{{ aiResult }}</p>
            <div class="ai-result-actions">
              <button v-if="aiMode === 'extract'" class="btn btn-primary btn-sm" @click="saveBeats" :disabled="savingBeats">{{ savingBeats ? '保存中…' : '保存为本章 Beats' }}</button>
              <button class="btn btn-ghost btn-sm" @click="aiResult = ''">关闭</button>
            </div>
          </div>
        </div>
```

- [ ] **Step 2: script——状态 + 三个动作**

在 `<script setup>` 中补充：

```js
// ---- P6-B4：任务卡 AI 搭把手 ----
const plotLoading = ref(false)
const extractLoading = ref(false)
const savingBeats = ref(false)
const aiResult = ref('')
const aiMode = ref('')  // 'plot' | 'extract'

const mainline = computed(() => {
  const p = planOutline.value
  return '' // 占位，下方 loadPlan 时写入 planMainline
})
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
```

- [ ] **Step 3: load() 里补 planMainline 读取**

`load()` 中 `planOutline.value = p.data.plan?.outline || []` 之后补：

```js
  planMainline.value = p.data.plan?.logline || ''
```

- [ ] **Step 4: import 补充 + 去除重复**

确认 script 顶部 import 含 `toast`（从 useToast），并新增：

```js
import { useToast } from '../../composables/useToast.js'
const toast = useToast()
```

> `mainline` computed 占位若未使用，删除以保持整洁（genPlot 直接用 planMainline.value）。

- [ ] **Step 5: 样式追加**

```css
.ai-zone { margin-top: 10px; padding-top: 10px; border-top: 1px dashed rgba(196,163,90,0.25); }
.ai-zone-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.ai-zone-label { font-size: 0.74rem; color: var(--accent-primary); }
.ai-result { padding: 10px 12px; border-radius: 10px; background: rgba(196,163,90,0.08); border: 1px solid rgba(196,163,90,0.25); }
.ai-result-text { font-size: 0.82rem; line-height: 1.8; color: var(--text-secondary); margin: 0 0 8px; white-space: pre-wrap; }
.ai-result-actions { display: flex; justify-content: flex-end; gap: 8px; }
```

- [ ] **Step 6: Build 验证**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

预期：`✓ built`，exit 0。

- [ ] **Step 7: Commit**

```bash
git add client/src/views/write/TaskCardPanel.vue
git commit -m "feat(ui): 任务卡 AI 搭把手——生成本章剧情 + 写完提取要点 + 保存为本章 Beats（P6-B4）"
```

---

## Task 3: WriteStudio「卡壳了」按钮 + 结果模态

**Files:**
- Modify: `client/src/views/write/WriteStudio.vue`

- [ ] **Step 1: 模板——editor-panel 里 float-find-btn 旁加「卡壳了」按钮（第 95-97 行区域）**

```html
        <!-- 快捷找句入口 -->
        <button class="float-find-btn" title="按意境找句" @click="openFindLines('')">
          <span class="ffb-ico">✦</span>找句
        </button>
        <!-- 卡壳了：让 AI 给续写方向 -->
        <button class="float-unstick-btn" title="写不下去了？让 AI 给你接下去的方向" @click="openUnstick" :disabled="unstickLoading || !writingStore.content.trim()">
          <span class="ffb-ico">😮‍💨</span>{{ unstickLoading ? 'AI 思考中…' : '卡壳了' }}
        </button>
```

- [ ] **Step 2: 模板——find-modal 之后加 unstick 模态**

在第 107 行（find-modal 关闭 div）之后插入：

```html
        <!-- 卡壳了模态 -->
        <div v-if="unstickOpen" class="modal-overlay" @click.self="closeUnstick">
          <div class="modal unstick-modal">
            <div class="find-modal-head">
              <h3 class="find-modal-title">😮‍💨 卡壳了？接下来可以写…</h3>
              <button class="find-modal-close" @click="closeUnstick">✕</button>
            </div>
            <p v-if="unstickResult" class="unstick-text">{{ unstickResult }}</p>
            <p v-else class="unstick-loading">AI 正在读你写到哪里、前情是什么，稍等…</p>
            <div class="unstick-actions">
              <button class="btn btn-ghost btn-sm" @click="genUnstick" :disabled="unstickLoading || !writingStore.content.trim()">⟳ 换一批方向</button>
              <button class="btn btn-primary btn-sm" @click="closeUnstick">回到编辑</button>
            </div>
          </div>
        </div>
```

- [ ] **Step 3: script——状态与动作**

```js
// ---- P6-B4：卡壳了 ----
const unstickOpen = ref(false)
const unstickLoading = ref(false)
const unstickResult = ref('')

function openUnstick() {
  if (!writingStore.content.trim()) return
  unstickOpen.value = true
  unstickResult.value = ''
  genUnstick()
}

function closeUnstick() {
  if (unstickLoading.value) return
  unstickOpen.value = false
}

async function genUnstick() {
  unstickLoading.value = true
  unstickResult.value = ''
  const res = await api.post('/api/write/unstick', {
    content: writingStore.content.trim(),
    work_id: writingStore.currentWorkId,
  })
  unstickLoading.value = false
  if (res.code === 0) unstickResult.value = res.data.suggestions
  else { toast.error(res.msg); unstickOpen.value = false }
}
```

> 确认 WriteStudio script 已 import ref / api / toast（是），无需新增 import。

- [ ] **Step 4: 样式追加**

```css
.float-unstick-btn {
  position: absolute; right: 64px; bottom: 16px; z-index: 5;
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 0.8rem; padding: 8px 14px; border-radius: 999px;
  background: rgba(196,163,90,0.12); border: 1px solid rgba(196,163,90,0.35);
  color: var(--accent-primary); cursor: pointer; transition: all 0.15s;
}
.float-unstick-btn:hover:not(:disabled) { background: rgba(196,163,90,0.22); }
.float-unstick-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.unstick-modal { width: min(520px, 92vw); }
.unstick-text { font-size: 0.88rem; line-height: 1.9; color: var(--text-secondary); white-space: pre-wrap; margin: 0 0 10px; }
.unstick-loading { font-size: 0.82rem; color: var(--text-muted); margin: 0 0 10px; }
.unstick-actions { display: flex; justify-content: flex-end; gap: 8px; }
```

> 若 `.float-find-btn` 是 absolute 定位（需确认现有样式），新按钮同规则；若是 static，则包一层或改 flex。实现时对照现有样式决定。

- [ ] **Step 5: Build 验证**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

预期：`✓ built`，exit 0。

- [ ] **Step 6: Commit**

```bash
git add client/src/views/write/WriteStudio.vue
git commit -m "feat(ui): 编辑器「卡壳了」按钮——读本章+作品上下文生成续写方向，可换一批（P6-B4）"
```

---

## Task 4: 全量验证 + 收尾登记

**Files:** 无（仅验证）

- [ ] **Step 1: pytest 全量（后端零改动，应无回归）**

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

1. 立项蓝图：不填 Logline 直接保存 → 成功；「进阶设置」折叠可展开；填全后保存成功
2. 任务卡：有一章 + 大纲树的场景下点「✨ 生成本章剧情」→ AI 结果出现 → 可关闭；点「📋 写完提取要点」→ 若本章有内容出结果 → 点「保存为本章 Beats」→ 大纲树对应章有 Beats 文本；无大纲节点时提示去加章节
3. 卡壳了：编辑器写几行 → 点「卡壳了」→ 模态出现 → AI 给方向 → 「换一批」重新生成 → 关闭回编辑
4. 老路径不回归：找句按钮、专注模式、面板切换正常

- [ ] **Step 4: 台账登记 + commit**

`docs/改造进度.md`：P6-B4 标记 ✅（pytest 129 / build 绿 / 冒烟待体验）；P6-B 二期整体标记 🚧「功能全部落地，待需求方完整体验」；Backlog 无需新增。

---

## Self-Review 结论

- **Spec 覆盖**：二期「任务卡 AI 生成本章剧情 + 提取要点」→ Task 2 ✅；「编辑器卡壳了按钮」→ Task 3 ✅；「原四格降级可选进阶」→ Task 1 ✅。至此二期 P6-B 全部 7 项功能落地（批次 1-4）。
- **占位符扫描**：无 TBD/TODO；每步完整代码；两处"对照现有实现确认"（float-find-btn 定位、toast import 现状）为适配核对项，非占位。
- **类型一致性**：`/api/write/chapter-plot`（work_id/mainline/chapter_no → plot）、`/api/write/extract-points`（content/chapter_title → points）、`/api/write/unstick`（content/work_id → suggestions）与 P6-B1 端点契约一致；plan PUT 的 logline/outline 与 plans.py 一致；`flatChapters`/`chapterNo` 为 TaskCardPanel 既有函数，直接复用。