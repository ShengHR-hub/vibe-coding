from collections import defaultdict
import time
from flask import session


def ok(data=None, msg='success'):
    return {'code': 0, 'data': data, 'msg': msg}


def fail(msg='error', code=1, data=None):
    return {'code': code, 'data': data, 'msg': msg}


def login_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return fail('请先登录', code=401)
        return func(*args, **kwargs)
    return wrapper


def get_login_user():
    return {
        'user_id': session.get('user_id'),
        'username': session.get('username')
    }


def _fmt(val):
    if val is None:
        return None
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return val


def check_achievements(user_id):
    """Check all achievement conditions for a user and unlock newly met ones.
    Optimized: single stats query + skip if all unlocked."""
    from database.db import query, execute

    all_achievements = query('SELECT * FROM achievements')
    if not all_achievements:
        return []

    unlocked = query('SELECT achievement_id FROM user_achievements WHERE user_id = %s', (user_id,))
    unlocked_ids = {u['achievement_id'] for u in unlocked}

    # 如果所有成就都已解锁，直接返回
    if len(unlocked_ids) >= len(all_achievements):
        return []

    # 合并查询获取所有统计值（减少数据库往返）
    stats = query(
        'SELECT '
        'COALESCE(SUM(word_count), 0) as word_count, '
        'COALESCE(SUM(likes_count), 0) as likes, '
        'COALESCE(SUM(comments_count), 0) as comments, '
        'COALESCE(SUM(CASE WHEN status = \'published\' THEN 1 ELSE 0 END), 0) as works, '
        '(SELECT COUNT(*) FROM follows WHERE following_id = %s) as followers '
        'FROM works WHERE user_id = %s',
        (user_id, user_id), one=True
    )

    # 写作打卡单独查询（涉及 JOIN）
    stats['checkin_days'] = query(
        'SELECT COUNT(DISTINCT cc.checkin_date) as v FROM challenge_checkins cc '
        'JOIN challenge_participants cp ON cc.participant_id = cp.participant_id '
        'WHERE cp.user_id = %s',
        (user_id,), one=True
    )['v'] or 0

    newly_unlocked = []
    for ach in all_achievements:
        if ach['achievement_id'] in unlocked_ids:
            continue
        current = stats.get(ach['condition_type'], 0) or 0
        if current >= ach['condition_value']:
            execute('INSERT IGNORE INTO user_achievements (user_id, achievement_id) VALUES (%s, %s)',
                    (user_id, ach['achievement_id']))
            newly_unlocked.append(ach['name'])

    if newly_unlocked:
        from routes.notifications import create_notification
        for name in newly_unlocked:
            create_notification(user_id, 'achievement', f'恭喜解锁成就「{name}」！', None)

    return newly_unlocked


# ---------------------------------------------------------------------------
# AI 调用配额（W1a）：按用户进程内限流（分钟窗口 + 每日上限）
# 注意：单进程有效；多 worker 部署时需换成 Redis（见 M3/部署项 Backlog）。
# ---------------------------------------------------------------------------
_ai_minute = defaultdict(list)   # user_id -> [时间戳]
_ai_daily = defaultdict(int)     # user_id -> 今日已用次数
_ai_day = {}                     # user_id -> 日期字符串


def check_ai_quota(user_id):
    """检查 AI 调用配额。返回 (ok: bool, msg: str)；未登录返回放行（由 login_required 拦截）。"""
    from config import Config
    if not user_id:
        return True, ''
    now = time.time()
    stamps = _ai_minute.setdefault(user_id, [])
    stamps[:] = [t for t in stamps if now - t < 60]
    if len(stamps) >= Config.AI_RATE_PER_MIN:
        return False, 'AI 请求太频繁，请稍后再试'
    today = time.strftime('%Y-%m-%d')
    if _ai_day.get(user_id) != today:
        _ai_day[user_id] = today
        _ai_daily[user_id] = 0
    if _ai_daily[user_id] >= Config.AI_DAILY_LIMIT:
        return False, '今日 AI 用量已达上限，请明天再试'
    stamps.append(now)
    _ai_daily[user_id] += 1
    return True, ''
