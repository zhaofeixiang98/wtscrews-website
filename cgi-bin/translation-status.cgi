#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Translation job status endpoint.
GET /cgi-bin/translation-status.cgi?slug=my-article-slug

Returns JSON:
  { "status": "starting"|"running"|"done"|"partial_error"|"not_found",
    "completed": ["ar","de",...], "failed": {"fr":"error"}, "total": 8,
    "updated_at": "..." }
"""
import os
import sys
import json
import re

from urllib.parse import parse_qs

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR   = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

sys.stdout.write('Content-Type: application/json; charset=utf-8\r\n\r\n')
sys.stdout.flush()


def respond(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()
    sys.exit(0)


qs   = parse_qs(os.environ.get('QUERY_STRING', ''))
slug = (qs.get('slug', [''])[0] or '').strip()

if not slug:
    respond({'error': 'slug parameter required'})

# Sanitize — only lowercase alphanumeric + hyphens allowed (prevent path traversal)
slug = re.sub(r'[^a-z0-9-]', '', slug.lower())
if not slug:
    respond({'error': 'invalid slug'})

status_path = os.path.join(BASE_DIR, '.translate-jobs', slug + '-status.json')

if not os.path.exists(status_path):
    respond({'status': 'not_found', 'completed': [], 'failed': {}, 'total': 8})

try:
    with open(status_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    respond(data)
except Exception as exc:
    respond({'error': str(exc)})
