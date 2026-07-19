"""Pytest 配置文件"""
import sys
import os
import pytest

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from database.db import query, execute


@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app()
    app.config['TESTING'] = True
    yield app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """创建已认证的测试客户端"""
    # 注册测试用户
    client.post('/api/auth/register', json={
        'username': 'testuser',
        'password': 'test123456'
    })

    # 登录
    client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'test123456'
    })

    return client


@pytest.fixture
def sample_work(auth_client):
    """创建示例作品"""
    res = auth_client.post('/api/works', json={
        'title': '测试作品',
        'type': 'novel',
        'summary': '这是一个测试作品',
        'content': '这是测试内容。'
    })
    return res.get_json()['data']['work_id']
