#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json, re, subprocess
import html as html_lib
from html.parser import HTMLParser
from datetime import datetime
from urllib.parse import parse_qs
from urllib import request as urlrequest
from urllib import error as urlerror

try:
    from PIL import Image
except Exception:
    Image = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
TRANSLATION_ENV_FILES = [
  os.path.join(BASE_DIR, '.translation-env'),
  os.path.join(BASE_DIR, '.env.translation'),
]
_translation_env_loaded = False
VOID_ELEMENTS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
HEADING_ELEMENTS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
BLOCK_ELEMENTS = {
  'address', 'article', 'aside', 'blockquote', 'details', 'div', 'dl', 'fieldset',
  'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'header', 'hr', 'main', 'nav', 'ol', 'p', 'pre', 'section', 'table', 'ul'
}
IMG_TAG_RE = re.compile(r'<img\b[^>]*>', re.I)
ATTR_RE = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)(?:\s*=\s*(".*?"|\'.*?\'|[^\s"\'>/=`]+))?', re.S)
IMAGE_DIMENSION_CACHE = {}

# ── Headers first ─────────────────────────────────────────────────────────────
sys.stdout.write("Content-Type: application/json; charset=utf-8\r\n\r\n")
sys.stdout.flush()

def respond(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()
    sys.exit(0)

class ArticleBodyValidator(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []

    def error(self, message):
        self._push_error(message)

    def _push_error(self, message):
        if len(self.errors) >= 12:
            return
        line, col = self.getpos()
        self.errors.append(f'第 {line} 行附近：{message}')

    def _process_start_tag(self, tag, attrs, self_closing=False):
        tag = tag.lower()
        attr_map = {str(k or '').lower(): str(v or '') for k, v in attrs}

        if tag in HEADING_ELEMENTS and any(parent in HEADING_ELEMENTS for parent in self.stack):
            self._push_error(f'不允许嵌套标题标签 `<{tag}>`')

        current_heading = next((parent for parent in reversed(self.stack) if parent in HEADING_ELEMENTS), '')
        if current_heading and tag in BLOCK_ELEMENTS:
            self._push_error(f'标题标签 `<{current_heading}>` 内不能包含块级元素 `<{tag}>`')

        if tag == 'li' and not any(parent in {'ul', 'ol'} for parent in self.stack):
            self._push_error('发现脱离列表容器的 `<li>`，请把列表项放进 `<ul>` 或 `<ol>` 内')

        if tag == 'a':
            href = attr_map.get('href', '').strip()
            if not href:
                self._push_error('发现空链接 `<a href="">`，请填写有效链接地址')

        if tag == 'img':
            src = attr_map.get('src', '').strip()
            if not src:
                self._push_error('发现缺少 `src` 的 `<img>` 标签')

        if tag not in VOID_ELEMENTS and not self_closing:
            self.stack.append(tag)

    def handle_starttag(self, tag, attrs):
        self._process_start_tag(tag, attrs, self_closing=False)

    def handle_startendtag(self, tag, attrs):
        self._process_start_tag(tag, attrs, self_closing=True)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in VOID_ELEMENTS:
            return
        if tag not in self.stack:
            self._push_error(f'发现多余的闭合标签 `</{tag}>`')
            return

        while self.stack:
            top = self.stack.pop()
            if top == tag:
                break
            self._push_error(f'标签闭合顺序错误：期望先闭合 `<{top}>`，但遇到 `</{tag}>`')

    def close(self):
        super().close()
        for tag in reversed(self.stack[-5:]):
            self._push_error(f'标签未闭合：`<{tag}>`')

def extract_attr_value(raw):
    value = (raw or '').strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return html_lib.unescape(value)

def parse_img_attributes(tag_html):
    inner = re.sub(r'^<img\b', '', tag_html.strip(), flags=re.I)
    inner = re.sub(r'/?>\s*$', '', inner).strip()
    attrs = []
    for match in ATTR_RE.finditer(inner):
        name = str(match.group(1) or '').lower()
        if not name:
            continue
        attrs.append([name, extract_attr_value(match.group(2))])
    return attrs

def set_attr(attrs, name, value, overwrite=False):
    name = name.lower()
    for item in attrs:
        if item[0] == name:
            if overwrite or not str(item[1] or '').strip():
                item[1] = value
            return
    attrs.append([name, value])

def serialize_img_tag(attrs):
    parts = ['<img']
    for name, value in attrs:
        if value is None or value == '':
            parts.append(f' {name}')
        else:
            parts.append(f' {name}="{he(str(value))}"')
    parts.append('>')
    return ''.join(parts)

def resolve_image_rel_path(src):
    path = str(src or '').strip()
    if not path or path.startswith('data:'):
        return ''
    path = path.split('?', 1)[0].split('#', 1)[0]
    path = re.sub(r'^\s*https?://[^/]+/images/', '', path, flags=re.I)
    path = re.sub(r'^(?:\.\./)+images/', '', path, flags=re.I)
    path = re.sub(r'^/?images/', '', path, flags=re.I)
    return path.lstrip('/')

def get_image_dimensions(rel_path):
    rel = str(rel_path or '').strip()
    if not rel:
        return None
    if rel in IMAGE_DIMENSION_CACHE:
        return IMAGE_DIMENSION_CACHE[rel]

    local_path = os.path.join(BASE_DIR, 'images', rel.replace('/', os.sep))
    dims = None
    if Image and os.path.exists(local_path):
        try:
            with Image.open(local_path) as img:
                dims = (int(img.width), int(img.height))
        except Exception:
            dims = None

    IMAGE_DIMENSION_CACHE[rel] = dims
    return dims

def validate_article_body_html(lang, body):
    parser = ArticleBodyValidator()
    try:
        parser.feed(body or '')
        parser.close()
    except Exception as exc:
        return [f'{lang}: HTML 解析失败：{exc}']
    return [f'{lang}: {msg}' for msg in parser.errors]

def enrich_body_images(body):
    state = {'seen': False}

    def replace_img(match):
        attrs = parse_img_attributes(match.group(0))
        if not attrs:
            return match.group(0)

        attr_map = {name: value for name, value in attrs}
        src = str(attr_map.get('src', '') or '').strip()
        if not src:
            return match.group(0)

        dims = get_image_dimensions(resolve_image_rel_path(src))
        prioritize = not state['seen']
        state['seen'] = True

        if prioritize:
            set_attr(attrs, 'loading', 'eager', overwrite=True)
            set_attr(attrs, 'fetchpriority', 'high', overwrite=True)
        elif not str(attr_map.get('loading', '') or '').strip():
            set_attr(attrs, 'loading', 'lazy')

        if not str(attr_map.get('decoding', '') or '').strip():
            set_attr(attrs, 'decoding', 'async')

        if dims:
            if not str(attr_map.get('width', '') or '').strip():
                set_attr(attrs, 'width', str(dims[0]))
            if not str(attr_map.get('height', '') or '').strip():
                set_attr(attrs, 'height', str(dims[1]))

        return serialize_img_tag(attrs)

    return IMG_TAG_RE.sub(replace_img, body or '')

def prepare_article_body_html(lang, body):
    content = str(body or '').strip()
    errors = validate_article_body_html(lang, content)
    if errors:
        raise ValueError('；'.join(errors))
    return enrich_body_images(content)

# ── Parse URL-encoded POST body ───────────────────────────────────────────────
try:
    cl  = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    raw = sys.stdin.buffer.read(cl).decode('utf-8', errors='replace') if cl > 0 else ''
    form = parse_qs(raw, keep_blank_values=True)
    def g(k, d=''):
        v = form.get(k, [d])
        return (v[0] if v else d).strip()
except Exception as e:
    respond({'success': False, 'error': 'POST parse error: ' + str(e)})

slug    = re.sub(r'-+', '-', re.sub(r'[^a-z0-9-]', '-', g('slug').lower())).strip('-')
date    = g('date') or datetime.now().strftime('%Y-%m-%d')
en_title    = g('en_title')
en_subtitle = g('en_subtitle')
en_summary  = g('en_summary')
en_meta     = g('en_meta_desc') or en_summary
en_kw       = g('en_keywords')
en_bc       = g('en_bc_label') or en_title
en_body     = g('en_body')
og_image        = g('og_image')          # relative to /images/, e.g. abouts/factory1.jpg
article_section = g('article_section') or 'Industry News'
extra_head      = g('extra_head')
auto_translate  = g('auto_translate', '0')

if not slug:     respond({'success': False, 'error': 'Slug 不能为空'})
if not en_title: respond({'success': False, 'error': '英文标题为必填项'})
if not en_body:  respond({'success': False, 'error': '英文正文内容为必填项'})
if not en_summary: respond({'success': False, 'error': '英文摘要为必填项'})

# ── Language config ───────────────────────────────────────────────────────────
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
    'bc_home':'Home','bc_news':'News',
    'footer_desc':'Professional fastener manufacturer and exporter since 2005. Delivering quality bolts, screws, washers, and custom fasteners to customers worldwide.',
    'quick_links':'Quick Links','footer_about':'About Us','footer_contact':'Contact Us',
    'email_lbl':'Email','phone_lbl':'Phone','addr_lbl':'Address',
    'addr_val':'Yongnian District, Handan, Hebei, China',
    'copyright':'All Rights Reserved.','privacy':'Privacy Policy',
    'rec_products':'Recommended Products','view_details':'View Details →',
    'fp':['Hex Bolts','Flange Bolts','Anchor Bolts','Flat Washers','Lock Washers'],
    'faq_title':'Frequently Asked Questions','faq_still':'Still have questions?','faq_contact':'Contact Us',
    'faq':[
      ('What is the minimum order quantity?','Our standard MOQ is 10 kg per item. For custom orders, the MOQ may vary depending on specifications — feel free to ask.'),
      ('How long does production take?','Standard products: 7–15 business days. Custom orders: 15–25 business days depending on complexity and quantity.'),
      ('Can you send samples before I place a bulk order?','Yes. We provide free samples for standard items (you cover shipping). For custom parts, a small sample fee may apply.'),
      ('What payment methods do you accept?','T/T (bank transfer), L/C, Western Union, and PayPal for small orders. We typically ask for 30% deposit with balance before shipment.'),
      ('Do you offer OEM / custom manufacturing?','Absolutely. Send us your drawings or specifications and we will provide a quote within 24 hours.'),
    ],
  },
  'zh': {
    'html_lang':'zh','hreflang':'zh-CN','rtl':False,'date_fn':dfmt_zh,
    'alt_logo':'WT Metal Co., Ltd.',
    'nav':['首页','产品','新闻','关于','联系'],
    'bc_home':'首页','bc_news':'新闻',
    'footer_desc':'自2005年以来的专业紧固件制造商和出口商。为全球客户提供优质螺栓、螺钉、垫圈和定制紧固件。',
    'quick_links':'快捷链接','footer_about':'关于我们','footer_contact':'联系我们',
    'email_lbl':'电子邮件','phone_lbl':'电话','addr_lbl':'地址',
    'addr_val':'中国河北省邯郸市永年区',
    'copyright':'版权所有','privacy':'隐私政策',
    'rec_products':'推荐产品','view_details':'查看详情 →',
    'fp':['六角螺栓','法兰螺栓','地脚螺栓','平垫圈','锁紧垫圈'],
    'faq_title':'常见问题','faq_still':'还有问题吗？','faq_contact':'联系我们',
    'faq':[
      ('最小起订量是多少？','我们的标准最小起订量为每种产品10公斤。定制订单的起订量根据规格有所不同，欢迎咨询。'),
      ('生产周期需要多久？','标准产品：7-15个工作日。定制订单：根据复杂程度和数量，15-25个工作日。'),
      ('大批量订单前可以提供样品吗？','可以。我们为标准产品提供免费样品（运费由客户承担）。定制零件可能收取少量样品费。'),
      ('你们接受哪些付款方式？','电汇（T/T）、信用证（L/C）、西联汇款，小额订单支持PayPal。通常要求预付30%定金，余款发货前付清。'),
      ('你们提供OEM/定制生产服务吗？','当然可以。发送您的图纸或规格，我们将在24小时内为您提供报价。'),
    ],
  },
  'de': {
    'html_lang':'de','hreflang':'de','rtl':False,'date_fn':dfmt_de,
    'alt_logo':'WT Metal Produkte Co., Ltd.',
    'nav':['Startseite','Produkte','Nachrichten','Über Uns','Kontakt'],
    'bc_home':'Startseite','bc_news':'Nachrichten',
    'footer_desc':'Professioneller Verbindungselemente-Hersteller und -Exporteur seit 2005.',
    'quick_links':'Schnelllinks','footer_about':'Über Uns','footer_contact':'Kontakt',
    'email_lbl':'E-Mail','phone_lbl':'Telefon','addr_lbl':'Adresse',
    'addr_val':'Yongnian District, Handan, Hebei, China',
    'copyright':'Alle Rechte vorbehalten.','privacy':'Datenschutzrichtlinie',
    'rec_products':'Empfohlene Produkte','view_details':'Details ansehen →',
    'fp':['Hex Bolts','Flange Bolts','Anchor Bolts','Flat Washers','Lock Washers'],
    'faq_title':'Häufig gestellte Fragen','faq_still':'Noch Fragen?','faq_contact':'Kontaktieren Sie uns',
    'faq':[
      ('Was ist die Mindestbestellmenge?','Unsere Standard-Mindestbestellmenge beträgt 10 kg pro Artikel.'),
      ('Wie lange dauert die Produktion?','Standardprodukte: 7–15 Werktage. Sonderanfertigungen: 15–25 Werktage.'),
      ('Können Sie Muster senden?','Ja. Wir liefern kostenlose Muster für Standardartikel (Versandkosten tragen Sie).'),
      ('Welche Zahlungsmethoden akzeptieren Sie?','T/T, Akkreditiv, Western Union und PayPal für kleine Bestellungen. 30% Anzahlung üblich.'),
      ('Bieten Sie OEM-Fertigung an?','Absolut. Senden Sie uns Ihre Zeichnungen und wir machen Ihnen innerhalb von 24 Stunden ein Angebot.'),
    ],
  },
  'ar': {
    'html_lang':'ar','hreflang':'ar','rtl':True,'date_fn':dfmt_ar,
    'alt_logo':'WT Metal Co., Ltd.',
    'nav':['الرئيسية','المنتجات','الأخبار','عن الشركة','اتصل'],
    'bc_home':'الرئيسية','bc_news':'الأخبار',
    'footer_desc':'مصنّع ومصدّر متخصص لمنتجات التثبيت منذ عام 2005.',
    'quick_links':'روابط سريعة','footer_about':'عن الشركة','footer_contact':'اتصل بنا',
    'email_lbl':'البريد الإلكتروني','phone_lbl':'الهاتف','addr_lbl':'العنوان',
    'addr_val':'منطقة يونغنيان، هاندان، خيبي، الصين',
    'copyright':'جميع الحقوق محفوظة.','privacy':'سياسة الخصوصية',
    'rec_products':'المنتجات الموصى بها','view_details':'عرض التفاصيل ←',
    'fp':['مسامير سداسية','مسامير الشفة','مسامير التثبيت','غسالات مسطحة','غسالات مخصصة'],
    'faq_title':'الأسئلة الشائعة','faq_still':'هل لديك المزيد من الأسئلة؟','faq_contact':'اتصل بنا',
    'faq':[
      ('ما هو الحد الأدنى لكمية الطلب؟','الحد الأدنى القياسي لكمية الطلب هو 10 كجم لكل بند.'),
      ('كم يستغرق وقت الإنتاج؟','المنتجات القياسية: 7–15 يوم عمل. الطلبات المخصصة: 15–25 يوم عمل.'),
      ('هل يمكنكم إرسال عينات؟','نعم. نوفر عينات مجانية للمنتجات القياسية.'),
      ('ما طرق الدفع المقبولة؟','T/T، خطاب اعتماد، ويسترن يونيون وPayPal للطلبات الصغيرة.'),
      ('هل تقدمون تصنيعاً مخصصاً؟','بالتأكيد. أرسل لنا رسوماتك وسنقدم عرض أسعار خلال 24 ساعة.'),
    ],
  },
  'es': {
    'html_lang':'es','hreflang':'es','rtl':False,'date_fn':dfmt_es,
    'alt_logo':'WT Metal Co., Ltd.',
    'nav':['Inicio','Productos','Noticias','Nosotros','Contacto'],
    'bc_home':'Inicio','bc_news':'Noticias',
    'footer_desc':'Fabricante y exportador profesional de sujetadores desde 2005.',
    'quick_links':'Accesos Rápidos','footer_about':'Sobre Nosotros','footer_contact':'Contáctenos',
    'email_lbl':'Correo','phone_lbl':'Teléfono','addr_lbl':'Dirección',
    'addr_val':'Yongnian District, Handan, Hebei, China',
    'copyright':'Todos los derechos reservados.','privacy':'Política de Privacidad',
    'rec_products':'Productos Recomendados','view_details':'Ver Detalles →',
    'fp':['Pernos Hex','Pernos de Brida','Pernos de Anclaje','Arandelas Planas','Arandelas de Bloqueo'],
    'faq_title':'Preguntas Frecuentes','faq_still':'¿Tienes más preguntas?','faq_contact':'Contáctenos',
    'faq':[
      ('¿Cuál es la cantidad mínima de pedido?','Nuestra cantidad mínima estándar es de 10 kg por artículo.'),
      ('¿Cuánto tiempo toma la producción?','Productos estándar: 7–15 días hábiles. Pedidos personalizados: 15–25 días.'),
      ('¿Pueden enviar muestras?','Sí. Ofrecemos muestras gratuitas para artículos estándar.'),
      ('¿Qué métodos de pago aceptan?','T/T, L/C, Western Union y PayPal. Solicitamos 30% de anticipo.'),
      ('¿Ofrecen fabricación OEM?','Por supuesto. Envíenos sus planos y le daremos una cotización en 24 horas.'),
    ],
  },
  'fr': {
    'html_lang':'fr','hreflang':'fr','rtl':False,'date_fn':dfmt_fr,
    'alt_logo':'WT Metal Co., Ltd.',
    'nav':['Accueil','Produits','Actualités','À propos','Contact'],
    'bc_home':'Accueil','bc_news':'Actualités',
    'footer_desc':'Fabricant et exportateur professionnel de fixations depuis 2005.',
    'quick_links':'Liens Rapides','footer_about':'À Propos','footer_contact':'Nous Contacter',
    'email_lbl':'Email','phone_lbl':'Téléphone','addr_lbl':'Adresse',
    'addr_val':'District Yongnian, Handan, Hebei, Chine',
    'copyright':'Tous droits réservés.','privacy':'Politique de Confidentialité',
    'rec_products':'Produits Recommandés','view_details':'Voir les Détails →',
    'fp':['Boulons Hex','Boulons à Bride','Boulons d\'Ancrage','Rondelles Plates','Rondelles de Blocage'],
    'faq_title':'Questions Fréquentes','faq_still':"Vous avez d'autres questions ?",'faq_contact':'Nous Contacter',
    'faq':[
      ('Quelle est la quantité minimale de commande ?','Notre quantité minimale standard est de 10 kg par article.'),
      ('Combien de temps prend la production ?','Produits standard : 7–15 jours ouvrables. Commandes sur mesure : 15–25 jours.'),
      ('Pouvez-vous envoyer des échantillons ?','Oui. Nous fournissons des échantillons gratuits pour les articles standard.'),
      ('Quels modes de paiement acceptez-vous ?','T/T, L/C, Western Union et PayPal. Acompte de 30% habituel.'),
      ('Proposez-vous la fabrication OEM ?','Absolument. Envoyez-nous vos plans et nous vous fournirons un devis en 24 heures.'),
    ],
  },
  'id': {
    'html_lang':'id','hreflang':'id','rtl':False,'date_fn':dfmt_id,
    'alt_logo':'WT Metal Co., Ltd.',
    'nav':['Beranda','Produk','Berita','Tentang','Kontak'],
    'bc_home':'Beranda','bc_news':'Berita',
    'footer_desc':'Produsen dan eksportir pengencang profesional sejak 2005.',
    'quick_links':'Tautan Cepat','footer_about':'Tentang Kami','footer_contact':'Hubungi Kami',
    'email_lbl':'Email','phone_lbl':'Telepon','addr_lbl':'Alamat',
    'addr_val':'Distrik Yongnian, Handan, Hebei, China',
    'copyright':'Semua Hak Dilindungi.','privacy':'Kebijakan Privasi',
    'rec_products':'Produk yang Direkomendasikan','view_details':'Lihat Detail →',
    'fp':['Baut Hex','Baut Flange','Baut Jangkar','Ring Datar','Ring Pengunci'],
    'faq_title':'Pertanyaan Umum','faq_still':'Masih ada pertanyaan?','faq_contact':'Hubungi Kami',
    'faq':[
      ('Berapa jumlah pesanan minimum?','MOQ standar kami adalah 10 kg per item.'),
      ('Berapa lama waktu produksi?','Produk standar: 7–15 hari kerja. Pesanan khusus: 15–25 hari kerja.'),
      ('Bisakah mengirim sampel?','Ya. Kami menyediakan sampel gratis untuk item standar.'),
      ('Metode pembayaran apa yang diterima?','T/T, L/C, Western Union, dan PayPal. Biasanya meminta 30% deposit.'),
      ('Apakah menawarkan manufaktur OEM?','Tentu. Kirimkan gambar atau spesifikasi dan kami berikan penawaran dalam 24 jam.'),
    ],
  },
  'ja': {
    'html_lang':'ja','hreflang':'ja','rtl':False,'date_fn':dfmt_ja,
    'alt_logo':'WT Metal Co., Ltd.',
    'nav':['ホーム','製品','ニュース','会社情報','お問い合わせ'],
    'bc_home':'ホーム','bc_news':'ニュース',
    'footer_desc':'2005年より専門的なファスナーメーカー・輸出業者として活動しています。',
    'quick_links':'クイックリンク','footer_about':'会社情報','footer_contact':'お問い合わせ',
    'email_lbl':'メール','phone_lbl':'電話','addr_lbl':'住所',
    'addr_val':'中国河北省邯鄲市永年区',
    'copyright':'All Rights Reserved.','privacy':'プライバシーポリシー',
    'rec_products':'おすすめ製品','view_details':'詳細を見る →',
    'fp':['六角ボルト','フランジボルト','アンカーボルト','平座金','ロック座金'],
    'faq_title':'よくある質問','faq_still':'まだご質問がありますか？','faq_contact':'お問い合わせ',
    'faq':[
      ('最小注文数量はいくつですか？','標準の最小注文数量はアイテムあたり10kgです。'),
      ('生産にはどのくらいかかりますか？','標準品：7〜15営業日。カスタム注文：15〜25営業日。'),
      ('サンプルを送ってもらえますか？','はい。標準品は無料サンプルを提供します（送料はお客様負担）。'),
      ('支払方法は何ですか？','T/T、L/C、Western Union、小口注文はPayPal。通常30%の前払いが必要です。'),
      ('OEM製造は可能ですか？','もちろんです。図面や仕様書を送っていただければ24時間以内に見積もりをお送りします。'),
    ],
  },
  'ko': {
    'html_lang':'ko','hreflang':'ko','rtl':False,'date_fn':dfmt_ko,
    'alt_logo':'WT Metal Co., Ltd.',
    'nav':['홈','제품','뉴스','회사소개','문의'],
    'bc_home':'홈','bc_news':'뉴스',
    'footer_desc':'2005년부터 전문 파스너 제조사 및 수출업체입니다.',
    'quick_links':'빠른 링크','footer_about':'회사 소개','footer_contact':'문의하기',
    'email_lbl':'이메일','phone_lbl':'전화','addr_lbl':'주소',
    'addr_val':'중국 허베이성 한단시 용년구',
    'copyright':'All Rights Reserved.','privacy':'개인정보 처리방침',
    'rec_products':'추천 제품','view_details':'자세히 보기 →',
    'fp':['육각 볼트','플랜지 볼트','앵커 볼트','평 와셔','잠금 와셔'],
    'faq_title':'자주 묻는 질문','faq_still':'더 궁금한 점이 있으신가요?','faq_contact':'문의하기',
    'faq':[
      ('최소 주문 수량은 얼마인가요?','표준 최소 주문 수량은 품목당 10kg입니다.'),
      ('생산 기간은 얼마나 걸리나요?','표준 제품: 7~15 영업일. 맞춤 주문: 15~25 영업일.'),
      ('샘플 발송이 가능한가요?','네. 표준 품목은 무료 샘플을 제공합니다.'),
      ('어떤 결제 방법을 받나요?','T/T, L/C, 웨스턴 유니온, 소액 주문은 PayPal.'),
      ('OEM 제조가 가능한가요?','물론입니다. 도면을 보내주시면 24시간 내에 견적을 드립니다.'),
    ],
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
    'You are a professional website localization translator for industrial fastener news. '
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
    raise RuntimeError(f'{target_name} 翻译结果缺少字段: {", ".join(missing)}')

  return {field: str(translated.get(field, '') or '') for field in TRANSLATABLE_FIELDS}

# ── Helpers ───────────────────────────────────────────────────────────────────
def he(s):
    """HTML-escape for attribute values"""
    return s.replace('&','&amp;').replace('"','&quot;').replace('<','&lt;').replace('>','&gt;')

def je(s):
    """JSON-safe escape for JSON-LD strings"""
    return s.replace('\\','\\\\').replace('"','\\"')

def build_faq(faq_items):
    out = ''
    for q, a in faq_items:
        out += f'      <article class="faq-item">\n'
        out += f'        <h3 class="faq-question">{q}</h3>\n'
        out += f'        <p class="faq-answer">{a}</p>\n'
        out += f'      </article>\n'
    return out

def build_head_extra(extra_head):
  snippet = (extra_head or '').strip()
  if not snippet:
    return ''
  return '\n  <!-- Custom Head Snippet -->\n' + snippet + '\n  <!-- End Custom Head Snippet -->'

def build_hreflang(slug, all_langs):
    hm = {'en':'en','ar':'ar','de':'de','es':'es','fr':'fr','id':'id','ja':'ja','ko':'ko','zh':'zh-CN'}
    lines = [f'  <link rel="alternate" hreflang="{hm[l]}" href="/pags/{l}/news/{slug}.html">' for l in all_langs]
    lines.append(f'  <link rel="alternate" hreflang="x-default" href="/pags/en/news/{slug}.html">')
    return '\n'.join(lines)

def build_html(lang, slug, date_str, title, subtitle, meta_desc, keywords, bc_label, body, all_langs, og_image='', article_section='Industry News', extra_head=''):
    c   = LC[lang]
    hl  = c['html_lang']
    dir_attr = ' dir="rtl"' if c['rtl'] else ''
    n   = c['nav']
    y, m, d = int(date_str[:4]), int(date_str[5:7]), int(date_str[8:10])
    date_display = c['date_fn'](y, m, d)
    hreflang = build_hreflang(slug, all_langs)
    faq_html = build_faq(c['faq'])
    fp = c['fp']
    og_img_url = f'https://wtscrews.com/images/{og_image}' if og_image else 'https://wtscrews.com/images/og-cover.jpg'
    extra_head_block = build_head_extra(extra_head)
    safe_body = prepare_article_body_html(lang, body)

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
  <link rel="canonical" href="https://wtscrews.com/pags/{lang}/news/{slug}.html">
  <link rel="sitemap" type="application/xml" href="../../../sitemap.xml">
  <meta name="geo.region" content="CN">
  <meta name="geo.placename" content="China">
  <meta name="geo.position" content="30.2741;120.1551">
  <meta name="ICBM" content="30.2741, 120.1551">
  <meta property="og:title" content="{he(title)} — WT Fasteners">
  <meta property="og:description" content="{he(meta_desc)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="https://wtscrews.com/pags/{lang}/news/{slug}.html">
  <meta property="og:image" content="{og_img_url}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "{je(title)}",
    "description": "{je(meta_desc)}",
    "datePublished": "{date_str}T08:00:00+08:00",
    "dateModified": "{date_str}T08:00:00+08:00",
    "author": {{"@type": "Organization", "name": "WT Fasteners", "url": "https://wtscrews.com"}},
    "publisher": {{"@type": "Organization", "name": "WT Fasteners", "logo": {{"@type": "ImageObject", "url": "https://wtscrews.com/images/logo.jpg"}}}},
    "mainEntityOfPage": {{"@type": "WebPage", "@id": "https://wtscrews.com/pags/{lang}/news/{slug}.html"}},
    "articleSection": "{je(article_section)}",
    "keywords": "{je(keywords)}",
    "image": "{og_img_url}"
  }}
  </script>{extra_head_block}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <!-- Async font load — eliminates render-blocking -->
  <link rel="preload" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" as="style" onload="this.onload=null;this.rel='stylesheet'">
  <noscript><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet"></noscript>
  <link rel="stylesheet" href="../../../css/base.css">
  <link rel="stylesheet" href="../../../css/common.css">
  <link rel="stylesheet" href="../../../css/news-detail.css">
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
</head>
<body>

  <header class="site-header" id="siteHeader">
    <nav class="container nav">
      <a href="../index.html" class="logo"><img src="../../../images/logo.jpg" alt="{he(c['alt_logo'])}" width="940" height="940" decoding="async"></a>
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
        <a href="../news.html">{c['bc_news']}</a>
        <span>/</span>
        {bc_label}
      </article>
    </nav>

    <section class="section">
      <article class="container article-content">
        <time class="article-meta" datetime="{date_str}">{date_display}</time>
        {safe_body}
      </article>
    </section>

    <section class="section">
      <article class="container">
        <div class="related-products">
          <h3>{c['rec_products']}</h3>
          <div class="related-grid">
            <a href="../products/hex-bolts.html" class="related-card">
              <div class="related-card-image">
                <img src="../../../images/products/bolts/Hex Bolt0.webp" alt="{fp[0]}" width="1500" height="1500" loading="lazy" decoding="async" style="width:100%;height:100%;object-fit:cover;">
              </div>
              <div class="related-card-body">
                <h4>{fp[0]}</h4>
                <p>DIN 931/933, ISO 4014/4017. Grades 4.8–12.9, M4–M64.</p>
                <span class="related-card-link">{c['view_details']}</span>
              </div>
            </a>
            <a href="../products/hex-nuts.html" class="related-card">
              <div class="related-card-image">
                <img src="../../../images/products/nuts/Hex Nut1.webp" alt="Hex Nuts" width="1500" height="1500" loading="lazy" decoding="async" style="width:100%;height:100%;object-fit:cover;">
              </div>
              <div class="related-card-body">
                <h4>Hex Nuts</h4>
                <p>DIN 934 / ISO 4032. M4–M64, grades 4, 6, 8, 10.</p>
                <span class="related-card-link">{c['view_details']}</span>
              </div>
            </a>
            <a href="../products/flat-washers.html" class="related-card">
              <div class="related-card-image">
                <img src="../../../images/products/washers/Flat Washer4.webp" alt="Flat Washers" width="1500" height="1500" loading="lazy" decoding="async" style="width:100%;height:100%;object-fit:cover;">
              </div>
              <div class="related-card-body">
                <h4>Flat Washers</h4>
                <p>DIN 125 / ISO 7089. Zinc plated, galvanized, or plain.</p>
                <span class="related-card-link">{c['view_details']}</span>
              </div>
            </a>
          </div>
        </div>
      </article>
    </section>
  </main>

  <footer class="site-footer">
    <section class="container footer-grid">
      <article class="footer-col">
        <h3>WT Fasteners</h3>
        <p>{c['footer_desc']}</p>
      </article>
      <article class="footer-col">
        <h3>{c['quick_links']}</h3>
        <ul>
          <li><a href="../index.html">{n[0]}</a></li>
          <li><a href="../products.html">{n[1]}</a></li>
          <li><a href="../news.html">{n[2]}</a></li>
          <li><a href="../about.html">{c['footer_about']}</a></li>
          <li><a href="../contact.html">{n[4]}</a></li>
        </ul>
      </article>
      <article class="footer-col">
        <h3>{n[1]}</h3>
        <ul>
          <li><a href="../products/hex-bolts.html">{fp[0]}</a></li>
          <li><a href="../products/flange-bolts.html">{fp[1]}</a></li>
          <li><a href="../products/anchor-bolts.html">{fp[2]}</a></li>
          <li><a href="../products/flat-washers.html">{fp[3]}</a></li>
          <li><a href="../products/lock-washers.html">{fp[4]}</a></li>
        </ul>
      </article>
      <article class="footer-col">
        <h3>{c['footer_contact']}</h3>
        <p>{c['email_lbl']}: info@wtbolts.com</p>
        <p>{c['email_lbl']}: lipbolts@gmail.com</p>
        <p>{c['phone_lbl']}: +8615175432812</p>
        <p>{c['addr_lbl']}: {c['addr_val']}</p>
      </article>
    </section>
    <section class="footer-bottom">
      <p class="container">&copy; 2026 WT Fasteners. {c['copyright']} &nbsp;|&nbsp; <a href="../privacy-policy.html">{c['privacy']}</a></p>
    </section>
  </footer>

  <aside class="faq-overlay" id="faqOverlay">
    <section class="faq-modal">
      <header class="faq-modal-header">
        <h2>{c['faq_title']}</h2>
        <button class="faq-close" aria-label="Close">&times;</button>
      </header>
{faq_html}      <footer class="faq-cta">
        <p>{c['faq_still']}</p>
        <a href="../contact.html" class="btn btn-primary">{c['faq_contact']}</a>
      </footer>
    </section>
  </aside>

  <script src="../../../js/i18n-config.js" defer></script>
  <script src="../../../js/main.js" defer></script>
  <script src="../../../js/chat-dock.js" defer></script>
</body>
</html>'''

# ── Update JSON ───────────────────────────────────────────────────────────────
def update_json(json_path, slug, title, date_str, summary, og_image=''):
    data = {'news': [], 'products': []}
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            pass
    news_slug = 'news/' + slug
    data['news'] = [n for n in data.get('news', []) if n.get('slug') != news_slug]
    data['news'].insert(0, {
        'slug': news_slug,
        'title': title,
        'date': date_str,
        'summary': summary,
        'icon': f'../../images/{og_image}' if og_image else '../../images/logo.jpg',
    })
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ── Main ──────────────────────────────────────────────────────────────────────
errors  = []
created = []
translated = []
prepared_lang_payloads = []

auto_translate_enabled = truthy(auto_translate)
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

for lang in LANGS:
  title_input    = g(f'{lang}_title')
  subtitle_input = g(f'{lang}_subtitle')
  summary_input  = g(f'{lang}_summary')
  meta_input     = g(f'{lang}_meta_desc')
  kw_input       = g(f'{lang}_keywords')
  bc_input       = g(f'{lang}_bc_label')
  body_input     = g(f'{lang}_body')

  translated_fields = translation_cache.get(lang, {})

  title    = title_input or translated_fields.get('title') or en_title
  subtitle = subtitle_input or translated_fields.get('subtitle') or en_subtitle
  summary  = summary_input or translated_fields.get('summary') or en_summary
  meta     = meta_input or translated_fields.get('meta_desc') or summary
  kw       = kw_input or translated_fields.get('keywords') or en_kw
  bc       = bc_input or translated_fields.get('bc_label') or title
  body     = body_input or translated_fields.get('body') or en_body

  body_errors = validate_article_body_html(lang, body)
  if body_errors:
    errors.extend(body_errors)
    continue

  news_dir  = os.path.join(BASE_DIR, 'pags', lang, 'news')
  html_path = os.path.join(news_dir, slug + '.html')
  json_path = os.path.join(BASE_DIR, 'pags', lang, f'pages_{lang}.json')

  prepared_lang_payloads.append({
    'lang': lang,
    'title': title,
    'subtitle': subtitle,
    'summary': summary,
    'meta': meta,
    'kw': kw,
    'bc': bc,
    'body': body,
    'news_dir': news_dir,
    'html_path': html_path,
    'json_path': json_path,
  })

if errors:
  respond({
      'success': False,
      'slug': slug,
      'created': created,
      'translated': translated,
      'translating': False,
      'errors': errors,
      'url': f'/pags/en/news/{slug}.html',
  })

for payload in prepared_lang_payloads:
  lang = payload['lang']
  try:
    os.makedirs(payload['news_dir'], exist_ok=True)
    html = build_html(
      lang, slug, date,
      payload['title'], payload['subtitle'], payload['meta'], payload['kw'],
      payload['bc'], payload['body'], LANGS, og_image, article_section, extra_head
    )
    with open(payload['html_path'], 'w', encoding='utf-8') as f:
      f.write(html)
    update_json(payload['json_path'], slug, payload['title'], date, payload['summary'], og_image)
    created.append(lang)
  except Exception as e:
    errors.append(f'{lang}: {str(e)}')

fork_error = None
if auto_translate_enabled:
    try:
        jobs_dir    = os.path.join(BASE_DIR, '.translate-jobs')
        os.makedirs(jobs_dir, exist_ok=True)
        status_path = os.path.join(jobs_dir, slug + '-status.json')
        job_path    = os.path.join(jobs_dir, slug + '-job.json')
        with open(status_path, 'w', encoding='utf-8') as _sf:
            json.dump({'status': 'starting', 'completed': [], 'failed': {}, 'total': len(LANGS) - 1,
                       'started_at': datetime.now().isoformat()}, _sf, ensure_ascii=False)
        job_data = {
            'slug': slug, 'date': date, 'og_image': og_image,
            'article_section': article_section, 'extra_head': extra_head,
            'source_fields': en_source_fields,
            'langs': [l for l in LANGS if l != 'en'],
            'base_dir': BASE_DIR,
            'article_save_path': os.path.abspath(__file__),
            'status_path': status_path,
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
        auto_translate_enabled = False   # 回退：不报告 translating=True


# Regenerate static news/products HTML
subprocess.run(['python3', os.path.join(BASE_DIR, 'render_list_pages.py')], capture_output=True)

respond({
    'success': len(created) > 0,
    'slug': slug,
    'created': created,
    'translated': translated,
    'translating': auto_translate_enabled,
    'errors': errors + ([f'translate fork failed: {fork_error}'] if fork_error else []),
    'url': f'/pags/en/news/{slug}.html',
})
