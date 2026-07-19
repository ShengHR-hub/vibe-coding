from flask import Blueprint, request, session
from database.db import query, execute, execute_many
from utils.helpers import ok, fail, login_required, _fmt

serialize_bp = Blueprint('serialize', __name__)


@serialize_bp.get('/<int:work_id>/volumes')
@login_required
def list_volumes(work_id):
    work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)

    volumes = query('SELECT * FROM volumes WHERE work_id = %s ORDER BY volume_no', (work_id,))
    for v in volumes:
        # 每卷的章节信息
        chapters = query(
            'SELECT chapter_id, chapter_no, title, word_count FROM chapters WHERE work_id = %s AND volume_id = %s ORDER BY chapter_no',
            (work_id, v['volume_id'])
        )
        v['chapters'] = chapters
        v['chapter_count'] = len(chapters)
        v['total_words'] = sum(c['word_count'] for c in chapters)

    # 未分卷的章节
    unassigned = query(
        'SELECT chapter_id, chapter_no, title, word_count FROM chapters WHERE work_id = %s AND volume_id IS NULL ORDER BY chapter_no',
        (work_id,)
    )

    # 连载状态
    w = query('SELECT serialization_status FROM works WHERE work_id = %s', (work_id,), one=True)

    return ok({
        'volumes': volumes,
        'unassigned': unassigned,
        'serialization_status': w['serialization_status'] if w else 'serializing',
    })


@serialize_bp.post('/<int:work_id>/volumes')
@login_required
def create_volume(work_id):
    work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)

    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    summary = (data.get('summary') or '').strip()

    max_no = query('SELECT COALESCE(MAX(volume_no), 0) as m FROM volumes WHERE work_id = %s', (work_id,), one=True)['m']
    volume_no = max_no + 1
    if not title:
        from routes.works import _cn
        title = f'第{_cn(volume_no)}卷'

    volume_id = execute(
        'INSERT INTO volumes (work_id, volume_no, title, summary) VALUES (%s, %s, %s, %s)',
        (work_id, volume_no, title, summary)
    )
    return ok({'volume_id': volume_id, 'volume_no': volume_no, 'title': title}, msg='卷已创建')


@serialize_bp.put('/<int:work_id>/volumes/<int:vol_id>')
@login_required
def update_volume(work_id, vol_id):
    work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)

    vol = query('SELECT * FROM volumes WHERE volume_id = %s AND work_id = %s', (vol_id, work_id), one=True)
    if not vol:
        return fail('卷不存在', code=404)

    data = request.get_json() or {}
    title = data.get('title', vol['title'])
    summary = data.get('summary', vol['summary'])
    execute('UPDATE volumes SET title = %s, summary = %s WHERE volume_id = %s', (title, summary, vol_id))
    return ok(msg='卷已更新')


@serialize_bp.delete('/<int:work_id>/volumes/<int:vol_id>')
@login_required
def delete_volume(work_id, vol_id):
    work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)

    vol = query('SELECT * FROM volumes WHERE volume_id = %s AND work_id = %s', (vol_id, work_id), one=True)
    if not vol:
        return fail('卷不存在', code=404)

    # 把该卷的章节设为未分卷
    execute('UPDATE chapters SET volume_id = NULL WHERE volume_id = %s AND work_id = %s', (vol_id, work_id))
    execute('DELETE FROM volumes WHERE volume_id = %s', (vol_id,))

    # 重排卷号（批量更新）
    remaining = query('SELECT volume_id FROM volumes WHERE work_id = %s ORDER BY volume_no', (work_id,))
    if remaining:
        ops = [('UPDATE volumes SET volume_no = %s WHERE volume_id = %s', (i, v['volume_id']))
               for i, v in enumerate(remaining, 1)]
        execute_many(ops)

    return ok(msg='卷已删除')


@serialize_bp.put('/<int:work_id>/chapters/<int:ch_id>/volume')
@login_required
def assign_chapter_to_volume(work_id, ch_id):
    work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)

    ch = query('SELECT chapter_id FROM chapters WHERE chapter_id = %s AND work_id = %s', (ch_id, work_id), one=True)
    if not ch:
        return fail('章节不存在', code=404)

    data = request.get_json() or {}
    volume_id = data.get('volume_id')  # null 表示移出卷

    if volume_id:
        vol = query('SELECT volume_id FROM volumes WHERE volume_id = %s AND work_id = %s', (volume_id, work_id), one=True)
        if not vol:
            return fail('卷不存在', code=404)

    execute('UPDATE chapters SET volume_id = %s WHERE chapter_id = %s', (volume_id, ch_id))
    return ok(msg='章节已分配到卷')


@serialize_bp.put('/<int:work_id>/status')
@login_required
def update_serialization_status(work_id):
    work = query('SELECT work_id FROM works WHERE work_id = %s AND user_id = %s', (work_id, session['user_id']), one=True)
    if not work:
        return fail('作品不存在', code=404)

    data = request.get_json() or {}
    status = data.get('serialization_status', 'serializing')
    if status not in ('serializing', 'completed', 'paused'):
        return fail('无效的状态')

    execute('UPDATE works SET serialization_status = %s WHERE work_id = %s', (status, work_id))
    return ok({'serialization_status': status}, msg='连载状态已更新')
