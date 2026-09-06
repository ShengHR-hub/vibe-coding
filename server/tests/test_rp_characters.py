"""P6-C2：角色卡 AI 生成 + 手改（复用 rp_characters）。

覆盖：generate 按灵感生成并入库、extract 既有保留、PUT 手改、权限隔离（非本人作品 404）。
AI 全部 stub，零 token 消耗。
"""
import json
import pytest

from routes import rp as rp_mod


@pytest.fixture
def stub_completion(monkeypatch):
    state = {'messages': None, 'result': None}

    def fake_completion(messages, temperature=0.7, max_tokens=1024):
        state['messages'] = messages
        if isinstance(state['result'], (dict, list)):
            return json.dumps(state['result'], ensure_ascii=False)
        return state['result'] or 'stub'

    monkeypatch.setattr(rp_mod, 'chat_completion', fake_completion)
    monkeypatch.setattr(rp_mod, 'chat_completion_stream', lambda *a, **k: (x for x in []))
    return state


def _make_second_user(app):
    """独立未登录客户端（避免与 auth_client 共用 session），注册第二个用户。"""
    c = app.test_client()
    c.post('/api/auth/register', json={'username': 'otheruser', 'password': 'test123456'})
    c.post('/api/auth/login', json={'username': 'otheruser', 'password': 'test123456'})
    return c


class TestGenerateCharacters:
    """P6-C2：按灵感生成角色卡"""

    def test_requires_login(self, app, auth_client, sample_work):
        anon = app.test_client()
        r = anon.post(f'/api/rp/{sample_work}/characters/generate', json={'inspiration': '仙侠世界'})
        assert r.get_json()['code'] == 401

    def test_requires_inspiration(self, auth_client, sample_work):
        r = auth_client.post(f'/api/rp/{sample_work}/characters/generate', json={})
        assert r.get_json()['code'] == 1
        assert '灵感' in r.get_json()['msg']

    def test_generate_creates_cards(self, auth_client, sample_work, stub_completion):
        stub_completion['result'] = [
            {'name': '林晚', 'description': '青衣女子', 'personality': '冷静果敢',
             'background': '出身剑阁', 'speaking_style': '话少'},
            {'name': '白泽', 'description': '白衣少年', 'personality': '开朗',
             'background': '市井出身', 'speaking_style': '爱开玩笑'},
        ]
        r = auth_client.post(f'/api/rp/{sample_work}/characters/generate',
                             json={'inspiration': '修仙少年入剑阁'})
        data = r.get_json()
        assert data['code'] == 0
        assert data['data']['count'] == 2

        # 已入库
        lst = auth_client.get(f'/api/rp/{sample_work}/characters').get_json()['data']['characters']
        assert len(lst) == 2
        names = {c['name'] for c in lst}
        assert names == {'林晚', '白泽'}
        by_name = {c['name']: c for c in lst}
        assert by_name['林晚']['personality'] == '冷静果敢'

    def test_generate_truncates_fields(self, auth_client, sample_work, stub_completion):
        stub_completion['result'] = [
            {'name': '名' * 30, 'description': '描' * 300, 'personality': '性' * 300,
             'background': '背' * 300, 'speaking_style': '说' * 300},
        ]
        auth_client.post(f'/api/rp/{sample_work}/characters/generate', json={'inspiration': '灵感'})
        lst = auth_client.get(f'/api/rp/{sample_work}/characters').get_json()['data']['characters']
        assert len(lst) == 1
        assert len(lst[0]['name']) <= 12
        assert len(lst[0]['description']) <= 150
        assert len(lst[0]['personality']) <= 150

    def test_generate_bad_json(self, auth_client, sample_work, stub_completion):
        stub_completion['result'] = '这不是JSON'
        r = auth_client.post(f'/api/rp/{sample_work}/characters/generate', json={'inspiration': '灵感'})
        data = r.get_json()
        assert data['code'] == 1
        assert '格式' in data['msg']

    def test_generate_other_users_work_404(self, app, auth_client, sample_work, stub_completion):
        stub_completion['result'] = [{'name': 'X', 'description': '', 'personality': '', 'background': '', 'speaking_style': ''}]
        other = _make_second_user(app)
        r = other.post(f'/api/rp/{sample_work}/characters/generate', json={'inspiration': '灵感'})
        assert r.get_json()['code'] == 404

    def test_generate_inspiration_too_long(self, auth_client, sample_work):
        r = auth_client.post(f'/api/rp/{sample_work}/characters/generate',
                             json={'inspiration': '长' * 8001})
        assert r.get_json()['code'] == 1


class TestUpdateCharacter:
    """P6-C2：手改角色卡"""

    def _seed_char(self, auth_client, work_id):
        r = auth_client.post(f'/api/rp/{work_id}/characters', json={
            'name': '初始名', 'description': '初始描述', 'personality': '初始性格',
            'background': '初始背景', 'speaking_style': '初始风格',
        })
        return r.get_json()['data']['char_id']

    def test_update_fields(self, auth_client, sample_work, stub_completion):
        cid = self._seed_char(auth_client, sample_work)
        r = auth_client.put(f'/api/rp/characters/{cid}', json={
            'name': '新名字', 'description': '新描述', 'personality': '新性格',
            'background': '新背景', 'speaking_style': '新风格',
        })
        assert r.get_json()['code'] == 0

        lst = auth_client.get(f'/api/rp/{sample_work}/characters').get_json()['data']['characters']
        ch = [c for c in lst if c['char_id'] == cid][0]
        assert ch['name'] == '新名字'
        assert ch['background'] == '新背景'

    def test_update_requires_name(self, auth_client, sample_work):
        cid = self._seed_char(auth_client, sample_work)
        r = auth_client.put(f'/api/rp/characters/{cid}', json={'name': ''})
        assert r.get_json()['code'] == 1
        assert '角色名' in r.get_json()['msg']

    def test_update_other_users_char_404(self, app, auth_client, sample_work):
        cid = self._seed_char(auth_client, sample_work)
        other = _make_second_user(app)
        r = other.put(f'/api/rp/characters/{cid}', json={'name': '抢改'})
        assert r.get_json()['code'] == 404

    def test_update_nonexistent_404(self, auth_client):
        r = auth_client.put('/api/rp/characters/99999', json={'name': '无名'})
        assert r.get_json()['code'] == 404

    def test_delete_still_works(self, auth_client, sample_work):
        cid = self._seed_char(auth_client, sample_work)
        r = auth_client.delete(f'/api/rp/characters/{cid}')
        assert r.get_json()['code'] == 0
        lst = auth_client.get(f'/api/rp/{sample_work}/characters').get_json()['data']['characters']
        assert len(lst) == 0