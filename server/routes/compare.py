from flask import Blueprint, request
from database.db import query
from utils.helpers import ok, fail

compare_bp = Blueprint('compare', __name__)


@compare_bp.get('')
def compare_books():
    """对比多本书籍"""
    ids = request.args.get('ids', '')
    book_type = request.args.get('type', 'library')

    if not ids:
        return fail('请选择要对比的书籍')

    id_list = [int(x) for x in ids.split(',') if x.strip().isdigit()]
    if len(id_list) < 2:
        return fail('至少选择2本书籍')
    if len(id_list) > 5:
        return fail('最多对比5本书籍')

    books = []
    for book_id in id_list:
        if book_type == 'library':
            book = query('''
                SELECT book_id, title, author, type, word_count, chapter_count,
                       rating_avg, rating_count, views, favorites_count, created_at
                FROM library_books WHERE book_id = %s
            ''', (book_id,), one=True)
        else:
            book = query('''
                SELECT work_id as book_id, title, u.username as author, type, word_count,
                       0 as chapter_count, 0 as rating_avg, 0 as rating_count,
                       views, favorites_count, created_at
                FROM works w JOIN users u ON w.user_id = u.user_id
                WHERE work_id = %s AND status = 'published'
            ''', (book_id,), one=True)

        if book:
            # 获取章节数
            if book_type == 'library':
                ch_count = query(
                    'SELECT COUNT(*) as cnt FROM library_chapters WHERE book_id = %s',
                    (book_id,), one=True
                )['cnt']
            else:
                ch_count = query(
                    'SELECT COUNT(*) as cnt FROM chapters WHERE work_id = %s',
                    (book_id,), one=True
                )['cnt']
            book['chapter_count'] = ch_count

            # 格式化日期
            if book.get('created_at'):
                book['created_at'] = str(book['created_at'])

            books.append(book)

    if len(books) < 2:
        return fail('部分书籍不存在')

    return ok({'books': books})
