#!/usr/bin/python3
"""Per-user install; preserve user state on upgrades and never touch unrelated Eww."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from initialize import initialize, MARKER, STATE

ROOT=Path(__file__).resolve().parent.parent

def desktop_quote(path):
    # Desktop Entry Exec syntax is not a shell; escape its reserved characters.
    value=str(path).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$').replace('%','%%')
    return '"'+value+'"'

def install(binary,autostart=False):
    home=Path.home();config=Path(os.environ.get('XDG_CONFIG_HOME',home/'.config'))/'ubuntu-widget'
    data=Path(os.environ.get('XDG_DATA_HOME',home/'.local/share'));lib=home/'.local/lib/ubuntu-widget'
    if config.exists() and any(config.iterdir()) and not (config/MARKER).exists():
        raise ValueError(f'{config} already contains an unrecognized installation. Move it aside before installing.')
    if not binary.is_file() or not os.access(binary,os.X_OK):raise ValueError('Build the patched Eww first, or use --eww /path/to/patched/eww.')
    content=binary.read_bytes()
    if b'eww-native-draggable' not in content or b'resize-min-width' not in content:
        raise ValueError('This Eww does not contain the required native move/resize extension. Use scripts/build-eww.sh.')
    config.mkdir(parents=True,exist_ok=True,mode=0o700);lib.mkdir(parents=True,exist_ok=True)
    initialize(config, force=True)
    # Regenerate CSS for the current settings at runtime; the daemon handles this.
    installed_binary=lib/'eww'
    if binary.resolve()!=installed_binary.resolve():shutil.copy2(binary,installed_binary)
    installed_binary.chmod(0o755)
    (home/'.local/bin').mkdir(parents=True,exist_ok=True)
    launcher=home/'.local/bin/ubuntu-widget';shutil.copy2(ROOT/'bin/ubuntu-widget',launcher);launcher.chmod(0o755)
    icon_dir=data/'icons/hicolor/scalable/apps';icon_dir.mkdir(parents=True,exist_ok=True)
    icon=icon_dir/'ubuntu-widget.svg';shutil.copy2(config/'assets/widget-gallery.svg',icon)
    appdir=data/'applications';appdir.mkdir(parents=True,exist_ok=True)
    desktop='''[Desktop Entry]
Version=1.0
Type=Application
Name=Widget Library
Name[ko]=위젯 보관함
Comment=Browse and customize 34 desktop widgets
Comment[ko]=34가지 위젯과 웹사이트 바로가기를 추가합니다
Exec={command} edit
Icon=ubuntu-widget
Terminal=false
Categories=Utility;
Keywords=widget;clock;calendar;weather;
Actions=Toggle;Restore;

[Desktop Action Toggle]
Name=Show or hide widgets
Exec={command} toggle

[Desktop Action Restore]
Name=Restore removed widgets
Exec={command} restore
'''.format(command=desktop_quote(launcher))
    (appdir/'ubuntu-widget.desktop').write_text(desktop)
    if autostart:
        startup=config.parent/'autostart';startup.mkdir(parents=True,exist_ok=True)
        (startup/'ubuntu-widget.desktop').write_text('''[Desktop Entry]
Type=Application
Name=Ubuntu Widget
Exec={command} start
Icon=ubuntu-widget
Terminal=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=8
OnlyShowIn=GNOME;Unity;
'''.format(command=desktop_quote(launcher)))
    print('Installed to '+str(config))
    print('Open Widget Library from the application menu, or run '+str(launcher))
    print('No widgets are added, no accounts are connected, and usage tracking is off on a fresh install.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--eww',type=Path,default=ROOT/'build/eww',help='Patched Eww built with native controls')
    parser.add_argument('--autostart',action='store_true',help='Start previously added widgets after login')
    args=parser.parse_args()
    try:install(args.eww,args.autostart)
    except (ValueError,OSError) as exc:parser.exit(1,str(exc)+'\n')
