(function () {
  'use strict';

  var menuToggle = document.getElementById('menuToggle');
  var navLinks = document.getElementById('navLinks');

  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', function () {
      navLinks.classList.toggle('open');
      menuToggle.classList.toggle('active');
    });

    navLinks.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        navLinks.classList.remove('open');
        menuToggle.classList.remove('active');
      });
    });
  }

  var header = document.getElementById('siteHeader');
  if (header) {
    function syncHeaderState() {
      if (window.scrollY > 50) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
    }

    syncHeaderState();
    window.addEventListener('scroll', syncHeaderState, { passive: true });
  }

  var currentPage = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(function (link) {
    var href = link.getAttribute('href') || '';
    var linkPage = href.split('/').pop();
    if (linkPage === currentPage) {
      link.classList.add('active');
    }
    if (window.location.pathname.indexOf('/products/') !== -1 && linkPage === 'products.html') {
      link.classList.add('active');
    }
  });

  var fadeElements = document.querySelectorAll('.fade-in');
  if (fadeElements.length > 0 && typeof IntersectionObserver !== 'undefined') {
    var observer = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    fadeElements.forEach(function (el) {
      observer.observe(el);
    });
  } else {
    fadeElements.forEach(function (el) {
      el.classList.add('visible');
    });
  }

  var cookieKey = 'wt_cookie_consent';
  if (!localStorage.getItem(cookieKey)) {
    var privacyPolicyPath = (function () {
      var path = window.location.pathname;
      var langs = ['zh', 'id', 'fr', 'de', 'es', 'ja', 'ko', 'ar', 'en'];
      var currentLang = 'en';
      langs.forEach(function (lang) {
        if (path.indexOf('/' + lang + '/') !== -1) {
          currentLang = lang;
        }
      });
      var langRoot = '/pags/' + currentLang + '/';
      var langRootIndex = path.indexOf(langRoot);
      if (langRootIndex !== -1) {
        return path.slice(0, langRootIndex + langRoot.length) + 'privacy-policy.html';
      }
      return langRoot + 'privacy-policy.html';
    })();

    var banner = document.createElement('aside');
    banner.className = 'cookie-banner';
    banner.innerHTML =
      '<p>We use cookies to improve your experience on our website. By continuing to browse, you agree to our <a href="' +
      privacyPolicyPath +
      '">Privacy Policy</a>.</p>' +
      '<button class="cookie-btn">Accept</button>';
    document.body.appendChild(banner);

    setTimeout(function () {
      banner.classList.add('show');
    }, 800);

    banner.querySelector('.cookie-btn').addEventListener('click', function () {
      localStorage.setItem(cookieKey, '1');
      banner.classList.remove('show');
      setTimeout(function () {
        banner.remove();
      }, 400);
    });
  }

  var backToTop = document.createElement('button');
  backToTop.className = 'back-to-top';
  backToTop.setAttribute('aria-label', 'Back to top');
  backToTop.innerHTML = '&#8593;';
  document.body.appendChild(backToTop);

  window.addEventListener('scroll', function () {
    if (window.scrollY > 400) {
      backToTop.classList.add('visible');
    } else {
      backToTop.classList.remove('visible');
    }
  }, { passive: true });

  backToTop.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();
