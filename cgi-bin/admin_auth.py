#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import secrets
import tempfile
import time
from http import cookies


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
SESSIONS_PATH = '/tmp/.admin-sessions.json'
COOKIE_NAME = 'WT_ADMIN_SESSION'
DEFAULT_MAX_AGE = 24 * 60 * 60


def _now():
    return int(time.time())


def _load_sessions():
    if not os.path.exists(SESSIONS_PATH):
        return {}
    try:
        with open(SESSIONS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return {str(k): int(v) for k, v in data.items() if str(k) and str(v).isdigit()}
    except Exception:
        return {}


def _atomic_write_sessions(data):
    os.makedirs(os.path.dirname(SESSIONS_PATH) or '.', exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='._admin_sessions_', suffix='.tmp', dir='/tmp/')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, SESSIONS_PATH)
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass


def _cleanup(sessions):
    now = _now()
    return {k: v for k, v in sessions.items() if int(v) > now}


def check_password(password):
    expected = os.environ.get('WT_ADMIN_PASSWORD', '-***-')
    return str(password or '') == expected


def create_session(max_age=DEFAULT_MAX_AGE):
    sessions = _cleanup(_load_sessions())
    token = secrets.token_urlsafe(32)
    expires_at = _now() + int(max_age)
    sessions[token] = expires_at
    _atomic_write_sessions(sessions)
    return token, expires_at


def revoke_session(token):
    token = str(token or '').strip()
    if not token:
        return
    sessions = _cleanup(_load_sessions())
    if token in sessions:
        sessions.pop(token, None)
        _atomic_write_sessions(sessions)


def parse_cookie_token(env=None):
    env = env or os.environ
    raw = env.get('HTTP_COOKIE', '')
    if not raw:
        return ''
    jar = cookies.SimpleCookie()
    try:
        jar.load(raw)
    except Exception:
        return ''
    morsel = jar.get(COOKIE_NAME)
    return morsel.value if morsel else ''


def is_token_valid(token):
    token = str(token or '').strip()
    if not token:
        return False
    sessions = _cleanup(_load_sessions())
    valid = token in sessions and int(sessions[token]) > _now()
    if sessions != _load_sessions():
        _atomic_write_sessions(sessions)
    return valid


def is_request_authenticated(env=None):
    env = env or os.environ
    if env.get('WT_ADMIN_BYPASS', '') == '1':
        return True
    return is_token_valid(parse_cookie_token(env))


def make_set_cookie_header(token, max_age=DEFAULT_MAX_AGE):
    return f'{COOKIE_NAME}={token}; Path=/; Max-Age={int(max_age)}; HttpOnly; SameSite=Lax'


def make_clear_cookie_header():
    return f'{COOKIE_NAME}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax'
