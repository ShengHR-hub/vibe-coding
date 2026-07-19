"""社区端点测试"""
import pytest


class TestFeed:
    """测试社区推荐流接口"""

    def test_feed_empty(self, client):
        res = client.get('/api/community/feed')
        data = res.get_json()
        assert data['code'] == 0
        assert data['data']['items'] == []

    def test_feed_with_published_work(self, client, auth_client, sample_work):
        # 发布作品
        auth_client.put(f'/api/works/{sample_work}/status', json={
            'status': 'published'
        })

        # 获取推荐流
        res = client.get('/api/community/feed')
        data = res.get_json()
        assert data['code'] == 0
        assert len(data['data']['items']) == 1
        assert data['data']['items'][0]['title'] == '测试作品'

    def test_feed_sort_hot(self, client, auth_client, sample_work):
        auth_client.put(f'/api/works/{sample_work}/status', json={
            'status': 'published'
        })

        res = client.get('/api/community/feed?sort=hot')
        data = res.get_json()
        assert data['code'] == 0

    def test_feed_sort_new(self, client, auth_client, sample_work):
        auth_client.put(f'/api/works/{sample_work}/status', json={
            'status': 'published'
        })

        res = client.get('/api/community/feed?sort=new')
        data = res.get_json()
        assert data['code'] == 0

    def test_feed_pagination(self, client, auth_client):
        # 创建并发布多个作品
        for i in range(5):
            res = auth_client.post('/api/works', json={
                'title': f'作品{i}',
                'type': 'novel'
            })
            work_id = res.get_json()['data']['work_id']
            auth_client.put(f'/api/works/{work_id}/status', json={
                'status': 'published'
            })

        # 第一页
        res = client.get('/api/community/feed?page=1&page_size=2')
        data = res.get_json()
        assert data['code'] == 0
        assert len(data['data']['items']) == 2
        assert data['data']['total'] == 5

        # 第二页
        res = client.get('/api/community/feed?page=2&page_size=2')
        data = res.get_json()
        assert len(data['data']['items']) == 2


class TestSearch:
    """测试搜索接口"""

    def test_search_by_title(self, client, auth_client, sample_work):
        auth_client.put(f'/api/works/{sample_work}/status', json={
            'status': 'published'
        })

        res = client.get('/api/community/search?q=测试')
        data = res.get_json()
        assert data['code'] == 0
        assert len(data['data']['items']) == 1

    def test_search_no_result(self, client, auth_client, sample_work):
        auth_client.put(f'/api/works/{sample_work}/status', json={
            'status': 'published'
        })

        res = client.get('/api/community/search?q=不存在的关键词')
        data = res.get_json()
        assert data['code'] == 0
        assert len(data['data']['items']) == 0

    def test_search_empty_query(self, client):
        res = client.get('/api/community/search?q=')
        data = res.get_json()
        assert data['code'] == 1
        assert '关键词' in data['msg']

    def test_search_by_type(self, client, auth_client, sample_work):
        auth_client.put(f'/api/works/{sample_work}/status', json={
            'status': 'published'
        })

        res = client.get('/api/community/search?q=测试&type=novel')
        data = res.get_json()
        assert data['code'] == 0

    def test_search_by_tag(self, client, auth_client):
        # 创建带标签的作品
        res = auth_client.post('/api/works', json={
            'title': '标签测试',
            'type': 'novel',
            'tags': '科幻,未来'
        })
        work_id = res.get_json()['data']['work_id']
        auth_client.put(f'/api/works/{work_id}/status', json={
            'status': 'published'
        })

        res = client.get('/api/community/search?tag=科幻')
        data = res.get_json()
        assert data['code'] == 0
        assert len(data['data']['items']) == 1


class TestCategory:
    """测试分类接口"""

    def test_category_novel(self, client, auth_client, sample_work):
        auth_client.put(f'/api/works/{sample_work}/status', json={
            'status': 'published'
        })

        res = client.get('/api/community/category/novel')
        data = res.get_json()
        assert data['code'] == 0
        assert len(data['data']['items']) == 1

    def test_category_invalid(self, client):
        res = client.get('/api/community/category/invalid')
        data = res.get_json()
        assert data['code'] == 1
        assert '类型' in data['msg']
