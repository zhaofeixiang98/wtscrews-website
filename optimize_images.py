#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片优化脚本
- abouts/*.png       → *.webp (max 900px wide, quality 82)
- products/**/*.webp → *_sm.webp (400×400, quality 80)  用于列表/卡片
- logo.jpg           → logo_sm.webp (88×88, quality 85)  用于导航
"""
import os, sys
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
IMGS = os.path.join(BASE, 'images')

results = []

def save_webp(src_path, dst_path, max_w=None, max_h=None, quality=82, exact_fit=False):
    """打开图片，按指定尺寸缩放，保存为 WebP。"""
    with Image.open(src_path) as im:
        im = im.convert('RGBA') if im.mode in ('P', 'RGBA') else im.convert('RGB')

        orig_w, orig_h = im.size
        if exact_fit and max_w and max_h:
            im = im.resize((max_w, max_h), Image.LANCZOS)
        elif max_w or max_h:
            if max_w and max_h:
                # thumbnail keeps aspect ratio within box
                im.thumbnail((max_w, max_h), Image.LANCZOS)
            elif max_w:
                ratio = max_w / orig_w
                im = im.resize((max_w, int(orig_h * ratio)), Image.LANCZOS)
            else:
                ratio = max_h / orig_h
                im = im.resize((int(orig_w * ratio), max_h), Image.LANCZOS)

        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        save_kwargs = {'format': 'WEBP', 'quality': quality, 'method': 6}
        # Drop alpha for RGB
        if im.mode == 'RGBA':
            # Composite onto white background for JPG-like appearance
            bg = Image.new('RGB', im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[3])
            im = bg

        im.save(dst_path, **save_kwargs)

        src_kb = os.path.getsize(src_path) // 1024
        dst_kb = os.path.getsize(dst_path) // 1024
        results.append((os.path.relpath(src_path, BASE), os.path.relpath(dst_path, BASE),
                        src_kb, dst_kb))


# ── 1. abouts PNG → WebP (max 900px wide) ────────────────────────────────────
abouts_dir = os.path.join(IMGS, 'abouts')
for fname in sorted(os.listdir(abouts_dir)):
    if not fname.lower().endswith('.png'):
        continue
    src = os.path.join(abouts_dir, fname)
    dst_name = os.path.splitext(fname)[0] + '.webp'
    dst = os.path.join(abouts_dir, dst_name)
    if os.path.exists(dst):
        print(f'  [SKIP] already exists: {dst_name}')
        continue
    save_webp(src, dst, max_w=900, quality=82)

# ── 2. products webp (1500x1500) → _sm.webp (max 400x400) ──────────────────
products_dir = os.path.join(IMGS, 'products')
for root, dirs, files in os.walk(products_dir):
    for fname in sorted(files):
        if not fname.lower().endswith('.webp'):
            continue
        if fname.endswith('_sm.webp'):
            continue
        src = os.path.join(root, fname)
        base_name = os.path.splitext(fname)[0]
        dst = os.path.join(root, base_name + '_sm.webp')
        if os.path.exists(dst):
            print(f'  [SKIP] already exists: {os.path.relpath(dst, BASE)}')
            continue
        with Image.open(src) as im:
            w, h = im.size
        if w <= 420 and h <= 420:
            print(f'  [SKIP] already small enough: {fname} ({w}x{h})')
            continue
        save_webp(src, dst, max_w=400, max_h=400, quality=80)

# ── 3. logo.jpg → logo_sm.webp (88x88 for 2× retina 44px display) ────────────
logo_src = os.path.join(IMGS, 'logo.jpg')
logo_dst = os.path.join(IMGS, 'logo_sm.webp')
if not os.path.exists(logo_dst):
    save_webp(logo_src, logo_dst, max_w=88, max_h=88, quality=85)
else:
    print(f'  [SKIP] logo_sm.webp already exists')

# ── Banner hero PNG (used as hero background) ─────────────────────────────────
banner_src = os.path.join(IMGS, 'banner-hero.png')
banner_dst = os.path.join(IMGS, 'banner-hero.webp')
if os.path.exists(banner_src) and not os.path.exists(banner_dst):
    save_webp(banner_src, banner_dst, max_w=1200, quality=80)

# ── Summary ───────────────────────────────────────────────────────────────────
total_saved = 0
print('')
print(f'{"Source":<50} {"→ Output":<45} {"Before":>7} {"After":>7} {"Saved":>7}')
print('-' * 120)
for src_rel, dst_rel, src_kb, dst_kb in results:
    saved = src_kb - dst_kb
    total_saved += saved
    print(f'{src_rel:<50} {dst_rel:<45} {src_kb:>5} KiB {dst_kb:>5} KiB {saved:>5} KiB')

print(f'\n✓ Total saved: {total_saved} KiB  ({total_saved/1024:.1f} MiB)')
print(f'  Files processed: {len(results)}')
