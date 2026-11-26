#!/usr/bin/python3
"""Restore saved widgets once the login display and window manager are ready."""
import datetime as dt
import fcntl
import os
from pathlib import Path
import subprocess
import time


def display_ready():
    # Do not initialize GTK before the login display is ready.
    try:
        display = subprocess.run(
            ['/usr/bin/xdpyinfo'], stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=3)
        if display.returncode:
            return False
        manager = subprocess.run(
            ['/usr/bin/xprop', '-root', '_NET_SUPPORTING_WM_CHECK'],
            capture_output=True, text=True, timeout=3)
        return (manager.returncode == 0 and 'window id # 0x' in manager.stdout
                and not manager.stdout.rstrip().endswith('0x0'))
    except (OSError, subprocess.TimeoutExpired):
        return False


def main():
    config = Path(os.environ.get('EWW_WIDGET_CONFIG', Path(__file__).resolve().parent.parent))
    cache = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'ubuntu-widget'
    cache.mkdir(parents=True, exist_ok=True)
    os.environ['GDK_BACKEND'] = 'x11'
    with (cache / 'autostart.lock').open('a') as lock, (cache / 'autostart.log').open('a', buffering=1) as log:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0

        def record(message):
            print(f'{dt.datetime.now().isoformat(timespec="seconds")} {message}', file=log)

        deadline = time.monotonic() + 90
        record('Waiting for the X11 login display and window manager.')
        while time.monotonic() < deadline:
            if display_ready():
                try:
                    for script, args in [('start-service.py', []), ('windows.py', ['open'])]:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise subprocess.TimeoutExpired(script, 0)
                        subprocess.run(['/usr/bin/python3', str(config / 'scripts' / script), *args],
                                       stdout=log, stderr=log, timeout=min(30, remaining), check=True)
                    record('Saved widgets restored successfully.')
                    return 0
                except (OSError, subprocess.SubprocessError) as exc:
                    record(f'Widget startup failed: {exc}; retrying.')
            time.sleep(2)
        record('Widget startup timed out; see daemon.log in this directory.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
