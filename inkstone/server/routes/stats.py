import logging
import json
from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, login_required, _fmt
from utils.mimos import chat_completion
from utils.prompt_builder import build_style_analysis, build_monthly_report

logger = logging.getLogger(__name__)

stats_bp = Blueprint('stats', __name__)


@stats_bp.get('/overview')
@login_required
def overview():
    user_id = session['user_id']

    total_words = query(
        'SELECT COALESCE(SUM(word_count), 0) as wc FROM works WHERE user_id = %s',
        (user_id,), one=True)['wc']
    total_works = query(
        'SELECT COUNT(*) as cnt FROM works WHERE user_id = %s',
        (user_id,), one=True)['cnt']
    total_sessions = query(
        'SELECT COUNT(*) as cnt FROM writing_sessions WHERE user_id = %s',
        (user_id,), one=True)['cnt']

    today_words = query(
        'SELECT COALESCE(SUM(word_count), 0) as wc FROM writing_sessions WHERE user_id = %s AND session_date = CURDATE()',
        (user_id,), one=True)['wc']

    from datetime import date, timedelta
    # 一次查询获取所有写作日期，然后在 Python 中计算连续天数
    session_dates = query(
        'SELECT DISTINCT session_date FROM writing_sessions WHERE user_id = %s ORDER BY session_date DESC',
        (user_id,)
    )
    date_set = {str(r['session_date']) for r in session_dates}
    d = date.today()
    streak = 0
    for _ in range(365):
        if str(d) in date_set:
            streak += 1
            d = d - timedelta(days=1)
        else:
            break

    first_session = query(
        'SELECT MIN(session_date) as fd FROM writing_sessions WHERE user_id = %s',
        (user_id,), one=True)
    if first_session and first_session['fd']:
        days = max(1, (date.today() - first_session['fd']).days + 1)
        avg_daily = round(total_words / days)
    else:
        avg_daily = 0

    def session_words_since(days_ago):
        r = query(
            'SELECT COALESCE(SUM(word_count), 0) as wc FROM writing_sessions WHERE user_id = %s AND session_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)',
            (user_id, days_ago), one=True)
        return r['wc']

    this_week = session_words_since(7)
    last_week = session_words_since(14) - this_week
    week_change = this_week - last_week

    this_month = session_words_since(30)
    last_month = session_words_since(60) - this_month
    month_change = this_month - last_month

    return ok({
        'total_words': total_words,
        'total_works': total_works,
        'total_sessions': total_sessions,
        'today_words': today_words,
        'streak_days': streak,
        'avg_daily': avg_daily,
        'comparison': {
            'week_change': week_change,
            'month_change': month_change
        }
    })


@stats_bp.get('/overview/bar')
@login_required
def overview_bar():
    user_id = session['user_id']
    rows = query('''
        SELECT DATE_FORMAT(session_date, '%%Y-%%m') as month, COALESCE(SUM(word_count), 0) as words
        FROM writing_sessions
        WHERE user_id = %s AND session_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        GROUP BY month ORDER BY month
    ''', (user_id,))
    return ok({'months': rows})


@stats_bp.get('/heatmap')
@login_required
def heatmap():
    user_id = session['user_id']
    rows = query('''
        SELECT session_date, COALESCE(SUM(word_count), 0) as count
        FROM writing_sessions
        WHERE user_id = %s AND session_date >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)
        GROUP BY session_date ORDER BY session_date
    ''', (user_id,))
    for r in rows:
        r['session_date'] = _fmt(r.get('session_date'))
    return ok({'days': rows})


@stats_bp.get('/style')
@login_required
def style_analysis():
    user_id = session['user_id']

    works = query('''
        SELECT w.title, COALESCE(c.content, '') as content
        FROM works w
        LEFT JOIN chapters c ON w.work_id = c.work_id AND c.chapter_no = 1
        WHERE w.user_id = %s
        ORDER BY w.updated_at DESC LIMIT 5
    ''', (user_id,))

    if not works:
        return fail('暂无作品数据，写点东西再来吧')

    combined = '\n\n'.join(w['content'][:3000] for w in works if w['content'])
    if not combined.strip():
        return fail('暂无作品内容')

    try:
        messages = build_style_analysis(combined[:4000])
        result = chat_completion(messages, temperature=0.3, max_tokens=1024)
        result = result.strip()
        if result.startswith('```'):
            result = result.split('\n', 1)[1].rsplit('\n', 1)[0]
        style_data = json.loads(result)
        return ok({'style': style_data})
    except (json.JSONDecodeError, KeyError, ValueError):
        return fail('风格分析失败，请稍后再试')


@stats_bp.get('/report')
@login_required
def monthly_report():
    user_id = session['user_id']

    stats = query('''
        SELECT
            COALESCE(SUM(word_count), 0) as month_words,
            COUNT(DISTINCT session_date) as active_days,
            COUNT(*) as session_count
        FROM writing_sessions
        WHERE user_id = %s AND DATE_FORMAT(session_date, '%%Y-%%m') = DATE_FORMAT(CURDATE(), '%%Y-%%m')
    ''', (user_id,), one=True)

    last_month = query('''
        SELECT COALESCE(SUM(word_count), 0) as wc
        FROM writing_sessions
        WHERE user_id = %s AND DATE_FORMAT(session_date, '%%Y-%%m') = DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), '%%Y-%%m')
    ''', (user_id,), one=True)

    top_tags = query("SELECT tags FROM works WHERE user_id = %s AND tags != ''", (user_id,))
    tag_text = ', '.join(t['tags'] for t in top_tags) if top_tags else '无'

    stats_text = (
        f"本月写作字数: {stats['month_words']}字\n"
        f"活跃天数: {stats['active_days']}天\n"
        f"写作次数: {stats['session_count']}次\n"
        f"上月字数: {last_month['wc']}字\n"
        f"常用标签: {tag_text}\n"
    )

    try:
        messages = build_monthly_report(stats_text)
        result = chat_completion(messages, temperature=0.7, max_tokens=1024)
        return ok({'report': result, 'stats': {**stats, 'last_month_words': last_month['wc']}})
    except Exception as e:
        logger.error(f'Monthly report error: {e}')
        return fail('报告生成失败，请稍后再试')


@stats_bp.post('/session')
@login_required
def record_session():
    user_id = session['user_id']
    data = request.get_json() or {}
    work_id = data.get('work_id')
    word_count = data.get('word_count', 0)
    duration = data.get('duration', 30)

    try:
        word_count = max(0, int(word_count))
        duration = max(0, int(duration))
    except (ValueError, TypeError):
        word_count = 0
        duration = 30

    execute(
        'INSERT INTO writing_sessions (user_id, work_id, word_count, duration, session_date) VALUES (%s, %s, %s, %s, CURDATE())',
        (user_id, work_id, word_count, duration)
    )
    return ok(msg='已记录')


@stats_bp.get('/sessions')
@login_required
def list_sessions():
    user_id = session['user_id']
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(30, request.args.get('page_size', 20, type=int))

    total = query(
        'SELECT COUNT(*) as cnt FROM writing_sessions WHERE user_id = %s',
        (user_id,), one=True)['cnt']

    rows = query('''
        SELECT ws.*, w.title as work_title
        FROM writing_sessions ws
        LEFT JOIN works w ON ws.work_id = w.work_id
        WHERE ws.user_id = %s
        ORDER BY ws.created_at DESC
        LIMIT %s OFFSET %s
    ''', (user_id, page_size, (page - 1) * page_size))

    for r in rows:
        r['session_date'] = _fmt(r.get('session_date'))
        r['created_at'] = _fmt(r.get('created_at'))

    return ok({'items': rows, 'total': total, 'page': page, 'page_size': page_size})
