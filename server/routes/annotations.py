from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, _fmt, login_required

annotations_bp = Blueprint('annotations', __name__)


@annotations_bp.get('/<book_type>/<int:book_id>/<int:chapter_id>')
def list_chapter_annotations(book_type, book_id, chapter_id):
    """获取章节批注（公开的 + 自己的）"""
    user_id = session.get('user_id')

    if book_type not in ('work', 'library'):
        return fail('无效的 book_type')

    rows = query('''
        SELECT a.*, u.username, u.avatar
        FROM reading_annotations a
        JOIN users u ON a.user_id = u.user_id
        WHERE a.book_type = %s AND a.book_id = %s AND a.chapter_id = %s AND a.parent_id IS NULL
          AND (a.is_public = 1 OR a.user_id = %s)
        ORDER BY a.paragraph_index ASC, a.created_at ASC
    ''', (book_type, book_id, chapter_id, user_id or 0))

    # 加载回复
    ann_map = {}
    roots = []
    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))
        r['updated_at'] = _fmt(r.get('updated_at'))
        r['replies'] = []
        ann_map[r['annotation_id']] = r
        roots.append(r)

    # 获取这些批注的回复
    if ann_map:
        ann_ids = list(ann_map.keys())
        placeholders = ','.join(['%s'] * len(ann_ids))
        replies = query(f'''
            SELECT a.*, u.username, u.avatar
            FROM reading_annotations a
            JOIN users u ON a.user_id = u.user_id
            WHERE a.parent_id IN ({placeholders})
            ORDER BY a.created_at ASC
        ''', ann_ids)
        for r in replies:
            r['created_at'] = _fmt(r.get('created_at'))
            r['updated_at'] = _fmt(r.get('updated_at'))
            if r['parent_id'] in ann_map:
                ann_map[r['parent_id']]['replies'].append(r)

    return ok({'annotations': roots, 'total': len(rows)})


@annotations_bp.post('')
@login_required
def create_annotation():
    """创建批注"""
    user_id = session.get('user_id')
    data = request.get_json(force=True)
    book_type = data.get('book_type', 'work')
    book_id = data.get('book_id')
    chapter_id = data.get('chapter_id')
    chapter_no = data.get('chapter_no', 0)
    paragraph_index = data.get('paragraph_index', 0)
    selected_text = (data.get('selected_text') or '')[:1000]
    content = (data.get('content') or '').strip()
    is_public = 1 if data.get('is_public', True) else 0
    parent_id = data.get('parent_id')

    if not book_id:
        return fail('缺少 book_id')
    if not content:
        return fail('请输入批注内容')

    annotation_id = execute(
        'INSERT INTO reading_annotations (user_id, book_type, book_id, chapter_id, chapter_no, paragraph_index, selected_text, content, is_public, parent_id) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (user_id, book_type, book_id, chapter_id, chapter_no, paragraph_index, selected_text, content, is_public, parent_id)
    )
    return ok({'annotation_id': annotation_id})


@annotations_bp.put('/<int:annotation_id>')
@login_required
def update_annotation(annotation_id):
    """编辑批注"""
    user_id = session.get('user_id')
    data = request.get_json(force=True)

    item = query(
        'SELECT annotation_id FROM reading_annotations WHERE annotation_id = %s AND user_id = %s',
        (annotation_id, user_id), one=True
    )
    if not item:
        return fail('批注不存在', code=404)

    updates = []
    params = []
    if 'content' in data:
        updates.append('content = %s')
        params.append(data['content'].strip())
    if 'is_public' in data:
        updates.append('is_public = %s')
        params.append(1 if data['is_public'] else 0)

    if not updates:
        return fail('没有要更新的字段')

    params.append(annotation_id)
    execute(f'UPDATE reading_annotations SET {", ".join(updates)} WHERE annotation_id = %s', params)
    return ok()


@annotations_bp.delete('/<int:annotation_id>')
@login_required
def delete_annotation(annotation_id):
    """删除批注"""
    user_id = session.get('user_id')
    item = query(
        'SELECT annotation_id FROM reading_annotations WHERE annotation_id = %s AND user_id = %s',
        (annotation_id, user_id), one=True
    )
    if not item:
        return fail('批注不存在', code=404)
    execute('DELETE FROM reading_annotations WHERE annotation_id = %s', (annotation_id,))
    return ok()


@annotations_bp.get('/mine')
@login_required
def my_annotations():
    """我的所有批注"""
    user_id = session.get('user_id')
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(50, request.args.get('page_size', 20, type=int))
    visibility = request.args.get('visibility', '')

    where = ['a.user_id = %s', 'a.parent_id IS NULL']
    params = [user_id]
    if visibility == 'public':
        where.append('a.is_public = 1')
    elif visibility == 'private':
        where.append('a.is_public = 0')

    cond = ' AND '.join(where)
    total = query(f'SELECT COUNT(*) as cnt FROM reading_annotations a WHERE {cond}', params, one=True)['cnt']

    rows = query(f'''
        SELECT a.*,
               CASE a.book_type
                 WHEN 'library' THEN (SELECT title FROM library_books WHERE book_id = a.book_id)
                 WHEN 'work' THEN (SELECT title FROM works WHERE work_id = a.book_id)
               END as book_title
        FROM reading_annotations a
        WHERE {cond}
        ORDER BY a.created_at DESC
        LIMIT %s OFFSET %s
    ''', params + [page_size, (page - 1) * page_size])

    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))
        r['updated_at'] = _fmt(r.get('updated_at'))

    return ok({'items': rows, 'total': total, 'page': page, 'page_size': page_size})
