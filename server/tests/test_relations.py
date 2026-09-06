"""P6-C3：角色关系图（work_relations）——手动维护的有向边。

覆盖：列表/新增/删除、参数校验、权限隔离（非本人作品 404）、上限、未登录 401。
"""
import pytest


class TestRelations:
    def test_list_requires_login(self, app, auth_client, sample_work):
        anon = app.test_client()
        r = anon.get(f'/api/relations/{sample_work}')
        assert r.get_json()['code'] == 401

    def test_list_empty(self, auth_client, sample_work):
        r = auth_client.get(f'/api/relations/{sample_work}')
        assert r.get_json()['code'] == 0
        assert r.get_json()['data']['items'] == []

    def test_add_and_list(self, auth_client, sample_work):
        r = auth_client.post(f'/api/relations/{sample_work}', json={
            'source': '林晚', 'relation': '师傅', 'target': '白泽'})
        assert r.get_json()['code'] == 0

        rows = auth_client.get(f'/api/relations/{sample_work}').get_json()['data']['items']
        assert len(rows) == 1
        assert rows[0]['source'] == '林晚'
        assert rows[0]['relation'] == '师傅'
        assert rows[0]['target'] == '白泽'

    def test_add_requires_all_fields(self, auth_client, sample_work):
        r = auth_client.post(f'/api/relations/{sample_work}', json={'source': 'A', 'relation': 'B'})
        data = r.get_json()
        assert data['code'] == 1
        assert '关系' in data['msg']

    def test_add_trims_and_limits_length(self, auth_client, sample_work):
        r = auth_client.post(f'/api/relations/{sample_work}', json={
            'source': '名' * 31, 'relation': '好友', 'target': 'B'})
        assert r.get_json()['code'] == 1

    def test_add_other_users_work_404(self, app, auth_client, sample_work):
        other = app.test_client()
        other.post('/api/auth/register', json={'username': 'other2', 'password': 'test123456'})
        other.post('/api/auth/login', json={'username': 'other2', 'password': 'test123456'})
        r = other.post(f'/api/relations/{sample_work}', json={
            'source': 'A', 'relation': 'B', 'target': 'C'})
        assert r.get_json()['code'] == 404

    def test_delete(self, auth_client, sample_work):
        rid = auth_client.post(f'/api/relations/{sample_work}', json={
            'source': 'A', 'relation': 'B', 'target': 'C'}).get_json()['data']['relation_id']
        r = auth_client.delete(f'/api/relations/{sample_work}/{rid}')
        assert r.get_json()['code'] == 0
        rows = auth_client.get(f'/api/relations/{sample_work}').get_json()['data']['items']
        assert rows == []

    def test_delete_not_owner_404(self, app, auth_client, sample_work):
        rid = auth_client.post(f'/api/relations/{sample_work}', json={
            'source': 'A', 'relation': 'B', 'target': 'C'}).get_json()['data']['relation_id']
        other = app.test_client()
        other.post('/api/auth/register', json={'username': 'other3', 'password': 'test123456'})
        other.post('/api/auth/login', json={'username': 'other3', 'password': 'test123456'})
        r = other.delete(f'/api/relations/{sample_work}/{rid}')
        assert r.get_json()['code'] == 404

    def test_delete_nonexistent_404(self, auth_client, sample_work):
        r = auth_client.delete(f'/api/relations/{sample_work}/99999')
        assert r.get_json()['code'] == 404

    def test_max_relations(self, auth_client, sample_work):
        # 塞满上限（通过数据库直插模拟，避免 60 次 HTTP 调用）
        from database.db import execute
        for i in range(60):
            execute(
                'INSERT INTO work_relations (work_id, source, relation, target) '
                "VALUES (%s, 'A', '与', 'B')",
                (sample_work,))
        r = auth_client.post(f'/api/relations/{sample_work}', json={
            'source': 'X', 'relation': '与', 'target': 'Y'})
        assert r.get_json()['code'] == 1
        assert '上限' in r.get_json()['msg']