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

script_dir   = os.path.dirname(os.path.abspath(__file__))
base_dir     = os.path.abspath(os.path.join(script_dir, '..'))
news_img_dir = os.path.join(base_dir, 'images', 'news')
LANGS        = ['en', 'ar', 'de', 'es', 'fr', 'id', 'ja', 'ko', 'zh']
IMG_EXTS     = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}

action = g('action', 'list')

# ── LIST ─────────────────────────────────────────────────────────────────────
if action == 'list':
    # All image files in /images/news/
    all_images = []
    if os.path.exists(news_img_dir):
        for fname in sorted(os.listdir(news_img_dir)):
            if os.path.splitext(fname)[1].lower() in IMG_EXTS:
                fpath = os.path.join(news_img_dir, fname)
                all_images.append({
                    'filename': fname,
                    'size':     os.path.getsize(fpath),
                })

    # Collect all referenced news image filenames from every JSON
    referenced = set()
    for lang in LANGS:
        json_path = os.path.join(base_dir, 'pags', lang, f'pages_{lang}.json')
        if not os.path.exists(json_path):
            continue
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for item in data.get('news', []):
                icon = item.get('icon', '')
                if 'images/news/' in icon:
                    referenced.add(icon.split('images/news/')[-1].strip('/'))
        except Exception:
            pass

    for img in all_images:
        img['used'] = img['filename'] in referenced

    unused = [i for i in all_images if not i['used']]
    respond({
        'success':      True,
        'images':       all_images,
        'total':        len(all_images),
        'unused_count': len(unused),
    })

# ── DELETE ────────────────────────────────────────────────────────────────────
elif action == 'delete':
    filenames_raw = g('filenames')
    if not filenames_raw:
        respond({'success': False, 'error': '未指定文件名'})

    filenames = [f.strip() for f in filenames_raw.split(',') if f.strip()]
    deleted = []
    errors  = []

    for fname in filenames:
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_\-\.]*\.(jpg|jpeg|png|gif|webp|svg)$', fname, re.IGNORECASE):
            errors.append(f'跳过非法文件名: {fname}')
            continue
        fpath = os.path.join(news_img_dir, fname)
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
                deleted.append(fname)
            except Exception as e:
                errors.append(f'{fname} 删除失败: {str(e)}')
        else:
            errors.append(f'{fname} 不存在')

    respond({'success': len(deleted) > 0, 'deleted': deleted, 'errors': errors})

else:
    respond({'success': False, 'error': '未知操作'})
