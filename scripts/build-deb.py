#!/usr/bin/python3
"""Build an amd64 Debian package from the patched engine and clean templates."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def build(binary, output, revision='1'):
    if subprocess.check_output(['dpkg', '--print-architecture'], text=True).strip() != 'amd64':
        raise ValueError('This release builder currently supports amd64 only.')
    version = (ROOT / 'VERSION').read_text().strip() + '-' + revision
    if not re.fullmatch(r'[0-9][A-Za-z0-9.+~:-]*', version):
        raise ValueError('Invalid Debian package version.')
    data = binary.read_bytes()
    if not data.startswith(b'\x7fELF') or b'eww-native-draggable' not in data or b'resize-min-width' not in data or b'EWW_SOCKET_ID' not in data or b'eww-native-stack-swipe' not in data or b'eww-native-stack-host' not in data:
        raise ValueError('Build the native-controls Eww engine first.')
    if re.search(rb'/(?:home|Users)/[^\s/"\x27]+/', data):
        raise ValueError('Developer home paths found in the engine. Rebuild using scripts/build-eww.sh.')
    notices = ROOT / 'build/rust-licenses'
    if not (notices / 'INDEX.json').is_file():
        raise ValueError('Run scripts/prepare-release-source.py first to collect source and license notices.')
    subprocess.run(['/usr/bin/python3', str(ROOT / 'scripts/check_public.py')], check=True)
    output.mkdir(parents=True, exist_ok=True)
    (ROOT / '.build').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='deb-', dir=ROOT / '.build') as temporary:
        stage = Path(temporary) / 'package'

        def copy(source, relative, executable=False):
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            target.chmod(0o755 if executable else 0o644)

        copy(binary, 'usr/lib/ubuntu-widget/eww', True)
        subprocess.run(['strip', '--strip-unneeded', str(stage / 'usr/lib/ubuntu-widget/eww')], check=True)
        copy(ROOT / 'packaging/ubuntu-widget', 'usr/bin/ubuntu-widget', True)
        copy(ROOT / 'bin/ubuntu-widget', 'usr/share/ubuntu-widget/bin/ubuntu-widget', True)
        copy(ROOT / 'scripts/initialize.py', 'usr/share/ubuntu-widget/scripts/initialize.py')
        copy(ROOT / 'packaging/ubuntu-widget.desktop', 'usr/share/applications/local.ubuntu.WidgetLibrary.desktop')
        copy(ROOT / 'config/assets/widget-gallery.svg', 'usr/share/icons/hicolor/scalable/apps/ubuntu-widget.svg')
        for source in sorted((ROOT / 'config').rglob('*')):
            if source.is_file() and '__pycache__' not in source.parts and source.suffix != '.pyc':
                if source.is_symlink():
                    raise ValueError('Unexpected template symlink: ' + str(source))
                copy(source, 'usr/share/ubuntu-widget/config/' + source.relative_to(ROOT / 'config').as_posix(), os.access(source, os.X_OK))
        for name in ('README.md', 'README.ko.md', 'THIRD_PARTY_NOTICES.md', 'LICENSE', 'VERSION'):
            copy(ROOT / name, 'usr/share/doc/ubuntu-widget/' + ('copyright' if name == 'LICENSE' else name))
        for directory, destination in [('docs', 'docs'), ('LICENSES', 'LICENSES'), ('build/rust-licenses', 'rust-licenses')]:
            for source in sorted((ROOT / directory).rglob('*')):
                if source.is_file():
                    copy(source, 'usr/share/doc/ubuntu-widget/' + destination + '/' + source.relative_to(ROOT / directory).as_posix())
        # Resolve actual ELF requirements, including their minimum symbol versions.
        debian = Path(temporary) / 'debian'
        debian.mkdir()
        (debian / 'control').write_text('Source: ubuntu-widget\nSection: x11\nPriority: optional\nMaintainer: KweonTJ <144107369+KweonTJ@users.noreply.github.com>\n\nPackage: ubuntu-widget\nArchitecture: amd64\nDescription: desktop widget library\n')
        shlibs = subprocess.check_output(['dpkg-shlibdeps', '-O', '-e' + str(stage / 'usr/lib/ubuntu-widget/eww')], cwd=temporary, text=True)
        dependencies = shlibs.strip().removeprefix('shlibs:Depends=')
        runtime = 'python3 (>= 3.10), python3-gi, python3-gi-cairo, python3-cairo, python3-dbus, tzdata, gir1.2-gtk-3.0, gir1.2-webkit2-4.0 | gir1.2-webkit2-4.1, gir1.2-secret-1, gnome-keyring, gsettings-desktop-schemas, dconf-gsettings-backend, librsvg2-common, libx11-6, libxss1, libxtst6, x11-utils, pulseaudio-utils, libnotify-bin, xdg-utils, systemd, dbus-user-session'
        control = stage / 'DEBIAN'
        control.mkdir()
        size = sum(p.stat().st_size for p in stage.rglob('*') if p.is_file())
        (control / 'control').write_text(f'''Package: ubuntu-widget
Version: {version}
Architecture: amd64
Maintainer: KweonTJ <144107369+KweonTJ@users.noreply.github.com>
Section: x11
Priority: optional
Homepage: https://github.com/KweonTJ/Ubuntu_Widget
Installed-Size: {(size + 1023) // 1024}
Depends: {dependencies}, {runtime}
Recommends: fonts-noto-cjk
Suggests: kdeconnect
Description: macOS-inspired desktop widget library for GNOME on Xorg
 Browse 35 widget and website choices with native grid movement, resizing,
 light/dark themes and optional glass effects. Includes the patched Eww engine.
 User data is initialized on first launch, never by a root install script.
 Verified on Ubuntu 22.04 amd64 with GNOME/Xorg. Wayland is unsupported.
''')
        payload = sorted(p for p in stage.rglob('*') if p.is_file() and 'DEBIAN' not in p.relative_to(stage).parts)
        (control / 'md5sums').write_text(''.join(hashlib.md5(p.read_bytes()).hexdigest() + '  ' + p.relative_to(stage).as_posix() + '\n' for p in payload))
        epoch = int(os.environ.get('SOURCE_DATE_EPOCH') or subprocess.check_output(['git', 'log', '-1', '--format=%ct'], cwd=ROOT, text=True))
        for path in stage.rglob('*'):
            if path.is_dir():
                path.chmod(0o755)
            os.utime(path, (epoch, epoch))
        stage.chmod(0o755)
        artifact = output / f'ubuntu-widget_{version}_amd64.deb'
        subprocess.run(['dpkg-deb', '--root-owner-group', '-Zxz', '--build', str(stage), str(artifact)], check=True, env={**os.environ, 'SOURCE_DATE_EPOCH': str(epoch)})
    print(artifact)
    return artifact


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--eww', type=Path, default=ROOT / 'build/eww')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    parser.add_argument('--revision', default='1')
    args = parser.parse_args()
    try:
        build(args.eww.resolve(), args.output.resolve(), args.revision)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, str(exc) + '\n')
