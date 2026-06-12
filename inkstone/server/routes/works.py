from flask import Blueprint, request, session
import re, json
from database.db import query, execute
from utils.helpers import ok, fail, login_required, _fmt

works_bp = Blueprint('works', __name__)


@works_bp.get('')
@login_required
def list_works():
    user_id = session['user_id']
    wtype = request.args.get('type', '')
    status = request.args.get('status', '')
    page = max(1, request.args.get('page', 1, type=int))
    page_size = min(50, request.args.get('page_size', 12, type=int))

    conditions = ['user_id = %s']
    params = [user_id]

    if wtype:
        conditions.append('type = %s')
        params.append(wtype)
    if status:
        conditions.append('status = %s')
        params.append(status)

    where = ' AND '.join(conditions)
    total = query(f'SELECT COUNT(*) as cnt FROM works WHERE {where}', params, one=True)['cnt']

    rows = query(
        f'SELECT * FROM works WHERE {where} ORDER BY updated_at DESC LIMIT %s OFFSET %s',
        params + [page_size, (page - 1) * page_size]
    )
    for r in rows:
        r['created_at'] = _fmt(r.get('created_at'))
        r['updated_at'] = _fmt(r.get('updated_at'))

    return ok({'items': rows, 'total': total, 'page': page, 'page_size': page_size})


@works_bp.post('')
@login_required
def create_work():
    data = request.get_json()
    title = (data.get('title') or '').strip()
    wtype = data.get('type', 'novel')
    summary = (data.get('summary') or '').strip()
    tags = (data.get('tags') or '').strip()
    content = (data.get('content') or '').strip()

    if not title:
        return fail('作品标题不能为空')
    if wtype not in ('novel', 'poetry', 'essay', 'script'):
        return fail('无效的作品类型')

    user_id = session['user_id']
    work_id = execute(
        'INSERT INTO works (user_id, title, type, summary, tags) VALUES (%s, %s, %s, %s, %s)',
        (user_id, title, wtype, summary, tags)
    )
    wc = len(re.sub(r'\s', '', content)) if content else 0
    execute(
        'INSERT INTO chapters (work_id, chapter_no, title, content, word_count) VALUES (%s, 1, %s, %s, %s)',
        (work_id, '第一章' if wtype == 'novel' else '', content, wc)
    )
    execute('UPDATE works SET word_count = %s WHERE work_id = %s', (wc, work_id))

    return ok({'work_id': work_id}, msg='作品创建成功')


@works_bp.get('/public/<int:work_id>')
def get_public_work(work_id):
    work = query(
        "SELECT w.*, u.username, u.avatar, u.level FROM works w JOIN users u ON w.user_id = u.user_id WHERE w.work_id = %s AND w.status = 'published'",
        (work_id,), one=True
    )
    if not work:
        return fail('作品不存在', code=404)
    work['created_at'] = _fmt(work.get('created_at'))
    work['updated_at'] = _fmt(work.get('updated_at'))

    chapters = query('SELECT * FROM chapters WHERE work_id = %s ORDER BY chapter_no', (work_id,))
    for c in chapters:
        c['created_at'] = _fmt(c.get('created_at'))
        c['updated_at'] = _fmt(c.get('updated_at'))

    # Increment view count
    execute('UPDATE works SET views = views + 1 WHERE work_id = %s', (work_id,))

    # Check login user's like/favorite status
    liked = False
    favorited = False
    if 'user_id' in session:
        l = query('SELECT 1 FROM work_likes WHERE user_id = %s AND work_id = %s', (session['user_id'], work_id), one=True)
        liked = l is not None
        f = query('SELECT 1 FROM favorites WHERE user_id = %s AND work_id = %s', (session['user_id'], work_id), one=True)
        favorited = f is not None

    return ok({'work': work, 'chapters': chapters, 'liked': liked, 'favorited': favorited})


@works_bp.get('/<int:work_id>')
@login_required
def get_own_work(work_id):
    work = query('SELECT * FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)
    work['created_at'] = _fmt(work.get('created_at'))
    work['updated_at'] = _fmt(work.get('updated_at'))

    chapters = query('SELECT * FROM chapters WHERE work_id = %s ORDER BY chapter_no', (work_id,))
    for c in chapters:
        c['created_at'] = _fmt(c.get('created_at'))
        c['updated_at'] = _fmt(c.get('updated_at'))

    return ok({'work': work, 'chapters': chapters})


@works_bp.put('/<int:work_id>')
@login_required
def update_work(work_id):
    work = query('SELECT * FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)

    data = request.get_json()

    new_title = (data.get('title') or '').strip()
    if 'title' in data and not new_title:
        return fail('作品标题不能为空')

    # Save version snapshot
    chapters = query('SELECT * FROM chapters WHERE work_id = %s ORDER BY chapter_no', (work_id,))
    snapshot = json.dumps({
        'work': {k: _fmt(v) for k, v in work.items()},
        'chapters': [{k: _fmt(v) for k, v in ch.items()} for ch in chapters]
    }, ensure_ascii=False)
    execute('INSERT INTO work_versions (work_id, content_json, word_count) VALUES (%s, %s, %s)',
            (work_id, snapshot, work['word_count']))

    # Update work metadata
    title = data.get('title', work['title'])
    summary = data.get('summary', work['summary'])
    tags = data.get('tags', work['tags'])
    execute('UPDATE works SET title = %s, summary = %s, tags = %s WHERE work_id = %s',
            (title, summary, tags, work_id))

    # Update chapter content if provided
    chapter_id = data.get('chapter_id')
    chapter_content = data.get('content')
    chapter_title = data.get('chapter_title')
    if chapter_id and chapter_content is not None:
        wc = len(re.sub(r'\s', '', chapter_content)) if chapter_content else 0
        execute('UPDATE chapters SET content = %s, title = %s, word_count = %s WHERE chapter_id = %s AND work_id = %s',
                (chapter_content, chapter_title or '', wc, chapter_id, work_id))
        # Update total word count
        total_wc = query('SELECT COALESCE(SUM(word_count), 0) as wc FROM chapters WHERE work_id = %s', (work_id,), one=True)['wc']
        execute('UPDATE works SET word_count = %s WHERE work_id = %s', (total_wc, work_id))

    return ok(msg='保存成功')


@works_bp.delete('/<int:work_id>')
@login_required
def delete_work(work_id):
    work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)
    execute('DELETE FROM works WHERE work_id = %s', (work_id,))
    return ok(msg='作品已删除')


@works_bp.get('/<int:work_id>/versions')
@login_required
def list_versions(work_id):
    work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)
    versions = query('SELECT version_id, word_count, saved_at FROM work_versions WHERE work_id = %s ORDER BY saved_at DESC', (work_id,))
    for v in versions:
        v['saved_at'] = _fmt(v.get('saved_at'))
    return ok({'versions': versions})


@works_bp.post('/<int:work_id>/versions/<int:version_id>/rollback')
@login_required
def rollback_version(work_id, version_id):
    work = query('SELECT * FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)

    version = query('SELECT * FROM work_versions WHERE version_id = %s AND work_id = %s', (version_id, work_id), one=True)
    if not version:
        return fail('版本不存在', code=404)

    snapshot = json.loads(version['content_json'])
    old_chapters = snapshot.get('chapters', [])

    # Save current state before rollback (so it's reversible)
    current_chapters = query('SELECT * FROM chapters WHERE work_id = %s ORDER BY chapter_no', (work_id,))
    current_snapshot = json.dumps({
        'work': {k: _fmt(v) for k, v in work.items()},
        'chapters': [{k: _fmt(v) for k, v in ch.items()} for ch in current_chapters]
    }, ensure_ascii=False)
    execute('INSERT INTO work_versions (work_id, content_json, word_count) VALUES (%s, %s, %s)',
            (work_id, current_snapshot, work['word_count']))

    # Restore chapters from version
    execute('DELETE FROM chapters WHERE work_id = %s', (work_id,))
    for ch in old_chapters:
        execute('INSERT INTO chapters (work_id, chapter_no, title, content, word_count) VALUES (%s, %s, %s, %s, %s)',
                (work_id, ch['chapter_no'], ch['title'], ch['content'], ch.get('word_count', 0)))

    total_wc = query('SELECT COALESCE(SUM(word_count), 0) as wc FROM chapters WHERE work_id = %s', (work_id,), one=True)['wc']
    execute('UPDATE works SET word_count = %s WHERE work_id = %s', (total_wc, work_id))

    return ok(msg='已回退到指定版本')


@works_bp.put('/<int:work_id>/status')
@login_required
def toggle_status(work_id):
    work = query('SELECT * FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)

    data = request.get_json()
    new_status = data.get('status', 'draft')
    if new_status not in ('draft', 'published', 'private'):
        return fail('无效的状态')

    execute('UPDATE works SET status = %s WHERE work_id = %s', (new_status, work_id))
    return ok({'status': new_status}, msg='状态已更新')
