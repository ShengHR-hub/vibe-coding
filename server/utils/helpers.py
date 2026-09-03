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
        '(SELECT COUNT(*) FROM follows WHERE following_id = %s) as followers, '
        '(SELECT COUNT(*) FROM reading_bookshelf WHERE user_id = %s AND shelf_group = \'completed\') as books_read, '
        '(SELECT COUNT(DISTINCT checkin_date) FROM reading_checkins WHERE user_id = %s) as reading_streak, '
        '(SELECT COALESCE(SUM(read_minutes), 0) FROM reading_time_logs WHERE user_id = %s) as reading_minutes, '
        '(SELECT COUNT(*) FROM reading_annotations WHERE user_id = %s) as annotations, '
        '(SELECT COUNT(*) FROM reading_highlights WHERE user_id = %s) as highlights '
        'FROM works WHERE user_id = %s',
        (user_id, user_id, user_id, user_id, user_id, user_id, user_id), one=True
    )

    stats['reading_hours'] = (stats.pop('reading_minutes', 0) or 0) // 60

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
