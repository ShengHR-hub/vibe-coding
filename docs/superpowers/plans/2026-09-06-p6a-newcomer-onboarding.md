# P6-A 新手入口引导 + 纯净写作 + 闪念便签 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成墨池一期：首次进写作台弹出「从哪开始？」使用说明弹窗（新手/老手/纯净三选一，选择存 localStorage）、新增 `/write/plain` 纯净写作页（标题+章节+编辑区+保存+导出，无任何 AI 面板）、主页「纯净写作」入口、写作台右下角闪念便签（新表 user_notes + CRUD + 悬浮面板 + Ctrl+Shift+N 快捷键）。

**Architecture:** 后端新增 notes 蓝图（4 端点，参数化 SQL + 仅本人权限，复用 inspire.py 模式）；schema.sql 追加 user_notes 表；前端新增 OnboardingModal.vue / PlainWrite.vue / NotesFloat.vue 三个组件，WriteStudio 挂载弹窗与便签，router 注册新路由，Home 加入口卡片。数据互通走现有 works/chapters API 与 writingStore，不新建业务表。

**Tech Stack:** Flask + PyMySQL（query/execute）、Vue3 + Pinia（writingStore）、Vite、pytest(inkstone_test)。

**Spec:** `docs/superpowers/specs/2026-09-06-p6a-newcomer-onboarding-design.md`

---

## 文件结构

| 文件 | 动作 | 职责 |
|---|---|---|
| `server/database/schema.sql` | Modify（追加 28 号表） | user_notes 表 DDL |
| `server/routes/notes.py` | Create | 便签 CRUD 4 端点（仅本人） |
| `server/routes/__init__.py` | Modify | 注册 notes_bp（url_prefix=/api/notes） |
| `server/tests/test_notes.py` | Create | 便签端点测试（登录/CRUD/越权/长度） |
| `client/src/components/OnboardingModal.vue` | Create | 使用说明弹窗（三模式选择） |
| `client/src/views/write/PlainWrite.vue` | Create | 纯净写作页 |
| `client/src/components/NotesFloat.vue` | Create | 便签悬浮面板 |
| `client/src/views/write/WriteStudio.vue` | Modify | 挂载 OnboardingModal + NotesFloat |
| `client/src/router/index.js` | Modify | 注册 /write/plain 路由 |
| `client/src/views/Home.vue` | Modify | Hero 区加纯净写作入口 |

---

## Task 1: user_notes 表（schema.sql）

**Files:**
- Modify: `server/database/schema.sql`（末尾追加）

- [ ] **Step 1: schema.sql 末尾追加 user_notes 表**

在 `server/database/schema.sql` 末尾（book_plans 之后）追加：

```sql
-- 28. 闪念便签表（P6-A：用户随时记录灵感片段，仅本人可见）
CREATE TABLE user_notes (
    note_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_notes_user (user_id),
    CONSTRAINT user_notes_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

- [ ] **Step 2: 开发库幂等补表（不碰测试库）**

```powershell
mysql -u root -p123456 inkstone -e "CREATE TABLE IF NOT EXISTS user_notes (
    note_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_notes_user (user_id),
    CONSTRAINT user_notes_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
```

预期：`Query OK, 0 rows affected`（幂等，重复执行不报错）。

- [ ] **Step 3: 验证表已建**

```powershell
mysql -u root -p123456 inkstone -e "SHOW TABLES LIKE 'user_notes';"
```

预期：输出 `user_notes`。

- [ ] **Step 4: Commit**

```bash
git add server/database/schema.sql
git commit -m "feat(db): 新增 user_notes 闪念便签表（P6-A）"
```

---

## Task 2: notes 蓝图 —— 便签 CRUD 端点

**Files:**
- Create: `server/routes/notes.py`
- Modify: `server/routes/__init__.py`

- [ ] **Step 1: 创建 notes.py**

参照 `routes/inspire.py` 的既有模式（Blueprint + @login_required + ok/fail + 参数化 SQL），创建 `server/routes/notes.py`：

```python
"""闪念便签（P6-A）：用户随时记录灵感片段，仅本人可读写。"""
from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, login_required, _fmt

notes_bp = Blueprint('notes', __name__)

_MAX_LEN = 2000


def _get_own_note(note_id):
    """取本人便签，不存在或非本人返回 None（防越权统一走 404）。"""
    return query(
        'SELECT note_id FROM user_notes WHERE note_id = %s AND user_id = %s',
        (note_id, session['user_id']), one=True)


@notes_bp.get('')
@login_required
def list_notes():
    rows = query(
        'SELECT note_id, content, created_at, updated_at FROM user_notes '
        'WHERE user_id = %s ORDER BY updated_at DESC',
        (session['user_id'],),
    )
    items = [{
        'note_id': r['note_id'],
        'content': r['content'],
        'created_at': _fmt(r['created_at']),
        'updated_at': _fmt(r['updated_at']),
    } for r in rows]
    return ok({'items': items})


@notes_bp.post('')
@login_required
def create_note():
    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    if not content:
        return fail('内容不能为空')
    if len(content) > _MAX_LEN:
        return fail(f'内容过长（最多 {_MAX_LEN} 字）')
    note_id = execute(
        'INSERT INTO user_notes (user_id, content) VALUES (%s, %s)',
        (session['user_id'], content),
    )
    return ok({'note_id': note_id}, msg='已保存便签')


@notes_bp.put('/<int:note_id>')
@login_required
def update_note(note_id):
    if not _get_own_note(note_id):
        return fail('便签不存在', code=404)
    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    if not content:
        return fail('内容不能为空')
    if len(content) > _MAX_LEN:
        return fail(f'内容过长（最多 {_MAX_LEN} 字）')
    execute(
        'UPDATE user_notes SET content = %s WHERE note_id = %s AND user_id = %s',
        (content, note_id, session['user_id']),
    )
    return ok(msg='已更新便签')


@notes_bp.delete('/<int:note_id>')
@login_required
def delete_note(note_id):
    if not _get_own_note(note_id):
        return fail('便签不存在', code=404)
    execute('DELETE FROM user_notes WHERE note_id = %s AND user_id = %s',
            (note_id, session['user_id']))
    return ok(msg='已删除便签')
```

- [ ] **Step 2: 注册蓝图**

修改 `server/routes/__init__.py`：
- 在 `from routes.plans import plan_bp` 后加一行 `from routes.notes import notes_bp`
- 在 `app.register_blueprint(plan_bp, url_prefix='/api/plan')` 后加一行 `app.register_blueprint(notes_bp, url_prefix='/api/notes')`

- [ ] **Step 3: 后端启动自检**

```powershell
cd server; python -c "from app import create_app; app = create_app(); print([str(r) for r in app.url_map.iter_rules() if 'notes' in str(r)])"
```

预期：输出 4 条 `/api/notes` 相关路由（GET/POST/''、PUT/<id>、DELETE/<id>）。

- [ ] **Step 4: Commit**

```bash
git add server/routes/notes.py server/routes/__init__.py
git commit -m "feat(write): 闪念便签 CRUD 端点（仅本人，参数化，P6-A）"
```

---

## Task 3: notes 端点测试

**Files:**
- Create: `server/tests/test_notes.py`

- [ ] **Step 1: 写测试**

参照 `tests/conftest.py` 的 `client`/`auth_client` fixture 与 `tests/test_write_quick_actions.py` 的校验风格（`r.get_json()['code']`，注意登录失败是 HTTP 200 + body code=401），创建 `server/tests/test_notes.py`：

```python
"""闪念便签端点测试（P6-A）：登录/CRUD/越权/长度，走 inkstone_test，零 AI token。"""
import pytest


def _mk_notes(client, *contents):
    ids = []
    for c in contents:
        r = client.post('/api/notes', json={'content': c})
        assert r.get_json()['code'] == 0
        ids.append(r.get_json()['data']['note_id'])
    return ids


def test_notes_requires_login(client):
    r = client.get('/api/notes')
    assert r.get_json()['code'] == 401


def test_notes_create_and_list(auth_client):
    note_id = _mk_notes(auth_client, '主角左手的伤疤是个伏笔')[0]
    r = auth_client.get('/api/notes')
    assert r.get_json()['code'] == 0
    items = r.get_json()['data']['items']
    assert len(items) == 1
    assert items[0]['note_id'] == note_id
    assert items[0]['content'] == '主角左手的伤疤是个伏笔'


def test_notes_order_desc(auth_client):
    _mk_notes(auth_client, '第一条', '第二条')
    r = auth_client.get('/api/notes')
    items = r.get_json()['data']['items']
    assert len(items) == 2
    # 列表按 updated_at DESC（同一秒内并列时无稳定序），只验证两条都在
    contents = {i['content'] for i in items}
    assert contents == {'第一条', '第二条'}


def test_notes_update_own(auth_client):
    note_id = _mk_notes(auth_client, '旧想法')[0]
    r = auth_client.put(f'/api/notes/{note_id}', json={'content': '新想法'})
    assert r.get_json()['code'] == 0
    items = auth_client.get('/api/notes').get_json()['data']['items']
    assert items[0]['content'] == '新想法'


def test_notes_delete_own(auth_client):
    note_id = _mk_notes(auth_client, '要删的')[0]
    r = auth_client.delete(f'/api/notes/{note_id}')
    assert r.get_json()['code'] == 0
    items = auth_client.get('/api/notes').get_json()['data']['items']
    assert items == []


def test_notes_cannot_touch_others(auth_client, client):
    note_id = _mk_notes(auth_client, '别人的便签')[0]
    # 第二个用户登录
    client.post('/api/auth/register', json={'username': 'other', 'password': 'test123456'})
    client.post('/api/auth/login', json={'username': 'other', 'password': 'test123456'})
    assert client.put(f'/api/notes/{note_id}', json={'content': '篡改'}).get_json()['code'] == 404
    assert client.delete(f'/api/notes/{note_id}').get_json()['code'] == 404


def test_notes_validation(auth_client):
    assert auth_client.post('/api/notes', json={'content': ''}).get_json()['code'] != 0
    assert auth_client.post('/api/notes', json={'content': '   '}).get_json()['code'] != 0
    long_text = '字' * 2001
    assert auth_client.post('/api/notes', json={'content': long_text}).get_json()['code'] != 0
```

- [ ] **Step 2: 运行测试**

```powershell
cd server; python -m pytest tests/test_notes.py -q -p no:cacheprovider
```

预期：7 passed（含 test_notes_cannot_touch_others 若注册/登录受限速影响则先确认 conftest 已清限速——已清，无需处理）。

- [ ] **Step 3: 全量回归**

```powershell
cd server; python -m pytest tests -q -p no:cacheprovider
```

预期：107 + 7 = **114 passed**，exit 0。

- [ ] **Step 4: Commit**

```bash
git add server/tests/test_notes.py
git commit -m "test(notes): 便签端点 7 用例（登录/CRUD/越权/长度），pytest 114 passed"
```

---

## Task 4: OnboardingModal —— 使用说明弹窗

**Files:**
- Create: `client/src/components/OnboardingModal.vue`

- [ ] **Step 1: 创建组件**

模态层复用 WriteStudio 现有 `.modal-overlay`/`.modal` 结构风格，创建 `client/src/components/OnboardingModal.vue`：

```vue
<template>
  <Teleport to="body">
    <div v-if="visible" class="ob-overlay" @click.self="close">
      <div class="ob-card">
        <div class="ob-head">
          <h3 class="ob-title">从哪开始？</h3>
          <button class="ob-close" @click="close">✕</button>
        </div>
        <p class="ob-desc">写书第一步：先接住你心里那个"想写的东西"。选一条路开始——以后随时可从右上角「说明」重新进入。</p>
        <div class="ob-options">
          <button class="ob-opt" @click="choose('guide')">
            <span class="ob-opt-ico">🧭</span>
            <span class="ob-opt-name">跟随引导（新手）</span>
            <span class="ob-opt-sub">一步步完成灵感 → 主线 → 大纲 → 动笔</span>
          </button>
          <button class="ob-opt" @click="choose('pro')">
            <span class="ob-opt-ico">✍</span>
            <span class="ob-opt-name">直接开始（老手）</span>
            <span class="ob-opt-sub">用完整写作台：面板 + AI + 素材引用</span>
          </button>
          <button class="ob-opt" @click="choose('plain')">
            <span class="ob-opt-ico">🌙</span>
            <span class="ob-opt-name">只想安静写</span>
            <span class="ob-opt-sub">纯净页面：只有写作、保存、导出</span>
          </button>
        </div>
        <p class="ob-foot">说明详文制作中 · 锚点占位：<a href="#/write" @click.prevent="close">帮助文档</a></p>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const visible = ref(false)
const router = useRouter()

const MODE_KEY = 'inkstone_mode'

function open() { visible.value = true }
function close() { visible.value = false }
defineExpose({ open })

function choose(mode) {
  localStorage.setItem(MODE_KEY, mode)
  visible.value = false
  if (mode === 'plain') {
    router.push('/write/plain')
  } else if (mode === 'guide') {
    // 二期创作工坊占位：暂无独立页，先留写作台并提示
    window.dispatchEvent(new CustomEvent('inkstone:toast', { detail: { type: 'info', text: '创作工坊正在建设中，先带你到写作台' } }))
  }
  // pro：留在当前写作台
}
</script>

<style scoped>
.ob-overlay {
  position: fixed; inset: 0; z-index: 900;
  display: flex; align-items: center; justify-content: center;
  background: rgba(10, 12, 20, 0.6); backdrop-filter: blur(4px);
}
.ob-card {
  width: min(480px, 92vw); padding: 22px 24px; border-radius: 16px;
  background: var(--bg-panel, #1a1c24); border: 1px solid rgba(196, 163, 90, 0.25);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
}
.ob-head { display: flex; justify-content: space-between; align-items: center; }
.ob-title { font-family: var(--font-serif); margin: 0; font-size: 1.2rem; }
.ob-close { background: none; border: none; color: var(--text-muted); font-size: 1rem; cursor: pointer; }
.ob-desc { color: var(--text-secondary); font-size: 0.85rem; line-height: 1.8; }
.ob-options { display: flex; flex-direction: column; gap: 10px; margin-top: 6px; }
.ob-opt {
  display: flex; align-items: center; gap: 12px; text-align: left;
  padding: 12px 14px; border-radius: 12px; cursor: pointer;
  background: var(--bg-glass); border: 1px solid transparent; color: var(--text-primary);
  transition: all 0.15s;
}
.ob-opt:hover { border-color: rgba(196, 163, 90, 0.5); background: rgba(196, 163, 90, 0.1); }
.ob-opt-ico { font-size: 1.3rem; }
.ob-opt-name { font-weight: 600; font-size: 0.92rem; }
.ob-opt-sub { display: block; color: var(--text-muted); font-size: 0.78rem; margin-top: 2px; }
.ob-foot { color: var(--text-muted); font-size: 0.75rem; margin: 14px 0 0; }
.ob-foot a { color: var(--accent-primary); }
</style>
```

> 说明：`inkstone:toast` 事件为现有 toast 体系占位（若项目无该事件名则 Choose guide 分支直接无害关闭，二期再做真跳转）。

- [ ] **Step 2: 验证组件无语法错误（前端 build 在后续 Task 统一验证）**

- [ ] **Step 3: Commit**

```bash
git add client/src/components/OnboardingModal.vue
git commit -m "feat(ui): 使用说明弹窗 OnboardingModal（新手/老手/纯净三选一，P6-A）"
```

---

## Task 5: WriteStudio 挂载 OnboardingModal + 说明入口

**Files:**
- Modify: `client/src/views/write/WriteStudio.vue`

- [ ] **Step 1: 引入并挂载**

- 在 `<script setup>` 的组件 import 区加：`import OnboardingModal from '../../components/OnboardingModal.vue'`
- 在 template 末尾（`</template>` 前）加：

```html
    <OnboardingModal ref="onboardingRef" />
```

- 在 script 中加：

```js
const onboardingRef = ref(null)

// 首次进入弹出说明，选择结果存 localStorage（inkstone_mode），可手动重开
onMounted(() => {
  window.addEventListener('inkstone:goto-tool', onGotoTool)
  if (!localStorage.getItem('inkstone_mode')) {
    onboardingRef.value?.open()
  }
})
```

> 注意：现有 `onMounted` 已有内容（监听 goto-tool），合并进去，不要重复注册第二个 onMounted。

- [ ] **Step 2: 右上角加「说明」重开入口**

在 header-right 区（PomodoroTimer 前）加入：

```html
<button class="header-btn" title="使用说明 / 模式选择" @click="onboardingRef?.open()">?</button>
```

- [ ] **Step 3: Build 验证**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

预期：`✓ built`，exit 0。

- [ ] **Step 4: Commit**

```bash
git add client/src/views/write/WriteStudio.vue
git commit -m "feat(ui): 写作台挂载使用说明弹窗 + 右上角说明入口（P6-A）"
```

---

## Task 6: PlainWrite.vue —— 纯净写作页

**Files:**
- Create: `client/src/views/write/PlainWrite.vue`
- Modify: `client/src/router/index.js`

- [ ] **Step 1: 创建纯净写作页**

核心逻辑：打开/新建作品 → 章节下拉切换 → 编辑 → 保存（`POST /api/works/save`）→ 导出（`GET /api/works/:id/export` 走 `api.download`）。复用 writingStore 保证与写作台数据互通：

```vue
<template>
  <div class="plain-root">
    <div class="plain-bar">
      <span class="plain-logo">墨池 · 纯净写作</span>
      <select v-model="workId" class="plain-select" @change="onOpenWork">
        <option :value="null" disabled>选择作品…</option>
        <option v-for="w in works" :key="w.work_id" :value="w.work_id">{{ w.title }}</option>
      </select>
      <button class="plain-btn" @click="onNewWork">＋ 新建</button>
      <span class="plain-spacer"></span>
      <button class="plain-btn" :disabled="!workId || saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
      <button class="plain-btn plain-btn-ghost" :disabled="!workId" @click="exportWork">导出</button>
    </div>

    <div class="plain-chapters" v-if="workId">
      <button
        v-for="ch in chapters" :key="ch.chapter_id"
        class="plain-ch" :class="{ active: ch.chapter_id === activeChapterId }"
        @click="onSwitchChapter(ch.chapter_id)"
      >{{ ch.title || `第${ch.chapter_no}章` }}</button>
      <button class="plain-ch plain-ch-add" @click="addChapter">＋ 章节</button>
    </div>

    <textarea
      v-if="workId" ref="editorRef" class="plain-editor"
      v-model="store.content"
      :placeholder="'在这里安静写作…（Ctrl+S 保存）'"
    ></textarea>
    <div v-else class="plain-empty">选择或新建一个作品开始写作</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { api } from '../../api/index.js'
import { useWritingStore } from '../../stores/writing.js'

const store = useWritingStore()
const works = ref([])
const workId = ref(null)
const chapters = ref([])
const activeChapterId = ref(null)
const saving = ref(false)
const editorRef = ref(null)

async function loadWorks() {
  const res = await api.get('/api/works')
  if (res.code === 0) works.value = res.data.items || []
}

async function openWork() {
  if (!workId.value) return
  const res = await api.get(`/api/works/${workId.value}`)
  if (res.code !== 0) return
  store.title = res.data.work?.title || ''
  chapters.value = res.data.chapters || []
  store.reset()
  store.chapters = chapters.value
  if (chapters.value.length) {
    activeChapterId.value = chapters.value[0].chapter_id
    store.activeChapterId = activeChapterId.value
    store.content = chapters.value[0].content || ''
  }
}

function onOpenWork() { openWork() }

async function onNewWork() {
  const title = prompt('作品标题', '未命名作品')
  if (title === null) return
  const res = await api.post('/api/works', { title: title || '未命名作品', type: 'novel', summary: '', content: '' })
  if (res.code === 0) {
    workId.value = res.data.work_id
    await loadWorks()
    await openWork()
  }
}

async function onSwitchChapter(chapterId) {
  await store.switchChapter(chapterId)
  activeChapterId.value = chapterId
  editorRef.value?.focus()
}

async function addChapter() {
  const ch = await store.addChapter()
  if (ch) {
    chapters.value = [...store.chapters]
    activeChapterId.value = ch.chapter_id
  }
}

async function save() {
  if (!workId.value) return
  saving.value = true
  const res = await api.post('/api/works/save', {
    work_id: workId.value,
    title: store.title || '未命名作品',
    chapter_id: store.activeChapterId,
    chapter_title: store.getActiveChapterTitle() || '',
    content: store.content,
  })
  saving.value = false
  if (res.code === 0) {
    const wc = (store.content || '').replace(/\s/g, '').length
    const ch = chapters.value.find(c => c.chapter_id === store.activeChapterId)
    if (ch) ch.word_count = wc
  } else {
    window.dispatchEvent(new CustomEvent('inkstone:toast', { detail: { type: 'error', text: res.msg } }))
  }
}

async function exportWork() {
  if (!workId.value) return
  await save()
  await api.download(`/api/works/${workId.value}/export`, `${store.title || '作品'}.txt`)
}

function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    save()
  }
}

onMounted(() => {
  loadWorks()
  window.addEventListener('keydown', onKeydown)
})
onUnmounted(() => {
  store.reset()
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.plain-root { min-height: 100vh; display: flex; flex-direction: column; background: var(--bg-base, #10131a); }
.plain-bar {
  display: flex; align-items: center; gap: 10px; padding: 12px 20px;
  border-bottom: 1px solid rgba(196, 163, 90, 0.15);
}
.plain-logo { font-family: var(--font-serif); color: var(--accent-secondary); font-weight: 600; font-size: 0.92rem; }
.plain-select {
  background: var(--bg-glass); color: var(--text-primary); border: 1px solid rgba(196, 163, 90, 0.2);
  border-radius: 8px; padding: 6px 10px; font-size: 0.85rem;
}
.plain-spacer { flex: 1; }
.plain-btn {
  background: var(--accent-primary, #c4a35a); color: #14161c; border: none;
  padding: 7px 16px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 0.85rem;
}
.plain-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.plain-btn-ghost { background: transparent; color: var(--text-secondary); border: 1px solid rgba(196,163,90,0.3); }
.plain-chapters { display: flex; flex-wrap: wrap; gap: 6px; padding: 10px 20px; }
.plain-ch {
  background: var(--bg-glass); color: var(--text-secondary); border: 1px solid transparent;
  border-radius: 999px; padding: 5px 14px; font-size: 0.8rem; cursor: pointer;
}
.plain-ch.active { border-color: var(--accent-primary); color: var(--accent-primary); }
.plain-ch-add { border-style: dashed; }
.plain-editor {
  flex: 1; margin: 0 20px 20px; padding: 24px; resize: none; outline: none;
  background: var(--bg-panel, #161923); color: var(--text-primary);
  border: 1px solid rgba(196, 163, 90, 0.12); border-radius: 14px;
  font-family: var(--font-serif); font-size: 1.02rem; line-height: 2;
}
.plain-empty { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text-muted); }
</style>
```

> 说明：`store.reset()` 后直接赋值 `store.chapters/store.activeChapterId/store.content`——writingStore 这些是 ref，setup 内部写法为 `store.xxx = value` 可直接写（Pinia store 实例属性可写）。若 build 时报只读，改为调用 store 现有方法（`store.loadChapters(workId)` + `store.switchChapter`）并本地同步 chapters 数组。

- [ ] **Step 2: 注册路由**

修改 `client/src/router/index.js`，在 `/write` 路由后加：

```js
{ path: '/write/plain', name: 'PlainWrite', component: () => import('../views/write/PlainWrite.vue'), meta: { auth: true } },
```

- [ ] **Step 3: Build 验证**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

预期：`✓ built`，exit 0。

- [ ] **Step 4: Commit**

```bash
git add client/src/views/write/PlainWrite.vue client/src/router/index.js
git commit -m "feat(ui): 纯净写作页 /write/plain（标题+章节+编辑+保存+导出，Ctrl+S，P6-A）"
```

---

## Task 7: Home 纯净写作入口

**Files:**
- Modify: `client/src/views/Home.vue`

- [ ] **Step 1: Hero portal 补纯净写作卡片**

在 hero-portals 区（`portal-community` 之后）追加（视觉上保持四卡或加上后自动换行的协调风格）：

```html
<router-link to="/write/plain" class="portal-card portal-plain">
  <span class="portal-en">Plain Writing</span>
  <span class="portal-title">纯净写作</span>
  <span class="portal-sub">无干扰 · 写完就走 · 保存导出</span>
  <span class="portal-line"></span>
</router-link>
```

并在 `<style>` 中为新卡片补与现有 portal 一致的样式（`.portal-plain` 复用 `.portal-card` 基类，必要时仅调整 hover 边框色，参考现有 `.portal-write`）。

- [ ] **Step 2: Build 验证**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

预期：`✓ built`，exit 0。

- [ ] **Step 3: Commit**

```bash
git add client/src/views/Home.vue
git commit -m "feat(ui): 主页新增纯净写作入口卡片（P6-A）"
```

---

## Task 8: NotesFloat —— 写作台闪念便签悬浮面板

**Files:**
- Create: `client/src/components/NotesFloat.vue`
- Modify: `client/src/views/write/WriteStudio.vue`

- [ ] **Step 1: 创建便签组件**

```vue
<template>
  <div class="nf-root">
    <button class="nf-fab" title="闪念便签 (Ctrl+Shift+N)" @click="toggle">
      📝
    </button>
    <div v-if="open" class="nf-panel">
      <div class="nf-head">
        <span class="nf-title">闪念便签</span>
        <button class="nf-close" @click="open = false">✕</button>
      </div>
      <div class="nf-list">
        <div v-for="n in notes" :key="n.note_id" class="nf-item">
          <p class="nf-text">{{ n.content }}</p>
          <div class="nf-item-foot">
            <span class="nf-time">{{ n.updated_at?.slice(5, 16) }}</span>
            <button class="nf-del" @click="del(n.note_id)">删除</button>
          </div>
        </div>
        <p v-if="!notes.length" class="nf-empty">想到什么好点子，随手记在这里——不怕忘。</p>
      </div>
      <div class="nf-input-row">
        <textarea v-model="draft" rows="2" class="nf-input" placeholder="记一个闪念…（Enter 保存，Shift+Enter 换行）" @keydown.enter.exact.prevent="add"></textarea>
        <button class="nf-add" :disabled="!draft.trim() || saving" @click="add">记下</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { api } from '../api/index.js'

const open = ref(false)
const notes = ref([])
const draft = ref('')
const saving = ref(false)

async function load() {
  const res = await api.get('/api/notes')
  if (res.code === 0) notes.value = res.data.items || []
}

async function add() {
  const text = draft.value.trim()
  if (!text || saving.value) return
  saving.value = true
  const res = await api.post('/api/notes', { content: text })
  saving.value = false
  if (res.code === 0) {
    draft.value = ''
    await load()
  }
}

async function del(noteId) {
  await api.delete(`/api/notes/${noteId}`)
  await load()
}

function toggle() {
  open.value = !open.value
  if (open.value) load()
}

function onShortcut(e) {
  if (e.ctrlKey && e.shiftKey && e.key === 'N') {
    e.preventDefault()
    toggle()
  }
}

onMounted(() => window.addEventListener('keydown', onShortcut))
onUnmounted(() => window.removeEventListener('keydown', onShortcut))
</script>

<style scoped>
.nf-root { position: fixed; right: 24px; bottom: 24px; z-index: 800; }
.nf-fab {
  width: 46px; height: 46px; border-radius: 50%; border: none; cursor: pointer;
  background: var(--accent-primary); color: #14161c; font-size: 1.2rem;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
}
.nf-panel {
  position: absolute; right: 0; bottom: 56px; width: min(320px, 84vw);
  background: var(--bg-panel, #1a1c24); border: 1px solid rgba(196, 163, 90, 0.25);
  border-radius: 14px; box-shadow: 0 10px 34px rgba(0, 0, 0, 0.5);
  padding: 12px 14px; display: flex; flex-direction: column; gap: 8px;
}
.nf-head { display: flex; justify-content: space-between; align-items: center; }
.nf-title { font-family: var(--font-serif); font-weight: 600; font-size: 0.95rem; }
.nf-close { background: none; border: none; color: var(--text-muted); cursor: pointer; }
.nf-list { max-height: 260px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
.nf-item {
  padding: 8px 10px; border-radius: 10px; background: var(--bg-glass);
  border: 1px solid rgba(196, 163, 90, 0.1);
}
.nf-text { margin: 0; font-size: 0.85rem; line-height: 1.7; color: var(--text-primary); white-space: pre-wrap; word-break: break-word; }
.nf-item-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; }
.nf-time { color: var(--text-muted); font-size: 0.7rem; }
.nf-del { background: none; border: none; color: var(--accent-red, #d66); font-size: 0.75rem; cursor: pointer; }
.nf-empty { color: var(--text-muted); font-size: 0.8rem; text-align: center; padding: 14px 0; }
.nf-input-row { display: flex; gap: 8px; align-items: flex-end; }
.nf-input {
  flex: 1; background: var(--bg-glass); color: var(--text-primary);
  border: 1px solid rgba(196, 163, 90, 0.2); border-radius: 8px; padding: 8px 10px;
  font-size: 0.85rem; resize: none;
}
.nf-add {
  background: var(--accent-primary); color: #14161c; border: none;
  padding: 8px 14px; border-radius: 8px; cursor: pointer; font-weight: 600;
}
.nf-add:disabled { opacity: 0.45; cursor: not-allowed; }
</style>
```

- [ ] **Step 2: WriteStudio 挂载**

- import 区加：`import NotesFloat from '../../components/NotesFloat.vue'`
- template 末尾（`</template>` 前）加：

```html
    <NotesFloat />
```

- [ ] **Step 3: Build 验证**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

预期：`✓ built`，exit 0。

- [ ] **Step 4: Commit**

```bash
git add client/src/components/NotesFloat.vue client/src/views/write/WriteStudio.vue
git commit -m "feat(ui): 写作台闪念便签悬浮面板（CRUD + Ctrl+Shift+N，P6-A）"
```

---

## Task 9: 全量验证 + 人肉冒烟清单

**Files:** 无（仅验证）

- [ ] **Step 1: 后端全量**

```powershell
cd server; python -m pytest tests -q -p no:cacheprovider
```

预期：**114 passed**，exit 0。

- [ ] **Step 2: 前端全量 build**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

预期：`✓ built`，exit 0。

- [ ] **Step 3: 人肉冒烟路径（需求方使用）**

1. 首次进 `/write` → 弹「从哪开始？」→ 选「只想安静写」→ 落在 `/write/plain`，新建作品→输入→保存→导出 .txt
2. 再次进 `/write` → 不再弹（localStorage 已置位）；点右上角「?」可重开
3. 老手：选了「直接开始」后仍在写作台，功能不受影响
4. 便签：写作台右下角 📝 → 记一条 → 关面板 → Ctrl+Shift+N 再开 → 删除 → 刷新仍在（落库）/删空
5. 数据互通：纯净页新建的作品，在写作台 /write 能看到同一本

- [ ] **Step 4: 收尾登记 + 最终提交（若无残留则跳过）**

`docs/改造进度.md` 追加阶段 P6 表（P6-A 各 E 项 ✅，登记 pytest/build 数字与冒烟状态），随改动一并 commit。

---

## Self-Review 结论

- **Spec 覆盖**：A 使用说明弹窗 → Task 4/5 ✅；B 纯净写作页 → Task 6（含路由）✅；C 主页入口 → Task 7 ✅；D 便签（表/端点/UI/快捷键）→ Task 1/2/3/8 ✅；架构决策（数据共用三边界/跨页复用 store）→ 全任务未新建业务表、复用 writingStore ✅。
- **占位符扫描**：无 TBD/TODO；Toast 事件名以注释说明兜底行为。
- **类型一致性**：`notes_bp`、`user_notes` 字段（note_id/user_id/content/created_at/updated_at）、`inkstone_mode`、`/write/plain`、`store.chapters` 等名称在前后端任务间一致。