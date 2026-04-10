#!/usr/bin/env python3
"""Fix remaining untranslated surface finish values in 10 product files × 7 languages."""
import os, re

# Surface finish term translations per language
TERMS = {
    'zh': {'Zinc Plated': '镀锌', 'Hot-Dip Galvanized': '热镀锌', 'Black Oxide': '黑色氧化', 'Dacromet': '达克罗', 'Geomet': '几何', 'Plain': '原色', 'Sherardized': '渗锌', 'Passivation': '钝化'},
    'ar': {'Zinc Plated': 'مطلي بالزنك', 'Hot-Dip Galvanized': 'مجلفن بالغمس الساخن', 'Black Oxide': 'أكسيد أسود', 'Dacromet': 'داكروميت', 'Geomet': 'جيوميت', 'Plain': 'سادة', 'Sherardized': 'شيرارديز', 'Passivation': 'تخميل'},
    'de': {'Zinc Plated': 'verzinkt', 'Hot-Dip Galvanized': 'feuerverzinkt', 'Black Oxide': 'Schwarzoxid', 'Dacromet': 'Dacromet', 'Geomet': 'Geomet', 'Plain': 'blank', 'Sherardized': 'sherardisiert', 'Passivation': 'Passivierung'},
    'es': {'Zinc Plated': 'galvanizado', 'Hot-Dip Galvanized': 'galvanizado en caliente', 'Black Oxide': 'óxido negro', 'Dacromet': 'Dacromet', 'Geomet': 'Geomet', 'Plain': 'natural', 'Sherardized': 'sherardizado', 'Passivation': 'pasivación'},
    'fr': {'Zinc Plated': 'zingué', 'Hot-Dip Galvanized': 'galvanisé à chaud', 'Black Oxide': 'oxyde noir', 'Dacromet': 'Dacromet', 'Geomet': 'Geomet', 'Plain': 'brut', 'Sherardized': 'shérardisé', 'Passivation': 'passivation'},
    'id': {'Zinc Plated': 'berlapis seng', 'Hot-Dip Galvanized': 'galvanis celup panas', 'Black Oxide': 'oksida hitam', 'Dacromet': 'Dacromet', 'Geomet': 'Geomet', 'Plain': 'polos', 'Sherardized': 'sherardisasi', 'Passivation': 'pasivasi'},
    'ko': {'Zinc Plated': '아연 도금', 'Hot-Dip Galvanized': '용융 아연 도금', 'Black Oxide': '흑색 산화', 'Dacromet': '다크로멧', 'Geomet': '지오멧', 'Plain': '무도금', 'Sherardized': '셰라다이징', 'Passivation': '부동태화'},
}

# FAQ answer translations per language
FAQ_ANSWERS = {
    'zh': {
        'flange-bolts': '我们提供镀锌、热镀锌、黑色氧化、达克罗及按要求定制的表面处理。',
        'flat-washers': '是的，我们提供镀锌、热镀锌、黑色氧化和钝化表面处理。',
        'high-strength-bolts': '我们提供黑色氧化、镀锌、热镀锌和达克罗表面处理。',
        'flange-nuts': '我们提供镀锌、热镀锌和黑色氧化表面处理。',
        'hex-nuts': '我们提供镀锌、热镀锌、黑色氧化和钝化表面处理。',
    },
    'ar': {
        'flange-bolts': 'نقدم مطلي بالزنك، مجلفن بالغمس الساخن، أكسيد أسود، داكروميت، وتشطيبات مخصصة حسب الطلب.',
        'flat-washers': 'نعم، نقدم مطلي بالزنك، مجلفن بالغمس الساخن، أكسيد أسود، وتخميل.',
        'high-strength-bolts': 'نقدم أكسيد أسود، مطلي بالزنك، مجلفن بالغمس الساخن، وداكروميت.',
        'flange-nuts': 'نقدم مطلي بالزنك، مجلفن بالغمس الساخن، وأكسيد أسود.',
        'hex-nuts': 'نقدم مطلي بالزنك، مجلفن بالغمس الساخن، أكسيد أسود، وتخميل.',
    },
    'de': {
        'flange-bolts': 'Wir bieten verzinkt, feuerverzinkt, Schwarzoxid, Dacromet und kundenspezifische Oberflächen auf Anfrage.',
        'flat-washers': 'Ja, wir bieten verzinkt, feuerverzinkt, Schwarzoxid und Passivierung.',
        'high-strength-bolts': 'Wir bieten Schwarzoxid, verzinkt, feuerverzinkt und Dacromet.',
        'flange-nuts': 'Wir bieten verzinkt, feuerverzinkt und Schwarzoxid.',
        'hex-nuts': 'Wir bieten verzinkt, feuerverzinkt, Schwarzoxid und Passivierung.',
    },
    'es': {
        'flange-bolts': 'Ofrecemos galvanizado, galvanizado en caliente, óxido negro, Dacromet y acabados personalizados bajo pedido.',
        'flat-washers': 'Sí, ofrecemos galvanizado, galvanizado en caliente, óxido negro y pasivación.',
        'high-strength-bolts': 'Ofrecemos óxido negro, galvanizado, galvanizado en caliente y Dacromet.',
        'flange-nuts': 'Ofrecemos galvanizado, galvanizado en caliente y óxido negro.',
        'hex-nuts': 'Ofrecemos galvanizado, galvanizado en caliente, óxido negro y pasivación.',
    },
    'fr': {
        'flange-bolts': 'Nous proposons zingué, galvanisé à chaud, oxyde noir, Dacromet et des finitions sur mesure sur demande.',
        'flat-washers': 'Oui, nous proposons zingué, galvanisé à chaud, oxyde noir et passivation.',
        'high-strength-bolts': 'Nous proposons oxyde noir, zingué, galvanisé à chaud et Dacromet.',
        'flange-nuts': 'Nous proposons zingué, galvanisé à chaud et oxyde noir.',
        'hex-nuts': 'Nous proposons zingué, galvanisé à chaud, oxyde noir et passivation.',
    },
    'id': {
        'flange-bolts': 'Kami menawarkan berlapis seng, galvanis celup panas, oksida hitam, Dacromet, dan finishing khusus sesuai permintaan.',
        'flat-washers': 'Ya, kami menawarkan berlapis seng, galvanis celup panas, oksida hitam, dan pasivasi.',
        'high-strength-bolts': 'Kami menawarkan oksida hitam, berlapis seng, galvanis celup panas, dan Dacromet.',
        'flange-nuts': 'Kami menawarkan berlapis seng, galvanis celup panas, dan oksida hitam.',
        'hex-nuts': 'Kami menawarkan berlapis seng, galvanis celup panas, oksida hitam, dan pasivasi.',
    },
    'ko': {
        'flange-bolts': '아연 도금, 용융 아연 도금, 흑색 산화, 다크로멧 및 요청 시 맞춤 마감을 제공합니다.',
        'flat-washers': '네, 아연 도금, 용융 아연 도금, 흑색 산화 및 부동태화 마감을 제공합니다.',
        'high-strength-bolts': '흑색 산화, 아연 도금, 용융 아연 도금 및 다크로멧 마감을 제공합니다.',
        'flange-nuts': '아연 도금, 용융 아연 도금 및 흑색 산화 마감을 제공합니다.',
        'hex-nuts': '아연 도금, 용융 아연 도금, 흑색 산화 및 부동태화 마감을 제공합니다.',
    },
}

# Surface finish spec-value replacements (exact td content strings)
SPEC_REPLACEMENTS = {
    'Zinc Plated, Hot-Dip Galvanized, Sherardized': lambda t: f"{t['Zinc Plated']}, {t['Hot-Dip Galvanized']}, {t['Sherardized']}",
    'Zinc Plated, Hot-Dip Galvanized, Black Oxide, Dacromet': lambda t: f"{t['Zinc Plated']}, {t['Hot-Dip Galvanized']}, {t['Black Oxide']}, {t['Dacromet']}",
    'Black Oxide, Zinc Plated, Hot-Dip Galvanized, Dacromet': lambda t: f"{t['Black Oxide']}, {t['Zinc Plated']}, {t['Hot-Dip Galvanized']}, {t['Dacromet']}",
    'Zinc Plated, Hot-Dip Galvanized, Black Oxide, Passivation': lambda t: f"{t['Zinc Plated']}, {t['Hot-Dip Galvanized']}, {t['Black Oxide']}, {t['Passivation']}",
    'Zinc Plated, Hot-Dip Galvanized, Black Oxide': lambda t: f"{t['Zinc Plated']}, {t['Hot-Dip Galvanized']}, {t['Black Oxide']}",
    'Zinc Plated, Hot-Dip Galvanized, Plain, Passivation': lambda t: f"{t['Zinc Plated']}, {t['Hot-Dip Galvanized']}, {t['Plain']}, {t['Passivation']}",
    'Zinc Plated, Hot-Dip Galvanized, Plain': lambda t: f"{t['Zinc Plated']}, {t['Hot-Dip Galvanized']}, {t['Plain']}",
    'Plain, Zinc Plated, Hot-Dip Galvanized, Black Oxide': lambda t: f"{t['Plain']}, {t['Zinc Plated']}, {t['Hot-Dip Galvanized']}, {t['Black Oxide']}",
}

# Also fix "Finish" header that wasn't translated
FINISH_HEADER = {
    'ar': 'تشطيب السطح',
    'de': 'Oberflächenbehandlung',
    'es': 'Acabado superficial',
    'fr': 'Finition de surface',
    'id': 'Finishing permukaan',
    'ko': '표면 처리',
    'zh': '表面处理',
}

# FAQ answer patterns to find English FAQ answers about finishes
FAQ_EN_PATTERNS = [
    (r'We offer Zinc Plated, Hot-Dip Galvanized, Black Oxide, Dacromet, and custom finishes upon request\.', 'flange-bolts'),
    (r'Yes, we offer Zinc Plated, Hot-Dip Galvanized, Black Oxide, and Passivation finishes\.', 'flat-washers'),
    (r'We provide Black Oxide, Zinc Plated, Hot-Dip Galvanized, and Dacromet finishes\.', 'high-strength-bolts'),
    (r'We provide Zinc Plated, Hot-Dip Galvanized, and Black Oxide finishes\.', 'flange-nuts'),
    (r'We provide Zinc Plated, Hot-Dip Galvanized, Black Oxide, and Passivation finishes\.', 'hex-nuts'),
]

PRODUCTS = [
    'anchor-bolts', 'double-end-studs', 'flat-washers', 'flange-bolts',
    'flange-nuts', 'hex-nuts', 'high-strength-bolts', 'square-washers',
    'threaded-rods', 'u-bolts'
]

langs = ['zh', 'ar', 'de', 'es', 'fr', 'id', 'ko']
base = '/Users/frank/wtscrews/222/pags'
count = 0

for lang in langs:
    terms = TERMS[lang]
    for prod in PRODUCTS:
        fpath = os.path.join(base, lang, 'products', f'{prod}.html')
        if not os.path.exists(fpath):
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        original = content

        # Fix spec table values
        for en_val, make_translated in SPEC_REPLACEMENTS.items():
            translated = make_translated(terms)
            content = content.replace(en_val, translated)

        # Fix "Finish" header (some files have untranslated <th>Finish</th>)
        if lang in FINISH_HEADER:
            content = content.replace('<th>Finish</th>', f'<th>{FINISH_HEADER[lang]}</th>')

        # Fix FAQ answers about finishes
        faq_answers = FAQ_ANSWERS.get(lang, {})
        for pattern, prod_key in FAQ_EN_PATTERNS:
            if prod == prod_key or True:  # Apply to any file that has this text
                if prod_key in faq_answers:
                    content = re.sub(pattern, faq_answers[prod_key], content)

        # Fix JSON-LD "Finish" value
        content = content.replace('"Zinc Plated, Hot-Dip Galvanized"', f'"{terms["Zinc Plated"]}, {terms["Hot-Dip Galvanized"]}"')

        if content != original:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)
            count += 1
            print(f'Fixed: {lang}/{prod}')

print(f'\nTotal files fixed: {count}')
