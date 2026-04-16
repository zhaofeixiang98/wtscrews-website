/* ===== Chat Dock: WhatsApp + LINE with QR Popups ===== */
(function () {
  var isMobile = /Android|iPhone|iPad|iPod|webOS|BlackBerry|Opera Mini|IEMobile/i.test(navigator.userAgent) || window.innerWidth <= 768;

  /* Derive image base path from this script's location */
  var src = document.currentScript && document.currentScript.src;
  var imgBase = 'images/';
  if (src) {
    var idx = src.lastIndexOf('/js/');
    if (idx !== -1) { imgBase = src.substring(0, idx) + '/images/'; }
  }

  var lineUrl = 'https://line.me/ti/p/StdQJteUYQ';
  var whatsappUrl = 'https://wa.me/8615175432812?text=' + encodeURIComponent('Hi, I\'m interested in your fastener products. Could you send me a catalog and price list?');

  var html;
  if (isMobile) {
    /* Mobile: direct links, no QR */
    html =
      '<nav class="chat-dock">' +
        '<a href="' + lineUrl + '" target="_blank" rel="noopener" class="chat-btn chat-btn--line" aria-label="Chat on LINE">' +
          '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M16 1.4C7.6 1.4.8 7 .8 14c0 6.2 5.5 11.4 12.9 12.4.5.1 1.2.3 1.3.8.1.4.1 1.1 0 1.5 0 0-.2 1-.2 1.2-.1.4-.3 1.5 1.3.8s8.8-5.2 12-8.9c2.2-2.4 3.2-4.9 3.2-7.8-.1-7-6.8-12.6-15.3-12.6zM10.2 18H7.4c-.4 0-.7-.3-.7-.7v-5.8c0-.4.3-.7.7-.7s.7.3.7.7v5.1h2.1c.4 0 .7.3.7.7s-.3.7-.7.7zm2.3-.7c0 .4-.3.7-.7.7s-.7-.3-.7-.7v-5.8c0-.4.3-.7.7-.7s.7.3.7.7v5.8zm6.2 0c0 .3-.2.5-.4.6h-.2c-.2 0-.4-.1-.5-.3l-2.9-3.9v3.6c0 .4-.3.7-.7.7s-.7-.3-.7-.7v-5.8c0-.3.2-.5.4-.6.2-.1.5-.1.7.1l2.8 3.8v-3.4c0-.4.3-.7.7-.7s.7.3.7.7v5.9zm4.7-4.4c.4 0 .7.3.7.7s-.3.7-.7.7h-2.1v1.3h2.1c.4 0 .7.3.7.7s-.3.7-.7.7h-2.8c-.4 0-.7-.3-.7-.7v-5.8c0-.4.3-.7.7-.7h2.8c.4 0 .7.3.7.7s-.3.7-.7.7h-2.1v1.3h2.1z"/></svg>' +
        '</a>' +
        '<a href="' + whatsappUrl + '" target="_blank" rel="noopener" class="chat-btn chat-btn--whatsapp" aria-label="Chat on WhatsApp">' +
          '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M16.004 0h-.008C7.174 0 0 7.176 0 16c0 3.5 1.128 6.744 3.046 9.378L1.054 31.29l6.118-1.96A15.9 15.9 0 0016.004 32C24.826 32 32 24.822 32 16S24.826 0 16.004 0zm9.32 22.608c-.39 1.1-1.932 2.014-3.15 2.28-.834.18-1.922.322-5.588-1.2-4.688-1.948-7.706-6.706-7.94-7.016-.226-.31-1.846-2.46-1.846-4.692 0-2.232 1.168-3.33 1.584-3.786.39-.426 1.034-.606 1.65-.606.2 0 .378.01.54.018.456.02.686.046.988.764.376.9 1.292 3.134 1.404 3.362.114.228.228.538.076.846-.144.316-.27.456-.496.716-.228.258-.444.456-.672.734-.21.24-.444.498-.19.978.254.472 1.13 1.866 2.426 3.022 1.666 1.49 3.07 1.952 3.508 2.168.34.168.744.14.998-.128.322-.34.72-.902 1.124-1.458.288-.396.65-.446 1.022-.302.376.138 2.382 1.124 2.79 1.328.408.206.68.306.78.476.098.168.098.978-.292 2.078z"/></svg>' +
        '</a>' +
      '</nav>';
  } else {
    /* Desktop: QR popup cards */
    html =
      '<nav class="chat-dock">' +
        '<div class="chat-btn chat-btn--line" data-qr aria-label="LINE QR Code" role="button" tabindex="0">' +
          '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M16 1.4C7.6 1.4.8 7 .8 14c0 6.2 5.5 11.4 12.9 12.4.5.1 1.2.3 1.3.8.1.4.1 1.1 0 1.5 0 0-.2 1-.2 1.2-.1.4-.3 1.5 1.3.8s8.8-5.2 12-8.9c2.2-2.4 3.2-4.9 3.2-7.8-.1-7-6.8-12.6-15.3-12.6zM10.2 18H7.4c-.4 0-.7-.3-.7-.7v-5.8c0-.4.3-.7.7-.7s.7.3.7.7v5.1h2.1c.4 0 .7.3.7.7s-.3.7-.7.7zm2.3-.7c0 .4-.3.7-.7.7s-.7-.3-.7-.7v-5.8c0-.4.3-.7.7-.7s.7.3.7.7v5.8zm6.2 0c0 .3-.2.5-.4.6h-.2c-.2 0-.4-.1-.5-.3l-2.9-3.9v3.6c0 .4-.3.7-.7.7s-.7-.3-.7-.7v-5.8c0-.3.2-.5.4-.6.2-.1.5-.1.7.1l2.8 3.8v-3.4c0-.4.3-.7.7-.7s.7.3.7.7v5.9zm4.7-4.4c.4 0 .7.3.7.7s-.3.7-.7.7h-2.1v1.3h2.1c.4 0 .7.3.7.7s-.3.7-.7.7h-2.8c-.4 0-.7-.3-.7-.7v-5.8c0-.4.3-.7.7-.7h2.8c.4 0 .7.3.7.7s-.3.7-.7.7h-2.1v1.3h2.1z"/></svg>' +
          '<aside class="qr-popup">' +
            '<img src="' + imgBase + 'qr-line-sm.webp" alt="LINE QR Code" width="320" height="320" loading="lazy">' +
            '<p>Scan to add us on LINE</p>' +
            '<a href="' + lineUrl + '" target="_blank" rel="noopener" class="qr-chat-link qr-chat-link--line">Quick Chat \u2192</a>' +
          '</aside>' +
        '</div>' +
        '<div class="chat-btn chat-btn--whatsapp" data-qr aria-label="WhatsApp QR Code" role="button" tabindex="0">' +
          '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M16.004 0h-.008C7.174 0 0 7.176 0 16c0 3.5 1.128 6.744 3.046 9.378L1.054 31.29l6.118-1.96A15.9 15.9 0 0016.004 32C24.826 32 32 24.822 32 16S24.826 0 16.004 0zm9.32 22.608c-.39 1.1-1.932 2.014-3.15 2.28-.834.18-1.922.322-5.588-1.2-4.688-1.948-7.706-6.706-7.94-7.016-.226-.31-1.846-2.46-1.846-4.692 0-2.232 1.168-3.33 1.584-3.786.39-.426 1.034-.606 1.65-.606.2 0 .378.01.54.018.456.02.686.046.988.764.376.9 1.292 3.134 1.404 3.362.114.228.228.538.076.846-.144.316-.27.456-.496.716-.228.258-.444.456-.672.734-.21.24-.444.498-.19.978.254.472 1.13 1.866 2.426 3.022 1.666 1.49 3.07 1.952 3.508 2.168.34.168.744.14.998-.128.322-.34.72-.902 1.124-1.458.288-.396.65-.446 1.022-.302.376.138 2.382 1.124 2.79 1.328.408.206.68.306.78.476.098.168.098.978-.292 2.078z"/></svg>' +
          '<aside class="qr-popup">' +
            '<img src="' + imgBase + 'qr-whatsapp-sm.webp" alt="WhatsApp QR Code" width="320" height="320" loading="lazy">' +
            '<p>Scan to chat on WhatsApp</p>' +
            '<a href="' + whatsappUrl + '" target="_blank" rel="noopener" class="qr-chat-link qr-chat-link--whatsapp">Quick Chat \u2192</a>' +
          '</aside>' +
        '</div>' +
      '</nav>';
  }

  document.body.insertAdjacentHTML('beforeend', html);

  /* Desktop only: bind click-to-toggle QR popups */
  if (!isMobile) {
    var chatBtns = document.querySelectorAll('.chat-btn[data-qr]');
    chatBtns.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        /* Let <a> links inside the popup navigate normally */
        if (e.target.closest('.qr-chat-link')) return;
        e.preventDefault();
        e.stopPropagation();
        var popup = btn.querySelector('.qr-popup');
        if (!popup) return;
        var isOpen = popup.classList.contains('show');
        document.querySelectorAll('.qr-popup.show').forEach(function (p) { p.classList.remove('show'); });
        if (!isOpen) { popup.classList.add('show'); }
      });
    });
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.chat-btn')) {
        document.querySelectorAll('.qr-popup.show').forEach(function (p) { p.classList.remove('show'); });
      }
    });
  }
})();
