(function () {
  'use strict';

  /* ===== Mobile Menu Toggle ===== */
  var menuToggle = document.getElementById('menuToggle');
  var navLinks = document.getElementById('navLinks');

  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', function () {
      navLinks.classList.toggle('open');
      menuToggle.classList.toggle('active');
    });

    /* Close menu when a link is clicked */
    navLinks.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        navLinks.classList.remove('open');
        menuToggle.classList.remove('active');
      });
    });
  }

  /* ===== Header Scroll Effect ===== */
  var header = document.getElementById('siteHeader');
  if (header) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 50) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
    }, { passive: true });
  }

  /* ===== Active Navigation Link ===== */
  var currentPage = window.location.pathname.split('/').pop() || 'index.html';
  var allNavLinks = document.querySelectorAll('.nav-links a');

  allNavLinks.forEach(function (link) {
    var linkPage = link.getAttribute('href').split('/').pop();
    if (linkPage === currentPage) {
      link.classList.add('active');
    }
    if (currentPage.indexOf('product-') === 0 && linkPage === 'products.html') {
      link.classList.add('active');
    }
    if ((currentPage.indexOf('bolt') !== -1 || currentPage.indexOf('washer') !== -1) && linkPage === 'products.html') {
      link.classList.add('active');
    }
    if (currentPage.indexOf('new-') === 0 && linkPage === 'news.html') {
      link.classList.add('active');
    }
  });

  function detectLangFromPath(path) {
    return path.indexOf('/zh/') !== -1 ? 'zh'
         : path.indexOf('/id/') !== -1 ? 'id'
         : path.indexOf('/fr/') !== -1 ? 'fr'
         : path.indexOf('/de/') !== -1 ? 'de'
         : path.indexOf('/es/') !== -1 ? 'es'
         : path.indexOf('/ja/') !== -1 ? 'ja'
         : path.indexOf('/ko/') !== -1 ? 'ko'
         : path.indexOf('/ar/') !== -1 ? 'ar'
         : 'en';
  }

  function getPrivacyPolicyPath() {
    var path = window.location.pathname;
    var lang = detectLangFromPath(path);
    var langRoot = '/pags/' + lang + '/';
    var langRootIndex = path.indexOf(langRoot);

    if (langRootIndex !== -1) {
      return path.slice(0, langRootIndex + langRoot.length) + 'privacy-policy.html';
    }

    return langRoot + 'privacy-policy.html';
  }

  function getPagesJsonInfo() {
    var path = window.location.pathname;
    var lang = detectLangFromPath(path);
    var inSubdir = path.indexOf('/products/') !== -1 || path.indexOf('/news/') !== -1;
    return {
      lang: lang,
      pagesJsonPath: (inSubdir ? '../' : './') + 'pages_' + lang + '.json'
    };
  }

  function resolveAssetUrl(assetPath, jsonBaseUrl) {
    try {
      return new URL(assetPath, jsonBaseUrl).href;
    } catch (err) {
      return assetPath;
    }
  }

  function getPrimaryImage(item) {
    if (!item) {
      return '';
    }
    if (item.icon) {
      return item.icon;
    }
    if (item.detailImage) {
      return item.detailImage;
    }
    if (item.articleImages && item.articleImages.length > 0) {
      return item.articleImages[0];
    }
    if (item.galleryImages && item.galleryImages.length > 0) {
      return item.galleryImages[0];
    }
    return '';
  }

  var pagesDataPromise = null;

  function fetchPagesData() {
    if (pagesDataPromise) {
      return pagesDataPromise;
    }

    var info = getPagesJsonInfo();
    var jsonBaseUrl = new URL(info.pagesJsonPath, window.location.href).href;

    pagesDataPromise = fetch(info.pagesJsonPath)
      .then(function (res) {
        if (!res.ok && info.lang !== 'en') {
          var fallbackPath = (window.location.pathname.indexOf('/products/') !== -1 || window.location.pathname.indexOf('/news/') !== -1 ? '../' : './') + 'pages_en.json';
          var fallbackBaseUrl = new URL(fallbackPath, window.location.href).href;
          return fetch(fallbackPath).then(function (fallbackRes) {
            if (!fallbackRes.ok) {
              throw new Error('Fallback also failed');
            }
            return fallbackRes.json().then(function (data) {
              return { data: data, jsonBaseUrl: fallbackBaseUrl };
            });
          });
        }
        return res.json().then(function (data) {
          return { data: data, jsonBaseUrl: jsonBaseUrl };
        });
      });

    return pagesDataPromise;
  }

  function getCurrentDetailSlug() {
    var match = window.location.pathname.match(/\/(news|products)\/([^/]+)\.html$/);
    if (!match) {
      return '';
    }
    return match[1] + '/' + match[2];
  }

  function findProductItemBySlug(data, slug) {
    var categories = data.products || [];
    for (var i = 0; i < categories.length; i++) {
      var items = categories[i].items || [];
      for (var j = 0; j < items.length; j++) {
        if (items[j].slug === slug) {
          return items[j];
        }
      }
    }
    return null;
  }

  function applyProductDetailImage(item, jsonBaseUrl) {
    var imagePath = item.detailImage || getPrimaryImage(item);
    var galleryImage = document.querySelector('.product-gallery img');
    if (!imagePath || !galleryImage) {
      return;
    }
    galleryImage.src = resolveAssetUrl(imagePath, jsonBaseUrl);
    galleryImage.alt = item.title || galleryImage.alt;
  }

  function applyNewsDetailImages(item, jsonBaseUrl) {
    var imagePaths = item.articleImages && item.articleImages.length > 0
      ? item.articleImages
      : (getPrimaryImage(item) ? [getPrimaryImage(item)] : []);
    if (imagePaths.length === 0) {
      return;
    }

    var figureImages = document.querySelectorAll('.article-figure img');
    if (figureImages.length === 0) {
      return;
    }

    figureImages.forEach(function (img, index) {
      var imagePath = imagePaths[index] || imagePaths[0];
      if (!imagePath) {
        return;
      }
      img.src = resolveAssetUrl(imagePath, jsonBaseUrl);
      img.alt = item.title || img.alt;
    });
  }

  function applyDetailPageAssets() {
    var slug = getCurrentDetailSlug();
    if (!slug) {
      return;
    }

    fetchPagesData()
      .then(function (result) {
        var item = null;
        if (slug.indexOf('products/') === 0) {
          item = findProductItemBySlug(result.data, slug);
          if (item) {
            applyProductDetailImage(item, result.jsonBaseUrl);
          }
          return;
        }

        if (slug.indexOf('news/') === 0) {
          item = (result.data.news || []).find(function (newsItem) {
            return newsItem.slug === slug;
          });
          if (item) {
            applyNewsDetailImages(item, result.jsonBaseUrl);
          }
        }
      })
      .catch(function () {
        /* Keep the static HTML image as fallback if JSON loading fails. */
      });
  }

  /* ===== Scroll Fade-In Animation ===== */
  var fadeElements = document.querySelectorAll('.fade-in');
  if (fadeElements.length > 0) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.1 }
    );

    fadeElements.forEach(function (el) {
      observer.observe(el);
    });
  }

  /* ===== Auto-Load Pages (News / Products) ===== */
  var newsContainer = document.getElementById('newsContainer');
  var newsCount = document.getElementById('newsCount');
  if (newsContainer) {
    loadPages('news', newsContainer, newsCount);
  }

  var productsContainer = document.getElementById('productsContainer');
  var productsCount = document.getElementById('productsCount');
  if (productsContainer) {
    loadCategorizedProducts(productsContainer, productsCount);
  }

  applyDetailPageAssets();

  function loadCategorizedProducts(container, countEl) {
    fetchPagesData()
      .then(function (result) {
        var data = result.data;
        var categories = data.products || [];
        var totalItems = 0;
        categories.forEach(function (cat) { totalItems += (cat.items || []).length; });

        if (countEl) {
          countEl.textContent = totalItems + ' products across ' + categories.length + ' categories';
        }

        while (container.firstChild) {
          container.removeChild(container.firstChild);
        }

        var cardIndex = 0;
        categories.forEach(function (cat) {
          /* Category heading */
          var heading = document.createElement('h2');
          heading.className = 'section-title category-heading';
          heading.textContent = cat.category;
          container.appendChild(heading);

          /* Cards grid for this category */
          var grid = document.createElement('section');
          grid.className = 'cards-grid';

          (cat.items || []).forEach(function (item) {
            var idx = cardIndex++;
            var card = document.createElement('a');
            card.href = item.slug + '.html';
            card.className = 'card fade-in';

            // Use IntersectionObserver instead of setTimeout to avoid forced reflow
            if (typeof IntersectionObserver !== 'undefined') {
              var cardObserver = new IntersectionObserver(function(entries, obs) {
                entries.forEach(function(entry) {
                  if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    obs.unobserve(entry.target);
                  }
                });
              }, { threshold: 0.05 });
              cardObserver.observe(card);
            } else {
              card.classList.add('visible');
            }

            var imageWrap = document.createElement('figure');
            imageWrap.className = 'card-image';
            if (getPrimaryImage(item)) {
              var img = document.createElement('img');
              img.src = resolveAssetUrl(getPrimaryImage(item), result.jsonBaseUrl);
              img.alt = item.title;
              img.loading = 'lazy';
              imageWrap.appendChild(img);
            } else {
              imageWrap.textContent = item.icon || '\u2699';
            }
            card.appendChild(imageWrap);

            var body = document.createElement('section');
            body.className = 'card-body';

            var title = document.createElement('h3');
            title.textContent = item.title;
            body.appendChild(title);

            var summary = document.createElement('p');
            summary.textContent = item.summary;
            body.appendChild(summary);

            var linkText = document.createElement('span');
            linkText.className = 'card-link';
            linkText.textContent = 'View Details \u2192';
            body.appendChild(linkText);

            card.appendChild(body);
            grid.appendChild(card);
          });

          container.appendChild(grid);
        });

        /* ===== Real-time search ===== */
        var searchInput = document.getElementById('productSearch');
        if (searchInput) {
          var noResultsEl = null;

          searchInput.addEventListener('input', function () {
            var query = this.value.trim().toLowerCase();
            var headings = container.querySelectorAll('.category-heading');
            var grids = container.querySelectorAll('.cards-grid');

            headings.forEach(function (heading, i) {
              var grid = grids[i];
              if (!grid) return;
              var cards = grid.querySelectorAll('.card');
              var visibleCount = 0;

              cards.forEach(function (card) {
                var titleEl = card.querySelector('h3');
                var summaryEl = card.querySelector('p');
                var text = (
                  (titleEl ? titleEl.textContent : '') + ' ' +
                  (summaryEl ? summaryEl.textContent : '')
                ).toLowerCase();
                var matches = !query || text.indexOf(query) !== -1;
                card.style.display = matches ? '' : 'none';
                if (matches) visibleCount++;
              });

              var show = !query || visibleCount > 0;
              heading.style.display = show ? '' : 'none';
              grid.style.display = show ? '' : 'none';
            });

            /* No-results message */
            var anyVisible = Array.prototype.some.call(
              container.querySelectorAll('.card'),
              function (c) { return c.style.display !== 'none'; }
            );

            if (!anyVisible && query) {
              if (!noResultsEl) {
                noResultsEl = document.createElement('p');
                noResultsEl.className = 'search-no-results';
                container.appendChild(noResultsEl);
              }
              var noResultsText = searchInput.getAttribute('data-no-results') || 'No products found.';
              noResultsEl.textContent = noResultsText;
              noResultsEl.style.display = '';
            } else if (noResultsEl) {
              noResultsEl.style.display = 'none';
            }
          });
        }
      })
      .catch(function () {
        while (container.firstChild) { container.removeChild(container.firstChild); }
        var errMsg = document.createElement('p');
        errMsg.className = 'loading';
        errMsg.textContent = 'Failed to load products. Please try again later.';
        container.appendChild(errMsg);
      });
  }

  function loadPages(type, container, countEl) {
    var ITEMS_PER_PAGE = 9;
    var currentPage = 1;
    var allItems = [];
    var jsonBase = '';

    /* Insert pagination nav after the container */
    var paginationEl = document.createElement('nav');
    paginationEl.className = 'pagination';
    container.parentNode.insertBefore(paginationEl, container.nextSibling);

    function renderPagination(totalPages) {
      while (paginationEl.firstChild) {
        paginationEl.removeChild(paginationEl.firstChild);
      }
      if (totalPages <= 1) { return; }

      var prev = document.createElement('button');
      prev.className = 'page-btn';
      prev.textContent = '\u2190';
      prev.disabled = currentPage === 1;
      prev.addEventListener('click', function () {
        if (currentPage > 1) { renderPage(currentPage - 1); }
      });
      paginationEl.appendChild(prev);

      for (var i = 1; i <= totalPages; i++) {
        (function (p) {
          var btn = document.createElement('button');
          btn.className = 'page-btn' + (p === currentPage ? ' active' : '');
          btn.textContent = p;
          btn.addEventListener('click', function () { renderPage(p); });
          paginationEl.appendChild(btn);
        })(i);
      }

      var next = document.createElement('button');
      next.className = 'page-btn';
      next.textContent = '\u2192';
      next.disabled = currentPage === totalPages;
      next.addEventListener('click', function () {
        if (currentPage < totalPages) { renderPage(currentPage + 1); }
      });
      paginationEl.appendChild(next);
    }

    function renderPage(page) {
      currentPage = page;
      var totalPages = Math.ceil(allItems.length / ITEMS_PER_PAGE);
      var start = (page - 1) * ITEMS_PER_PAGE;
      var pageItems = allItems.slice(start, start + ITEMS_PER_PAGE);

      if (countEl) {
        countEl.textContent =
          allItems.length + (allItems.length === 1 ? ' item' : ' items') + ' found';
      }

      while (container.firstChild) {
        container.removeChild(container.firstChild);
      }

      pageItems.forEach(function (item, index) {
        var card = document.createElement('a');
        card.href = item.slug + '.html';
        card.className = 'card fade-in';

        // Use IntersectionObserver to avoid forced reflow from setTimeout
        if (typeof IntersectionObserver !== 'undefined') {
          var newsObs = new IntersectionObserver(function(entries, obs) {
            entries.forEach(function(entry) {
              if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                obs.unobserve(entry.target);
              }
            });
          }, { threshold: 0.05 });
          newsObs.observe(card);
        } else {
          card.classList.add('visible');
        }

        var imageWrap = document.createElement('figure');
        imageWrap.className = 'card-image';
        if (getPrimaryImage(item)) {
          var img = document.createElement('img');
          img.src = resolveAssetUrl(getPrimaryImage(item), jsonBase);
          img.alt = item.title;
          img.loading = 'lazy';
          imageWrap.appendChild(img);
        } else {
          imageWrap.textContent = item.icon || (type === 'products' ? '\u2699' : '\uD83D\uDCF0');
        }
        card.appendChild(imageWrap);

        var body = document.createElement('section');
        body.className = 'card-body';

        var title = document.createElement('h3');
        title.textContent = item.title;
        body.appendChild(title);

        var summary = document.createElement('p');
        summary.textContent = item.summary;
        body.appendChild(summary);

        if (item.date) {
          var meta = document.createElement('time');
          meta.className = 'card-meta';
          meta.textContent = item.date;
          meta.setAttribute('datetime', item.date);
          body.appendChild(meta);
        }

        var linkText = document.createElement('span');
        linkText.className = 'card-link';
        var isProduct = (type === 'products' || type === 'bolts' || type === 'washers');
        linkText.textContent = isProduct ? 'View Details \u2192' : 'Read More \u2192';
        body.appendChild(linkText);

        card.appendChild(body);
        container.appendChild(card);
      });

      renderPagination(totalPages);

      if (page > 1) {
        container.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    fetchPagesData()
      .then(function (result) {
        allItems = result.data[type] || [];
        jsonBase = result.jsonBaseUrl;
        renderPage(1);
      })
      .catch(function () {
        while (container.firstChild) {
          container.removeChild(container.firstChild);
        }
        var errMsg = document.createElement('p');
        errMsg.className = 'loading';
        errMsg.textContent = 'Failed to load content. Please try again later.';
        container.appendChild(errMsg);
      });
  }

  /* ===== Contact Form Handling with Validation ===== */
  var contactForm = document.getElementById('contactForm');
  if (contactForm) {
    var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    function showError(input, msg) {
      input.classList.add('error');
      var errEl = input.parentElement.querySelector('.form-error');
      if (errEl) { errEl.textContent = msg; errEl.classList.add('show'); }
    }

    function clearError(input) {
      input.classList.remove('error');
      var errEl = input.parentElement.querySelector('.form-error');
      if (errEl) { errEl.classList.remove('show'); }
    }

    contactForm.addEventListener('submit', function (e) {
      var valid = true;

      var nameInput = contactForm.elements.name;
      var emailInput = contactForm.elements.email;
      var messageInput = contactForm.elements.message;

      clearError(nameInput);
      clearError(emailInput);
      clearError(messageInput);

      if (!nameInput.value.trim()) {
        showError(nameInput, 'Please enter your name.');
        valid = false;
      }
      if (!emailInput.value.trim()) {
        showError(emailInput, 'Please enter your email address.');
        valid = false;
      } else if (!emailRegex.test(emailInput.value.trim())) {
        showError(emailInput, 'Please enter a valid email address.');
        valid = false;
      }
      if (!messageInput.value.trim()) {
        showError(messageInput, 'Please enter your message.');
        valid = false;
      }

      if (!valid) { e.preventDefault(); return; }
      // If valid, allow form to submit to server (no client-side interception)
    });

    /* Clear errors on input */
    contactForm.querySelectorAll('input, textarea').forEach(function (el) {
      el.addEventListener('input', function () { clearError(el); });
    });
  }

  /* ===== FAQ Modal (3-second auto-popup) ===== */
  var faqOverlay = document.getElementById('faqOverlay');
  if (faqOverlay) {
    var faqKey = 'wt_faq_shown';
    var faqShown = sessionStorage.getItem(faqKey);

    function closeFaq() {
      faqOverlay.classList.remove('active');
    }

    var faqClose = faqOverlay.querySelector('.faq-close');
    if (faqClose) { faqClose.addEventListener('click', closeFaq); }

    document.addEventListener('click', function (e) {
      if (faqOverlay.classList.contains('active') && !faqOverlay.contains(e.target)) {
        closeFaq();
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && faqOverlay.classList.contains('active')) {
        closeFaq();
      }
    });

    if (!faqShown) {
      setTimeout(function () {
        faqOverlay.classList.add('active');
        sessionStorage.setItem(faqKey, '1');
      }, 3000);
    }
  }
  /* ===== Cookie Consent Banner ===== */
  var cookieKey = 'wt_cookie_consent';
  if (!localStorage.getItem(cookieKey)) {
    var banner = document.createElement('aside');
    banner.className = 'cookie-banner';
    banner.innerHTML =
      '<p>We use cookies to improve your experience on our website. By continuing to browse, you agree to our <a href="' +
      getPrivacyPolicyPath() +
      '">Privacy Policy</a>.</p>' +
      '<button class="cookie-btn">Accept</button>';
    document.body.appendChild(banner);

    setTimeout(function () { banner.classList.add('show'); }, 800);

    banner.querySelector('.cookie-btn').addEventListener('click', function () {
      localStorage.setItem(cookieKey, '1');
      banner.classList.remove('show');
      setTimeout(function () { banner.remove(); }, 400);
    });
  }

  /* ===== Back to Top Button ===== */
  var btt = document.createElement('button');
  btt.className = 'back-to-top';
  btt.setAttribute('aria-label', 'Back to top');
  btt.innerHTML = '&#8593;';
  document.body.appendChild(btt);

  window.addEventListener('scroll', function () {
    if (window.scrollY > 400) {
      btt.classList.add('visible');
    } else {
      btt.classList.remove('visible');
    }
  }, { passive: true });

  btt.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

})();
