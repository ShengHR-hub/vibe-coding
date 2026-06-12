from flask import session


def ok(data=None, msg='success'):
    return {'code': 0, 'data': data, 'msg': msg}


def fail(msg='error', code=1, data=None):
    return {'code': code, 'data': data, 'msg': msg}


def login_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return fail('请先登录', code=401)
        return func(*args, **kwargs)
    return wrapper


def get_login_user():
    return {
        'user_id': session.get('user_id'),
        'username': session.get('username')
    }


def _fmt(val):
    if val is None:
        return None
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return val
