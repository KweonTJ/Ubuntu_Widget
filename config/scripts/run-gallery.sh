#!/bin/bash
set -euo pipefail
widget_config="${EWW_WIDGET_CONFIG:-$(cd -- "$(dirname -- "$0")/.." && pwd)}"
widget_cache="${XDG_CACHE_HOME:-$HOME/.cache}/ubuntu-widget"
mkdir -p -- "$widget_cache"
if [ "${1:-}" = app ] && [[ "${2:-}" = todomate || "${2:-}" = todomate-sync ]]; then
  exec /usr/bin/python3 "$widget_config/scripts/todomate_webview.py" "$([ "${2:-}" = todomate-sync ] && echo sync || echo connect)" >> "$widget_cache/gallery.log" 2>&1
fi
if [ "${1:-}" = menu ]; then
  exec /usr/bin/python3 "$widget_config/scripts/widget-menu.py" "$2" >> "$widget_cache/gallery.log" 2>&1
fi
exec /usr/bin/python3 "$widget_config/scripts/widget_gallery.py" "$@" >> "$widget_cache/gallery.log" 2>&1
