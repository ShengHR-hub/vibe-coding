"""写作 AI 端点输入上限与配额测试（不触发真实 MiMo 调用）。

覆盖：
- W1b: diagnose/summary 超长输入被拒绝（在限流/AI 调用前拦截，无外部请求）；
- W1a: AI 端点按用户限流与每日配额（monkeypatch chat_completion，避免真实调用）。
"""
import config as cfg_mod
from routes import write as write_mod
from utils import helpers


def _post(client, path, payload):
    return client.post(path, json=payload)


# ---------- W1b：输入上限 ----------

def test_diagnose_too_short(auth_client):
    r = _post(auth_client, '/api/write/diagnose', {'content': '太短了'})
    assert r.get_json()['code'] != 0
    assert '太短' in r.get_json()['msg']


def test_diagnose_over_cap(auth_client):
    long_text = '好' * 20001
    r = _post(auth_client, '/api/write/diagnose', {'content': long_text})
    data = r.get_json()
    assert data['code'] != 0
    assert '过长' in data['msg']


def test_summary_over_cap(auth_client):
    long_text = '好' * 30001
    r = _post(auth_client, '/api/write/summary', {'title': '第1章', 'content': long_text})
    data = r.get_json()
    assert data['code'] != 0
    assert '过长' in data['msg']


def test_summary_under_min(auth_client):
    r = _post(auth_client, '/api/write/summary', {'title': '第1章', 'content': '好' * 99})
    data = r.get_json()
    assert data['code'] != 0
    assert '太短' in data['msg']


# ---------- W1a：按用户限流 ----------

def _reset_quota(monkeypatch, per_min=3, daily=5):
    """清空配额计数并把阈值调小，替换真实 AI 调用为 stub。"""
    helpers._ai_minute.clear()
    helpers._ai_daily.clear()
    helpers._ai_day.clear()
    monkeypatch.setattr(cfg_mod.Config, 'AI_RATE_PER_MIN', per_min)
    monkeypatch.setattr(cfg_mod.Config, 'AI_DAILY_LIMIT', daily)
    monkeypatch.setattr(write_mod, 'chat_completion', lambda messages: 'stub-result')
    monkeypatch.setattr(write_mod, 'log_ai_call', lambda *a, **k: None)


def test_ai_quota_minute_window(auth_client, monkeypatch):
    _reset_quota(monkeypatch, per_min=3, daily=5)
    # 窗口内前 3 次放行（stub，不真实调用）
    for _ in range(3):
        r = _post(auth_client, '/api/write/inspire', {'keywords': '末日 爱情'})
        assert r.get_json()['code'] == 0, r.get_json()
    # 第 4 次被分钟限流拦截
    r = _post(auth_client, '/api/write/inspire', {'keywords': '末日 爱情'})
    data = r.get_json()
    assert data['code'] != 0
    assert '频繁' in data['msg']


def test_ai_quota_daily_limit(auth_client, monkeypatch):
    _reset_quota(monkeypatch, per_min=100, daily=2)
    # 每日上限 2：前 2 次放行，第 3 次被每日上限拦截
    for _ in range(2):
        r = _post(auth_client, '/api/write/inspire', {'keywords': '夜色 城市'})
        assert r.get_json()['code'] == 0, r.get_json()
    r = _post(auth_client, '/api/write/inspire', {'keywords': '夜色 城市'})
    data = r.get_json()
    assert data['code'] != 0
    assert '上限' in data['msg']


def test_invalid_requests_also_consume_quota(auth_client, monkeypatch):
    """配额在进入处理前计数：无效请求同样消耗窗口，防止无效请求滥用打满资源。"""
    _reset_quota(monkeypatch, per_min=2, daily=5)
    # 1) 无效请求（空关键词）：校验失败，但已消耗 1 次配额
    r = _post(auth_client, '/api/write/inspire', {'keywords': ''})
    assert r.get_json()['code'] != 0
    # 2) 第 2 次（有效）放行
    r = _post(auth_client, '/api/write/inspire', {'keywords': '灵感 火花'})
    assert r.get_json()['code'] == 0, r.get_json()
    # 3) 第 3 次达到窗口上限被拦截
    r = _post(auth_client, '/api/write/inspire', {'keywords': '灵感 火花'})
    assert r.get_json()['code'] != 0
    assert '频繁' in r.get_json()['msg']
