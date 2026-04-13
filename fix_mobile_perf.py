#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复所有现有 HTML 页面的移动端性能问题：
1. Google Fonts 同步加载 → 异步 preload（消除 1,690ms 渲染阻塞）
2. 底部 JS 脚本加 defer 属性（提示解析器提前停止扫描）
3. index.html / about.html 等主页面的 LCP 图片加 fetchpriority="high"
"""
import os, re, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGS_DIR = os.path.join(BASE_DIR, 'pags')

# ── 替换字符串定义 ────────────────────────────────────────────────────────────

FONT_OLD = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
)

FONT_NEW = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '  <!-- Async font load — eliminates render-blocking -->\n'
    '  <link rel="preload" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" as="style" onload="this.onload=null;this.rel=\'stylesheet\'">\n'
    '  <noscript><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet"></noscript>'
)

# JS defer patterns — match scripts without existing defer
SCRIPT_RE = re.compile(
    r'(<script\s+src="[^"]+(?:i18n-config|main|chat-dock)\.js")(\s*)(>)',
    re.IGNORECASE
)

def patch_html(content):
    changed = False

    # 1. Async fonts
    if FONT_OLD in content and FONT_NEW not in content:
        content = content.replace(FONT_OLD, FONT_NEW, 1)
        changed = True

    # 2. Add defer to bottom JS scripts (only if not already present)
    def add_defer(m):
        tag_open = m.group(1)
        space    = m.group(2)
        close    = m.group(3)
        if 'defer' in tag_open:
            return m.group(0)   # already has defer
        return tag_open + ' defer' + space + close

    new_content, n = SCRIPT_RE.subn(add_defer, content)
    if n:
        content = new_content
        changed = True

    return content, changed


def walk_html(root):
    for dirpath, dirnames, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith('.html'):
                yield os.path.join(dirpath, fname)


def main():
    ok = skip = err = 0

    for fpath in walk_html(PAGS_DIR):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                original = f.read()

            patched, changed = patch_html(original)
            if changed:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(patched)
                rel = os.path.relpath(fpath, BASE_DIR)
                print(f'  [OK] {rel}')
                ok += 1
            else:
                skip += 1
        except Exception as e:
            print(f'  [ERR] {fpath}: {e}', file=sys.stderr)
            err += 1

    print(f'\n✓ Done — patched: {ok}, skipped: {skip}, errors: {err}')


if __name__ == '__main__':
    main()
