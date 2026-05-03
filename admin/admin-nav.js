(function () {
  'use strict';

  var path = (window.location.pathname || '').toLowerCase();
  if (path.endsWith('/login.html') || path.indexOf('/admin/login.html') !== -1) {
    return;
  }

  var links = [
    { href: 'index.html', label: '🏠 后台首页' },
    { href: 'article-new.html', label: '✍️ 发布文章' },
    { href: 'article-list.html', label: '📝 文章列表' },
    { href: 'product-new.html', label: '🛠️ 发布产品' },
    { href: 'product-management.html', label: '🛍️ 产品管理' },
    { href: 'landing-new.html', label: '🚀 发布落地页' },
    { href: 'landing-management.html', label: '📄 落地页管理' },
    { href: 'pages-health.html', label: '🧪 索引体检' },
    { href: 'image-manager.html', label: '🖼️ 图片管理' },
    { href: 'users-view.html', label: '👥 用户数据' }
  ];

  function currentFileName() {
    var seg = (window.location.pathname || '').split('/');
    return (seg[seg.length - 1] || 'index.html').toLowerCase();
  }

  function setLegacyAuthStamp() {
    if (window.WTAdminAuth && WTAdminAuth.setLegacyAuthStamp) {
      WTAdminAuth.setLegacyAuthStamp();
      return;
    }
    var expiry = new Date().getTime() + 24 * 60 * 60 * 1000;
    localStorage.setItem('userAdminAuth', String(expiry));
  }

  function redirectToLogin() {
    if (window.WTAdminAuth && WTAdminAuth.redirectToLogin) {
      WTAdminAuth.redirectToLogin();
      return;
    }
    localStorage.removeItem('userAdminAuth');
    window.location.href = 'login.html';
  }

  async function ensureServerSession() {
    if (window.WTAdminAuth && WTAdminAuth.ensure) {
      return await WTAdminAuth.ensure({ redirect: false });
    }
    if (window.location.protocol === 'file:') {
      var auth = localStorage.getItem('userAdminAuth');
      var ok = !!auth && Date.now() <= parseInt(auth, 10);
      return ok;
    }
    try {
      var resp = await fetch('../cgi-bin/admin-auth.cgi?action=status&_=' + Date.now(), {
        credentials: 'include'
      });
      var data = await resp.json();
      if (resp.ok && data && data.authenticated) {
        setLegacyAuthStamp();
        return true;
      }
    } catch (err) {
      return false;
    }
    return false;
  }

  async function mountNav() {
    var authed = await ensureServerSession();
    if (!authed) {
      redirectToLogin();
      return;
    }

    var legacy = document.querySelectorAll('.admin-header, .topbar');
    legacy.forEach(function (el) {
      el.classList.add('legacy-admin-header');
    });

    var nav = document.createElement('header');
    nav.className = 'global-admin-nav';

    var inner = document.createElement('div');
    inner.className = 'global-admin-nav-inner';

    var brand = document.createElement('a');
    brand.className = 'global-admin-brand';
    brand.href = 'index.html';
    brand.textContent = 'WT 后台管理';
    inner.appendChild(brand);

    var group = document.createElement('nav');
    group.className = 'global-admin-links';
    var now = currentFileName();

    links.forEach(function (item) {
      var a = document.createElement('a');
      a.className = 'global-admin-link' + (now === item.href.toLowerCase() ? ' active' : '');
      a.href = item.href;
      a.textContent = item.label;
      group.appendChild(a);
    });
    inner.appendChild(group);

    var logout = document.createElement('button');
    logout.type = 'button';
    logout.className = 'global-admin-logout';
    logout.textContent = '退出登录';
    logout.addEventListener('click', function () {
      if (window.WTAdminAuth && WTAdminAuth.logout) {
        WTAdminAuth.logout();
        return;
      }
      if (window.location.protocol === 'file:') {
        localStorage.removeItem('userAdminAuth');
        window.location.href = 'login.html';
        return;
      }
      fetch('../cgi-bin/admin-auth.cgi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        credentials: 'include',
        body: 'action=logout'
      }).finally(function () {
        localStorage.removeItem('userAdminAuth');
        window.location.href = 'login.html';
      });
    });
    inner.appendChild(logout);

    nav.appendChild(inner);
    document.body.insertBefore(nav, document.body.firstChild);
    document.body.classList.add('admin-nav-mounted');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountNav);
  } else {
    mountNav();
  }
})();
