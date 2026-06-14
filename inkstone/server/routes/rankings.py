from flask import Blueprint, request
from database.db import query
from utils.helpers import ok

rankings_bp = Blueprint('rankings', __name__)


@rankings_bp.get('/works')
def works_ranking():
    """Top works ranked by metric."""
    metric = request.args.get('metric', 'hot')  # hot | views | likes | comments
    limit = min(50, request.args.get('limit', 20, type=int))

    order_map = {
        'hot': '(w.views * 0.3 + w.likes_count * 5 + w.comments_count * 3) DESC',
        'views': 'w.views DESC',
        'likes': 'w.likes_count DESC',
        'comments': 'w.comments_count DESC',
    }
    order = order_map.get(metric, order_map['hot'])

    rows = query(f'''
        SELECT w.work_id, w.title, w.type, w.summary, w.tags,
               w.word_count, w.views, w.likes_count, w.comments_count,
               w.created_at, u.user_id, u.username, u.avatar
        FROM works w
        JOIN users u ON w.user_id = u.user_id
        WHERE w.status = 'published'
        ORDER BY {order}
        LIMIT %s
    ''', [limit])

    return ok({'works': rows, 'metric': metric})


@rankings_bp.get('/authors')
def authors_ranking():
    """Top authors ranked by exp."""
    limit = min(50, request.args.get('limit', 20, type=int))

    rows = query('''
        SELECT u.user_id, u.username, u.avatar, u.bio, u.level, u.exp,
               COUNT(DISTINCT w.work_id) as work_count,
               COALESCE(SUM(w.views), 0) as total_views,
               COALESCE(SUM(w.likes_count), 0) as total_likes
        FROM users u
        LEFT JOIN works w ON u.user_id = w.user_id AND w.status = 'published'
        GROUP BY u.user_id
        ORDER BY u.exp DESC
        LIMIT %s
    ''', [limit])

    return ok({'authors': rows})


@rankings_bp.get('/weekly')
def weekly_ranking():
    """This week's hottest works (by recent likes + comments)."""
    limit = min(30, request.args.get('limit', 15, type=int))

    # Use likes and comments from the past 7 days
    rows = query('''
        SELECT w.work_id, w.title, w.type, w.summary, w.tags,
               w.word_count, w.views, w.likes_count, w.comments_count,
               w.created_at, u.user_id, u.username, u.avatar,
               COALESCE(recent.recent_likes, 0) as recent_likes,
               COALESCE(recent.recent_comments, 0) as recent_comments
        FROM works w
        JOIN users u ON w.user_id = u.user_id
        LEFT JOIN (
            SELECT w2.work_id,
                   COUNT(DISTINCT wl.like_id) as recent_likes,
                   COUNT(DISTINCT c.comment_id) as recent_comments
            FROM works w2
            LEFT JOIN work_likes wl ON w2.work_id = wl.work_id AND wl.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            LEFT JOIN comments c ON w2.work_id = c.work_id AND c.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            WHERE w2.status = 'published'
            GROUP BY w2.work_id
        ) recent ON w.work_id = recent.work_id
        WHERE w.status = 'published'
        ORDER BY (recent.recent_likes * 3 + recent.recent_comments * 2 + w.views * 0.1) DESC
        LIMIT %s
    ''', [limit])

    return ok({'works': rows})


@rankings_bp.get('/new')
def new_works():
    """Latest published works."""
    limit = min(30, request.args.get('limit', 15, type=int))

    rows = query('''
        SELECT w.work_id, w.title, w.type, w.summary, w.tags,
               w.word_count, w.views, w.likes_count, w.comments_count,
               w.created_at, u.user_id, u.username, u.avatar
        FROM works w
        JOIN users u ON w.user_id = u.user_id
        WHERE w.status = 'published'
        ORDER BY w.created_at DESC
        LIMIT %s
    ''', [limit])

    return ok({'works': rows})
