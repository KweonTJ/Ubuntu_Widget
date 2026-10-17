#!/bin/bash
set -euo pipefail
export EWW_WIDGET_CONFIG="$HOME/.config/ubuntu-widget"
export EWW_WIDGET_BINARY=/usr/lib/ubuntu-widget/eww
export GDK_BACKEND=x11
cd -- "$EWW_WIDGET_CONFIG"
log_dir="$(mktemp -d)"
"$EWW_WIDGET_BINARY" --config "$EWW_WIDGET_CONFIG" --no-daemonize daemon > "$log_dir/engine.log" 2>&1 &
engine_pid=$!
gallery_pid=
trap 'kill "$engine_pid" ${gallery_pid:+"$gallery_pid"} 2>/dev/null || true' EXIT
for attempt in {1..40}; do
  if "$EWW_WIDGET_BINARY" --config "$EWW_WIDGET_CONFIG" ping >/dev/null 2>&1; then break; fi
  sleep .1
done
/usr/bin/python3 - <<'PY'
import subprocess
import sys
sys.path.insert(0, 'scripts')
from widget_store import BINARY, CONFIG, BUILTINS
ids = [w['id'] for w in BUILTINS]
subprocess.run([BINARY, '--config', str(CONFIG), 'open-many', *ids], check=True)
active = subprocess.check_output([BINARY, '--config', str(CONFIG), 'active-windows'], text=True)
assert {line.split(':', 1)[0] for line in active.splitlines()} == set(ids), active
print('Rendered all', len(ids), 'native windows under Xvfb.')
PY
/usr/bin/python3 scripts/widget_gallery.py > "$log_dir/gallery.log" 2>&1 &
gallery_pid=$!
sleep 3
kill -0 "$gallery_pid"
/usr/bin/python3 - <<'PY'
import json
import subprocess
import sys
sys.path.insert(0, 'scripts')
from widget_store import BINARY, CONFIG
def value(name):
    result = json.loads(subprocess.check_output([BINARY, '--config', str(CONFIG), 'get', name], text=True))
    return json.loads(result) if isinstance(result, str) else result
assert len(value('extra')['world']) == 4
assert value('services')['clock']
PY
if /usr/bin/grep -E 'Traceback|ModuleNotFoundError|No time zone found|failed to parse|error:|ERROR' "$log_dir/engine.log" "$log_dir/gallery.log"; then
  exit 1
fi
echo 'Native engine and GTK gallery smoke checks passed.'
