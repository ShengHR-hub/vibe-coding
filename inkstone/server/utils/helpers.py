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
    """Check all achievement conditions for a user and unlock newly met ones. Returns list of newly unlocked achievement names."""
    from database.db import query, execute

    all_achievements = query('SELECT * FROM achievements')
    if not all_achievements:
        return []

    unlocked = query('SELECT achievement_id FROM user_achievements WHERE user_id = %s', (user_id,))
    unlocked_ids = {u['achievement_id'] for u in unlocked}

    stats = {
        'word_count': query('SELECT COALESCE(SUM(word_count), 0) as v FROM works WHERE user_id = %s', (user_id,), one=True)['v'],
        'likes': query('SELECT COALESCE(SUM(likes_count), 0) as v FROM works WHERE user_id = %s', (user_id,), one=True)['v'],
        'comments': query('SELECT COALESCE(SUM(comments_count), 0) as v FROM works WHERE user_id = %s', (user_id,), one=True)['v'],
        'works': query("SELECT COUNT(*) as v FROM works WHERE user_id = %s AND status = 'published'", (user_id,), one=True)['v'],
        'checkin_days': query('''
            SELECT COUNT(DISTINCT checkin_date) as v FROM challenge_checkins cc
            JOIN challenge_participants cp ON cc.participant_id = cp.participant_id
            WHERE cp.user_id = %s
        ''', (user_id,), one=True)['v'],
        'followers': query('SELECT COUNT(*) as v FROM follows WHERE following_id = %s', (user_id,), one=True)['v'],
    }

    newly_unlocked = []
    for ach in all_achievements:
        if ach['achievement_id'] in unlocked_ids:
            continue
        current = stats.get(ach['condition_type'], 0)
        if current >= ach['condition_value']:
            execute('INSERT IGNORE INTO user_achievements (user_id, achievement_id) VALUES (%s, %s)',
                    (user_id, ach['achievement_id']))
            newly_unlocked.append(ach['name'])

    if newly_unlocked:
        from routes.notifications import create_notification
        for name in newly_unlocked:
            create_notification(user_id, 'achievement', f'恭喜解锁成就「{name}」！', None)

    return newly_unlocked
