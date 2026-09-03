from flask import Blueprint, request, session
from database.db import query
from utils.helpers import ok, fail, login_required
from utils.mimos import chat_completion
from utils.prompt_builder import build_book_review, build_recommendation
import json

review_bp = Blueprint('review', __name__)


@review_bp.post('/generate')
@login_required
def generate_review():
    data = request.get_json() or {}
    work_id = data.get('work_id')

    if not work_id:
        return fail('缺少作品ID', code=400)

    work = query("SELECT * FROM works WHERE work_id = %s AND status = 'published'", (work_id,), one=True)
    if not work:
        return fail('作品不存在或未公开', code=404)

    chapters = query('SELECT title, content FROM chapters WHERE work_id = %s ORDER BY chapter_no', (work_id,))
    if not chapters:
        return fail('作品暂无章节内容')

    combined = '\n\n'.join(c['content'][:2000] for c in chapters if c['content'])[:6000]
    if not combined.strip():
        return fail('暂无足够文本内容')

    try:
        messages = build_book_review(f"《{work['title']}》\n类型: {work['type']}\n标签: {work.get('tags','')}\n\n正文:\n{combined}")
        result = chat_completion(messages, temperature=0.7, max_tokens=1024)
        return ok({'review': result, 'work_title': work['title']})
    except (json.JSONDecodeError, KeyError, ValueError):
        return fail('书评生成失败，请稍后再试')


@review_bp.get('/recommend')
@login_required
def recommend():
    user_id = session['user_id']

    # Collect user's reading preferences
    liked_works = query('''
        SELECT w.type, w.tags FROM work_likes wl
        JOIN works w ON wl.work_id = w.work_id
        WHERE wl.user_id = %s ORDER BY wl.created_at DESC LIMIT 10
    ''', (user_id,))

    fav_works = query('''
        SELECT w.type, w.tags FROM favorites f
        JOIN works w ON f.work_id = w.work_id
        WHERE f.user_id = %s ORDER BY f.created_at DESC LIMIT 10
    ''', (user_id,))

    all_prefs = liked_works + fav_works
    if not all_prefs:
        # Fallback: recommend popular works
        rows = query('''
            SELECT w.*, u.username, u.avatar
            FROM works w JOIN users u ON w.user_id = u.user_id
            WHERE w.status = 'published'
            ORDER BY (w.likes_count * 2 + w.favorites_count * 5) DESC
            LIMIT 10
        ''')
        return ok({'items': rows, 'source': 'popular'})

    # Build preference profile
    types = list(set(w['type'] for w in all_prefs if w['type']))
    tags = list(set(t for w in all_prefs if w['tags'] for t in w['tags'].split(',')))
    profile = f"偏好的作品类型: {', '.join(types)}\n偏好的标签: {', '.join(tags)}"

    try:
        messages = build_recommendation(profile)
        result = chat_completion(messages, temperature=0.5, max_tokens=1024)
        result = result.strip()
        if result.startswith('```'):
            result = result.split('\n', 1)[1].rsplit('\n', 1)[0]
        ai_rec = json.loads(result)

        # Query DB based on AI-recommended tags
        rec_tags = ai_rec.get('tags', tags)[:5]
        rec_types = ai_rec.get('types', types)

        conditions = ["w.status = 'published'"]
        params = []
        if rec_tags:
            tag_clauses = ' OR '.join(['w.tags LIKE %s'] * len(rec_tags))
            conditions.append(f'({tag_clauses})')
            params.extend([f'%{t}%' for t in rec_tags])
        if rec_types:
            placeholders = ','.join(['%s'] * len(rec_types))
            conditions.append(f'w.type IN ({placeholders})')
            params.extend(rec_types)

        where = ' AND '.join(conditions)
        rows = query(f'''
            SELECT w.*, u.username, u.avatar
            FROM works w JOIN users u ON w.user_id = u.user_id
            WHERE {where}
            ORDER BY (w.likes_count * 2 + w.favorites_count * 5) DESC
            LIMIT 10
        ''', params)

        return ok({'items': rows, 'reason': ai_rec.get('reason', ''), 'source': 'ai'})
    except (json.JSONDecodeError, KeyError, ValueError):
        return fail('推荐生成失败，请稍后再试')


@review_bp.get('/similar/<int:work_id>')
def get_similar(work_id):
    work = query("SELECT * FROM works WHERE work_id = %s AND status = 'published'", (work_id,), one=True)
    if not work:
        return fail('作品不存在或未公开', code=404)

    # DB-based similar: match by tags and type
    tags = work.get('tags', '')
    tag_parts = [t.strip() for t in tags.split(',') if t.strip()]

    conditions = ["w.status = 'published'", 'w.work_id != %s']
    params = [work_id]

    if tag_parts:
        tag_clauses = ' OR '.join(['w.tags LIKE %s'] * len(tag_parts))
        conditions.append(f'({tag_clauses})')
        params.extend([f'%{t}%' for t in tag_parts])

    conditions.append('w.type = %s')
    params.append(work['type'])

    where = ' AND '.join(conditions)
    candidates = query(f'''
        SELECT w.*, u.username, u.avatar
        FROM works w JOIN users u ON w.user_id = u.user_id
        WHERE {where}
        ORDER BY (w.likes_count * 2 + w.favorites_count * 5) DESC
        LIMIT 10
    ''', params)

    return ok({'items': candidates, 'work_title': work['title']})
