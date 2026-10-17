#!/usr/bin/python3
"""Keep the desktop widget daemon alive independently of its launch terminal."""
import os
from pathlib import Path
import subprocess
import time
import uuid
import dbus

from widget_store import BINARY,CONFIG
binary=BINARY
config=str(CONFIG)
cache=Path(os.environ.get('XDG_CACHE_HOME',Path.home()/'.cache'))/'ubuntu-widget'
cache.mkdir(parents=True,exist_ok=True)

def ready():
    p = subprocess.run([binary, '--config', config, 'ping'], capture_output=True, text=True, timeout=8)
    return p.stdout.strip() == 'pong'

if not ready():
    bus = dbus.SessionBus()
    manager = dbus.Interface(bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1'),
                             'org.freedesktop.systemd1.Manager')
    env = [f'{key}={os.environ[key]}' for key in
           ('DISPLAY','XAUTHORITY','XDG_RUNTIME_DIR','DBUS_SESSION_BUS_ADDRESS','LANG','LC_ALL','GDK_BACKEND','EWW_WIDGET_CONFIG','EWW_WIDGET_BINARY','EWW_INTEGRATION_CACHE','XDG_CACHE_HOME','XDG_DATA_HOME','TZ','EWW_WIDGET_APP_ID')
           if key in os.environ]
    log = str(cache/'daemon.log')
    props = [
        ('Description', dbus.String('Eww movable desktop widgets')),
        ('Type', dbus.String('exec')),
        ('CollectMode', dbus.String('inactive-or-failed')),
        ('WorkingDirectory', dbus.String(config)),
        ('Environment', dbus.Array(env, signature='s')),
        ('ExecStart', dbus.Array([('/bin/bash', dbus.Array(['/bin/bash', config + '/scripts/run-daemon.sh'], signature='s'), False)], signature='(sasb)')),
    ]
    unit = 'ubuntu-widget-daemon-' + uuid.uuid4().hex[:8] + '.service'
    manager.StartTransientUnit(unit, 'fail', dbus.Array(props, signature='(sv)'), dbus.Array([], signature='(sa(sv))'))
    for _ in range(40):
        if ready(): break
        time.sleep(.1)
    else:
        raise SystemExit('Eww did not start. Check ' + log)
