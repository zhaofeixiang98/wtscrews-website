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
    });
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

  function loadCategorizedProducts(container, countEl) {
    var pagesJsonPath = '../pages.json';

    fetch(pagesJsonPath)
      .then(function (res) { return res.json(); })
      .then(function (data) {
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

            setTimeout(function () { card.classList.add('visible'); }, idx * 100);

            var imageWrap = document.createElement('figure');
            imageWrap.className = 'card-image';
            if (item.icon && item.icon.indexOf('images/') === 0) {
              var img = document.createElement('img');
              img.src = '../' + item.icon;
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
    var path = window.location.pathname;
    var pagesJsonPath = '../pages.json';
    if (path.indexOf('/products/') !== -1 || path.indexOf('/news/') !== -1) {
      pagesJsonPath = '../../pages.json';
    }

    fetch(pagesJsonPath)
      .then(function (res) {
        return res.json();
      })
      .then(function (data) {
        var items = data[type] || [];

        /* Update count display */
        if (countEl) {
          countEl.textContent =
            items.length + (items.length === 1 ? ' item' : ' items') + ' found';
        }

        /* Clear loading text */
        while (container.firstChild) {
          container.removeChild(container.firstChild);
        }

        /* Create cards using DOM API — no HTML tags in JS */
        items.forEach(function (item, index) {
          var card = document.createElement('a');
          card.href = item.slug + '.html';
          card.className = 'card fade-in';

          /* Stagger animation */
          setTimeout(function () {
            card.classList.add('visible');
          }, index * 100);

          /* Image area */
          var imageWrap = document.createElement('figure');
          imageWrap.className = 'card-image';
          if (item.icon && item.icon.indexOf('images/') === 0) {
            var img = document.createElement('img');
            img.src = pagesJsonPath.replace('pages.json', '') + item.icon;
            img.alt = item.title;
            img.loading = 'lazy';
            imageWrap.appendChild(img);
          } else {
            imageWrap.textContent = item.icon || (type === 'products' ? '\u2699' : '\uD83D\uDCF0');
          }
          card.appendChild(imageWrap);

          /* Body */
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
      (window.location.pathname.indexOf('/pags/') !== -1
        ? (window.location.pathname.indexOf('/products/') !== -1 || window.location.pathname.indexOf('/news/') !== -1
          ? '../privacy-policy.html' : 'privacy-policy.html')
        : 'pags/privacy-policy.html') +
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
  });

  btt.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

})();
