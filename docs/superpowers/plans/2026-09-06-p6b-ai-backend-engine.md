# P6-B1 AI 生成后端引擎 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为二期创作工坊与写作台增强提供 5 个 AI 生成端点（主线/卷级大纲/本章剧情/提取要点/卡壳续写），含 prompt 模板与测试，纯后端不依赖 UI。

**Architecture:** 复用现有 write 蓝图与 `utils/prompt_builder.py` 模板集中模式：每个新能力 = 一个 `build_*` prompt 函数 + 一个 write 端点（非流式 `chat_completion` + `@ai_quota` + `log_ai_call`），与 `/outline`、`/inspire` 同构。客户端以普适接口消费：作品上下文仍走 `_build_work_context` + `_sanitize_references`（均已存在）。**新增能力端点全部为"生成类"非持久化**（结果由各 UI 决定存哪：主线/大纲存 book_plans，要点/续写即时展示），延续"AI 输出不入业务表"的现有成交模式。

**Tech Stack:** Flask + PyMySQL + utils.mimos（chat_completion）；pytest（inkstone_test，monkeypatch chat_completion 零 token）。

**Spec:** `docs/superpowers/specs/2026-09-06-p6a-newcomer-onboarding-design.md` §5 二期；本计划为其批次 1。

---

## 文件结构

| 文件 | 动作 | 职责 |
|---|---|---|
| `server/utils/prompt_builder.py` | Modify（追加 5 函数） | build_mainline / build_volume_outline / build_chapter_plot / build_extract_points / build_unstick 的 messages 构造 |
| `server/routes/write.py` | Modify（追加 5 端点 + import） | mainline / volume-outline / chapter-plot / extract-points / unstick，全部走 chat_completion + ai_quota + log_ai_call |
| `server/tests/test_write_quick_actions.py` | Modify（追加用例） | 对齐现有 monkeypatch 风格，用例见各 Task |

---

## Task 1: prompt_builder 新增 5 个 build_* 函数

**Files:**
- Modify: `server/utils/prompt_builder.py`（文件末尾追加）

- [ ] **Step 1: 追加 5 个 prompt 函数**

在 `server/utils/prompt_builder.py` 末尾追加：

```python
def build_mainline(inspiration, requirements=''):
    """二期：从灵感/闪念生成整体主线大方向（谁+想要什么+拦着什么→目标与冲突弧）。"""
    system = (
        '你是一位资深故事架构师。用户会给你一些故事灵感（可能零散）。'
        '请把它们整合为一条清晰的整体主线（Mainline）：'
        '包含【核心命题】【主角】【核心目标】【核心障碍】【冲突弧概览】【预期结局与主题】六项。'
        '语言精炼，每项 1-3 句，不做具体章节规划。'
    )
    user = f'灵感素材：\n{inspiration}'
    if requirements:
        user += f'\n\n用户补充要求：\n{requirements}'
    user += '\n\n请输出整体主线。'
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]


def build_volume_outline(mainline, volume_count=3):
    """二期：依据主线生成卷级故事曲线草稿（每卷 2-4 句目标/转折/走向）。"""
    system = (
        '你是一位资深故事架构师。根据用户给出的整体主线，生成卷级（Volumes）故事大纲草稿：'
        '分若干卷，每卷包含【卷目标】【主要转折】【结尾钩子】。'
        '卷级即可，不做章节级细化（章节到时边写边细化）。'
    )
    try:
        count = max(2, min(int(volume_count), 6))
    except (TypeError, ValueError):
        count = 3
    user = f'整体主线：\n{mainline}\n\n请分为 {count} 卷输出。'
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]


def build_chapter_plot(context, inspire_text, mainline='', chapter_no=0):
    """二期：任务卡 AI 生成本章剧情要点（结合前情/设定/主线/灵感）。"""
    system = (
        '你是一位帮写作者推进进度的编辑。根据作品上下文与灵感，生成本章（第 N 章）的剧情要点：'
        '包含【本章目标】【本章 Beats（3-6 条）】【本章钩子】【写完后建议提取的前情要点】。'
        'Beats 是具体情节步骤，不是抽象主题。'
    )
    user = f'作品上下文：\n{context}'
    if mainline:
        user += f'\n\n整体主线：\n{mainline}'
    if inspire_text:
        user += f'\n\n灵感素材：\n{inspire_text}'
    user += f'\n\n本章编号：第 {chapter_no} 章' if chapter_no else '\n\n本章编号：下一章'
    user += '\n\n请输出本章剧情要点。'
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]


def build_extract_points(chapter_content, chapter_title=''):
    """二期：用户写完一章后提取【本章要点】【本章钩子】【前情提要】。"""
    system = (
        '你是一位资深的编辑。给定一章已完成内容，提取三项供后续使用：'
        '【本章要点】（3-5 条核心事件）、【本章钩子】（结尾留下的悬念/期待）、'
        '【前情提要】（供下一章开头追述的一句话概述）。语言精炼。'
    )
    user = ''
    if chapter_title:
        user += f'章节标题：{chapter_title}\n\n'
    user += f'本章内容：\n{chapter_content[:12000]}\n\n请输出三项提取。'
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]


def build_unstick(context, chapter_content, last_summary=''):
    """二期：写作卡壳时，读本章实时内容 + 前几章摘要，生成"接下来写什么"。"""
    system = (
        '你是一位很有耐心的写作伙伴。用户写到这里卡住了。'
        '请基于本章已写内容与作品上下文，给出【接下来可以写什么】的具体建议 2-4 条：'
        '每条是一个可直接开写的情节方向（含承接上一段的衔接句示例）。'
        '不要说教，不要列抽象道理，给能直接接着写的料。'
    )
    user = f'作品上下文：\n{context}'
    if last_summary:
        user += f'\n\n前情摘要：\n{last_summary}'
    user += f'\n\n本章已写内容（截至卡壳处）：\n{chapter_content[:8000]}\n\n请给出接下来写什么的建议。'
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]
```

- [ ] **Step 2: 验证模块可导入、函数返回 messages 结构**

```powershell
cd server; python -c "from utils.prompt_builder import build_mainline, build_volume_outline, build_chapter_plot, build_extract_points, build_unstick; m = build_mainline('一个女孩在雨夜捡到会说话的猫'); assert len(m) == 2 and m[0]['role'] == 'system' and m[1]['role'] == 'user'; print('5 个 build_* 导入 + 结构 OK')"
```

预期：打印 `5 个 build_* 导入 + 结构 OK`，exit 0。

- [ ] **Step 3: Commit**

```bash
git add server/utils/prompt_builder.py
git commit -m "feat(ai): prompt_builder 新增 5 个二期生成模板（主线/卷级大纲/本章剧情/提取要点/卡壳续写）"
```

---

## Task 2: write.py 新增 5 个端点

**Files:**
- Modify: `server/routes/write.py`（import 区 + 文件末尾追加）

- [ ] **Step 1: import 区补充 5 个 build_***

修改 `server/routes/write.py` 第 6-11 行的 import：

```python
from utils.prompt_builder import (
    build_continue, build_inspire, build_outline,
    build_character, build_polish, build_prompt_suggestion,
    build_chat_system, build_diagnose, build_summary, build_references_text,
    build_struct_review, build_fix, build_interpret, build_find_lines,
    build_mainline, build_volume_outline, build_chapter_plot,
    build_extract_points, build_unstick,
)
```

- [ ] **Step 2: 文件末尾追加 5 个端点**

在 `server/routes/write.py` 末尾（`ai_find_lines` 之后，若 find-lines 复用池子则在其函数定义之后）追加：

```python
# ============ 二期 P6-B1：AI 生成后端引擎 ============


@write_bp.post('/mainline')
@login_required
@ai_quota
def ai_mainline():
    """从灵感/闪念生成整体主线大方向（结果由前端决定存 book_plans 或即时展示）。"""
    data = request.get_json()
    inspiration = (data.get('inspiration') or '').strip()
    if not inspiration:
        return fail('请提供灵感素材')
    if len(inspiration) > 8000:
        return fail('灵感素材过长，最多8000字')
    requirements = (data.get('requirements') or '').strip()[:2000]
    messages = build_mainline(inspiration, requirements)
    try:
        result = chat_completion(messages)
        log_ai_call(current_app, session.get('user_id'), '/mainline', success=True)
    except Exception as e:
        logger.error(f'AI mainline error: {e}')
        log_ai_call(current_app, session.get('user_id'), '/mainline', success=False, error=str(e))
        return fail('主线生成失败，请稍后再试')
    conv_key = str(uuid.uuid4())
    _save_conv(conv_key, 'user', inspiration)
    _save_conv(conv_key, 'assistant', result)
    return ok({'mainline': result})


@write_bp.post('/volume-outline')
@login_required
@ai_quota
def ai_volume_outline():
    """依据主线生成卷级故事曲线草稿。"""
    data = request.get_json()
    mainline = (data.get('mainline') or '').strip()
    if not mainline:
        return fail('请先提供整体主线')
    if len(mainline) > 12000:
        return fail('主线过长，最多12000字')
    volume_count = data.get('volume_count') or 3
    messages = build_volume_outline(mainline, volume_count)
    try:
        result = chat_completion(messages)
        log_ai_call(current_app, session.get('user_id'), '/volume-outline', success=True)
    except Exception as e:
        logger.error(f'AI volume-outline error: {e}')
        log_ai_call(current_app, session.get('user_id'), '/volume-outline', success=False, error=str(e))
        return fail('大纲生成失败，请稍后再试')
    conv_key = str(uuid.uuid4())
    _save_conv(conv_key, 'user', mainline)
    _save_conv(conv_key, 'assistant', result)
    return ok({'outline': result})


@write_bp.post('/chapter-plot')
@login_required
@ai_quota
def ai_chapter_plot():
    """任务卡：按上下文+主线+灵感生成本章剧情要点（非持久化，前端即时展示/编辑）。"""
    data = request.get_json()
    work_id = data.get('work_id')
    try:
        work_id = int(work_id) if work_id else None
    except (TypeError, ValueError):
        work_id = None
    context = _build_work_context(session.get('user_id'), work_id) if work_id else ''
    if not context:
        return fail('作品不存在或不属于你', code=404)
    inspire_text = (data.get('inspiration') or '').strip()[:4000]
    mainline = (data.get('mainline') or '').strip()[:6000]
    chapter_no = data.get('chapter_no') or 0
    try:
        chapter_no = int(chapter_no)
    except (TypeError, ValueError):
        chapter_no = 0
    messages = build_chapter_plot(context, inspire_text, mainline, chapter_no)
    try:
        result = chat_completion(messages)
        log_ai_call(current_app, session.get('user_id'), '/chapter-plot', success=True)
    except Exception as e:
        logger.error(f'AI chapter-plot error: {e}')
        log_ai_call(current_app, session.get('user_id'), '/chapter-plot', success=False, error=str(e))
        return fail('本章剧情生成失败，请稍后再试')
    conv_key = str(uuid.uuid4())
    _save_conv(conv_key, 'user', f'chapter-plot work={work_id}')
    _save_conv(conv_key, 'assistant', result)
    return ok({'plot': result})


@write_bp.post('/extract-points')
@login_required
@ai_quota
def ai_extract_points():
    """写完一章后提取 要点/钩子/前情提要（UI 依大纲树结构填入或展示）。"""
    data = request.get_json()
    chapter_content = (data.get('content') or '').strip()
    if not chapter_content:
        return fail('本章内容为空')
    if len(chapter_content) > 20000:
        return fail('内容过长，最多20000字')
    chapter_title = (data.get('chapter_title') or '').strip()[:100]
    messages = build_extract_points(chapter_content, chapter_title)
    try:
        result = chat_completion(messages)
        log_ai_call(current_app, session.get('user_id'), '/extract-points', success=True)
    except Exception as e:
        logger.error(f'AI extract-points error: {e}')
        log_ai_call(current_app, session.get('user_id'), '/extract-points', success=False, error=str(e))
        return fail('要点提取失败，请稍后再试')
    conv_key = str(uuid.uuid4())
    _save_conv(conv_key, 'user', chapter_title or 'extract-points')
    _save_conv(conv_key, 'assistant', result)
    return ok({'points': result})


@write_bp.post('/unstick')
@login_required
@ai_quota
def ai_unstick():
    """卡壳时：读本章实时内容+前几章摘要，生成接下来写什么（可反复重新生成）。"""
    data = request.get_json()
    chapter_content = (data.get('content') or '').strip()
    if not chapter_content:
        return fail('本章还没有内容，先写几行再点「卡壳了」')
    if len(chapter_content) > 20000:
        return fail('内容过长，最多20000字')
    work_id = data.get('work_id')
    try:
        work_id = int(work_id) if work_id else None
    except (TypeError, ValueError):
        work_id = None
    context = _build_work_context(session.get('user_id'), work_id) if work_id else ''
    last_summary = (data.get('last_summary') or '').strip()[:3000]
    messages = build_unstick(context, chapter_content, last_summary)
    try:
        result = chat_completion(messages)
        log_ai_call(current_app, session.get('user_id'), '/unstick', success=True)
    except Exception as e:
        logger.error(f'AI unstick error: {e}')
        log_ai_call(current_app, session.get('user_id'), '/unstick', success=False, error=str(e))
        return fail('生成失败，请稍后再试')
    conv_key = str(uuid.uuid4())
    _save_conv(conv_key, 'user', 'unstick')
    _save_conv(conv_key, 'assistant', result)
    return ok({'suggestions': result})
```

- [ ] **Step 3: 后端启动自检（路由注册）**

```powershell
cd server; python -c "from app import create_app; app = create_app(); rules = [str(r) for r in app.url_map.iter_rules() if r.rule in ('/api/write/mainline','/api/write/volume-outline','/api/write/chapter-plot','/api/write/extract-points','/api/write/unstick')]; print('\n'.join(sorted(rules)) if rules else 'MISSING')"
```

预期：5 条路由全部列出，exit 0。

- [ ] **Step 4: Commit**

```bash
git add server/routes/write.py
git commit -m "feat(ai): 二期 5 个 AI 生成端点（mainline/volume-outline/chapter-plot/extract-points/unstick）"
```

---

## Task 3: 测试——5 端点 401/参数/成功/越权

**Files:**
- Modify: `server/tests/test_write_quick_actions.py`（追加用例，复用文件已有 `stub_completion` fixture）

- [ ] **Step 1: 先确认现有 stub 风格（test_write_quick_actions.py:13-25 已有）**

现有 fixture（已存在，无需重复定义）：

```python
@pytest.fixture
def stub_completion(monkeypatch):
    def fake_completion(messages):
        calls.append(messages)
        return 'AI 生成的测试文本'
    calls = []
    monkeypatch.setattr(write_mod, 'chat_completion', fake_completion)
    monkeypatch.setattr(write_mod, 'log_ai_call', lambda *a, **k: None)
    return calls
```

> 若 fixture 名不同（如 `capture`），适配到现有命名。

- [ ] **Step 2: 追加 5 组用例**

在 `test_write_quick_actions.py` 末尾追加（保持 `write_mod = write.py 模块` 的既有引用方式；若文件未定义 write_mod，则顶部补 `from routes import write as write_mod`）：

```python
# ============ 二期 P6-B1：AI 生成引擎 ============


def test_mainline_requires_login(client):
    r = client.post('/api/write/mainline', json={'inspiration': 'x'})
    assert r.get_json()['code'] == 401


def test_mainline_generates(auth_client, stub_completion):
    r = auth_client.post('/api/write/mainline', json={'inspiration': '雨夜里会说话的猫'})
    assert r.get_json()['code'] == 0
    assert r.get_json()['data']['mainline'] == 'AI 生成的测试文本'
    assert len(stub_completion) == 1
    system_msg = stub_completion[0][0]['content']
    assert '主线' in system_msg


def test_mainline_requires_inspiration(auth_client, stub_completion):
    r = auth_client.post('/api/write/mainline', json={'inspiration': ''})
    assert r.get_json()['code'] != 0


def test_volume_outline_generates(auth_client, stub_completion):
    r = auth_client.post('/api/write/volume-outline', json={'mainline': '命题：少年追光', 'volume_count': 3})
    assert r.get_json()['code'] == 0
    assert r.get_json()['data']['outline'] == 'AI 生成的测试文本'
    assert '分 3 卷' in stub_completion[0][1]['content'] or '3 卷' in stub_completion[0][1]['content']


def test_volume_outline_requires_mainline(auth_client, stub_completion):
    r = auth_client.post('/api/write/volume-outline', json={'mainline': ''})
    assert r.get_json()['code'] != 0


def test_chapter_plot_requires_work(auth_client, stub_completion):
    r = auth_client.post('/api/write/chapter-plot', json={'work_id': 999999})
    assert r.get_json()['code'] == 404


def test_chapter_plot_generates(auth_client, sample_work, stub_completion):
    r = auth_client.post('/api/write/chapter-plot', json={'work_id': sample_work['work_id'], 'inspiration': '猫说人话', 'chapter_no': 1})
    assert r.get_json()['code'] == 0
    assert r.get_json()['data']['plot'] == 'AI 生成的测试文本'
    assert len(stub_completion) == 1


def test_extract_points_requires_content(auth_client, stub_completion):
    r = auth_client.post('/api/write/extract-points', json={'content': ''})
    assert r.get_json()['code'] != 0


def test_extract_points_generates(auth_client, stub_completion):
    r = auth_client.post('/api/write/extract-points', json={'content': '这是本章的内容。' * 10, 'chapter_title': '第一章'})
    assert r.get_json()['code'] == 0
    assert r.get_json()['data']['points'] == 'AI 生成的测试文本'


def test_unstick_requires_content(auth_client, stub_completion):
    r = auth_client.post('/api/write/unstick', json={'content': ''})
    assert r.get_json()['code'] != 0


def test_unstick_generates(auth_client, sample_work, stub_completion):
    r = auth_client.post('/api/write/unstick', json={'content': '他推开门，愣住了。', 'work_id': sample_work['work_id']})
    assert r.get_json()['code'] == 0
    assert r.get_json()['data']['suggestions'] == 'AI 生成的测试文本'
```

> 若 sample_work 返回结构是 `res.data.work_id`（如 test_notes.py 中 _mk_notes 用法），确认 conftest.py 中 sample_work fixture 实际返回形式后再用（`sample_work['work_id']` 或 `sample_work` 直接为 id，以 conftest 为准）。

- [ ] **Step 3: 运行新用例，确认全过**

```powershell
cd server; python -m pytest tests/test_write_quick_actions.py -q -p no:cacheprovider
```

预期：既有用例 + 新增 11 个全部 passed（原有 quick actions 用例大概 6-15 个，总数相加）。

- [ ] **Step 4: 全量回归**

```powershell
cd server; python -m pytest tests -q -p no:cacheprovider
```

预期：**125 passed**（114 + 11），exit 0。

- [ ] **Step 5: Commit**

```bash
git add server/tests/test_write_quick_actions.py
git commit -m "test(ai): 二期 5 端点 11 用例（401/参数/成功/越权），pytest 125 passed"
```

---

## Self-Review 结论

- **Spec 覆盖**：二期 §5 中「AI 主线生成」「AI 卷级大纲草稿」「任务卡 AI 生成本章剧情」「写完后提取要点/钩子/前情提要」「编辑器卡壳了按钮」对应的后端能力全部落在本批次（mainline / volume-outline / chapter-plot / extract-points / unstick）。
- **占位符扫描**：无 TBD/TODO；所有步骤含完整代码。fixture 名与 sample_work 结构两处注明"以 conftest 实际为准"，执行时核对即可（非占位）。
- **类型一致性**：端点返回字段名（mainline/outline/plot/points/suggestions）与前端计划（批次 3/4 规划中）约定一致；`build_*` 函数签名与端点调用参数一致；`_build_work_context`、`_sanitize_references`、`_save_conv`、`ai_quota`、`log_ai_call` 均为 write.py 既有符号，无新名冲突。