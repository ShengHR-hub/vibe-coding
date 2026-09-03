from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, _fmt, login_required

bookmarks_bp = Blueprint('bookmarks', __name__)


@bookmarks_bp.get('')
@login_required
def list_bookmarks():
    """书签列表"""
    user_id = session.get('user_id')
    book_type = request.args.get('book_type', '')
    book_id = request.args.get('book_id', '', type=str)

    where = ['b.user_id = %s']
    params = [user_id]
    if book_type:
        where.append('b.book_type = %s')
        params.append(book_type)
    if book_id:
        where.append('b.book_id = %s')
        params.append(book_id)

    cond = ' AND '.join(where)
    rows = query(f'''
        SELECT b.*,
               CASE b.book_type
                 WHEN 'library' THEN (SELECT title FROM library_books WHERE book_id = b.book_id)
                 WHEN 'work' THEN (SELECT title FROM works WHERE work_id = b.book_id)
               END as book_title
        FROM reading_bookmarks b
        WHERE {cond}
        ORDER BY b.created_at DESC
    ''', params)

    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))

    return ok({'items': rows, 'total': len(rows)})


@bookmarks_bp.post('')
@login_required
def add_bookmark():
    """添加书签"""
    user_id = session.get('user_id')
    data = request.get_json(force=True)
    book_type = data.get('book_type', 'work')
    book_id = data.get('book_id')
    chapter_id = data.get('chapter_id')
    chapter_no = data.get('chapter_no', 0)
    paragraph_index = data.get('paragraph_index', 0)
    selected_text = (data.get('selected_text') or '')[:500]
    note = (data.get('note') or '')[:500]

    if not book_id:
        return fail('缺少 book_id')

    bookmark_id = execute(
        'INSERT INTO reading_bookmarks (user_id, book_type, book_id, chapter_id, chapter_no, paragraph_index, selected_text, note) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
        (user_id, book_type, book_id, chapter_id, chapter_no, paragraph_index, selected_text, note)
    )
    return ok({'bookmark_id': bookmark_id})


@bookmarks_bp.delete('/<int:bookmark_id>')
@login_required
def delete_bookmark(bookmark_id):
    """删除书签"""
    user_id = session.get('user_id')
    item = query(
        'SELECT bookmark_id FROM reading_bookmarks WHERE bookmark_id = %s AND user_id = %s',
        (bookmark_id, user_id), one=True
    )
    if not item:
        return fail('书签不存在', code=404)
    execute('DELETE FROM reading_bookmarks WHERE bookmark_id = %s', (bookmark_id,))
    return ok()
