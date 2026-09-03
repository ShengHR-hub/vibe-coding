import logging
from flask import Blueprint, request, Response, session, current_app
from database.db import query, execute
from utils.helpers import ok, fail, login_required, check_ai_quota
from utils.mimos import chat_completion, chat_completion_stream
from utils.prompt_builder import (
    build_continue, build_inspire, build_outline,
    build_character, build_polish, build_prompt_suggestion,
    build_chat_system, build_diagnose, build_summary
)
from utils.logger import log_ai_call
import json, uuid

logger = logging.getLogger(__name__)

write_bp = Blueprint('write', __name__)


def _save_conv(session_key, role, content):
    # W1d：入库内容截断，防止超长输出撑爆 ai_conversations
    content = (content or '')[:20000]
    execute(
        'INSERT INTO ai_conversations (user_id, session_key, role, content) VALUES (%s, %s, %s, %s)',
        (session.get('user_id'), session_key, role, content)
    )


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

    messages = build_continue(content, style, context=context)
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

    messages = build_polish(text, mode)
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
