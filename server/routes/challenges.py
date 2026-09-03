from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, login_required, _fmt, check_achievements

challenges_bp = Blueprint('challenges', __name__)


@challenges_bp.get('')
def list_challenges():
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(30, request.args.get('page_size', 12, type=int))
    status_filter = request.args.get('status', '').strip() or None

    conditions = []
    params = []

    if status_filter:
        conditions.append('status = %s')
        params.append(status_filter)

    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

    total = query(f'SELECT COUNT(*) as cnt FROM challenges {where}', params, one=True)['cnt']

    rows = query(f'''
        SELECT * FROM challenges
        {where}
        ORDER BY FIELD(status, 'active', 'upcoming', 'ended'), start_date DESC
        LIMIT %s OFFSET %s
    ''', params + [page_size, (page - 1) * page_size])

    for r in rows:
        r['start_date'] = _fmt(r.get('start_date'))
        r['end_date'] = _fmt(r.get('end_date'))
        r['created_at'] = _fmt(r.get('created_at'))

    # Check current user's participation for each challenge
    user_id = session.get('user_id')
    if user_id:
        challenge_ids = [r['challenge_id'] for r in rows]
        if challenge_ids:
            placeholders = ','.join(['%s'] * len(challenge_ids))
            participations = query(f'''
                SELECT challenge_id FROM challenge_participants
                WHERE user_id = %s AND challenge_id IN ({placeholders})
            ''', [user_id] + challenge_ids)
            joined_ids = {p['challenge_id'] for p in participations}
            for r in rows:
                r['is_joined'] = r['challenge_id'] in joined_ids
    else:
        for r in rows:
            r['is_joined'] = False

    return ok({'items': rows, 'total': total, 'page': page, 'page_size': page_size})


@challenges_bp.post('/<int:challenge_id>/join')
@login_required
def join_challenge(challenge_id):
    user_id = session['user_id']

    challenge = query('SELECT * FROM challenges WHERE challenge_id = %s', (challenge_id,), one=True)
    if not challenge:
        return fail('挑战不存在', code=404)
    if challenge['status'] == 'ended':
        return fail('挑战已结束')

    existing = query(
        'SELECT participant_id FROM challenge_participants WHERE challenge_id = %s AND user_id = %s',
        (challenge_id, user_id), one=True
    )
    if existing:
        return fail('已参加该挑战')

    execute('INSERT INTO challenge_participants (challenge_id, user_id) VALUES (%s, %s)',
            (challenge_id, user_id))
    execute('UPDATE challenges SET participant_count = participant_count + 1 WHERE challenge_id = %s',
            (challenge_id,))

    return ok(msg='参加成功')


@challenges_bp.post('/<int:challenge_id>/checkin')
@login_required
def checkin(challenge_id):
    user_id = session['user_id']
    data = request.get_json() or {}
    try:
        word_count = max(0, int(data.get('word_count', 0) or 0))
    except (ValueError, TypeError):
        word_count = 0
    note = (data.get('note') or '').strip()

    participant = query(
        'SELECT participant_id, checkin_days FROM challenge_participants WHERE challenge_id = %s AND user_id = %s',
        (challenge_id, user_id), one=True
    )
    if not participant:
        return fail('请先参加挑战')

    challenge = query('SELECT * FROM challenges WHERE challenge_id = %s', (challenge_id,), one=True)
    if challenge['status'] == 'ended':
        return fail('挑战已结束')

    from datetime import date
    today = date.today()
    if today < challenge['start_date']:
        return fail('挑战尚未开始')
    if today > challenge['end_date']:
        return fail('挑战已结束')

    # 用 INSERT ... ON DUPLICATE KEY UPDATE 避免竞态
    try:
        execute(
            'INSERT INTO challenge_checkins (participant_id, checkin_date, word_count, note) '
            'VALUES (%s, CURDATE(), %s, %s) '
            'ON DUPLICATE KEY UPDATE word_count = %s, note = %s',
            (participant['participant_id'], word_count, note, word_count, note)
        )
    except Exception:
        return fail('打卡失败，请稍后再试')

    # 重新计算总进度
    total_progress = query(
        'SELECT COALESCE(SUM(word_count), 0) as total FROM challenge_checkins WHERE participant_id = %s',
        (participant['participant_id'],), one=True
    )['total']
    checkin_count = query(
        'SELECT COUNT(*) as cnt FROM challenge_checkins WHERE participant_id = %s',
        (participant['participant_id'],), one=True
    )['cnt']

    execute(
        'UPDATE challenge_participants SET progress = %s, checkin_days = %s WHERE participant_id = %s',
        (total_progress, checkin_count, participant['participant_id'])
    )
    check_achievements(user_id)
    return ok(msg='打卡成功')


@challenges_bp.get('/<int:challenge_id>/checkins')
@login_required
def list_checkins(challenge_id):
    user_id = session['user_id']

    participant = query(
        'SELECT participant_id FROM challenge_participants WHERE challenge_id = %s AND user_id = %s',
        (challenge_id, user_id), one=True
    )
    if not participant:
        return fail('请先参加挑战')

    rows = query('''
        SELECT checkin_date, word_count, note
        FROM challenge_checkins
        WHERE participant_id = %s
        ORDER BY checkin_date DESC
        LIMIT 365
    ''', (participant['participant_id'],))

    for r in rows:
        r['checkin_date'] = _fmt(r.get('checkin_date'))

    return ok({'items': rows})


@challenges_bp.get('/<int:challenge_id>/relay')
def list_relay(challenge_id):
    rows = query('''
        SELECT rs.*, u.username, u.avatar
        FROM relay_segments rs JOIN users u ON rs.user_id = u.user_id
        WHERE rs.challenge_id = %s
        ORDER BY rs.segment_order
    ''', (challenge_id,))

    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))

    return ok({'items': rows})


@challenges_bp.post('/<int:challenge_id>/relay')
@login_required
def add_relay(challenge_id):
    user_id = session['user_id']
    data = request.get_json() or {}
    content = (data.get('content') or '').strip()

    if not content:
        return fail('内容不能为空')

    challenge = query('SELECT * FROM challenges WHERE challenge_id = %s', (challenge_id,), one=True)
    if not challenge:
        return fail('挑战不存在', code=404)
    if challenge['status'] == 'ended':
        return fail('挑战已结束')

    participant = query(
        'SELECT participant_id FROM challenge_participants WHERE challenge_id = %s AND user_id = %s',
        (challenge_id, user_id), one=True
    )
    if not participant:
        return fail('请先参加挑战')

    next_order = query(
        'SELECT COALESCE(MAX(segment_order), 0) + 1 as nxt FROM relay_segments WHERE challenge_id = %s',
        (challenge_id,), one=True
    )['nxt']

    execute(
        'INSERT INTO relay_segments (challenge_id, user_id, content, segment_order) VALUES (%s, %s, %s, %s)',
        (challenge_id, user_id, content, next_order)
    )

    return ok({'segment_order': next_order}, msg='接力成功')
