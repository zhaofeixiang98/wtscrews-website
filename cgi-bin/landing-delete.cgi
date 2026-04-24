#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import re
import sys
from urllib.parse import parse_qs
from admin_auth import is_request_authenticated

sys.stdout.write("Content-Type: application/json; charset=utf-8\r\n\r\n")
sys.stdout.flush()

LANGS = ['en', 'ar', 'de', 'es', 'fr', 'id', 'ja', 'ko', 'zh']
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
SLUG_RE = re.compile(r'^[a-z0-9][a-z0-9\-]*$')


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


targets_raw = g('slugs')
if not targets_raw:
    respond({'success': False, 'error': '未指定要删除的落地页'})

requested_targets = [item.strip() for item in targets_raw.split(',') if item.strip()]
if not requested_targets:
    respond({'success': False, 'error': '无效的目标列表'})

deleted = []
errors = []

for raw_target in requested_targets:
    if ':' in raw_target:
        kind, slug = raw_target.split(':', 1)
    else:
        kind, slug = 'folder', raw_target
    kind = (kind or '').strip().lower()
    slug = (slug or '').strip()

    if not SLUG_RE.match(slug):
        errors.append(f'跳过非法 slug: {raw_target}')
        continue
    if kind not in {'folder', 'root'}:
        errors.append(f'未知删除类型: {raw_target}')
        continue

    filename = slug + '.html'
    removed_anything = False
    matched_anything = False

    for lang in LANGS:
        if kind == 'folder':
            path = os.path.join(BASE_DIR, 'pags', lang, 'landing', filename)
        else:
            path = os.path.join(BASE_DIR, 'pags', lang, filename)
        if os.path.exists(path):
            matched_anything = True
            try:
                os.remove(path)
                removed_anything = True
            except Exception as exc:
                if isinstance(exc, PermissionError):
                    errors.append(
                        f'{lang}/{filename} 删除失败: 权限不足 ({exc}). '
                        f'请在服务器执行: chown -R www-data:www-data {os.path.join(BASE_DIR, "pags", lang)} '
                        f'并确保目录可写 chmod -R u+rwX,go+rX {os.path.join(BASE_DIR, "pags", lang)}'
                    )
                else:
                    errors.append(f'{lang}/{filename} 删除失败: {exc}')

    if removed_anything:
        deleted.append(f'{kind}:{slug}')
    elif not matched_anything:
        errors.append(f'未找到可删除文件: {kind}:{slug}')

respond({
    'success': len(deleted) > 0,
    'deleted': deleted,
    'errors': errors,
})
