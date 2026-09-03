from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, login_required, _fmt, check_achievements
from routes.notifications import create_notification

interactions_bp = Blueprint('interactions', __name__)


@interactions_bp.get('/comments/<int:work_id>')
def list_comments(work_id):
    rows = query('''
        SELECT c.*, u.username, u.avatar, u.level
        FROM comments c JOIN users u ON c.user_id = u.user_id
        WHERE c.work_id = %s
        ORDER BY c.is_pinned DESC, c.created_at ASC
    ''', (work_id,))

    # Build nested structure
    comment_map = {}
    roots = []
    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))
        r['replies'] = []
        comment_map[r['comment_id']] = r
        if r['parent_id'] is None:
            roots.append(r)

    for r in rows:
        if r['parent_id'] and r['parent_id'] in comment_map:
            comment_map[r['parent_id']]['replies'].append(r)

    return ok({'comments': roots, 'total': len(rows)})


@interactions_bp.post('/comments')
@login_required
def create_comment():
    data = request.get_json()
    work_id = data.get('work_id')
    content = (data.get('content') or '').strip()
    parent_id = data.get('parent_id')

    if not work_id or not content:
        return fail('请填写评论内容')

    comment_id = execute(
        'INSERT INTO comments (work_id, user_id, parent_id, content) VALUES (%s, %s, %s, %s)',
        (work_id, session['user_id'], parent_id, content)
    )
    execute('UPDATE works SET comments_count = comments_count + 1 WHERE work_id = %s', (work_id,))

    username = session.get('username', '某人')

    # Notify work author (unless self-comment)
    work_author = query('SELECT user_id FROM works WHERE work_id = %s', (work_id,), one=True)
    if work_author and work_author['user_id'] != session['user_id']:
        create_notification(work_author['user_id'], 'comment',
                            f'{username} 评论了你的作品', work_id)
    if work_author:
        check_achievements(work_author['user_id'])

    # Notify parent comment author (if replying)
    if parent_id:
        parent_author = query('SELECT user_id FROM comments WHERE comment_id = %s', (parent_id,), one=True)
        if parent_author and parent_author['user_id'] != session['user_id']:
            create_notification(parent_author['user_id'], 'reply',
                                f'{username} 回复了你的评论', work_id)

    return ok({'comment_id': comment_id}, msg='评论发表成功')


@interactions_bp.post('/like')
@login_required
def toggle_like():
    data = request.get_json()
    work_id = data.get('work_id')
    if not work_id:
        return fail('缺少作品ID')

    user_id = session['user_id']
    existing = query(
        'SELECT like_id FROM work_likes WHERE user_id = %s AND work_id = %s',
        (user_id, work_id), one=True
    )

    if existing:
        execute('DELETE FROM work_likes WHERE user_id = %s AND work_id = %s', (user_id, work_id))
        execute('UPDATE works SET likes_count = GREATEST(likes_count - 1, 0) WHERE work_id = %s', (work_id,))
        return ok({'liked': False}, msg='已取消点赞')
    else:
        try:
            execute('INSERT INTO work_likes (user_id, work_id) VALUES (%s, %s)', (user_id, work_id))
        except Exception:
            return ok({'liked': True}, msg='点赞成功')
        execute('UPDATE works SET likes_count = likes_count + 1 WHERE work_id = %s', (work_id,))

        work_author = query('SELECT user_id FROM works WHERE work_id = %s', (work_id,), one=True)
        if work_author:
            if work_author['user_id'] != user_id:
                create_notification(work_author['user_id'], 'like',
                                    f'{session.get("username", "某人")} 赞了你的作品', work_id)
            check_achievements(work_author['user_id'])

        return ok({'liked': True}, msg='点赞成功')


@interactions_bp.post('/favorite')
@login_required
def toggle_favorite():
    data = request.get_json()
    work_id = data.get('work_id')
    if not work_id:
        return fail('缺少作品ID')

    user_id = session['user_id']
    existing = query(
        'SELECT favorite_id FROM favorites WHERE user_id = %s AND work_id = %s',
        (user_id, work_id), one=True
    )

    if existing:
        execute('DELETE FROM favorites WHERE user_id = %s AND work_id = %s', (user_id, work_id))
        execute('UPDATE works SET favorites_count = GREATEST(favorites_count - 1, 0) WHERE work_id = %s', (work_id,))
        return ok({'favorited': False}, msg='已取消收藏')
    else:
        try:
            execute('INSERT INTO favorites (user_id, work_id) VALUES (%s, %s)', (user_id, work_id))
        except Exception:
            return ok({'favorited': True}, msg='收藏成功')
        execute('UPDATE works SET favorites_count = favorites_count + 1 WHERE work_id = %s', (work_id,))

        work_author = query('SELECT user_id FROM works WHERE work_id = %s', (work_id,), one=True)
        if work_author and work_author['user_id'] != user_id:
            create_notification(work_author['user_id'], 'favorite',
                                f'{session.get("username", "某人")} 收藏了你的作品', work_id)
        if work_author:
            check_achievements(work_author['user_id'])

        return ok({'favorited': True}, msg='收藏成功')


@interactions_bp.get('/favorites')
@login_required
def list_favorites():
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(30, request.args.get('page_size', 12, type=int))
    user_id = session['user_id']

    total = query(
        'SELECT COUNT(*) as cnt FROM favorites WHERE user_id = %s',
        (user_id,), one=True
    )['cnt']

    rows = query('''
        SELECT w.*, u.username, u.avatar, u.level, f.created_at as favorited_at
        FROM favorites f
        JOIN works w ON f.work_id = w.work_id
        JOIN users u ON w.user_id = u.user_id
        WHERE f.user_id = %s
        ORDER BY f.created_at DESC
        LIMIT %s OFFSET %s
    ''', (user_id, page_size, (page - 1) * page_size))

    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))
        r['updated_at'] = _fmt(r.get('updated_at'))
        r['favorited_at'] = _fmt(r.get('favorited_at'))

    return ok({'items': rows, 'total': total, 'page': page, 'page_size': page_size})
