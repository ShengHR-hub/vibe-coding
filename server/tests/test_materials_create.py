"""F3：手动收录素材端点测试。"""
from database.db import query


def test_create_material_ok(auth_client):
    r = auth_client.post('/api/materials', json={
        'category': '名言金句', 'content': '少年与爱永不老去。',
    })
    data = r.get_json()
    assert data['code'] == 0
    assert data['data']['material_id'] > 0
    row = query('SELECT * FROM materials WHERE material_id = %s', (data['data']['material_id'],), one=True)
    assert row['content'] == '少年与爱永不老去。'
    assert row['category'] == '名言金句'
    assert row['title'] == '少年与爱永不老去。'
    assert row['source'] == 'user'


def test_create_material_validation_and_auth(app, auth_client):
    # 未登录 401
    guest = app.test_client()
    assert guest.post('/api/materials', json={'content': 'x'}).get_json()['code'] == 401
    # 空内容 / 超长内容 / 超长分类
    assert auth_client.post('/api/materials', json={'content': ''}).get_json()['code'] != 0
    assert auth_client.post('/api/materials', json={'content': '好' * 2001}).get_json()['code'] != 0
    assert auth_client.post('/api/materials', json={'category': '长' * 21, 'content': 'x'}).get_json()['code'] != 0
    # 分类缺省回退 '随想'
    r = auth_client.post('/api/materials', json={'content': '随手一句'})
    assert r.get_json()['code'] == 0
