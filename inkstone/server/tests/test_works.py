"""作品端点测试"""
import pytest


class TestCreateWork:
    """测试创建作品接口"""

    def test_create_work_success(self, auth_client):
        res = auth_client.post('/api/works', json={
            'title': '我的小说',
            'type': 'novel',
            'summary': '这是一个测试小说'
        })
        data = res.get_json()
        assert data['code'] == 0
        assert 'work_id' in data['data']

    def test_create_work_empty_title(self, auth_client):
        res = auth_client.post('/api/works', json={
            'title': '',
            'type': 'novel'
        })
        data = res.get_json()
        assert data['code'] == 1
        assert '标题' in data['msg']

    def test_create_work_invalid_type(self, auth_client):
        res = auth_client.post('/api/works', json={
            'title': '测试',
            'type': 'invalid_type'
        })
        data = res.get_json()
        assert data['code'] == 1
        assert '类型' in data['msg']

    def test_create_work_not_logged_in(self, client):
        res = client.post('/api/works', json={
            'title': '测试',
            'type': 'novel'
        })
        data = res.get_json()
        assert data['code'] == 401


class TestListWorks:
    """测试作品列表接口"""

    def test_list_works_empty(self, auth_client):
        res = auth_client.get('/api/works')
        data = res.get_json()
        assert data['code'] == 0
        assert data['data']['items'] == []
        assert data['data']['total'] == 0

    def test_list_works_with_data(self, auth_client, sample_work):
        res = auth_client.get('/api/works')
        data = res.get_json()
        assert data['code'] == 0
        assert len(data['data']['items']) == 1
        assert data['data']['items'][0]['title'] == '测试作品'

    def test_list_works_not_logged_in(self, client):
        res = client.get('/api/works')
        data = res.get_json()
        assert data['code'] == 401


class TestGetWork:
    """测试获取作品详情接口"""

    def test_get_own_work(self, auth_client, sample_work):
        res = auth_client.get(f'/api/works/{sample_work}')
        data = res.get_json()
        assert data['code'] == 0
        assert data['data']['work']['title'] == '测试作品'
        assert len(data['data']['chapters']) > 0

    def test_get_nonexistent_work(self, auth_client):
        res = auth_client.get('/api/works/99999')
        data = res.get_json()
        assert data['code'] == 404


class TestUpdateWork:
    """测试更新作品接口"""

    def test_update_work_title(self, auth_client, sample_work):
        res = auth_client.put(f'/api/works/{sample_work}', json={
            'title': '新标题'
        })
        data = res.get_json()
        assert data['code'] == 0

        # 验证更新
        res = auth_client.get(f'/api/works/{sample_work}')
        data = res.get_json()
        assert data['data']['work']['title'] == '新标题'


class TestDeleteWork:
    """测试删除作品接口"""

    def test_delete_work(self, auth_client, sample_work):
        res = auth_client.delete(f'/api/works/{sample_work}')
        data = res.get_json()
        assert data['code'] == 0

        # 验证删除
        res = auth_client.get(f'/api/works/{sample_work}')
        data = res.get_json()
        assert data['code'] == 404


class TestPublishWork:
    """测试发布作品接口"""

    def test_publish_work(self, auth_client, sample_work):
        res = auth_client.put(f'/api/works/{sample_work}/status', json={
            'status': 'published'
        })
        data = res.get_json()
        assert data['code'] == 0
        assert data['data']['status'] == 'published'


class TestPublicWork:
    """测试公开作品接口"""

    def test_get_public_work(self, client, auth_client, sample_work):
        # 先发布作品
        auth_client.put(f'/api/works/{sample_work}/status', json={
            'status': 'published'
        })

        # 未登录用户访问公开作品
        res = client.get(f'/api/works/public/{sample_work}')
        data = res.get_json()
        assert data['code'] == 0
        assert data['data']['work']['title'] == '测试作品'

    def test_get_unpublished_work(self, client, sample_work):
        # 未发布的作品不应被公开访问
        res = client.get(f'/api/works/public/{sample_work}')
        data = res.get_json()
        assert data['code'] == 404
