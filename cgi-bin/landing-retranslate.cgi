#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import re
import sys
import subprocess
from datetime import datetime
from html import unescape
from urllib.parse import parse_qs

from admin_auth import is_request_authenticated

sys.stdout.write("Content-Type: application/json; charset=utf-8\r\n\r\n")
sys.stdout.flush()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
LANGS = ['ar', 'de', 'es', 'fr', 'id', 'ja', 'ko', 'zh']
SLUG_RE = re.compile(r'^[a-z0-9][a-z0-9\-]*$')


def respond(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()
    sys.exit(0)


if not is_request_authenticated():
    respond({'success': False, 'error': 'unauthorized'})


try:
    cl = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    raw = sys.stdin.buffer.read(cl).decode('utf-8', errors='replace') if cl > 0 else ''
    form = parse_qs(raw, keep_blank_values=True)

    def g(key, default=''):
        values = form.get(key, [default])
        return (values[0] if values else default).strip()
except Exception as exc:
    respond({'success': False, 'error': 'Parse error: ' + str(exc)})


def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def pick(pattern, text, default='', flags=re.I | re.S):
    match = re.search(pattern, text, flags)
    if not match:
        return default
    return match.group(1).strip()


def extract_source_from_en_page(slug):
    path = os.path.join(BASE_DIR, 'pags', 'en', 'landing', slug + '.html')
    if not os.path.exists(path):
        raise FileNotFoundError(f'未找到英文落地页: {path}')

    html = read_file(path)

    title = unescape(pick(r'<h1[^>]*>(.*?)</h1>', html))
    subtitle = unescape(pick(r'<p class="subtitle">(.*?)</p>', html))
    summary = unescape(pick(r'<p class="summary">(.*?)</p>', html))
    meta_desc = unescape(pick(r'<meta name="description" content="(.*?)">', html))
    keywords = unescape(pick(r'<meta name="keywords" content="(.*?)">', html))
    bc_label = unescape(pick(r'<section class="section">\s*<h2>(.*?)</h2>', html))
    body = pick(r'<article class="article-body">\s*(.*?)\s*</article>', html)
    hero_src = unescape(pick(r'<aside class="hero-media">\s*<img src="(.*?)"', html))
    whatsapp_url = unescape(pick(r'<a class="btn chat" href="(.*?)"', html))
    extra_head = pick(r'<meta property="og:image"[^>]*>\s*(.*?)\s*<style>', html, '')

    if hero_src.startswith('../../../images/'):
        hero_src = hero_src[len('../../../images/'):]
    elif hero_src.startswith('/images/'):
        hero_src = hero_src[len('/images/'):]
    elif hero_src.startswith('https://wtscrews.com/images/'):
        hero_src = hero_src[len('https://wtscrews.com/images/'):]

    if not title or not summary or not body:
        raise RuntimeError('英文落地页内容提取失败，请先确认英文页结构正常')

    return {
        'title': title,
        'subtitle': subtitle,
        'summary': summary,
        'meta_desc': meta_desc or summary,
        'keywords': keywords,
        'bc_label': bc_label or title,
        'body': body,
        'hero_image': hero_src or 'banner-hero.webp',
        'whatsapp_url': whatsapp_url or 'https://wa.me/8615175432812',
        'extra_head': extra_head,
    }


slug = g('slug').lower()
if not SLUG_RE.match(slug):
    respond({'success': False, 'error': '无效的 slug'})

try:
    source = extract_source_from_en_page(slug)
except Exception as exc:
    respond({'success': False, 'error': str(exc)})

jobs_dir = os.path.join(BASE_DIR, '.translate-jobs')
os.makedirs(jobs_dir, exist_ok=True)
status_path = os.path.join(jobs_dir, slug + '-status.json')
job_path = os.path.join(jobs_dir, slug + '-job.json')

try:
    with open(status_path, 'w', encoding='utf-8') as sf:
        json.dump({
            'status': 'starting',
            'completed': [],
            'failed': {},
            'total': len(LANGS),
            'updated_at': datetime.now().isoformat(),
            'mode': 'landing_retranslate',
        }, sf, ensure_ascii=False)

    job_data = {
        'slug': slug,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'og_image': source['hero_image'],
        'article_section': 'Landing Page',
        'extra_head': source['extra_head'],
        'source_fields': {
            'title': source['title'],
            'subtitle': source['subtitle'],
            'summary': source['summary'],
            'meta_desc': source['meta_desc'],
            'keywords': source['keywords'],
            'bc_label': source['bc_label'],
            'body': source['body'],
        },
        'langs': list(LANGS),
        'base_dir': BASE_DIR,
        'article_save_path': os.path.join(SCRIPT_DIR, 'landing-save.cgi'),
        'status_path': status_path,
        'extra_params': {
            'whatsapp_url': source['whatsapp_url'],
            'hero_image': source['hero_image'],
        },
    }
    with open(job_path, 'w', encoding='utf-8') as jf:
        json.dump(job_data, jf, ensure_ascii=False)

    worker_path = os.path.join(SCRIPT_DIR, 'translate-worker.py')
    subprocess.Popen(
        [sys.executable, worker_path, job_path],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        start_new_session=True,
    )
except Exception as exc:
    respond({'success': False, 'error': '启动重翻译失败: ' + str(exc)})

respond({
    'success': True,
    'slug': slug,
    'translating': True,
    'message': '已开始使用 DeepSeek 重新翻译全部语言',
})
