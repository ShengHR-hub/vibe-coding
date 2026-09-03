from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, login_required, check_achievements
from datetime import date, timedelta

daily_bp = Blueprint('daily', __name__)


@daily_bp.get('/today')
def today_prompt():
    """Get today's practice prompt. Returns the prompt assigned to today's date, or the latest one."""
    today = date.today()
    row = query('SELECT * FROM daily_prompts WHERE active_date = %s', [today], one=True)
    if not row:
        # Fallback: pick the most recent prompt
        row = query('SELECT * FROM daily_prompts ORDER BY active_date DESC LIMIT 1', one=True)
    if not row:
        return fail('暂无练习题目')

    # Check if current user has submitted
    submitted = False
    submission = None
    if session.get('user_id'):
        submission = query(
            'SELECT * FROM daily_submissions WHERE prompt_id = %s AND user_id = %s',
            [row['prompt_id'], session['user_id']], one=True
        )
        if submission:
            submitted = True

    return ok({
        'prompt': row,
        'submitted': submitted,
        'submission': submission,
    })


@daily_bp.get('/prompt/<int:prompt_id>')
def get_prompt(prompt_id):
    """Get a specific prompt by ID."""
    row = query('SELECT * FROM daily_prompts WHERE prompt_id = %s', [prompt_id], one=True)
    if not row:
        return fail('题目不存在', code=404)

    submitted = False
    submission = None
    if session.get('user_id'):
        submission = query(
            'SELECT * FROM daily_submissions WHERE prompt_id = %s AND user_id = %s',
            [prompt_id, session['user_id']], one=True
        )
        if submission:
            submitted = True

    return ok({'prompt': row, 'submitted': submitted, 'submission': submission})


@daily_bp.post('/submit')
@login_required
def submit():
    """Submit a response to today's prompt."""
    data = request.get_json(force=True) or {}
    prompt_id = data.get('prompt_id')
    content = (data.get('content') or '').strip()

    if not prompt_id or not content:
        return fail('请提供题目ID和内容')

    prompt = query('SELECT * FROM daily_prompts WHERE prompt_id = %s', [prompt_id], one=True)
    if not prompt:
        return fail('题目不存在')

    word_count = len(content.replace(' ', '').replace('\n', ''))

    # Check if already submitted
    existing = query(
        'SELECT submission_id FROM daily_submissions WHERE prompt_id = %s AND user_id = %s',
        [prompt_id, session['user_id']], one=True
    )
    if existing:
        return fail('你已经提交过这道题了')

    sub_id = execute(
        'INSERT INTO daily_submissions (prompt_id, user_id, content, word_count) VALUES (%s, %s, %s, %s)',
        [prompt_id, session['user_id'], content, word_count]
    )

    check_achievements(session['user_id'])
    return ok({'submission_id': sub_id, 'msg': '提交成功！'})


@daily_bp.get('/submissions/<int:prompt_id>')
def list_submissions(prompt_id):
    """List submissions for a prompt, ordered by likes."""
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(50, request.args.get('page_size', 20, type=int))
    sort = request.args.get('sort', 'hot')  # hot | new

    base = '''
        FROM daily_submissions ds
        JOIN users u ON ds.user_id = u.user_id
        WHERE ds.prompt_id = %s
    '''
    params = [prompt_id]
    order = 'ORDER BY ds.likes_count DESC, ds.created_at DESC'
    if sort == 'new':
        order = 'ORDER BY ds.created_at DESC'

    total = query(f'SELECT COUNT(*) as cnt {base}', params, one=True)['cnt']
    rows = query(
        f'SELECT ds.*, u.username, u.avatar {base} {order} LIMIT %s OFFSET %s',
        params + [page_size, (page - 1) * page_size]
    )

    # Mark which submissions the current user has liked
    user_id = session.get('user_id')
    if user_id and rows:
        sub_ids = [r['submission_id'] for r in rows]
        placeholders = ','.join(['%s'] * len(sub_ids))
        liked = query(
            f'SELECT submission_id FROM submission_likes WHERE user_id = %s AND submission_id IN ({placeholders})',
            [user_id] + sub_ids
        )
        liked_set = {l['submission_id'] for l in liked}
        for r in rows:
            r['_liked'] = r['submission_id'] in liked_set
    else:
        for r in rows:
            r['_liked'] = False

    return ok({'submissions': rows, 'total': total, 'page': page, 'page_size': page_size})


@daily_bp.post('/like')
@login_required
def like_submission():
    """Toggle like on a submission."""
    data = request.get_json(force=True) or {}
    submission_id = data.get('submission_id')
    if not submission_id:
        return fail('缺少参数')

    sub = query('SELECT * FROM daily_submissions WHERE submission_id = %s', [submission_id], one=True)
    if not sub:
        return fail('作品不存在')

    existing = query(
        'SELECT like_id FROM submission_likes WHERE user_id = %s AND submission_id = %s',
        [session['user_id'], submission_id], one=True
    )
    if existing:
        execute('DELETE FROM submission_likes WHERE like_id = %s', [existing['like_id']])
        execute('UPDATE daily_submissions SET likes_count = GREATEST(likes_count - 1, 0) WHERE submission_id = %s', [submission_id])
        return ok({'liked': False})
    else:
        execute('INSERT INTO submission_likes (user_id, submission_id) VALUES (%s, %s)', [session['user_id'], submission_id])
        execute('UPDATE daily_submissions SET likes_count = likes_count + 1 WHERE submission_id = %s', [submission_id])
        return ok({'liked': True})


@daily_bp.get('/history')
def prompt_history():
    """Get recent prompts with submission counts."""
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(30, request.args.get('page_size', 15, type=int))

    total = query('SELECT COUNT(*) as cnt FROM daily_prompts', one=True)['cnt']
    rows = query('''
        SELECT dp.*,
            (SELECT COUNT(*) FROM daily_submissions ds WHERE ds.prompt_id = dp.prompt_id) as submission_count
        FROM daily_prompts dp
        ORDER BY dp.active_date DESC
        LIMIT %s OFFSET %s
    ''', [page_size, (page - 1) * page_size])

    return ok({'prompts': rows, 'total': total, 'page': page, 'page_size': page_size})


@daily_bp.get('/streak')
@login_required
def streak():
    """Get user's submission streak and stats."""
    user_id = session['user_id']

    # Total submissions
    total = query('SELECT COUNT(*) as cnt FROM daily_submissions WHERE user_id = %s', [user_id], one=True)['cnt']

    # Recent submission dates (for calendar display)
    dates = query(
        'SELECT DATE(created_at) as d FROM daily_submissions WHERE user_id = %s ORDER BY created_at DESC LIMIT 30',
        [user_id]
    )

    # Calculate streak
    streak_count = 0
    check_date = date.today()
    date_set = {str(r['d']) for r in dates}

    while str(check_date) in date_set:
        streak_count += 1
        check_date -= timedelta(days=1)

    return ok({
        'total_submissions': total,
        'streak': streak_count,
        'recent_dates': [str(r['d']) for r in dates],
    })
