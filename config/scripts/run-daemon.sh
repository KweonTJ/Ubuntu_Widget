#!/bin/bash
set -euo pipefail
# Keep GTK on the same backend as the X11-only engine, even when launched directly.
export GDK_BACKEND=x11
widget_config="${EWW_WIDGET_CONFIG:-$(cd -- "$(dirname -- "$0")/.." && pwd)}"
widget_binary="${EWW_WIDGET_BINARY:-$HOME/.local/lib/ubuntu-widget/eww}"
widget_cache="${XDG_CACHE_HOME:-$HOME/.cache}/ubuntu-widget"
mkdir -p -- "$widget_cache"
exec "$widget_binary" --config "$widget_config" --no-daemonize daemon >> "$widget_cache/daemon.log" 2>&1
