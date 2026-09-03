import time
from collections import defaultdict
from flask import Blueprint, request, session
import bcrypt
from database.db import query, execute
from utils.helpers import ok, fail, login_required, get_login_user, _fmt

auth_bp = Blueprint('auth', __name__)

# 简单内存速率限制：{ip: [timestamps]}
_login_attempts = defaultdict(list)
_REGISTER_ATTEMPTS = defaultdict(list)
_MAX_LOGIN_ATTEMPTS = 10  # 10次
_LOGIN_WINDOW = 60  # 60秒内
_MAX_REGISTER_ATTEMPTS = 5
_REGISTER_WINDOW = 300  # 5分钟内


def _check_rate_limit(store, ip, max_attempts, window):
    now = time.time()
    store[ip] = [t for t in store[ip] if now - t < window]
    if len(store[ip]) >= max_attempts:
        return False
    store[ip].append(now)
    return True


@auth_bp.post('/register')
def register():
    ip = request.remote_addr or 'unknown'
    if not _check_rate_limit(_REGISTER_ATTEMPTS, ip, _MAX_REGISTER_ATTEMPTS, _REGISTER_WINDOW):
        return fail('注册过于频繁，请稍后再试')

    data = request.get_json()
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return fail('用户名和密码不能为空')
    if len(username) < 2 or len(username) > 50:
        return fail('用户名长度需在2-50字符之间')
    if len(password) < 6:
        return fail('密码长度不能少于6位')

    existing = query('SELECT user_id FROM users WHERE username = %s', (username,), one=True)
    if existing:
        return fail('该用户名已被注册')

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, password_hash))

    return ok(msg='注册成功')


@auth_bp.post('/login')
def login():
    ip = request.remote_addr or 'unknown'
    if not _check_rate_limit(_login_attempts, ip, _MAX_LOGIN_ATTEMPTS, _LOGIN_WINDOW):
        return fail('登录尝试过多，请1分钟后再试')

    data = request.get_json()
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return fail('请输入用户名和密码')

    user = query('SELECT * FROM users WHERE username = %s', (username,), one=True)
    if not user:
        return fail('用户名或密码错误')

    if not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
        return fail('用户名或密码错误')

    session['user_id'] = user['user_id']
    session['username'] = user['username']

    return ok({
        'user_id': user['user_id'],
        'username': user['username'],
        'avatar': user['avatar'],
        'bio': user['bio'],
        'level': user['level'],
        'exp': user['exp']
    }, msg='登录成功')


@auth_bp.post('/logout')
def logout():
    session.clear()
    return ok(msg='已退出登录')


@auth_bp.get('/me')
def me():
    if 'user_id' not in session:
        return fail('未登录', code=401)

    user = query('SELECT user_id, username, avatar, cover_image, bio, level, exp, created_at FROM users WHERE user_id = %s', (session['user_id'],), one=True)
    if not user:
        session.clear()
        return fail('用户不存在', code=401)

    user['created_at'] = _fmt(user.get('created_at'))
    return ok(user)
