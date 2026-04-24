#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import subprocess
import re
import sys
from urllib.parse import parse_qs
from json_store import update_pages_json, JsonStoreError
from admin_auth import is_request_authenticated

sys.stdout.write("Content-Type: application/json; charset=utf-8\r\n\r\n")
sys.stdout.flush()


def respond(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()
    sys.exit(0)


if not is_request_authenticated():
    respond({'success': False, 'error': 'unauthorized'})


try:
    cl = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    raw = sys.stdin.buffer.read(cl).decode('utf-8', errors='replace') if cl > 0 else ''
    form = parse_qs(raw, keep_blank_values=True)

    def g(key, default=''):
        values = form.get(key, [default])
        return (values[0] if values else default).strip()
except Exception as exc:
    respond({'success': False, 'error': 'Parse error: ' + str(exc)})


slugs_raw = g('slugs')
if not slugs_raw:
    respond({'success': False, 'error': '未指定要删除的产品'})

requested_slugs = [item.strip() for item in slugs_raw.split(',') if item.strip()]
if not requested_slugs:
    respond({'success': False, 'error': '无效的 slug 列表'})

LANGS = ['en', 'ar', 'de', 'es', 'fr', 'id', 'ja', 'ko', 'zh']
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

deleted = []
errors = []


def normalize_slug(raw_slug):
    raw_slug = (raw_slug or '').strip()
    if '/' in raw_slug:
        prefix, suffix = raw_slug.split('/', 1)
        if prefix != 'products':
            return None, None
        file_slug = suffix
    else:
        file_slug = raw_slug
    if not re.match(r'^[a-z0-9][a-z0-9\-]*$', file_slug):
        return None, None
    return file_slug, 'products/' + file_slug


def delete_from_json(json_path, full_slug):
    if not os.path.exists(json_path):
        return False

    changed = {'value': False}
    try:
        def mutator(data):
            new_categories = []
            local_changed = False
            for category in data.get('products', []):
                original_items = list(category.get('items', []))
                kept_items = [item for item in original_items if item.get('slug') != full_slug]
                if len(kept_items) != len(original_items):
                    local_changed = True
                if kept_items:
                    category['items'] = kept_items
                    new_categories.append(category)
                elif original_items:
                    local_changed = True
            data['products'] = new_categories
            changed['value'] = local_changed
            return data

        update_pages_json(json_path, mutator)
    except JsonStoreError as exc:
        errors.append(f'{os.path.basename(json_path)} 更新失败: {exc}')
        return False
    except Exception as exc:
        errors.append(f'{os.path.basename(json_path)} 写入失败: {exc}')
        return False
    return changed['value']


for requested_slug in requested_slugs:
    file_slug, full_slug = normalize_slug(requested_slug)
    if not file_slug:
        errors.append(f'跳过非法 slug: {requested_slug}')
        continue

    removed_anything = False

    for lang in LANGS:
        html_path = os.path.join(BASE_DIR, 'pags', lang, 'products', file_slug + '.html')
        if os.path.exists(html_path):
            try:
                os.remove(html_path)
                removed_anything = True
            except Exception as exc:
                errors.append(f'{lang}/{file_slug}.html 删除失败: {exc}')

        json_path = os.path.join(BASE_DIR, 'pags', lang, f'pages_{lang}.json')
        if delete_from_json(json_path, full_slug):
            removed_anything = True

    if removed_anything:
        deleted.append(full_slug)

# Regenerate static HTML
subprocess.run(['python3', os.path.join(BASE_DIR, 'render_list_pages.py')], capture_output=True)

respond({
    'success': len(deleted) > 0,
    'deleted': deleted,
    'errors': errors,
})
