"""闪念便签（P6-A）：用户随时记录灵感片段，仅本人可读写。"""
from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, login_required, _fmt

notes_bp = Blueprint('notes', __name__)

_MAX_LEN = 2000


def _get_own_note(note_id):
    """取本人便签，不存在或非本人返回 None（防越权统一走 404）。"""
    return query(
        'SELECT note_id FROM user_notes WHERE note_id = %s AND user_id = %s',
        (note_id, session['user_id']), one=True)


@notes_bp.get('')
@login_required
def list_notes():
    rows = query(
        'SELECT note_id, content, created_at, updated_at FROM user_notes '
        'WHERE user_id = %s ORDER BY updated_at DESC',
        (session['user_id'],),
    )
    items = [{
        'note_id': r['note_id'],
        'content': r['content'],
        'created_at': _fmt(r['created_at']),
        'updated_at': _fmt(r['updated_at']),
    } for r in rows]
    return ok({'items': items})


@notes_bp.post('')
@login_required
def create_note():
    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    if not content:
        return fail('内容不能为空')
    if len(content) > _MAX_LEN:
        return fail(f'内容过长（最多 {_MAX_LEN} 字）')
    note_id = execute(
        'INSERT INTO user_notes (user_id, content) VALUES (%s, %s)',
        (session['user_id'], content),
    )
    return ok({'note_id': note_id}, msg='已保存便签')


@notes_bp.put('/<int:note_id>')
@login_required
def update_note(note_id):
    if not _get_own_note(note_id):
        return fail('便签不存在', code=404)
    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    if not content:
        return fail('内容不能为空')
    if len(content) > _MAX_LEN:
        return fail(f'内容过长（最多 {_MAX_LEN} 字）')
    execute(
        'UPDATE user_notes SET content = %s WHERE note_id = %s AND user_id = %s',
        (content, note_id, session['user_id']),
    )
    return ok(msg='已更新便签')


@notes_bp.delete('/<int:note_id>')
@login_required
def delete_note(note_id):
    if not _get_own_note(note_id):
        return fail('便签不存在', code=404)
    execute('DELETE FROM user_notes WHERE note_id = %s AND user_id = %s',
            (note_id, session['user_id']))
    return ok(msg='已删除便签')