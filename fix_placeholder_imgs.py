#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复产品页面中 images/image.png 占位符 → 正确的产品图片路径
根据文件名 slug 映射到 pages_zh.json 中对应的 icon 图片
"""
import os, re, json

BASE = os.path.dirname(os.path.abspath(__file__))
PAGS = os.path.join(BASE, 'pags')
LANGS = ['ar', 'de', 'en', 'es', 'fr', 'id', 'ja', 'ko', 'zh']

# 从 pages_zh.json 建立 slug → 图片路径映射
with open(os.path.join(PAGS, 'zh', 'pages_zh.json'), encoding='utf-8') as f:
    data = json.load(f)

# icon 存储为 ../../images/products/... 格式（相对于二级目录）
# 产品页面在 pags/{lang}/products/*.html，相对路径是 ../../../images/...
slug_to_img = {}
for cat in data['products']:
    for item in cat.get('items', []):
        slug = item['slug'].split('/')[-1]          # "hex-bolts"
        icon = item.get('icon', '')                  # "../../images/products/bolts/Hex Bolt0.webp"
        if icon:
            # 从 ../../ 前缀调整为 ../../../（产品详情页比列表页深一级）
            img_path = icon.replace('../../images/', '../../../images/')
            slug_to_img[slug] = img_path

print('Slug → image mappings:', len(slug_to_img))

fixed = 0
for lang in LANGS:
    prods_dir = os.path.join(PAGS, lang, 'products')
    if not os.path.isdir(prods_dir):
        continue
    for fname in os.listdir(prods_dir):
        if not fname.endswith('.html'):
            continue
        slug = fname.replace('.html', '')
        if slug not in slug_to_img:
            continue
        fpath = os.path.join(prods_dir, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        if '../../../images/image.png' not in content and '../../images/image.png' not in content:
            continue
        # 替换占位符
        new_content = content.replace('../../../images/image.png', slug_to_img[slug])
        new_content = new_content.replace('../../images/image.png', slug_to_img[slug].replace('../../../', '../../'))
        if new_content != content:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            fixed += 1
            print(f'  Fixed: {lang}/{fname} → {slug_to_img[slug]}')

print(f'\n✓ Fixed {fixed} files')

# 验证还有多少残留
remaining = 0
for root, dirs, files in os.walk(PAGS):
    for f in files:
        if not f.endswith('.html'):
            continue
        with open(os.path.join(root, f), encoding='utf-8') as fh:
            if 'images/image.png' in fh.read():
                remaining += 1
print(f'  Remaining image.png references: {remaining}')
