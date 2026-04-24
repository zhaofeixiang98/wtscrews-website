#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys
from urllib.parse import parse_qs

from admin_auth import (
    check_password,
    create_session,
    is_request_authenticated,
    make_clear_cookie_header,
    make_set_cookie_header,
    parse_cookie_token,
    revoke_session,
)


def parse_form():
    method = (os.environ.get('REQUEST_METHOD') or 'GET').upper()
    if method == 'POST':
        cl = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
        raw = sys.stdin.buffer.read(cl).decode('utf-8', errors='replace') if cl > 0 else ''
        form = parse_qs(raw, keep_blank_values=True)
    else:
        form = parse_qs(os.environ.get('QUERY_STRING', ''), keep_blank_values=True)

    def g(key, default=''):
        vals = form.get(key, [default])
        return (vals[0] if vals else default).strip()

    return method, g


def send_json(obj, set_cookie=None, status_line=None):
    if status_line:
        sys.stdout.write(status_line + "\r\n")
    if set_cookie:
        sys.stdout.write("Set-Cookie: " + set_cookie + "\r\n")
    sys.stdout.write("Content-Type: application/json; charset=utf-8\r\n\r\n")
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()
    sys.exit(0)


def main():
    try:
        method, g = parse_form()
    except Exception as exc:
        send_json({'success': False, 'error': f'parse error: {exc}'}, status_line='Status: 400 Bad Request')

    action = (g('action', 'status') or 'status').lower()

    if action == 'status':
        ok = is_request_authenticated()
        send_json({'success': True, 'authenticated': ok})

    if action == 'login':
        if method != 'POST':
            send_json({'success': False, 'error': 'POST required'}, status_line='Status: 405 Method Not Allowed')
        password = g('password', '')
        if not check_password(password):
            send_json({'success': False, 'error': '密码错误'}, status_line='Status: 401 Unauthorized')
        token, _ = create_session()
        send_json({'success': True, 'authenticated': True}, set_cookie=make_set_cookie_header(token))

    if action == 'logout':
        token = parse_cookie_token()
        if token:
            revoke_session(token)
        send_json({'success': True}, set_cookie=make_clear_cookie_header())

    send_json({'success': False, 'error': 'unknown action'}, status_line='Status: 400 Bad Request')


if __name__ == '__main__':
    main()
