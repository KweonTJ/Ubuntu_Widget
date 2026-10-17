#!/usr/bin/python3
"""Populate/update one user's configuration without replacing their saved state."""
import fcntl
import hashlib
import os
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parent.parent
STATE = {'positions.json', 'hidden-widgets.json', 'enabled-widgets.json',
         'widget-settings.json', 'connections.json', 'web-widgets.json',
         'web-windows.yuck', 'glass-settings.json', 'theme-mode',
         'glass-compositor-state.json', 'linked-apps.json', 'widget-stacks.json'}
MARKER = '.ubuntu-widget-package'


def initialize(config, template=None, force=False):
    template = template or ROOT / 'config'
    config = Path(config)
    config.mkdir(parents=True, exist_ok=True, mode=0o700)
    # The lock is outside the configuration so a failed first run does not make
    # an unrelated directory look like an installation owned by this package.
    with (config.parent / '.ubuntu-widget-initialize.lock').open('a') as lock:
        os.chmod(lock.name, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        if any(config.iterdir()) and not (config / MARKER).is_file():
            raise ValueError(f'{config} already contains an unrecognized installation. Move it aside before installing.')
        files = sorted(p for p in template.rglob('*') if p.is_file()
                       and '__pycache__' not in p.parts and p.suffix != '.pyc')
        digest = hashlib.sha256()
        for source in files:
            digest.update(source.relative_to(template).as_posix().encode() + b'\0')
            digest.update(source.read_bytes())
        stamp = 'Ubuntu Widget templates sha256:' + digest.hexdigest() + '\n'
        marker = config / MARKER
        if not force and marker.exists() and marker.read_text() == stamp:
            if all((config / p.relative_to(template)).is_file() for p in files):
                return
        if not marker.exists():
            marker.write_text('Ubuntu Widget initialization pending\n')
        for source in files:
            relative = source.relative_to(template)
            target = config / relative
            if relative.as_posix() in STATE and target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix='.update-', dir=target.parent)
            os.close(fd)
            try:
                shutil.copyfile(source, temporary)
                os.chmod(temporary, 0o755 if os.access(source, os.X_OK) else 0o600)
                os.replace(temporary, target)
            finally:
                Path(temporary).unlink(missing_ok=True)
        marker.write_text(stamp)


if __name__ == '__main__':
    try:
        initialize(Path(os.environ.get('EWW_WIDGET_CONFIG',
                   str(Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'ubuntu-widget'))))
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc))
