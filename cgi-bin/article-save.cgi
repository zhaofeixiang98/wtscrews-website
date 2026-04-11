#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json, re
from datetime import datetime
from urllib.parse import parse_qs

# ── Headers first ─────────────────────────────────────────────────────────────
sys.stdout.write("Content-Type: application/json; charset=utf-8\r\n\r\n")
sys.stdout.flush()

def respond(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()
    sys.exit(0)

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

if not slug:     respond({'success': False, 'error': 'Slug 不能为空'})
if not en_title: respond({'success': False, 'error': '英文标题为必填项'})
if not en_body:  respond({'success': False, 'error': '英文正文内容为必填项'})
if not en_summary: respond({'success': False, 'error': '英文摘要为必填项'})

# ── Language config ───────────────────────────────────────────────────────────
LANGS = ['en', 'ar', 'de', 'es', 'fr', 'id', 'ja', 'ko', 'zh']

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

def build_hreflang(slug, all_langs):
    hm = {'en':'en','ar':'ar','de':'de','es':'es','fr':'fr','id':'id','ja':'ja','ko':'ko','zh':'zh-CN'}
    lines = [f'  <link rel="alternate" hreflang="{hm[l]}" href="/pags/{l}/news/{slug}.html">' for l in all_langs]
    lines.append(f'  <link rel="alternate" hreflang="x-default" href="/pags/en/news/{slug}.html">')
    return '\n'.join(lines)

def build_html(lang, slug, date_str, title, subtitle, meta_desc, keywords, bc_label, body, all_langs, og_image='', article_section='Industry News'):
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
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../../css/style.css">
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
      <a href="../index.html" class="logo"><img src="../../../images/logo.jpg" alt="{he(c['alt_logo'])}"></a>
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
        {body}
      </article>
    </section>

    <section class="section">
      <article class="container">
        <div class="related-products">
          <h3>{c['rec_products']}</h3>
          <div class="related-grid">
            <a href="../products/hex-bolts.html" class="related-card">
              <div class="related-card-image">
                <img src="../../../images/products/bolts/Hex Bolt0.webp" alt="{fp[0]}" loading="lazy" style="width:100%;height:100%;object-fit:cover;">
              </div>
              <div class="related-card-body">
                <h4>{fp[0]}</h4>
                <p>DIN 931/933, ISO 4014/4017. Grades 4.8–12.9, M4–M64.</p>
                <span class="related-card-link">{c['view_details']}</span>
              </div>
            </a>
            <a href="../products/hex-nuts.html" class="related-card">
              <div class="related-card-image">
                <img src="../../../images/products/nuts/Hex Nut1.webp" alt="Hex Nuts" loading="lazy" style="width:100%;height:100%;object-fit:cover;">
              </div>
              <div class="related-card-body">
                <h4>Hex Nuts</h4>
                <p>DIN 934 / ISO 4032. M4–M64, grades 4, 6, 8, 10.</p>
                <span class="related-card-link">{c['view_details']}</span>
              </div>
            </a>
            <a href="../products/flat-washers.html" class="related-card">
              <div class="related-card-image">
                <img src="../../../images/products/washers/Flat Washer4.webp" alt="Flat Washers" loading="lazy" style="width:100%;height:100%;object-fit:cover;">
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

  <script src="../../../js/i18n-config.js"></script>
  <script src="../../../js/main.js"></script>
  <script src="../../../js/chat-dock.js"></script>
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
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir   = os.path.abspath(os.path.join(script_dir, '..'))

errors  = []
created = []

for lang in LANGS:
    title    = g(f'{lang}_title')    or en_title
    subtitle = g(f'{lang}_subtitle') or en_subtitle
    summary  = g(f'{lang}_summary')  or en_summary
    meta     = g(f'{lang}_meta_desc') or summary
    kw       = g(f'{lang}_keywords') or en_kw
    bc       = g(f'{lang}_bc_label') or title
    body     = g(f'{lang}_body')     or en_body

    news_dir  = os.path.join(base_dir, 'pags', lang, 'news')
    html_path = os.path.join(news_dir, slug + '.html')
    json_path = os.path.join(base_dir, 'pags', lang, f'pages_{lang}.json')

    try:
        os.makedirs(news_dir, exist_ok=True)
        html = build_html(lang, slug, date, title, subtitle, meta, kw, bc, body, LANGS, og_image, article_section)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        update_json(json_path, slug, title, date, summary, og_image)
        created.append(lang)
    except Exception as e:
        errors.append(f'{lang}: {str(e)}')

respond({
    'success': len(created) > 0,
    'slug': slug,
    'created': created,
    'errors': errors,
    'url': f'/pags/en/news/{slug}.html',
})
