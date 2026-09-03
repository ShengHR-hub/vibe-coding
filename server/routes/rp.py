import logging
from flask import Blueprint, request, session, Response
from database.db import query, execute
from utils.helpers import ok, fail, login_required
from utils.mimos import chat_completion, chat_completion_stream
from utils.prompt_builder import build_rp_extract, build_rp_chat
import json, uuid

logger = logging.getLogger(__name__)

rp_bp = Blueprint('rp', __name__)


@rp_bp.get('/<int:work_id>/characters')
@login_required
def list_characters(work_id):
    chars = query('SELECT * FROM rp_characters WHERE work_id = %s ORDER BY char_id', (work_id,))
    return ok({'characters': chars})


@rp_bp.post('/<int:work_id>/characters')
@login_required
def create_character(work_id):
    work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)

    data = request.get_json()
    name = (data.get('name') or '').strip()
    if not name:
        return fail('角色名不能为空')

    char_id = execute(
        'INSERT INTO rp_characters (work_id, name, description, personality, background, speaking_style) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (work_id, name,
         (data.get('description') or '').strip(),
         (data.get('personality') or '').strip(),
         (data.get('background') or '').strip(),
         (data.get('speaking_style') or '').strip())
    )
    return ok({'char_id': char_id}, msg='角色已创建')


@rp_bp.post('/<int:work_id>/characters/extract')
@login_required
def extract_characters(work_id):
    work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)

    # 取前几章内容作为分析素材
    chapters = query(
        'SELECT content FROM chapters WHERE work_id = %s ORDER BY chapter_no LIMIT 5',
        (work_id,)
    )
    if not chapters:
        return fail('作品没有章节内容')

    content = '\n\n'.join(ch['content'] for ch in chapters if ch['content'])
    if len(content) < 100:
        return fail('内容太短，无法提取角色')

    messages = build_rp_extract(content)
    try:
        result = chat_completion(messages)
    except Exception:
        return fail('AI 提取失败，请稍后再试')

    # 解析 JSON
    try:
        # 尝试提取 JSON 部分
        import re
        json_match = re.search(r'\[.*\]', result, re.DOTALL)
        if json_match:
            characters = json.loads(json_match.group())
        else:
            characters = json.loads(result)
    except (json.JSONDecodeError, Exception):
        return fail('AI 返回格式异常，请重试')

    # 存入数据库
    created = []
    for c in characters[:8]:
        name = (c.get('name') or '').strip()
        if not name:
            continue
        char_id = execute(
            'INSERT INTO rp_characters (work_id, name, description, personality, background, speaking_style) '
            'VALUES (%s, %s, %s, %s, %s, %s)',
            (work_id, name,
             (c.get('description') or '').strip(),
             (c.get('personality') or '').strip(),
             (c.get('background') or '').strip(),
             (c.get('speaking_style') or '').strip())
        )
        created.append({'char_id': char_id, 'name': name})

    return ok({'characters': created, 'count': len(created)}, msg=f'已提取 {len(created)} 个角色')


@rp_bp.post('/chat')
@login_required
def rp_chat():
    data = request.get_json()
    char_id = data.get('char_id')
    message = (data.get('message') or '').strip()
    history = data.get('history') or []

    if not message:
        return fail('请输入消息')
    if not char_id:
        return fail('请选择角色')

    char = query('SELECT * FROM rp_characters WHERE char_id = %s', (char_id,), one=True)
    if not char:
        return fail('角色不存在', code=404)

    messages = build_rp_chat(char, history, message)

    def generate():
        full = []
        try:
            for chunk in chat_completion_stream(messages):
                full.append(chunk)
                yield f'data: {json.dumps({"chunk": chunk}, ensure_ascii=False)}\n\n'
        except Exception as e:
            logger.error(f'RP chat error: {e}')
            yield f'data: {json.dumps({"error": "对话生成失败，请稍后再试"}, ensure_ascii=False)}\n\n'
        yield 'data: [DONE]\n\n'

    return Response(generate(), mimetype='text/event-stream; charset=utf-8')


@rp_bp.delete('/characters/<int:char_id>')
@login_required
def delete_character(char_id):
    char = query(
        'SELECT rc.* FROM rp_characters rc JOIN works w ON rc.work_id = w.work_id WHERE rc.char_id = %s AND w.user_id = %s',
        (char_id, session['user_id']), one=True)
    if not char:
        return fail('角色不存在', code=404)
    execute('DELETE FROM rp_characters WHERE char_id = %s', (char_id,))
    return ok(msg='角色已删除')
