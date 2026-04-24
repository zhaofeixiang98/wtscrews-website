#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import re
import json
import subprocess
from datetime import datetime
from urllib.parse import parse_qs
from admin_auth import is_request_authenticated

sys.stdout.write("Content-Type: application/json; charset=utf-8\r\n\r\n")
sys.stdout.flush()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
LANGS = ['en', 'ar', 'de', 'es', 'fr', 'id', 'ja', 'ko', 'zh']
FIELDS = ['title', 'subtitle', 'summary', 'meta_desc', 'keywords', 'bc_label', 'body']


def respond(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()
    sys.exit(0)


if not is_request_authenticated():
    respond({'success': False, 'error': 'unauthorized'})


def g(form, key, default=''):
    values = form.get(key, [default])
    return (values[0] if values else default).strip()


def truthy(value):
    return str(value or '').strip().lower() in {'1', 'true', 'yes', 'on'}


def he(text):
    return (
        str(text or '')
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
    )


def make_hreflang(slug):
    mapping = {'en': 'en', 'ar': 'ar', 'de': 'de', 'es': 'es', 'fr': 'fr', 'id': 'id', 'ja': 'ja', 'ko': 'ko', 'zh': 'zh-CN'}
    lines = []
    for lang in LANGS:
        lines.append(f'  <link rel="alternate" hreflang="{mapping[lang]}" href="/pags/{lang}/landing/{slug}.html">')
    lines.append(f'  <link rel="alternate" hreflang="x-default" href="/pags/en/landing/{slug}.html">')
    return '\n'.join(lines)


LC = {
    'en': {'html_lang': 'en', 'cta_quote': 'Get Quote in 24h', 'cta_chat': 'WhatsApp Now', 'form_title': 'Tell us your requirements', 'form_btn': 'Submit Request', 'privacy': 'Privacy Policy', 'lead_notice': 'Industrial fastener quotation page'},
    'zh': {'html_lang': 'zh-CN', 'cta_quote': '24小时内获取报价', 'cta_chat': 'WhatsApp 立即沟通', 'form_title': '提交您的需求', 'form_btn': '提交需求', 'privacy': '隐私政策', 'lead_notice': '工业紧固件报价页面'},
    'de': {'html_lang': 'de', 'cta_quote': 'Angebot in 24h', 'cta_chat': 'WhatsApp jetzt', 'form_title': 'Senden Sie Ihre Anforderungen', 'form_btn': 'Anfrage senden', 'privacy': 'Datenschutz', 'lead_notice': 'Landingpage für industrielle Verbindungselemente'},
    'es': {'html_lang': 'es', 'cta_quote': 'Cotización en 24h', 'cta_chat': 'WhatsApp ahora', 'form_title': 'Envíe sus requisitos', 'form_btn': 'Enviar solicitud', 'privacy': 'Política de privacidad', 'lead_notice': 'Página de cotización para tornillería industrial'},
    'fr': {'html_lang': 'fr', 'cta_quote': 'Devis en 24h', 'cta_chat': 'WhatsApp maintenant', 'form_title': 'Envoyez vos besoins', 'form_btn': 'Envoyer la demande', 'privacy': 'Politique de confidentialité', 'lead_notice': 'Page de devis pour fixations industrielles'},
    'ar': {'html_lang': 'ar', 'cta_quote': 'احصل على عرض خلال 24 ساعة', 'cta_chat': 'تواصل واتساب الآن', 'form_title': 'أرسل متطلباتك', 'form_btn': 'إرسال الطلب', 'privacy': 'سياسة الخصوصية', 'lead_notice': 'صفحة هبوط لطلبات المثبتات الصناعية'},
    'id': {'html_lang': 'id', 'cta_quote': 'Dapatkan penawaran 24 jam', 'cta_chat': 'WhatsApp sekarang', 'form_title': 'Kirim kebutuhan Anda', 'form_btn': 'Kirim permintaan', 'privacy': 'Kebijakan privasi', 'lead_notice': 'Halaman penawaran fastener industri'},
    'ja': {'html_lang': 'ja', 'cta_quote': '24時間以内に見積回答', 'cta_chat': 'WhatsApp で相談', 'form_title': 'ご要望を送信', 'form_btn': '送信する', 'privacy': 'プライバシーポリシー', 'lead_notice': '工業用ファスナー見積ページ'},
    'ko': {'html_lang': 'ko', 'cta_quote': '24시간 내 견적 회신', 'cta_chat': 'WhatsApp 바로 문의', 'form_title': '요구사항을 보내주세요', 'form_btn': '문의 제출', 'privacy': '개인정보처리방침', 'lead_notice': '산업용 패스너 견적 랜딩페이지'},
}


def build_html(lang, slug, title, subtitle, summary, meta_desc, keywords, bc_label, body, hero_image, whatsapp_url, extra_head):
    c = LC.get(lang, LC['en'])
    html_lang = c['html_lang']
    dir_attr = ' dir="rtl"' if lang == 'ar' else ''
    image_src = '../../../images/' + hero_image if hero_image else '../../../images/banner-hero.webp'
    head_extra = ('\n' + extra_head + '\n') if extra_head else ''

    return f'''<!DOCTYPE html>
<html lang="{html_lang}"{dir_attr}>
<head>
{make_hreflang(slug)}
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{he(title)} | WT Fasteners</title>
  <meta name="description" content="{he(meta_desc)}">
  <meta name="keywords" content="{he(keywords)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://wtscrews.com/pags/{lang}/landing/{slug}.html">
  <link rel="icon" type="image/x-icon" href="../../../favicon.ico">
  <meta property="og:title" content="{he(title)} | WT Fasteners">
  <meta property="og:description" content="{he(summary)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://wtscrews.com/pags/{lang}/landing/{slug}.html">
  <meta property="og:image" content="https://wtscrews.com/images/{he(hero_image) if hero_image else 'banner-hero.png'}">{head_extra}
  <style>
    :root {{
      --bg: #071427;
      --panel: #10223f;
      --line: rgba(255,255,255,.16);
      --text: #e8f0ff;
      --muted: #b8c6de;
      --cta: #22c55e;
      --cta2: #2563eb;
      --radius: 16px;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: "Inter","PingFang SC","Noto Sans SC",sans-serif;
      background: linear-gradient(180deg,#071427 0%,#081a33 100%);
      color: var(--text);
      line-height: 1.6;
      padding-bottom: 88px;
    }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 0 18px; }}
    .hero {{ padding: 28px 0 34px; }}
    .hero-grid {{ display: grid; grid-template-columns: 1.1fr .9fr; gap: 22px; }}
    .hero-copy, .hero-media, .section, .form-box {{
      background: rgba(255,255,255,.03);
      border: 1px solid var(--line);
      border-radius: 20px;
      box-shadow: 0 16px 42px rgba(0,0,0,.28);
    }}
    .hero-copy {{ padding: 24px; }}
    .hero-copy .badge {{
      display: inline-block;
      padding: 6px 11px;
      border-radius: 999px;
      border: 1px solid rgba(34,197,94,.52);
      background: rgba(34,197,94,.16);
      color: #8af0b1;
      font-size: .82rem;
      font-weight: 700;
      margin-bottom: 12px;
    }}
    h1 {{ font-size: clamp(1.7rem, 4vw, 2.7rem); line-height: 1.15; margin-bottom: 10px; }}
    .subtitle {{ color: var(--muted); margin-bottom: 10px; }}
    .summary {{ color: var(--muted); margin-bottom: 16px; }}
    .cta {{ display: flex; gap: 10px; flex-wrap: wrap; }}
    .btn {{
      display: inline-flex;
      justify-content: center;
      align-items: center;
      border: 0;
      border-radius: 11px;
      text-decoration: none;
      color: #fff;
      font-weight: 700;
      padding: 11px 16px;
    }}
    .btn.chat {{ background: var(--cta); }}
    .btn.quote {{ background: var(--cta2); }}
    .hero-media {{ padding: 12px; }}
    .hero-media img {{ width: 100%; height: 100%; min-height: 260px; object-fit: cover; border-radius: 12px; }}
    .section {{ margin-top: 18px; padding: 24px; }}
    .section h2 {{ margin-bottom: 12px; font-size: 1.35rem; }}
    .article-body :where(p,li) {{ color: var(--muted); margin-bottom: 10px; }}
    .article-body :where(h2,h3,h4) {{ margin: 16px 0 10px; }}
    .article-body img {{ max-width: 100%; height: auto; border-radius: 10px; border: 1px solid var(--line); }}
    .form-box {{ margin-top: 18px; padding: 20px; }}
    .form-box h3 {{ margin-bottom: 8px; }}
    .form-box p {{ color: var(--muted); margin-bottom: 10px; }}
    .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    input, textarea {{
      width: 100%;
      border: 1px solid rgba(255,255,255,.24);
      border-radius: 10px;
      padding: 10px 11px;
      background: rgba(255,255,255,.06);
      color: var(--text);
      font-size: .95rem;
    }}
    textarea {{ min-height: 110px; resize: vertical; }}
    .field {{ margin-bottom: 10px; }}
    .submit-btn {{
      width: 100%;
      background: var(--cta);
      color: #fff;
      border: 0;
      border-radius: 10px;
      padding: 12px 14px;
      font-weight: 800;
      cursor: pointer;
    }}
    .fixed-wa {{
      position: fixed;
      left: 0; right: 0; bottom: 12px;
      margin: 0 auto;
      max-width: 1100px;
      padding: 0 18px;
      z-index: 90;
    }}
    .fixed-wa-inner {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      border: 1px solid rgba(34,197,94,.52);
      background: rgba(7,20,39,.9);
      border-radius: 14px;
      padding: 10px 12px;
      backdrop-filter: blur(6px);
    }}
    .fixed-wa b {{ font-size: .92rem; }}
    .fixed-wa a {{
      text-decoration: none;
      color: #fff;
      background: var(--cta);
      border-radius: 9px;
      padding: 10px 13px;
      font-weight: 800;
    }}
    .foot {{ color: var(--muted); font-size: .84rem; margin: 20px 0 14px; }}
    @media (max-width: 860px) {{
      .hero-grid, .row {{ grid-template-columns: 1fr; }}
      .fixed-wa-inner {{ flex-direction: column; align-items: stretch; }}
      .fixed-wa a {{ text-align: center; }}
      body {{ padding-bottom: 130px; }}
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <div class="hero-grid">
        <article class="hero-copy">
          <span class="badge">{he(c['lead_notice'])}</span>
          <h1>{he(title)}</h1>
          <p class="subtitle">{he(subtitle)}</p>
          <p class="summary">{he(summary)}</p>
          <div class="cta">
            <a class="btn chat" href="{he(whatsapp_url)}" target="_blank" rel="noopener">{he(c['cta_chat'])}</a>
            <a class="btn quote" href="#lead-form">{he(c['cta_quote'])}</a>
          </div>
        </article>
        <aside class="hero-media">
          <img src="{he(image_src)}" alt="{he(title)}" loading="eager" fetchpriority="high">
        </aside>
      </div>
    </section>

    <section class="section">
      <h2>{he(bc_label or title)}</h2>
      <article class="article-body">
{body}
      </article>
    </section>

    <section class="form-box" id="lead-form">
      <h3>{he(c['form_title'])}</h3>
      <p>{he(summary)}</p>
      <form action="/cgi-bin/save.php" method="post" id="contactForm">
        <input type="hidden" name="lang" value="{lang}">
        <input type="hidden" name="utm_source" value="">
        <input type="hidden" name="utm_medium" value="">
        <input type="hidden" name="utm_campaign" value="">
        <input type="hidden" name="utm_content" value="">
        <input type="hidden" name="utm_term" value="">
        <input type="hidden" name="utm_id" value="">
        <input type="hidden" name="gclid" value="">
        <input type="hidden" name="gbraid" value="">
        <input type="hidden" name="wbraid" value="">
        <input type="hidden" name="fbclid" value="">
        <input type="hidden" name="landing_page" value="">
        <input type="hidden" name="page_path" value="">
        <input type="hidden" name="page_title" value="">
        <input type="hidden" name="referrer" value="">
        <div class="row">
          <div class="field"><input type="text" name="name" placeholder="Name *" required></div>
          <div class="field"><input type="email" name="email" placeholder="Email *" required></div>
        </div>
        <div class="row">
          <div class="field"><input type="text" name="company" placeholder="Company"></div>
          <div class="field"><input type="tel" name="phone" placeholder="Phone / WhatsApp"></div>
        </div>
        <div class="field"><textarea name="message" placeholder="Please describe specs, quantity and lead-time request *" required></textarea></div>
        <button class="submit-btn" type="submit">{he(c['form_btn'])}</button>
      </form>
    </section>

    <p class="foot"><a href="/pags/{lang}/privacy-policy.html" style="color:#b8c6de">{he(c['privacy'])}</a></p>
  </main>

  <div class="fixed-wa">
    <div class="fixed-wa-inner">
      <b>{he(c['cta_quote'])}</b>
      <a href="{he(whatsapp_url)}" target="_blank" rel="noopener">{he(c['cta_chat'])}</a>
    </div>
  </div>
  <script>
    (function () {{
      var TRACKING_KEYS = [
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'utm_id',
        'gclid', 'gbraid', 'wbraid', 'fbclid'
      ];
      var STORAGE_KEY = 'wt_lp_tracking_v1';

      function safeTrim(v) {{
        return String(v || '').trim();
      }}

      function parseTrackingFromQuery() {{
        var params = new URLSearchParams(window.location.search || '');
        var data = {{}};
        TRACKING_KEYS.forEach(function (key) {{
          var val = safeTrim(params.get(key));
          if (val) data[key] = val;
        }});
        return data;
      }}

      function readTrackingStore() {{
        try {{
          var raw = localStorage.getItem(STORAGE_KEY);
          if (!raw) return {{}};
          var obj = JSON.parse(raw);
          return obj && typeof obj === 'object' ? obj : {{}};
        }} catch (e) {{
          return {{}};
        }}
      }}

      function saveTrackingStore(obj) {{
        try {{
          localStorage.setItem(STORAGE_KEY, JSON.stringify(obj || {{}}));
        }} catch (e) {{
          // ignore storage issues
        }}
      }}

      function mergeTrackingData() {{
        var fromQuery = parseTrackingFromQuery();
        var fromStore = readTrackingStore();
        var merged = {{}};
        TRACKING_KEYS.forEach(function (key) {{
          merged[key] = safeTrim(fromQuery[key] || fromStore[key] || '');
        }});
        saveTrackingStore(merged);
        return merged;
      }}

      function setHidden(name, value) {{
        var fields = document.querySelectorAll('input[type="hidden"][name="' + name + '"]');
        fields.forEach(function (field) {{
          field.value = safeTrim(value);
        }});
      }}

      function fillTrackingHiddenFields(data) {{
        TRACKING_KEYS.forEach(function (key) {{
          setHidden(key, data[key] || '');
        }});
        setHidden('landing_page', window.location.href || '');
        setHidden('page_path', window.location.pathname || '');
        setHidden('page_title', document.title || '');
        setHidden('referrer', document.referrer || '');
      }}

      function trackEvent(eventName, label) {{
        if (typeof window.gtag === 'function') {{
          window.gtag('event', eventName, {{
            event_category: 'lead',
            event_label: label || '',
            transport_type: 'beacon'
          }});
          return;
        }}
        if (Array.isArray(window.dataLayer)) {{
          window.dataLayer.push({{
            event: eventName,
            event_category: 'lead',
            event_label: label || ''
          }});
        }}
      }}

      function buildWhatsAppText(baseText, data) {{
        var lines = [];
        var base = safeTrim(baseText);
        if (base) lines.push(base);
        if (data.utm_term) lines.push('Google keyword: ' + data.utm_term);
        if (data.utm_campaign) lines.push('Campaign: ' + data.utm_campaign);
        if (data.utm_content) lines.push('Ad group/creative: ' + data.utm_content);
        if (data.gclid) lines.push('GCLID: ' + data.gclid);
        if (!lines.length) lines.push('Hello, I am interested in your products.');
        return lines.join('\\n');
      }}

      function upgradeWhatsAppLinks(data) {{
        var waLinks = document.querySelectorAll('a[href*="wa.me/"]');
        waLinks.forEach(function (link) {{
          try {{
            var url = new URL(link.getAttribute('href') || '', window.location.origin);
            if (!/wa\\.me$/i.test(url.hostname)) return;
            var originalText = safeTrim(url.searchParams.get('text'));
            var trackedText = buildWhatsAppText(originalText, data);
            url.searchParams.set('text', trackedText);
            link.setAttribute('href', url.toString());
          }} catch (e) {{
            // skip invalid links
          }}

          link.addEventListener('click', function () {{
            var href = link.getAttribute('href') || 'wa_link';
            trackEvent('whatsapp_click', href);
          }});
        }});
      }}

      var trackingData = mergeTrackingData();
      fillTrackingHiddenFields(trackingData);
      upgradeWhatsAppLinks(trackingData);

      var form = document.getElementById('contactForm');
      if (form) {{
        form.addEventListener('submit', function () {{
          fillTrackingHiddenFields(trackingData);
          trackEvent('landing_form_submit', window.location.pathname || 'landing_form');
        }});
      }}
    }})();
  </script>
</body>
</html>
'''


def save_one(lang, slug, content):
    out_dir = os.path.join(BASE_DIR, 'pags', lang, 'landing')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, slug + '.html')
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(content)


try:
    cl = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    raw = sys.stdin.buffer.read(cl).decode('utf-8', errors='replace') if cl > 0 else ''
    form = parse_qs(raw, keep_blank_values=True)
except Exception as exc:
    respond({'success': False, 'error': f'POST parse error: {exc}'})

slug = re.sub(r'-+', '-', re.sub(r'[^a-z0-9-]', '-', g(form, 'slug').lower())).strip('-')
date = g(form, 'date') or datetime.now().strftime('%Y-%m-%d')
hero_image = g(form, 'hero_image') or g(form, 'og_image')
whatsapp_url = g(form, 'whatsapp_url') or 'https://wa.me/8615175432812?text=Hi%2C%20I%20need%20a%20quotation%20for%20fasteners.'
extra_head = g(form, 'extra_head')
auto_translate = truthy(g(form, 'auto_translate', '1'))
translated_langs_raw = g(form, 'translated_langs')
translated_langs_present = truthy(g(form, 'translated_langs_present', '0'))
translated_langs = []
if translated_langs_raw:
    for part in re.split(r'[\s,]+', translated_langs_raw):
        lang_code = str(part or '').strip().lower()
        if lang_code in LANGS and lang_code != 'en' and lang_code not in translated_langs:
            translated_langs.append(lang_code)
translated_langs_set = set(translated_langs)

en_title = g(form, 'en_title')
en_subtitle = g(form, 'en_subtitle')
en_summary = g(form, 'en_summary')
en_meta_desc = g(form, 'en_meta_desc') or en_summary
en_keywords = g(form, 'en_keywords')
en_bc_label = g(form, 'en_bc_label') or en_title
en_body = g(form, 'en_body')

if not slug:
    respond({'success': False, 'error': 'Slug 不能为空'})
if not en_title:
    respond({'success': False, 'error': '英文标题为必填项'})
if not en_summary:
    respond({'success': False, 'error': '英文摘要为必填项'})
if not en_body:
    respond({'success': False, 'error': '英文正文为必填项'})

source_fields = {
    'title': en_title,
    'subtitle': en_subtitle,
    'summary': en_summary,
    'meta_desc': en_meta_desc,
    'keywords': en_keywords,
    'bc_label': en_bc_label,
    'body': en_body,
}

errors = []
created = []

def values_for_lang(lang):
    return {
        'title': g(form, f'{lang}_title') or source_fields['title'],
        'subtitle': g(form, f'{lang}_subtitle') or source_fields['subtitle'],
        'summary': g(form, f'{lang}_summary') or source_fields['summary'],
        'meta_desc': g(form, f'{lang}_meta_desc') or source_fields['meta_desc'],
        'keywords': g(form, f'{lang}_keywords') or source_fields['keywords'],
        'bc_label': g(form, f'{lang}_bc_label') or source_fields['bc_label'],
        'body': g(form, f'{lang}_body') or source_fields['body'],
    }

if auto_translate:
    # First save EN quickly, then async translate others via existing worker.
    try:
        html = build_html(
            'en', slug,
            source_fields['title'], source_fields['subtitle'], source_fields['summary'],
            source_fields['meta_desc'], source_fields['keywords'], source_fields['bc_label'],
            source_fields['body'], hero_image, whatsapp_url, extra_head
        )
        save_one('en', slug, html)
        created.append('en')
    except Exception as exc:
        respond({'success': False, 'error': f'en: {exc}'})

    translating = True
    fork_error = None
    try:
        jobs_dir = os.path.join(BASE_DIR, '.translate-jobs')
        os.makedirs(jobs_dir, exist_ok=True)
        status_path = os.path.join(jobs_dir, slug + '-status.json')
        job_path = os.path.join(jobs_dir, slug + '-job.json')
        with open(status_path, 'w', encoding='utf-8') as sf:
            json.dump({
                'status': 'starting',
                'completed': [],
                'failed': {},
                'total': len(LANGS) - 1,
                'started_at': datetime.now().isoformat(),
            }, sf, ensure_ascii=False)

        job_data = {
            'slug': slug,
            'date': date,
            'og_image': hero_image,
            'article_section': g(form, 'article_section') or 'Landing Page',
            'extra_head': extra_head,
            'source_fields': source_fields,
            'langs': [l for l in LANGS if l != 'en'],
            'base_dir': BASE_DIR,
            'article_save_path': os.path.abspath(__file__),
            'status_path': status_path,
            # below fields are passed by translate-worker to this script on second pass
            'extra_params': {
                'whatsapp_url': whatsapp_url,
                'hero_image': hero_image,
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
        translating = False
        fork_error = str(exc)
else:
    translating = False
    target_langs = list(LANGS)
    if translated_langs_present:
        target_langs = ['en'] + [l for l in LANGS if l in translated_langs_set]
    for lang in target_langs:
        try:
            data = values_for_lang(lang)
            html = build_html(
                lang, slug,
                data['title'], data['subtitle'], data['summary'],
                data['meta_desc'], data['keywords'], data['bc_label'],
                data['body'], hero_image, whatsapp_url, extra_head
            )
            save_one(lang, slug, html)
            created.append(lang)
        except Exception as exc:
            errors.append(f'{lang}: {exc}')

# When worker calls this script with translated fields (auto_translate=0),
# save all languages with provided values.
out = {
    'success': len(created) > 0,
    'slug': slug,
    'created': created,
    'translating': translating,
    'errors': errors,
    'url': f'/pags/en/landing/{slug}.html',
}
if auto_translate and 'fork_error' in locals() and fork_error:
    out['errors'].append('translate fork failed: ' + fork_error)

respond(out)
