from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, login_required

materials_bp = Blueprint('materials', __name__)


@materials_bp.get('/')
def list_materials():
    """List materials with optional category filter and pagination."""
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(50, request.args.get('page_size', 20, type=int))
    category = request.args.get('category', '').strip()

    base = 'FROM materials'
    params = []
    if category:
        base += ' WHERE category = %s'
        params.append(category)

    total = query(f'SELECT COUNT(*) as cnt {base}', params, one=True)['cnt']
    rows = query(
        f'SELECT * {base} ORDER BY material_id LIMIT %s OFFSET %s',
        params + [page_size, (page - 1) * page_size]
    )
    return ok({'materials': rows, 'total': total, 'page': page, 'page_size': page_size})


@materials_bp.get('/categories')
def categories():
    """Get all categories with material counts."""
    rows = query('SELECT category, COUNT(*) as count FROM materials GROUP BY category ORDER BY count DESC')
    return ok({'categories': rows})


@materials_bp.get('/search')
def search():
    """Search materials by keyword in title, content, or tags."""
    q = request.args.get('q', '').strip()
    if not q:
        return fail('请输入搜索关键词')
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(50, request.args.get('page_size', 20, type=int))
    like = f'%{q}%'
    base = 'FROM materials WHERE title LIKE %s OR content LIKE %s OR tags LIKE %s'
    params = [like, like, like]

    total = query(f'SELECT COUNT(*) as cnt {base}', params, one=True)['cnt']
    rows = query(
        f'SELECT * {base} ORDER BY material_id LIMIT %s OFFSET %s',
        params + [page_size, (page - 1) * page_size]
    )
    return ok({'materials': rows, 'total': total, 'page': page, 'page_size': page_size, 'keyword': q})


@materials_bp.get('/random')
def random_material():
    """Get random materials, optionally filtered by category."""
    category = request.args.get('category', '').strip()
    count = min(10, request.args.get('count', 1, type=int))

    if category:
        rows = query('SELECT * FROM materials WHERE category = %s ORDER BY RAND() LIMIT %s', [category, count])
    else:
        rows = query('SELECT * FROM materials ORDER BY RAND() LIMIT %s', [count])
    return ok({'materials': rows})


@materials_bp.post('')
@login_required
def create_material():
    """F3：手动收录短句素材（灵感馆"收录句子"）。"""
    data = request.get_json() or {}
    category = (data.get('category') or '').strip() or '随想'
    content = (data.get('content') or '').strip()
    if len(category) > 20:
        return fail('分类过长，最多20字')
    if not content:
        return fail('请输入内容')
    if len(content) > 2000:
        return fail('内容过长，最多2000字')
    title = (data.get('title') or '').strip() or content[:20]
    tags = (data.get('tags') or '').strip()[:200]
    material_id = execute(
        'INSERT INTO materials (title, content, category, tags, source) VALUES (%s, %s, %s, %s, %s)',
        (title, content, category, tags, 'user'),
    )
    return ok({'material_id': material_id}, msg='已收录到素材库')
