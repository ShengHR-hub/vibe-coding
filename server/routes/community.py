from flask import Blueprint, request
from database.db import query
from utils.helpers import ok, fail, _fmt

community_bp = Blueprint('community', __name__)


@community_bp.get('/feed')
def feed():
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(30, request.args.get('page_size', 12, type=int))
    sort = request.args.get('sort', 'hot')

    base = '''
        FROM works w
        JOIN users u ON w.user_id = u.user_id
        WHERE w.status = 'published'
    '''
    order = 'ORDER BY w.updated_at DESC'
    if sort == 'hot':
        order = 'ORDER BY (w.likes_count * 2 + w.comments_count * 3 + w.favorites_count * 5) DESC, w.updated_at DESC'
    elif sort == 'new':
        order = 'ORDER BY w.created_at DESC'

    total = query(f'SELECT COUNT(*) as cnt {base}', one=True)['cnt']

    rows = query(f'''
        SELECT w.*, u.username, u.avatar, u.level
        {base}
        {order}
        LIMIT %s OFFSET %s
    ''', (page_size, (page - 1) * page_size))

    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))
        r['updated_at'] = _fmt(r.get('updated_at'))

    return ok({'items': rows, 'total': total, 'page': page, 'page_size': page_size})


@community_bp.get('/search')
def search():
    q = (request.args.get('q') or '').strip()
    wtype = request.args.get('type', '')
    tag = request.args.get('tag', '')
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(30, request.args.get('page_size', 12, type=int))

    if not q and not tag:
        return fail('请输入搜索关键词或标签')

    conditions = ["w.status = 'published'"]
    params = []

    if q:
        conditions.append('(w.title LIKE %s OR w.summary LIKE %s)')
        like_q = f'%{q}%'
        params.extend([like_q, like_q])
    if wtype:
        conditions.append('w.type = %s')
        params.append(wtype)
    if tag:
        conditions.append('w.tags LIKE %s')
        params.append(f'%{tag}%')

    where = ' AND '.join(conditions)

    total = query(f'''
        SELECT COUNT(*) as cnt FROM works w WHERE {where}
    ''', params, one=True)['cnt']

    rows = query(f'''
        SELECT w.*, u.username, u.avatar, u.level
        FROM works w JOIN users u ON w.user_id = u.user_id
        WHERE {where}
        ORDER BY w.updated_at DESC
        LIMIT %s OFFSET %s
    ''', params + [page_size, (page - 1) * page_size])

    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))
        r['updated_at'] = _fmt(r.get('updated_at'))

    return ok({'items': rows, 'total': total, 'page': page, 'page_size': page_size})


@community_bp.get('/category/<wtype>')
def category(wtype):
    if wtype not in ('novel', 'poetry', 'essay', 'script'):
        return fail('无效的作品类型')

    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(30, request.args.get('page_size', 12, type=int))

    total = query(
        "SELECT COUNT(*) as cnt FROM works WHERE status = 'published' AND type = %s",
        (wtype,), one=True
    )['cnt']

    rows = query('''
        SELECT w.*, u.username, u.avatar, u.level
        FROM works w JOIN users u ON w.user_id = u.user_id
        WHERE w.status = 'published' AND w.type = %s
        ORDER BY w.updated_at DESC
        LIMIT %s OFFSET %s
    ''', (wtype, page_size, (page - 1) * page_size))

    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))
        r['updated_at'] = _fmt(r.get('updated_at'))

    return ok({'items': rows, 'total': total, 'page': page, 'page_size': page_size})
