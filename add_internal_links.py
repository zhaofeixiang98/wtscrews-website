#!/usr/bin/env python3
"""
为所有语言的产品详情页和文章页添加内链模块。
- 产品页：在 CTA 区域前注入"相关产品"板块（同类目其他产品，最多3个）
- 文章页：在 </main> 前注入"推荐产品"板块（每大类首个产品，最多4个）
"""
import os
import json

LANGS = ['zh', 'en', 'de', 'fr', 'es', 'ar', 'id', 'ja', 'ko']
BASE_DIR = os.path.join(os.path.dirname(__file__), 'pags')

RELATED_HEADING = {
    'zh': '相关产品',
    'en': 'Related Products',
    'de': 'Ähnliche Produkte',
    'fr': 'Produits connexes',
    'es': 'Productos relacionados',
    'ar': 'منتجات ذات صلة',
    'id': 'Produk Terkait',
    'ja': '関連製品',
    'ko': '관련 제품',
}

ARTICLE_HEADING = {
    'zh': '推荐产品',
    'en': 'Recommended Products',
    'de': 'Empfohlene Produkte',
    'fr': 'Produits recommandés',
    'es': 'Productos recomendados',
    'ar': 'المنتجات الموصى بها',
    'id': 'Produk yang Direkomendasikan',
    'ja': 'おすすめ製品',
    'ko': '추천 제품',
}

VIEW_MORE = {
    'zh': '查看详情 →',
    'en': 'View Details →',
    'de': 'Details →',
    'fr': 'Voir détails →',
    'es': 'Ver detalles →',
    'ar': 'عرض التفاصيل →',
    'id': 'Lihat Detail →',
    'ja': '詳細を見る →',
    'ko': '자세히 보기 →',
}


def load_json(lang):
    path = os.path.join(BASE_DIR, lang, f'pages_{lang}.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_product_map(data):
    """
    Returns {slug_filename: {title, summary, icon, category, category_items}}
    slug_filename = e.g. 'hex-bolts'
    """
    product_map = {}
    for cat in data['products']:
        for item in cat['items']:
            fname = item['slug'].split('/')[-1]
            product_map[fname] = {
                'title': item['title'],
                'summary': item['summary'],
                'icon': item['icon'],
                'category': cat['category'],
                'category_items': cat['items'],
            }
    return product_map


def icon_to_product_page_path(icon):
    """
    JSON icon 路径形如 "../../images/products/bolts/Hex Bolt0.webp"
    产品页、文章页均在 pags/{lang}/products/ 或 pags/{lang}/news/ 下，
    需要 ../../../images/ 才能到达工作区根目录下的 images/
    """
    return icon.replace('../../images/', '../../../images/', 1)


def build_cards_html(items, href_prefix, lang, max_cards=3):
    """生成 related-card 列表 HTML"""
    cards = []
    for item in items[:max_cards]:
        slug = item['slug'].split('/')[-1]
        href = f"{href_prefix}{slug}.html"
        img_src = icon_to_product_page_path(item['icon'])
        title = item['title']
        summary = item['summary']
        view_more = VIEW_MORE.get(lang, 'View →')
        cards.append(f'''\
        <a href="{href}" class="related-card">
          <div class="related-card-image">
            <img src="{img_src}" alt="{title}" loading="lazy" style="width:100%;height:100%;object-fit:cover;">
          </div>
          <div class="related-card-body">
            <h4>{title}</h4>
            <p>{summary}</p>
            <span class="related-card-link">{view_more}</span>
          </div>
        </a>''')
    return '\n'.join(cards)


def build_related_section(items_for_cards, href_prefix, heading, lang):
    cards_html = build_cards_html(items_for_cards, href_prefix, lang, max_cards=3)
    if not cards_html:
        return ''
    return f'''
    <!-- Related Products -->
    <section class="section">
      <article class="container">
        <div class="related-products">
          <h3>{heading}</h3>
          <div class="related-grid">
{cards_html}
          </div>
        </div>
      </article>
    </section>
'''


def inject_before(content, marker, injection):
    """在 marker 第一次出现之前插入 injection，返回新内容"""
    idx = content.find(marker)
    if idx == -1:
        return None
    return content[:idx] + injection + content[idx:]


# ── Product pages ──────────────────────────────────────────────────────────

def process_product_page(filepath, current_slug, category_items, heading, lang):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'related-products' in content:
        print(f'  [SKIP] already has related-products: {os.path.basename(filepath)}')
        return False

    # 同类其他产品
    related = [i for i in category_items if i['slug'].split('/')[-1] != current_slug]
    if not related:
        print(f'  [SKIP] no other products in category: {os.path.basename(filepath)}')
        return False

    section_html = build_related_section(related, '', heading, lang)

    # 注入点：CTA section 之前
    new_content = inject_before(content, '<section class="cta-section">', section_html)
    if new_content is None:
        # 备用注入点：</main>
        new_content = inject_before(content, '\n  </main>', section_html)
    if new_content is None:
        print(f'  [WARN] injection point not found: {filepath}')
        return False

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'  [OK] product related: {os.path.basename(filepath)}')
    return True


# ── Article pages ──────────────────────────────────────────────────────────

def process_article_page(filepath, featured_items, heading, lang):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'related-products' in content:
        print(f'  [SKIP] already has related-products: {os.path.basename(filepath)}')
        return False

    section_html = build_related_section(featured_items, '../products/', heading, lang)

    new_content = inject_before(content, '\n  </main>', section_html)
    if new_content is None:
        new_content = inject_before(content, '</main>', section_html)
    if new_content is None:
        print(f'  [WARN] injection point not found: {filepath}')
        return False

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'  [OK] article related: {os.path.basename(filepath)}')
    return True


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    total_ok = 0
    total_skip = 0

    for lang in LANGS:
        print(f'\n=== {lang} ===')
        lang_dir = os.path.join(BASE_DIR, lang)

        try:
            data = load_json(lang)
        except Exception as e:
            print(f'  [ERROR] load JSON: {e}')
            continue

        product_map = get_product_map(data)
        rel_heading = RELATED_HEADING.get(lang, 'Related Products')
        art_heading = ARTICLE_HEADING.get(lang, 'Recommended Products')

        # 产品页
        products_dir = os.path.join(lang_dir, 'products')
        if os.path.isdir(products_dir):
            for fname in sorted(os.listdir(products_dir)):
                if not fname.endswith('.html'):
                    continue
                slug = fname[:-5]
                if slug not in product_map:
                    print(f'  [WARN] slug not in JSON: {slug}')
                    continue
                fpath = os.path.join(products_dir, fname)
                ok = process_product_page(fpath, slug,
                                          product_map[slug]['category_items'],
                                          rel_heading, lang)
                if ok:
                    total_ok += 1
                else:
                    total_skip += 1

        # 文章页 —— 每个大类取第一个产品作为"推荐产品"
        news_dir = os.path.join(lang_dir, 'news')
        if os.path.isdir(news_dir):
            featured = []
            for cat in data['products']:
                if cat['items']:
                    featured.append(cat['items'][0])
                if len(featured) >= 4:
                    break

            for fname in sorted(os.listdir(news_dir)):
                if not fname.endswith('.html'):
                    continue
                fpath = os.path.join(news_dir, fname)
                ok = process_article_page(fpath, featured, art_heading, lang)
                if ok:
                    total_ok += 1
                else:
                    total_skip += 1

    print(f'\n✓ Done — injected: {total_ok}, skipped: {total_skip}')


if __name__ == '__main__':
    main()
