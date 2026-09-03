"""认证端点测试"""
import pytest


class TestRegister:
    """测试注册接口"""

    def test_register_success(self, client):
        res = client.post('/api/auth/register', json={
            'username': 'newuser',
            'password': 'password123'
        })
        data = res.get_json()
        assert data['code'] == 0
        assert data['msg'] == '注册成功'

    def test_register_empty_username(self, client):
        res = client.post('/api/auth/register', json={
            'username': '',
            'password': 'password123'
        })
        data = res.get_json()
        assert data['code'] == 1
        assert '用户名' in data['msg']

    def test_register_short_password(self, client):
        res = client.post('/api/auth/register', json={
            'username': 'testuser2',
            'password': '123'
        })
        data = res.get_json()
        assert data['code'] == 1
        assert '密码' in data['msg']

    def test_register_duplicate(self, client):
        # 第一次注册
        client.post('/api/auth/register', json={
            'username': 'dupuser',
            'password': 'password123'
        })
        # 第二次注册同名用户
        res = client.post('/api/auth/register', json={
            'username': 'dupuser',
            'password': 'password123'
        })
        data = res.get_json()
        assert data['code'] == 1
        assert '已被注册' in data['msg']


class TestLogin:
    """测试登录接口"""

    def test_login_success(self, client):
        # 先注册
        client.post('/api/auth/register', json={
            'username': 'loginuser',
            'password': 'password123'
        })
        # 登录
        res = client.post('/api/auth/login', json={
            'username': 'loginuser',
            'password': 'password123'
        })
        data = res.get_json()
        assert data['code'] == 0
        assert data['msg'] == '登录成功'
        assert 'user_id' in data['data']

    def test_login_wrong_password(self, client):
        client.post('/api/auth/register', json={
            'username': 'wrongpass',
            'password': 'password123'
        })
        res = client.post('/api/auth/login', json={
            'username': 'wrongpass',
            'password': 'wrongpassword'
        })
        data = res.get_json()
        assert data['code'] == 1
        assert '错误' in data['msg']

    def test_login_nonexistent_user(self, client):
        res = client.post('/api/auth/login', json={
            'username': 'nonexistent',
            'password': 'password123'
        })
        data = res.get_json()
        assert data['code'] == 1


class TestMe:
    """测试获取当前用户接口"""

    def test_me_not_logged_in(self, client):
        res = client.get('/api/auth/me')
        data = res.get_json()
        assert data['code'] == 401

    def test_me_logged_in(self, auth_client):
        res = auth_client.get('/api/auth/me')
        data = res.get_json()
        assert data['code'] == 0
        assert data['data']['username'] == 'testuser'


class TestLogout:
    """测试登出接口"""

    def test_logout(self, auth_client):
        res = auth_client.post('/api/auth/logout')
        data = res.get_json()
        assert data['code'] == 0

        # 登出后应无法访问需要认证的接口
        res = auth_client.get('/api/auth/me')
        data = res.get_json()
        assert data['code'] == 401
