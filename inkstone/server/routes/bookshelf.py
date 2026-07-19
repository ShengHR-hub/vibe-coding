from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, _fmt, login_required

bookshelf_bp = Blueprint('bookshelf', __name__)


@bookshelf_bp.get('')
@login_required
def list_shelf():
    """书架列表"""
    user_id = session.get('user_id')
    group = request.args.get('group', '')
    folder = request.args.get('folder', '')
    sort = request.args.get('sort', 'recent')

    where = ['s.user_id = %s']
    params = [user_id]
    if group:
        where.append('s.shelf_group = %s')
        params.append(group)
    if folder:
        where.append('s.folder_name = %s')
        params.append(folder)

    # 排序映射
    sort_map = {
        'recent': 's.last_read_at DESC, s.created_at DESC',
        'progress': 'rp.total_percent DESC, s.created_at DESC',
        'rating': 's.rating DESC, s.created_at DESC',
        'added': 's.created_at DESC',
        'title': 'COALESCE(lb.title, w.title) ASC',
    }
    order = sort_map.get(sort, sort_map['recent'])

    cond = ' AND '.join(where)
    rows = query(f'''
        SELECT s.shelf_id, s.book_type, s.book_id, s.shelf_group, s.folder_name,
               s.rating, s.last_read_at, s.created_at,
               COALESCE(rp.total_percent, 0) as total_percent,
               COALESCE(lb.title, w.title) as title,
               COALESCE(lb.author, u.username) as author,
               COALESCE(lb.cover_image, w.cover_image) as cover_image,
               COALESCE(lb.type, w.type) as type
        FROM reading_bookshelf s
        LEFT JOIN reading_progress rp ON rp.user_id = s.user_id AND rp.book_type = s.book_type AND rp.book_id = s.book_id
        LEFT JOIN library_books lb ON s.book_type = 'library' AND lb.book_id = s.book_id
        LEFT JOIN works w ON s.book_type = 'work' AND w.work_id = s.book_id
        LEFT JOIN users u ON s.book_type = 'work' AND w.user_id = u.user_id
        WHERE {cond}
        ORDER BY {order}
    ''', params)

    for r in rows:
        r['last_read_at'] = _fmt(r.get('last_read_at'))
        r['created_at'] = _fmt(r.get('created_at'))

    return ok({'items': rows, 'total': len(rows)})


@bookshelf_bp.post('')
@login_required
def add_to_shelf():
    """加入书架"""
    user_id = session.get('user_id')
    data = request.get_json(force=True)
    book_type = data.get('book_type', 'library')
    book_id = data.get('book_id')
    group = data.get('shelf_group', 'want_read')

    if not book_id:
        return fail('缺少 book_id')

    # 验证书籍存在
    if book_type == 'library':
        book = query('SELECT book_id FROM library_books WHERE book_id = %s', (book_id,), one=True)
    else:
        book = query("SELECT work_id FROM works WHERE work_id = %s AND status = 'published'", (book_id,), one=True)
    if not book:
        return fail('书籍不存在', code=404)

    # 检查是否已在书架
    existing = query(
        'SELECT shelf_id FROM reading_bookshelf WHERE user_id = %s AND book_type = %s AND book_id = %s',
        (user_id, book_type, book_id), one=True
    )
    if existing:
        return fail('已在书架中')

    shelf_id = execute(
        'INSERT INTO reading_bookshelf (user_id, book_type, book_id, shelf_group) VALUES (%s, %s, %s, %s)',
        (user_id, book_type, book_id, group)
    )
    return ok({'shelf_id': shelf_id})


@bookshelf_bp.put('/<int:shelf_id>')
@login_required
def update_shelf(shelf_id):
    """更新书架条目（分组/评分/书单）"""
    user_id = session.get('user_id')
    data = request.get_json(force=True)

    # 验证归属
    item = query(
        'SELECT shelf_id FROM reading_bookshelf WHERE shelf_id = %s AND user_id = %s',
        (shelf_id, user_id), one=True
    )
    if not item:
        return fail('书架条目不存在', code=404)

    updates = []
    params = []
    for field in ('shelf_group', 'folder_name', 'rating'):
        if field in data:
            updates.append(f'{field} = %s')
            params.append(data[field])

    if not updates:
        return fail('没有要更新的字段')

    params.append(shelf_id)
    execute(f'UPDATE reading_bookshelf SET {", ".join(updates)} WHERE shelf_id = %s', params)
    return ok()


@bookshelf_bp.delete('/<int:shelf_id>')
@login_required
def remove_shelf(shelf_id):
    """从书架移除"""
    user_id = session.get('user_id')
    item = query(
        'SELECT shelf_id FROM reading_bookshelf WHERE shelf_id = %s AND user_id = %s',
        (shelf_id, user_id), one=True
    )
    if not item:
        return fail('书架条目不存在', code=404)
    execute('DELETE FROM reading_bookshelf WHERE shelf_id = %s', (shelf_id,))
    return ok()


@bookshelf_bp.get('/folders')
@login_required
def list_folders():
    """自定义书单列表"""
    user_id = session.get('user_id')
    rows = query(
        "SELECT DISTINCT folder_name FROM reading_bookshelf WHERE user_id = %s AND folder_name != '' ORDER BY folder_name",
        (user_id,)
    )
    return ok({'folders': [r['folder_name'] for r in rows]})


@bookshelf_bp.post('/folders')
@login_required
def create_folder():
    """创建书单（仅记录名称，后续加书时使用）"""
    data = request.get_json(force=True)
    name = (data.get('name') or '').strip()
    if not name:
        return fail('请输入书单名称')
    if len(name) > 50:
        return fail('书单名称过长')
    # 无需实际创建表，书单通过 folder_name 字段隐式管理
    return ok({'name': name})


@bookshelf_bp.post('/batch')
@login_required
def batch_update():
    """批量更新书架条目（移动分组、评分）"""
    user_id = session.get('user_id')
    data = request.get_json(force=True)
    shelf_ids = data.get('shelf_ids', [])
    updates = data.get('updates', {})

    if not shelf_ids:
        return fail('请选择要操作的书籍')
    if not updates:
        return fail('没有要更新的内容')

    # 构建更新语句
    set_clauses = []
    params = []
    for field in ('shelf_group', 'folder_name', 'rating'):
        if field in updates:
            set_clauses.append(f'{field} = %s')
            params.append(updates[field])

    if not set_clauses:
        return fail('没有有效的更新字段')

    # 批量更新
    placeholders = ','.join(['%s'] * len(shelf_ids))
    params.extend(shelf_ids)
    execute(
        f'UPDATE reading_bookshelf SET {", ".join(set_clauses)} WHERE shelf_id IN ({placeholders}) AND user_id = %s',
        params + [user_id]
    )
    return ok(msg=f'已更新 {len(shelf_ids)} 本书')


@bookshelf_bp.post('/batch-delete')
@login_required
def batch_delete():
    """批量删除书架条目"""
    user_id = session.get('user_id')
    data = request.get_json(force=True)
    shelf_ids = data.get('shelf_ids', [])

    if not shelf_ids:
        return fail('请选择要删除的书籍')

    placeholders = ','.join(['%s'] * len(shelf_ids))
    execute(
        f'DELETE FROM reading_bookshelf WHERE shelf_id IN ({placeholders}) AND user_id = %s',
        shelf_ids + [user_id]
    )
    return ok(msg=f'已删除 {len(shelf_ids)} 本书')
