"""Pytest 配置文件（测试库隔离版）

约定：
- pytest 一律使用独立测试库 inkstone_test，绝不写开发库 inkstone；
- 每个 pytest 会话开始时自动重建 inkstone_test（删库→建库→执行 schema.sql），
  保证可重复执行、无脏数据、不撞唯一键/限速；
- 需在导入 app/config 之前设置 MYSQL_DB 环境变量（dotenv 不会覆盖已存在变量）。
"""
import os
# 测试库隔离：必须在导入 app/config 之前设置
os.environ['MYSQL_DB'] = 'inkstone_test'

import sys
import re
import pymysql
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from config import Config
from database.db import query, execute  # noqa: F401

_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
_TEST_DB = 'inkstone_test'
_ALL_TABLES = []  # 会话开始时填充


@pytest.fixture(scope='session', autouse=True)
def _fresh_test_db():
    """会话级：重建独立测试库并灌入最新 schema，确保每次运行从干净状态开始。"""
    conn_kw = dict(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        port=Config.MYSQL_PORT,
        autocommit=True,
        connect_timeout=10,
    )
    # 1) 重建数据库
    conn = pymysql.connect(**conn_kw)
    with conn.cursor() as cur:
        cur.execute(f'DROP DATABASE IF EXISTS {_TEST_DB}')
        cur.execute(
            f'CREATE DATABASE {_TEST_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    conn.close()

    # 2) 执行 schema（剔除其中的 CREATE DATABASE / USE 语句）
    with open(_SCHEMA_PATH, encoding='utf-8') as f:
        sql = f.read()
    sql = re.sub(r'(?im)^CREATE DATABASE[^;]*;\s*', '', sql)
    sql = re.sub(r'(?im)^USE [^;]*;\s*', '', sql)

    conn = pymysql.connect(
        database=_TEST_DB,
        client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS,
        **conn_kw,
    )
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute('SELECT 1')  # 排空多语句游标
    # 3) 记录全部表名，供用例间清空
    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            f"WHERE table_schema='{_TEST_DB}' ORDER BY table_name")
        _ALL_TABLES.extend(row[0] for row in cur.fetchall())
    conn.close()
    yield


@pytest.fixture(autouse=True)
def _clean_between_tests(_fresh_test_db):
    """函数级：每个用例开始前清空全部表，消除用例间顺序/数据依赖，保证可独立重复执行。"""
    conn_kw = dict(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        port=Config.MYSQL_PORT,
        autocommit=True,
        connect_timeout=10,
    )
    conn = pymysql.connect(database=_TEST_DB, **conn_kw)
    with conn.cursor() as cur:
        for t in _ALL_TABLES:
            cur.execute(f'DELETE FROM `{t}`')
    conn.close()
    # 清空内存限速计数（auth 限速按进程内 IP 计数，跨用例共享会误触发）
    from routes import auth as _auth_mod
    _auth_mod._login_attempts.clear()
    _auth_mod._REGISTER_ATTEMPTS.clear()
    # 清空 AI 配额计数（W1a，防止用例间相互影响）
    from utils import helpers as _helpers
    _helpers._ai_minute.clear()
    _helpers._ai_daily.clear()
    _helpers._ai_day.clear()
    yield


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
