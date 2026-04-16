from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "pags"

TEXTS = {
    "en": {
        "product_link": "View Details ->",
        "news_link": "Read More ->",
        "lang_label": "Select language",
        "news_section": "Latest Articles",
    },
    "zh": {
        "product_link": "查看详情 ->",
        "news_link": "阅读全文 ->",
        "lang_label": "选择语言",
        "news_section": "最新文章",
    },
    "de": {
        "product_link": "Details ansehen ->",
        "news_link": "Mehr lesen ->",
        "lang_label": "Sprache auswahlen",
        "news_section": "Neueste Artikel",
    },
    "es": {
        "product_link": "Ver detalles ->",
        "news_link": "Leer mas ->",
        "lang_label": "Seleccionar idioma",
        "news_section": "Articulos recientes",
    },
    "fr": {
        "product_link": "Voir les details ->",
        "news_link": "Lire la suite ->",
        "lang_label": "Choisir la langue",
        "news_section": "Derniers articles",
    },
    "id": {
        "product_link": "Lihat Detail ->",
        "news_link": "Baca Selengkapnya ->",
        "lang_label": "Pilih bahasa",
        "news_section": "Artikel terbaru",
    },
    "ja": {
        "product_link": "詳細を見る ->",
        "news_link": "続きを読む ->",
        "lang_label": "言語を選択",
        "news_section": "最新記事",
    },
    "ko": {
        "product_link": "자세히 보기 ->",
        "news_link": "더 읽기 ->",
        "lang_label": "언어 선택",
        "news_section": "최신 기사",
    },
    "ar": {
        "product_link": "عرض التفاصيل ->",
        "news_link": "اقرا المزيد ->",
        "lang_label": "اختر اللغة",
        "news_section": "احدث المقالات",
    },
}


def escape(value: str) -> str:
    return html.escape(value or "", quote=True)


def resolve_list_image(src: str) -> str:
    path = (ROOT.parent / src.replace("../../", "")).resolve()
    if src.endswith(".webp"):
        small_path = path.with_name(path.stem + "_sm.webp")
        if small_path.exists():
            return src[:-5] + "_sm.webp"

    if src.endswith("logo.jpg"):
        logo_small = path.with_name("logo_sm.webp")
        if logo_small.exists():
            return src[:-8] + "logo_sm.webp"

    for suffix in (".png", ".jpg", ".jpeg"):
        if src.endswith(suffix):
            small_webp = path.with_name(path.stem + "_sm.webp")
            if small_webp.exists():
                return src[: -len(suffix)] + "_sm.webp"

    return src


def build_image(src: str, alt: str, *, eager: bool = False) -> str:
    src = resolve_list_image(src)
    attrs = [
        f'src="{escape(src)}"',
        f'alt="{escape(alt)}"',
        'width="440"',
        'height="220"',
        f'loading="{"eager" if eager else "lazy"}"',
        'decoding="async"',
    ]
    if eager:
        attrs.append('fetchpriority="high"')
    return "<img " + " ".join(attrs) + ">"


def add_lang_label_and_logo_size(page_html: str, lang_label: str) -> str:
    page_html = re.sub(
        r'<select id="langSwitcher" onchange="switchLanguage\(this.value\)">',
        (
            '<select id="langSwitcher" onchange="switchLanguage(this.value)" '
            f'aria-label="{escape(lang_label)}">'
        ),
        page_html,
    )
    page_html = re.sub(
        r'(<a href="index\.html" class="logo"><img[^>]*src="\.\./\.\./images/logo_sm\.webp"[^>]*?)(\s*/?>)',
        lambda match: (
            match.group(1)
            if 'width="' in match.group(1)
            else match.group(1) + ' width="88" height="88"'
        )
        + match.group(2),
        page_html,
    )
    return page_html


def update_hreflang_links(page_html: str, lang: str, page_name: str) -> str:
    replacements = {
        "en": f"https://wtscrews.com/pags/en/{page_name}",
        "zh-CN": f"https://wtscrews.com/pags/zh/{page_name}",
        "x-default": f"https://wtscrews.com/pags/{lang}/{page_name}",
    }
    for hreflang, href in replacements.items():
        page_html = re.sub(
            rf'<link rel="alternate" hreflang="{re.escape(hreflang)}" href="[^"]+">',
            f'<link rel="alternate" hreflang="{hreflang}" href="{href}">',
            page_html,
        )
    return page_html


def build_product_section(page_html: str, data: dict, lang_texts: dict) -> str:
    search_match = re.search(
        r'(\s*<div class="product-search-wrap">.*?</div>\s*)',
        page_html,
        re.S,
    )
    if not search_match:
        raise RuntimeError("Product search block not found")
    search_block = search_match.group(1).rstrip()

    groups = []
    product_index = 0

    for category in data.get("products", []):
        cards = []
        for item in category.get("items", []):
            product_index += 1
            eager = product_index <= 2
            cards.append(
                "\n".join(
                    [
                        f'            <a href="{escape(item.get("slug", ""))}.html" class="card">',
                        f'              <figure class="card-image">{build_image(item.get("icon", ""), item.get("title", ""), eager=eager)}</figure>',
                        '              <section class="card-body">',
                        f'                <h3>{html.escape(item.get("title", ""))}</h3>',
                        f'                <p>{html.escape(item.get("summary", ""))}</p>',
                        f'                <span class="card-link">{html.escape(lang_texts["product_link"])}</span>',
                        '              </section>',
                        '            </a>',
                    ]
                )
            )

        groups.append(
            "\n".join(
                [
                    f'          <h2 class="section-title category-heading">{html.escape(category.get("category", ""))}</h2>',
                    '          <section class="cards-grid">',
                    *cards,
                    '          </section>',
                ]
            )
        )

    new_section = "\n".join(
        [
            "    <!-- Products Listing -->",
            '    <section class="section">',
            '      <article class="container">',
            search_block,
            '        <section id="productsContainer">',
            *groups,
            '        </section>',
            '      </article>',
            '    </section>',
        ]
    )

    return re.sub(
        r"\s*<!-- Products Listing -->.*?<!-- CTA Section -->",
        "\n" + new_section + "\n\n    <!-- CTA Section -->",
        page_html,
        count=1,
        flags=re.S,
    )


def build_news_section(page_html: str, data: dict, lang_texts: dict) -> str:
    cards = []
    for index, item in enumerate(data.get("news", []), start=1):
        eager = index == 1
        cards.append(
            "\n".join(
                [
                    f'          <a href="{escape(item.get("slug", ""))}.html" class="card">',
                    f'            <figure class="card-image">{build_image(item.get("icon", ""), item.get("title", ""), eager=eager)}</figure>',
                    '            <section class="card-body">',
                    f'              <time class="card-meta" datetime="{escape(item.get("date", ""))}">{html.escape(item.get("date", ""))}</time>',
                    f'              <h3>{html.escape(item.get("title", ""))}</h3>',
                    f'              <p>{html.escape(item.get("summary", ""))}</p>',
                    f'              <span class="card-link">{html.escape(lang_texts["news_link"])}</span>',
                    '            </section>',
                    '          </a>',
                ]
            )
        )

    new_section = "\n".join(
        [
            "    <!-- News Listing -->",
            '    <section class="section">',
            '      <article class="container">',
            f'        <h2 class="sr-only">{html.escape(lang_texts["news_section"])}</h2>',
            '        <section class="cards-grid" id="newsContainer">',
            *cards,
            '        </section>',
            '      </article>',
            '    </section>',
        ]
    )

    return re.sub(
        r"\s*<!-- News Listing -->.*?</main>",
        "\n" + new_section + "\n  </main>",
        page_html,
        count=1,
        flags=re.S,
    )


def main() -> None:
    for json_path in sorted(ROOT.glob("*/pages_*.json")):
        lang = json_path.parent.name
        if lang not in TEXTS:
            continue

        lang_texts = TEXTS[lang]
        data = json.loads(json_path.read_text(encoding="utf-8"))

        products_path = json_path.parent / "products.html"
        products_html = products_path.read_text(encoding="utf-8")
        products_html = build_product_section(products_html, data, lang_texts)
        products_html = add_lang_label_and_logo_size(products_html, lang_texts["lang_label"])
        products_html = update_hreflang_links(products_html, lang, "products.html")
        products_path.write_text(products_html, encoding="utf-8")

        news_path = json_path.parent / "news.html"
        news_html = news_path.read_text(encoding="utf-8")
        news_html = build_news_section(news_html, data, lang_texts)
        news_html = add_lang_label_and_logo_size(news_html, lang_texts["lang_label"])
        news_html = update_hreflang_links(news_html, lang, "news.html")
        news_path.write_text(news_html, encoding="utf-8")

    print("Rendered static list markup for all language news/products pages.")


if __name__ == "__main__":
    main()
