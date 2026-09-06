"""闪念便签端点测试（P6-A）：登录/CRUD/越权/长度，走 inkstone_test，零 AI token。"""
import pytest


def _mk_notes(client, *contents):
    ids = []
    for c in contents:
        r = client.post('/api/notes', json={'content': c})
        assert r.get_json()['code'] == 0
        ids.append(r.get_json()['data']['note_id'])
    return ids


def test_notes_requires_login(client):
    r = client.get('/api/notes')
    assert r.get_json()['code'] == 401


def test_notes_create_and_list(auth_client):
    note_id = _mk_notes(auth_client, '主角左手的伤疤是个伏笔')[0]
    r = auth_client.get('/api/notes')
    assert r.get_json()['code'] == 0
    items = r.get_json()['data']['items']
    assert len(items) == 1
    assert items[0]['note_id'] == note_id
    assert items[0]['content'] == '主角左手的伤疤是个伏笔'


def test_notes_order_desc(auth_client):
    _mk_notes(auth_client, '第一条', '第二条')
    r = auth_client.get('/api/notes')
    items = r.get_json()['data']['items']
    assert len(items) == 2
    # 列表按 updated_at DESC（同一秒内并列时无稳定序），只验证两条都在
    contents = {i['content'] for i in items}
    assert contents == {'第一条', '第二条'}


def test_notes_update_own(auth_client):
    note_id = _mk_notes(auth_client, '旧想法')[0]
    r = auth_client.put(f'/api/notes/{note_id}', json={'content': '新想法'})
    assert r.get_json()['code'] == 0
    items = auth_client.get('/api/notes').get_json()['data']['items']
    assert items[0]['content'] == '新想法'


def test_notes_delete_own(auth_client):
    note_id = _mk_notes(auth_client, '要删的')[0]
    r = auth_client.delete(f'/api/notes/{note_id}')
    assert r.get_json()['code'] == 0
    items = auth_client.get('/api/notes').get_json()['data']['items']
    assert items == []


def test_notes_cannot_touch_others(auth_client, client):
    note_id = _mk_notes(auth_client, '别人的便签')[0]
    # 第二个用户登录
    client.post('/api/auth/register', json={'username': 'other', 'password': 'test123456'})
    client.post('/api/auth/login', json={'username': 'other', 'password': 'test123456'})
    assert client.put(f'/api/notes/{note_id}', json={'content': '篡改'}).get_json()['code'] == 404
    assert client.delete(f'/api/notes/{note_id}').get_json()['code'] == 404


def test_notes_validation(auth_client):
    assert auth_client.post('/api/notes', json={'content': ''}).get_json()['code'] != 0
    assert auth_client.post('/api/notes', json={'content': '   '}).get_json()['code'] != 0
    long_text = '字' * 2001
    assert auth_client.post('/api/notes', json={'content': long_text}).get_json()['code'] != 0


# ---------- P6-B2：note_kind（note/mainline） ----------

def test_notes_kind_default_is_note(auth_client):
    note_id = _mk_notes(auth_client, '普通便签')[0]
    items = auth_client.get('/api/notes').get_json()['data']['items']
    it = next(i for i in items if i['note_id'] == note_id)
    assert it['kind'] == 'note'


def test_notes_create_mainline_kind(auth_client):
    r = auth_client.post('/api/notes', json={'content': '主线：少年追光，破除枷锁', 'kind': 'mainline'})
    assert r.get_json()['code'] == 0
    items = auth_client.get('/api/notes').get_json()['data']['items']
    it = next(i for i in items if i['note_id'] == r.get_json()['data']['note_id'])
    assert it['kind'] == 'mainline'
    assert it['content'] == '主线：少年追光，破除枷锁'


def test_notes_rejects_bad_kind(auth_client):
    r = auth_client.post('/api/notes', json={'content': 'x', 'kind': 'hack'})
    assert r.get_json()['code'] != 0


def test_notes_kind_kept_on_update(auth_client):
    note_id = _mk_notes(auth_client, '初始普通')[0]
    auth_client.put(f'/api/notes/{note_id}', json={'content': '改成主线'})
    items = auth_client.get('/api/notes').get_json()['data']['items']
    it = next(i for i in items if i['note_id'] == note_id)
    assert it['content'] == '改成主线'
    assert it['kind'] == 'note'  # 更新不改变 kind