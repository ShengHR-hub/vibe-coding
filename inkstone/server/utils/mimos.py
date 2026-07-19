import requests
import json
from config import Config


def _headers():
    return {
        'x-api-key': Config.MIMO_API_KEY,
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json'
    }


def _build_body(messages, temperature=0.7, max_tokens=2048):
    """Convert OpenAI-format messages to Anthropic format."""
    system = None
    user_assistant = []
    for m in messages:
        role = m.get('role', 'user')
        content = m.get('content', '')
        if role == 'system':
            system = content
        elif role in ('user', 'assistant'):
            user_assistant.append({'role': role, 'content': content})
    body = {
        'model': Config.MIMO_MODEL,
        'messages': user_assistant,
        'max_tokens': max_tokens,
        'temperature': temperature,
        'thinking': {'type': 'disabled'},
    }
    if system:
        body['system'] = system
    return body


def chat_completion(messages, temperature=0.7, max_tokens=2048):
    """非流式调用 MiMo API (Anthropic 格式)"""
    resp = requests.post(
        f'{Config.MIMO_BASE_URL}/v1/messages',
        headers=_headers(),
        json=_build_body(messages, temperature, max_tokens),
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    # Extract text from Anthropic response content blocks
    text_parts = []
    for block in data.get('content', []):
        if block.get('type') == 'text':
            text_parts.append(block.get('text', ''))
    return '\n'.join(text_parts)


def chat_completion_stream(messages, temperature=0.7, max_tokens=2048):
    """流式调用 MiMo API，返回生成器逐块产出文本"""
    resp = requests.post(
        f'{Config.MIMO_BASE_URL}/v1/messages',
        headers=_headers(),
        json={**_build_body(messages, temperature, max_tokens), 'stream': True},
        timeout=120,
        stream=True,
    )
    resp.raise_for_status()
    resp.encoding = 'utf-8'
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith('data:'):
            chunk = line[5:].strip()
            if not chunk:
                continue
            try:
                obj = json.loads(chunk)
            except json.JSONDecodeError:
                continue
            if obj.get('type') == 'content_block_delta':
                delta = obj.get('delta', {})
                if delta.get('type') == 'text_delta':
                    text = delta.get('text', '')
                    if text:
                        yield text
            elif obj.get('type') == 'message_stop':
                break
