"""P6-C3：作品角色关系图——手动维护的有向边（谁 与 谁 是什么关系）。

仅本人作品可读写；表 work_relations。提供 列表/新增/删除，删除/更新按 relation_id。
"""
from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, login_required

relation_bp = Blueprint('relations', __name__)

_MAX_NODES = 60  # 单作品关系边上限，防滥用


def _own_work(work_id):
    return query(
        'SELECT work_id FROM works WHERE work_id = %s AND user_id = %s',
        (work_id, session['user_id']), one=True,
    )


@relation_bp.get('/<int:work_id>')
@login_required
def list_relations(work_id):
    if not _own_work(work_id):
        return fail('作品不存在', code=404)
    rows = query(
        'SELECT relation_id, source, relation, target FROM work_relations '
        'WHERE work_id = %s ORDER BY relation_id', (work_id,))
    return ok({'items': rows})


@relation_bp.post('/<int:work_id>')
@login_required
def add_relation(work_id):
    if not _own_work(work_id):
        return fail('作品不存在', code=404)
    data = request.get_json() or {}
    source = (data.get('source') or '').strip()
    relation = (data.get('relation') or '').strip()
    target = (data.get('target') or '').strip()
    if not source or not relation or not target:
        return fail('需要填写 角色 A、关系、角色 B')
    if not all(len(x) <= 30 for x in (source, relation, target)):
        return fail('角色名与关系描述过长（各不超过 30 字）')

    count = query('SELECT COUNT(*) AS n FROM work_relations WHERE work_id = %s', (work_id,), one=True)['n']
    if count >= _MAX_NODES:
        return fail('关系边已达上限，请先删除一些')

    rid = execute(
        'INSERT INTO work_relations (work_id, source, relation, target) VALUES (%s, %s, %s, %s)',
        (work_id, source, relation, target),
    )
    return ok({'relation_id': rid}, msg='关系已添加')


@relation_bp.delete('/<int:work_id>/<int:relation_id>')
@login_required
def delete_relation(work_id, relation_id):
    row = query(
        'SELECT r.relation_id FROM work_relations r JOIN works w ON r.work_id = w.work_id '
        'WHERE r.relation_id = %s AND r.work_id = %s AND w.user_id = %s',
        (relation_id, work_id, session['user_id']), one=True,
    )
    if not row:
        return fail('关系不存在', code=404)
    execute('DELETE FROM work_relations WHERE relation_id = %s', (relation_id,))
    return ok(msg='关系已删除')