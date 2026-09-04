"""多 Provider 网关：解析与协议纯函数（无网络）。"""
import config as cfg_mod
from utils import mimos


def test_openai_body():
    body = mimos._openai_body(
        [{'role': 'system', 'content': 's'}, {'role': 'user', 'content': 'u'}],
        model='qwen-turbo', temperature=0.5, max_tokens=100, stream=False,
    )
    assert body['model'] == 'qwen-turbo'
    assert body['max_tokens'] == 100
    assert len(body['messages']) == 2
    assert body['messages'][0]['role'] == 'system'


def test_parse_openai_message():
    assert mimos._parse_openai_message({'choices': [{'message': {'content': 'hi'}}]}) == 'hi'
    assert mimos._parse_openai_message({'choices': [{'message': {'content': [{'text': 'a'}, {'text': 'b'}]}}]}) == 'a\nb'
    assert mimos._parse_openai_message({}) == ''


def test_openai_stream_text():
    assert mimos._openai_stream_text({'choices': [{'delta': {'content': 'x'}}]}) == 'x'
    assert mimos._openai_stream_text({'choices': [{'delta': {}}]}) == ''
    assert mimos._openai_stream_text({'choices': []}) == ''


def test_openai_body_glm_thinking_auto(monkeypatch):
    # bigmodel 域默认自动 thinking=enabled
    monkeypatch.setattr(cfg_mod.Config, 'AI_THINKING', '')
    body = mimos._openai_body([{'role': 'user', 'content': 'u'}], 'glm-4.7-flash', 0.7, 100,
                              base='https://open.bigmodel.cn/api/paas/v4')
    assert body.get('thinking') == {'type': 'enabled'}
    # 非 bigmodel（如百炼）不加 thinking
    body2 = mimos._openai_body([{'role': 'user', 'content': 'u'}], 'qwen3.8-flash', 0.7, 100,
                               base='https://ws.example.aliyuncs.com/compatible-mode/v1')
    assert 'thinking' not in body2
    # 显式 disabled 可覆盖
    monkeypatch.setattr(cfg_mod.Config, 'AI_THINKING', 'disabled')
    body3 = mimos._openai_body([{'role': 'user', 'content': 'u'}], 'glm-4.7-flash', 0.7, 100,
                               base='https://open.bigmodel.cn/api/paas/v4')
    assert body3.get('thinking') == {'type': 'disabled'}


def test_providers_chain_openai_with_fallback(monkeypatch):
    monkeypatch.setattr(cfg_mod.Config, 'AI_PROVIDER', 'openai')
    monkeypatch.setattr(cfg_mod.Config, 'AI_BASE_URL', 'https://a.example/v1')
    monkeypatch.setattr(cfg_mod.Config, 'AI_API_KEY', 'k1')
    monkeypatch.setattr(cfg_mod.Config, 'AI_MODEL', 'm1')
    monkeypatch.setattr(cfg_mod.Config, 'AI_FALLBACK_ENABLED', '1')
    monkeypatch.setattr(cfg_mod.Config, 'AI_FALLBACK_BASE_URL', 'https://b.example/v1')
    monkeypatch.setattr(cfg_mod.Config, 'AI_FALLBACK_API_KEY', 'k2')
    monkeypatch.setattr(cfg_mod.Config, 'AI_FALLBACK_MODEL', 'm2')
    chain = mimos._providers()
    assert len(chain) == 2
    assert chain[0] == ('openai', 'https://a.example/v1', 'k1', 'm1')
    assert chain[1] == ('openai', 'https://b.example/v1', 'k2', 'm2')


def test_providers_mimo_default(monkeypatch):
    monkeypatch.setattr(cfg_mod.Config, 'AI_PROVIDER', 'mimo')
    monkeypatch.setattr(cfg_mod.Config, 'MIMO_BASE_URL', 'https://mimo.example')
    monkeypatch.setattr(cfg_mod.Config, 'MIMO_API_KEY', 'mk')
    monkeypatch.setattr(cfg_mod.Config, 'MIMO_MODEL', 'mimo-v2.5')
    chain = mimos._providers()
    assert chain[0][0] == 'mimo'
