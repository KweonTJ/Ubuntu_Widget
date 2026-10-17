#!/usr/bin/python3
"""Remove installed program files; keep user settings, data and keyring entries."""
import os
from pathlib import Path
import shutil
import subprocess
home=Path.home();launcher=home/'.local/bin/ubuntu-widget'
if launcher.is_file():subprocess.run([str(launcher),'hide'],check=False)
data=Path(os.environ.get('XDG_DATA_HOME',home/'.local/share'))
config=Path(os.environ.get('XDG_CONFIG_HOME',home/'.config'))
for target in [launcher,data/'applications/local.ubuntu.WidgetLibrary.desktop',data/'applications/ubuntu-widget.desktop',data/'icons/hicolor/scalable/apps/ubuntu-widget.svg',config/'autostart/ubuntu-widget.desktop']:
    target.unlink(missing_ok=True)
lib=home/'.local/lib/ubuntu-widget'
if lib.is_dir():shutil.rmtree(lib)
print('Program files removed. Your configuration, usage data and keyring entries were preserved.')
print('Disconnect accounts in the app before uninstalling if you want to delete its stored API keys.')
