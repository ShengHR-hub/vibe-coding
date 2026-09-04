"""P4：作品立项计划（book_plans）——蓝图字段 + 大纲树(outline_json)，仅本人作品可读写。"""
import json
from flask import Blueprint, request, session
from database.db import query, execute
from utils.helpers import ok, fail, login_required, _fmt

plan_bp = Blueprint('plan', __name__)

_OUTLINE_MAX = 200 * 1024  # 大纲树 JSON 上限 200KB
_STAGES = ('plan', 'write', 'review', 'done')


def _own_work(work_id):
    return query(
        'SELECT work_id FROM works WHERE work_id = %s AND user_id = %s',
        (work_id, session['user_id']), one=True,
    )


@plan_bp.get('/<int:work_id>')
@login_required
def get_plan(work_id):
    if not _own_work(work_id):
        return fail('作品不存在', code=404)
    row = query('SELECT * FROM book_plans WHERE work_id = %s', (work_id,), one=True)
    if not row:
        return ok({'plan': None})
    plan = {
        'work_id': row['work_id'],
        'logline': row['logline'],
        'audience': row['audience'],
        'target_words': row['target_words'],
        'deadline': _fmt(row.get('deadline')),
        'stage': row['stage'],
        'outline': json.loads(row['outline_json']) if row.get('outline_json') else [],
        'updated_at': _fmt(row.get('updated_at')),
    }
    return ok({'plan': plan})


@plan_bp.put('/<int:work_id>')
@login_required
def upsert_plan(work_id):
    if not _own_work(work_id):
        return fail('作品不存在', code=404)
    data = request.get_json() or {}
    logline = (data.get('logline') or '').strip()[:1000]
    audience = (data.get('audience') or '').strip()[:500]
    try:
        target_words = int(data.get('target_words') or 0)
        if target_words < 0 or target_words > 2_000_000:
            raise ValueError
    except (TypeError, ValueError):
        return fail('目标字数无效')
    deadline = data.get('deadline') or None
    stage = (data.get('stage') or 'plan').strip()
    if stage not in _STAGES:
        return fail('无效的阶段')
    outline = data.get('outline')
    outline_json = None
    if outline is not None:
        try:
            text = json.dumps(outline, ensure_ascii=False)
        except (TypeError, ValueError):
            return fail('大纲数据格式错误')
        if len(text) > _OUTLINE_MAX:
            return fail('大纲过大')
        outline_json = text

    exists = query('SELECT plan_id FROM book_plans WHERE work_id = %s', (work_id,), one=True)
    if exists:
        execute(
            'UPDATE book_plans SET logline=%s, audience=%s, target_words=%s, deadline=%s, '
            'stage=%s, outline_json=COALESCE(%s, outline_json) WHERE work_id=%s',
            (logline, audience, target_words, deadline, stage, outline_json, work_id),
        )
    else:
        execute(
            'INSERT INTO book_plans (work_id, logline, audience, target_words, deadline, stage, outline_json) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (work_id, logline, audience, target_words, deadline, stage, outline_json),
        )
    return ok(msg='计划已保存')


@plan_bp.post('/<int:work_id>/stage')
@login_required
def set_stage(work_id):
    if not _own_work(work_id):
        return fail('作品不存在', code=404)
    data = request.get_json() or {}
    stage = (data.get('stage') or '').strip()
    if stage not in _STAGES:
        return fail('无效的阶段')
    execute(
        'INSERT INTO book_plans (work_id, logline, audience, target_words, stage, outline_json) '
        'VALUES (%s, \'\', \'\', 0, %s, NULL) '
        'ON DUPLICATE KEY UPDATE stage = %s',
        (work_id, stage, stage),
    )
    return ok({'stage': stage}, msg='阶段已更新')
