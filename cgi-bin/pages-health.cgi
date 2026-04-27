#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys
from urllib.parse import parse_qs

from json_store import (
    JsonStoreError,
    atomic_write_json,
    default_pages_data,
    normalize_pages_data,
    read_pages_data,
)
from admin_auth import is_request_authenticated


sys.stdout.write("Content-Type: application/json; charset=utf-8\r\n\r\n")
sys.stdout.flush()


def respond(payload):
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.flush()
    sys.exit(0)


if not is_request_authenticated():
    respond({'success': False, 'error': 'unauthorized'})


def get_form():
    try:
        method = (os.environ.get('REQUEST_METHOD') or 'GET').upper()
        if method == 'POST':
            cl = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
            raw = sys.stdin.buffer.read(cl).decode('utf-8', errors='replace') if cl > 0 else ''
            form = parse_qs(raw, keep_blank_values=True)
        else:
            raw = os.environ.get('QUERY_STRING', '')
            form = parse_qs(raw, keep_blank_values=True)
    except Exception:
        form = {}

    def g(key, default=''):
        values = form.get(key, [default])
        return (values[0] if values else default).strip()

    return method, g


LANGS = ['en', 'ar', 'de', 'es', 'fr', 'id', 'ja', 'ko', 'zh']
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))


def safe_load_json(path):
    if not os.path.exists(path):
        return None, 'missing'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            raw = f.read()
        if not raw.strip():
            return None, 'empty file'
        return json.loads(raw), None
    except Exception as exc:
        return None, str(exc)


def count_products(items):
    return sum(len((cat or {}).get('items', []) or []) for cat in (items or []))


def rebuild_static_lists():
    render_script = os.path.join(BASE_DIR, 'render_list_pages.py')
    if not os.path.exists(render_script):
        return 'render_list_pages.py not found'
    try:
        result = subprocess.run(
            [sys.executable, render_script],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except Exception as exc:
        return f'render list pages failed: {exc}'
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or '').strip()
        return f'render list pages failed: {detail or "unknown error"}'
    return ''


def analyze_lang(lang, en_news_titles, en_product_titles):
    path = os.path.join(BASE_DIR, 'pags', lang, f'pages_{lang}.json')
    bak_path = path + '.bak'
    item = {
        'lang': lang,
        'path': path,
        'exists': os.path.exists(path),
        'status': 'ok',
        'issues': [],
        'news_count': 0,
        'product_count': 0,
        'translation_same_news_titles': 0,
        'translation_same_product_titles': 0,
        'same_news_examples': [],
        'same_product_examples': [],
        'repairable': False,
        'repair_reasons': [],
        'has_backup': os.path.exists(bak_path),
    }

    parsed, err = safe_load_json(path)
    if err:
        item['status'] = 'error'
        item['issues'].append(f'json invalid: {err}')
        item['repairable'] = True
        item['repair_reasons'].append('json invalid')
        return item

    try:
        normalized = normalize_pages_data(parsed)
    except Exception as exc:
        item['status'] = 'error'
        item['issues'].append(f'structure invalid: {exc}')
        item['repairable'] = True
        item['repair_reasons'].append('structure invalid')
        return item

    item['news_count'] = len(normalized.get('news', []))
    item['product_count'] = count_products(normalized.get('products', []))

    if normalized != parsed:
        item['status'] = 'warn'
        item['issues'].append('structure non-standard, should normalize')
        item['repairable'] = True
        item['repair_reasons'].append('structure non-standard')

    if lang != 'en':
        same_news = 0
        for news in normalized.get('news', []):
            slug = news.get('slug')
            if slug and en_news_titles.get(slug) == news.get('title'):
                same_news += 1
                if len(item['same_news_examples']) < 5:
                    item['same_news_examples'].append({'slug': slug, 'title': news.get('title', '')})
        same_products = 0
        for cat in normalized.get('products', []):
            for prod in cat.get('items', []):
                slug = prod.get('slug')
                if slug and en_product_titles.get(slug) == prod.get('title'):
                    same_products += 1
                    if len(item['same_product_examples']) < 5:
                        item['same_product_examples'].append({'slug': slug, 'title': prod.get('title', '')})
        item['translation_same_news_titles'] = same_news
        item['translation_same_product_titles'] = same_products
        if (same_news + same_products) > 0:
            if item['status'] == 'ok':
                item['status'] = 'warn'
            item['issues'].append('possible untranslated titles found')

    return item


def load_en_title_map():
    en_path = os.path.join(BASE_DIR, 'pags', 'en', 'pages_en.json')
    try:
        data = read_pages_data(en_path)
    except Exception:
        return {}, {}
    news = {n.get('slug'): n.get('title', '') for n in data.get('news', []) if n.get('slug')}
    products = {}
    for cat in data.get('products', []):
        for item in cat.get('items', []):
            slug = item.get('slug')
            if slug:
                products[slug] = item.get('title', '')
    return news, products


def repair_item(info):
    path = info['path']
    bak = path + '.bak'
    fixed = {'lang': info['lang'], 'repaired': False, 'method': '', 'error': ''}

    parsed, err = safe_load_json(path)
    if err:
        bak_data, bak_err = safe_load_json(bak)
        if not bak_err:
            try:
                normalized = normalize_pages_data(bak_data)
                atomic_write_json(path, normalized)
                fixed['repaired'] = True
                fixed['method'] = 'restore_from_backup'
                return fixed
            except Exception as exc:
                fixed['error'] = f'backup restore failed: {exc}'
                return fixed
        try:
            atomic_write_json(path, default_pages_data())
            fixed['repaired'] = True
            fixed['method'] = 'reset_default_structure'
            return fixed
        except Exception as exc:
            fixed['error'] = f'default reset failed: {exc}'
            return fixed

    try:
        normalized = normalize_pages_data(parsed)
        if normalized != parsed:
            atomic_write_json(path, normalized)
            fixed['repaired'] = True
            fixed['method'] = 'normalize_structure'
        else:
            fixed['method'] = 'no_change_needed'
        return fixed
    except JsonStoreError as exc:
        fixed['error'] = str(exc)
    except Exception as exc:
        fixed['error'] = str(exc)
    return fixed


def build_report(do_repair=False):
    en_news_titles, en_product_titles = load_en_title_map()
    items = [analyze_lang(lang, en_news_titles, en_product_titles) for lang in LANGS]
    repairs = []
    render_error = ''
    if do_repair:
        for item in items:
            if item.get('repairable'):
                repairs.append(repair_item(item))
        if any(item.get('repaired') for item in repairs):
            render_error = rebuild_static_lists()
        # recheck after repair. Reload EN maps in case the English file changed.
        en_news_titles, en_product_titles = load_en_title_map()
        items = [analyze_lang(lang, en_news_titles, en_product_titles) for lang in LANGS]

    summary = {
        'total': len(items),
        'ok': sum(1 for x in items if x['status'] == 'ok'),
        'warn': sum(1 for x in items if x['status'] == 'warn'),
        'error': sum(1 for x in items if x['status'] == 'error'),
        'translation_suspected': sum(
            (x.get('translation_same_news_titles') or 0) + (x.get('translation_same_product_titles') or 0)
            for x in items
        ),
    }
    repaired_count = sum(1 for x in repairs if x.get('repaired'))

    return {
        'success': True,
        'repair_requested': do_repair,
        'repaired': repaired_count > 0,
        'repaired_count': repaired_count,
        'summary': summary,
        'items': items,
        'repairs': repairs,
        'render_error': render_error,
    }


def main():
    method, g = get_form()
    action = g('action', 'check')
    if action not in {'check', 'repair'}:
        respond({'success': False, 'error': 'unsupported action'})
    if action == 'repair' and method != 'POST':
        respond({'success': False, 'error': 'repair requires POST'})
    do_repair = action == 'repair'
    if method not in {'GET', 'POST'}:
        respond({'success': False, 'error': 'unsupported method'})
    respond(build_report(do_repair=do_repair))


if __name__ == '__main__':
    main()
