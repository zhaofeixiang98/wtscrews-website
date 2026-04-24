#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import re
import sys
from datetime import datetime
from admin_auth import is_request_authenticated

sys.stdout.write("Content-Type: application/json; charset=utf-8\r\n\r\n")
sys.stdout.flush()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
LANGS = ['en', 'ar', 'de', 'es', 'fr', 'id', 'ja', 'ko', 'zh']
TITLE_RE = re.compile(r'<title>(.*?)</title>', re.IGNORECASE | re.DOTALL)
SLUG_RE = re.compile(r'^[a-z0-9][a-z0-9\-]*$')


def respond(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()
    sys.exit(0)


if not is_request_authenticated():
    respond({'success': False, 'error': 'unauthorized'})


def read_title(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            head = f.read(8192)
        m = TITLE_RE.search(head)
        if not m:
            return ''
        title = re.sub(r'\s+', ' ', m.group(1)).strip()
        return title
    except Exception:
        return ''


def file_mtime(path):
    try:
        return os.path.getmtime(path)
    except Exception:
        return 0


items = []

# A) /pags/{lang}/landing/{slug}.html
folder_names = set()
for lang in LANGS:
    folder_dir = os.path.join(BASE_DIR, 'pags', lang, 'landing')
    if not os.path.isdir(folder_dir):
        continue
    for name in os.listdir(folder_dir):
        if name.endswith('.html'):
            folder_names.add(name)

for name in sorted(folder_names):
    slug = name[:-5]
    if not SLUG_RE.match(slug):
        continue
    lang_paths = {}
    available_langs = []
    latest_mtime = 0
    title = ''
    for lang in LANGS:
        p = os.path.join(BASE_DIR, 'pags', lang, 'landing', name)
        if not os.path.exists(p):
            continue
        available_langs.append(lang)
        latest_mtime = max(latest_mtime, file_mtime(p))
        lang_paths[lang] = f'/pags/{lang}/landing/{name}'
        if not title:
            title = read_title(p)
    if not available_langs:
        continue
    items.append({
        'id': f'folder:{slug}',
        'kind': 'folder',
        'slug': slug,
        'title': title or slug,
        'langs': available_langs,
        'urls': lang_paths,
        'preview_url': lang_paths.get('zh') or lang_paths.get('en') or next(iter(lang_paths.values())),
        'updated_at': datetime.fromtimestamp(latest_mtime).isoformat() if latest_mtime else '',
        'updated_ts': latest_mtime,
    })

# B) /pags/{lang}/landing-*.html
root_names = set()
for lang in LANGS:
    root_dir = os.path.join(BASE_DIR, 'pags', lang)
    if not os.path.isdir(root_dir):
        continue
    for name in os.listdir(root_dir):
        if name.startswith('landing-') and name.endswith('.html'):
            root_names.add(name)

for name in sorted(root_names):
    slug = name[:-5]
    if not SLUG_RE.match(slug):
        continue
    lang_paths = {}
    available_langs = []
    latest_mtime = 0
    title = ''
    for lang in LANGS:
        p = os.path.join(BASE_DIR, 'pags', lang, name)
        if not os.path.exists(p):
            continue
        available_langs.append(lang)
        latest_mtime = max(latest_mtime, file_mtime(p))
        lang_paths[lang] = f'/pags/{lang}/{name}'
        if not title:
            title = read_title(p)
    if not available_langs:
        continue
    items.append({
        'id': f'root:{slug}',
        'kind': 'root',
        'slug': slug,
        'title': title or slug,
        'langs': available_langs,
        'urls': lang_paths,
        'preview_url': lang_paths.get('zh') or lang_paths.get('en') or next(iter(lang_paths.values())),
        'updated_at': datetime.fromtimestamp(latest_mtime).isoformat() if latest_mtime else '',
        'updated_ts': latest_mtime,
    })

items.sort(key=lambda x: x.get('updated_ts', 0), reverse=True)
respond({'success': True, 'items': items})
