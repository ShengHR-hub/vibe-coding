from flask import Blueprint, request, session, Response
import re, json, urllib.parse
from pymysql.err import IntegrityError
from database.db import query, execute, execute_many
from utils.helpers import ok, fail, login_required, _fmt, check_achievements

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

    check_achievements(user_id)
    return ok({'work_id': work_id}, msg='作品创建成功')


@works_bp.post('/save')
@login_required
def save_work():
    """保存作品（创建或更新），支持章节内容更新"""
    data = request.get_json()
    user_id = session['user_id']
    work_id = data.get('work_id')
    title = (data.get('title') or '未命名作品').strip()
    content = (data.get('content') or '').strip()
    chapter_id = data.get('chapter_id')
    chapter_title = (data.get('chapter_title') or '').strip()

    if work_id:
        # 更新现有作品
        work = query('SELECT * FROM works WHERE work_id = %s AND user_id = %s', (work_id, user_id), one=True)
        if not work:
            return fail('作品不存在', code=404)

        # 更新作品标题
        execute('UPDATE works SET title = %s WHERE work_id = %s', (title, work_id))

        # 更新章节内容
        if chapter_id:
            wc = len(re.sub(r'\s', '', content)) if content else 0
            execute('UPDATE chapters SET content = %s, title = %s, word_count = %s WHERE chapter_id = %s AND work_id = %s',
                    (content, chapter_title, wc, chapter_id, work_id))
            # 更新总字数
            total_wc = query('SELECT COALESCE(SUM(word_count), 0) as wc FROM chapters WHERE work_id = %s', (work_id,), one=True)['wc']
            execute('UPDATE works SET word_count = %s WHERE work_id = %s', (total_wc, work_id))
        elif content:
            # 没有 chapter_id 时，更新第一个章节
            first_ch = query('SELECT chapter_id FROM chapters WHERE work_id = %s ORDER BY chapter_no LIMIT 1', (work_id,), one=True)
            if first_ch:
                wc = len(re.sub(r'\s', '', content))
                execute('UPDATE chapters SET content = %s, word_count = %s WHERE chapter_id = %s',
                        (content, wc, first_ch['chapter_id']))
                total_wc = query('SELECT COALESCE(SUM(word_count), 0) as wc FROM chapters WHERE work_id = %s', (work_id,), one=True)['wc']
                execute('UPDATE works SET word_count = %s WHERE work_id = %s', (total_wc, work_id))

        check_achievements(user_id)
        return ok({'work_id': work_id}, msg='保存成功')
    else:
        # 创建新作品
        work_id = execute(
            'INSERT INTO works (user_id, title, type, summary, tags) VALUES (%s, %s, %s, %s, %s)',
            (user_id, title, 'novel', '', '')
        )
        wc = len(re.sub(r'\s', '', content)) if content else 0
        execute(
            'INSERT INTO chapters (work_id, chapter_no, title, content, word_count) VALUES (%s, 1, %s, %s, %s)',
            (work_id, '第一章', content, wc)
        )
        execute('UPDATE works SET word_count = %s WHERE work_id = %s', (wc, work_id))
        check_achievements(user_id)
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


TYPE_NAMES = {'novel': '小说', 'poetry': '诗歌', 'essay': '散文', 'script': '剧本'}


@works_bp.get('/<int:work_id>/export')
@login_required
def export_work(work_id):
    work = query(
        'SELECT w.*, u.username FROM works w JOIN users u ON w.user_id = u.user_id WHERE w.work_id = %s',
        (work_id,), one=True
    )
    if not work:
        return fail('作品不存在', code=404)

    # Allow owner to export any status, others only published
    is_owner = 'user_id' in session and session['user_id'] == work['user_id']
    if work['status'] != 'published' and not is_owner:
        return fail('作品不存在', code=404)

    chapters = query(
        'SELECT title, content, chapter_no FROM chapters WHERE work_id = %s ORDER BY chapter_no',
        (work_id,)
    )

    type_name = TYPE_NAMES.get(work['type'], work['type'])
    tags = work.get('tags', '')

    lines = [
        f"# {work['title']}",
        f"作者：{work['username']}",
        f"类型：{type_name}",
    ]
    if tags:
        lines.append(f"标签：{tags}")
    if work.get('summary'):
        lines.append(f"简介：{work['summary']}")
    lines.append('')
    lines.append('—' * 20)
    lines.append('')

    for ch in chapters:
        ch_title = ch['title'] or f"第{ch['chapter_no']}章"
        lines.append(f"## {ch_title}")
        lines.append('')
        if ch['content']:
            lines.append(ch['content'])
        lines.append('')
        lines.append('—' * 20)
        lines.append('')

    content = '\n'.join(lines)
    filename = f"{work['title']}.txt"
    encoded = urllib.parse.quote(filename)

    return Response(
        content,
        mimetype='text/plain; charset=utf-8',
        headers={
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded}",
            'Content-Type': 'text/plain; charset=utf-8',
        }
    )


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

    check_achievements(session['user_id'])
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

    # Build transaction operations: save snapshot + delete old chapters + insert restored chapters
    ops = [
        ('INSERT INTO work_versions (work_id, content_json, word_count) VALUES (%s, %s, %s)',
         (work_id, current_snapshot, work['word_count'])),
        ('DELETE FROM chapters WHERE work_id = %s', (work_id,)),
    ]
    for ch in old_chapters:
        ops.append(
            ('INSERT INTO chapters (work_id, chapter_no, title, content, word_count) VALUES (%s, %s, %s, %s, %s)',
             (work_id, ch['chapter_no'], ch['title'], ch['content'], ch.get('word_count', 0)))
        )

    total_wc = sum(ch.get('word_count', 0) or 0 for ch in old_chapters)
    ops.append(('UPDATE works SET word_count = %s WHERE work_id = %s', (total_wc, work_id)))

    execute_many(ops)

    return ok(msg='已回退到指定版本')


@works_bp.post('/<int:work_id>/chapters')
@login_required
def create_chapter(work_id):
    work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)

    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    max_no = query('SELECT COALESCE(MAX(chapter_no), 0) as m FROM chapters WHERE work_id = %s', (work_id,), one=True)['m']
    chapter_no = max_no + 1
    if not title:
        title = f'第{_cn(chapter_no)}章'

    chapter_id = execute(
        'INSERT INTO chapters (work_id, chapter_no, title, content, word_count) VALUES (%s, %s, %s, %s, 0)',
        (work_id, chapter_no, title, '')
    )
    return ok({'chapter_id': chapter_id, 'chapter_no': chapter_no, 'title': title}, msg='章节已创建')


def _cn(n):
    """数字转中文：1→一，2→二...支持到9999"""
    cn = '零一二三四五六七八九十'
    if 1 <= n <= 10:
        return cn[n]
    if 11 <= n <= 19:
        return '十' + cn[n - 10]
    if 20 <= n <= 99:
        tens, ones = divmod(n, 10)
        result = cn[tens] + '十'
        if ones:
            result += cn[ones]
        return result
    if 100 <= n <= 999:
        hundreds, rest = divmod(n, 100)
        result = cn[hundreds] + '百'
        if rest >= 10:
            tens, ones = divmod(rest, 10)
            result += cn[tens] + '十'
            if ones:
                result += cn[ones]
        elif rest > 0:
            result += '零' + cn[rest]
        return result
    if 1000 <= n <= 9999:
        thousands, rest = divmod(n, 1000)
        result = cn[thousands] + '千'
        if rest >= 100:
            result += _cn(rest)
        elif rest > 0:
            result += '零' + _cn(rest)
        return result
    return str(n)


@works_bp.delete('/<int:work_id>/chapters/<int:chapter_id>')
@login_required
def delete_chapter(work_id, chapter_id):
    work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)

    ch = query('SELECT chapter_id FROM chapters WHERE chapter_id = %s AND work_id = %s', (chapter_id, work_id), one=True)
    if not ch:
        return fail('章节不存在', code=404)

    execute('DELETE FROM chapters WHERE chapter_id = %s', (chapter_id,))

    # 重排 chapter_no（批量更新）
    remaining = query('SELECT chapter_id FROM chapters WHERE work_id = %s ORDER BY chapter_no', (work_id,))
    if remaining:
        ops = []
        for i, r in enumerate(remaining, 1):
            ops.append(('UPDATE chapters SET chapter_no = %s WHERE chapter_id = %s', (i, r['chapter_id'])))
        execute_many(ops)

    # 更新总字数
    total_wc = query('SELECT COALESCE(SUM(word_count), 0) as wc FROM chapters WHERE work_id = %s', (work_id,), one=True)['wc']
    execute('UPDATE works SET word_count = %s WHERE work_id = %s', (total_wc, work_id))

    return ok(msg='章节已删除')


@works_bp.put('/<int:work_id>/chapters/reorder')
@login_required
def reorder_chapters(work_id):
    work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)

    data = request.get_json()
    order = data.get('order') or []
    if not order:
        return fail('请提供排序列表')
    if len(order) > 200:
        return fail('排序列表过长')

    # 验证所有 chapter_id 属于该作品
    valid_ids = {r['chapter_id'] for r in query(
        'SELECT chapter_id FROM chapters WHERE work_id = %s', (work_id,))}
    if not all(cid in valid_ids for cid in order):
        return fail('包含无效的章节ID')

    for i, ch_id in enumerate(order, 1):
        execute('UPDATE chapters SET chapter_no = %s WHERE chapter_id = %s AND work_id = %s', (i, ch_id, work_id))

    return ok(msg='排序已更新')


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
    check_achievements(session['user_id'])
    return ok({'status': new_status}, msg='状态已更新')


# ---------------------------------------------------------------------------
# W2b：作品设定记忆 work_lore（轻量 lorebook，仅本人作品）
# ---------------------------------------------------------------------------

@works_bp.get('/<int:work_id>/lore')
@login_required
def list_lore(work_id):
    work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s',
                 (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)
    rows = query('SELECT lore_id, title, content, updated_at FROM work_lore WHERE work_id = %s ORDER BY lore_id', (work_id,))
    for r in rows:
        r['updated_at'] = _fmt(r.get('updated_at'))
    return ok({'items': rows})


@works_bp.post('/<int:work_id>/lore')
@login_required
def create_lore(work_id):
    work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s',
                 (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    if not title:
        return fail('设定标题不能为空')
    if len(title) > 100:
        return fail('设定标题过长，最多100字')
    if not content:
        return fail('设定内容不能为空')
    if len(content) > 10000:
        return fail('设定内容过长，最多10000字')
    try:
        lore_id = execute(
            'INSERT INTO work_lore (work_id, title, content) VALUES (%s, %s, %s)',
            (work_id, title, content),
        )
    except IntegrityError:
        return fail('同名设定已存在，请修改标题')
    return ok({'lore_id': lore_id}, msg='设定已保存')


@works_bp.put('/<int:work_id>/lore/<int:lore_id>')
@login_required
def update_lore(work_id, lore_id):
    row = query(
        'SELECT l.lore_id FROM work_lore l JOIN works w ON l.work_id = w.work_id '
        'WHERE l.lore_id = %s AND l.work_id = %s AND w.user_id = %s',
        (lore_id, work_id, session['user_id']), one=True,
    )
    if not row:
        return fail('设定不存在', code=404)
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    if not title:
        return fail('设定标题不能为空')
    if len(title) > 100:
        return fail('设定标题过长，最多100字')
    if not content:
        return fail('设定内容不能为空')
    if len(content) > 10000:
        return fail('设定内容过长，最多10000字')
    try:
        execute('UPDATE work_lore SET title = %s, content = %s WHERE lore_id = %s AND work_id = %s',
                (title, content, lore_id, work_id))
    except IntegrityError:
        return fail('同名设定已存在，请修改标题')
    return ok(msg='设定已更新')


@works_bp.delete('/<int:work_id>/lore/<int:lore_id>')
@login_required
def delete_lore(work_id, lore_id):
    row = query(
        'SELECT l.lore_id FROM work_lore l JOIN works w ON l.work_id = w.work_id '
        'WHERE l.lore_id = %s AND l.work_id = %s AND w.user_id = %s',
        (lore_id, work_id, session['user_id']), one=True,
    )
    if not row:
        return fail('设定不存在', code=404)
    execute('DELETE FROM work_lore WHERE lore_id = %s', (lore_id,))
    return ok(msg='设定已删除')
