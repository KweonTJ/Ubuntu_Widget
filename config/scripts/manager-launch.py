#!/usr/bin/python3
"""Launch a persistent gallery/menu without depending on the caller terminal."""
from pathlib import Path
import os,sys,uuid
import dbus
from widget_store import find, CONFIG
config=CONFIG
args=sys.argv[1:]
if args:
    if len(args)==2 and args[0]=='app' and args[1] in ('todomate','todomate-sync'):pass
    elif len(args)==2 and args[0] in ('select','menu'):find(args[1])
    else:raise SystemExit('Usage: manager-launch.py [select|menu <widget-id>] | app todomate')
manager=dbus.Interface(dbus.SessionBus().get_object('org.freedesktop.systemd1','/org/freedesktop/systemd1'),'org.freedesktop.systemd1.Manager')
env=[f'{k}={os.environ[k]}' for k in ('DISPLAY','XAUTHORITY','XDG_RUNTIME_DIR','DBUS_SESSION_BUS_ADDRESS','LANG','LC_ALL','GDK_BACKEND','EWW_WIDGET_CONFIG','EWW_WIDGET_BINARY','EWW_INTEGRATION_CACHE','XDG_CACHE_HOME','XDG_DATA_HOME','TZ','EWW_WIDGET_APP_ID','DESKTOP_STARTUP_ID') if k in os.environ]
props=[('Description',dbus.String('Desktop widget gallery')),('Type',dbus.String('exec')),('CollectMode',dbus.String('inactive-or-failed')),('WorkingDirectory',dbus.String(str(config))),('Environment',dbus.Array(env,signature='s')),('ExecStart',dbus.Array([('/bin/bash',dbus.Array(['/bin/bash',str(config/'scripts/run-gallery.sh'),*args],signature='s'),False)],signature='(sasb)'))]
manager.StartTransientUnit('ubuntu-widget-gallery-'+uuid.uuid4().hex[:8]+'.service','fail',dbus.Array(props,signature='(sv)'),dbus.Array([],signature='(sa(sv))'))
