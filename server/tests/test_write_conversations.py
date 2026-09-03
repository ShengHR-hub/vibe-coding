"""W3a：AI 会话管理端点测试（数据层语义：列表/详情/删除/剪枝，不依赖 SSE 上下文）。"""
from database.db import execute, query
from routes import write as write_mod


def _uid(username='testuser'):
    return query('SELECT user_id FROM users WHERE username = %s', (username,), one=True)['user_id']


def _seed(user_id, session_key, texts=None):
    """落库 user+assistant 两行（模拟一次完整对话）。"""
    texts = texts or (f'关于{session_key}的问题', f'关于{session_key}的回答')
    execute(
        'INSERT INTO ai_conversations (user_id, session_key, role, content) VALUES (%s, %s, %s, %s)',
        (user_id, session_key, 'user', texts[0]),
    )
    execute(
        'INSERT INTO ai_conversations (user_id, session_key, role, content) VALUES (%s, %s, %s, %s)',
        (user_id, session_key, 'assistant', texts[1]),
    )


def test_conversation_lifecycle(auth_client):
    uid = _uid()
    _seed(uid, 'demo-session-1', ('帮我构思悬疑开头', '好的，夜晚的小巷里…'))
    # 列表含该会话：预览 + 计数
    sessions = auth_client.get('/api/write/conversations').get_json()['data']['sessions']
    assert any(s['session_key'] == 'demo-session-1' for s in sessions)
    hit = next(s for s in sessions if s['session_key'] == 'demo-session-1')
    assert '悬疑' in hit['preview']
    assert hit['msg_count'] == 2
    # 详情：user 在前
    detail = auth_client.get('/api/write/conversations/demo-session-1').get_json()['data']
    assert len(detail['messages']) == 2
    assert detail['messages'][0]['role'] == 'user'
    # 删除后列表不可见、详情 404
    assert auth_client.delete('/api/write/conversations/demo-session-1').get_json()['code'] == 0
    sessions = auth_client.get('/api/write/conversations').get_json()['data']['sessions']
    assert not any(s['session_key'] == 'demo-session-1' for s in sessions)
    assert auth_client.get('/api/write/conversations/demo-session-1').get_json()['code'] == 404


def test_cannot_read_foreign_session(auth_client, app):
    uid = _uid()
    _seed(uid, 'secret-key-1', ('我的私密构思', '秘密回复'))
    other = app.test_client()
    other.post('/api/auth/register', json={'username': 'conv_other', 'password': 'test123456'})
    other.post('/api/auth/login', json={'username': 'conv_other', 'password': 'test123456'})
    # 他人读/删：404/无影响
    assert other.get('/api/write/conversations/secret-key-1').get_json()['code'] == 404
    other.delete('/api/write/conversations/secret-key-1')
    sessions = auth_client.get('/api/write/conversations').get_json()['data']['sessions']
    assert any(s['session_key'] == 'secret-key-1' for s in sessions)


def test_prune_keeps_recent_sessions(auth_client):
    uid = _uid()
    for i in range(3):
        _seed(uid, f'prune-key-{i}')
    # keep=2：保留 conv_id 最新的 2 个（prune-key-1/2）
    write_mod._prune_conversations(uid, keep=2)
    keys = {s['session_key'] for s in auth_client.get('/api/write/conversations').get_json()['data']['sessions']}
    assert keys == {'prune-key-1', 'prune-key-2'}
    # keep=0：全部清空
    write_mod._prune_conversations(uid, keep=0)
    sessions = auth_client.get('/api/write/conversations').get_json()['data']['sessions']
    assert len(sessions) == 0
