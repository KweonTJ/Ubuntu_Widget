#!/bin/bash
# Run only inside the disposable container created by `make test-deb`.
set -euo pipefail
test -f /.dockerenv || { echo 'This test must run in a disposable Docker container.' >&2; exit 1; }
package_deb="${1:?Pass the Debian package path}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y "$package_deb" xvfb dbus-x11 desktop-file-utils
useradd -m -u 1101 -d /tmp/widget-user-demo demo
useradd -m -u 1102 -d /tmp/widget-user-other other
test ! -e /tmp/widget-user-demo/.config/ubuntu-widget
test ! -e /tmp/widget-user-other/.config/ubuntu-widget
desktop-file-validate /usr/share/applications/local.ubuntu.WidgetLibrary.desktop
if ldd /usr/lib/ubuntu-widget/eww | /usr/bin/grep 'not found'; then exit 1; fi
/usr/bin/ubuntu-widget --help
if /usr/bin/ubuntu-widget edit; then echo 'Root launch should be rejected'; exit 1; fi
if runuser -u demo -- env HOME=/tmp/widget-user-demo DISPLAY=:99 XDG_SESSION_TYPE=wayland /usr/bin/ubuntu-widget edit; then
  echo 'Wayland should be rejected'; exit 1
fi
test ! -e /tmp/widget-user-demo/.config/ubuntu-widget
runuser -u demo -- env HOME=/tmp/widget-user-demo DISPLAY=:99 XDG_SESSION_TYPE=x11 /usr/bin/ubuntu-widget theme dark
runuser -u other -- env HOME=/tmp/widget-user-other DISPLAY=:99 XDG_SESSION_TYPE=x11 /usr/bin/ubuntu-widget theme light
/usr/bin/python3 - <<'PY'
import json
from pathlib import Path
for name in ('demo', 'other'):
    config = Path('/tmp/widget-user-' + name) / '.config/ubuntu-widget'
    assert json.loads((config / 'positions.json').read_text()) == {}
    assert json.loads((config / 'connections.json').read_text())['screentime']['enabled'] is False
    assert json.loads((config / 'widget-settings.json').read_text())['note']['text'] == ''
    assert not (config.parent / 'autostart/ubuntu-widget.desktop').exists()
(Path('/tmp/widget-user-demo/.config/ubuntu-widget/widget-settings.json')).write_text(json.dumps({'note': {'title': 'Test', 'text': 'keep test content'}}))
PY
echo '# upgrade test' >> /usr/share/ubuntu-widget/config/scripts/data.py
runuser -u demo -- env HOME=/tmp/widget-user-demo DISPLAY=:99 XDG_SESSION_TYPE=x11 /usr/bin/ubuntu-widget theme auto
/usr/bin/python3 - <<'PY'
import json
from pathlib import Path
config = Path('/tmp/widget-user-demo/.config/ubuntu-widget')
assert json.loads((config / 'widget-settings.json').read_text())['note']['text'] == 'keep test content'
assert (config / 'scripts/data.py').read_text().endswith('# upgrade test\n')
assert json.loads(Path('/tmp/widget-user-other/.config/ubuntu-widget/widget-settings.json').read_text())['note']['text'] == ''
PY
runuser -u demo -- env HOME=/tmp/widget-user-demo XDG_SESSION_TYPE=x11 dbus-run-session -- xvfb-run -a /bin/bash /package/tests/deb-ui-smoke.sh
apt-get purge -y ubuntu-widget
/usr/bin/python3 - <<'PY'
import json
from pathlib import Path
assert not Path('/usr/bin/ubuntu-widget').exists()
assert not Path('/usr/lib/ubuntu-widget/eww').exists()
assert json.loads(Path('/tmp/widget-user-demo/.config/ubuntu-widget/widget-settings.json').read_text())['note']['text'] == 'keep test content'
print('Debian install, two-user initialization, template upgrade and purge checks passed.')
PY
