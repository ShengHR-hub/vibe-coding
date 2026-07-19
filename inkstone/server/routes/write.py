import logging
from flask import Blueprint, request, Response, session, current_app
from database.db import query, execute
from utils.helpers import ok, fail, login_required
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
    execute(
        'INSERT INTO ai_conversations (user_id, session_key, role, content) VALUES (%s, %s, %s, %s)',
        (session.get('user_id'), session_key, role, content)
    )


@write_bp.post('/continue')
@login_required
def ai_continue():
    data = request.get_json()
    content = (data.get('content') or '').strip()
    style = (data.get('style') or '现代').strip()
    if not content:
        return fail('请提供上文内容')
    if len(content) > 20000:
        return fail('内容过长，最多20000字')

    messages = build_continue(content, style)
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
def ai_diagnose():
    data = request.get_json()
    content = (data.get('content') or '').strip()
    if not content:
        return fail('请提供需要诊断的文字')

    if len(content) < 50:
        return fail('文字太短，至少需要50字才能进行诊断')

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
def ai_summary():
    """AI 章节摘要"""
    data = request.get_json()
    chapter_title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    if not content:
        return fail('请提供章节内容')
    if len(content) < 100:
        return fail('内容太短，至少需要100字才能生成摘要')

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
