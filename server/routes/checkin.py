from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, login_required

checkin_bp = Blueprint('checkin', __name__)


@checkin_bp.post('')
@login_required
def record_reading():
    """记录阅读（自动打卡）"""
    user_id = session.get('user_id')
    data = request.get_json(force=True)
    read_minutes = max(0, data.get('read_minutes', 1))
    pages_read = max(0, data.get('pages_read', 0))
    books_read = max(0, data.get('books_read', 0))
    book_type = data.get('book_type', '')
    book_id = data.get('book_id', 0)

    # UPSERT: 今天已有记录则累加
    existing = query(
        'SELECT checkin_id, read_minutes FROM reading_checkins WHERE user_id = %s AND checkin_date = CURDATE()',
        (user_id,), one=True
    )
    if existing:
        execute(
            'UPDATE reading_checkins SET read_minutes = read_minutes + %s, pages_read = pages_read + %s, books_read = books_read + %s WHERE checkin_id = %s',
            (read_minutes, pages_read, books_read, existing['checkin_id'])
        )
    else:
        execute(
            'INSERT INTO reading_checkins (user_id, checkin_date, read_minutes, pages_read, books_read) VALUES (%s, CURDATE(), %s, %s, %s)',
            (user_id, read_minutes, pages_read, books_read)
        )

    # 记录按书籍的阅读时长
    if book_type and book_id and read_minutes > 0:
        execute(
            'INSERT INTO reading_time_logs (user_id, book_type, book_id, read_minutes, session_date) VALUES (%s, %s, %s, %s, CURDATE())',
            (user_id, book_type, book_id, read_minutes)
        )

    return ok()


@checkin_bp.get('/calendar')
@login_required
def checkin_calendar():
    """打卡日历（当月）"""
    user_id = session.get('user_id')
    month = request.args.get('month', '')  # 格式: 2026-06

    if month:
        rows = query(
            'SELECT checkin_date, read_minutes, pages_read FROM reading_checkins WHERE user_id = %s AND DATE_FORMAT(checkin_date, "%%Y-%%m") = %s ORDER BY checkin_date',
            (user_id, month)
        )
    else:
        rows = query(
            'SELECT checkin_date, read_minutes, pages_read FROM reading_checkins WHERE user_id = %s AND MONTH(checkin_date) = MONTH(CURDATE()) AND YEAR(checkin_date) = YEAR(CURDATE()) ORDER BY checkin_date',
            (user_id,)
        )

    for r in rows:
        r['checkin_date'] = str(r['checkin_date'])

    return ok({'days': rows})


@checkin_bp.get('/streak')
@login_required
def checkin_streak():
    """连续打卡天数"""
    user_id = session.get('user_id')

    rows = query(
        'SELECT checkin_date FROM reading_checkins WHERE user_id = %s ORDER BY checkin_date DESC',
        (user_id,)
    )

    if not rows:
        return ok({'streak': 0, 'total_days': 0})

    streak = 0
    from datetime import date, timedelta
    today = date.today()
    expected = today

    for r in rows:
        d = r['checkin_date']
        if isinstance(d, str):
            from datetime import datetime
            d = datetime.strptime(d, '%Y-%m-%d').date()
        if d == expected:
            streak += 1
            expected = expected - timedelta(days=1)
        elif d < expected:
            break

    return ok({'streak': streak, 'total_days': len(rows)})


@checkin_bp.get('/goals')
@login_required
def get_goals():
    """获取阅读目标"""
    user_id = session.get('user_id')
    from datetime import date
    today = date.today()
    month_str = today.strftime('%Y-%m')

    row = query(
        'SELECT * FROM reading_goals WHERE user_id = %s AND month = %s',
        (user_id, month_str), one=True
    )
    if not row:
        return ok({'goal': None})

    # 计算当月完成情况
    days = query(
        'SELECT checkin_date, read_minutes, books_read FROM reading_checkins WHERE user_id = %s AND DATE_FORMAT(checkin_date, "%%Y-%%m") = %s',
        (user_id, month_str)
    )
    total_minutes = sum(d['read_minutes'] for d in days)
    total_books = sum(d['books_read'] for d in days)

    return ok({
        'goal': {
            'target_minutes': row['target_minutes'],
            'target_books': row['target_books'],
            'current_minutes': total_minutes,
            'current_books': total_books,
            'days': [{'checkin_date': str(d['checkin_date']), 'read_minutes': d['read_minutes']} for d in days],
        }
    })


@checkin_bp.post('/goals')
@login_required
def set_goals():
    """设定阅读目标"""
    user_id = session.get('user_id')
    data = request.get_json(force=True)
    target_minutes = max(0, data.get('target_minutes', 0))
    target_books = max(0, data.get('target_books', 0))

    from datetime import date
    today = date.today()
    month_str = today.strftime('%Y-%m')

    existing = query(
        'SELECT goal_id FROM reading_goals WHERE user_id = %s AND month = %s',
        (user_id, month_str), one=True
    )
    if existing:
        execute(
            'UPDATE reading_goals SET target_minutes = %s, target_books = %s WHERE goal_id = %s',
            (target_minutes, target_books, existing['goal_id'])
        )
    else:
        execute(
            'INSERT INTO reading_goals (user_id, month, target_minutes, target_books) VALUES (%s, %s, %s, %s)',
            (user_id, month_str, target_minutes, target_books)
        )

    return ok()


@checkin_bp.get('/heatmap')
@login_required
def reading_heatmap():
    """阅读热力图数据（过去一年）"""
    user_id = session.get('user_id')
    from datetime import date, timedelta

    today = date.today()
    start_date = today - timedelta(days=364)

    rows = query(
        '''SELECT checkin_date, read_minutes
           FROM reading_checkins
           WHERE user_id = %s AND checkin_date >= %s
           ORDER BY checkin_date''',
        (user_id, start_date)
    )

    # 构建日期到分钟的映射
    data = {}
    for r in rows:
        d = r['checkin_date']
        if isinstance(d, str):
            from datetime import datetime
            d = datetime.strptime(d, '%Y-%m-%d').date()
        data[d.isoformat()] = r['read_minutes']

    # 生成完整的365天数据
    heatmap = []
    current = start_date
    while current <= today:
        date_str = current.isoformat()
        heatmap.append({
            'date': date_str,
            'minutes': data.get(date_str, 0),
            'level': _get_heatmap_level(data.get(date_str, 0))
        })
        current += timedelta(days=1)

    # 统计
    total_minutes = sum(d['minutes'] for d in heatmap)
    active_days = sum(1 for d in heatmap if d['minutes'] > 0)

    return ok({
        'heatmap': heatmap,
        'total_minutes': total_minutes,
        'active_days': active_days,
        'total_days': len(heatmap)
    })


def _get_heatmap_level(minutes):
    """根据阅读分钟数返回热力等级 0-4"""
    if minutes == 0:
        return 0
    elif minutes < 15:
        return 1
    elif minutes < 30:
        return 2
    elif minutes < 60:
        return 3
    else:
        return 4


@checkin_bp.get('/time-stats')
@login_required
def reading_time_stats():
    """按书籍统计阅读时长"""
    user_id = session.get('user_id')
    limit = min(50, request.args.get('limit', 10, type=int))

    rows = query('''
        SELECT rtl.book_type, rtl.book_id,
               SUM(rtl.read_minutes) as total_minutes,
               COUNT(DISTINCT rtl.session_date) as days,
               COALESCE(lb.title, w.title) as title,
               COALESCE(lb.author, u.username) as author
        FROM reading_time_logs rtl
        LEFT JOIN library_books lb ON rtl.book_type = 'library' AND lb.book_id = rtl.book_id
        LEFT JOIN works w ON rtl.book_type = 'work' AND w.work_id = rtl.book_id
        LEFT JOIN users u ON rtl.book_type = 'work' AND w.user_id = u.user_id
        WHERE rtl.user_id = %s
        GROUP BY rtl.book_type, rtl.book_id
        ORDER BY total_minutes DESC
        LIMIT %s
    ''', (user_id, limit))

    return ok({'items': rows})


@checkin_bp.get('/daily-stats')
@login_required
def daily_reading_stats():
    """每日阅读时长统计（最近30天）"""
    user_id = session.get('user_id')
    days = min(90, request.args.get('days', 30, type=int))

    rows = query('''
        SELECT checkin_date, read_minutes, pages_read
        FROM reading_checkins
        WHERE user_id = %s AND checkin_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        ORDER BY checkin_date
    ''', (user_id, days))

    for r in rows:
        r['checkin_date'] = str(r['checkin_date'])

    return ok({'items': rows})
