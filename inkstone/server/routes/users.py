from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, login_required, _fmt, check_achievements
from routes.notifications import create_notification
import os, uuid

users_bp = Blueprint('users', __name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
ALLOWED_TYPES = {'image/png', 'image/jpeg', 'image/gif', 'image/webp'}
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB

# Level thresholds: exp needed for each level
LEVEL_THRESHOLDS = [0, 100, 500, 1500, 5000, 12000, 30000, 80000, 200000, 500000]


def _compute_level(exp):
    """Return (level, prev_level_exp, next_level_exp) based on exp."""
    level = 1
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if exp >= threshold:
            level = i + 1
    prev_exp = LEVEL_THRESHOLDS[level - 1]
    next_exp = LEVEL_THRESHOLDS[level] if level < len(LEVEL_THRESHOLDS) else None
    return level, prev_exp, next_exp


def _calc_user_exp(user_id):
    """Calculate user exp from word_count + likes + comments."""
    stats = query('''
        SELECT COALESCE(SUM(w.word_count), 0) as total_words,
               COALESCE(SUM(w.likes_count), 0) as total_likes,
               COALESCE(SUM(w.comments_count), 0) as total_comments
        FROM works w WHERE w.user_id = %s
    ''', (user_id,), one=True)
    return stats['total_words'] + stats['total_likes'] * 2 + stats['total_comments'] * 3


@users_bp.get('/<int:user_id>')
def get_profile(user_id):
    user = query('SELECT user_id, username, avatar, cover_image, bio, level, exp, created_at FROM users WHERE user_id = %s', (user_id,), one=True)
    if not user:
        return fail('用户不存在', code=404)

    # Recalculate exp and level
    exp = _calc_user_exp(user_id)
    level, prev_exp, next_exp = _compute_level(exp)
    if exp != user['exp'] or level != user['level']:
        execute('UPDATE users SET exp = %s, level = %s WHERE user_id = %s', (exp, level, user_id))
        user['exp'] = exp
        user['level'] = level

    user['created_at'] = _fmt(user.get('created_at'))

    # Stats
    works_count = query('SELECT COUNT(*) as cnt FROM works WHERE user_id = %s AND status = %s', (user_id, 'published'), one=True)['cnt']
    total_words = query('SELECT COALESCE(SUM(word_count), 0) as wc FROM works WHERE user_id = %s', (user_id,), one=True)['wc']
    followers_count = query('SELECT COUNT(*) as cnt FROM follows WHERE following_id = %s', (user_id,), one=True)['cnt']
    following_count = query('SELECT COUNT(*) as cnt FROM follows WHERE follower_id = %s', (user_id,), one=True)['cnt']
    total_likes = query('SELECT COALESCE(SUM(likes_count), 0) as lc FROM works WHERE user_id = %s', (user_id,), one=True)['lc']

    # Is current user following?
    is_following = False
    if 'user_id' in session and session['user_id'] != user_id:
        f = query('SELECT 1 FROM follows WHERE follower_id = %s AND following_id = %s',
                  (session['user_id'], user_id), one=True)
        is_following = f is not None

    return ok({
        'user': user,
        'stats': {
            'works_count': works_count,
            'total_words': total_words,
            'total_likes': total_likes,
            'followers_count': followers_count,
            'following_count': following_count
        },
        'is_following': is_following,
        'is_own': 'user_id' in session and session['user_id'] == user_id,
        'prev_level_exp': prev_exp,
        'next_level_exp': next_exp
    })


@users_bp.post('/upload')
@login_required
def upload_file():
    if 'file' not in request.files:
        return fail('未选择文件')
    file = request.files['file']
    if not file.filename:
        return fail('文件名为空')

    # Check file size via Content-Length
    content_length = request.content_length
    if content_length and content_length > MAX_UPLOAD_SIZE:
        return fail(f'文件过大，最大允许 {MAX_UPLOAD_SIZE // (1024*1024)}MB')

    # Validate extension
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return fail('仅支持 PNG/JPG/GIF/WebP 图片')
    if file.content_type not in ALLOWED_TYPES:
        return fail('仅支持 PNG/JPG/GIF/WebP 图片')

    # Read content and check actual size
    file_bytes = file.read()
    if len(file_bytes) > MAX_UPLOAD_SIZE:
        return fail(f'文件过大，最大允许 {MAX_UPLOAD_SIZE // (1024*1024)}MB')

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(file_bytes)

    return ok(data={'url': f'/uploads/{filename}'})


@users_bp.put('/profile')
@login_required
def edit_profile():
    data = request.get_json()
    user_id = session['user_id']

    avatar = data.get('avatar', '').strip()
    cover_image = data.get('cover_image', '').strip()
    bio = data.get('bio', '').strip()

    execute('UPDATE users SET avatar = %s, cover_image = %s, bio = %s WHERE user_id = %s',
            (avatar, cover_image, bio, user_id))

    return ok(msg='资料已更新')


@users_bp.post('/follow')
@login_required
def toggle_follow():
    data = request.get_json()
    following_id = data.get('user_id')
    if not following_id:
        return fail('缺少用户ID')
    following_id = int(following_id)

    follower_id = session['user_id']
    if follower_id == following_id:
        return fail('不能关注自己')

    existing = query('SELECT follow_id FROM follows WHERE follower_id = %s AND following_id = %s',
                     (follower_id, following_id), one=True)

    if existing:
        execute('DELETE FROM follows WHERE follow_id = %s', (existing['follow_id'],))
        return ok({'following': False}, msg='已取消关注')
    else:
        execute('INSERT INTO follows (follower_id, following_id) VALUES (%s, %s)',
                (follower_id, following_id))

        create_notification(following_id, 'follow',
                            f'{session.get("username", "某人")} 关注了你',
                            related_id=follower_id)

        check_achievements(following_id)

        return ok({'following': True}, msg='关注成功')


@users_bp.get('/<int:user_id>/followers')
def list_followers(user_id):
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(30, request.args.get('page_size', 20, type=int))

    total = query('SELECT COUNT(*) as cnt FROM follows WHERE following_id = %s', (user_id,), one=True)['cnt']

    rows = query('''
        SELECT u.user_id, u.username, u.avatar, u.bio, f.created_at as followed_at
        FROM follows f JOIN users u ON f.follower_id = u.user_id
        WHERE f.following_id = %s
        ORDER BY f.created_at DESC
        LIMIT %s OFFSET %s
    ''', (user_id, page_size, (page - 1) * page_size))

    for r in rows:
        r['followed_at'] = _fmt(r.get('followed_at'))

    return ok({'items': rows, 'total': total, 'page': page, 'page_size': page_size})


@users_bp.get('/<int:user_id>/following')
def list_following(user_id):
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(30, request.args.get('page_size', 20, type=int))

    total = query('SELECT COUNT(*) as cnt FROM follows WHERE follower_id = %s', (user_id,), one=True)['cnt']

    rows = query('''
        SELECT u.user_id, u.username, u.avatar, u.bio, f.created_at as followed_at
        FROM follows f JOIN users u ON f.following_id = u.user_id
        WHERE f.follower_id = %s
        ORDER BY f.created_at DESC
        LIMIT %s OFFSET %s
    ''', (user_id, page_size, (page - 1) * page_size))

    for r in rows:
        r['followed_at'] = _fmt(r.get('followed_at'))

    return ok({'items': rows, 'total': total, 'page': page, 'page_size': page_size})


@users_bp.get('/<int:user_id>/works')
def list_user_works(user_id):
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(30, request.args.get('page_size', 12, type=int))

    total = query("SELECT COUNT(*) as cnt FROM works WHERE user_id = %s AND status = 'published'",
                  (user_id,), one=True)['cnt']

    rows = query('''
        SELECT w.*, u.username, u.avatar
        FROM works w JOIN users u ON w.user_id = u.user_id
        WHERE w.user_id = %s AND w.status = 'published'
        ORDER BY w.updated_at DESC
        LIMIT %s OFFSET %s
    ''', (user_id, page_size, (page - 1) * page_size))

    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))
        r['updated_at'] = _fmt(r.get('updated_at'))

    return ok({'items': rows, 'total': total, 'page': page, 'page_size': page_size})


@users_bp.get('/<int:user_id>/favorites')
def list_user_favorites(user_id):
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(30, request.args.get('page_size', 12, type=int))

    total = query('SELECT COUNT(*) as cnt FROM favorites WHERE user_id = %s',
                  (user_id,), one=True)['cnt']

    rows = query('''
        SELECT w.*, u.username, u.avatar, f.created_at as favorited_at
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


@users_bp.get('/achievements')
@login_required
def list_achievements():
    user_id = session['user_id']

    # Check for any missed unlocks
    check_achievements(user_id)

    # All achievement definitions
    all_achievements = query('SELECT * FROM achievements ORDER BY condition_value')

    # User's unlocked achievements
    unlocked = query('SELECT achievement_id, unlocked_at FROM user_achievements WHERE user_id = %s', (user_id,))
    unlocked_map = {u['achievement_id']: _fmt(u['unlocked_at']) for u in unlocked}

    # User stats for progress calculation
    total_words = query('SELECT COALESCE(SUM(word_count), 0) as wc FROM works WHERE user_id = %s', (user_id,), one=True)['wc']
    total_likes = query('SELECT COALESCE(SUM(likes_count), 0) as lc FROM works WHERE user_id = %s', (user_id,), one=True)['lc']
    total_comments = query('SELECT COALESCE(SUM(comments_count), 0) as cc FROM works WHERE user_id = %s', (user_id,), one=True)['cc']
    works_count = query('SELECT COUNT(*) as cnt FROM works WHERE user_id = %s AND status = %s', (user_id, 'published'), one=True)['cnt']
    checkin_days = query('''
        SELECT COUNT(DISTINCT checkin_date) as cnt FROM challenge_checkins cc
        JOIN challenge_participants cp ON cc.participant_id = cp.participant_id
        WHERE cp.user_id = %s
    ''', (user_id,), one=True)['cnt']
    followers_count = query('SELECT COUNT(*) as cnt FROM follows WHERE following_id = %s', (user_id,), one=True)['cnt']

    result = []
    for ach in all_achievements:
        current = 0
        ct = ach['condition_type']
        if ct == 'word_count':
            current = total_words
        elif ct == 'likes':
            current = total_likes
        elif ct == 'comments':
            current = total_comments
        elif ct == 'works':
            current = works_count
        elif ct == 'checkin_days':
            current = checkin_days
        elif ct == 'followers':
            current = followers_count

        target = ach['condition_value']
        result.append({
            'achievement_id': ach['achievement_id'],
            'name': ach['name'],
            'description': ach['description'],
            'icon': ach['icon'],
            'condition_type': ct,
            'condition_value': target,
            'current': current,
            'unlocked': ach['achievement_id'] in unlocked_map,
            'unlocked_at': unlocked_map.get(ach['achievement_id'])
        })

    return ok({'achievements': result})
