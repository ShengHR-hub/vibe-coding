import logging
import requests as http_requests
import json
from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, login_required

logger = logging.getLogger(__name__)

poems_bp = Blueprint('poems', __name__)


@poems_bp.get('')
def list_poems():
    """List poems with optional category filter and pagination."""
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(50, request.args.get('page_size', 20, type=int))
    category = request.args.get('category', '').strip()

    base = 'FROM poems'
    params = []
    if category:
        base += ' WHERE category = %s'
        params.append(category)

    total = query(f'SELECT COUNT(*) as cnt {base}', params, one=True)['cnt']
    rows = query(
        f'SELECT * {base} ORDER BY poem_id LIMIT %s OFFSET %s',
        params + [page_size, (page - 1) * page_size]
    )
    return ok({'poems': rows, 'total': total, 'page': page, 'page_size': page_size})


@poems_bp.get('/categories')
def categories():
    """Get all categories with poem counts."""
    rows = query('SELECT category, COUNT(*) as count FROM poems GROUP BY category ORDER BY count DESC')
    return ok({'categories': rows})


@poems_bp.get('/search')
def search():
    """Search poems by keyword in title, author, or content."""
    q = request.args.get('q', '').strip()
    if not q:
        return fail('请输入搜索关键词')
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(50, request.args.get('page_size', 20, type=int))
    like = f'%{q}%'
    base = 'FROM poems WHERE title LIKE %s OR author LIKE %s OR content LIKE %s'
    params = [like, like, like]

    total = query(f'SELECT COUNT(*) as cnt {base}', params, one=True)['cnt']
    rows = query(
        f'SELECT * {base} ORDER BY poem_id LIMIT %s OFFSET %s',
        params + [page_size, (page - 1) * page_size]
    )
    return ok({'poems': rows, 'total': total, 'page': page, 'page_size': page_size, 'keyword': q})


@poems_bp.get('/random')
def random_poem():
    """Get a random poem, optionally filtered by category."""
    category = request.args.get('category', '').strip()
    count = min(10, request.args.get('count', 1, type=int))

    if category:
        rows = query('SELECT * FROM poems WHERE category = %s ORDER BY RAND() LIMIT %s', [category, count])
    else:
        rows = query('SELECT * FROM poems ORDER BY RAND() LIMIT %s', [count])
    return ok({'poems': rows})


@poems_bp.get('/featured')
def featured():
    """Get daily featured poems — same set all day, rotates automatically each day."""
    count = min(10, request.args.get('count', 7, type=int))
    rows = query(
        'SELECT * FROM poems ORDER BY RAND(UNIX_TIMESTAMP(CURDATE())) LIMIT %s',
        [count]
    )
    return ok({'poems': rows})


@poems_bp.get('/<int:poem_id>')
def get_poem(poem_id):
    """Get a single poem by ID."""
    row = query('SELECT * FROM poems WHERE poem_id = %s', [poem_id], one=True)
    if not row:
        return fail('诗词不存在', code=404)
    return ok({'poem': row})


@poems_bp.get('/realtime')
def realtime():
    """Fetch random poems from jinrishici API in real-time."""
    count = min(10, request.args.get('count', 1, type=int))
    poems = []
    for _ in range(count):
        try:
            resp = http_requests.get(
                'https://v1.jinrishici.com/all.json',
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=5
            )
            resp.raise_for_status()
            data = resp.json()
            poems.append({
                'title': data.get('origin', ''),
                'author': data.get('author', ''),
                'content': data.get('content', ''),
                'category': data.get('category', ''),
                'source': '今日诗词',
            })
        except Exception as e:
            logger.warning(f'Failed to fetch poem: {e}')
            continue
    if not poems:
        return fail('获取诗词失败，请稍后再试')
    return ok({'poems': poems})


@poems_bp.post('/save')
@login_required
def save_poem():
    """Save a poem from realtime source into local database."""
    data = request.get_json(force=True) or {}
    title = (data.get('title') or '').strip()
    author = (data.get('author') or '').strip()
    content = (data.get('content') or '').strip()
    category = (data.get('category') or '').strip()

    if not title or not content:
        return fail('诗词标题和内容不能为空')

    # Check if already saved by this user (avoid duplicates)
    existing = query(
        "SELECT poem_id FROM poems WHERE title = %s AND author = %s AND source = '今日诗词'",
        [title, author], one=True
    )
    if existing:
        return ok({'poem_id': existing['poem_id'], 'msg': '该诗词已存在于库中'})

    poem_id = execute(
        'INSERT INTO poems (title, author, content, category, source) VALUES (%s, %s, %s, %s, %s)',
        [title, author, content, category, '今日诗词']
    )
    return ok({'poem_id': poem_id, 'msg': '已收藏到诗词库'})
