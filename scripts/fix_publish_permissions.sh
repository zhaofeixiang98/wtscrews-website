#!/usr/bin/env bash
set -euo pipefail

WEB_ROOT="${1:-/var/www/html}"
WEB_GROUP="${WEB_GROUP:-www-data}"
OWNER_UID="${OWNER_UID:-501}"
LANGS=(en zh ja ko fr de es ar id)

if [[ ! -d "$WEB_ROOT" ]]; then
  echo "ERROR: WEB_ROOT not found: $WEB_ROOT" >&2
  exit 1
fi

cd "$WEB_ROOT"

# Runtime job/status files for auto translation used by article/product/landing publishers.
mkdir -p .translate-jobs images/news
chown -R www-data:"$WEB_GROUP" .translate-jobs images/news 2>/dev/null || chown -R :"$WEB_GROUP" .translate-jobs images/news
chmod 775 .translate-jobs images/news
find .translate-jobs images/news -type d -exec chmod 775 {} +
find .translate-jobs images/news -type f -exec chmod 664 {} +

for lang in "${LANGS[@]}"; do
  lang_dir="pags/$lang"
  [[ -d "$lang_dir" ]] || mkdir -p "$lang_dir"

  # Needed by json_store.py atomic writes: ._pages_*.tmp, pages_*.json.lock, pages_*.json.bak.
  chown "$OWNER_UID":"$WEB_GROUP" "$lang_dir" 2>/dev/null || chown :"$WEB_GROUP" "$lang_dir"
  chmod 775 "$lang_dir"

  # Product/article/landing output directories.
  for sub in products news landing; do
    mkdir -p "$lang_dir/$sub"
    chown -R "$OWNER_UID":"$WEB_GROUP" "$lang_dir/$sub" 2>/dev/null || chown -R :"$WEB_GROUP" "$lang_dir/$sub"
    chmod 775 "$lang_dir/$sub"
    find "$lang_dir/$sub" -type d -exec chmod 775 {} +
    find "$lang_dir/$sub" -type f -exec chmod 664 {} +
  done

  # JSON and static list pages updated by publishers/render_list_pages.py.
  for f in "$lang_dir/pages_${lang}.json" "$lang_dir/pages_${lang}.json.bak" "$lang_dir/pages_${lang}.json.lock" "$lang_dir/products.html" "$lang_dir/news.html"; do
    if [[ -e "$f" ]]; then
      chown "$OWNER_UID":"$WEB_GROUP" "$f" 2>/dev/null || chown :"$WEB_GROUP" "$f"
      chmod 664 "$f"
    fi
  done
done

# CGI scripts must remain executable after Git sync.
if [[ -d cgi-bin ]]; then
  chown -R www-data:"$WEB_GROUP" cgi-bin 2>/dev/null || chown -R :"$WEB_GROUP" cgi-bin
  find cgi-bin -type f -name '*.cgi' -exec chmod 755 {} +
  find cgi-bin -type f -name '*.py' -exec chmod 755 {} +
fi

# Verify the actual Apache user can write all publisher targets.
sudo -u www-data sh -c '
set -e
for lang in en zh ja ko fr de es ar id; do
  echo ok > "pags/$lang/._pages_permission_test.tmp"
  rm "pags/$lang/._pages_permission_test.tmp"
  echo ok > "pags/$lang/products/.permission-test" && rm "pags/$lang/products/.permission-test"
  echo ok > "pags/$lang/news/.permission-test" && rm "pags/$lang/news/.permission-test"
  echo ok > "pags/$lang/landing/.permission-test" && rm "pags/$lang/landing/.permission-test"
done
echo ok > .translate-jobs/.permission-test && rm .translate-jobs/.permission-test
echo ok > images/news/.permission-test && rm images/news/.permission-test
'

echo "Publish permissions fixed for $WEB_ROOT"
