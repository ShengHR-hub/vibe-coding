import logging
from flask import Blueprint, request, Response, session, current_app
from database.db import query, execute
from utils.helpers import ok, fail, login_required, check_ai_quota, _fmt
from utils.mimos import chat_completion, chat_completion_stream
from utils.prompt_builder import (
    build_continue, build_inspire, build_outline,
    build_character, build_polish, build_prompt_suggestion,
    build_chat_system, build_diagnose, build_summary, build_references_text,
    build_struct_review, build_fix, build_interpret, build_find_lines,
)
from utils.logger import log_ai_call
import json, uuid, time

logger = logging.getLogger(__name__)

write_bp = Blueprint('write', __name__)


def _save_conv(session_key, role, content):
    # W1d：入库内容截断，防止超长输出撑爆 ai_conversations
    content = (content or '')[:20000]
    execute(
        'INSERT INTO ai_conversations (user_id, session_key, role, content) VALUES (%s, %s, %s, %s)',
        (session.get('user_id'), session_key, role, content)
    )


def _sanitize_references(raw):
    """W4a：清洗前端 references（≤6 条，每条 ≤600 字，dict/字符串均可）。"""
    if not isinstance(raw, list):
        return None
    out = []
    for r in raw[:8]:
        if isinstance(r, dict):
            content = str(r.get('content') or '').strip()
            if not content:
                continue
            label = str(r.get('type') or r.get('category') or '素材')
            out.append({'type': label[:20], 'content': content[:600]})
        elif isinstance(r, str) and r.strip():
            out.append({'type': '素材', 'content': r.strip()[:600]})
        if len(out) >= 6:
            break
    return out or None


def _build_work_context(user_id, work_id):
    """W2a：组装作品上下文（简介 + 章节结构 + 主要角色卡），仅限本人作品。"""
    work = query(
        'SELECT work_id, user_id, title, type, summary FROM works WHERE work_id = %s',
        (work_id,), one=True,
    )
    if not work or work['user_id'] != user_id:
        return None
    lines = [f"作品：《{work['title']}》（{work.get('type') or 'novel'}）"]
    if work.get('summary'):
        lines.append('简介：' + str(work['summary'])[:300])
    chs = query(
        'SELECT chapter_no, title FROM chapters WHERE work_id = %s ORDER BY chapter_no DESC LIMIT 30',
        (work_id,),
    )
    if chs:
        titles = '；'.join(f"第{c['chapter_no']}章 {c['title'] or ''}" for c in reversed(chs))
        lines.append('章节结构：' + titles[:600])
    chars = query(
        'SELECT name, description, personality, background FROM rp_characters '
        'WHERE work_id = %s LIMIT 6',
        (work_id,),
    )
    if chars:
        parts = []
        for c in chars:
            brief = '；'.join(x for x in (c.get('description'), c.get('personality'), c.get('background')) if x)
            parts.append(f"{c['name']}（{brief[:120]}）")
        lines.append('主要角色：' + ' '.join(parts))
    lore = query(
        'SELECT title, content FROM work_lore WHERE work_id = %s ORDER BY lore_id LIMIT 10',
        (work_id,),
    )
    if lore:
        parts = []
        for l in lore:
            parts.append(f"{l['title']}：{str(l['content'])[:80]}")
        lines.append('作品设定（work_lore）：' + '；'.join(parts))

    # P4-E3：注入大纲中的「本章/下章计划」（beats + 钩子）
    plan = query('SELECT outline_json FROM book_plans WHERE work_id = %s', (work_id,), one=True)
    if plan and plan.get('outline_json'):
        try:
            outline = json.loads(plan['outline_json'])
        except (TypeError, ValueError):
            outline = None
        if isinstance(outline, list):
            planned = []

            def _walk(nodes):
                for n in nodes:
                    if not isinstance(n, dict):
                        continue
                    if n.get('kind') == 'chapter':
                        planned.append(n)
                    elif n.get('children'):
                        _walk(n.get('children'))

            _walk(outline)
            if planned:
                created = query(
                    'SELECT COUNT(*) AS c FROM chapters WHERE work_id = %s', (work_id,), one=True
                )['c']
                idx = min(created, len(planned) - 1)
                target = planned[idx]
                bits = []
                if target.get('title'):
                    bits.append(f"《{target['title']}》")
                if target.get('beats'):
                    bits.append('要点：' + str(target['beats'])[:150])
                if target.get('hook'):
                    bits.append('钩子：' + str(target['hook'])[:100])
                if bits:
                    lines.append('大纲参考（写作时应朝向）：' + '；'.join(bits))

    context = '\n'.join(lines)
    return context[:2000] if len(lines) > 1 else None


def ai_quota(func):
    """AI 调用配额装饰器（W1a）：登录后、进入逻辑前按用户限流，超限返回 429。"""
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        ok_, msg_ = check_ai_quota(session.get('user_id'))
        if not ok_:
            return fail(msg_, code=429)
        return func(*args, **kwargs)
    return wrapper


@write_bp.post('/continue')
@login_required
@ai_quota
def ai_continue():
    data = request.get_json()
    content = (data.get('content') or '').strip()
    style = (data.get('style') or '现代').strip()
    if not content:
        return fail('请提供上文内容')
    if len(content) > 20000:
        return fail('内容过长，最多20000字')

    # W2a：可选携带 work_id，注入作品设定/章节/角色上下文（仅本人作品）
    work_id = data.get('work_id')
    try:
        work_id = int(work_id) if work_id else None
    except (TypeError, ValueError):
        work_id = None
    context = _build_work_context(session.get('user_id'), work_id) if work_id else None
    references = _sanitize_references(data.get('references'))

    messages = build_continue(content, style, context=context, references=references)
    conv_key = str(uuid.uuid4())
    _save_conv(conv_key, 'user', content)

    def generate():
        full = []
        try:
            for chunk in chat_completion_stream(messages):
                full.append(chunk)
                yield f'data: {json.dumps({"chunk": chunk}, ensure_ascii=False)}\n\n'
            log_ai_call(current_app, session.get('user_id'), '/continue', success=True)
        except Exception as e:
            logger.error(f'AI continue error: {e}')
            log_ai_call(current_app, session.get('user_id'), '/continue', success=False, error=str(e))
            yield f'data: {json.dumps({"error": "续写生成失败，请稍后再试"}, ensure_ascii=False)}\n\n'
        # 流结束后保存（客户端仍连接时执行）
        try:
            _save_conv(conv_key, 'assistant', ''.join(full))
        except Exception as e:
            logger.error(f'Failed to save AI conversation: {e}')
        yield 'data: [DONE]\n\n'

    return Response(generate(), mimetype='text/event-stream; charset=utf-8')


@write_bp.post('/inspire')
@login_required
@ai_quota
def ai_inspire():
    data = request.get_json()
    keywords = (data.get('keywords') or '').strip()
    if not keywords:
        return fail('请输入关键词')
    if len(keywords) > 500:
        return fail('关键词过长，最多500字')

    messages = build_inspire(keywords)
    try:
        result = chat_completion(messages)
        log_ai_call(current_app, session.get('user_id'), '/inspire', success=True)
    except Exception as e:
        log_ai_call(current_app, session.get('user_id'), '/inspire', success=False, error=str(e))
        return fail('灵感生成失败，请稍后再试')
    conv_key = str(uuid.uuid4())
    _save_conv(conv_key, 'user', keywords)
    _save_conv(conv_key, 'assistant', result)
    return ok({'inspirations': result})


@write_bp.post('/outline')
@login_required
@ai_quota
def ai_outline():
    data = request.get_json()
    theme = (data.get('theme') or '').strip()
    if not theme:
        return fail('请输入故事主题')

    messages = build_outline(theme)
    try:
        result = chat_completion(messages)
        log_ai_call(current_app, session.get('user_id'), '/outline', success=True)
    except Exception as e:
        log_ai_call(current_app, session.get('user_id'), '/outline', success=False, error=str(e))
        return fail('大纲生成失败，请稍后再试')
    conv_key = str(uuid.uuid4())
    _save_conv(conv_key, 'user', theme)
    _save_conv(conv_key, 'assistant', result)
    return ok({'outline': result})


@write_bp.post('/character')
@login_required
@ai_quota
def ai_character():
    data = request.get_json()
    story_context = (data.get('story_context') or '').strip()
    if not story_context:
        return fail('请提供故事背景')

    messages = build_character(story_context)
    try:
        result = chat_completion(messages)
        log_ai_call(current_app, session.get('user_id'), '/character', success=True)
    except Exception as e:
        log_ai_call(current_app, session.get('user_id'), '/character', success=False, error=str(e))
        return fail('角色生成失败，请稍后再试')
    conv_key = str(uuid.uuid4())
    _save_conv(conv_key, 'user', story_context)
    _save_conv(conv_key, 'assistant', result)
    return ok({'characters': result})


@write_bp.post('/polish')
@login_required
@ai_quota
def ai_polish():
    data = request.get_json()
    text = (data.get('text') or '').strip()
    mode = (data.get('mode') or '流畅').strip()
    if not text:
        return fail('请提供需要润色的文字')
    if len(text) > 20000:
        return fail('内容过长，最多20000字')

    references = _sanitize_references(data.get('references'))
    messages = build_polish(text, mode, references=references)
    try:
        result = chat_completion(messages)
        log_ai_call(current_app, session.get('user_id'), '/polish', success=True)
    except Exception as e:
        log_ai_call(current_app, session.get('user_id'), '/polish', success=False, error=str(e))
        return fail('润色失败，请稍后再试')
    conv_key = str(uuid.uuid4())
    _save_conv(conv_key, 'user', f'[{mode}] {text}')
    _save_conv(conv_key, 'assistant', result)
    return ok({'polished': result})


@write_bp.post('/prompt')
@login_required
@ai_quota
def ai_prompt():
    data = request.get_json()
    context = (data.get('context') or '').strip()
    if not context:
        return fail('请描述当前卡文的情节')

    messages = build_prompt_suggestion(context)
    try:
        result = chat_completion(messages)
        log_ai_call(current_app, session.get('user_id'), '/prompt', success=True)
    except Exception as e:
        log_ai_call(current_app, session.get('user_id'), '/prompt', success=False, error=str(e))
        return fail('剧情建议生成失败，请稍后再试')
    conv_key = str(uuid.uuid4())
    _save_conv(conv_key, 'user', context)
    _save_conv(conv_key, 'assistant', result)
    return ok({'suggestions': result})


@write_bp.post('/chat')
@login_required
@ai_quota
def ai_chat():
    data = request.get_json()
    message = (data.get('message') or '').strip()
    history = data.get('history') or []  # [{role, content}, ...]
    session_key = (data.get('session_key') or '').strip() or str(uuid.uuid4())

    if not message:
        return fail('请输入消息')
    if len(message) > 5000:
        return fail('消息过长，最多5000字')
    if len(history) > 100:
        return fail('对话历史过长')

    # Build multi-turn messages: system + history + new user message
    messages = [build_chat_system()]
    for h in history[-50:]:  # Keep last 50 turns to avoid token limit
        role = h.get('role', 'user')
        if role in ('user', 'assistant'):
            messages.append({'role': role, 'content': h.get('content', '')})
    messages.append({'role': 'user', 'content': message})

    # W4a：对话同样支持注入参考素材
    references = _sanitize_references(data.get('references'))
    ref_block = build_references_text(references)
    if ref_block:
        messages[-1] = {'role': 'user', 'content': messages[-1]['content'] + ref_block}

    _save_conv(session_key, 'user', message)

    def generate():
        full = []
        try:
            for chunk in chat_completion_stream(messages):
                full.append(chunk)
                yield f'data: {json.dumps({"chunk": chunk, "session_key": session_key}, ensure_ascii=False)}\n\n'
            log_ai_call(current_app, session.get('user_id'), '/chat', success=True)
        except Exception as e:
            logger.error(f'AI chat error: {e}')
            log_ai_call(current_app, session.get('user_id'), '/chat', success=False, error=str(e))
            yield f'data: {json.dumps({"error": "对话生成失败，请稍后再试"}, ensure_ascii=False)}\n\n'
        try:
            _save_conv(session_key, 'assistant', ''.join(full))
        except Exception as e:
            logger.error(f'Failed to save AI conversation: {e}')
        yield 'data: [DONE]\n\n'

    return Response(generate(), mimetype='text/event-stream; charset=utf-8')


@write_bp.post('/diagnose')
@login_required
@ai_quota
def ai_diagnose():
    data = request.get_json()
    content = (data.get('content') or '').strip()
    if not content:
        return fail('请提供需要诊断的文字')

    if len(content) < 50:
        return fail('文字太短，至少需要50字才能进行诊断')
    if len(content) > 20000:
        return fail('文字过长，最多20000字')

    messages = build_diagnose(content)
    try:
        result = chat_completion(messages)
        log_ai_call(current_app, session.get('user_id'), '/diagnose', success=True)
    except Exception as e:
        log_ai_call(current_app, session.get('user_id'), '/diagnose', success=False, error=str(e))
        return fail('诊断失败，请稍后再试')
    conv_key = str(uuid.uuid4())
    _save_conv(conv_key, 'user', f'[诊断] {content[:200]}...')
    _save_conv(conv_key, 'assistant', result)
    return ok({'diagnosis': result})


@write_bp.post('/summary')
@login_required
@ai_quota
def ai_summary():
    """AI 章节摘要"""
    data = request.get_json()
    chapter_title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    if not content:
        return fail('请提供章节内容')
    if len(content) < 100:
        return fail('内容太短，至少需要100字才能生成摘要')
    if len(content) > 30000:
        return fail('章节内容过长，最多30000字')

    messages = build_summary(chapter_title, content)
    try:
        result = chat_completion(messages)
        log_ai_call(current_app, session.get('user_id'), '/summary', success=True)
    except Exception as e:
        log_ai_call(current_app, session.get('user_id'), '/summary', success=False, error=str(e))
        return fail('摘要生成失败，请稍后再试')
    conv_key = str(uuid.uuid4())
    _save_conv(conv_key, 'user', f'[摘要] {chapter_title}: {content[:100]}...')
    _save_conv(conv_key, 'assistant', result)
    return ok({'summary': result})


# ---------------------------------------------------------------------------
# P4-E3b：第一轮结构审校（AI 辅助，对照大纲审全书结构/节奏）
# ---------------------------------------------------------------------------

@write_bp.post('/struct')
@login_required
@ai_quota
def ai_struct_review():
    data = request.get_json() or {}
    work_id = data.get('work_id')
    try:
        work_id = int(work_id) if work_id else None
    except (TypeError, ValueError):
        work_id = None
    if not work_id:
        return fail('缺少作品ID')
    work = query('SELECT work_id, user_id, title FROM works WHERE work_id = %s', (work_id,), one=True)
    if not work or work['user_id'] != session.get('user_id'):
        return fail('作品不存在', code=404)

    chapters = query(
        'SELECT chapter_no, title, word_count, content FROM chapters '
        'WHERE work_id = %s ORDER BY chapter_no LIMIT 60',
        (work_id,),
    )
    if not chapters:
        return fail('作品还没有章节内容')

    lines = []
    for c in chapters:
        head = ' '.join(str(c.get('content') or '').split())[:150]
        lines.append(f"第{c['chapter_no']}章《{c.get('title') or ''}》（{c.get('word_count') or 0}字）：{head}")
    chapters_summary = '\n'.join(lines)

    outline_text = ''
    plan = query('SELECT outline_json FROM book_plans WHERE work_id = %s', (work_id,), one=True)
    if plan and plan.get('outline_json'):
        try:
            outline = json.loads(plan['outline_json'])
        except (TypeError, ValueError):
            outline = None
        if isinstance(outline, list):
            texts = []

            def _walk(nodes):
                for n in nodes:
                    if not isinstance(n, dict):
                        continue
                    if n.get('kind') in ('part', 'chapter') and n.get('title'):
                        texts.append(str(n['title']))
                    if n.get('children'):
                        _walk(n.get('children'))

            _walk(outline)
            outline_text = ' / '.join(texts)

    messages = build_struct_review(chapters_summary, outline_text or None)
    try:
        result = chat_completion(messages)
        log_ai_call(current_app, session.get('user_id'), '/struct', success=True)
    except Exception as e:
        log_ai_call(current_app, session.get('user_id'), '/struct', success=False, error=str(e))
        return fail('结构审校生成失败，请稍后再试')
    return ok({'report': result})


# ---------------------------------------------------------------------------
# W3a：AI 会话管理（历史列表 / 详情 / 删除 / 自动清理）
# ---------------------------------------------------------------------------

def _prune_conversations(user_id, keep=100):
    """只保留每个用户最近的 keep 个会话（按最近消息时间），防止 ai_conversations 无限增长。"""
    if keep <= 0:
        execute('DELETE FROM ai_conversations WHERE user_id = %s', (user_id,))
        return
    keys = [r['session_key'] for r in query(
        'SELECT session_key, MAX(created_at) AS mx, MAX(conv_id) AS mid '
        'FROM ai_conversations WHERE user_id = %s '
        'GROUP BY session_key ORDER BY mx DESC, mid DESC LIMIT %s',
        (user_id, keep),
    )]
    if not keys:
        return
    marks = ','.join(['%s'] * len(keys))
    execute(
        f'DELETE FROM ai_conversations WHERE user_id = %s AND session_key NOT IN ({marks})',
        [user_id] + keys,
    )


@write_bp.get('/conversations')
@login_required
def list_conversations():
    user_id = session['user_id']
    _prune_conversations(user_id)
    rows = query(
        'SELECT c.session_key, MAX(c.created_at) AS updated_at, '
        '(SELECT cc.content FROM ai_conversations cc WHERE cc.user_id = c.user_id '
        '  AND cc.session_key = c.session_key AND cc.role = \'user\' '
        '  ORDER BY cc.conv_id DESC LIMIT 1) AS last_user_msg, '
        'COUNT(*) AS msg_count '
        'FROM ai_conversations c WHERE c.user_id = %s '
        'GROUP BY c.session_key ORDER BY updated_at DESC, MAX(c.conv_id) DESC',
        (user_id,),
    )
    sessions = []
    for r in rows:
        sessions.append({
            'session_key': r['session_key'],
            'updated_at': _fmt(r['updated_at']),
            'preview': (r['last_user_msg'] or '')[:60],
            'msg_count': r['msg_count'],
        })
    return ok({'sessions': sessions})


@write_bp.get('/conversations/<session_key>')
@login_required
def get_conversation(session_key):
    user_id = session['user_id']
    rows = query(
        'SELECT conv_id, role, content, created_at FROM ai_conversations '
        'WHERE user_id = %s AND session_key = %s ORDER BY conv_id ASC',
        (user_id, session_key),
    )
    if not rows:
        return fail('会话不存在', code=404)
    messages = []
    for r in rows:
        messages.append({
            'role': r['role'],
            'content': r['content'],
            'created_at': _fmt(r['created_at']),
        })
    return ok({'session_key': session_key, 'messages': messages})


@write_bp.delete('/conversations/<session_key>')
@login_required
def delete_conversation(session_key):
    user_id = session['user_id']
    execute(
        'DELETE FROM ai_conversations WHERE user_id = %s AND session_key = %s',
        (user_id, session_key),
    )
    return ok(msg='会话已删除')


# ---------------------------------------------------------------------------
# 划词快捷操作（2026-09）：选中文字 → 查错 / 翻译解释 / 意境找句
# ---------------------------------------------------------------------------

def _extract_json(text):
    """从 AI 输出中提取 JSON（兼容 markdown 代码块包裹与前后杂文）。"""
    if not text:
        return None
    t = text.strip()
    if t.startswith('```'):
        # 剥掉 ```json ... ``` 围栏
        lines = t.splitlines()
        if lines and lines[0].strip().startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        t = '\n'.join(lines).strip()
    # 找到第一个 { 或 [ 与配对的结尾
    start = -1
    for i, ch in enumerate(t):
        if ch in '{[':
            start = i
            break
    if start < 0:
        return None
    stack = []
    for i in range(start, len(t)):
        ch = t[i]
        if ch in '{[':
            stack.append(ch)
        elif ch in '}]':
            if stack and ((ch == '}' and stack[-1] == '{') or (ch == ']' and stack[-1] == '[')):
                stack.pop()
                if not stack:
                    end = i + 1
                    break
    try:
        return json.loads(t[start:end])
    except (json.JSONDecodeError, UnboundLocalError, ValueError):
        return None


@write_bp.post('/fix')
@login_required
@ai_quota
def ai_fix():
    """错字/病句检查：返回结构化 [{original, suggestion, reason}]，前端可一键替换。"""
    data = request.get_json()
    text = (data.get('text') or '').strip()
    if not text:
        return fail('请先选中需要检查的文字')
    if len(text) < 4:
        return fail('选中的文字太短，至少 4 个字')
    if len(text) > 5000:
        return fail('内容过长，最多检查 5000 字')

    messages = build_fix(text)
    try:
        raw = chat_completion(messages, temperature=0.2)
        log_ai_call(current_app, session.get('user_id'), '/fix', success=True)
    except Exception as e:
        logger.error(f'AI fix error: {e}')
        log_ai_call(current_app, session.get('user_id'), '/fix', success=False, error=str(e))
        return fail('检查失败，请稍后再试')

    fixes = _extract_json(raw)
    if not isinstance(fixes, list):
        # 单对象兜底：包一层
        if isinstance(fixes, dict):
            fixes = [fixes]
        else:
            fixes = []
    cleaned = []
    for f in fixes[:20]:
        if not isinstance(f, dict):
            continue
        original = str(f.get('original') or '').strip()
        suggestion = str(f.get('suggestion') or '').strip()
        reason = str(f.get('reason') or '').strip()
        if original and suggestion and original in text:
            cleaned.append({
                'original': original[:200],
                'suggestion': suggestion[:200],
                'reason': reason[:200],
            })
    return ok({'fixes': cleaned})


@write_bp.post('/interpret')
@login_required
@ai_quota
def ai_interpret():
    """翻译/解释选中内容（古诗句→白话释义 + 意境 + 用典）。"""
    data = request.get_json()
    text = (data.get('text') or '').strip()
    if not text:
        return fail('请先选中需要解释的内容')
    if len(text) > 2000:
        return fail('内容过长，最多解释 2000 字')

    messages = build_interpret(text)
    try:
        result = chat_completion(messages, temperature=0.4)
        log_ai_call(current_app, session.get('user_id'), '/interpret', success=True)
    except Exception as e:
        logger.error(f'AI interpret error: {e}')
        log_ai_call(current_app, session.get('user_id'), '/interpret', success=False, error=str(e))
        return fail('解释失败，请稍后再试')
    return ok({'explanation': result})


# 意境找句缓存：intent → (ts, result)；TTL 10 分钟，防重复消耗 token
_FIND_LINES_CACHE = {}
_FIND_LINES_TTL = 600
_FIND_LINES_CACHE_MAX = 50


def _load_find_pool():
    """拉全量本地素材池（诗词 + 素材），每条压缩为单行文本。"""
    rows = query(
        "SELECT 'poem' AS kind, poem_id AS id, title, author, content, category "
        'FROM poems ORDER BY poem_id'
    )
    mats = query(
        "SELECT 'material' AS kind, material_id AS id, title, content, category "
        'FROM materials ORDER BY material_id'
    )
    pool = []
    for r in rows + mats:
        content = ' '.join(str(r.get('content') or '').split())
        if not content:
            continue
        pool.append({
            'kind': r['kind'],
            'id': r['id'],
            'title': str(r.get('title') or ''),
            'author': str(r.get('author') or ''),
            'category': str(r.get('category') or ''),
            'content': content,
        })
    return pool


@write_bp.post('/find-lines')
@login_required
@ai_quota
def ai_find_lines():
    """意境找句：本地库语义匹配（AI 打分排序）+ AI 原创句子。"""
    data = request.get_json()
    intent = (data.get('intent') or '').strip()
    if not intent:
        return fail('请描述你想描写的意境，比如"夕阳下离别的惆怅"')
    if len(intent) > 200:
        return fail('意境描述过长，最多 200 字')

    cache_key = intent
    hit = _FIND_LINES_CACHE.get(cache_key)
    now = time.time()
    if hit and now - hit[0] < _FIND_LINES_TTL:
        return ok(hit[1])

    pool = _load_find_pool()
    if not pool:
        return fail('本地素材库为空，请先在灵感馆收录句子')

    # 素材池压缩：每条最多保留 60 字，总长限制在 12000 字内
    lines = []
    for i, p in enumerate(pool):
        snippet = p['content'][:60]
        head = f"[{i}] {p['kind']} "
        if p['title']:
            head += f"《{p['title']}》"
        if p['author']:
            head += f"（{p['author']}）"
        elif p.get('category'):
            head += f"（{p['category']}）"
        lines.append(f'{head}：{snippet}')
    pool_text = '\n'.join(lines)[:12000]

    messages = build_find_lines(intent, pool_text)
    try:
        raw = chat_completion(messages, temperature=0.6, max_tokens=2048)
        log_ai_call(current_app, session.get('user_id'), '/find-lines', success=True)
    except Exception as e:
        logger.error(f'AI find-lines error: {e}')
        log_ai_call(current_app, session.get('user_id'), '/find-lines', success=False, error=str(e))
        return fail('找句失败，请稍后再试')

    parsed = _extract_json(raw)
    picks, created = [], []
    if isinstance(parsed, dict):
        picks = parsed.get('picks') if isinstance(parsed.get('picks'), list) else []
        created_raw = parsed.get('created') if isinstance(parsed.get('created'), list) else []
        created = [str(c).strip() for c in created_raw if str(c).strip()][:4]
    elif isinstance(parsed, list):
        # 兜底：如果是数组说明模型只给了 picks
        picks = parsed

    local = []
    for p in picks[:6]:
        if not isinstance(p, dict):
            continue
        try:
            idx = int(p.get('idx'))
        except (TypeError, ValueError):
            continue
        if 0 <= idx < len(pool):
            item = pool[idx]
            local.append({
                'kind': item['kind'],
                'id': item['id'],
                'title': item['title'],
                'author': item['author'],
                'category': item['category'],
                'content': item['content'],
                'reason': str(p.get('reason') or '')[:120],
            })
    # 去重（同一句可能被选两次）
    seen = set()
    uniq_local = []
    for it in local:
        key = it['kind'] + ':' + str(it['id'])
        if key in seen:
            continue
        seen.add(key)
        uniq_local.append(it)
    if not uniq_local and not created:
        return fail('没有找到合适的句子，换个描述试试')

    result = {'intent': intent, 'local': uniq_local, 'created': created}
    _FIND_LINES_CACHE[cache_key] = (now, result)
    if len(_FIND_LINES_CACHE) > _FIND_LINES_CACHE_MAX:
        # 淘汰最旧
        oldest = min(_FIND_LINES_CACHE, key=lambda k: _FIND_LINES_CACHE[k][0])
        _FIND_LINES_CACHE.pop(oldest, None)
    return ok(result)
