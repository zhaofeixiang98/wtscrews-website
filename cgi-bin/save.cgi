#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import re
import sys
from datetime import datetime, timezone
from time import time
from urllib.parse import parse_qs

LANGS = {'en', 'zh', 'ar', 'de', 'es', 'fr', 'id', 'ja', 'ko'}


def send_text(message, status='200 OK'):
    print(f'Status: {status}')
    print('Content-Type: text/plain; charset=utf-8')
    print()
    print(message)
    sys.exit(0)


def redirect(url):
    print('Status: 302 Found')
    print('Location: ' + url)
    print('Content-Type: text/html; charset=utf-8')
    print()
    print('<!doctype html><meta charset="utf-8"><p>Redirecting...</p>')
    sys.exit(0)


def form_data():
    method = (os.environ.get('REQUEST_METHOD') or 'GET').upper()
    if method == 'POST':
        length = int(os.environ.get('CONTENT_LENGTH', '0') or 0)
        raw = sys.stdin.buffer.read(length).decode('utf-8', errors='replace') if length > 0 else ''
    else:
        raw = os.environ.get('QUERY_STRING', '')
    parsed = parse_qs(raw, keep_blank_values=True)

    def get(key, default=''):
        vals = parsed.get(key, [default])
        return (vals[0] if vals else default).strip()

    return get


def client_ip_details():
    candidates = [
        ('HTTP_CF_CONNECTING_IP', 'cf-connecting-ip'),
        ('HTTP_X_REAL_IP', 'x-real-ip'),
        ('HTTP_X_FORWARDED_FOR', 'x-forwarded-for'),
        ('REMOTE_ADDR', 'remote-addr'),
    ]
    ip_re = re.compile(r'^[0-9a-fA-F:.]+$')
    for key, label in candidates:
        raw = (os.environ.get(key) or '').strip()
        if not raw:
            continue
        parts = [p.strip() for p in raw.split(',')] if key == 'HTTP_X_FORWARDED_FOR' else [raw]
        for part in parts:
            if part and ip_re.match(part):
                return {
                    'ip': part,
                    'ip_source': label,
                    'ip_raw': raw,
                    'ip_raw_remote_addr': os.environ.get('REMOTE_ADDR', ''),
                }
    return {'ip': '127.0.0.1', 'ip_source': 'fallback', 'ip_raw': '', 'ip_raw_remote_addr': os.environ.get('REMOTE_ADDR', '')}


def choose_save_dir(project_root):
    candidates = [
        '/var/www/users/',
        '/var/www/html/users/',
        os.path.join(project_root, 'users'),
    ]
    for folder in candidates:
        try:
            os.makedirs(folder, exist_ok=True)
            if os.path.isdir(folder) and os.access(folder, os.W_OK):
                return folder
        except Exception:
            continue
    return ''


get = form_data()
lang = get('lang', 'en')
if lang not in LANGS:
    lang = 'en'

# Honeypot bots get a silent success so they do not learn the filter.
if get('website'):
    redirect(f'/pags/{lang}/success.html')

name = get('name')
email = get('email')
company = get('company')
phone = get('phone')
subject = get('subject')
message = get('message')

if not name or not email or not message:
    redirect(f'/pags/{lang}/contact.html?error=1')
if '@' not in email or '.' not in email.rsplit('@', 1)[-1]:
    redirect(f'/pags/{lang}/contact.html?error=2')

ip_info = client_ip_details()
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
save_dir = choose_save_dir(project_root)
if not save_dir:
    send_text('Submission could not be saved. Please contact us by WhatsApp or email.', '500 Internal Server Error')

throttle_file = os.path.join(save_dir, '.last_submits.json')
try:
    with open(throttle_file, 'r', encoding='utf-8') as f:
        last_submits = json.load(f)
        if not isinstance(last_submits, dict):
            last_submits = {}
except Exception:
    last_submits = {}

now_ts = time()
key_ip = 'ip:' + ip_info['ip']
key_email = 'email:' + email.lower()
if now_ts - float(last_submits.get(key_ip, 0) or 0) < 30 or now_ts - float(last_submits.get(key_email, 0) or 0) < 30:
    send_text('Please wait 30 seconds before submitting again.', '429 Too Many Requests')

tracking_keys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'utm_id', 'gclid', 'gbraid', 'wbraid', 'fbclid', 'landing_page', 'page_path', 'page_title', 'referrer']
tracking = {key: get(key) for key in tracking_keys}
record = {
    'name': name,
    'email': email,
    'company': company,
    'phone': phone,
    'subject': subject,
    'message': message,
    'ip': ip_info['ip'],
    'ip_source': ip_info['ip_source'],
    'ip_raw': ip_info['ip_raw'],
    'ip_raw_remote_addr': ip_info['ip_raw_remote_addr'],
    'tracking': tracking,
    'lang': lang,
    'time': datetime.now(timezone.utc).isoformat(),
}

safe_email = re.sub(r'[^a-zA-Z0-9@._-]', '_', email).replace('@', '_at_').replace('.', '_') or 'noemail'
safe_time = datetime.now(timezone.utc).isoformat().replace(':', '-')
filename = os.path.join(save_dir, f'{safe_time}_{safe_email}.json')
try:
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    last_submits[key_ip] = now_ts
    last_submits[key_email] = now_ts
    with open(throttle_file, 'w', encoding='utf-8') as f:
        json.dump(last_submits, f, ensure_ascii=False, indent=2)
except Exception:
    send_text('Submission could not be saved. Please contact us by WhatsApp or email.', '500 Internal Server Error')

redirect(f'/pags/{lang}/success.html')
