"""工具函数测试"""
import pytest
from utils.helpers import ok, fail, _fmt, get_login_user
from datetime import datetime


class TestOkFail:
    """测试 ok() 和 fail() 函数"""

    def test_ok_default(self):
        result = ok()
        assert result == {'code': 0, 'data': None, 'msg': 'success'}

    def test_ok_with_data(self):
        data = {'id': 1, 'name': 'test'}
        result = ok(data)
        assert result == {'code': 0, 'data': data, 'msg': 'success'}

    def test_ok_with_custom_msg(self):
        result = ok(msg='创建成功')
        assert result == {'code': 0, 'data': None, 'msg': '创建成功'}

    def test_fail_default(self):
        result = fail()
        assert result == {'code': 1, 'data': None, 'msg': 'error'}

    def test_fail_with_msg(self):
        result = fail('用户名不能为空')
        assert result == {'code': 1, 'data': None, 'msg': '用户名不能为空'}

    def test_fail_with_custom_code(self):
        result = fail('未登录', code=401)
        assert result == {'code': 401, 'data': None, 'msg': '未登录'}

    def test_fail_with_data(self):
        data = {'field': 'username'}
        result = fail('验证失败', data=data)
        assert result == {'code': 1, 'data': data, 'msg': '验证失败'}


class TestFmt:
    """测试 _fmt() 日期格式化函数"""

    def test_fmt_none(self):
        assert _fmt(None) is None

    def test_fmt_datetime(self):
        dt = datetime(2026, 1, 15, 10, 30, 0)
        result = _fmt(dt)
        assert result == '2026-01-15T10:30:00'

    def test_fmt_string(self):
        assert _fmt('2026-01-15') == '2026-01-15'

    def test_fmt_number(self):
        assert _fmt(123) == 123


class TestGetLoginUser:
    """测试 get_login_user() 函数"""

    def test_not_logged_in(self, app):
        with app.test_request_context():
            user = get_login_user()
            assert user['user_id'] is None
            assert user['username'] is None
