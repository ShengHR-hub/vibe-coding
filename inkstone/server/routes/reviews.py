from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, login_required, _fmt

reviews_bp = Blueprint('reviews', __name__)


@reviews_bp.get('/<int:book_id>')
def get_reviews(book_id):
    """获取书评列表"""
    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(50, request.args.get('per_page', 20, type=int))
    offset = (page - 1) * per_page

    # 获取总数
    total = query(
        'SELECT COUNT(*) as cnt FROM library_reviews WHERE book_id = %s',
        (book_id,), one=True
    )['cnt']

    # 获取书评
    rows = query('''
        SELECT r.*, u.username, u.avatar
        FROM library_reviews r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.book_id = %s
        ORDER BY r.created_at DESC
        LIMIT %s OFFSET %s
    ''', (book_id, per_page, offset))

    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))
        r['updated_at'] = _fmt(r.get('updated_at'))

    # 获取评分统计
    stats = query('''
        SELECT
            COUNT(*) as count,
            AVG(rating) as avg_rating,
            SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) as star5,
            SUM(CASE WHEN rating = 4 THEN 1 ELSE 0 END) as star4,
            SUM(CASE WHEN rating = 3 THEN 1 ELSE 0 END) as star3,
            SUM(CASE WHEN rating = 2 THEN 1 ELSE 0 END) as star2,
            SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as star1
        FROM library_reviews WHERE book_id = %s
    ''', (book_id,), one=True)

    return ok({
        'reviews': rows,
        'total': total,
        'page': page,
        'per_page': per_page,
        'stats': {
            'count': stats['count'] or 0,
            'avg_rating': round(float(stats['avg_rating']), 1) if stats['avg_rating'] else 0,
            'star5': stats['star5'] or 0,
            'star4': stats['star4'] or 0,
            'star3': stats['star3'] or 0,
            'star2': stats['star2'] or 0,
            'star1': stats['star1'] or 0,
        }
    })


@reviews_bp.post('')
@login_required
def create_review():
    """创建或更新书评"""
    user_id = session.get('user_id')
    data = request.get_json(force=True)
    book_id = data.get('book_id')
    rating = data.get('rating', 5)
    content = data.get('content', '').strip()

    if not book_id:
        return fail('缺少 book_id')

    if not (1 <= rating <= 5):
        return fail('评分范围 1-5')

    # 检查书籍是否存在
    book = query(
        'SELECT book_id FROM library_books WHERE book_id = %s',
        (book_id,), one=True
    )
    if not book:
        return fail('书籍不存在')

    # UPSERT
    existing = query(
        'SELECT review_id FROM library_reviews WHERE book_id = %s AND user_id = %s',
        (book_id, user_id), one=True
    )
    if existing:
        execute(
            'UPDATE library_reviews SET rating = %s, content = %s WHERE review_id = %s',
            (rating, content, existing['review_id'])
        )
    else:
        execute(
            'INSERT INTO library_reviews (book_id, user_id, rating, content) VALUES (%s, %s, %s, %s)',
            (book_id, user_id, rating, content)
        )

    # 更新书籍平均评分
    update_book_rating(book_id)

    return ok()


@reviews_bp.get('/user/<int:book_id>')
@login_required
def get_user_review(book_id):
    """获取当前用户对某本书的书评"""
    user_id = session.get('user_id')
    row = query(
        'SELECT * FROM library_reviews WHERE book_id = %s AND user_id = %s',
        (book_id, user_id), one=True
    )
    if row:
        row['created_at'] = _fmt(row.get('created_at'))
        row['updated_at'] = _fmt(row.get('updated_at'))
    return ok({'review': row})


@reviews_bp.delete('/<int:review_id>')
@login_required
def delete_review(review_id):
    """删除书评"""
    user_id = session.get('user_id')
    review = query(
        'SELECT book_id FROM library_reviews WHERE review_id = %s AND user_id = %s',
        (review_id, user_id), one=True
    )
    if not review:
        return fail('书评不存在或无权限删除')

    execute('DELETE FROM library_reviews WHERE review_id = %s', (review_id,))
    update_book_rating(review['book_id'])
    return ok()


def update_book_rating(book_id):
    """更新书籍平均评分"""
    stats = query(
        'SELECT COUNT(*) as cnt, AVG(rating) as avg_r FROM library_reviews WHERE book_id = %s',
        (book_id,), one=True
    )
    execute(
        'UPDATE library_books SET rating_avg = %s, rating_count = %s WHERE book_id = %s',
        (round(float(stats['avg_r']), 2) if stats['avg_r'] else 0, stats['cnt'], book_id)
    )
