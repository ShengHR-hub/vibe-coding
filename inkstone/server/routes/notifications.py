import logging
from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, login_required, _fmt

logger = logging.getLogger(__name__)
notifications_bp = Blueprint('notifications', __name__)


def create_notification(user_id, ntype, content, related_id=None):
    """Create a notification. Fails silently to avoid breaking main flow."""
    try:
        execute(
            'INSERT INTO notifications (user_id, type, content, related_id) VALUES (%s, %s, %s, %s)',
            (user_id, ntype, content, related_id)
        )
    except Exception as e:
        logger.error(f'Failed to create notification: {e}')


@notifications_bp.get('')
@login_required
def list_notifications():
    user_id = session['user_id']
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(30, request.args.get('page_size', 20, type=int))

    total = query('SELECT COUNT(*) as cnt FROM notifications WHERE user_id = %s', (user_id,), one=True)['cnt']
    unread = query('SELECT COUNT(*) as cnt FROM notifications WHERE user_id = %s AND is_read = 0', (user_id,), one=True)['cnt']

    rows = query('''
        SELECT * FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    ''', (user_id, page_size, (page - 1) * page_size))

    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))

    return ok({'items': rows, 'total': total, 'unread': unread, 'page': page, 'page_size': page_size})


@notifications_bp.post('/mark-read')
@login_required
def mark_read():
    user_id = session['user_id']
    data = request.get_json() or {}
    notification_id = data.get('notification_id')
    mark_all = data.get('mark_all', False)

    if mark_all:
        execute('UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0', (user_id,))
        return ok(msg='全部标为已读')

    if notification_id:
        execute('UPDATE notifications SET is_read = 1 WHERE notification_id = %s AND user_id = %s',
                (notification_id, user_id))
        return ok(msg='已标为已读')

    return fail('缺少 notification_id 或 mark_all')
