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


class TestChapterStatus:
    """P6-C1：章节草稿/正式状态 + 导出只导正式稿"""

    def _save_chapter(self, auth_client, work_id, title, content, status=None):
        """保存第一章（默认内容更新不带状态）"""
        res = auth_client.get(f'/api/works/{work_id}')
        ch_id = res.get_json()['data']['chapters'][0]['chapter_id']
        body = {
            'work_id': work_id,
            'title': '测试作品',
            'chapter_id': ch_id,
            'chapter_title': title,
            'content': content,
        }
        if status:
            body['status'] = status
        return auth_client.post('/api/works/save', json=body)

    def test_save_chapter_default_status_draft(self, auth_client, sample_work):
        self._save_chapter(auth_client, sample_work, '第一章', '正文内容')
        res = auth_client.get(f'/api/works/{sample_work}')
        ch = res.get_json()['data']['chapters'][0]
        assert ch['status'] == 'draft'

    def test_save_chapter_mark_formal(self, auth_client, sample_work):
        self._save_chapter(auth_client, sample_work, '第一章', '正文内容', status='formal')
        res = auth_client.get(f'/api/works/{sample_work}')
        ch = res.get_json()['data']['chapters'][0]
        assert ch['status'] == 'formal'

    def test_save_chapter_invalid_status(self, auth_client, sample_work):
        res = self._save_chapter(auth_client, sample_work, '第一章', '正文', status='done')
        assert res.get_json()['code'] == 1
        assert '状态' in res.get_json()['msg']

    def test_save_chapter_without_status_keeps_formal(self, auth_client, sample_work):
        # 先标正式，再用不带 status 的接口保存（保存正文不应把状态打回草稿）
        res = self._save_chapter(auth_client, sample_work, '第一章', '正文A', status='formal')
        assert res.get_json()['code'] == 0
        self._save_chapter(auth_client, sample_work, '第一章', '正文B')
        res = auth_client.get(f'/api/works/{sample_work}')
        assert res.get_json()['data']['chapters'][0]['status'] == 'formal'

    def test_export_default_includes_all(self, auth_client, sample_work):
        self._save_chapter(auth_client, sample_work, '第一章', '正文内容')
        res = auth_client.get(f'/api/works/{sample_work}/export')
        assert res.status_code == 200
        assert '正文内容' in res.get_data(as_text=True)

    def test_export_formal_only(self, auth_client, sample_work):
        # 当前所有章节都标正式 → 导出包含正文
        self._save_chapter(auth_client, sample_work, '第一章', '正式稿内容', status='formal')
        res = auth_client.get(f'/api/works/{sample_work}/export?formal=1')
        assert res.status_code == 200
        text = res.get_data(as_text=True)
        assert '正式稿内容' in text

    def test_export_formal_excludes_draft(self, auth_client, sample_work):
        # 章节保持草稿 → formal 导出不含其正文
        self._save_chapter(auth_client, sample_work, '第一章', '草稿内容')
        res = auth_client.get(f'/api/works/{sample_work}/export?formal=1')
        text = res.get_data(as_text=True)
        assert '草稿内容' not in text

    def test_export_formal_requires_login(self, app, auth_client, sample_work):
        # 未登录用户访问导出端点 → 401（独立未登录客户端，避免 session 串号）
        anon = app.test_client()
        res = anon.get(f'/api/works/{sample_work}/export?formal=1')
        assert res.get_json()['code'] == 401
