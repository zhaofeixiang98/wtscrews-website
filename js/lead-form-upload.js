(function () {
  if (window.WTLeadUploadValidationLoaded) { return; }
  window.WTLeadUploadValidationLoaded = true;

  var MAX_FILE_BYTES = 10 * 1024 * 1024;
  var MAX_FILE_COUNT = 5;
  var MAX_TOTAL_BYTES = 30 * 1024 * 1024;
  var ALLOWED_EXTENSIONS = [
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'txt',
    'jpg', 'jpeg', 'png', 'gif', 'webp',
    'zip', 'rar', '7z',
    'dwg', 'dxf', 'step', 'stp', 'igs', 'iges', 'stl', 'sldprt', 'sldasm'
  ];
  var BLOCKED_EXTENSIONS = [
    'php', 'phtml', 'phar', 'cgi', 'pl', 'py', 'sh', 'bash', 'zsh',
    'exe', 'dll', 'bat', 'cmd', 'com', 'scr', 'js', 'mjs', 'html', 'htm', 'shtml', 'svg'
  ];

  function isLeadForm(form) {
    var action = (form.getAttribute('action') || '').toLowerCase();
    return action.indexOf('/cgi-bin/save.php') !== -1 || action.indexOf('cgi-bin/save.php') !== -1;
  }

  function extOf(name) {
    var parts = String(name || '').toLowerCase().split('.');
    return parts.length > 1 ? parts.pop() : '';
  }

  function hasBlockedDoubleExtension(name) {
    var parts = String(name || '').toLowerCase().split('.');
    parts.pop();
    return parts.some(function (part) { return BLOCKED_EXTENSIONS.indexOf(part) !== -1; });
  }

  function validateAttachments(form) {
    var inputs = form.querySelectorAll('input[type="file"][name^="attachments"]');
    var files = [];
    inputs.forEach(function (input) {
      Array.prototype.forEach.call(input.files || [], function (file) { files.push(file); });
    });
    if (files.length === 0) { return ''; }
    if (files.length > MAX_FILE_COUNT) {
      return 'You can upload up to ' + MAX_FILE_COUNT + ' files per submission.';
    }
    var total = 0;
    for (var i = 0; i < files.length; i++) {
      var file = files[i];
      var ext = extOf(file.name);
      total += file.size || 0;
      if (!ext || ALLOWED_EXTENSIONS.indexOf(ext) === -1 || BLOCKED_EXTENSIONS.indexOf(ext) !== -1 || hasBlockedDoubleExtension(file.name)) {
        return 'This file type is not allowed: ' + file.name + '\nPlease upload common documents, images, ZIP/RAR/7Z archives, or CAD drawing files.';
      }
      if ((file.size || 0) <= 0) {
        return 'This file is empty: ' + file.name;
      }
      if ((file.size || 0) > MAX_FILE_BYTES) {
        return 'Each uploaded file must be 10MB or smaller: ' + file.name;
      }
    }
    if (total > MAX_TOTAL_BYTES) {
      return 'Total uploaded files must be 30MB or smaller.';
    }
    return '';
  }

  function setSubmitDisabled(form, disabled) {
    var btn = form.querySelector('[type="submit"]');
    if (btn) { btn.disabled = disabled; }
  }

  document.addEventListener('submit', function (event) {
    var form = event.target;
    if (!form || !isLeadForm(form)) { return; }

    if (form.checkValidity && !form.checkValidity()) {
      event.preventDefault();
      event.stopImmediatePropagation();
      if (form.reportValidity) { form.reportValidity(); }
      return;
    }

    var uploadError = validateAttachments(form);
    if (uploadError) {
      event.preventDefault();
      event.stopImmediatePropagation();
      alert(uploadError);
      setSubmitDisabled(form, false);
      return;
    }

    if (!window.fetch || !window.FormData) { return; }

    event.preventDefault();
    event.stopImmediatePropagation();
    setSubmitDisabled(form, true);

    fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      credentials: 'same-origin',
      headers: {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
      .then(function (response) {
        return response.text().then(function (text) {
          var data = null;
          try { data = JSON.parse(text); } catch (e) {}
          if (!response.ok || !data || data.success === false) {
            throw new Error((data && data.message) || text || 'Submission failed. Please check your file and try again.');
          }
          return data;
        });
      })
      .then(function (data) {
        window.location.href = data.redirect || '/pags/en/success.html';
      })
      .catch(function (err) {
        alert(err.message || 'Submission failed. Please check your file and try again.');
        setSubmitDisabled(form, false);
      });
  }, true);
})();
