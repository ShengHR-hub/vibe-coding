"""P4-E3b：结构审校（builder 级 + 端点级，stub AI）。"""
import pytest

from utils.prompt_builder import build_struct_review
from routes import write as write_mod


def test_struct_prompt_shape():
    msgs = build_struct_review('第1章《归来》：开头。\n第2章《旧信》：开头。', outline_text='第一卷 灯 / 第一章 归来')
    assert msgs[0]['role'] == 'system'
    user = msgs[1]['content']
    assert '结构审校' in user
    assert '第1章《归来》' in user
    assert '原定大纲' in user and '灯' in user


def test_struct_prompt_no_outline_ok():
    user = build_struct_review('第1章：x', None)[1]['content']
    assert '原定大纲' not in user


@pytest.fixture
def capture(monkeypatch):
    state = {}

    def fake_completion(messages, temperature=0.7, max_tokens=2048):
        state['messages'] = messages
        return '【总体判断】节奏平稳；【优先级】先处理第二章。'

    monkeypatch.setattr(write_mod, 'chat_completion', fake_completion)
    monkeypatch.setattr(write_mod, 'log_ai_call', lambda *a, **k: None)
    return state


def _create_work_with_chapters(client):
    res = client.post('/api/works', json={'title': '审校书', 'type': 'novel', 'content': '正文。'})
    work_id = res.get_json()['data']['work_id']
    from database.db import execute
    execute('INSERT INTO chapters (work_id, chapter_no, title, content, word_count) VALUES (%s, 2, %s, %s, %s)',
            (work_id, '第二章', '第二章的正文内容。', 8))
    return work_id


def test_struct_endpoint_ok(auth_client, capture):
    work_id = _create_work_with_chapters(auth_client)
    r = auth_client.post('/api/write/struct', json={'work_id': work_id})
    assert r.get_json()['code'] == 0
    assert '总体判断' in r.get_json()['data']['report']
    user = capture['messages'][1]['content']
    assert '第2章' in user


def test_struct_endpoint_guards(auth_client, app):
    work_id = _create_work_with_chapters(auth_client)
    # 无效 work_id / 未登录
    assert auth_client.post('/api/write/struct', json={'work_id': 999999}).get_json()['code'] == 404
    guest = app.test_client()
    assert guest.post('/api/write/struct', json={'work_id': work_id}).get_json()['code'] == 401
    # 他人作品
    other = app.test_client()
    other.post('/api/auth/register', json={'username': 'struct_other', 'password': 'test123456'})
    other.post('/api/auth/login', json={'username': 'struct_other', 'password': 'test123456'})
    assert other.post('/api/write/struct', json={'work_id': work_id}).get_json()['code'] == 404
