"""F2：灵感收藏端点测试（无需真实 AI）。"""
from database.db import execute


def _seed_poem():
    return execute(
        'INSERT INTO poems (title, dynasty, author, content, category) '
        'VALUES (%s, %s, %s, %s, %s)',
        ('静夜思', '唐', '李白', '床前明月光，疑是地上霜。', '咏怀'),
    )


def _seed_material():
    return execute(
        'INSERT INTO materials (title, content, category) VALUES (%s, %s, %s)',
        ('雨夜', '雨打芭蕉，声声入耳。', '景物描写'),
    )


def test_favorite_lifecycle(auth_client):
    poem_id = _seed_poem()
    mat_id = _seed_material()
    # 收藏诗词
    r = auth_client.post('/api/inspire/favorites', json={'item_type': 'poem', 'ref_id': poem_id})
    assert r.get_json()['code'] == 0
    # 重复收藏幂等
    auth_client.post('/api/inspire/favorites', json={'item_type': 'poem', 'ref_id': poem_id})
    # 收藏素材
    auth_client.post('/api/inspire/favorites', json={'item_type': 'material', 'ref_id': mat_id})
    # 列表：2 条，含快照
    items = auth_client.get('/api/inspire/favorites').get_json()['data']['items']
    assert len(items) == 2
    by_type = {i['item_type']: i for i in items}
    assert by_type['poem']['title'] == '静夜思'
    assert '床前明月光' in by_type['poem']['content']
    assert by_type['material']['title'] == '雨夜'
    # 取消收藏
    r = auth_client.delete(f'/api/inspire/favorites/poem/{poem_id}')
    assert r.get_json()['code'] == 0
    items = auth_client.get('/api/inspire/favorites').get_json()['data']['items']
    assert len(items) == 1
    assert items[0]['item_type'] == 'material'


def test_favorite_validation_and_notfound(auth_client):
    assert auth_client.post('/api/inspire/favorites', json={'item_type': 'novel', 'ref_id': 1}).get_json()['code'] != 0
    assert auth_client.post('/api/inspire/favorites', json={'item_type': 'poem', 'ref_id': 999999}).get_json()['code'] == 404
    assert auth_client.delete('/api/inspire/favorites/bad/1').get_json()['code'] != 0


def test_favorites_are_private(auth_client, app):
    poem_id = _seed_poem()
    auth_client.post('/api/inspire/favorites', json={'item_type': 'poem', 'ref_id': poem_id})
    other = app.test_client()
    other.post('/api/auth/register', json={'username': 'fav_other', 'password': 'test123456'})
    other.post('/api/auth/login', json={'username': 'fav_other', 'password': 'test123456'})
    items = other.get('/api/inspire/favorites').get_json()['data']['items']
    assert items == []
