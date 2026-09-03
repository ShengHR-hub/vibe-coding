from flask import Blueprint, request, session
from database.db import query
from utils.helpers import ok, login_required

report_bp = Blueprint('report', __name__)


@report_bp.get('/weekly')
@login_required
def weekly_report():
    """本周阅读数据"""
    user_id = session.get('user_id')

    rows = query('''
        SELECT checkin_date, read_minutes, pages_read, books_read
        FROM reading_checkins
        WHERE user_id = %s AND checkin_date >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)
        ORDER BY checkin_date
    ''', (user_id,))

    total_minutes = sum(r['read_minutes'] for r in rows)
    total_pages = sum(r['pages_read'] for r in rows)
    total_books = sum(r['books_read'] for r in rows)

    daily = []
    for r in rows:
        daily.append({
            'date': str(r['checkin_date']),
            'minutes': r['read_minutes'],
            'pages': r['pages_read'],
        })

    return ok({
        'total_minutes': total_minutes,
        'total_pages': total_pages,
        'total_books': total_books,
        'daily_breakdown': daily,
        'active_days': len(rows),
    })


@report_bp.get('/monthly')
@login_required
def monthly_report():
    """本月阅读数据"""
    user_id = session.get('user_id')

    rows = query('''
        SELECT checkin_date, read_minutes, pages_read, books_read
        FROM reading_checkins
        WHERE user_id = %s AND MONTH(checkin_date) = MONTH(CURDATE()) AND YEAR(checkin_date) = YEAR(CURDATE())
        ORDER BY checkin_date
    ''', (user_id,))

    total_minutes = sum(r['read_minutes'] for r in rows)
    total_pages = sum(r['pages_read'] for r in rows)

    return ok({
        'total_minutes': total_minutes,
        'total_pages': total_pages,
        'active_days': len(rows),
        'daily_breakdown': [{'date': str(r['checkin_date']), 'minutes': r['read_minutes']} for r in rows],
    })


@report_bp.get('/trend')
@login_required
def reading_trend():
    """阅读趋势（近 N 天）"""
    user_id = session.get('user_id')
    days = min(365, request.args.get('days', 30, type=int))

    rows = query('''
        SELECT checkin_date, read_minutes
        FROM reading_checkins
        WHERE user_id = %s AND checkin_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        ORDER BY checkin_date
    ''', (user_id, days))

    return ok({'trend': [{'date': str(r['checkin_date']), 'minutes': r['read_minutes']} for r in rows]})


@report_bp.get('/annual')
@login_required
def annual_report():
    """年度阅读报告"""
    user_id = session.get('user_id')
    year = request.args.get('year', '', type=str)

    if not year:
        from datetime import date
        year = str(date.today().year)

    # 打卡数据
    checkins = query('''
        SELECT MONTH(checkin_date) as month, SUM(read_minutes) as total_minutes,
               SUM(pages_read) as total_pages, COUNT(*) as active_days
        FROM reading_checkins
        WHERE user_id = %s AND YEAR(checkin_date) = %s
        GROUP BY MONTH(checkin_date)
        ORDER BY month
    ''', (user_id, year))

    total_minutes = sum(r['total_minutes'] for r in checkins)
    total_pages = sum(r['total_pages'] for r in checkins)
    total_active_days = sum(r['active_days'] for r in checkins)

    # 读过的书
    books_read = query('''
        SELECT COUNT(DISTINCT book_id) as cnt FROM reading_progress WHERE user_id = %s
    ''', (user_id,), one=True)['cnt']

    # 读过最长的书
    longest = query('''
        SELECT CASE rp.book_type
          WHEN 'library' THEN (SELECT title FROM library_books WHERE book_id = rp.book_id)
          WHEN 'work' THEN (SELECT title FROM works WHERE work_id = rp.book_id)
        END as title,
        CASE rp.book_type
          WHEN 'library' THEN (SELECT word_count FROM library_books WHERE book_id = rp.book_id)
          WHEN 'work' THEN (SELECT word_count FROM works WHERE work_id = rp.book_id)
        END as word_count
        FROM reading_progress rp
        WHERE rp.user_id = %s
        ORDER BY CASE rp.book_type
          WHEN 'library' THEN (SELECT word_count FROM library_books WHERE book_id = rp.book_id)
          WHEN 'work' THEN (SELECT word_count FROM works WHERE work_id = rp.book_id)
        END DESC LIMIT 1
    ''', (user_id,), one=True)

    # 类型分布（用子查询绕过 only_full_group_by）
    type_dist = query('''
        SELECT book_type, COUNT(*) as cnt FROM (
            SELECT CASE rp.book_type
              WHEN 'library' THEN (SELECT type FROM library_books WHERE book_id = rp.book_id)
              WHEN 'work' THEN (SELECT type FROM works WHERE work_id = rp.book_id)
            END as book_type
            FROM reading_progress rp
            WHERE rp.user_id = %s
        ) t GROUP BY book_type
    ''', (user_id,))

    monthly_data = [{'month': r['month'], 'minutes': r['total_minutes'], 'pages': r['total_pages'], 'days': r['active_days']} for r in checkins]

    return ok({
        'year': year,
        'total_minutes': total_minutes,
        'total_pages': total_pages,
        'total_active_days': total_active_days,
        'books_read': books_read,
        'longest_book': longest,
        'type_distribution': type_dist,
        'monthly_data': monthly_data,
    })


@report_bp.get('/stats')
@login_required
def reading_stats():
    """阅读统计增强：时段分布、阅读速度、最长连续记录"""
    user_id = session.get('user_id')

    # 最长连续打卡记录
    checkins = query(
        'SELECT checkin_date FROM reading_checkins WHERE user_id = %s ORDER BY checkin_date',
        (user_id,)
    )
    max_streak = 0
    current_streak = 0
    prev_date = None
    from datetime import date, timedelta
    for r in checkins:
        d = r['checkin_date']
        if isinstance(d, str):
            from datetime import datetime
            d = datetime.strptime(d, '%Y-%m-%d').date()
        if prev_date and (d - prev_date).days == 1:
            current_streak += 1
        else:
            current_streak = 1
        max_streak = max(max_streak, current_streak)
        prev_date = d

    # 阅读速度（总字数 / 总分钟数）
    reading_data = query('''
        SELECT SUM(rp.total_percent * CASE rp.book_type
            WHEN 'library' THEN (SELECT word_count FROM library_books WHERE book_id = rp.book_id)
            WHEN 'work' THEN (SELECT word_count FROM works WHERE work_id = rp.book_id)
        END / 100) as total_words_read
        FROM reading_progress rp WHERE rp.user_id = %s
    ''', (user_id,), one=True)
    total_words = float(reading_data['total_words_read'] or 0)

    total_minutes_data = query(
        'SELECT SUM(read_minutes) as total FROM reading_checkins WHERE user_id = %s',
        (user_id,), one=True
    )
    total_mins = total_minutes_data['total'] or 0
    speed = round(total_words / total_mins) if total_mins > 0 else 0

    return ok({
        'max_streak': max_streak,
        'reading_speed': speed,  # 字/分钟
        'total_words_read': round(total_words),
    })
