(function () {
  'use strict';

  var KEY = 'userAdminAuth';
  var DAY_MS = 24 * 60 * 60 * 1000;

  function isFileMode() {
    return window.location.protocol === 'file:';
  }

  function setLegacyAuthStamp() {
    localStorage.setItem(KEY, String(Date.now() + DAY_MS));
  }

  function hasLegacyAuth() {
    var raw = localStorage.getItem(KEY);
    var expiry = parseInt(raw || '0', 10);
    return !!raw && Number.isFinite(expiry) && Date.now() <= expiry;
  }

  function redirectToLogin() {
    localStorage.removeItem(KEY);
    if (!/login\.html$/i.test(window.location.pathname || '')) {
      window.location.href = 'login.html';
    }
  }

  async function ensure(options) {
    options = options || {};
    if (isFileMode()) {
      if (hasLegacyAuth()) return true;
      if (options.redirect !== false) redirectToLogin();
      return false;
    }

    try {
      var resp = await fetch('../cgi-bin/admin-auth.cgi?action=status&_=' + Date.now(), {
        credentials: 'include'
      });
      var data = await resp.json();
      if (resp.ok && data && data.success && data.authenticated) {
        setLegacyAuthStamp();
        return true;
      }
    } catch (err) {}

    localStorage.removeItem(KEY);
    if (options.redirect !== false) redirectToLogin();
    return false;
  }

  function logout() {
    if (isFileMode()) {
      redirectToLogin();
      return;
    }
    fetch('../cgi-bin/admin-auth.cgi', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      credentials: 'include',
      body: 'action=logout'
    }).finally(redirectToLogin);
  }

  window.WTAdminAuth = {
    ensure: ensure,
    logout: logout,
    hasLegacyAuth: hasLegacyAuth,
    setLegacyAuthStamp: setLegacyAuthStamp,
    redirectToLogin: redirectToLogin
  };
})();
