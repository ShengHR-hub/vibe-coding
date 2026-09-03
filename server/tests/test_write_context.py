"""W2a：续写上下文注入测试（stub 掉真实流式调用，零 token 消耗）。"""
import pytest

from routes import write as write_mod


@pytest.fixture
def capture_stream(monkeypatch):
    """捕获发给模型的 messages，并返回假流内容。"""
    captured = {}

    def fake_stream(messages, temperature=0.7, max_tokens=2048):
        captured['messages'] = messages
        yield '续写片段。'

    monkeypatch.setattr(write_mod, 'chat_completion_stream', fake_stream)
    monkeypatch.setattr(write_mod, 'log_ai_call', lambda *a, **k: None)
    return captured


def _create_work_with_context(client, title='我的长篇小说'):
    """通过 API 建作品，并直接写库加章节与角色卡。"""
    from database.db import execute
    res = client.post('/api/works', json={
        'title': title, 'type': 'novel', 'summary': '一个少年在末日寻找家人。',
        'content': '第一章内容。',
    })
    work_id = res.get_json()['data']['work_id']
    execute(
        'INSERT INTO chapters (work_id, chapter_no, title, content, word_count) '
        'VALUES (%s, %s, %s, %s, %s)',
        (work_id, 1, '第一章', '主角醒来，城市已空。', 10),
    )
    execute(
        'INSERT INTO chapters (work_id, chapter_no, title, content, word_count) '
        'VALUES (%s, %s, %s, %s, %s)',
        (work_id, 2, '第二章', '他遇到了同伴。', 8),
    )
    execute(
        'INSERT INTO rp_characters (work_id, name, description, personality, background, speaking_style) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (work_id, '林墨', '黑发少年', '冷静寡言', '失去家人的幸存者', '简短直接'),
    )
    return work_id


def test_continue_injects_work_context(auth_client, capture_stream):
    work_id = _create_work_with_context(auth_client)
    r = auth_client.post('/api/write/continue', json={
        'content': '他望向远方，',
        'style': '现代',
        'work_id': work_id,
    })
    assert r.status_code == 200
    user_msg = capture_stream['messages'][-1]['content']
    assert '我的长篇小说' in user_msg
    assert '第一章' in user_msg and '第二章' in user_msg
    assert '主要角色' in user_msg and '林墨' in user_msg
    assert '设定参考' in user_msg


def test_continue_ignores_foreign_work(auth_client, app, capture_stream):
    """他人作品不得注入上下文（红线：works 归属保护）。"""
    # 注册并登录另一个真实用户（FK 约束下 works.user_id 必须指向存在的 users）
    other = app.test_client()
    other.post('/api/auth/register', json={'username': 'otheruser', 'password': 'test123456'})
    other.post('/api/auth/login', json={'username': 'otheruser', 'password': 'test123456'})
    foreign_work_id = _create_work_with_context(other, title='他人的私密作品')
    # 当前登录用户（testuser）用他人的 work_id 续写
    r = auth_client.post('/api/write/continue', json={
        'content': '夜色降临。', 'work_id': foreign_work_id,
    })
    assert r.status_code == 200
    user_msg = capture_stream['messages'][-1]['content']
    assert '他人的私密作品' not in user_msg
    assert '设定参考' not in user_msg


def test_continue_without_work_id_still_works(auth_client, capture_stream):
    r = auth_client.post('/api/write/continue', json={'content': '雨一直下。'})
    assert r.status_code == 200
    user_msg = capture_stream['messages'][-1]['content']
    assert '设定参考' not in user_msg
    assert '雨一直下' in user_msg
