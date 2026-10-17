#!/usr/bin/python3
"""KDE Connect file sharing through the installed daemon's session D-Bus API."""
import json
import os
from pathlib import Path
import re
import shutil
import sys
import uuid

import dbus

SERVICE = 'org.kde.kdeconnect'
ROOT = '/modules/kdeconnect'
DEVICE = SERVICE + '.device'


class ShareError(Exception):
    pass


class Client:
    def __init__(self, bus=None):
        self.bus = bus if bus is not None else dbus.SessionBus(private=True)

    def interface(self, path, name):
        return dbus.Interface(self.bus.get_object(SERVICE, path, introspect=False), name)

    def devices(self):
        if not self.bus.name_has_owner(SERVICE):
            return []
        daemon = self.interface(ROOT, SERVICE + '.daemon')
        result = []
        for device_id in daemon.devices(True, True, signature='bb', timeout=3):
            device_id = str(device_id)
            if not re.fullmatch(r'[A-Za-z0-9_]+', device_id):
                continue
            path = ROOT + '/devices/' + device_id
            try:
                props = self.interface(path, 'org.freedesktop.DBus.Properties').GetAll(DEVICE, timeout=2)
                # Ubuntu 22.04 calls this isTrusted; newer KDE Connect uses isPaired.
                if not props.get('isReachable') or not props.get('isPaired', props.get('isTrusted', False)):
                    continue
                if not self.interface(path, DEVICE).hasPlugin('kdeconnect_share', timeout=2):
                    continue
                result.append({'id': device_id, 'name': str(props.get('name') or '연결된 기기')})
            except dbus.DBusException:
                # A device can disconnect while its properties are being read.
                continue
        return sorted(result, key=lambda row: (row['name'].casefold(), row['id']))

    def send(self, device_id, files):
        if not files:
            raise ShareError('보낼 파일을 선택하세요.')
        urls = []
        for filename in files:
            path = Path(filename).expanduser().resolve(strict=True)
            if not path.is_file() or not os.access(path, os.R_OK):
                raise ShareError('읽을 수 있는 파일만 보낼 수 있습니다. 폴더는 압축한 뒤 선택하세요.')
            urls.append(path.as_uri())
        # Recheck trust, reachability and the sharing plugin immediately before sending.
        if device_id not in {row['id'] for row in self.devices()}:
            raise ShareError('기기 연결이 끊겼거나 파일 공유가 꺼져 있습니다. 기기를 다시 선택하세요.')
        share = self.interface(ROOT + '/devices/' + device_id + '/share', DEVICE + '.share')
        share.shareUrls(dbus.Array(urls, signature='s'), timeout=8)
        # D-Bus acceptance does not mean the remote transfer has finished.
        return len(urls)


def snapshot(client=None):
    result = {'available': False, 'count': 0, 'name': '기기를 연결하세요', 'status': 'KDE Connect에서 기기를 연결해 주세요.'}
    if client is None and shutil.which('kdeconnect-cli') is None:
        result.update(name='KDE Connect가 필요합니다', status='KDE Connect를 설치한 뒤 기기를 연결하세요.')
        return result
    try:
        devices = (client if client is not None else Client()).devices()
        if devices:
            result.update(available=True, count=len(devices), name=devices[0]['name'] + (f' 외 {len(devices)-1}대' if len(devices)>1 else ''),
                          status=f'{len(devices)}대 연결됨 · 파일 공유 가능')
    except dbus.DBusException:
        result.update(status='KDE Connect를 실행하고 연결을 확인해 주세요.')
    return result


def open_settings():
    from gi.repository import Gio
    app = Gio.DesktopAppInfo.new('org.kde.kdeconnect-settings.desktop')
    if app is None:
        raise ShareError('KDE Connect가 설치되어 있지 않습니다. Ubuntu 소프트웨어에서 설치하세요.')
    app.launch([], None)


def launch_dialog():
    config = Path(__file__).resolve().parent.parent
    bus = dbus.SessionBus()
    manager = dbus.Interface(bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1'), 'org.freedesktop.systemd1.Manager')
    keys = ('DISPLAY', 'XAUTHORITY', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS', 'LANG', 'LC_ALL', 'GDK_BACKEND',
            'XDG_DATA_HOME', 'XDG_CACHE_HOME', 'EWW_WIDGET_CONFIG', 'EWW_WIDGET_APP_ID', 'DESKTOP_STARTUP_ID')
    environment = [f'{key}={os.environ[key]}' for key in keys if key in os.environ]
    command = ['/usr/bin/python3', str(config / 'scripts/kdeconnect_dialog.py')]
    props = [('Description', dbus.String('Widget Library file sharing')), ('Type', dbus.String('exec')),
             ('CollectMode', dbus.String('inactive-or-failed')), ('WorkingDirectory', dbus.String(str(config))),
             ('Environment', dbus.Array(environment, signature='s')),
             ('ExecStart', dbus.Array([(command[0], dbus.Array(command, signature='s'), False)], signature='(sasb)'))]
    manager.StartTransientUnit('ubuntu-widget-share-' + uuid.uuid4().hex[:8] + '.service', 'fail',
                               dbus.Array(props, signature='(sv)'), dbus.Array([], signature='(sa(sv))'))


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv)>1 else 'snapshot'
    if action == 'snapshot':
        print(json.dumps(snapshot(), ensure_ascii=False))
    elif action == 'send':
        launch_dialog()
    else:
        raise SystemExit('Usage: kdeconnect_widget.py snapshot|send')
