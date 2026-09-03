from flask import Blueprint, request
from database.db import query
from utils.helpers import ok, fail, login_required
from utils.mimos import chat_completion
from utils.prompt_builder import build_character_graph, build_timeline
import json

graph_bp = Blueprint('graph', __name__)


@graph_bp.get('/<int:work_id>/characters')
@login_required
def get_characters(work_id):
    work = query("SELECT * FROM works WHERE work_id = %s AND status = 'published'", (work_id,), one=True)
    if not work:
        return fail('作品不存在或未公开', code=404)

    chapters = query('SELECT title, content FROM chapters WHERE work_id = %s ORDER BY chapter_no', (work_id,))
    if not chapters:
        return fail('作品暂无章节内容')

    combined = '\n\n'.join(c['content'][:2000] for c in chapters if c['content'])[:5000]
    if not combined.strip():
        return fail('暂无足够文本内容进行分析')

    try:
        messages = build_character_graph(combined)
        result = chat_completion(messages, temperature=0.3, max_tokens=1024)
        result = result.strip()
        if result.startswith('```'):
            result = result.split('\n', 1)[1].rsplit('\n', 1)[0]
        graph_data = json.loads(result)
        return ok({'graph': graph_data, 'work_title': work['title']})
    except (json.JSONDecodeError, KeyError, ValueError):
        return fail('角色分析失败，请稍后再试')


@graph_bp.get('/<int:work_id>/timeline')
@login_required
def get_timeline(work_id):
    work = query("SELECT * FROM works WHERE work_id = %s AND status = 'published'", (work_id,), one=True)
    if not work:
        return fail('作品不存在或未公开', code=404)

    chapters = query('SELECT chapter_no, title, content FROM chapters WHERE work_id = %s ORDER BY chapter_no', (work_id,))
    if not chapters:
        return fail('作品暂无章节内容')

    # Build summary per chapter
    parts = []
    for c in chapters:
        txt = c['content'][:1500] if c['content'] else ''
        parts.append(f"第{c['chapter_no']}章 {c['title']}\n{txt}")
    combined = '\n\n'.join(parts)[:5000]

    if not combined.strip():
        return fail('暂无足够文本内容进行分析')

    try:
        messages = build_timeline(combined)
        result = chat_completion(messages, temperature=0.3, max_tokens=1024)
        result = result.strip()
        if result.startswith('```'):
            result = result.split('\n', 1)[1].rsplit('\n', 1)[0]
        events = json.loads(result)
        return ok({'timeline': events, 'work_title': work['title']})
    except (json.JSONDecodeError, KeyError, ValueError):
        return fail('时间线分析失败，请稍后再试')
