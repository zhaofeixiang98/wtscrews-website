#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys
from urllib.parse import quote

sys.stdout.write("Content-Type: application/json; charset=utf-8\r\n\r\n")
sys.stdout.flush()


def respond(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()
    sys.exit(0)


IMG_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(script_dir, '..'))
images_dir = os.path.join(base_dir, 'images')

if not os.path.isdir(images_dir):
    respond({'success': True, 'images': [], 'total': 0})

images = []

try:
    for root, dirnames, filenames in os.walk(images_dir):
        dirnames[:] = [name for name in dirnames if not name.startswith('.')]
        for filename in sorted(filenames):
            if filename.startswith('.'):
                continue
            ext = os.path.splitext(filename)[1].lower()
            if ext not in IMG_EXTS:
                continue

            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, images_dir).replace(os.sep, '/')
            section = rel_path.split('/', 1)[0] if '/' in rel_path else 'root'
            images.append({
                'filename': filename,
                'path': rel_path,
                'section': section,
                'size': os.path.getsize(full_path),
                'url': '/images/' + quote(rel_path, safe='/'),
            })

    images.sort(key=lambda item: item['path'].lower())
    respond({'success': True, 'images': images, 'total': len(images)})
except Exception as exc:
    respond({'success': False, 'error': '读取图片库失败: ' + str(exc)})