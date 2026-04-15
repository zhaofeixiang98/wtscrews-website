#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys
import time
from urllib import request as urlrequest
from urllib import error as urlerror

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
ENV_FILES = [
    os.path.join(BASE_DIR, '.translation-env'),
    os.path.join(BASE_DIR, '.env.translation'),
]
_loaded = False

sys.stdout.write('Content-Type: application/json; charset=utf-8\r\n\r\n')
sys.stdout.flush()


def respond(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()
    sys.exit(0)


def load_env_files():
    global _loaded
    if _loaded:
        return
    _loaded = True

    for env_path in ENV_FILES:
        if not os.path.exists(env_path):
            continue

        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            continue

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue

            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]

            os.environ.setdefault(key, value)


def pick_api_key():
    load_env_files()
    return (
        os.environ.get('WT_TRANSLATE_API_KEY', '').strip()
        or os.environ.get('DEEPSEEK_API_KEY', '').strip()
        or os.environ.get('OPENAI_API_KEY', '').strip()
    )


def pick_api_url():
    load_env_files()
    explicit_url = (
        os.environ.get('WT_TRANSLATE_API_URL', '').strip()
        or os.environ.get('DEEPSEEK_API_URL', '').strip()
        or os.environ.get('OPENAI_API_URL', '').strip()
    )
    if explicit_url:
        return explicit_url

    base_url = (
        os.environ.get('WT_TRANSLATE_API_BASE', '').strip()
        or os.environ.get('DEEPSEEK_API_BASE', '').strip()
        or os.environ.get('OPENAI_BASE_URL', '').strip()
    )
    if base_url:
        return base_url.rstrip('/') + '/chat/completions'

    if os.environ.get('DEEPSEEK_API_KEY', '').strip():
        return 'https://api.deepseek.com/chat/completions'

    if os.environ.get('OPENAI_API_KEY', '').strip():
        return 'https://api.openai.com/v1/chat/completions'

    return ''


def pick_model():
    load_env_files()
    return (
        os.environ.get('WT_TRANSLATE_MODEL', '').strip()
        or os.environ.get('DEEPSEEK_MODEL', '').strip()
        or os.environ.get('OPENAI_MODEL', '').strip()
        or ('deepseek-chat' if os.environ.get('DEEPSEEK_API_KEY', '').strip() else '')
        or 'gpt-4o-mini'
    )


def detect_provider(api_url):
    url = (api_url or '').lower()
    if 'deepseek' in url or os.environ.get('DEEPSEEK_API_KEY', '').strip():
        return 'DeepSeek'
    if 'openai' in url or os.environ.get('OPENAI_API_KEY', '').strip():
        return 'OpenAI-compatible'
    return 'Custom OpenAI-compatible'


def detect_source():
    for env_path in ENV_FILES:
        if os.path.exists(env_path):
            return os.path.basename(env_path)
    return 'process-env'


api_key = pick_api_key()
api_url = pick_api_url()
model = pick_model()

if not api_key or not api_url:
    respond({
        'success': False,
        'provider': detect_provider(api_url),
        'model': model,
        'configSource': detect_source(),
        'error': '未检测到翻译接口配置',
    })

payload = {
    'model': model,
    'temperature': 0,
    'max_tokens': 12,
    'messages': [
        {'role': 'system', 'content': 'Return the single word OK.'},
        {'role': 'user', 'content': 'Health check'},
    ],
}

request_obj = urlrequest.Request(
    api_url,
    data=json.dumps(payload).encode('utf-8'),
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    },
    method='POST',
)

started = time.time()

try:
    with urlrequest.urlopen(request_obj, timeout=30) as resp:
        raw_resp = resp.read().decode('utf-8', errors='replace')
    elapsed_ms = int((time.time() - started) * 1000)
except urlerror.HTTPError as exc:
    detail = exc.read().decode('utf-8', errors='replace')
    respond({
        'success': False,
        'provider': detect_provider(api_url),
        'model': model,
        'apiUrl': api_url,
        'configSource': detect_source(),
        'error': f'HTTP {exc.code}: {detail[:240]}',
    })
except Exception as exc:
    respond({
        'success': False,
        'provider': detect_provider(api_url),
        'model': model,
        'apiUrl': api_url,
        'configSource': detect_source(),
        'error': str(exc),
    })

try:
    data = json.loads(raw_resp)
    content = data['choices'][0]['message']['content'].strip()
except Exception as exc:
    respond({
        'success': False,
        'provider': detect_provider(api_url),
        'model': model,
        'apiUrl': api_url,
        'configSource': detect_source(),
        'error': f'响应解析失败: {exc}',
    })

respond({
    'success': True,
    'provider': detect_provider(api_url),
    'model': model,
    'apiUrl': api_url,
    'configSource': detect_source(),
    'latencyMs': elapsed_ms,
    'reply': content[:80],
})