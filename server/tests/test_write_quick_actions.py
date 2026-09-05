"""划词快捷操作（2026-09）：/fix 查错、/interpret 翻译解释、/find-lines 意境找句。

AI 全部 stub，零 token 消耗；find-lines 走本地素材池 + mock 模型打分。
"""
import json
import pytest

from routes import write as write_mod
from utils.prompt_builder import build_fix, build_interpret, build_find_lines


@pytest.fixture
def stub_completion(monkeypatch):
    """stub 非流式 chat_completion，记录最近一次 messages 并返回预设文本。"""
    state = {'messages': None, 'result': 'stub'}

    def fake_completion(messages, temperature=0.7, max_tokens=2048):
        state['messages'] = messages
        # 返回预设 JSON（支持 dict 转字符串）
        if isinstance(state['result'], (dict, list)):
            return json.dumps(state['result'], ensure_ascii=False)
        return state['result']

    monkeypatch.setattr(write_mod, 'chat_completion', fake_completion)
    monkeypatch.setattr(write_mod, 'log_ai_call', lambda *a, **k: None)
    return state


def _seed_pool(auth_client):
    """往素材库塞两条，供 find-lines 本地匹配。"""
    from database.db import execute
    execute(
        'INSERT INTO poems (title, author, content, category, source) '
        "VALUES ('静夜思', '李白', '床前明月光，疑是地上霜。举头望明月，低头思故乡。', '思乡', 'seed')"
    )
    execute(
        'INSERT INTO poems (title, author, content, category, source) '
        "VALUES ('送别', '王维', '劝君更尽一杯酒，西出阳关无故人。', '离别', 'seed')"
    )
    execute(
        'INSERT INTO materials (title, category, content) '
        'VALUES (%s, %s, %s)',
        ('离别祝福', '离别', '愿此去繁花似锦，再相逢依旧如故。')
    )


# ---------- /fix 查错 ----------

def test_fix_requires_login(client):
    r = client.post('/api/write/fix', json={'text': '今天天气很好。'})
    assert r.get_json()['code'] == 401


def test_fix_returns_structured_fixes(auth_client, stub_completion):
    stub_completion['result'] = [
        {'original': '在次', 'suggestion': '在此', 'reason': '错别字'},
    ]
    r = auth_client.post('/api/write/fix', json={'text': '请在次确认。'})
    assert r.status_code == 200
    data = r.get_json()['data']
    assert len(data['fixes']) == 1
    assert data['fixes'][0]['original'] == '在次'
    assert data['fixes'][0]['suggestion'] == '在此'
    # prompt 中应包含原文
    user_msg = stub_completion['messages'][-1]['content']
    assert '请在次确认' in user_msg


def test_fix_rejects_suggestion_not_in_text(auth_client, stub_completion):
    """模型胡编的 original 不在原文中 → 过滤掉（防误替换）。"""
    stub_completion['result'] = [
        {'original': '不存在的词', 'suggestion': '替换词', 'reason': 'xxx'},
    ]
    r = auth_client.post('/api/write/fix', json={'text': '今天的阳光很好。'})
    data = r.get_json()['data']
    assert data['fixes'] == []


def test_fix_requires_min_length(auth_client):
    r = auth_client.post('/api/write/fix', json={'text': '短'})
    assert r.get_json()['code'] != 0


# ---------- /interpret 翻译解释 ----------

def test_interpret_returns_explanation(auth_client, stub_completion):
    stub_completion['result'] = '这句写的是思乡之情。'
    r = auth_client.post('/api/write/interpret', json={'text': '举头望明月'})
    assert r.status_code == 200
    data = r.get_json()['data']
    assert data['explanation'] == '这句写的是思乡之情。'
    user_msg = stub_completion['messages'][-1]['content']
    assert '举头望明月' in user_msg


def test_interpret_requires_text(auth_client):
    r = auth_client.post('/api/write/interpret', json={'text': '  '})
    assert r.get_json()['code'] != 0


def test_prompt_builders_shape():
    """prompt 模板结构自检：系统 + 用户，内容完整。"""
    fx = build_fix('他说的对，我认同。')
    assert fx[0]['role'] == 'system' and '校对' in fx[0]['content']
    assert '他说的对' in fx[1]['content']

    interp = build_interpret('举头望明月')
    assert interp[0]['role'] == 'system' and '释义' in interp[0]['content']
    assert '举头望明月' in interp[1]['content']

    fl = build_find_lines('夕阳下离别的惆怅', '[0] poem 《送别》（王维）：劝君更尽一杯酒')
    assert fl[0]['role'] == 'system'
    assert 'picks' in fl[0]['content'] and 'created' in fl[0]['content']
    assert '夕阳下离别的惆怅' in fl[1]['content']
    assert '送别' in fl[1]['content']


# ---------- /find-lines 意境找句 ----------

def test_find_lines_local_match(auth_client, stub_completion):
    _seed_pool(auth_client)
    write_mod._FIND_LINES_CACHE.clear()
    stub_completion['result'] = {
        'picks': [
            {'idx': 1, 'reason': '同是送别题'},
            {'idx': 2, 'reason': '离别祝福'},
        ],
        'created': ['长风送君去，明月照归途。'],
    }
    r = auth_client.post('/api/write/find-lines', json={'intent': '送别老友的惆怅'})
    assert r.status_code == 200
    data = r.get_json()['data']
    assert len(data['local']) == 2
    assert data['local'][0]['title'] == '送别'
    assert data['local'][1]['kind'] == 'material'
    assert data['local'][1]['content'].startswith('愿此去')
    assert data['created'] == ['长风送君去，明月照归途。']
    # pool 中应包含素材库内容
    user_msg = stub_completion['messages'][-1]['content']
    assert '送别' in user_msg and '素材清单' in user_msg


def test_find_lines_caches_same_intent(auth_client, stub_completion):
    _seed_pool(auth_client)
    write_mod._FIND_LINES_CACHE.clear()
    stub_completion['result'] = {'picks': [{'idx': 0, 'reason': '思乡'}], 'created': ['x']}
    r1 = auth_client.post('/api/write/find-lines', json={'intent': '思乡'})
    assert r1.get_json()['code'] == 0
    called_once = stub_completion['messages']
    # 第二次相同 intent 应命中缓存，不再调用模型
    r2 = auth_client.post('/api/write/find-lines', json={'intent': '思乡'})
    assert r2.get_json()['code'] == 0
    assert r2.get_json()['data']['local'][0]['title'] == '静夜思'
    # 消息未被覆盖（未再次调用）→ 指针一致
    assert stub_completion['messages'] is called_once
    write_mod._FIND_LINES_CACHE.clear()


def test_find_lines_rejects_bad_idx(auth_client, stub_completion):
    _seed_pool(auth_client)
    write_mod._FIND_LINES_CACHE.clear()
    stub_completion['result'] = {
        'picks': [{'idx': 999, 'reason': '越界'}, {'idx': -1, 'reason': '负索引'}],
        'created': ['原创句。'],
    }
    r = auth_client.post('/api/write/find-lines', json={'intent': '夜空'})
    data = r.get_json()['data']
    assert data['local'] == []
    assert data['created'] == ['原创句。']


def test_find_lines_requires_intent(auth_client):
    r = auth_client.post('/api/write/find-lines', json={'intent': ''})
    assert r.get_json()['code'] != 0