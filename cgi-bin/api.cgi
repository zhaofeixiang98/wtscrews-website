#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WT Fasteners Content API  —  /cgi-bin/api.cgi
AI-agent endpoint for managing articles and images.

Authentication: X-API-Key: <key>  (or Authorization: Bearer <key>)
Content-Type:   application/json  (or application/x-www-form-urlencoded)
"""
import os, sys, json, re, base64, subprocess
from urllib.parse import parse_qs, urlencode
from datetime import datetime

# ── Output headers first ──────────────────────────────────────────────────────
sys.stdout.write("Content-Type: application/json; charset=utf-8\r\n")
sys.stdout.write("Access-Control-Allow-Origin: *\r\n")
sys.stdout.write("Access-Control-Allow-Methods: POST, GET, OPTIONS\r\n")
sys.stdout.write("Access-Control-Allow-Headers: Content-Type, X-API-Key, Authorization\r\n")
sys.stdout.write("\r\n")
sys.stdout.flush()

# ── Config ────────────────────────────────────────────────────────────────────
API_KEY      = "wt2026-api-key"          # <-- change this to a secure value
API_KEY      = os.environ.get('WT_CONTENT_API_KEY', API_KEY)
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
BASE_DIR     = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
NEWS_IMG_DIR = os.path.join(BASE_DIR, 'images', 'news')
LANGS        = ['en', 'ar', 'de', 'es', 'fr', 'id', 'ja', 'ko', 'zh']
IMG_EXTS     = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}

def respond(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, indent=2))
    sys.stdout.flush()
    sys.exit(0)

# ── OPTIONS preflight ────────────────────────────────────────────────────────
if os.environ.get('REQUEST_METHOD', '') == 'OPTIONS':
    respond({'ok': True})

# ── Auth ──────────────────────────────────────────────────────────────────────
key = (os.environ.get('HTTP_X_API_KEY', '') or
       os.environ.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '').strip())
if key != API_KEY:
    respond({'success': False, 'error': 'Unauthorized — provide X-API-Key header'})

# ── Parse request ─────────────────────────────────────────────────────────────
try:
    cl = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    ct = os.environ.get('CONTENT_TYPE', '')
    qs = os.environ.get('QUERY_STRING', '')
    raw = sys.stdin.buffer.read(cl).decode('utf-8', errors='replace') if cl > 0 else ''

    if 'application/json' in ct:
        body = json.loads(raw) if raw.strip() else {}
    else:
        merged = (raw + '&' + qs).strip('&')
        form   = parse_qs(merged, keep_blank_values=True)
        body   = {k: v[0] for k, v in form.items()}
except Exception as e:
    respond({'success': False, 'error': 'Parse error: ' + str(e)})

action = str(body.get('action', '')).strip()
if not action:
    respond({
        'success': False,
        'error': 'Missing action',
        'actions': {
            'list_images':    'List all images in /images/news/ with used/unused status',
            'delete_images':  'Delete images — body: {"filenames": ["a.jpg", "b.png"]}',
            'list_articles':  'List all published articles',
            'delete_articles':'Delete articles — body: {"slugs":["news/x"], "delete_images":true}',
            'create_article': 'Publish new article across all 9 languages — see schema below',
            'upload_image':   'Upload image via base64 — body: {"filename":"x.jpg","data":"<base64>"}',
            'schema': {
                'create_article': {
                    'slug':           'required, lowercase-hyphen, e.g. "market-update-2026"',
                    'date':           'required, YYYY-MM-DD',
                    'og_image':       'optional, relative to /images/, e.g. "news/cover.jpg"',
                    'article_section':'optional, default "Industry News"',
                    'extra_head':     'optional, raw HTML/JSON injected before </head>',
                    'auto_translate': 'optional, 1/true to auto-translate empty non-English fields from English source',
                    'en_title':       'required',
                    'en_summary':     'required (shown in news listing)',
                    'en_body':        'required (HTML)',
                    'en_subtitle':    'optional',
                    'en_meta_desc':   'optional (SEO)',
                    'en_keywords':    'optional',
                    'en_bc_label':    'optional (breadcrumb)',
                    'zh_title':       'optional — leave blank to use EN fallback',
                    'zh_body':        'optional — leave blank to use EN fallback',
                    '... (same _title/_subtitle/_summary/_meta_desc/_keywords/_bc_label/_body for ar/de/es/fr/id/ja/ko)': ''
                }
            }
        }
    })

# ═══════════════════════════════════════════════════════════════════════════════
# list_images
# ═══════════════════════════════════════════════════════════════════════════════
if action == 'list_images':
    images = []
    if os.path.exists(NEWS_IMG_DIR):
        for fname in sorted(os.listdir(NEWS_IMG_DIR)):
            if os.path.splitext(fname)[1].lower() in IMG_EXTS:
                fpath = os.path.join(NEWS_IMG_DIR, fname)
                images.append({'filename': fname, 'size': os.path.getsize(fpath), 'url': '/images/news/' + fname})

    referenced = set()
    for lang in LANGS:
        jp = os.path.join(BASE_DIR, 'pags', lang, f'pages_{lang}.json')
        if os.path.exists(jp):
            try:
                with open(jp, encoding='utf-8') as f:
                    data = json.load(f)
                for item in data.get('news', []):
                    icon = item.get('icon', '')
                    if 'images/news/' in icon:
                        referenced.add(icon.split('images/news/')[-1].strip('/'))
            except Exception:
                pass

    for img in images:
        img['used'] = img['filename'] in referenced

    unused = [i for i in images if not i['used']]
    respond({'success': True, 'images': images, 'total': len(images), 'unused': len(unused)})

# ═══════════════════════════════════════════════════════════════════════════════
# delete_images
# ═══════════════════════════════════════════════════════════════════════════════
elif action == 'delete_images':
    filenames = body.get('filenames', [])
    if isinstance(filenames, str):
        filenames = [f.strip() for f in filenames.split(',') if f.strip()]

    deleted = []
    errors  = []
    for fname in filenames:
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_%\-\.]*\.(jpg|jpeg|png|gif|webp|svg)$', fname, re.I):
            errors.append(f'Invalid filename: {fname}')
            continue
        fpath = os.path.join(NEWS_IMG_DIR, fname)
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
                deleted.append(fname)
            except Exception as e:
                errors.append(f'{fname}: {e}')
        else:
            errors.append(f'{fname}: not found')

    respond({'success': bool(deleted), 'deleted': deleted, 'errors': errors})

# ═══════════════════════════════════════════════════════════════════════════════
# list_articles
# ═══════════════════════════════════════════════════════════════════════════════
elif action == 'list_articles':
    jp = os.path.join(BASE_DIR, 'pags', 'en', 'pages_en.json')
    try:
        with open(jp, encoding='utf-8') as f:
            data = json.load(f)
        articles = [a for a in data.get('news', []) if a.get('slug', '').startswith('news/')]
        respond({'success': True, 'articles': articles, 'total': len(articles)})
    except Exception as e:
        respond({'success': False, 'error': str(e)})

# ═══════════════════════════════════════════════════════════════════════════════
# delete_articles
# ═══════════════════════════════════════════════════════════════════════════════
elif action == 'delete_articles':
    slugs = body.get('slugs', [])
    if isinstance(slugs, str):
        slugs = [s.strip() for s in slugs.split(',') if s.strip()]
    delete_imgs = bool(body.get('delete_images', False))

    # Collect image paths from EN JSON before deletion
    images_to_delete = {}
    if delete_imgs:
        jp = os.path.join(BASE_DIR, 'pags', 'en', 'pages_en.json')
        if os.path.exists(jp):
            try:
                with open(jp, encoding='utf-8') as f:
                    en_data = json.load(f)
                for item in en_data.get('news', []):
                    if item.get('slug') in slugs:
                        icon = item.get('icon', '')
                        if 'images/news/' in icon:
                            images_to_delete[item['slug']] = icon.split('images/news/')[-1].strip('/')
            except Exception:
                pass

    deleted = []
    errors  = []
    for news_slug in slugs:
        file_slug = news_slug.split('/', 1)[1] if '/' in news_slug else news_slug
        if not re.match(r'^[a-z0-9][a-z0-9\-]*$', file_slug):
            errors.append(f'Invalid slug: {news_slug}')
            continue
        ok = False
        for lang in LANGS:
            hp = os.path.join(BASE_DIR, 'pags', lang, 'news', file_slug + '.html')
            if os.path.exists(hp):
                try:
                    os.remove(hp)
                    ok = True
                except Exception as e:
                    errors.append(f'{lang}/{file_slug}: {e}')
            jp = os.path.join(BASE_DIR, 'pags', lang, f'pages_{lang}.json')
            if os.path.exists(jp):
                try:
                    with open(jp, encoding='utf-8') as f:
                        jdata = json.load(f)
                    before = len(jdata.get('news', []))
                    jdata['news'] = [n for n in jdata.get('news', []) if n.get('slug') != news_slug]
                    if len(jdata['news']) < before:
                        with open(jp, 'w', encoding='utf-8') as f:
                            json.dump(jdata, f, ensure_ascii=False, indent=4)
                        ok = True
                except Exception as e:
                    errors.append(f'{lang}/json: {e}')
        if ok:
            deleted.append(news_slug)

    deleted_images = []
    if delete_imgs:
        for fname in images_to_delete.values():
            if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_%\-\.]+\.(jpg|jpeg|png|gif|webp|svg)$', fname, re.I):
                ip = os.path.join(NEWS_IMG_DIR, fname)
                if os.path.exists(ip):
                    try:
                        os.remove(ip)
                        deleted_images.append(fname)
                    except Exception as e:
                        errors.append(f'image {fname}: {e}')

    respond({'success': bool(deleted), 'deleted': deleted, 'deleted_images': deleted_images, 'errors': errors})

# ═══════════════════════════════════════════════════════════════════════════════
# upload_image  (base64)
# ═══════════════════════════════════════════════════════════════════════════════
elif action == 'upload_image':
    filename   = str(body.get('filename', '')).strip()
    b64_data   = str(body.get('data', '')).strip()
    if not filename or not b64_data:
        respond({'success': False, 'error': 'filename and data (base64) required'})

    ext = os.path.splitext(filename)[1].lower()
    if ext not in IMG_EXTS:
        respond({'success': False, 'error': f'Unsupported extension: {ext}'})

    safe_base = re.sub(r'[^a-zA-Z0-9_\-]', '-', os.path.splitext(filename)[0]).strip('-') or 'image'
    final_name = safe_base + ext

    try:
        img_data = base64.b64decode(b64_data)
    except Exception as e:
        respond({'success': False, 'error': 'base64 decode error: ' + str(e)})

    try:
        os.makedirs(NEWS_IMG_DIR, exist_ok=True)
        base = os.path.splitext(final_name)[0]
        candidate = final_name
        counter = 1
        while os.path.exists(os.path.join(NEWS_IMG_DIR, candidate)):
            candidate = f'{base}-{counter}{ext}'
            counter += 1
        final_name = candidate
        with open(os.path.join(NEWS_IMG_DIR, final_name), 'wb') as f:
            f.write(img_data)
        respond({'success': True, 'filename': final_name, 'path': 'news/' + final_name, 'url': '/images/news/' + final_name})
    except Exception as e:
        respond({'success': False, 'error': str(e)})

# ═══════════════════════════════════════════════════════════════════════════════
# create_article  —  delegates to article-save.cgi
# ═══════════════════════════════════════════════════════════════════════════════
elif action == 'create_article':
    required = ['slug', 'en_title', 'en_body', 'en_summary']
    missing  = [k for k in required if not str(body.get(k, '')).strip()]
    if missing:
        respond({'success': False, 'error': 'Missing required fields: ' + ', '.join(missing)})

    # Build URL-encoded params for article-save.cgi
    params = {}
    all_fields = ['title','subtitle','summary','meta_desc','keywords','bc_label','body']
    scalar_keys = ['slug','date','og_image','article_section','extra_head','auto_translate']
    for k in scalar_keys:
        if body.get(k):
            params[k] = str(body[k])
    if 'date' not in params:
        params['date'] = datetime.now().strftime('%Y-%m-%d')
    for lang in LANGS:
        for field in all_fields:
            key = f'{lang}_{field}'
            if body.get(key):
                params[key] = str(body[key])

    params_str = urlencode(params)
    params_bytes = params_str.encode('utf-8')
    save_script = os.path.join(SCRIPT_DIR, 'article-save.cgi')

    try:
        result = subprocess.run(
            [sys.executable, save_script],
            input=params_bytes,
            capture_output=True, timeout=30,
            env={
                **os.environ,
                'REQUEST_METHOD':  'POST',
                'CONTENT_TYPE':    'application/x-www-form-urlencoded',
                'CONTENT_LENGTH':  str(len(params_bytes)),
                'WT_ADMIN_BYPASS': '1',
            }
        )
        raw_out = result.stdout.decode('utf-8', errors='replace')
        # Strip CGI header if present
        json_part = raw_out.split('\r\n\r\n', 1)[-1] if '\r\n\r\n' in raw_out else raw_out
        respond(json.loads(json_part))
    except subprocess.TimeoutExpired:
        respond({'success': False, 'error': 'article-save.cgi timed out'})
    except Exception as e:
        respond({'success': False, 'error': str(e)})

# ═══════════════════════════════════════════════════════════════════════════════
else:
    respond({'success': False, 'error': f'Unknown action: {action}'})
