"""W4a：references 素材注入测试（builder 级 + 端点级，stub 掉真实 AI）。"""
import pytest

from utils.prompt_builder import (
    build_continue, build_polish, build_references_text,
)
from routes import write as write_mod


# ---------- builder 级 ----------

def test_references_text_format():
    block = build_references_text([
        {'type': '景物描写', 'content': '雨打芭蕉，声声入耳。'},
        '孤舟蓑笠翁，独钓寒江雪。',
    ])
    assert block is not None
    assert '参考素材' in block
    assert '[景物描写] 雨打芭蕉' in block
    assert '不要照抄整句或整段' in block


def test_references_text_empty_and_cap():
    assert build_references_text(None) is None
    assert build_references_text([]) is None
    assert build_references_text([{'content': '   '}]) is None
    many = [{'type': f't{i}', 'content': f'内容{i}'} for i in range(9)]
    block = build_references_text(many)
    assert block.count('- [') <= 6
    assert '内容7' not in block


def test_builders_embed_references():
    refs = [{'type': '诗词', 'content': '海上生明月，天涯共此时。'}]
    c = build_continue('夜色深沉。', references=refs)
    assert '参考素材' in c[-1]['content']
    assert '海上生明月' in c[-1]['content']
    assert '参考素材' not in build_continue('夜色深沉。')[-1]['content']
    p = build_polish('我很难过。', mode='文艺', references=refs)
    assert '参考素材' in p[-1]['content']


# ---------- 端点级 ----------

@pytest.fixture
def capture(monkeypatch):
    state = {}

    def fake_stream(messages, temperature=0.7, max_tokens=2048):
        state['stream_messages'] = messages
        yield '续写。'

    def fake_completion(messages, temperature=0.7, max_tokens=2048):
        state['completion_messages'] = messages
        return 'ok'

    monkeypatch.setattr(write_mod, 'chat_completion_stream', fake_stream)
    monkeypatch.setattr(write_mod, 'chat_completion', fake_completion)
    monkeypatch.setattr(write_mod, 'log_ai_call', lambda *a, **k: None)
    return state


def test_continue_sends_references(auth_client, capture):
    refs = [
        {'type': '景物描写', 'content': '雨打芭蕉'},
        {'type': '诗词', 'content': '海上生明月'},
    ]
    r = auth_client.post('/api/write/continue', json={'content': '他推开门。', 'references': refs})
    assert r.status_code == 200
    user_msg = capture['stream_messages'][-1]['content']
    assert '参考素材' in user_msg
    assert '雨打芭蕉' in user_msg and '海上生明月' in user_msg


def test_polish_sends_references(auth_client, capture):
    r = auth_client.post('/api/write/polish', json={
        'text': '他在夜里哭泣。', 'mode': '文艺',
        'references': [{'type': '情感表达', 'content': '月落乌啼霜满天'}],
    })
    assert r.get_json()['code'] == 0
    user_msg = capture['completion_messages'][-1]['content']
    assert '月落乌啼霜满天' in user_msg


def test_references_absent_when_not_provided(auth_client, capture):
    r = auth_client.post('/api/write/polish', json={'text': '他在夜里哭泣。', 'mode': '文艺'})
    assert r.get_json()['code'] == 0
    assert '参考素材' not in capture['completion_messages'][-1]['content']
