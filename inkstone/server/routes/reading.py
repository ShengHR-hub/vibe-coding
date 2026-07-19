from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, _fmt, login_required

reading_bp = Blueprint('reading', __name__)


@reading_bp.get('/progress/<book_type>/<int:book_id>')
@login_required
def get_progress(book_type, book_id):
    """获取阅读进度"""
    user_id = session.get('user_id')
    if book_type not in ('work', 'library'):
        return fail('无效的 book_type')

    row = query(
        'SELECT * FROM reading_progress WHERE user_id = %s AND book_type = %s AND book_id = %s',
        (user_id, book_type, book_id), one=True
    )
    if not row:
        return ok({'progress': None})

    row['updated_at'] = _fmt(row.get('updated_at'))
    return ok({'progress': row})


@reading_bp.put('/progress/<book_type>/<int:book_id>')
@login_required
def update_progress(book_type, book_id):
    """更新阅读进度（UPSERT）"""
    user_id = session.get('user_id')
    if book_type not in ('work', 'library'):
        return fail('无效的 book_type')

    data = request.get_json(force=True)
    chapter_id = data.get('chapter_id')
    chapter_no = data.get('chapter_no', 0)
    scroll_percent = data.get('scroll_percent', 0)

    # 计算总进度百分比
    if book_type == 'library':
        total_chapters = query(
            'SELECT COUNT(*) as cnt FROM library_chapters WHERE book_id = %s',
            (book_id,), one=True
        )['cnt']
    else:
        total_chapters = query(
            'SELECT COUNT(*) as cnt FROM chapters WHERE work_id = %s',
            (book_id,), one=True
        )['cnt']

    total_percent = round((chapter_no / max(total_chapters, 1)) * 100, 2) if total_chapters else 0

    # UPSERT
    existing = query(
        'SELECT progress_id FROM reading_progress WHERE user_id = %s AND book_type = %s AND book_id = %s',
        (user_id, book_type, book_id), one=True
    )
    if existing:
        execute(
            'UPDATE reading_progress SET chapter_id = %s, chapter_no = %s, scroll_percent = %s, total_percent = %s '
            'WHERE user_id = %s AND book_type = %s AND book_id = %s',
            (chapter_id, chapter_no, scroll_percent, total_percent, user_id, book_type, book_id)
        )
    else:
        execute(
            'INSERT INTO reading_progress (user_id, book_type, book_id, chapter_id, chapter_no, scroll_percent, total_percent) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (user_id, book_type, book_id, chapter_id, chapter_no, scroll_percent, total_percent)
        )

    # 同步更新书架 last_read_at 和分组（进度100%自动流转到已读）
    if total_percent >= 100:
        execute(
            "UPDATE reading_bookshelf SET last_read_at = NOW(), shelf_group = 'completed' "
            'WHERE user_id = %s AND book_type = %s AND book_id = %s',
            (user_id, book_type, book_id)
        )
    else:
        execute(
            "UPDATE reading_bookshelf SET last_read_at = NOW(), shelf_group = CASE WHEN shelf_group = 'want_read' THEN 'reading' ELSE shelf_group END "
            'WHERE user_id = %s AND book_type = %s AND book_id = %s',
            (user_id, book_type, book_id)
        )

    return ok({'total_percent': total_percent})


@reading_bp.get('/history')
@login_required
def reading_history():
    """阅读历史（最近阅读的书籍）"""
    user_id = session.get('user_id')
    limit = min(50, request.args.get('limit', 20, type=int))

    rows = query('''
        SELECT rp.book_type, rp.book_id, rp.chapter_no, rp.total_percent, rp.updated_at,
               CASE rp.book_type
                 WHEN 'library' THEN (SELECT title FROM library_books WHERE book_id = rp.book_id)
                 WHEN 'work' THEN (SELECT title FROM works WHERE work_id = rp.book_id)
               END as title,
               CASE rp.book_type
                 WHEN 'library' THEN (SELECT author FROM library_books WHERE book_id = rp.book_id)
                 WHEN 'work' THEN (SELECT u.username FROM works w JOIN users u ON w.user_id = u.user_id WHERE w.work_id = rp.book_id)
               END as author
        FROM reading_progress rp
        WHERE rp.user_id = %s
        ORDER BY rp.updated_at DESC
        LIMIT %s
    ''', (user_id, limit))

    for r in rows:
        r['updated_at'] = _fmt(r.get('updated_at'))

    return ok({'items': rows})
