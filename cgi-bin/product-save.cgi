#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json, re, struct, subprocess
from datetime import datetime
from urllib.parse import parse_qs
from urllib import request as urlrequest
from urllib import error as urlerror
from json_store import update_pages_json, read_pages_data, JsonStoreError
from admin_auth import is_request_authenticated

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
TRANSLATION_ENV_FILES = [
  os.path.join(BASE_DIR, '.translation-env'),
  os.path.join(BASE_DIR, '.env.translation'),
]
_translation_env_loaded = False

sys.stdout.write("Content-Type: application/json; charset=utf-8\r\n\r\n")
sys.stdout.flush()

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
    def g(k, d=''):
        v = form.get(k, [d])
        return (v[0] if v else d).strip()
except Exception as e:
    respond({'success': False, 'error': 'POST parse error: ' + str(e)})

slug = re.sub(r'-+', '-', re.sub(r'[^a-z0-9-]', '-', g('slug').lower())).strip('-')
date = g('date') or datetime.now().strftime('%Y-%m-%d')
product_category = g('product_category') or 'Other Fasteners'
en_title = g('en_title')
en_subtitle = g('en_subtitle')
en_summary = g('en_summary')
en_meta = g('en_meta_desc') or en_summary
en_kw = g('en_keywords')
en_bc = g('en_bc_label') or en_title
en_body = g('en_body')
og_image = g('og_image')
auto_translate = g('auto_translate', '0')
force_translate_non_en = g('force_translate_non_en', '0')
translated_langs_raw = g('translated_langs', '')
translated_langs_present_raw = g('translated_langs_present', '0')
extra_head = g('extra_head')
applications_data = g('applications_data')
materials_data = g('materials_data')
size_chart_data = g('size_chart_data')
reviews_data = g('reviews_data')
related_products_data = g('related_products_data')
cta_title = g('cta_title')
cta_desc = g('cta_desc')
cta_button_text = g('cta_button_text')

if not slug:    respond({'success': False, 'error': 'Slug 不能为空'})
if not en_title: respond({'success': False, 'error': '英文标题为必填项'})
if not en_summary: respond({'success': False, 'error': '英文摘要为必填项'})
if not en_body:  respond({'success': False, 'error': '英文正文内容为必填项'})

LANGS = ['en', 'ar', 'de', 'es', 'fr', 'id', 'ja', 'ko', 'zh']
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

MON_EN = ['','January','February','March','April','May','June','July','August','September','October','November','December']
MON_ZH = ['','1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
MON_DE = ['','Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember']
MON_AR = ['','يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر']
MON_ES = ['','enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
MON_FR = ['','janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre']
MON_ID = ['','Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
MON_JA = ['','1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
MON_KO = ['','1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월']

def dfmt_en(y,m,d): return f'Published on {MON_EN[m]} {d}, {y}'
def dfmt_zh(y,m,d): return f'发布于 {y}年{MON_ZH[m]}{d}日'
def dfmt_de(y,m,d): return f'Veröffentlicht am {d}. {MON_DE[m]} {y}'
def dfmt_ar(y,m,d): return f'نشر في {d} {MON_AR[m]} {y}'
def dfmt_es(y,m,d): return f'Publicado el {d} de {MON_ES[m]} de {y}'
def dfmt_fr(y,m,d): return f'Publié le {d} {MON_FR[m]} {y}'
def dfmt_id(y,m,d): return f'Diterbitkan pada {d} {MON_ID[m]} {y}'
def dfmt_ja(y,m,d): return f'公開日：{y}年{MON_JA[m]}{d}日'
def dfmt_ko(y,m,d): return f'게시일: {y}년 {MON_KO[m]} {d}일'

LC = {
  'en': {
    'html_lang':'en','hreflang':'en','rtl':False,'date_fn':dfmt_en,
    'alt_logo':'Hebei Wangtu Metal Co., Ltd.',
    'nav':['Home','Products','News','About','Contact'],
    'bc_home':'Home','bc_news':'Products',
    'footer_desc':'Professional fastener manufacturer and exporter since 2005. Delivering quality bolts, screws, washers, and custom fasteners to customers worldwide.',
    'quick_links':'Quick Links','footer_about':'About Us','footer_contact':'Contact Us',
    'email_lbl':'Email','phone_lbl':'Phone','addr_lbl':'Address',
    'addr_val':'Yongnian District, Handan, Hebei, China',
    'copyright':'All Rights Reserved.','privacy':'Privacy Policy',
    'rec_products':'Recommended Products','view_details':'View Details →',
  },
  'zh': {
    'html_lang':'zh','hreflang':'zh-CN','rtl':False,'date_fn':dfmt_zh,
    'alt_logo':'WT Metal Co., Ltd.',
    'nav':['首页','产品','新闻','关于','联系'],
    'bc_home':'首页','bc_news':'产品',
    'footer_desc':'自2005年以来的专业紧固件制造商和出口商。为全球客户提供优质螺栓、螺钉、垫圈和定制紧固件。',
    'quick_links':'快捷链接','footer_about':'关于我们','footer_contact':'联系我们',
    'email_lbl':'电子邮件','phone_lbl':'电话','addr_lbl':'地址',
    'addr_val':'中国河北省邯郸市永年区',
    'copyright':'版权所有','privacy':'隐私政策',
    'rec_products':'推荐产品','view_details':'查看详情 →',
  },
  'de': {
    'html_lang':'de','hreflang':'de','rtl':False,'date_fn':dfmt_de,
    'alt_logo':'WT Metal Produkte Co., Ltd.',
    'nav':['Startseite','Produkte','Nachrichten','Über Uns','Kontakt'],
    'bc_home':'Startseite','bc_news':'Produkte',
    'footer_desc':'Professioneller Verbindungselemente-Hersteller und -Exporteur seit 2005.',
    'quick_links':'Schnelllinks','footer_about':'Über Uns','footer_contact':'Kontakt',
    'email_lbl':'E-Mail','phone_lbl':'Telefon','addr_lbl':'Adresse',
    'addr_val':'Yongnian District, Handan, Hebei, China',
    'copyright':'Alle Rechte vorbehalten.','privacy':'Datenschutzrichtlinie',
    'rec_products':'Empfohlene Produkte','view_details':'Details ansehen →',
  },
  'ar': {
    'html_lang':'ar','hreflang':'ar','rtl':True,'date_fn':dfmt_ar,
    'alt_logo':'WT Metal Co., Ltd.',
    'nav':['الرئيسية','المنتجات','الأخبار','عن الشركة','اتصل'],
    'bc_home':'الرئيسية','bc_news':'المنتجات',
    'footer_desc':'مصنّع ومصدّر متخصص لمنتجات التثبيت منذ عام 2005.',
    'quick_links':'روابط سريعة','footer_about':'عن الشركة','footer_contact':'اتصل بنا',
    'email_lbl':'البريد الإلكتروني','phone_lbl':'الهاتف','addr_lbl':'العنوان',
    'addr_val':'منطقة يونغنيان، هاندان، خيبي، الصين',
    'copyright':'جميع الحقوق محفوظة.','privacy':'سياسة الخصوصية',
    'rec_products':'المنتجات الموصى بها','view_details':'عرض التفاصيل ←',
  },
  'es': {
    'html_lang':'es','hreflang':'es','rtl':False,'date_fn':dfmt_es,
    'alt_logo':'WT Metal Co., Ltd.',
    'nav':['Inicio','Productos','Noticias','Nosotros','Contacto'],
    'bc_home':'Inicio','bc_news':'Productos',
    'footer_desc':'Fabricante y exportador profesional de sujetadores desde 2005.',
    'quick_links':'Accesos Rápidos','footer_about':'Sobre Nosotros','footer_contact':'Contáctenos',
    'email_lbl':'Correo','phone_lbl':'Teléfono','addr_lbl':'Dirección',
    'addr_val':'Yongnian District, Handan, Hebei, China',
    'copyright':'Todos los derechos reservados.','privacy':'Política de Privacidad',
    'rec_products':'Productos Recomendados','view_details':'Ver Detalles →',
  },
  'fr': {
    'html_lang':'fr','hreflang':'fr','rtl':False,'date_fn':dfmt_fr,
    'alt_logo':'WT Metal Co., Ltd.',
    'nav':['Accueil','Produits','Actualités','À propos','Contact'],
    'bc_home':'Accueil','bc_news':'Produits',
    'footer_desc':'Fabricant et exportateur professionnel de fixations depuis 2005.',
    'quick_links':'Liens Rapides','footer_about':'À Propos','footer_contact':'Nous Contacter',
    'email_lbl':'Email','phone_lbl':'Téléphone','addr_lbl':'Adresse',
    'addr_val':'District Yongnian, Handan, Hebei, Chine',
    'copyright':'Tous droits réservés.','privacy':'Politique de Confidentialité',
    'rec_products':'Produits Recommandés','view_details':'Voir les Détails →',
  },
  'id': {
    'html_lang':'id','hreflang':'id','rtl':False,'date_fn':dfmt_id,
    'alt_logo':'WT Metal Co., Ltd.',
    'nav':['Beranda','Produk','Berita','Tentang','Kontak'],
    'bc_home':'Beranda','bc_news':'Produk',
    'footer_desc':'Produsen dan eksportir pengencang profesional sejak 2005.',
    'quick_links':'Tautan Cepat','footer_about':'Tentang Kami','footer_contact':'Hubungi Kami',
    'email_lbl':'Email','phone_lbl':'Telepon','addr_lbl':'Alamat',
    'addr_val':'Distrik Yongnian, Handan, Hebei, China',
    'copyright':'Semua Hak Dilindungi.','privacy':'Kebijakan Privasi',
    'rec_products':'Produk yang Direkomendasikan','view_details':'Lihat Detail →',
  },
  'ja': {
    'html_lang':'ja','hreflang':'ja','rtl':False,'date_fn':dfmt_ja,
    'alt_logo':'WT Metal Co., Ltd.',
    'nav':['ホーム','製品','ニュース','会社情報','お問い合わせ'],
    'bc_home':'ホーム','bc_news':'製品',
    'footer_desc':'2005年より専門的なファスナーメーカー・輸出業者として活動しています。',
    'quick_links':'クイックリンク','footer_about':'会社情報','footer_contact':'お問い合わせ',
    'email_lbl':'メール','phone_lbl':'電話','addr_lbl':'住所',
    'addr_val':'中国河北省邯郸市永年区',
    'copyright':'All Rights Reserved.','privacy':'プライバシーポリシー',
    'rec_products':'おすすめ製品','view_details':'詳細を見る →',
  },
  'ko': {
    'html_lang':'ko','hreflang':'ko','rtl':False,'date_fn':dfmt_ko,
    'alt_logo':'WT Metal Co., Ltd.',
    'nav':['홈','제품','뉴스','회사소개','문의'],
    'bc_home':'홈','bc_news':'제품',
    'footer_desc':'2005년부터 전문 파스너 제조사 및 수출업체입니다.',
    'quick_links':'빠른 링크','footer_about':'회사 소개','footer_contact':'문의하기',
    'email_lbl':'이메일','phone_lbl':'전화','addr_lbl':'주소',
    'addr_val':'중국 허베이성 한단시 용년구',
    'copyright':'All Rights Reserved.','privacy':'개인정보 처리방침',
    'rec_products':'추천 제품','view_details':'자세히 보기 →',
  },
}

def truthy(value):
  return str(value or '').strip().lower() in {'1', 'true', 'yes', 'on'}

def load_translation_env_files():
  global _translation_env_loaded
  if _translation_env_loaded:
    return
  _translation_env_loaded = True
  for env_path in TRANSLATION_ENV_FILES:
    if not os.path.exists(env_path):
      continue
    try:
      with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    except Exception:
      continue
    for raw_line in lines:
      line = raw_line.strip()
      if not line or line.startswith('#') or '=' not in line:
        continue
      key, value = line.split('=', 1)
      key = key.strip()
      value = value.strip()
      if not key:
        continue
      if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
      os.environ.setdefault(key, value)

def pick_translation_api_key():
  load_translation_env_files()
  return (
    os.environ.get('WT_TRANSLATE_API_KEY', '').strip()
    or os.environ.get('DEEPSEEK_API_KEY', '').strip()
    or os.environ.get('OPENAI_API_KEY', '').strip()
  )

def pick_translation_api_url():
  load_translation_env_files()
  explicit_url = (
    os.environ.get('WT_TRANSLATE_API_URL', '').strip()
    or os.environ.get('DEEPSEEK_API_URL', '').strip()
    or os.environ.get('OPENAI_API_URL', '').strip()
  )
  if explicit_url:
    return explicit_url
  base_url = (
    os.environ.get('WT_TRANSLATE_API_BASE', '').strip()
    or os.environ.get('DEEPSEEK_API_BASE', '').strip()
    or os.environ.get('OPENAI_BASE_URL', '').strip()
  )
  if base_url:
    return base_url.rstrip('/') + '/chat/completions'
  if os.environ.get('DEEPSEEK_API_KEY', '').strip():
    return 'https://api.deepseek.com/chat/completions'
  if os.environ.get('OPENAI_API_KEY', '').strip():
    return 'https://api.openai.com/v1/chat/completions'
  return ''

def pick_translation_model():
  load_translation_env_files()
  return (
    os.environ.get('WT_TRANSLATE_MODEL', '').strip()
    or os.environ.get('DEEPSEEK_MODEL', '').strip()
    or os.environ.get('OPENAI_MODEL', '').strip()
    or ('deepseek-chat' if os.environ.get('DEEPSEEK_API_KEY', '').strip() else '')
    or 'gpt-4o-mini'
  )

def extract_json_object(raw_text):
  text = (raw_text or '').strip()
  if not text:
    raise ValueError('translation model returned empty content')
  try:
    return json.loads(text)
  except Exception:
    match = re.search(r'\{.*\}', text, re.S)
    if not match:
      raise ValueError('translation model did not return valid JSON')
    return json.loads(match.group(0))

def translate_fields(lang, source_fields):
  api_key = pick_translation_api_key()
  api_url = pick_translation_api_url()
  if not api_key or not api_url:
    raise RuntimeError('自动翻译已启用，但服务器未配置 WT_TRANSLATE_API_KEY / WT_TRANSLATE_API_URL、DEEPSEEK_API_KEY / DEEPSEEK_API_BASE，或 OPENAI_API_KEY / OPENAI_BASE_URL')
  target_name = LANG_LABELS.get(lang, lang)
  body_text = source_fields.get('body', '')
  img_masks = []

  def mask_img(match):
    img_masks.append(match.group(0))
    return f'__IMG_MASK_{len(img_masks) - 1}__'

  masked_source_fields = dict(source_fields)
  masked_source_fields['body'] = re.sub(r'<img\s+[^>]*>', mask_img, body_text)
  system_prompt = (
    'You are a professional website localization translator for industrial fastener product pages. '
    'Translate English source content into the requested target language and return strict JSON only.'
  )
  user_prompt = (
    f'Target language: {target_name} ({lang}).\n'
    'Return exactly one JSON object with keys: title, subtitle, summary, meta_desc, keywords, bc_label, body.\n'
    'Rules:\n'
    '1. Preserve HTML structure in body exactly: keep tag names, nesting, href, src, class, id, style, loading, and relative paths unchanged. Do not alter placeholders like __IMG_MASK_0__.\n'
    '2. Translate only human-readable text content. Do not translate URLs, filenames, product standards, model numbers, or brand names like WT Fasteners.\n'
    '3. Keep measurements, units, dates, percentages, DIN/ISO/ASTM codes, and punctuation formatting appropriate for the target language.\n'
    '4. keywords must stay a comma-separated SEO keyword string in the target language.\n'
    '5. meta_desc should remain concise and suitable for a meta description.\n'
    '6. If subtitle is empty, return an empty string for subtitle.\n'
    '7. Output JSON only, with no markdown fences or explanations.\n\n'
    'Source JSON:\n'
    + json.dumps(masked_source_fields, ensure_ascii=False)
  )
  payload = {
    'model': pick_translation_model(),
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

  try:
    with urlrequest.urlopen(req, timeout=120) as resp:
      raw_resp = resp.read().decode('utf-8', errors='replace')
  except urlerror.HTTPError as exc:
    detail = exc.read().decode('utf-8', errors='replace')
    raise RuntimeError(f'{target_name} 翻译请求失败: HTTP {exc.code} {detail[:300]}')
  except Exception as exc:
    raise RuntimeError(f'{target_name} 翻译请求失败: {exc}')

  try:
    data = json.loads(raw_resp)
    content = data['choices'][0]['message']['content']
  except Exception as exc:
    raise RuntimeError(f'{target_name} 翻译响应解析失败: {exc}')

  translated = extract_json_object(content)
  if 'body' in translated:
    def restore_img(match):
      idx = int(match.group(1))
      if 0 <= idx < len(img_masks):
        return img_masks[idx]
      return match.group(0)

    translated['body'] = re.sub(r'__IMG_MASK_(\d+)__', restore_img, translated['body'])
  missing = [field for field in TRANSLATABLE_FIELDS if field not in translated]
  if missing:
    raise RuntimeError(f"{target_name} 翻译结果缺少字段: {', '.join(missing)}")
  return {field: str(translated.get(field, '') or '') for field in TRANSLATABLE_FIELDS}

def he(s):
    return s.replace('&','&amp;').replace('"','&quot;').replace('<','&lt;').replace('>','&gt;')

def je(s):
    return s.replace('\\','\\\\').replace('"','\\"')

def build_head_extra(extra_head):
  snippet = (extra_head or '').strip()
  if not snippet:
    return ''
  return '\n  <!-- Custom Head Snippet -->\n' + snippet + '\n  <!-- End Custom Head Snippet -->'

def build_hreflang(slug, all_langs):
    hm = {'en':'en','ar':'ar','de':'de','es':'es','fr':'fr','id':'id','ja':'ja','ko':'ko','zh':'zh-CN'}
    lines = [f'  <link rel="alternate" hreflang="{hm[l]}" href="/pags/{l}/products/{slug}.html">' for l in all_langs]
    lines.append(f'  <link rel="alternate" hreflang="x-default" href="/pags/en/products/{slug}.html">')
    return '\n'.join(lines)

DEFAULT_APPLICATIONS_DATA = '''
🏢|Building Construction|Structural connections, facade mounting, equipment installation
🏗️|Infrastructure|Bridges, highway barriers, railings, sign posts
🏭|Industrial|Equipment anchoring, conveyor systems, machinery bases
⚡|Energy|Solar panel mounting, wind turbine bases, utility poles
🏠|Residential|Deck mounting, fence posts, garage door installation
🚧|Renovation|Wall mounting, ceiling fixtures, bathroom installations
'''.strip()

DEFAULT_MATERIALS_DATA = '''
Carbon Steel|Grade 4.8, 8.8, 10.9;Good strength, cost-effective;Zinc plated for corrosion resistance
Stainless Steel 304|A2-70, A2-80;Excellent corrosion resistance;Suitable for indoor/outdoor use
Stainless Steel 316|A4-70, A4-80;Superior marine corrosion resistance;Chloride and acid resistant
Hot-Dip Galvanized|Heavy-duty corrosion protection;Suitable for outdoor applications;Extended service life
'''.strip()

DEFAULT_SIZE_CHART_DATA = '''
M6|1.0 mm|50 - 150 mm|12 kN|8 kN|40 mm
M8|1.25 mm|60 - 200 mm|18 kN|12 kN|50 mm
M10|1.5 mm|80 - 250 mm|25 kN|18 kN|60 mm
M12|1.75 mm|100 - 300 mm|35 kN|24 kN|70 mm
M16|2.0 mm|120 - 350 mm|45 kN|32 kN|80 mm
M20|2.5 mm|150 - 400 mm|50 kN|40 kN|100 mm
M24|3.0 mm|180 - 400 mm|55 kN|45 kN|100 mm
'''.strip()

DEFAULT_REVIEWS_DATA = '''
Michael Johnson|January 15, 2026|Excellent quality anchor bolts. Used them for installing solar panel mounts and they held up perfectly. Fast delivery and well-packaged.|5
Sarah Williams|December 8, 2025|We ordered M12 and M16 anchor bolts for our construction project. The quality exceeded our expectations. Will definitely order again.|5
'''.strip()

DEFAULT_RELATED_PRODUCTS_DATA = '''
hex-bolts|Hex Bolts|Full and partial thread hex bolts in DIN 931/933, ISO 4014/4017. Grades 4.8 to 12.9, sizes M4–M64.|products/bolts/Hex Bolt0_sm.webp
flange-bolts|Flange Bolts|Serrated and non-serrated flange bolts per DIN 6921 / ISO 1665. Built-in washer face for vibration resistance.|products/bolts/Flange Bolt1_sm.webp
high-strength-bolts|High Strength Bolts|High strength structural bolts for heavy-duty applications. Grade 8.8, 10.9, 12.9 available.|products/bolts/High Strength Bolt1_sm.webp
'''.strip()

def split_structured_lines(raw, default=''):
    source = (raw or '').strip() or (default or '').strip()
    return [line.strip() for line in source.splitlines() if line.strip() and not line.strip().startswith('#')]

def normalize_image_path(path):
    p = (path or '').strip()
    p = re.sub(r'^\s*https?://[^/]+/images/', '', p, flags=re.I)
    p = re.sub(r'^/?images/', '', p, flags=re.I)
    return p.lstrip('/')

def get_image_dimensions(image_path):
    rel = normalize_image_path(image_path)
    if not rel:
        return None
    abs_path = os.path.join(BASE_DIR, 'images', rel)
    if not os.path.exists(abs_path):
        return None
    try:
        with open(abs_path, 'rb') as f:
            header = f.read(32)
            if header.startswith(b'\x89PNG\r\n\x1a\n') and len(header) >= 24:
                return struct.unpack('>II', header[16:24])
            if header[:6] in (b'GIF87a', b'GIF89a') and len(header) >= 10:
                return struct.unpack('<HH', header[6:10])
            if header.startswith(b'RIFF') and header[8:12] == b'WEBP':
                chunk = header[12:16]
                if chunk == b'VP8X' and len(header) >= 30:
                    width = 1 + int.from_bytes(header[24:27], 'little')
                    height = 1 + int.from_bytes(header[27:30], 'little')
                    return (width, height)
                if chunk == b'VP8L' and len(header) >= 25:
                    b0, b1, b2, b3 = header[21:25]
                    width = 1 + (((b1 & 0x3F) << 8) | b0)
                    height = 1 + (((b3 & 0x0F) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
                    return (width, height)
                if chunk == b'VP8 ' and len(header) >= 30:
                    width = struct.unpack('<H', header[26:28])[0] & 0x3FFF
                    height = struct.unpack('<H', header[28:30])[0] & 0x3FFF
                    return (width, height)
            if header[:2] == b'\xff\xd8':
                f.seek(2)
                while True:
                    marker_prefix = f.read(1)
                    if not marker_prefix:
                        break
                    if marker_prefix != b'\xff':
                        continue
                    marker = f.read(1)
                    while marker == b'\xff':
                        marker = f.read(1)
                    if not marker or marker in (b'\xd8', b'\xd9'):
                        continue
                    length_bytes = f.read(2)
                    if len(length_bytes) != 2:
                        break
                    length = struct.unpack('>H', length_bytes)[0]
                    if marker in (b'\xc0', b'\xc1', b'\xc2', b'\xc3', b'\xc5', b'\xc6', b'\xc7', b'\xc9', b'\xca', b'\xcb', b'\xcd', b'\xce', b'\xcf'):
                        payload = f.read(5)
                        if len(payload) == 5:
                            height, width = struct.unpack('>HH', payload[1:5])
                            return (width, height)
                        break
                    f.seek(length - 2, os.SEEK_CUR)
    except Exception:
        return None
    return None

def enrich_img_tag(match):
    tag = match.group(0)
    if re.search(r'\bwidth\s*=', tag, flags=re.I) and re.search(r'\bheight\s*=', tag, flags=re.I):
        return tag
    src_match = re.search(r'\bsrc\s*=\s*["\']([^"\']+)["\']', tag, flags=re.I)
    if not src_match:
        return tag
    src = src_match.group(1).strip()
    if not src or src.startswith('data:'):
        return tag
    dims = get_image_dimensions(src)
    if not dims:
        return tag
    insert = ''
    if not re.search(r'\bwidth\s*=', tag, flags=re.I):
        insert += f' width="{dims[0]}"'
    if not re.search(r'\bheight\s*=', tag, flags=re.I):
        insert += f' height="{dims[1]}"'
    return re.sub(r'(?i)<img\b', '<img' + insert, tag, count=1)

def prepare_body_html(raw_html):
    html = raw_html or ''
    return re.sub(r'(?is)<img\b[^>]*>', enrich_img_tag, html)

def render_applications_html(raw):
    cards = []
    for line in split_structured_lines(raw, DEFAULT_APPLICATIONS_DATA):
        parts = [p.strip() for p in line.split('|')]
        icon = parts[0] if len(parts) > 0 else '📦'
        title = parts[1] if len(parts) > 1 else ''
        desc = parts[2] if len(parts) > 2 else ''
        if not title and not desc:
            continue
        cards.append(f'''            <article class="application-card">
              <div class="app-icon">{he(icon or '📦')}</div>
              <section>
                <h4>{he(title)}</h4>
                <p>{he(desc)}</p>
              </section>
            </article>''')
    return '\n'.join(cards)

def render_materials_html(raw):
    cards = []
    for line in split_structured_lines(raw, DEFAULT_MATERIALS_DATA):
        parts = [p.strip() for p in line.split('|')]
        title = parts[0] if len(parts) > 0 else ''
        bullets = []
        if len(parts) > 1:
            bullets = [item.strip() for item in '|'.join(parts[1:]).split(';') if item.strip()]
        if not title:
            continue
        lis = '\n'.join([f'                <li>{he(item)}</li>' for item in bullets])
        cards.append(f'''            <article class="material-card">
              <h4>{he(title)}</h4>
              <ul>
{lis}
              </ul>
            </article>''')
    return '\n'.join(cards)

def render_size_chart_html(raw):
    rows_html = []
    for line in split_structured_lines(raw, DEFAULT_SIZE_CHART_DATA):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 6:
            continue
        cols = ''.join([f'<td>{he(col)}</td>' for col in parts[:6]])
        rows_html.append(f'                <tr>{cols}</tr>')
    return '\n'.join(rows_html)

def render_reviews_html(raw):
    cards = []
    for line in split_structured_lines(raw, DEFAULT_REVIEWS_DATA):
        parts = [p.strip() for p in line.split('|')]
        name = parts[0] if len(parts) > 0 else ''
        date_label = parts[1] if len(parts) > 1 else ''
        content = parts[2] if len(parts) > 2 else ''
        try:
            rating_num = int(parts[3]) if len(parts) > 3 and parts[3] else 5
        except Exception:
            rating_num = 5
        rating_num = max(1, min(5, rating_num))
        if not name and not content:
            continue
        cards.append(f'''            <article class="review-card">
              <header class="review-header">
                <div class="review-rating">{'★' * rating_num}</div>
                <section class="review-info">
                  <h4>{he(name)}</h4>
                  <p class="review-date">{he(date_label)}</p>
                </section>
              </header>
              <p>"{he(content)}"</p>
            </article>''')
    return '\n'.join(cards)

def render_related_html(raw):
    cards = []
    for line in split_structured_lines(raw, DEFAULT_RELATED_PRODUCTS_DATA):
        parts = [p.strip() for p in line.split('|')]
        slug = parts[0] if len(parts) > 0 else ''
        title = parts[1] if len(parts) > 1 else ''
        summary = parts[2] if len(parts) > 2 else ''
        image = normalize_image_path(parts[3] if len(parts) > 3 else '')
        if not slug and not title:
            continue
        href = slug if slug.endswith('.html') else (slug + '.html' if slug else '#')
        image_rel = image or 'logo.jpg'
        image_src = f'../../../images/{he(image_rel)}'
        image_dims = get_image_dimensions(image_rel) or (400, 400)
        cards.append(f'''        <a href="{he(href)}" class="related-card">
          <div class="related-card-image">
            <img src="{image_src}" alt="{he(title)}" loading="lazy" width="{image_dims[0]}" height="{image_dims[1]}" style="width:100%;height:100%;object-fit:cover;">
          </div>
          <div class="related-card-body">
            <h4>{he(title)}</h4>
            <p>{he(summary)}</p>
            <span class="related-card-link">View Details →</span>
          </div>
        </a>''')
    return '\n'.join(cards)

def build_html(lang, slug, date_str, title, subtitle, summary, meta_desc, keywords, bc_label, body, all_langs, og_image='', product_category='Other Fasteners', extra_head='', applications_data='', materials_data='', size_chart_data='', reviews_data='', related_products_data='', cta_title='', cta_desc='', cta_button_text=''):
    c = LC[lang]
    hl = c['html_lang']
    dir_attr = ' dir="rtl"' if c['rtl'] else ''
    n = c['nav']
    y, m, d = int(date_str[:4]), int(date_str[5:7]), int(date_str[8:10])
    date_display = c['date_fn'](y, m, d)
    hreflang = build_hreflang(slug, all_langs)
    og_img_url = f'https://wtscrews.com/images/{og_image}' if og_image else 'https://wtscrews.com/images/og-cover.jpg'
    hero_image_rel = normalize_image_path(og_image or 'og-cover.jpg')
    hero_image_dims = get_image_dimensions(hero_image_rel) or (1500, 1500)
    body_html = prepare_body_html(body)
    extra_head_block = build_head_extra(extra_head)
    applications_html = render_applications_html(applications_data)
    materials_html = render_materials_html(materials_data)
    size_chart_html = render_size_chart_html(size_chart_data)
    reviews_html = render_reviews_html(reviews_data)
    related_html = render_related_html(related_products_data)
    cta_title_text = cta_title or 'Need a Custom Product?'
    cta_desc_text = cta_desc or 'We can manufacture products to your exact specifications — just send us the details.'
    cta_button_text_value = cta_button_text or 'Contact Our Team'
    json_ld = {
      '@context': 'https://schema.org',
      '@type': 'Product',
      'name': title,
      'description': summary,
      'image': og_img_url,
      'brand': {'@type': 'Brand', 'name': 'WT Fasteners'},
      'manufacturer': {'@type': 'Organization', 'name': 'WT Fasteners', 'url': 'https://wtscrews.com'},
      'category': product_category,
      'offers': {
        '@type': 'Offer',
        'priceCurrency': 'USD',
        'priceSpecification': {
          '@type': 'UnitPriceSpecification',
          'eligibleQuantity': {'@type': 'QuantitativeValue', 'minValue': 10, 'unitCode': 'KGM'},
        },
        'seller': {'@type': 'Organization', 'name': 'WT Fasteners'},
      },
    }
    json_ld_json = json.dumps(json_ld, ensure_ascii=False, indent=2)
    return f'''<!DOCTYPE html>
<html lang="{hl}"{dir_attr}>
<head>
{hreflang}
  <meta charset="UTF-8">
  <link rel="icon" type="image/x-icon" href="../../../favicon.ico">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{he(title)} — WT Fasteners</title>
  <meta name="description" content="{he(meta_desc)}">
  <meta name="keywords" content="{he(keywords)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://wtscrews.com/pags/{lang}/products/{slug}.html">
  <link rel="sitemap" type="application/xml" href="../../../sitemap.xml">
  <meta name="geo.region" content="CN">
  <meta name="geo.placename" content="China">
  <meta name="geo.position" content="30.2741;120.1551">
  <meta name="ICBM" content="30.2741, 120.1551">
  <meta property="og:title" content="{he(title)} — WT Fasteners">
  <meta property="og:description" content="{he(summary)}">
  <meta property="og:type" content="product">
  <meta property="og:url" content="https://wtscrews.com/pags/{lang}/products/{slug}.html">
  <script type="application/ld+json">
{json_ld_json}
  </script>
  <meta property="og:image" content="{og_img_url}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <link rel="preload" as="image" href="../../../images/{he(hero_image_rel)}" fetchpriority="high">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=optional">
  <style>
:root{{--blue-900:#0a1628;--blue-800:#0f2140;--blue-700:#163264;--blue-500:#2563eb;--blue-400:#3b82f6;--blue-300:#60a5fa;--white:#ffffff;--text:#1e293b;--radius:6px;--radius-lg:12px;--header-h:76px;--transition:0.3s cubic-bezier(.4,0,.2,1)}}
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
html{{scroll-behavior:smooth;font-size:16px}}
body{{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:var(--text);background:var(--white);line-height:1.65;-webkit-font-smoothing:antialiased}}
img{{max-width:100%;height:auto;display:block}}
a{{text-decoration:none;color:inherit}}
ul{{list-style:none}}
.site-header{{position:fixed;top:0;left:0;right:0;z-index:1000;background:transparent}}
.nav{{display:flex;align-items:center;justify-content:space-between;height:var(--header-h)}}
.logo{{display:flex;align-items:center}}
.logo img{{height:44px;width:auto}}
.hero{{position:relative;min-height:100vh;display:flex;align-items:center;background:linear-gradient(165deg,var(--blue-900) 0%,var(--blue-800) 40%,var(--blue-700) 100%);color:var(--white);overflow:hidden}}
.page-hero,.inner-hero{{background:linear-gradient(165deg,var(--blue-900) 0%,var(--blue-800) 40%,var(--blue-700) 100%);color:var(--white)}}
.container{{max-width:1220px;margin:0 auto;padding:0 24px}}
</style>
  <link rel="stylesheet" href="../../../css/base.css">
  <link rel="stylesheet" href="../../../css/common.css">
  <link rel="stylesheet" href="../../../css/product-detail.css">
  <!-- Facebook Meta Pixel Code -->
  <script>
  !function(f,b,e,v,n,t,s)
  {{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
  n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t,s)}}(window, document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', '1626729111828175');
  fbq('track', 'PageView');
  </script>
  <noscript><img height="1" width="1" style="display:none"
  src="https://www.facebook.com/tr?id=1626729111828175&ev=PageView&noscript=1"
  /></noscript>
  <!-- End Meta Pixel Code -->
{extra_head_block}
</head>
<body>

  <header class="site-header" id="siteHeader">
    <nav class="container nav">
      <a href="../../../index.html" class="logo"><img src="../../../images/logo_sm.webp" alt="Hebei Wangtu Metal Co., Ltd." width="88" height="88"></a>
      <button class="menu-toggle" id="menuToggle" aria-label="Toggle navigation menu">
        <span></span><span></span><span></span>
      </button>
      <ul class="nav-links" id="navLinks">
        <li><a href="../index.html">{n[0]}</a></li>
        <li><a href="../products.html">{n[1]}</a></li>
        <li><a href="../news.html">{n[2]}</a></li>
        <li><a href="../about.html">{n[3]}</a></li>
        <li><a href="../contact.html">{n[4]}</a></li>
      </ul>
      <div class="lang-select">
        <select id="langSwitcher" onchange="switchLanguage(this.value)">
          
          
        </select>
      </div>
    </nav>
  </header>
  <div class="header-spacer" aria-hidden="true"></div>

  <main>
    <section class="page-header">
      <article class="container">
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </article>
    </section>

    <nav class="breadcrumb">
      <article class="container">
        <a href="../index.html">{c['bc_home']}</a>
        <span>/</span>
        <a href="../products.html">{c['bc_news']}</a>
        <span>/</span>
        {bc_label}
      </article>
    </nav>

    <section class="section">
      <article class="container product-detail">
        <figure class="product-gallery fade-in"><img src="../../../images/{he(hero_image_rel)}" alt="{he(title)}" width="{hero_image_dims[0]}" height="{hero_image_dims[1]}" fetchpriority="high"></figure>
        <section class="product-info fade-in">
          <h2>{title}</h2>
          <p>{summary}</p>
          {body_html}
          <a href="../contact.html" class="btn btn-primary">Request a Quote</a>
        </section>
      </article>
    </section>

    <!-- Applications Section -->
    <section class="section">
      <article class="container">
        <section class="applications-section">
          <h3>Applications</h3>
          <section class="applications-grid">
{applications_html}
          </section>
        </section>
      </article>
    </section>

    <!-- Materials & Grades Section -->
    <section class="section">
      <article class="container">
        <section class="materials-section">
          <h3>Materials & Grades</h3>
          <section class="materials-grid">
{materials_html}
          </section>
        </section>
      </article>
    </section>

    <!-- Size Chart Section -->
    <section class="section">
      <article class="container">
        <section class="size-chart-section">
          <h3>Size Chart</h3>
          <div class="size-chart">
            <table>
              <thead>
                <tr>
                  <th>Size</th>
                  <th>Thread</th>
                  <th>Length Range</th>
                  <th>Pull-out Strength</th>
                  <th>Shear Strength</th>
                  <th>Embedment</th>
                </tr>
              </thead>
              <tbody>
{size_chart_html}
              </tbody>
            </table>
          </div>
        </section>
      </article>
    </section>

    <!-- Customer Reviews Section -->
    <section class="section">
      <article class="container">
        <section class="customer-reviews">
          <h3>Customer Reviews</h3>
          <section class="reviews-grid">
{reviews_html}
          </section>
        </section>
      </article>
    </section>

    
    <!-- Related Products -->
    <section class="section">
      <article class="container">
        <div class="related-products">
          <h3>Related Products</h3>
          <div class="related-grid">
{related_html}
          </div>
        </div>
      </article>
    </section>
<section class="cta-section">
      <article class="container">
        <h2>{he(cta_title_text)}</h2>
        <p>{he(cta_desc_text)}</p>
        <a href="../contact.html" class="btn btn-primary">{he(cta_button_text_value)}</a>
      </article>
    </section>
  </main>

  <footer class="site-footer">
    <section class="container footer-grid">
      <article class="footer-col">
        <h3>WT Fasteners</h3>
        <p>Professional fastener manufacturer and exporter since 2005.</p>
      </article>
      <article class="footer-col">
        <h3>Quick Links</h3>
        <ul>
          <li><a href="../index.html">Home</a></li>
          <li><a href="../products.html">Products</a></li>
          <li><a href="../news.html">News</a></li>
          <li><a href="../about.html">About Us</a></li>
          <li><a href="../contact.html">Contact</a></li>
        </ul>
      </article>
      <article class="footer-col">
        <h3>Products</h3>
        <ul>
          <li><a href="hex-bolts.html">Hex Bolts</a></li>
          <li><a href="flange-bolts.html">Flange Bolts</a></li>
          <li><a href="{slug}.html">Anchor Bolts</a></li>
        </ul>
      </article>
      <article class="footer-col">
        <h3>Contact Us</h3>
        <p>Email: info&#64;wtbolts.com</p>
        <p>Email: lipbolts&#64;gmail.com</p>
        <p>Phone: +8615175432812</p>
      </article>
    </section>
    <section class="footer-bottom">
      <p class="container">&copy; 2026 WT Fasteners. All Rights Reserved.</p>
    </section>
  </footer>

  <script src="../../../js/i18n-config.js" defer></script>
  <script src="../../../js/detail-page.js" defer></script>
  <script src="../../../js/chat-dock.js" defer></script>
</body>
</html>'''

def update_json(json_path, slug, title, summary, og_image='', product_category='Other Fasteners'):
    category_slug = 'products/' + slug

    def mutator(data):
        for category in data.get('products', []):
            category['items'] = [item for item in category.get('items', []) if item.get('slug') != category_slug]
        target_category = None
        for category in data.get('products', []):
            if category.get('category') == product_category:
                target_category = category
                break
        if target_category is None:
            target_category = {
                'category': product_category,
                'icon': 'images/products/others/Solid Rivet1.webp',
                'items': [],
            }
            data.setdefault('products', []).insert(0, target_category)
        target_category.setdefault('items', []).insert(0, {
            'slug': category_slug,
            'title': title,
            'summary': summary,
            'icon': f'../../images/{og_image}' if og_image else '../../images/logo.jpg',
        })
        return data

    update_pages_json(json_path, mutator)


def verify_product_outputs(lang, products_dir, html_path, json_path, slug):
    expected_slug = 'products/' + slug
    safe_products_dir = os.path.abspath(products_dir)
    safe_html_path = os.path.abspath(html_path)
    if os.path.commonpath([safe_products_dir, safe_html_path]) != safe_products_dir:
        return f'{lang}: html path escaped products dir'
    if os.path.dirname(safe_html_path) != safe_products_dir:
        return f'{lang}: html not under /pags/{lang}/products/'
    if not os.path.exists(safe_html_path):
        return f'{lang}: html file not written'
    if not safe_html_path.endswith(os.sep + slug + '.html'):
        return f'{lang}: html filename mismatch'
    try:
        pages = read_pages_data(json_path)
    except Exception as exc:
        return f'{lang}: pages JSON read failed: {exc}'
    found = False
    for category in pages.get('products', []):
        for item in category.get('items', []):
            if item.get('slug') == expected_slug:
                found = True
                break
        if found:
            break
    if not found:
        return f'{lang}: pages_{lang}.json missing slug {expected_slug}'
    return ''

def rebuild_static_product_lists():
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

errors = []
created = []
translated = []

auto_translate_enabled = truthy(auto_translate)
force_translate_non_en_enabled = truthy(force_translate_non_en)
translated_langs_present = truthy(translated_langs_present_raw)
translated_langs = []
if translated_langs_raw:
  for part in re.split(r'[\s,]+', translated_langs_raw):
    lang_code = str(part or '').strip().lower()
    if lang_code in LANGS and lang_code != 'en' and lang_code not in translated_langs:
      translated_langs.append(lang_code)
translated_langs_set = set(translated_langs)
translation_cache = {}
en_source_fields = {
  'title': en_title,
  'subtitle': en_subtitle,
  'summary': en_summary,
  'meta_desc': en_meta,
  'keywords': en_kw,
  'bc_label': en_bc,
  'body': en_body,
}

target_langs = list(LANGS)
if translated_langs_present:
  target_langs = ['en'] + [l for l in LANGS if l in translated_langs_set]

for lang in target_langs:
  title_input = g(f'{lang}_title')
  subtitle_input = g(f'{lang}_subtitle')
  summary_input = g(f'{lang}_summary')
  meta_input = g(f'{lang}_meta_desc')
  kw_input = g(f'{lang}_keywords')
  bc_input = g(f'{lang}_bc_label')
  body_input = g(f'{lang}_body')
  has_manual_localized_input = any([title_input, subtitle_input, summary_input, meta_input, kw_input, bc_input, body_input])

  translated_fields = translation_cache.get(lang, {})
  translated_priority = auto_translate_enabled and lang != 'en'
  allow_manual_non_en = (not translated_priority) or (not force_translate_non_en_enabled)
  if translated_priority and not translated_fields and not has_manual_localized_input:
    continue

  title = (translated_fields.get('title') or (title_input if allow_manual_non_en else '') or en_title) if translated_priority else (title_input or translated_fields.get('title') or en_title)
  subtitle = (translated_fields.get('subtitle') or (subtitle_input if allow_manual_non_en else '') or en_subtitle) if translated_priority else (subtitle_input or translated_fields.get('subtitle') or en_subtitle)
  summary = (translated_fields.get('summary') or (summary_input if allow_manual_non_en else '') or en_summary) if translated_priority else (summary_input or translated_fields.get('summary') or en_summary)
  meta_desc = (translated_fields.get('meta_desc') or (meta_input if allow_manual_non_en else '') or summary) if translated_priority else (meta_input or translated_fields.get('meta_desc') or summary)
  keywords = (translated_fields.get('keywords') or (kw_input if allow_manual_non_en else '') or en_kw) if translated_priority else (kw_input or translated_fields.get('keywords') or en_kw)
  bc_label = (translated_fields.get('bc_label') or (bc_input if allow_manual_non_en else '') or title) if translated_priority else (bc_input or translated_fields.get('bc_label') or title)
  body = (translated_fields.get('body') or (body_input if allow_manual_non_en else '') or en_body) if translated_priority else (body_input or translated_fields.get('body') or en_body)

  products_dir = os.path.join(BASE_DIR, 'pags', lang, 'products')
  html_path = os.path.join(products_dir, slug + '.html')
  json_path = os.path.join(BASE_DIR, 'pags', lang, f'pages_{lang}.json')

  try:
    os.makedirs(products_dir, exist_ok=True)
    html = build_html(
      lang, slug, date, title, subtitle, summary, meta_desc, keywords, bc_label, body, LANGS,
      og_image, product_category, extra_head,
      applications_data, materials_data, size_chart_data, reviews_data, related_products_data,
      cta_title, cta_desc, cta_button_text
    )
    with open(html_path, 'w', encoding='utf-8') as f:
      f.write(html)
    update_json(json_path, slug, title, summary, og_image, product_category)
    verify_error = verify_product_outputs(
      lang,
      products_dir,
      html_path,
      json_path,
      slug
    )
    if verify_error:
      errors.append(verify_error)
      continue
    created.append(lang)
  except JsonStoreError as e:
    errors.append(f'{lang}: pages JSON update failed: {str(e)}')
  except Exception as e:
    errors.append(f'{lang}: {str(e)}')

render_error = ''
if created:
    render_error = rebuild_static_product_lists()

fork_error = None
if auto_translate_enabled:
    try:
        jobs_dir = os.path.join(BASE_DIR, '.translate-jobs')
        os.makedirs(jobs_dir, exist_ok=True)
        status_path = os.path.join(jobs_dir, slug + '-status.json')
        job_path = os.path.join(jobs_dir, slug + '-job.json')
        with open(status_path, 'w', encoding='utf-8') as _sf:
            json.dump({'status': 'starting', 'completed': [], 'failed': {}, 'total': len(LANGS) - 1,
                       'started_at': datetime.now().isoformat()}, _sf, ensure_ascii=False)
        job_data = {
            'slug': slug, 'date': date, 'og_image': og_image,
            'product_category': product_category,
            'extra_head': extra_head,
            'source_fields': en_source_fields,
            'langs': [l for l in LANGS if l != 'en'],
            'base_dir': BASE_DIR,
            'article_save_path': os.path.abspath(__file__),
            'status_path': status_path,
            'extra_params': {'product_category': product_category},
        }
        with open(job_path, 'w', encoding='utf-8') as _jf:
            json.dump(job_data, _jf, ensure_ascii=False)
        worker_path = os.path.join(SCRIPT_DIR, 'translate-worker.py')
        subprocess.Popen(
            [sys.executable, worker_path, job_path],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )
    except Exception as _fork_exc:
        fork_error = str(_fork_exc)
        auto_translate_enabled = False


# Regenerate static HTML
subprocess.run(['python3', os.path.join(BASE_DIR, 'render_list_pages.py')], capture_output=True)

respond({
    'success': len(created) > 0,
    'slug': slug,
    'created': created,
    'translated': translated,
    'translating': auto_translate_enabled,
    'errors': errors + ([render_error] if render_error else []) + ([f'translate fork failed: {fork_error}'] if fork_error else []),
    'url': f'/pags/en/products/{slug}.html',
})
