#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json, re
from urllib.parse import parse_qs

sys.stdout.write("Content-Type: application/json; charset=utf-8\r\n\r\n")
sys.stdout.flush()

def respond(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()
    sys.exit(0)

try:
    cl  = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    raw = sys.stdin.buffer.read(cl).decode('utf-8', errors='replace') if cl > 0 else ''
    form = parse_qs(raw, keep_blank_values=True)
    def g(k, d=''):
        v = form.get(k, [d])
        return (v[0] if v else d).strip()
except Exception as e:
    respond({'success': False, 'error': 'Parse error: ' + str(e)})

slugs_raw = g('slugs')
if not slugs_raw:
    respond({'success': False, 'error': '未指定要删除的文章'})

slugs = [s.strip() for s in slugs_raw.split(',') if s.strip()]
if not slugs:
    respond({'success': False, 'error': '无效的 slug 列表'})

delete_image = g('delete_image', '0') == '1'

LANGS = ['en', 'ar', 'de', 'es', 'fr', 'id', 'ja', 'ko', 'zh']

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir   = os.path.abspath(os.path.join(script_dir, '..'))

# ── Collect image paths from EN JSON before deletion ─────────────────────────
images_to_delete = {}   # {news_slug: filename}
if delete_image:
    en_json = os.path.join(base_dir, 'pags', 'en', 'pages_en.json')
    if os.path.exists(en_json):
        try:
            with open(en_json, 'r', encoding='utf-8') as f:
                en_data = json.load(f)
            for item in en_data.get('news', []):
                if item.get('slug') in slugs:
                    icon = item.get('icon', '')
                    if 'images/news/' in icon:
                        fname = icon.split('images/news/')[-1].strip('/')
                        images_to_delete[item['slug']] = fname
        except Exception:
            pass

deleted = []
errors  = []

for news_slug in slugs:
    if '/' in news_slug:
        file_slug = news_slug.split('/', 1)[1]
    else:
        file_slug = news_slug

    if not re.match(r'^[a-z0-9][a-z0-9\-]*$', file_slug):
        errors.append(f'跳过非法 slug: {news_slug}')
        continue

    slug_deleted = False
    for lang in LANGS:
        html_path = os.path.join(base_dir, 'pags', lang, 'news', file_slug + '.html')
        if os.path.exists(html_path):
            try:
                os.remove(html_path)
                slug_deleted = True
            except Exception as e:
                errors.append(f'{lang}/{file_slug}.html 删除失败: {e}')

        json_path = os.path.join(base_dir, 'pags', lang, f'pages_{lang}.json')
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                before = len(data.get('news', []))
                data['news'] = [n for n in data.get('news', []) if n.get('slug') != news_slug]
                if len(data['news']) < before:
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    slug_deleted = True
            except Exception as e:
                errors.append(f'{lang}/pages_{lang}.json 更新失败: {e}')

    if slug_deleted:
        deleted.append(news_slug)

# ── Regenerate static HTML ───────────────────────────────────────────────────
import subprocess
subprocess.run(['python3', os.path.join(base_dir, 'render_list_pages.py')], capture_output=True)

# ── Delete associated images ──────────────────────────────────────────────────
deleted_images = []
if delete_image:
    img_dir = os.path.join(base_dir, 'images', 'news')
    for news_slug, fname in images_to_delete.items():
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_\-\.]+\.(jpg|jpeg|png|gif|webp|svg)$', fname, re.IGNORECASE):
            errors.append(f'跳过非法图片文件名: {fname}')
            continue
        img_path = os.path.join(img_dir, fname)
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
                deleted_images.append(fname)
            except Exception as e:
                errors.append(f'图片 {fname} 删除失败: {e}')

respond({
    'success':        len(deleted) > 0,
    'deleted':        deleted,
    'deleted_images': deleted_images,
    'errors':         errors,
})
