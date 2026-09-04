"""P4：作品立项计划 book_plans 端点测试。"""
import json

from database.db import query


def _create_work(client, title='计划测试书'):
    res = client.post('/api/works', json={'title': title, 'type': 'novel', 'summary': 's', 'content': '正文。'})
    return res.get_json()['data']['work_id']


def test_plan_roundtrip(auth_client):
    work_id = _create_work(auth_client)
    # 无计划时返回 null
    assert auth_client.get(f'/api/plan/{work_id}').get_json()['data']['plan'] is None
    # 保存蓝图 + 大纲
    outline = [
        {'kind': 'part', 'title': '第一卷 故土', 'children': [
            {'kind': 'chapter', 'title': '第一章 归来', 'beats': '主角回到故乡，发现灯的秘密。', 'hook': '灯芯是谁留下的？'},
        ]},
    ]
    r = auth_client.put(f'/api/plan/{work_id}', json={
        'logline': '一个少年为解开祖屋灯的秘密踏上旅程。',
        'audience': '喜欢悬疑与家庭温情的读者',
        'target_words': 120000,
        'deadline': '2026-12-31',
        'stage': 'plan',
        'outline': outline,
    })
    assert r.get_json()['code'] == 0
    # 读取
    data = auth_client.get(f'/api/plan/{work_id}').get_json()['data']['plan']
    assert data['logline'].startswith('一个少年')
    assert data['target_words'] == 120000
    assert data['stage'] == 'plan'
    assert data['outline'][0]['title'] == '第一卷 故土'
    # stage 快捷更新
    r = auth_client.post(f'/api/plan/{work_id}/stage', json={'stage': 'write'})
    assert r.get_json()['code'] == 0
    assert auth_client.get(f'/api/plan/{work_id}').get_json()['data']['plan']['stage'] == 'write'
    # outline 不传则保留（COALESCE）
    auth_client.put(f'/api/plan/{work_id}', json={'logline': '改过的命题。'})
    data = auth_client.get(f'/api/plan/{work_id}').get_json()['data']['plan']
    assert data['logline'] == '改过的命题。'
    assert len(data['outline']) == 1


def test_plan_validation(auth_client):
    work_id = _create_work(auth_client)
    assert auth_client.put(f'/api/plan/{work_id}', json={'target_words': -5}).get_json()['code'] != 0
    assert auth_client.put(f'/api/plan/{work_id}', json={'stage': 'boom'}).get_json()['code'] != 0
    big = {'outline': ['x' * (210 * 1024)]}
    assert auth_client.put(f'/api/plan/{work_id}', json=big).get_json()['code'] != 0
    assert auth_client.post(f'/api/plan/{work_id}/stage', json={'stage': 'x'}).get_json()['code'] != 0


def test_plan_owner_only(auth_client, app):
    work_id = _create_work(auth_client)
    other = app.test_client()
    other.post('/api/auth/register', json={'username': 'plan_other', 'password': 'test123456'})
    other.post('/api/auth/login', json={'username': 'plan_other', 'password': 'test123456'})
    assert other.get(f'/api/plan/{work_id}').get_json()['code'] == 404
    assert other.put(f'/api/plan/{work_id}', json={'logline': 'x'}).get_json()['code'] == 404


def test_plan_cascade_delete(auth_client):
    work_id = _create_work(auth_client)
    auth_client.put(f'/api/plan/{work_id}', json={'logline': '将被删除'})
    assert query('SELECT COUNT(*) AS c FROM book_plans WHERE work_id = %s', (work_id,), one=True)['c'] == 1
    auth_client.delete(f'/api/works/{work_id}')
    assert query('SELECT COUNT(*) AS c FROM book_plans WHERE work_id = %s', (work_id,), one=True)['c'] == 0
