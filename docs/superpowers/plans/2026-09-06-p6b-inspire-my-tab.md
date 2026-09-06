# P6-B2 灵感馆「我的灵感」页签 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 灵感馆新增「我的灵感」页签：聚合三类本人数据——闪念便签（user_notes）、诗词/素材收藏（inspiration_favorites）、AI 主线——并在页签内直接生成/保存 AI 主线。

**Architecture:** 遵循三边界：不新建业务表。`user_notes` 表加列 `note_kind`（默认 `note`，`mainline`=AI 主线），复用现有 `/api/notes` 与 `/api/inspire/favorites` CRUD；AI 主线生成走批次 1 已上线的 `POST /api/write/mainline`，前端拿结果后以 `note_kind='mainline'` 存为便签（同时自然进入便签列表，二期「我的灵感」即聚合此表）。实现上给 notes 蓝图补一个"保存主线"辅助（POST /api/notes 增加可选 `kind` 参数），并在 Inspire.vue 增加 `my` 页签（三区聚合 UI）。

**Tech Stack:** Flask + PyMySQL；Vue3 + Pinia（userStore）/ api 封装；pytest（inkstone_test）。

**Spec:** `docs/superpowers/specs/2026-09-06-p6a-newcomer-onboarding-design.md` §5 二期；本计划为其批次 2。

---

## 文件结构

| 文件 | 动作 | 职责 |
|---|---|---|
| `server/database/schema.sql` | Modify（user_notes 加 note_kind 列，追加 ALTER 注释） | 表结构演进记录 |
| `server/routes/notes.py` | Modify | POST 接受可选 `kind`（note/mainline）；GET 返回 kind 字段 |
| `server/tests/test_notes.py` | Modify（追加用例） | kind 参数校验 + 列表返回 kind |
| `client/src/views/Inspire.vue` | Modify | 新增「我的灵感」页签：三区聚合（便签/收藏/AI 主线）+ 生成主线按钮 |
| `server/tests/test_inspire_favorites.py` | Modify 或不动 | 收藏复用现有，无需改动（若需要可加一个跨区聚合冒烟） |

---

## Task 1: user_notes 加 note_kind 列

**Files:**
- Modify: `server/database/schema.sql`（user_notes 建表语句）

- [ ] **Step 1: schema.sql 中 user_notes 表加列**

把 `server/database/schema.sql` 第 28 张表 user_notes 的定义改为（在 content 后加 note_kind）：

```sql
-- 28. 闪念便签表（P6-A：用户随时记录灵感片段，仅本人可见；P6-B2：note_kind 区分便签/AI主线）
CREATE TABLE user_notes (
    note_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    note_kind VARCHAR(16) NOT NULL DEFAULT 'note',
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_notes_user (user_id),
    CONSTRAINT user_notes_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

- [ ] **Step 2: 开发库幂等加列**

```powershell
cd server; python -c "
import pymysql
conn = pymysql.connect(host='localhost', user='root', password='123456', database='inkstone', autocommit=True, charset='utf8mb4')
with conn.cursor() as cur:
    cur.execute(\"ALTER TABLE user_notes ADD COLUMN note_kind VARCHAR(16) NOT NULL DEFAULT 'note' AFTER user_id\")
    cur.execute(\"SHOW COLUMNS FROM user_notes LIKE 'note_kind'\")
    print('note_kind exists:', cur.fetchone() is not None)
conn.close()
" 2>&1 | Select-String -NotMatch 'warnings.warn'
```

预期：`note_kind exists: True`（若已存在则重复执行报错，先 DROP COLUMN 再试；或直接忽略"Duplicate column"错误判断为已加好）。

- [ ] **Step 3: Commit**

```bash
git add server/database/schema.sql
git commit -m "feat(db): user_notes 加 note_kind 列（note/mainline 区分便签与AI主线，P6-B2）"
```

---

## Task 2: notes.py 支持 kind

**Files:**
- Modify: `server/routes/notes.py`

- [ ] **Step 1: list 返回 kind；POST 接受可选 kind**

修改 notes.py：

```python
@notes_bp.get('')
@login_required
def list_notes():
    rows = query(
        'SELECT note_id, note_kind, content, created_at, updated_at FROM user_notes '
        'WHERE user_id = %s ORDER BY updated_at DESC',
        (session['user_id'],),
    )
    items = [{
        'note_id': r['note_id'],
        'kind': r['note_kind'],
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
    kind = (data.get('kind') or 'note').strip()
    if kind not in ('note', 'mainline'):
        return fail('无效的类型')
    note_id = execute(
        'INSERT INTO user_notes (user_id, note_kind, content) VALUES (%s, %s, %s)',
        (session['user_id'], kind, content),
    )
    return ok({'note_id': note_id, 'kind': kind}, msg='已保存')
```

> put/delete 保持不变（不涉及 kind）；_get_own_note 也不需动。

- [ ] **Step 2: 后端自检**

```powershell
cd server; python -c "from app import create_app; app = create_app(); print('notes app OK')" 2>&1 | Select-String -NotMatch 'warnings.warn|墨池'
```

预期：`notes app OK` + 启动日志，exit 0。

- [ ] **Step 3: Commit**

```bash
git add server/routes/notes.py
git commit -m "feat(notes): 列表返回 kind + POST 支持 note/mainline 类型（P6-B2）"
```

---

## Task 3: tests 追加 kind 用例

**Files:**
- Modify: `server/tests/test_notes.py`

- [ ] **Step 1: 追加 4 个用例**

在 test_notes.py 末尾追加：

```python
def test_notes_kind_default_is_note(auth_client):
    note_id = _mk_notes(auth_client, '普通便签')[0]
    items = auth_client.get('/api/notes').get_json()['data']['items']
    it = next(i for i in items if i['note_id'] == note_id)
    assert it['kind'] == 'note'


def test_notes_create_mainline_kind(auth_client):
    r = auth_client.post('/api/notes', json={'content': '主线：少年追光，破除枷锁', 'kind': 'mainline'})
    assert r.get_json()['code'] == 0
    items = auth_client.get('/api/notes').get_json()['data']['items']
    it = next(i for i in items if i['note_id'] == r.get_json()['data']['note_id'])
    assert it['kind'] == 'mainline'
    assert it['content'] == '主线：少年追光，破除枷锁'


def test_notes_rejects_bad_kind(auth_client):
    r = auth_client.post('/api/notes', json={'content': 'x', 'kind': 'hack'})
    assert r.get_json()['code'] != 0


def test_notes_kind_kept_on_update(auth_client):
    note_id = _mk_notes(auth_client, '初始普通')[0]
    auth_client.put(f'/api/notes/{note_id}', json={'content': '改成主线'})
    items = auth_client.get('/api/notes').get_json()['data']['items']
    it = next(i for i in items if i['note_id'] == note_id)
    assert it['content'] == '改成主线'
    assert it['kind'] == 'note'  # 更新不改变 kind
```

> 若 _mk_notes 需要传 kind，保留原签名不动（只测默认 note），或扩展：`_mk_notes(client, *contents, kind='note')`——以现有实现为准，新增用例不依赖改它。

- [ ] **Step 2: 运行用例**

```powershell
cd server; python -m pytest tests/test_notes.py -q -p no:cacheprovider
```

预期：原 7 + 新 4 = **11 passed**。

- [ ] **Step 3: 全量回归**

```powershell
cd server; python -m pytest tests -q -p no:cacheprovider
```

预期：**129 passed**（125 + 4），exit 0。

- [ ] **Step 4: Commit**

```bash
git add server/tests/test_notes.py
git commit -m "test(notes): kind 4 用例（默认note/mainline创建/非法拦截/更新保kind），pytest 129 passed"
```

---

## Task 4: Inspire.vue 新增「我的灵感」页签

**Files:**
- Modify: `client/src/views/Inspire.vue`

- [ ] **Step 1: BASE_SEGS 加 my 页签（登录后）**

```js
const BASE_SEGS = [
  { key: 'intent', label: '意境找句' },
  { key: 'my', label: '我的灵感' },
  { key: 'poems', label: '诗词' },
  { key: 'materials', label: '句子素材' },
]
const segs = computed(() => {
  const base = [...BASE_SEGS]
  if (userStore.isLoggedIn) base.push({ key: 'favorites', label: `收藏${favsCount.value ? ` (${favsCount.value})` : ''}` })
  const all = base.filter(s => s.key !== 'my' || userStore.isLoggedIn)
  return all
})
```

> 若不想登录也显示占位，可仅登录后插入 `my`（同上 filter 处理）；按 spec「我的灵感」是个人数据，登录后显示，未登录不显示。

- [ ] **Step 2: 搜索/换一批栏隐藏条件加 my**

模板第 31 行条件改为：

```html
<template v-if="activeTab !== 'favorites' && activeTab !== 'intent' && activeTab !== 'my'">
```

- [ ] **Step 3: 内容区加 my 专属区块（在 intent-area 之后、`<template v-else>` 之前）**

```html
<!-- 我的灵感：便签 / 收藏 / AI 主线 三区聚合（P6-B2） -->
<div v-if="activeTab === 'my'" class="my-area">
  <div class="my-card glass-card">
    <div class="my-card-head">
      <span class="my-title">✨ 闪念便签</span>
      <span class="my-sub">写作中随手记下的点子（写作台右下角📝也可记）</span>
    </div>
    <div class="my-list">
      <p v-if="!notes.length" class="muted my-empty">还没有便签，去写作台点 📝 记一个闪念吧</p>
      <div v-for="n in notes" :key="'n' + n.note_id" class="my-item">
        <p class="my-text">{{ n.content }}</p>
        <div class="my-item-foot">
          <span class="my-time">{{ (n.updated_at || '').slice(5, 16) }}</span>
          <button class="ic-btn" @click="deleteNote(n.note_id)">✕</button>
        </div>
      </div>
      <div class="my-add-row">
        <input v-model="noteDraft" class="my-input" placeholder="记一个闪念…（回车保存）" @keydown.enter="addNote" />
        <button class="btn btn-primary btn-sm" @click="addNote" :disabled="!noteDraft.trim()">记下</button>
      </div>
    </div>
  </div>

  <div class="my-card glass-card">
    <div class="my-card-head">
      <span class="my-title">🧭 AI 主线</span>
      <span class="my-sub">让 AI 从灵感里帮你定整体大方向，随时生成/重新生成</span>
    </div>
    <textarea v-model="mainlineInput" class="my-input my-textarea" rows="2" placeholder="贴几条灵感/闪念，或直接描述你脑海里的故事…"></textarea>
    <button class="btn btn-primary btn-sm" @click="genMainline" :disabled="mainlineLoading || !mainlineInput.trim()">
      {{ mainlineLoading ? '生成中…' : '生成整体主线' }}
    </button>
    <div v-if="mainlineResult" class="my-result">
      <p class="my-result-text">{{ mainlineResult }}</p>
      <div class="my-item-foot">
        <span class="my-time">AI 生成</span>
        <button class="ic-btn" @click="saveMainline">保存到我的灵感</button>
        <button class="ic-btn" @click="mainlineResult = ''">放弃</button>
      </div>
    </div>
    <div class="my-list" v-if="mainlines.length">
      <p class="muted my-empty" style="text-align:left">已保存的主线：</p>
      <div v-for="m in mainlines" :key="'m' + m.note_id" class="my-item">
        <p class="my-text">{{ m.content }}</p>
        <div class="my-item-foot">
          <span class="my-time">{{ (m.updated_at || '').slice(5, 16) }}</span>
          <button class="ic-btn" @click="deleteNote(m.note_id)">✕</button>
        </div>
      </div>
    </div>
  </div>

  <div class="my-card glass-card">
    <div class="my-card-head">
      <span class="my-title">💛 我的收藏</span>
      <span class="my-sub">在诗词/素材里点 ♡ 收藏的内容</span>
    </div>
    <div class="my-list">
      <p v-if="!favItems.length" class="muted my-empty">还没有收藏，去诗词/素材里点 ♡ 吧</p>
      <div v-for="f in favItems" :key="'f' + f.fav_id" class="my-item">
        <p class="my-text">{{ f.content }}</p>
        <div class="my-item-foot">
          <span class="my-time">{{ f.item_type === 'poem' ? `《${f.title}》${f.author}` : (f.title || '素材') }}</span>
          <button class="ic-btn" @click="removeFav(f)">✕</button>
        </div>
      </div>
    </div>
  </div>
</div>
```

- [ ] **Step 4: script 加状态与逻辑**

```js
// ---- 我的灵感（P6-B2）----
const notes = ref([])
const mainlines = ref([])
const noteDraft = ref('')
const mainlineInput = ref('')
const mainlineResult = ref('')
const mainlineLoading = ref(false)

async function loadMyNotes() {
  if (!userStore.isLoggedIn) return
  const res = await api.get('/api/notes')
  if (res.code === 0) {
    const all = res.data.items || []
    notes.value = all.filter(i => i.kind === 'note')
    mainlines.value = all.filter(i => i.kind === 'mainline')
  }
}

async function addNote() {
  const text = noteDraft.value.trim()
  if (!text) return
  const res = await api.post('/api/notes', { content: text })
  if (res.code === 0) { noteDraft.value = ''; loadMyNotes() }
}

async function deleteNote(noteId) {
  await api.delete(`/api/notes/${noteId}`)
  loadMyNotes()
}

async function genMainline() {
  const inspiration = mainlineInput.value.trim()
  if (!inspiration || mainlineLoading.value) return
  mainlineLoading.value = true
  const res = await api.post('/api/write/mainline', { inspiration })
  mainlineLoading.value = false
  if (res.code === 0) mainlineResult.value = res.data.mainline
}

async function saveMainline() {
  const text = mainlineResult.value.trim()
  if (!text) return
  const res = await api.post('/api/notes', { content: text, kind: 'mainline' })
  if (res.code === 0) { mainlineResult.value = ''; loadMyNotes() }
}

const favItems = ref([])
async function loadMyFavs() {
  if (!userStore.isLoggedIn) return
  const res = await api.get('/api/inspire/favorites')
  if (res.code === 0) favItems.value = res.data.items || []
}
```

- [ ] **Step 5: switchSeg 加载 my 数据**

在 `switchSeg(key)`（现有，约 280 行）中加入：

```js
function switchSeg(key) {
  if (activeTab.value === key) return
  activeTab.value = key
  if (key === 'my') { loadMyNotes(); loadMyFavs() }
  else if (key === 'favorites') loadFavorites()
  else if (key === 'intent') { /* FindLinesPanel 自加载 */ }
  else { cats.value = []; activeCat.value = ''; query.value = ''; loadItems() }
}
```

> 与现有 switchSeg 合并（保留原有 else 分支），不重复注册。若现有 `loadFavorites` 函数名不同（如 loadItems 走 favorites 分支），以实际代码为准，my 分支只调 loadMyNotes + loadMyFavs。

- [ ] **Step 6: 样式追加（style 区）**

```css
.my-area { display: flex; flex-direction: column; gap: 18px; }
.my-card { padding: 16px 18px; }
.my-card-head { display: flex; align-items: baseline; gap: 10px; margin-bottom: 10px; }
.my-title { font-family: var(--font-serif); font-weight: 600; font-size: 0.98rem; }
.my-sub { color: var(--text-muted); font-size: 0.75rem; }
.my-list { display: flex; flex-direction: column; gap: 6px; }
.my-item { padding: 8px 10px; border-radius: 8px; background: var(--bg-glass); border: 1px solid rgba(196,163,90,0.1); }
.my-item + .my-item { border-top: none; }
.my-text { margin: 0; font-size: 0.85rem; line-height: 1.7; white-space: pre-wrap; word-break: break-word; }
.my-item-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
.my-time { color: var(--text-muted); font-size: 0.7rem; }
.my-empty { font-size: 0.8rem; }
.my-add-row { display: flex; gap: 8px; margin-top: 8px; }
.my-input { flex: 1; background: var(--bg-glass); color: var(--text-primary); border: 1px solid rgba(196,163,90,0.2); border-radius: 8px; padding: 7px 10px; font-size: 0.85rem; }
.my-textarea { resize: none; }
.my-result { margin-top: 10px; padding: 10px 12px; border-radius: 10px; background: rgba(196,163,90,0.08); border: 1px solid rgba(196,163,90,0.25); }
.my-result-text { margin: 0 0 8px; font-size: 0.85rem; line-height: 1.8; white-space: pre-wrap; }
```

- [ ] **Step 7: Build 验证**

```powershell
cd client; npm run build 2>&1 | Select-Object -Last 2
```

预期：`✓ built`，exit 0。

- [ ] **Step 8: Commit**

```bash
git add client/src/views/Inspire.vue
git commit -m "feat(ui): 灵感馆「我的灵感」页签——便签/AI主线/收藏三区聚合 + 生成主线入口（P6-B2）"
```

---

## Task 5: 全量验证 + 收尾登记

**Files:** 无（仅验证）

- [ ] **Step 1: pytest 全量**

```powershell
cd server; python -m pytest tests -q -p no:cacheprovider
```

预期：**129 passed**，exit 0。

- [ ] **Step 2: build 全量**

已完成于 Task 4 Step 7；如中间有改动重跑一次。

- [ ] **Step 3: 人肉冒烟路径**

1. 灵感馆 → 登录 → 页签出现「我的灵感」
2. 便签区：记一条 → 回车 → 出现；✕ 删除
3. AI 主线区：贴两条灵感 → 生成 → 出结果 → 保存 → 出现在"已保存的主线"；重新生成可用
4. 收藏区：去诗词页 ♡ 收藏两首 → 回「我的灵感」看到
5. 写作台右下角 📝 记的便签 → 灵感馆「我的灵感」也能看到（同一批 user_notes）

- [ ] **Step 4: 台账登记 + commit（无残留跳过）**

`docs/改造进度.md`：P6-B2 标记 ✅（pytest 129 / build 绿），并注明批次 3（创作工坊）待做。

---

## Self-Review 结论

- **Spec 覆盖**：二期「「我的灵感」页签（聚合便签/收藏/AI 主线）」→ Task 1-4 ✅；「AI 主线生成」→ 复用批次 1 `/api/write/mainline` + Task 4 保存为 mainline 便签 ✅；便签数据源完全复用一期 user_notes ✅。
- **占位符扫描**：无 TBD/TODO；每步含完整代码；两处"以实际代码为准"的开关（switchSeg 现有分支、loadFavorites 名称）是适配现有代码的核对项，非占位。
- **类型一致性**：`kind` 取值（note/mainline）在 schema/notes.py/测试/前端完全一致；后端返回字段 `kind`、前端消费 `kind`；`/api/notes`、`/api/inspire/favorites`、`/api/write/mainline` 三个端点在 Task 4 中的调用方式与既有实现一致。