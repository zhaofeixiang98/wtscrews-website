#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy
import fcntl
import json
import os
import shutil
import tempfile


class JsonStoreError(Exception):
    pass


def default_pages_data():
    return {'news': [], 'products': []}


def _normalize_news(news_value):
    if not isinstance(news_value, list):
        return []
    return [item for item in news_value if isinstance(item, dict)]


def _normalize_products(products_value):
    if not isinstance(products_value, list):
        return []
    normalized = []
    for category in products_value:
        if not isinstance(category, dict):
            continue
        fixed = dict(category)
        items = fixed.get('items', [])
        if not isinstance(items, list):
            items = []
        fixed['items'] = [item for item in items if isinstance(item, dict)]
        normalized.append(fixed)
    return normalized


def normalize_pages_data(data):
    if data is None:
        return default_pages_data()
    if not isinstance(data, dict):
        raise JsonStoreError('pages JSON root must be an object')
    fixed = dict(data)
    fixed['news'] = _normalize_news(fixed.get('news'))
    fixed['products'] = _normalize_products(fixed.get('products'))
    return fixed


def read_pages_data(json_path):
    if not os.path.exists(json_path):
        return default_pages_data()
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            raw = f.read()
    except Exception as exc:
        raise JsonStoreError(f'cannot read {os.path.basename(json_path)}: {exc}') from exc
    if not raw.strip():
        return default_pages_data()
    try:
        parsed = json.loads(raw)
    except Exception as exc:
        raise JsonStoreError(f'invalid JSON in {os.path.basename(json_path)}: {exc}') from exc
    return normalize_pages_data(parsed)


def atomic_write_json(json_path, data):
    parent = os.path.dirname(json_path) or '.'
    os.makedirs(parent, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix='._pages_', suffix='.tmp', dir=parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        if os.path.exists(json_path):
            try:
                shutil.copy2(json_path, json_path + '.bak')
            except Exception:
                pass
        os.replace(tmp_path, json_path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


def update_pages_json(json_path, mutator):
    lock_path = json_path + '.lock'
    os.makedirs(os.path.dirname(lock_path) or '.', exist_ok=True)
    with open(lock_path, 'a+', encoding='utf-8') as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        current = read_pages_data(json_path)
        working = copy.deepcopy(current)
        updated = mutator(working)
        if updated is None:
            updated = working
        normalized = normalize_pages_data(updated)
        atomic_write_json(json_path, normalized)
        return normalized
