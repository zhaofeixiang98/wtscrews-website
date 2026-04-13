#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新 HTML 中的图片引用，使用已优化的 WebP 版本。

1. images/abouts/*.png  → images/abouts/*.webp
2. images/logo.jpg      → images/logo_sm.webp  (仅 <img> 标签, 不动 og:image)
3. related-card-image 内的 products/*.webp → products/*_sm.webp
"""
import os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))
PAGS = os.path.join(BASE, 'pags')

# ── 已存在的 _sm.webp 文件集（用于验证替换安全性）─────────────────────────────
sm_files = set()
for root, dirs, files in os.walk(os.path.join(BASE, 'images', 'products')):
    for f in files:
        if f.endswith('_sm.webp'):
            sm_files.add(f)

# ── 已存在的 abouts webp 文件集 ────────────────────────────────────────────────
abouts_webp = set()
abouts_dir = os.path.join(BASE, 'images', 'abouts')
for f in os.listdir(abouts_dir):
    if f.endswith('.webp'):
        abouts_webp.add(f)

def abouts_png_to_webp(html: str) -> str:
    """把所有 images/abouts/NAME.png 的 src 引用改成 .webp"""
    def replacer(m):
        path = m.group(0)
        # 取文件名（URL编码版本）
        fname_enc = re.search(r'abouts/([^"\']+)\.png', path)
        if not fname_enc:
            return path
        # 解码空格等
        import urllib.parse
        fname = urllib.parse.unquote(fname_enc.group(1))
        webp_name = fname + '.webp'
        if webp_name in abouts_webp:
            return path.replace('.png', '.webp')
        return path
    # 匹配 src 中 abouts/xxx.png 的引用
    return re.sub(r'(?:(?:\.\./)+)images/abouts/[^"\']+\.png', replacer, html)

def logo_to_sm(html: str) -> str:
    """将 <img src="...logo.jpg"> 替换成 logo_sm.webp（不改 og:image）"""
    # 只替换 <img ... src="...logo.jpg"> 里的 logo.jpg
    return re.sub(
        r'(<img\b[^>]*\bsrc="([^"]*?))(logo\.jpg)("[^>]*>)',
        lambda m: m.group(1) + 'logo_sm.webp' + m.group(4),
        html
    )

def product_cards_to_sm(html: str) -> str:
    """
    在 <div class="related-card-image"> 或 news related 块内，
    把 products/CATEGORY/NAME.webp → products/CATEGORY/NAME_sm.webp
    """
    # 找到所有 related-card-image div 内容，替换其中的 .webp 引用
    def section_replacer(m):
        inner = m.group(0)
        def img_replacer(im):
            src = im.group(0)
            # 提取文件名
            name_m = re.search(r'/([^/]+)\.webp"', src)
            if not name_m:
                return src
            name = name_m.group(1)
            sm_name = name + '_sm.webp'
            if sm_name in sm_files:
                return src.replace(name + '.webp"', sm_name + '"')
            return src
        return re.sub(r'<img\b[^>]+images/products/[^>]+>', img_replacer, inner)
    
    # 匹配 related-card-image 整个 div（假设是 <div ...>...</div> 单行或多行较短）
    html = re.sub(
        r'<div class="related-card-image">.*?</div>',
        section_replacer,
        html,
        flags=re.DOTALL
    )
    return html

# ── 遍历所有 HTML ──────────────────────────────────────────────────────────────
changed = []
skipped = 0

for root, dirs, files in os.walk(PAGS):
    for fname in files:
        if not fname.endswith('.html'):
            continue
        fpath = os.path.join(root, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            original = f.read()
        
        html = original
        html = abouts_png_to_webp(html)
        html = logo_to_sm(html)
        html = product_cards_to_sm(html)
        
        if html != original:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(html)
            changed.append(os.path.relpath(fpath, BASE))
        else:
            skipped += 1

print(f'✓ Updated: {len(changed)} files')
print(f'  Skipped (no change): {skipped} files')
if changed:
    print('\nChanged files:')
    for p in sorted(changed):
        print(f'  {p}')
