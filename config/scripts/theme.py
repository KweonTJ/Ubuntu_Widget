#!/usr/bin/python3
"""Emit Eww appearance when GNOME settings or the local override change."""
from pathlib import Path
from gi.repository import Gio, GLib
import glass_effect as glass
import widget_store as store

CONFIG = store.CONFIG
settings = Gio.Settings.new('org.gnome.desktop.interface')

def current():
    try:
        override = (CONFIG / 'theme-mode').read_text().strip()
    except OSError:
        override = 'auto'
    if override in ('light', 'dark'):
        return override
    scheme = settings.get_string('color-scheme')
    if scheme == 'prefer-dark':
        return 'dark'
    if scheme == 'prefer-light':
        return 'light'
    return 'dark' if 'dark' in settings.get_string('gtk-theme').lower() else 'light'

def emit(*_):
    value = current()
    options=glass.settings();items=store.catalogue()
    glass.sync_compositor(any(glass.enabled(w,options) for w in items))
    # Write only actual changes so config reload cannot form a loop.
    store.atomic_text('glass.scss',glass.stylesheet(value,items,options))
    palette='@import "themes/dark";\n' if value=='dark' else '/* Light palette: base colors. */\n'
    if options['enabled']:palette+='@import "glass";\n'
    store.atomic_text('appearance.scss',palette)
    print(value,flush=True)

def main():
    settings.connect('changed::color-scheme',emit);settings.connect('changed::gtk-theme',emit)
    monitor=Gio.File.new_for_path(str(CONFIG)).monitor_directory(Gio.FileMonitorFlags.NONE,None)
    pending=None
    def changed(_monitor,file,other,_event):
        nonlocal pending
        if any(f and f.get_basename() in ('theme-mode','glass-settings.json','web-widgets.json') for f in (file,other)):
            if pending:GLib.source_remove(pending)
            def update():
                nonlocal pending
                pending=None;emit();return False
            pending=GLib.timeout_add(80,update)
    monitor.connect('changed',changed);emit();GLib.MainLoop().run()

if __name__=='__main__':
    try:main()
    except (BrokenPipeError,KeyboardInterrupt):pass
