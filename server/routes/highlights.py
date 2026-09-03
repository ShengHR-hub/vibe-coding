from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, _fmt, login_required

highlights_bp = Blueprint('highlights', __name__)


@highlights_bp.get('')
@login_required
def list_highlights():
    """好句列表"""
    user_id = session.get('user_id')
    book_type = request.args.get('book_type', '')
    book_id = request.args.get('book_id', '', type=str)
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(50, request.args.get('page_size', 20, type=int))

    where = ['h.user_id = %s']
    params = [user_id]
    if book_type:
        where.append('h.book_type = %s')
        params.append(book_type)
    if book_id:
        where.append('h.book_id = %s')
        params.append(book_id)

    cond = ' AND '.join(where)
    total = query(f'SELECT COUNT(*) as cnt FROM reading_highlights h WHERE {cond}', params, one=True)['cnt']

    rows = query(f'''
        SELECT h.*,
               CASE h.book_type
                 WHEN 'library' THEN (SELECT title FROM library_books WHERE book_id = h.book_id)
                 WHEN 'work' THEN (SELECT title FROM works WHERE work_id = h.book_id)
               END as book_title
        FROM reading_highlights h
        WHERE {cond}
        ORDER BY h.created_at DESC
        LIMIT %s OFFSET %s
    ''', params + [page_size, (page - 1) * page_size])

    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))

    return ok({'items': rows, 'total': total, 'page': page, 'page_size': page_size})


@highlights_bp.post('')
@login_required
def add_highlight():
    """标记好句"""
    user_id = session.get('user_id')
    data = request.get_json(force=True)
    book_type = data.get('book_type', 'work')
    book_id = data.get('book_id')
    chapter_id = data.get('chapter_id')
    chapter_no = data.get('chapter_no', 0)
    selected_text = (data.get('selected_text') or '').strip()

    if not book_id:
        return fail('缺少 book_id')
    if not selected_text:
        return fail('请选择文字')
    if len(selected_text) > 1000:
        return fail('选中文字过长（最多1000字）')

    highlight_id = execute(
        'INSERT INTO reading_highlights (user_id, book_type, book_id, chapter_id, chapter_no, selected_text) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (user_id, book_type, book_id, chapter_id, chapter_no, selected_text)
    )
    return ok({'highlight_id': highlight_id})


@highlights_bp.delete('/<int:highlight_id>')
@login_required
def delete_highlight(highlight_id):
    """删除好句标记"""
    user_id = session.get('user_id')
    item = query(
        'SELECT highlight_id FROM reading_highlights WHERE highlight_id = %s AND user_id = %s',
        (highlight_id, user_id), one=True
    )
    if not item:
        return fail('好句不存在', code=404)
    execute('DELETE FROM reading_highlights WHERE highlight_id = %s', (highlight_id,))
    return ok()


@highlights_bp.post('/<int:highlight_id>/sync')
@login_required
def sync_to_material(highlight_id):
    """同步到素材库"""
    user_id = session.get('user_id')
    hl = query(
        "SELECT h.*, "
        "CASE h.book_type "
        "  WHEN 'library' THEN (SELECT title FROM library_books WHERE book_id = h.book_id) "
        "  WHEN 'work' THEN (SELECT title FROM works WHERE work_id = h.book_id) "
        "END as book_title "
        "FROM reading_highlights h WHERE h.highlight_id = %s AND h.user_id = %s",
        (highlight_id, user_id), one=True
    )
    if not hl:
        return fail('好句不存在', code=404)
    if hl['synced_to_material']:
        return fail('已同步过')

    # 构造素材来源
    source = hl.get('book_title', '未知书籍')
    if hl.get('chapter_no'):
        source += f' 第{hl["chapter_no"]}章'

    execute(
        'INSERT INTO materials (title, content, category, source) VALUES (%s, %s, %s, %s)',
        (f'好句摘录 - {source[:50]}', hl['selected_text'], 'inspiration', source)
    )

    execute('UPDATE reading_highlights SET synced_to_material = 1 WHERE highlight_id = %s', (highlight_id,))

    return ok({'synced': True})
