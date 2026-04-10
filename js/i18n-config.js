/* ===== i18n Configuration ===== */
/* 要添加新语言，只需在这里加一行配置 */

var I18N = {
  defaultLang: 'en',
languages: [
  { code: 'en', name: 'English', path: '/pags/en/', htmlLang: 'en' },
  { code: 'zh', name: '中文', path: '/pags/zh/', htmlLang: 'zh-CN' },
  { code: 'id', name: 'Indonesia', path: '/pags/id/', htmlLang: 'id' },

  { code: 'ar', name: 'العربية', path: '/pags/ar/', htmlLang: 'ar' },
  { code: 'de', name: 'Deutsch', path: '/pags/de/', htmlLang: 'de' },
  { code: 'fr', name: 'Français', path: '/pags/fr/', htmlLang: 'fr' },
  { code: 'es', name: 'Español', path: '/pags/es/', htmlLang: 'es' },
  { code: 'ja', name: '日本語', path: '/pags/ja/', htmlLang: 'ja' },
  { code: 'ko', name: '한국어', path: '/pags/ko/', htmlLang: 'ko' }
]
};

/* ===== 自动检测当前语言 ===== */
function getCurrentLang() {
  var path = window.location.pathname;
  for (var i = 0; i < I18N.languages.length; i++) {
    if (path.indexOf('/' + I18N.languages[i].code + '/') !== -1) {
      return I18N.languages[i].code;
    }
  }
  return I18N.defaultLang;
}

/* ===== 生成语言切换下拉菜单（自动选中当前语言） ===== */
function buildLangSwitcher() {
  var currentLang = getCurrentLang();
  var select = document.getElementById('langSwitcher');
  if (!select) return;
  
  var html = '';
  for (var i = 0; i < I18N.languages.length; i++) {
    var lang = I18N.languages[i];
    var selected = (lang.code === currentLang) ? ' selected' : '';
    html += '<option value="' + lang.code + '"' + selected + '>' + lang.name + '</option>';
  }
  select.innerHTML = html;
}

/* ===== 语言切换逻辑 ===== */
function switchLanguage(lang) {
  var currentPath = window.location.pathname;
  var currentLang = getCurrentLang();
  
  if (lang === currentLang) return;
  
  var newPath = currentPath
    .replace('/' + currentLang + '/', '/' + lang + '/')
    .replace('/' + I18N.defaultLang + '/', '/' + lang + '/');
  
  // 如果路径没变（首页等），直接跳到目标语言首页
  if (newPath === currentPath || newPath.indexOf('/' + lang + '/') === -1) {
    var targetLangConfig = null;
    for (var i = 0; i < I18N.languages.length; i++) {
      if (I18N.languages[i].code === lang) {
        targetLangConfig = I18N.languages[i];
        break;
      }
    }
    if (targetLangConfig) {
      window.location.href = targetLangConfig.path + 'index.html';
    }
    return;
  }
  
  window.location.href = newPath;
}

/* ===== 页面加载完成后初始化 ===== */
document.addEventListener('DOMContentLoaded', function() {
  buildLangSwitcher();
});
