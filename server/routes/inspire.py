"""灵感收藏（F2）：诗词/素材的个人收藏，仅本人可读/删。"""
from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, login_required, _fmt

inspire_bp = Blueprint('inspire', __name__)

_ALLOWED_TYPES = ('poem', 'material')


def _fetch_source(item_type, ref_id):
    """取源内容（用于收藏快照）；不存在返回 None。"""
    if item_type == 'poem':
        return query('SELECT poem_id, title, content, author, dynasty FROM poems WHERE poem_id = %s', (ref_id,), one=True)
    return query('SELECT material_id, title, content, category FROM materials WHERE material_id = %s', (ref_id,), one=True)


@inspire_bp.get('/favorites')
@login_required
def list_favorites():
    user_id = session['user_id']
    rows = query(
        'SELECT * FROM inspiration_favorites WHERE user_id = %s ORDER BY created_at DESC',
        (user_id,),
    )
    items = []
    for r in rows:
        items.append({
            'fav_id': r['fav_id'],
            'item_type': r['item_type'],
            'ref_id': r['ref_id'],
            'title': r['title'],
            'content': r['content'],
            'author': r['author'],
            'created_at': _fmt(r['created_at']),
        })
    return ok({'items': items})


@inspire_bp.post('/favorites')
@login_required
def add_favorite():
    data = request.get_json() or {}
    item_type = (data.get('item_type') or '').strip()
    try:
        ref_id = int(data.get('ref_id') or 0)
    except (TypeError, ValueError):
        ref_id = 0
    if item_type not in _ALLOWED_TYPES or ref_id <= 0:
        return fail('参数无效')
    src = _fetch_source(item_type, ref_id)
    if not src:
        return fail('内容不存在', code=404)
    title = src.get('title') or (src.get('category') or '')
    author = src.get('author') or ''
    execute(
        'INSERT IGNORE INTO inspiration_favorites '
        '(user_id, item_type, ref_id, title, content, author) VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], item_type, ref_id, title[:200], src['content'][:5000], author[:100]),
    )
    return ok(msg='已收藏')


@inspire_bp.delete('/favorites/<item_type>/<int:ref_id>')
@login_required
def remove_favorite(item_type, ref_id):
    if item_type not in _ALLOWED_TYPES:
        return fail('参数无效')
    execute(
        'DELETE FROM inspiration_favorites WHERE user_id = %s AND item_type = %s AND ref_id = %s',
        (session['user_id'], item_type, ref_id),
    )
    return ok(msg='已取消收藏')
