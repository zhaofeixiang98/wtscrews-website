#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Background translation worker for WT Fasteners article system.
Usage: python3 translate-worker.py /path/to/{slug}-job.json

Reads the job file written by article-save.cgi, translates all 8 non-English
languages IN PARALLEL using ThreadPoolExecutor, then calls article-save.cgi as
a subprocess (with auto_translate=0 and all pre-translated content) to write
the final HTML files and update each language's pages_*.json.
"""
import sys
import os
import json
import re
import subprocess
from datetime import datetime
from urllib import request as urlrequest
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Translation constants ─────────────────────────────────────────────────────
TRANSLATABLE_FIELDS = ['title', 'subtitle', 'summary', 'meta_desc', 'keywords', 'bc_label', 'body']
LANG_LABELS = {
    'ar': 'Arabic',
    'de': 'German',
    'es': 'Spanish',
    'fr': 'French',
    'id': 'Indonesian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Simplified Chinese',
}
ENV_FILE_NAMES = ['.translation-env', '.env.translation']
_env_loaded = False


# ── Env / API helpers ─────────────────────────────────────────────────────────
def load_env(base_dir):
    global _env_loaded
    if _env_loaded:
        return
    _env_loaded = True
    for name in ENV_FILE_NAMES:
        path = os.path.join(base_dir, name)
        if not os.path.exists(path):
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    key, val = line.split('=', 1)
                    key, val = key.strip(), val.strip()
                    if not key:
                        continue
                    if len(val) >= 2 and val[0] == val[-1] and val[0] in {'"', "'"}:
                        val = val[1:-1]
                    os.environ.setdefault(key, val)
        except Exception:
            pass


def get_api_key():
    return (
        os.environ.get('WT_TRANSLATE_API_KEY', '').strip()
        or os.environ.get('DEEPSEEK_API_KEY', '').strip()
        or os.environ.get('OPENAI_API_KEY', '').strip()
    )


def get_api_url():
    explicit = (
        os.environ.get('WT_TRANSLATE_API_URL', '').strip()
        or os.environ.get('DEEPSEEK_API_URL', '').strip()
        or os.environ.get('OPENAI_API_URL', '').strip()
    )
    if explicit:
        return explicit
    base = (
        os.environ.get('WT_TRANSLATE_API_BASE', '').strip()
        or os.environ.get('DEEPSEEK_API_BASE', '').strip()
        or os.environ.get('OPENAI_BASE_URL', '').strip()
    )
    if base:
        return base.rstrip('/') + '/chat/completions'
    if os.environ.get('DEEPSEEK_API_KEY', '').strip():
        return 'https://api.deepseek.com/chat/completions'
    if os.environ.get('OPENAI_API_KEY', '').strip():
        return 'https://api.openai.com/v1/chat/completions'
    return ''


def get_model():
    return (
        os.environ.get('WT_TRANSLATE_MODEL', '').strip()
        or os.environ.get('DEEPSEEK_MODEL', '').strip()
        or os.environ.get('OPENAI_MODEL', '').strip()
        or ('deepseek-chat' if os.environ.get('DEEPSEEK_API_KEY', '').strip() else 'gpt-4o-mini')
    )


def extract_json_object(text):
    text = (text or '').strip()
    if not text:
        raise ValueError('model returned empty content')
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r'\{.*\}', text, re.S)
        if not m:
            raise ValueError('no valid JSON in model response')
        return json.loads(m.group(0))


# ── Core: translate one language ──────────────────────────────────────────────
def translate_one(lang, source_fields, api_key, api_url, model):
    target_name = LANG_LABELS.get(lang, lang)
    
    # ── Mask <img> tags to prevent LLM from confusing or dropping them ──
    body_text = source_fields.get('body', '')
    img_masks = []
    def mask_img(m):
        img_masks.append(m.group(0))
        return f'__IMG_MASK_{len(img_masks)-1}__'
    
    masked_body = re.sub(r'<img\s+[^>]*>', mask_img, body_text)
    masked_source_fields = dict(source_fields)
    masked_source_fields['body'] = masked_body

    system_prompt = (
        'You are a professional website localization translator for industrial fastener news. '
        'Translate English source content into the requested target language and return strict JSON only.'
    )
    user_prompt = (
        f'Target language: {target_name} ({lang}).\n'
        'Return exactly one JSON object with keys: title, subtitle, summary, meta_desc, keywords, bc_label, body.\n'
        'Rules:\n'
        '1. Preserve HTML structure in body exactly: keep tag names, nesting, href, src, class, id, '
        'style, loading, and relative paths unchanged. Do not alter placeholders like __IMG_MASK_0__.\n'
        '2. Translate only human-readable text content. Do not translate URLs, filenames, product '
        'standards, model numbers, or brand names like WT Fasteners.\n'
        '3. Keep measurements, units, dates, percentages, DIN/ISO/ASTM codes, and punctuation '
        'formatting appropriate for the target language.\n'
        '4. keywords must stay a comma-separated SEO keyword string in the target language.\n'
        '5. meta_desc should remain concise and suitable for a meta description.\n'
        '6. If subtitle is empty, return an empty string for subtitle.\n'
        '7. Output JSON only, with no markdown fences or explanations.\n\n'
        'Source JSON:\n'
        + json.dumps(masked_source_fields, ensure_ascii=False)
    )
    payload = {
        'model': model,
        'temperature': 0.2,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
    }
    req = urlrequest.Request(
        api_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )
    # Long timeout — this process is not bound by the HTTP request timeout
    with urlrequest.urlopen(req, timeout=360) as resp:
        raw = resp.read().decode('utf-8', errors='replace')

    data = json.loads(raw)
    content = data['choices'][0]['message']['content']
    translated = extract_json_object(content)
    
    # Restore img masks
    if 'body' in translated:
        def restore_img(m):
            idx = int(m.group(1))
            if 0 <= idx < len(img_masks):
                return img_masks[idx]
            return m.group(0)
        translated['body'] = re.sub(r'__IMG_MASK_(\d+)__', restore_img, translated['body'])
        
    missing = [f for f in TRANSLATABLE_FIELDS if f not in translated]
    if missing:
        raise ValueError(f'missing fields in response: {", ".join(missing)}')
    return {f: str(translated.get(f, '') or '') for f in TRANSLATABLE_FIELDS}


# ── Status helpers ────────────────────────────────────────────────────────────
def write_status(status_path, completed, failed, total, finished=False):
    if finished:
        status = 'done' if not failed else 'partial_error'
    else:
        status = 'running'
    try:
        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump({
                'status': status,
                'completed': list(completed),
                'failed': dict(failed),
                'total': total,
                'updated_at': datetime.now().isoformat(),
            }, f, ensure_ascii=False)
    except Exception:
        pass


# ── Save all translated pages via article-save.cgi subprocess ────────────────
def save_via_cgi(article_save_path, slug, date, og_image, article_section,
                 extra_head, source_fields, translations):
    """
    Call article-save.cgi as a CGI subprocess with auto_translate=0 and all
    translated content pre-filled. The CGI will write HTML + update JSON for
    every language (EN is re-saved idempotently; translated langs get their
    proper pages).
    """
    params = {
        'slug': slug,
        'date': date,
        'og_image': og_image,
        'article_section': article_section,
        'extra_head': extra_head,
        'auto_translate': '0',  # no further translation — prevent re-forking
    }
    # English source fields (en_title, en_body, …)
    for field, value in source_fields.items():
        params[f'en_{field}'] = value
    # Non-English translated fields
    for lang, fields in translations.items():
        for field, value in fields.items():
            params[f'{lang}_{field}'] = value

    body = urlencode(params).encode('utf-8')
    env = os.environ.copy()
    env.update({
        'REQUEST_METHOD': 'POST',
        'CONTENT_TYPE': 'application/x-www-form-urlencoded',
        'CONTENT_LENGTH': str(len(body)),
    })
    result = subprocess.run(
        [sys.executable, article_save_path],
        input=body,
        capture_output=True,
        env=env,
        timeout=120,
    )
    # CGI stdout format: "Content-Type: ...\r\n\r\n{json}"
    output = result.stdout.decode('utf-8', errors='replace')
    json_str = output.split('\r\n\r\n', 1)[-1].strip()
    return json.loads(json_str)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print('Usage: translate-worker.py <job-file>', file=sys.stderr)
        sys.exit(1)

    job_file = sys.argv[1]
    try:
        with open(job_file, 'r', encoding='utf-8') as f:
            job = json.load(f)
    except Exception as e:
        print(f'[translate-worker] cannot read job file: {e}', file=sys.stderr)
        sys.exit(1)

    slug               = job['slug']
    base_dir           = job['base_dir']
    langs              = job.get('langs', ['ar', 'de', 'es', 'fr', 'id', 'ja', 'ko', 'zh'])
    source_fields      = job['source_fields']
    status_path        = job['status_path']
    article_save_path  = job['article_save_path']

    load_env(base_dir)
    api_key = get_api_key()
    api_url = get_api_url()
    model   = get_model()

    total     = len(langs)
    completed = []
    failed    = {}
    write_status(status_path, completed, failed, total)

    # ── Translate all languages in parallel ───────────────────────────────────
    translations = {}
    with ThreadPoolExecutor(max_workers=min(8, total)) as executor:
        future_to_lang = {
            executor.submit(translate_one, lang, source_fields, api_key, api_url, model): lang
            for lang in langs
        }
        for future in as_completed(future_to_lang):
            lang = future_to_lang[future]
            try:
                translations[lang] = future.result()
                completed.append(lang)
            except Exception as exc:
                failed[lang] = str(exc)
                print(f'[translate-worker] {lang} failed: {exc}', file=sys.stderr)
            write_status(status_path, completed, failed, total)

    # ── Save all pages in one CGI call ────────────────────────────────────────
    try:
        save_result = save_via_cgi(
            article_save_path,
            slug=slug,
            date=job['date'],
            og_image=job.get('og_image', ''),
            article_section=job.get('article_section', 'Industry News'),
            extra_head=job.get('extra_head', ''),
            source_fields=source_fields,
            translations=translations,
        )
        if not save_result.get('success'):
            print(f'[translate-worker] save_via_cgi reported errors: {save_result}',
                  file=sys.stderr)
    except Exception as exc:
        # Mark all completed langs as failed if we can't save
        for lang in list(completed):
            failed[lang] = f'save failed: {exc}'
        completed.clear()
        print(f'[translate-worker] save_via_cgi crashed: {exc}', file=sys.stderr)

    write_status(status_path, completed, failed, total, finished=True)

    # Clean up job file
    try:
        os.remove(job_file)
    except Exception:
        pass


if __name__ == '__main__':
    main()
