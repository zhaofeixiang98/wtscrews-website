#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
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
        'has_backup': os.path.exists(bak_path),
    }

    parsed, err = safe_load_json(path)
    if err:
        item['status'] = 'error'
        item['issues'].append(f'json invalid: {err}')
        return item

    try:
        normalized = normalize_pages_data(parsed)
    except Exception as exc:
        item['status'] = 'error'
        item['issues'].append(f'structure invalid: {exc}')
        return item

    item['news_count'] = len(normalized.get('news', []))
    item['product_count'] = count_products(normalized.get('products', []))

    if normalized != parsed:
        item['status'] = 'warn'
        item['issues'].append('structure non-standard, should normalize')

    if lang != 'en':
        same_news = 0
        for news in normalized.get('news', []):
            slug = news.get('slug')
            if slug and en_news_titles.get(slug) == news.get('title'):
                same_news += 1
        same_products = 0
        for cat in normalized.get('products', []):
            for prod in cat.get('items', []):
                slug = prod.get('slug')
                if slug and en_product_titles.get(slug) == prod.get('title'):
                    same_products += 1
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
    if do_repair:
        for item in items:
            if item['status'] in {'warn', 'error'}:
                repairs.append(repair_item(item))
        # recheck after repair
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

    return {
        'success': True,
        'repaired': do_repair,
        'summary': summary,
        'items': items,
        'repairs': repairs,
    }


def main():
    method, g = get_form()
    action = g('action', 'check')
    do_repair = action == 'repair'
    if method not in {'GET', 'POST'}:
        respond({'success': False, 'error': 'unsupported method'})
    respond(build_report(do_repair=do_repair))


if __name__ == '__main__':
    main()
