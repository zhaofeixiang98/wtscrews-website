<?php
// article-save.php — Generate article HTML files and update news JSON for all languages
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    exit(json_encode(['error' => 'Method not allowed']));
}

$base = realpath(__DIR__ . '/..');

// ── Input validation ─────────────────────────────────────────────────────────
$slug = preg_replace('/[^a-z0-9\-]/', '-', strtolower(trim($_POST['slug'] ?? '')));
$slug = trim(preg_replace('/-+/', '-', $slug), '-');
$date = trim($_POST['date'] ?? date('Y-m-d'));

if (empty($slug)) {
    exit(json_encode(['error' => 'Slug (URL 标识) 不能为空']));
}
if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $date)) {
    exit(json_encode(['error' => '日期格式错误，请使用 YYYY-MM-DD']));
}

$en_title      = trim($_POST['en_title']    ?? '');
$en_subtitle   = trim($_POST['en_subtitle'] ?? '');
$en_summary    = trim($_POST['en_summary']  ?? '');
$en_meta_desc  = trim($_POST['en_meta_desc'] ?? '') ?: $en_summary;
$en_keywords   = trim($_POST['en_keywords'] ?? '');
$en_bc_label   = trim($_POST['en_bc_label'] ?? '') ?: $en_title;
$en_body       = trim($_POST['en_body']     ?? '');
$extra_head    = trim($_POST['extra_head']  ?? '');

if (empty($en_title) || empty($en_body)) {
    exit(json_encode(['error' => '英文标题和正文内容为必填项']));
}

// ── Per-language config ───────────────────────────────────────────────────────
$langs = ['en', 'ar', 'de', 'es', 'fr', 'id', 'ja', 'ko', 'zh'];

$html_lang = ['en'=>'en','ar'=>'ar','de'=>'de','es'=>'es','fr'=>'fr','id'=>'id','ja'=>'ja','ko'=>'ko','zh'=>'zh'];
$hreflang  = ['en'=>'en','ar'=>'ar','de'=>'de','es'=>'es','fr'=>'fr','id'=>'id','ja'=>'ja','ko'=>'ko','zh'=>'zh-CN'];
$rtl_langs = ['ar'];

$nav = [
    'en' => ['Home','Products','News','About','Contact'],
    'zh' => ['首页','产品','新闻','关于','联系'],
    'de' => ['Startseite','Produkte','Nachrichten','Über Uns','Kontakt'],
    'es' => ['Inicio','Productos','Noticias','Sobre Nosotros','Contacto'],
    'fr' => ['Accueil','Produits','Actualités','À propos','Contact'],
    'ar' => ['الرئيسية','المنتجات','الأخبار','عن الشركة','تواصل معنا'],
    'id' => ['Beranda','Produk','Berita','Tentang Kami','Kontak'],
    'ja' => ['ホーム','製品','ニュース','会社情報','お問い合わせ'],
    'ko' => ['홈','제품','뉴스','회사 소개','문의'],
];
$bc_home  = ['en'=>'Home','zh'=>'首页','de'=>'Startseite','es'=>'Inicio','fr'=>'Accueil','ar'=>'الرئيسية','id'=>'Beranda','ja'=>'ホーム','ko'=>'홈'];
$bc_news  = ['en'=>'News','zh'=>'新闻','de'=>'Nachrichten','es'=>'Noticias','fr'=>'Actualités','ar'=>'الأخبار','id'=>'Berita','ja'=>'ニュース','ko'=>'뉴스'];

$rec_products_label = ['en'=>'Recommended Products','zh'=>'推荐产品','de'=>'Empfohlene Produkte','es'=>'Productos Recomendados','fr'=>'Produits Recommandés','ar'=>'المنتجات الموصى بها','id'=>'Produk yang Direkomendasikan','ja'=>'おすすめ製品','ko'=>'추천 제품'];
$view_details       = ['en'=>'View Details →','zh'=>'查看详情 →','de'=>'Details ansehen →','es'=>'Ver Detalles →','fr'=>'Voir les Détails →','ar'=>'← عرض التفاصيل','id'=>'Lihat Detail →','ja'=>'詳細を見る →','ko'=>'자세히 보기 →'];

// Footer texts
$ft_brand_desc = [
    'en' => 'Professional fastener manufacturer and exporter since 2005. Delivering quality bolts, screws, washers, and custom fasteners to customers worldwide.',
    'zh' => '自2005年以来的专业紧固件制造商和出口商。为全球客户提供优质螺栓、螺钉、垫圈和定制紧固件。',
    'de' => 'Professioneller Hersteller und Exporteur von Verbindungselementen seit 2005. Qualitätsprodukte für Kunden weltweit.',
    'es' => 'Fabricante y exportador profesional de sujetadores desde 2005. Calidad garantizada para clientes de todo el mundo.',
    'fr' => 'Fabricant et exportateur professionnel de fixations depuis 2005. Des produits de qualité pour des clients du monde entier.',
    'ar' => 'مصنّع ومُصدِّر متخصص لمنتجات التثبيت منذ عام 2005. جودة عالية لعملاء حول العالم.',
    'id' => 'Produsen dan eksportir pengencang profesional sejak 2005. Kualitas terjamin untuk pelanggan di seluruh dunia.',
    'ja' => '2005年より専門的なファスナーメーカー・輸出業者として活動しています。世界中のお客様に高品質な製品をお届けします。',
    'ko' => '2005년부터 전문 파스너 제조사 및 수출업체입니다. 전 세계 고객에게 고품질 제품을 제공합니다.',
];
$ft_quicklinks = ['en'=>'Quick Links','zh'=>'快速链接','de'=>'Schnell Links','es'=>'Accesos Rápidos','fr'=>'Liens Rapides','ar'=>'روابط سريعة','id'=>'Tautan Cepat','ja'=>'クイックリンク','ko'=>'빠른 링크'];
$ft_about      = ['en'=>'About Us','zh'=>'关于我们','de'=>'Über Uns','es'=>'Sobre Nosotros','fr'=>'À Propos','ar'=>'عن الشركة','id'=>'Tentang Kami','ja'=>'会社情報','ko'=>'회사 소개'];
$ft_contact_h  = ['en'=>'Contact Us','zh'=>'联系我们','de'=>'Kontaktieren Sie Uns','es'=>'Contáctenos','fr'=>'Nous contacter','ar'=>'تواصل معنا','id'=>'Hubungi Kami','ja'=>'お問い合わせ','ko'=>'문의하기'];
$ft_email_lbl  = ['en'=>'Email','zh'=>'电子邮箱','de'=>'E-Mail','es'=>'Correo','fr'=>'E-mail','ar'=>'البريد الإلكتروني','id'=>'Email','ja'=>'メール','ko'=>'이메일'];
$ft_phone_lbl  = ['en'=>'Phone','zh'=>'电话','de'=>'Telefon','es'=>'Teléfono','fr'=>'Tél','ar'=>'الهاتف','id'=>'Telepon','ja'=>'電話','ko'=>'전화'];
$ft_addr_lbl   = ['en'=>'Address','zh'=>'地址','de'=>'Adresse','es'=>'Dirección','fr'=>'Adresse','ar'=>'العنوان','id'=>'Alamat','ja'=>'住所','ko'=>'주소'];
$ft_addr_val   = ['en'=>'Yongnian District, Handan, Hebei, China','zh'=>'中国河北邯郸永年区','de'=>'Yongnian District, Handan, Hebei, China','es'=>'Yongnian District, Handan, Hebei, China','fr'=>'Yongnian District, Handan, Hebei, China','ar'=>'منطقة يونغنيان، هاندان، خبي، الصين','id'=>'Yongnian District, Handan, Hebei, China','ja'=>'中国河北省邯鄲市永年区','ko'=>'중국 허베이성 한단시 용녠구'];
$ft_copyright  = ['en'=>'All Rights Reserved.','zh'=>'保留所有权利.','de'=>'Alle Rechte vorbehalten.','es'=>'Todos los derechos reservados.','fr'=>'Tous droits réservés.','ar'=>'جميع الحقوق محفوظة.','id'=>'Semua Hak Dilindungi.','ja'=>'All Rights Reserved.','ko'=>'모든 권리 보유.'];
$ft_privacy    = ['en'=>'Privacy Policy','zh'=>'隐私政策','de'=>'Datenschutzrichtlinie','es'=>'Política de Privacidad','fr'=>'Politique de Confidentialité','ar'=>'سياسة الخصوصية','id'=>'Kebijakan Privasi','ja'=>'プライバシーポリシー','ko'=>'개인정보 처리방침'];
$ft_products = [
    'en' => ['Hex Bolts','Flange Bolts','Anchor Bolts','Standard Flat Washers','Custom Washers'],
    'zh' => ['六角螺栓','法兰螺栓','地脚螺栓','标准平垫圈','定制垫圈'],
    'de' => ['Hex Bolts','Flange Bolts','Anchor Bolts','Standard Flat Washers','Custom Washers'],
    'es' => ['Tornillos Hexagonales','Tornillos de Brida','Pernos de Anclaje','Arandelas Planas','Arandelas Personalizadas'],
    'fr' => ['Boulons Hexagonaux','Boulons à Bride','Boulons d\'Ancrage','Rondelles Plates','Rondelles Personnalisées'],
    'ar' => ['مسامير سداسية','مسامير الشفة','مسامير التثبيت','غسالات مسطحة','غسالات مخصصة'],
    'id' => ['Baut Hex','Baut Flange','Baut Jangkar','Cincin Datar Standar','Cincin Kustom'],
    'ja' => ['六角ボルト','フランジボルト','アンカーボルト','平座金','カスタム座金'],
    'ko' => ['육각 볼트','플랜지 볼트','앵커 볼트','평 와셔','커스텀 와셔'],
];

// FAQ per language
$faq_data = [
    'zh' => [
        'heading' => '常见问题',
        'close_label' => '关闭弹窗',
        'still_q' => '还有其他问题？',
        'contact_btn' => '联系我们',
        'items' => [
            ['最小起订量是多少？', '我们的标准最小起订量为每种产品10公斤。定制订单的起订量根据规格有所不同，欢迎咨询。'],
            ['生产周期需要多久？', '标准产品：7-15个工作日。定制订单：根据复杂程度和数量，15-25个工作日。'],
            ['大批量订单前可以提供样品吗？', '可以。我们为标准产品提供免费样品（运费由客户承担）。定制零件可能收取少量样品费。'],
            ['你们接受哪些付款方式？', '电汇（银行转账）、信用证、西联汇款，小额订单支持PayPal。通常要求预付30%定金，余款发货前付清。'],
            ['你们提供OEM/定制生产服务吗？', '当然可以。发送您的图纸或规格，我们将在24小时内为您提供报价。'],
        ],
    ],
    '_default' => [
        'heading' => 'Frequently Asked Questions',
        'close_label' => 'Close FAQ',
        'still_q' => 'Still have questions?',
        'contact_btn' => 'Contact Us',
        'items' => [
            ['What is the minimum order quantity?', 'Our standard MOQ is 10 kg per item. For custom orders, the MOQ may vary depending on specifications — feel free to ask.'],
            ['How long does production take?', 'Standard products: 7–15 business days. Custom orders: 15–25 business days depending on complexity and quantity.'],
            ['Can you send samples before I place a bulk order?', 'Yes. We provide free samples for standard items (you cover shipping). For custom parts, a small sample fee may apply.'],
            ['What payment methods do you accept?', 'T/T (bank transfer), L/C, Western Union, and PayPal for small orders. We typically ask for 30% deposit with balance before shipment.'],
            ['Do you offer OEM / custom manufacturing?', 'Absolutely. Send us your drawings or specifications and we will provide a quote within 24 hours.'],
        ],
    ],
];

// ── Date formatting ───────────────────────────────────────────────────────────
function formatArticleDate(string $d, string $lang): string {
    [$y, $m, $day] = explode('-', $d);
    $y = (int)$y; $m = (int)$m; $day = (int)$day;
    $months_en = ['January','February','March','April','May','June','July','August','September','October','November','December'];
    switch ($lang) {
        case 'en': return "Published on {$months_en[$m-1]} {$day}, {$y}";
        case 'zh': return "发布于 {$y}年{$m}月{$day}日";
        case 'ja': return "公開日：{$y}年{$m}月{$day}日";
        case 'ko': return "게시일: {$y}년 {$m}월 {$day}일";
        case 'ar': return "نُشر في: {$day}/{$m}/{$y}";
        default:   return "Published: {$d}";
    }
}

function buildHeadExtra(string $extraHead): string {
  $snippet = trim($extraHead);
  if ($snippet === '') {
    return '';
  }
  return "\n  <!-- Custom Head Snippet -->\n{$snippet}\n  <!-- End Custom Head Snippet -->";
}

// ── HTML generator ────────────────────────────────────────────────────────────
function buildArticleHtml(
    string $lang, string $slug, string $date,
    string $title, string $subtitle, string $meta_desc, string $keywords, string $bc_label, string $body,
  string $extra_head,
    array $config
): string {
    extract($config);
    $dir_attr = in_array($lang, $rtl_langs) ? ' dir="rtl"' : '';
    $n = $nav[$lang];
    $faq = $faq_data[$lang] ?? $faq_data['_default'];
    $fp = $ft_products[$lang] ?? $ft_products['en'];
    $published = formatArticleDate($date, $lang);

    // Build hreflang links
    $hreflang_links = '';
    foreach ($hreflang as $l => $hl) {
        $hreflang_links .= "  <link rel=\"alternate\" hreflang=\"{$hl}\" href=\"/pags/{$l}/news/{$slug}.html\">\n";
    }
    $hreflang_links .= "  <link rel=\"alternate\" hreflang=\"x-default\" href=\"/pags/en/news/{$slug}.html\">\n";

    // Build FAQ items
    $faq_items_html = '';
    foreach ($faq['items'] as [$q, $a]) {
        $faq_items_html .= "      <article class=\"faq-item\">\n";
        $faq_items_html .= "        <h3 class=\"faq-question\">" . htmlspecialchars($q) . "</h3>\n";
        $faq_items_html .= "        <p class=\"faq-answer\">" . htmlspecialchars($a) . "</p>\n";
        $faq_items_html .= "      </article>\n";
    }

    $hl  = $html_lang[$lang];
    $ql  = $ft_quicklinks[$lang];
    $abu = $ft_about[$lang];
    $ch  = $ft_contact_h[$lang];
    $el  = $ft_email_lbl[$lang];
    $pl  = $ft_phone_lbl[$lang];
    $al  = $ft_addr_lbl[$lang];
    $av  = $ft_addr_val[$lang];
    $cp  = $ft_copyright[$lang];
    $priv= $ft_privacy[$lang];
    $rp  = $rec_products_label[$lang];
    $vd  = $view_details[$lang];
    $bch = $bc_home[$lang];
    $bcn = $bc_news[$lang];
    $bd  = $ft_brand_desc[$lang];
    $ptitle = $nav[$lang][1]; // "Products" label for footer column heading
    // year for copyright
    $copy_year = substr($date, 0, 4) >= 2026 ? 2026 : 2026;
    $page_url = "https://wtscrews.com/pags/{$lang}/news/{$slug}.html";
    $head_extra_block = buildHeadExtra($extra_head);

    $html = <<<HTML
<!DOCTYPE html>
<html lang="{$hl}"{$dir_attr}>
<head>
{$hreflang_links}  <meta charset="UTF-8">
  <link rel="icon" type="image/x-icon" href="../../../favicon.ico">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{$title} — WT Fasteners</title>
  <meta name="description" content="{$meta_desc}">
  <meta name="keywords" content="{$keywords}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{$page_url}">
  <link rel="sitemap" type="application/xml" href="../../../sitemap.xml">
  <!-- Geo Tags -->
  <meta name="geo.region" content="CN">
  <meta name="geo.placename" content="China">
  <meta name="geo.position" content="30.2741;120.1551">
  <meta name="ICBM" content="30.2741, 120.1551">
  <!-- Open Graph -->
  <meta property="og:title" content="{$title} — WT Fasteners">
  <meta property="og:description" content="{$meta_desc}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{$page_url}">
  <meta property="og:image" content="../../../images/og-cover.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <!-- Structured Data -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "{$title}",
    "description": "{$meta_desc}",
    "datePublished": "{$date}T08:00:00+08:00",
    "dateModified": "{$date}T08:00:00+08:00",
    "author": {
      "@type": "Organization",
      "name": "WT Fasteners",
      "url": "https://wtscrews.com"
    },
    "publisher": {
      "@type": "Organization",
      "name": "WT Fasteners",
      "logo": {
        "@type": "ImageObject",
        "url": "https://wtscrews.com/images/logo.jpg"
      }
    },
    "mainEntityOfPage": {
      "@type": "WebPage",
      "@id": "{$page_url}"
    }
  }
  </script>{$head_extra_block}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../../css/style.css">
  <!-- Facebook Meta Pixel Code -->
  <script>
  !function(f,b,e,v,n,t,s)
  {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
  n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t,s)}(window, document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', '1626729111828175');
  fbq('track', 'PageView');
  </script>
  <noscript><img height="1" width="1" style="display:none"
  src="https://www.facebook.com/tr?id=1626729111828175&ev=PageView&noscript=1"
  /></noscript>
  <!-- End Meta Pixel Code -->
</head>
<body>

  <!-- Header -->
  <header class="site-header" id="siteHeader">
    <nav class="container nav">
      <a href="../index.html" class="logo"><img src="../../../images/logo.jpg" alt="Hebei Wangtu Metal Co., Ltd."></a>
      <button class="menu-toggle" id="menuToggle" aria-label="Toggle navigation menu">
        <span></span><span></span><span></span>
      </button>
      <ul class="nav-links" id="navLinks">
        <li><a href="../index.html">{$n[0]}</a></li>
        <li><a href="../products.html">{$n[1]}</a></li>
        <li><a href="../news.html">{$n[2]}</a></li>
        <li><a href="../about.html">{$n[3]}</a></li>
        <li><a href="../contact.html">{$n[4]}</a></li>
      </ul>
      <div class="lang-select">
        <select id="langSwitcher" onchange="switchLanguage(this.value)">


        </select>
      </div>
    </nav>
  </header>

  <main>
    <!-- Page Header -->
    <section class="page-header">
      <article class="container">
        <h1>{$title}</h1>
        <p>{$subtitle}</p>
      </article>
    </section>

    <!-- Breadcrumb -->
    <nav class="breadcrumb">
      <article class="container">
        <a href="../index.html">{$bch}</a>
        <span>/</span>
        <a href="../news.html">{$bcn}</a>
        <span>/</span>
        {$bc_label}
      </article>
    </nav>

    <!-- Article Content -->
    <section class="section">
      <article class="container article-content">
        <time class="article-meta" datetime="{$date}">{$published}</time>
        {$body}
      </article>
    </section>

    <!-- Related Products -->
    <section class="section">
      <article class="container">
        <div class="related-products">
          <h3>{$rp}</h3>
          <div class="related-grid">
        <a href="../products/hex-bolts.html" class="related-card">
          <div class="related-card-image">
            <img src="../../../images/products/bolts/Hex Bolt0.webp" alt="{$fp[0]}" loading="lazy" style="width:100%;height:100%;object-fit:cover;">
          </div>
          <div class="related-card-body">
            <h4>{$fp[0]}</h4>
            <p>Full and partial thread hex bolts in DIN 931/933, ISO 4014/4017. Grades 4.8 to 12.9, sizes M4–M64.</p>
            <span class="related-card-link">{$vd}</span>
          </div>
        </a>
        <a href="../products/hex-nuts.html" class="related-card">
          <div class="related-card-image">
            <img src="../../../images/products/nuts/Hex Nut1.webp" alt="Hex Nuts" loading="lazy" style="width:100%;height:100%;object-fit:cover;">
          </div>
          <div class="related-card-body">
            <h4>Hex Nuts</h4>
            <p>Standard hex nuts per DIN 934 / ISO 4032. Sizes M4–M64, grades 4, 6, 8, 10.</p>
            <span class="related-card-link">{$vd}</span>
          </div>
        </a>
        <a href="../products/flat-washers.html" class="related-card">
          <div class="related-card-image">
            <img src="../../../images/products/washers/Flat Washer4.webp" alt="Flat Washers" loading="lazy" style="width:100%;height:100%;object-fit:cover;">
          </div>
          <div class="related-card-body">
            <h4>Flat Washers</h4>
            <p>Standard flat washers per DIN 125 / ISO 7089. Zinc plated, galvanized, or plain finish.</p>
            <span class="related-card-link">{$vd}</span>
          </div>
        </a>
          </div>
        </div>
      </article>
    </section>

  </main>

  <!-- Footer -->
  <footer class="site-footer">
    <section class="container footer-grid">
      <article class="footer-col">
        <h3>WT Fasteners</h3>
        <p>{$bd}</p>
      </article>
      <article class="footer-col">
        <h3>{$ql}</h3>
        <ul>
          <li><a href="../index.html">{$n[0]}</a></li>
          <li><a href="../products.html">{$n[1]}</a></li>
          <li><a href="../news.html">{$n[2]}</a></li>
          <li><a href="../about.html">{$abu}</a></li>
          <li><a href="../contact.html">{$n[4]}</a></li>
        </ul>
      </article>
      <article class="footer-col">
        <h3>{$ptitle}</h3>
        <ul>
          <li><a href="../products/hex-bolts.html">{$fp[0]}</a></li>
          <li><a href="../products/flange-bolts.html">{$fp[1]}</a></li>
          <li><a href="../products/anchor-bolts.html">{$fp[2]}</a></li>
          <li><a href="../products/flat-washers.html">{$fp[3]}</a></li>
          <li><a href="../products/lock-washers.html">{$fp[4]}</a></li>
        </ul>
      </article>
      <article class="footer-col">
        <h3>{$ch}</h3>
        <p>{$el}: info@wtbolts.com</p>
        <p>{$el}: lipbolts@gmail.com</p>
        <p>{$pl}: +8615175432812</p>
        <p>{$al}: {$av}</p>
      </article>
    </section>
    <section class="footer-bottom">
      <p class="container">&copy; {$copy_year} WT Fasteners. {$cp} &nbsp;|&nbsp; <a href="../privacy-policy.html">{$priv}</a></p>
    </section>
  </footer>

  <!-- FAQ Modal -->
  <aside class="faq-overlay" id="faqOverlay">
    <section class="faq-modal">
      <header class="faq-modal-header">
        <h2>{$faq['heading']}</h2>
        <button class="faq-close" aria-label="{$faq['close_label']}">&times;</button>
      </header>
{$faq_items_html}      <footer class="faq-cta">
        <p>{$faq['still_q']}</p>
        <a href="../contact.html" class="btn btn-primary">{$faq['contact_btn']}</a>
      </footer>
    </section>
  </aside>

  <script src="../../../js/i18n-config.js"></script>
  <script src="../../../js/main.js"></script>
  <script src="../../../js/chat-dock.js"></script>
</body>
</html>
HTML;
    return $html;
}

// ── Main loop: generate and save ──────────────────────────────────────────────
$config = compact(
    'html_lang','hreflang','rtl_langs','nav','bc_home','bc_news',
    'rec_products_label','view_details','ft_brand_desc','ft_quicklinks',
    'ft_about','ft_contact_h','ft_email_lbl','ft_phone_lbl','ft_addr_lbl',
    'ft_addr_val','ft_copyright','ft_privacy','ft_products','faq_data'
);

$errors  = [];
$created = [];

foreach ($langs as $lang) {
    $title     = trim($_POST["{$lang}_title"]    ?? '') ?: $en_title;
    $subtitle  = trim($_POST["{$lang}_subtitle"] ?? '') ?: $en_subtitle;
    $summary   = trim($_POST["{$lang}_summary"]  ?? '') ?: $en_summary;
    $meta_desc = trim($_POST["{$lang}_meta_desc"]?? '') ?: $en_meta_desc;
    $keywords  = trim($_POST["{$lang}_keywords"] ?? '') ?: $en_keywords;
    $bc_label  = trim($_POST["{$lang}_bc_label"] ?? '') ?: $en_bc_label;
    $body      = trim($_POST["{$lang}_body"]     ?? '') ?: $en_body;

    // Write HTML
    $news_dir = $base . '/pags/' . $lang . '/news';
    if (!is_dir($news_dir)) {
        mkdir($news_dir, 0755, true);
    }
    $html_path = $news_dir . '/' . $slug . '.html';
    $html_content = buildArticleHtml($lang, $slug, $date, $title, $subtitle, $meta_desc, $keywords, $bc_label, $body, $extra_head, $config);
    if (file_put_contents($html_path, $html_content) === false) {
        $errors[] = "无法写入文件: pags/{$lang}/news/{$slug}.html";
        continue;
    }

    // Update JSON
    $json_path = $base . '/pags/' . $lang . '/pages_' . $lang . '.json';
    if (!file_exists($json_path)) {
        $errors[] = "找不到 JSON 文件: pags/{$lang}/pages_{$lang}.json";
        continue;
    }
    $json_data = json_decode(file_get_contents($json_path), true);
    if (!isset($json_data['news'])) {
        $json_data['news'] = [];
    }
    // Remove existing entry with same slug
    $target_slug = 'news/' . $slug;
    $json_data['news'] = array_values(array_filter($json_data['news'], function($n) use ($target_slug) {
        return ($n['slug'] ?? '') !== $target_slug;
    }));
    // Prepend new entry
    array_unshift($json_data['news'], [
        'slug'    => 'news/' . $slug,
        'title'   => $title,
        'date'    => $date,
        'summary' => $summary,
        'icon'    => '../../images/logo.jpg',
    ]);
    if (file_put_contents($json_path, json_encode($json_data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)) === false) {
        $errors[] = "无法写入 JSON: pags/{$lang}/pages_{$lang}.json";
        continue;
    }

    $created[] = $lang;
}

if (!empty($errors)) {
    echo json_encode(['success' => false, 'errors' => $errors, 'created' => $created]);
} else {
    echo json_encode(['success' => true, 'slug' => $slug, 'created' => $created, 'url' => "/pags/en/news/{$slug}.html"]);
}
