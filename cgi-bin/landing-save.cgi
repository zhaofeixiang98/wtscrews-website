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


def build_keyword_chips(keywords):
    parts = []
    for raw in str(keywords or '').split(','):
        item = raw.strip()
        if item and item not in parts:
            parts.append(item)
        if len(parts) >= 4:
            break
    if not parts:
        return ''
    return ''.join(f'<span class="chip">{he(item)}</span>' for item in parts)


def build_language_switch(lang, slug):
    labels = {
        'en': 'English',
        'ar': 'العربية',
        'de': 'Deutsch',
        'es': 'Español',
        'fr': 'Français',
        'id': 'Indonesia',
        'ja': '日本語',
        'ko': '한국어',
        'zh': '中文',
    }
    options = []
    for code in LANGS:
        selected = ' selected' if code == lang else ''
        options.append(
            f'<option value="/pags/{code}/landing/{slug}.html"{selected}>{he(labels.get(code, code.upper()))}</option>'
        )
    current_label = he(labels.get(lang, lang.upper()))
    return (
        f'<div class="lang-picker">'
        f'<span class="lang-picker-label">{current_label}</span>'
        f'<select class="lang-select" aria-label="Language switcher" onchange="if(this.value) window.location.href=this.value">'
        + ''.join(options) +
        '</select></div>'
    )


def safe_chmod(path, mode):
    try:
        os.chmod(path, mode)
    except Exception:
        pass


def make_hreflang(slug):
    mapping = {'en': 'en', 'ar': 'ar', 'de': 'de', 'es': 'es', 'fr': 'fr', 'id': 'id', 'ja': 'ja', 'ko': 'ko', 'zh': 'zh-CN'}
    lines = []
    for lang in LANGS:
        lines.append(f'  <link rel="alternate" hreflang="{mapping[lang]}" href="/pags/{lang}/landing/{slug}.html">')
    lines.append(f'  <link rel="alternate" hreflang="x-default" href="/pags/en/landing/{slug}.html">')
    return '\n'.join(lines)


LC = {
    'en': {'html_lang': 'en', 'cta_quote': 'Get Quote in 24h', 'cta_chat': 'WhatsApp Now', 'form_title': 'Tell us your requirements', 'form_btn': 'Submit Request', 'privacy': 'Privacy Policy', 'lead_notice': 'Industrial fastener quotation page', 'name_ph': 'Name *', 'email_ph': 'Email *', 'company_ph': 'Company', 'phone_ph': 'Phone / WhatsApp', 'message_ph': 'Please describe specs, quantity and lead-time request *', 'sticky_note': 'Urgent order or restocking need?', 'sticky_hint': 'WhatsApp is usually the fastest way to confirm specs and lead-time.', 'trust_title': 'Supply capability at a glance', 'strength_1_k': 'Response', 'strength_1_v': '24h quote support', 'strength_2_k': 'Production', 'strength_2_v': 'OEM / ODM available', 'strength_3_k': 'Standards', 'strength_3_v': 'DIN / ISO / custom drawing', 'strength_4_k': 'Delivery', 'strength_4_v': 'Export packing & shipment support', 'why_title': 'Why buyers work with WT Fasteners', 'why_1': 'Fast quotation based on drawing, standard or sample', 'why_2': 'Stable quality control for repeat international orders', 'why_3': 'Flexible support for custom dimensions and finishes', 'process_title': 'Simple sourcing process', 'process_1': 'Send drawing, size, standard or sample reference', 'process_2': 'Confirm material, finish, quantity and delivery target', 'process_3': 'Receive quotation, lead time and packing plan', 'faq_title': 'Frequently asked questions', 'faq_q1': 'Can you quote from drawing or sample?', 'faq_a1': 'Yes. You can send drawing, standard code, size list or sample reference for evaluation.', 'faq_q2': 'Do you support custom material and surface finish?', 'faq_a2': 'Yes. Material, hardness, coating and packaging can be discussed based on your order requirement.', 'faq_q3': 'How fast can you respond?', 'faq_a3': 'For standard inquiries, we usually respond with quotation direction within 24 hours.'},
    'zh': {'html_lang': 'zh-CN', 'cta_quote': '24小时内获取报价', 'cta_chat': 'WhatsApp 立即沟通', 'form_title': '提交您的需求', 'form_btn': '提交需求', 'privacy': '隐私政策', 'lead_notice': '工业紧固件报价页面', 'name_ph': '姓名 *', 'email_ph': '邮箱 *', 'company_ph': '公司名称', 'phone_ph': '电话 / WhatsApp', 'message_ph': '请填写规格、数量、交期要求 *', 'sticky_note': '急单或补货需求？', 'sticky_hint': '建议直接通过 WhatsApp 沟通，确认规格和交期更快。', 'trust_title': '供应能力一目了然', 'strength_1_k': '响应速度', 'strength_1_v': '24小时内报价支持', 'strength_2_k': '生产能力', 'strength_2_v': '支持 OEM / ODM', 'strength_3_k': '执行标准', 'strength_3_v': 'DIN / ISO / 来图定制', 'strength_4_k': '交付支持', 'strength_4_v': '支持出口包装与出货', 'why_title': '为什么采购商选择 WT Fasteners', 'why_1': '可根据图纸、标准或样品快速报价', 'why_2': '适合稳定复购的国际订单质量控制', 'why_3': '支持非标尺寸与表面处理定制', 'process_title': '采购流程简单清晰', 'process_1': '发送图纸、尺寸、标准或样品信息', 'process_2': '确认材质、表面处理、数量和交期', 'process_3': '获取报价、交期和包装方案', 'faq_title': '常见问题', 'faq_q1': '可以根据图纸或样品报价吗？', 'faq_a1': '可以。您可发送图纸、标准编号、尺寸清单或样品参考供我们评估。', 'faq_q2': '支持定制材质和表面处理吗？', 'faq_a2': '支持。材质、硬度、电镀和包装都可以根据订单需求沟通确认。', 'faq_q3': '一般多久回复？', 'faq_a3': '标准询盘通常可在 24 小时内给出初步报价方向。'},
    'de': {'html_lang': 'de', 'cta_quote': 'Angebot in 24h', 'cta_chat': 'WhatsApp jetzt', 'form_title': 'Senden Sie Ihre Anforderungen', 'form_btn': 'Anfrage senden', 'privacy': 'Datenschutz', 'lead_notice': 'Landingpage für industrielle Verbindungselemente', 'name_ph': 'Name *', 'email_ph': 'E-Mail *', 'company_ph': 'Unternehmen', 'phone_ph': 'Telefon / WhatsApp', 'message_ph': 'Bitte Spezifikation, Menge und Lieferzeit angeben *', 'sticky_note': 'Dringende Bestellung oder Nachschub?', 'sticky_hint': 'Per WhatsApp lassen sich Spezifikation und Lieferzeit meist am schnellsten abstimmen.', 'trust_title': 'Lieferkompetenz auf einen Blick', 'strength_1_k': 'Reaktion', 'strength_1_v': 'Angebotsunterstützung in 24 Std.', 'strength_2_k': 'Produktion', 'strength_2_v': 'OEM / ODM verfügbar', 'strength_3_k': 'Normen', 'strength_3_v': 'DIN / ISO / Zeichnung nach Maß', 'strength_4_k': 'Lieferung', 'strength_4_v': 'Exportverpackung und Versandunterstützung', 'why_title': 'Warum Einkäufer mit WT Fasteners arbeiten', 'why_1': 'Schnelles Angebot auf Basis von Zeichnung, Norm oder Muster', 'why_2': 'Stabile Qualitätskontrolle für wiederkehrende Exportaufträge', 'why_3': 'Flexible Unterstützung für Sondermaße und Oberflächen', 'process_title': 'Einfacher Beschaffungsprozess', 'process_1': 'Zeichnung, Größe, Norm oder Muster senden', 'process_2': 'Material, Oberfläche, Menge und Lieferziel bestätigen', 'process_3': 'Angebot, Lieferzeit und Verpackungsplan erhalten'},
    'es': {'html_lang': 'es', 'cta_quote': 'Cotización en 24h', 'cta_chat': 'WhatsApp ahora', 'form_title': 'Envíe sus requisitos', 'form_btn': 'Enviar solicitud', 'privacy': 'Política de privacidad', 'lead_notice': 'Página de cotización para tornillería industrial', 'name_ph': 'Nombre *', 'email_ph': 'Correo electrónico *', 'company_ph': 'Empresa', 'phone_ph': 'Teléfono / WhatsApp', 'message_ph': 'Describa especificaciones, cantidad y plazo de entrega *', 'sticky_note': '¿Pedido urgente o reabastecimiento?', 'sticky_hint': 'WhatsApp suele ser la forma más rápida de confirmar especificaciones y plazo.', 'trust_title': 'Capacidad de suministro de un vistazo', 'strength_1_k': 'Respuesta', 'strength_1_v': 'Soporte de cotización en 24 h', 'strength_2_k': 'Producción', 'strength_2_v': 'OEM / ODM disponible', 'strength_3_k': 'Normas', 'strength_3_v': 'DIN / ISO / plano personalizado', 'strength_4_k': 'Entrega', 'strength_4_v': 'Soporte de empaque y envío de exportación', 'why_title': 'Por qué los compradores trabajan con WT Fasteners', 'why_1': 'Cotización rápida según plano, norma o muestra', 'why_2': 'Control de calidad estable para pedidos internacionales repetidos', 'why_3': 'Soporte flexible para medidas y acabados personalizados', 'process_title': 'Proceso de compra simple', 'process_1': 'Envíe plano, medida, norma o referencia de muestra', 'process_2': 'Confirme material, acabado, cantidad y objetivo de entrega', 'process_3': 'Reciba cotización, plazo de entrega y plan de embalaje'},
    'fr': {'html_lang': 'fr', 'cta_quote': 'Devis en 24h', 'cta_chat': 'WhatsApp maintenant', 'form_title': 'Envoyez vos besoins', 'form_btn': 'Envoyer la demande', 'privacy': 'Politique de confidentialité', 'lead_notice': 'Page de devis pour fixations industrielles', 'name_ph': 'Nom *', 'email_ph': 'E-mail *', 'company_ph': 'Entreprise', 'phone_ph': 'Téléphone / WhatsApp', 'message_ph': 'Merci de préciser spécifications, quantité et délai *', 'sticky_note': 'Commande urgente ou réassort ?', 'sticky_hint': 'WhatsApp est souvent le moyen le plus rapide pour confirmer les spécifications et le délai.', 'trust_title': 'Capacité d’approvisionnement en un coup d’œil', 'strength_1_k': 'Réponse', 'strength_1_v': 'Support devis sous 24 h', 'strength_2_k': 'Production', 'strength_2_v': 'OEM / ODM disponible', 'strength_3_k': 'Normes', 'strength_3_v': 'DIN / ISO / plan sur mesure', 'strength_4_k': 'Livraison', 'strength_4_v': 'Support emballage export et expédition', 'why_title': 'Pourquoi les acheteurs choisissent WT Fasteners', 'why_1': 'Devis rapide à partir d’un plan, d’une norme ou d’un échantillon', 'why_2': 'Contrôle qualité stable pour les commandes export récurrentes', 'why_3': 'Support flexible pour dimensions et finitions personnalisées', 'process_title': 'Processus d’achat simple', 'process_1': 'Envoyez plan, dimension, norme ou référence échantillon', 'process_2': 'Confirmez matière, finition, quantité et délai cible', 'process_3': 'Recevez devis, délai et plan d’emballage'},
    'ar': {'html_lang': 'ar', 'cta_quote': 'احصل على عرض خلال 24 ساعة', 'cta_chat': 'تواصل واتساب الآن', 'form_title': 'أرسل متطلباتك', 'form_btn': 'إرسال الطلب', 'privacy': 'سياسة الخصوصية', 'lead_notice': 'صفحة هبوط لطلبات المثبتات الصناعية', 'name_ph': 'الاسم *', 'email_ph': 'البريد الإلكتروني *', 'company_ph': 'اسم الشركة', 'phone_ph': 'الهاتف / واتساب', 'message_ph': 'يرجى كتابة المواصفات والكمية وموعد التسليم *', 'sticky_note': 'طلب عاجل أو إعادة توريد؟', 'sticky_hint': 'غالبا يكون واتساب أسرع طريقة لتأكيد المواصفات ومدة التسليم.', 'trust_title': 'قدرة التوريد باختصار', 'strength_1_k': 'الاستجابة', 'strength_1_v': 'دعم عرض السعر خلال 24 ساعة', 'strength_2_k': 'الإنتاج', 'strength_2_v': 'يتوفر OEM / ODM', 'strength_3_k': 'المعايير', 'strength_3_v': 'DIN / ISO / تصنيع حسب الرسم', 'strength_4_k': 'التسليم', 'strength_4_v': 'دعم التعبئة والشحن للتصدير', 'why_title': 'لماذا يعمل المشترون مع WT Fasteners', 'why_1': 'عرض سعر سريع بناء على الرسم أو المعيار أو العينة', 'why_2': 'رقابة جودة مستقرة للطلبات الدولية المتكررة', 'why_3': 'دعم مرن للأبعاد والطلاءات المخصصة', 'process_title': 'خطوات شراء بسيطة', 'process_1': 'أرسل الرسم أو المقاس أو المعيار أو مرجع العينة', 'process_2': 'أكد المادة والمعالجة والكمية وموعد التسليم', 'process_3': 'استلم عرض السعر ومدة التوريد وخطة التعبئة'},
    'id': {'html_lang': 'id', 'cta_quote': 'Dapatkan penawaran 24 jam', 'cta_chat': 'WhatsApp sekarang', 'form_title': 'Kirim kebutuhan Anda', 'form_btn': 'Kirim permintaan', 'privacy': 'Kebijakan privasi', 'lead_notice': 'Halaman penawaran fastener industri', 'name_ph': 'Nama *', 'email_ph': 'Email *', 'company_ph': 'Perusahaan', 'phone_ph': 'Telepon / WhatsApp', 'message_ph': 'Jelaskan spesifikasi, jumlah, dan kebutuhan lead time *', 'sticky_note': 'Butuh pesanan cepat atau restock?', 'sticky_hint': 'WhatsApp biasanya cara tercepat untuk konfirmasi spesifikasi dan lead time.', 'trust_title': 'Kemampuan suplai sekilas', 'strength_1_k': 'Respons', 'strength_1_v': 'Dukungan penawaran 24 jam', 'strength_2_k': 'Produksi', 'strength_2_v': 'OEM / ODM tersedia', 'strength_3_k': 'Standar', 'strength_3_v': 'DIN / ISO / sesuai gambar', 'strength_4_k': 'Pengiriman', 'strength_4_v': 'Dukungan packing ekspor & pengiriman', 'why_title': 'Mengapa pembeli memilih WT Fasteners', 'why_1': 'Penawaran cepat berdasarkan gambar, standar, atau sampel', 'why_2': 'Kontrol kualitas stabil untuk pesanan ekspor berulang', 'why_3': 'Dukungan fleksibel untuk ukuran dan finishing khusus', 'process_title': 'Proses pembelian sederhana', 'process_1': 'Kirim gambar, ukuran, standar, atau referensi sampel', 'process_2': 'Konfirmasi material, finishing, jumlah, dan target pengiriman', 'process_3': 'Terima penawaran, lead time, dan rencana packing'},
    'ja': {'html_lang': 'ja', 'cta_quote': '24時間以内に見積回答', 'cta_chat': 'WhatsApp で相談', 'form_title': 'ご要望を送信', 'form_btn': '送信する', 'privacy': 'プライバシーポリシー', 'lead_notice': '工業用ファスナー見積ページ', 'name_ph': 'お名前 *', 'email_ph': 'メールアドレス *', 'company_ph': '会社名', 'phone_ph': '電話 / WhatsApp', 'message_ph': '仕様・数量・希望納期をご記入ください *', 'sticky_note': '至急案件や補充のご相談ですか？', 'sticky_hint': '仕様や納期確認は WhatsApp が最も早いことが多いです。', 'trust_title': '供給対応力をひと目で', 'strength_1_k': '対応', 'strength_1_v': '24時間以内の見積対応', 'strength_2_k': '生産', 'strength_2_v': 'OEM / ODM 対応', 'strength_3_k': '規格', 'strength_3_v': 'DIN / ISO / 図面対応', 'strength_4_k': '出荷', 'strength_4_v': '輸出梱包と出荷サポート', 'why_title': 'WT Fasteners が選ばれる理由', 'why_1': '図面・規格・サンプルに基づく迅速な見積', 'why_2': '継続的な海外注文に向けた安定した品質管理', 'why_3': '特注寸法や表面処理にも柔軟対応', 'process_title': 'シンプルな調達フロー', 'process_1': '図面、サイズ、規格、またはサンプル情報を送信', 'process_2': '材質、表面処理、数量、納期目標を確認', 'process_3': '見積、納期、梱包案を受領'},
    'ko': {'html_lang': 'ko', 'cta_quote': '24시간 내 견적 회신', 'cta_chat': 'WhatsApp 바로 문의', 'form_title': '요구사항을 보내주세요', 'form_btn': '문의 제출', 'privacy': '개인정보처리방침', 'lead_notice': '산업용 패스너 견적 랜딩페이지', 'name_ph': '이름 *', 'email_ph': '이메일 *', 'company_ph': '회사명', 'phone_ph': '전화 / WhatsApp', 'message_ph': '사양, 수량, 납기 요청을 입력해 주세요 *', 'sticky_note': '긴급 주문이나 재보충이 필요하신가요?', 'sticky_hint': '사양과 납기 확인은 WhatsApp 이 가장 빠른 경우가 많습니다.', 'trust_title': '공급 역량 한눈에 보기', 'strength_1_k': '응답', 'strength_1_v': '24시간 견적 지원', 'strength_2_k': '생산', 'strength_2_v': 'OEM / ODM 가능', 'strength_3_k': '규격', 'strength_3_v': 'DIN / ISO / 도면 맞춤', 'strength_4_k': '납품', 'strength_4_v': '수출 포장 및 선적 지원', 'why_title': 'WT Fasteners를 선택하는 이유', 'why_1': '도면, 규격 또는 샘플 기준의 빠른 견적', 'why_2': '반복 해외 주문에 적합한 안정적 품질관리', 'why_3': '비표준 치수와 표면처리도 유연하게 지원', 'process_title': '간단한 구매 프로세스', 'process_1': '도면, 치수, 규격 또는 샘플 정보를 전달', 'process_2': '재질, 표면처리, 수량 및 납기 목표 확인', 'process_3': '견적, 납기 및 포장 계획 수령'},
}


def build_html(lang, slug, title, subtitle, summary, meta_desc, keywords, bc_label, body, hero_image, whatsapp_url, extra_head):
    c = LC.get(lang, LC['en'])
    html_lang = c['html_lang']
    dir_attr = ' dir="rtl"' if lang == 'ar' else ''
    image_src = '../../../images/' + hero_image if hero_image else '../../../images/banner-hero.webp'
    head_extra = ('\n' + extra_head + '\n') if extra_head else ''
    keyword_chips = build_keyword_chips(keywords)
    language_switch = build_language_switch(lang, slug)
    trust_cards = ''.join([
        f'<article class="stat-card"><span>{he(c["strength_1_k"])}</span><strong>{he(c["strength_1_v"])}</strong></article>',
        f'<article class="stat-card"><span>{he(c["strength_2_k"])}</span><strong>{he(c["strength_2_v"])}</strong></article>',
        f'<article class="stat-card"><span>{he(c["strength_3_k"])}</span><strong>{he(c["strength_3_v"])}</strong></article>',
        f'<article class="stat-card"><span>{he(c["strength_4_k"])}</span><strong>{he(c["strength_4_v"])}</strong></article>',
    ])
    why_cards = ''.join([
        f'<li>{he(c["why_1"])}</li>',
        f'<li>{he(c["why_2"])}</li>',
        f'<li>{he(c["why_3"])}</li>',
    ])
    process_steps = ''.join([
        f'<li>{he(c["process_1"])}</li>',
        f'<li>{he(c["process_2"])}</li>',
        f'<li>{he(c["process_3"])}</li>',
    ])
    faq_items = ''.join([
        f'<article class="faq-item"><h3>{he(c.get("faq_q1", ""))}</h3><p>{he(c.get("faq_a1", ""))}</p></article>',
        f'<article class="faq-item"><h3>{he(c.get("faq_q2", ""))}</h3><p>{he(c.get("faq_a2", ""))}</p></article>',
        f'<article class="faq-item"><h3>{he(c.get("faq_q3", ""))}</h3><p>{he(c.get("faq_a3", ""))}</p></article>',
    ])

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
      --bg: #f6f7f4;
      --panel: rgba(255, 255, 255, 0.88);
      --panel-strong: rgba(248, 250, 252, 0.96);
      --line: rgba(148, 163, 184, 0.22);
      --text: #0f172a;
      --muted: #526072;
      --cta: #22c55e;
      --cta2: #f97316;
      --accent: #0ea5e9;
      --accent-soft: rgba(14, 165, 233, 0.1);
      --radius: 18px;
      --shadow: 0 28px 60px rgba(148, 163, 184, 0.18);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: "Inter","PingFang SC","Noto Sans SC",sans-serif;
      background:
        radial-gradient(circle at top left, rgba(14,165,233,.12), transparent 26%),
        radial-gradient(circle at 85% 10%, rgba(249,115,22,.12), transparent 24%),
        linear-gradient(180deg,#fbfcfd 0%,#f4f7fb 48%,#eef3f8 100%);
      color: var(--text);
      line-height: 1.6;
      padding-bottom: 108px;
    }}
    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image: linear-gradient(rgba(148,163,184,.09) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,.09) 1px, transparent 1px);
      background-size: 52px 52px;
      mask-image: linear-gradient(180deg, rgba(255,255,255,.8), transparent 78%);
    }}
    .wrap {{ max-width: 1180px; margin: 0 auto; padding: 0 20px; position: relative; z-index: 1; }}
    .topbar {{ padding-top: 20px; display: flex; justify-content: flex-end; }}
    .lang-switch {{ display: flex; justify-content: flex-end; }}
    .lang-picker {{ display: inline-flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 999px; border: 1px solid rgba(148,163,184,.24); background: rgba(255,255,255,.84); box-shadow: 0 10px 22px rgba(148,163,184,.12); }}
    .lang-picker-label {{ color: #0f766e; font-size: .82rem; font-weight: 800; }}
    .lang-select {{ appearance: none; -webkit-appearance: none; border: 0; background: transparent; color: #334155; font-size: .82rem; font-weight: 700; padding-right: 18px; outline: none; cursor: pointer; min-width: 108px; }}
    .hero {{ padding: 34px 0 22px; }}
    .hero-grid {{ display: grid; grid-template-columns: 1.08fr .92fr; gap: 22px; align-items: stretch; }}
    .hero-copy, .hero-media, .section, .form-box {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 22px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }}
    .hero-copy {{ padding: 28px; position: relative; overflow: hidden; }}
    .hero-copy::after {{
      content: "";
      position: absolute;
      width: 220px;
      height: 220px;
      border-radius: 50%;
      right: -80px;
      top: -80px;
      background: radial-gradient(circle, rgba(14,165,233,.14), transparent 68%);
      pointer-events: none;
    }}
    .hero-copy .badge {{
      display: inline-block;
      padding: 7px 12px;
      border-radius: 999px;
      border: 1px solid rgba(14,165,233,.22);
      background: var(--accent-soft);
      color: #0369a1;
      font-size: .82rem;
      font-weight: 700;
      margin-bottom: 12px;
    }}
    h1 {{ font-size: clamp(2rem, 4.4vw, 3.35rem); line-height: 1.05; margin-bottom: 12px; max-width: 12ch; }}
    .subtitle {{ color: #1e293b; margin-bottom: 10px; font-size: 1.02rem; }}
    .summary {{ color: var(--muted); margin-bottom: 18px; font-size: 1rem; max-width: 60ch; }}
    .chip-row {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 0 0 18px; }}
    .chip {{
      display: inline-flex;
      align-items: center;
      padding: 7px 10px;
      border-radius: 999px;
      border: 1px solid rgba(148,163,184,.24);
      background: rgba(255,255,255,.72);
      color: #334155;
      font-size: .8rem;
      font-weight: 700;
    }}
    .cta {{ display: flex; gap: 10px; flex-wrap: wrap; }}
    .btn {{
      display: inline-flex;
      justify-content: center;
      align-items: center;
      border: 0;
      border-radius: 12px;
      text-decoration: none;
      color: #fff;
      font-weight: 800;
      padding: 12px 18px;
      box-shadow: 0 14px 28px rgba(0,0,0,.18);
    }}
    .btn.chat {{ background: linear-gradient(135deg, #22c55e, #16a34a); }}
    .btn.quote {{ background: linear-gradient(135deg, #fb923c, #ea580c); }}
    .hero-media {{ padding: 12px; background: linear-gradient(180deg, rgba(255,255,255,.96), rgba(241,245,249,.94)); }}
    .hero-media img {{ width: 100%; height: 100%; min-height: 360px; object-fit: cover; border-radius: 16px; box-shadow: 0 20px 42px rgba(148,163,184,.18); }}
    .trust-strip {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-top: 16px; }}
    .stat-card {{ background: rgba(255,255,255,.78); border: 1px solid rgba(148,163,184,.22); border-radius: 18px; padding: 16px; box-shadow: 0 16px 36px rgba(148,163,184,.12); }}
    .stat-card span {{ display: block; color: #64748b; font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 8px; }}
    .stat-card strong {{ display: block; font-size: 1rem; line-height: 1.4; color: #0f172a; }}
    .section {{ margin-top: 18px; padding: 28px; }}
    .section h2 {{ margin-bottom: 14px; font-size: 1.5rem; }}
    .article-body :where(p,li) {{ color: var(--muted); margin-bottom: 12px; font-size: 1rem; }}
    .article-body :where(h2,h3,h4) {{ margin: 20px 0 12px; color: #0f172a; }}
    .article-body ul, .article-body ol {{ padding-inline-start: 20px; }}
    .article-body img {{ max-width: 100%; height: auto; border-radius: 14px; border: 1px solid var(--line); box-shadow: 0 18px 40px rgba(148,163,184,.16); }}
    .biz-grid {{ display: grid; grid-template-columns: 1.05fr .95fr; gap: 18px; margin-top: 18px; }}
    .biz-box {{ background: rgba(255,255,255,.84); border: 1px solid rgba(148,163,184,.22); border-radius: 22px; padding: 24px; box-shadow: 0 20px 42px rgba(148,163,184,.14); }}
    .biz-box h3 {{ margin-bottom: 12px; font-size: 1.18rem; color: #0f172a; }}
    .biz-box ul, .biz-box ol {{ padding-inline-start: 20px; color: #526072; display: grid; gap: 10px; }}
    .faq-section {{ margin-top: 18px; background: rgba(255,255,255,.88); border: 1px solid rgba(148,163,184,.22); border-radius: 22px; padding: 28px; box-shadow: 0 20px 42px rgba(148,163,184,.14); }}
    .faq-section h2 {{ margin-bottom: 14px; font-size: 1.36rem; color: #0f172a; }}
    .faq-list {{ display: grid; gap: 12px; }}
    .faq-item {{ padding: 16px 18px; border-radius: 16px; border: 1px solid rgba(148,163,184,.18); background: rgba(248,250,252,.86); }}
    .faq-item h3 {{ margin-bottom: 8px; font-size: 1rem; color: #0f172a; }}
    .faq-item p {{ color: #526072; line-height: 1.7; }}
    .form-box {{ margin-top: 18px; padding: 24px; background: linear-gradient(180deg, rgba(255,255,255,.96), rgba(244,247,252,.95)); color: #0f172a; }}
    .form-box h3 {{ margin-bottom: 8px; font-size: 1.34rem; color: #0f172a; }}
    .form-box p {{ color: #475569; margin-bottom: 12px; }}
    .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    input, textarea {{
      width: 100%;
      border: 1px solid #cbd5e1;
      border-radius: 12px;
      padding: 11px 12px;
      background: #fff;
      color: #0f172a;
      font-size: .95rem;
    }}
    textarea {{ min-height: 110px; resize: vertical; }}
    .field {{ margin-bottom: 10px; }}
    .submit-btn {{
      width: 100%;
      background: linear-gradient(135deg, #2563eb, #1d4ed8);
      color: #fff;
      border: 0;
      border-radius: 12px;
      padding: 13px 14px;
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 14px 28px rgba(37,99,235,.18);
    }}
    .fixed-wa {{
      position: fixed;
      left: 0; right: 0; bottom: 12px;
      margin: 0 auto;
      max-width: 1180px;
      padding: 0 20px;
      z-index: 90;
    }}
    .fixed-wa-inner {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 14px;
      border: 1px solid rgba(148,163,184,.24);
      background: rgba(255,255,255,.94);
      border-radius: 16px;
      padding: 12px 14px;
      backdrop-filter: blur(10px);
      box-shadow: 0 20px 42px rgba(148,163,184,.18);
    }}
    .sticky-copy {{ display: grid; gap: 2px; }}
    .fixed-wa b {{ font-size: .96rem; }}
    .sticky-copy span {{ color: var(--muted); font-size: .82rem; }}
    .fixed-wa a {{
      text-decoration: none;
      color: #fff;
      background: linear-gradient(135deg, #22c55e, #16a34a);
      border-radius: 10px;
      padding: 11px 14px;
      font-weight: 800;
    }}
    .foot {{ color: var(--muted); font-size: .84rem; margin: 20px 0 14px; text-align: center; }}
    @media (max-width: 860px) {{
      .hero-grid, .row, .biz-grid, .trust-strip {{ grid-template-columns: 1fr; }}
      h1 {{ max-width: none; }}
      .hero-media img {{ min-height: 260px; }}
      .fixed-wa-inner {{ flex-direction: column; align-items: stretch; }}
      .fixed-wa a {{ text-align: center; }}
      body {{ padding-bottom: 148px; }}
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <div class="topbar">
      <nav class="lang-switch" aria-label="Language switcher">
        {language_switch}
      </nav>
    </div>
    <section class="hero">
      <div class="hero-grid">
        <article class="hero-copy">
          <span class="badge">{he(c['lead_notice'])}</span>
          <h1>{he(title)}</h1>
          <p class="subtitle">{he(subtitle)}</p>
          <p class="summary">{he(summary)}</p>
          <div class="chip-row">{keyword_chips}</div>
          <div class="cta">
            <a class="btn chat" href="{he(whatsapp_url)}" target="_blank" rel="noopener">{he(c['cta_chat'])}</a>
            <a class="btn quote" href="#lead-form">{he(c['cta_quote'])}</a>
          </div>
        </article>
        <aside class="hero-media">
          <img src="{he(image_src)}" alt="{he(title)}" loading="eager" fetchpriority="high">
        </aside>
      </div>
      <div class="trust-strip" aria-label="{he(c['trust_title'])}">
        {trust_cards}
      </div>
    </section>

    <section class="section">
      <h2>{he(bc_label or title)}</h2>
      <article class="article-body">
{body}
      </article>
    </section>

    <section class="biz-grid">
      <article class="biz-box">
        <h3>{he(c['why_title'])}</h3>
        <ul>{why_cards}</ul>
      </article>
      <article class="biz-box">
        <h3>{he(c['process_title'])}</h3>
        <ol>{process_steps}</ol>
      </article>
    </section>

    <section class="faq-section">
      <h2>{he(c.get('faq_title', 'Frequently asked questions'))}</h2>
      <div class="faq-list">{faq_items}</div>
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
          <div class="field"><input type="text" name="name" placeholder="{he(c['name_ph'])}" required></div>
          <div class="field"><input type="email" name="email" placeholder="{he(c['email_ph'])}" required></div>
        </div>
        <div class="row">
          <div class="field"><input type="text" name="company" placeholder="{he(c['company_ph'])}"></div>
          <div class="field"><input type="tel" name="phone" placeholder="{he(c['phone_ph'])}"></div>
        </div>
        <div class="field"><textarea name="message" placeholder="{he(c['message_ph'])}" required></textarea></div>
        <button class="submit-btn" type="submit">{he(c['form_btn'])}</button>
      </form>
    </section>

    <p class="foot"><a href="/pags/{lang}/privacy-policy.html" style="color:#b8c6de">{he(c['privacy'])}</a></p>
  </main>

  <div class="fixed-wa">
    <div class="fixed-wa-inner">
      <div class="sticky-copy">
        <b>{he(c['sticky_note'])}</b>
        <span>{he(c['sticky_hint'])}</span>
      </div>
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
    safe_chmod(out_dir, 0o755)
    out_file = os.path.join(out_dir, slug + '.html')
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(content)
    safe_chmod(out_file, 0o644)
    return out_file


def verify_landing_output(lang, slug, html_path):
    expected_dir = os.path.join(BASE_DIR, 'pags', lang, 'landing')
    safe_expected_dir = os.path.abspath(expected_dir)
    safe_html_path = os.path.abspath(html_path)
    if os.path.commonpath([safe_expected_dir, safe_html_path]) != safe_expected_dir:
        return f'{lang}: html path escaped landing dir'
    if os.path.dirname(safe_html_path) != safe_expected_dir:
        return f'{lang}: html not under /pags/{lang}/landing/'
    if not os.path.exists(safe_html_path):
        return f'{lang}: html file not written'
    if not safe_html_path.endswith(os.sep + slug + '.html'):
        return f'{lang}: html filename mismatch'
    return ''


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
prepared_lang_payloads = []

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

target_langs = list(LANGS)
if translated_langs_present:
    target_langs = ['en'] + [l for l in LANGS if l in translated_langs_set]

for lang in target_langs:
    title_input = g(form, f'{lang}_title')
    subtitle_input = g(form, f'{lang}_subtitle')
    summary_input = g(form, f'{lang}_summary')
    meta_input = g(form, f'{lang}_meta_desc')
    kw_input = g(form, f'{lang}_keywords')
    bc_input = g(form, f'{lang}_bc_label')
    body_input = g(form, f'{lang}_body')
    has_manual_localized_input = any([title_input, subtitle_input, summary_input, meta_input, kw_input, bc_input, body_input])

    # Match article/product flow: untouched non-EN pages wait for DeepSeek.
    if auto_translate and lang != 'en' and not has_manual_localized_input:
        continue

    data = {
        'lang': lang,
        'title': title_input or source_fields['title'],
        'subtitle': subtitle_input or source_fields['subtitle'],
        'summary': summary_input or source_fields['summary'],
        'meta_desc': meta_input or source_fields['meta_desc'],
        'keywords': kw_input or source_fields['keywords'],
        'bc_label': bc_input or source_fields['bc_label'],
        'body': body_input or source_fields['body'],
    }
    prepared_lang_payloads.append(data)

for payload in prepared_lang_payloads:
    try:
        html = build_html(
            payload['lang'], slug,
            payload['title'], payload['subtitle'], payload['summary'],
            payload['meta_desc'], payload['keywords'], payload['bc_label'],
            payload['body'], hero_image, whatsapp_url, extra_head
        )
        html_path = save_one(payload['lang'], slug, html)
        verify_error = verify_landing_output(payload['lang'], slug, html_path)
        if verify_error:
            errors.append(verify_error)
            continue
        created.append(payload['lang'])
    except Exception as exc:
        errors.append(f"{payload['lang']}: {exc}")

fork_error = None
translating = False
if auto_translate:
    translating = True
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
