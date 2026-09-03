"""W2b：作品设定记忆 work_lore CRUD / 越权 / 去重 / 续写注入（stub 掉真实 AI）。"""
import pytest

from routes import write as write_mod


def _create_work(client, title='设定测试作'):
    res = client.post('/api/works', json={
        'title': title, 'type': 'novel', 'summary': '摘要', 'content': '正文。',
    })
    return res.get_json()['data']['work_id']


def _login_other(app, username='lore_other'):
    c = app.test_client()
    c.post('/api/auth/register', json={'username': username, 'password': 'test123456'})
    c.post('/api/auth/login', json={'username': username, 'password': 'test123456'})
    return c


def test_lore_crud_roundtrip(auth_client):
    work_id = _create_work(auth_client)
    # 创建两条
    r = auth_client.post(f'/api/works/{work_id}/lore', json={'title': '世界观', 'content': '蒸汽朋克大陆，魔法被禁止。'})
    assert r.get_json()['code'] == 0
    r2 = auth_client.post(f'/api/works/{work_id}/lore', json={'title': '主角能力', 'content': '能读取金属记忆。'})
    lore_id = r2.get_json()['data']['lore_id']
    # 列表
    items = auth_client.get(f'/api/works/{work_id}/lore').get_json()['data']['items']
    assert len(items) == 2
    # 更新
    r = auth_client.put(f'/api/works/{work_id}/lore/{lore_id}', json={'title': '主角能力', 'content': '能读取金属与纸张的记忆。'})
    assert r.get_json()['code'] == 0
    # 删除
    r = auth_client.delete(f'/api/works/{work_id}/lore/{lore_id}')
    assert r.get_json()['code'] == 0
    items = auth_client.get(f'/api/works/{work_id}/lore').get_json()['data']['items']
    assert len(items) == 1


def test_lore_duplicate_title_rejected(auth_client):
    work_id = _create_work(auth_client)
    auth_client.post(f'/api/works/{work_id}/lore', json={'title': '同名', 'content': '一'})
    r = auth_client.post(f'/api/works/{work_id}/lore', json={'title': '同名', 'content': '二'})
    assert r.get_json()['code'] != 0
    assert '同名' in r.get_json()['msg']


def test_lore_validation(auth_client):
    work_id = _create_work(auth_client)
    assert auth_client.post(f'/api/works/{work_id}/lore', json={'title': '', 'content': 'x'}).get_json()['code'] != 0
    assert auth_client.post(f'/api/works/{work_id}/lore', json={'title': 't', 'content': ''}).get_json()['code'] != 0
    assert auth_client.post(f'/api/works/{work_id}/lore', json={'title': 't' * 101, 'content': 'x'}).get_json()['code'] != 0


def test_lore_foreign_user_forbidden(auth_client, app):
    work_id = _create_work(auth_client)
    other = _login_other(app)
    assert other.get(f'/api/works/{work_id}/lore').get_json()['code'] == 404
    assert other.post(f'/api/works/{work_id}/lore', json={'title': 'x', 'content': 'y'}).get_json()['code'] == 404


@pytest.fixture
def capture_stream(monkeypatch):
    captured = {}

    def fake_stream(messages, temperature=0.7, max_tokens=2048):
        captured['messages'] = messages
        yield '续写。'

    monkeypatch.setattr(write_mod, 'chat_completion_stream', fake_stream)
    monkeypatch.setattr(write_mod, 'log_ai_call', lambda *a, **k: None)
    return captured


def test_lore_injected_into_continue(auth_client, capture_stream):
    from database.db import execute
    res = auth_client.post('/api/works', json={'title': '设定注入作', 'type': 'novel', 'content': '正文。'})
    work_id = res.get_json()['data']['work_id']
    execute('INSERT INTO chapters (work_id, chapter_no, title, content, word_count) VALUES (%s, 1, %s, %s, %s)',
            (work_id, '第一章', '内容', 2))
    auth_client.post(f'/api/works/{work_id}/lore', json={'title': '禁地规则', 'content': '北境禁地不可踏入。'})
    r = auth_client.post('/api/write/continue', json={'content': '他走向北方，', 'work_id': work_id})
    assert r.status_code == 200
    user_msg = capture_stream['messages'][-1]['content']
    assert '作品设定' in user_msg
    assert '北境禁地不可踏入' in user_msg
