#!/usr/bin/python3
"""Desktop data, player artwork and explicit controls for the Eww widgets."""
import calendar
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

import dbus
from album_art import ArtworkCache

TZ = None  # None means the current user's local system timezone.
PLAYER = "org.mpris.MediaPlayer2.Player"
PROPS = "org.freedesktop.DBus.Properties"
BATTERIES = Path("/sys/class/power_supply")
BUS = None
SYSTEM_BUS = None
ARTWORK = ArtworkCache()


def command(args):
    try:
        return subprocess.check_output(args, text=True, timeout=1.5,
                                       stderr=subprocess.DEVNULL,
                                       env={**os.environ, "LC_ALL": "C"}).strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def media(artwork=True):
    global BUS
    players = []
    try:
        if BUS is None:
            BUS = dbus.SessionBus()
        for name in BUS.list_names():
            if str(name).startswith("org.mpris.MediaPlayer2."):
                try:
                    obj = BUS.get_object(name, "/org/mpris/MediaPlayer2")
                    p = dbus.Interface(obj, PROPS).GetAll(PLAYER, timeout=0.4)
                    players.append((obj, p))
                except dbus.DBusException:
                    pass
    except dbus.DBusException:
        BUS = None
    if not players:
        return None, {"title": "재생 중인 음악 없음", "artist": "음악 앱이나 브라우저에서 재생하세요",
                      "status": "음악", "playing": False, "available": False,
                      "can_play": False, "can_previous": False, "can_next": False, "art": ""}
    players.sort(key=lambda p: {"Playing": 0, "Paused": 1}.get(str(p[1].get("PlaybackStatus")), 2))
    obj, p = players[0]
    m = p.get("Metadata", {})
    playing = str(p.get("PlaybackStatus")) == "Playing"
    title = str(m.get("xesam:title", "제목 없음"))[:160]
    artist = ", ".join(str(x) for x in m.get("xesam:artist", []))[:160]
    control = bool(p.get("CanControl", False))
    return obj, {"title": title, "artist": artist or "미디어 플레이어",
                 "art": ARTWORK.get(str(m.get("mpris:artUrl", ""))) if artwork else "",
                 "status": "지금 재생 중" if playing else "일시 정지", "playing": playing,
                 "available": control, "can_play": control and bool(p.get("CanPause" if playing else "CanPlay", False)),
                 "can_previous": control and bool(p.get("CanGoPrevious", False)),
                 "can_next": control and bool(p.get("CanGoNext", False))}


def sound():
    raw = command(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
    match = re.search(r"(\d+)%", raw)
    mute_raw = command(["pactl", "get-sink-mute", "@DEFAULT_SINK@"])
    muted = mute_raw.endswith("yes")
    value = int(match.group(1)) if match else 0
    return {"value": min(value, 100), "muted": muted,
            "label": "음소거" if muted else f"{value}%", "available": bool(match)}


def battery():
    for path in sorted(BATTERIES.iterdir()):
        try:
            if (path / "type").read_text().strip() != "Battery":
                continue
            value = int((path / "capacity").read_text())
            state = (path / "status").read_text().strip()
            return {"value": value, "label": f"{value}%", "detail": {
                "Charging": "충전 중", "Full": "충전 완료", "Discharging": "배터리 사용 중",
                "Not charging": "전원 연결됨"}.get(state, "배터리"), "available": True}
        except (OSError, ValueError):
            continue
    return {"value": 100, "label": "AC", "detail": "외부 전원", "available": False}


def bluetooth_batteries():
    """Read connected BlueZ devices; use UPower only if Battery1 is absent."""
    global SYSTEM_BUS
    try:
        if SYSTEM_BUS is None:
            SYSTEM_BUS = dbus.SystemBus()
        objects = dbus.Interface(SYSTEM_BUS.get_object('org.bluez', '/'),
                                 'org.freedesktop.DBus.ObjectManager').GetManagedObjects(timeout=1)
        powered = any(bool(interfaces.get('org.bluez.Adapter1', {}).get('Powered', False))
                      for interfaces in objects.values())
        devices = []
        for path, interfaces in objects.items():
            device = interfaces.get('org.bluez.Device1', {})
            if not device.get('Connected', False):
                continue
            value = interfaces.get('org.bluez.Battery1', {}).get('Percentage')
            source = 'BlueZ'
            if value is None:
                # Some devices expose their battery through UPower instead.
                try:
                    power = dbus.Interface(SYSTEM_BUS.get_object('org.freedesktop.UPower',
                                           '/org/freedesktop/UPower'), 'org.freedesktop.UPower')
                    for power_path in power.EnumerateDevices(timeout=0.5):
                        props = dbus.Interface(SYSTEM_BUS.get_object('org.freedesktop.UPower', power_path),
                                               'org.freedesktop.DBus.Properties').GetAll(
                                                   'org.freedesktop.UPower.Device', timeout=0.3)
                        if str(props.get('NativePath', '')) == str(path) and props.get('IsPresent', False):
                            value = props.get('Percentage')
                            source = 'UPower'
                            break
                except dbus.DBusException:
                    pass
            known = value is not None
            percent = max(0, min(100, round(float(value)))) if known else 0
            name = str(device.get('Alias') or device.get('Name') or '블루투스 기기')[:80]
            icon = {'input-mouse': 'mouse', 'input-keyboard': 'keyboard',
                    'audio-headphones': 'headphones', 'audio-headset': 'headphones',
                    'phone': 'phone', 'computer': 'laptop'}.get(str(device.get('Icon', '')), 'bluetooth')
            devices.append({'name': name, 'value': percent, 'known': known, 'icon': icon,
                            'label': f'{percent}%' if known else '잔량 정보 없음',
                            'low': known and percent <= 20,
                            'tooltip': f'{name} · {source}에서 보고한 배터리 잔량' if known
                                       else f'{name} · 연결됨, 기기가 배터리 정보를 제공하지 않음'})
        devices.sort(key=lambda item: item['name'].casefold())
        return {'available': True, 'powered': powered, 'count': len(devices), 'devices': devices,
                'empty': '연결된 블루투스 기기 없음' if powered else '블루투스 꺼짐'}
    except (dbus.DBusException, ValueError, TypeError):
        SYSTEM_BUS = None
        return {'available': False, 'powered': False, 'count': 0, 'devices': [],
                'empty': '블루투스 정보를 읽을 수 없음'}


def cpu_times():
    parts = [int(v) for v in Path("/proc/stat").read_text().splitlines()[0].split()[1:9]]
    return sum(parts), parts[3] + parts[4]


def calendar_data(now):
    weeks = calendar.Calendar(firstweekday=calendar.SUNDAY).monthdatescalendar(now.year, now.month)
    return {"month": f"{now.year}년 {now.month}월", "weeks": [[{
        "label": str(day.day),
        "class": "day today" if day == now.date() else "day outside" if day.month != now.month else "day weekend" if day.weekday() > 4 else "day"
    } for day in week] for week in weeks]}


def snapshot(previous):
    now = dt.datetime.now().astimezone()
    current = cpu_times()
    total = current[0] - previous[0]
    idle = current[1] - previous[1]
    cpu = max(0, min(100, round(100 * (total - idle) / total))) if total else 0
    mem = {line.split(':')[0]: int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()}
    used = mem['MemTotal'] - mem['MemAvailable']
    disk = shutil.disk_usage(Path.home())
    _, music = media()
    result = {
        "time": now.strftime("%H:%M"), "date": now.strftime("%a, %b %d"),
        "zone": "Local time", "zone_detail": now.tzname() or "System timezone",
        "calendar": calendar_data(now),
        "cpu": cpu, "memory": round(used / mem['MemTotal'] * 100),
        "memory_text": f"{used / 1048576:.1f} / {mem['MemTotal'] / 1048576:.0f} GB",
        "disk": round(disk.used / disk.total * 100), "disk_text": f"{disk.free / 1073741824:.0f} GB 여유",
        "battery": battery(), "bluetooth": bluetooth_batteries(), "sound": sound(), "music": music}
    battery_info=result['battery']
    devices=[{'name':'이 PC','value':battery_info.get('value',0),'known':battery_info.get('available',False),
              'label':battery_info.get('label','—'),'icon':'laptop','detail':battery_info.get('detail',''),
              'low':battery_info.get('available',False) and battery_info.get('value',0)<=20,'primary':True}]
    devices += [{**device,'primary':False,'detail':'연결됨' if device['known'] else '잔량 정보 없음'} for device in result['bluetooth']['devices']]
    result.update(battery_devices=devices,battery_rows2=[devices[i:i+2] for i in range(0,len(devices),2)],
                  battery_rows3=[devices[i:i+3] for i in range(0,len(devices),3)])
    return current,result


def action(name):
    if name in ("play", "previous", "next"):
        obj, info = media(artwork=False)
        key = {"play": "can_play", "previous": "can_previous", "next": "can_next"}[name]
        if obj is not None and info[key]:
            method = {"play": "PlayPause", "previous": "Previous", "next": "Next"}[name]
            getattr(dbus.Interface(obj, PLAYER), method)(timeout=1)
    elif name == "mute":
        command(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])
    elif name in ("quieter", "louder"):
        current = sound()
        if current["available"]:
            value = min(100, max(0, current["value"] + (5 if name == "louder" else -5)))
            command(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{value}%"])


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "action":
            action(sys.argv[2])
        else:
            previous = cpu_times()
            while True:
                previous, data = snapshot(previous)
                print(json.dumps(data, ensure_ascii=False), flush=True)
                if len(sys.argv) > 1 and sys.argv[1] == "once":
                    break
                time.sleep(3)
    except (BrokenPipeError, KeyboardInterrupt):
        pass
    except dbus.DBusException as exc:
        print(f"Media control unavailable: {exc}", file=sys.stderr)
