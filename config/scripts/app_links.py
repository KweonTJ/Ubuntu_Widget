#!/usr/bin/python3
"""Read an explicitly selected Obsidian note and open the user's installed apps."""
import json
import os
from pathlib import Path
import re
import sys
import urllib.parse
import widget_store as store

STATE = 'linked-apps.json'


def vaults():
    home = Path.home()
    candidates = [Path(os.environ.get('XDG_CONFIG_HOME', home/'.config'))/'obsidian/obsidian.json',
                  home/'.var/app/md.obsidian.Obsidian/config/obsidian/obsidian.json']
    for path in candidates:
        try:
            data = json.loads(path.read_text())
            return [Path(row['path']).resolve() for row in data.get('vaults', {}).values() if Path(row.get('path', '')).is_dir()]
        except (OSError, ValueError, KeyError):
            continue
    return []


def selected_note():
    text = store.read_json(STATE, {}).get('obsidian', {}).get('note', '')
    return Path(text).expanduser().resolve() if text else None


def save_note(filename):
    path = Path(filename).expanduser().resolve(strict=True)
    if path.suffix.lower() != '.md' or not path.is_file():
        raise ValueError('Obsidian의 Markdown(.md) 노트를 선택하세요.')
    if not any(path.is_relative_to(vault) for vault in vaults()):
        raise ValueError('Obsidian에 등록된 보관함 안의 노트를 선택하세요.')
    with store.locked():
        state = store.read_json(STATE, {})
        state['obsidian'] = {'note': str(path)}
        store.atomic_json(STATE, state)


def snapshot():
    result = {'obsidian_title': 'Obsidian', 'obsidian_text': '표시할 노트를 선택하세요.', 'obsidian_connected': False}
    try:
        path = selected_note()
        if path is None:
            return result
        if not any(path.is_relative_to(vault) for vault in vaults()):
            result['obsidian_text'] = '등록된 보관함에서 노트를 다시 선택하세요.'
            return result
        with path.open() as file:
            text = file.read(65536)
        text = re.sub(r'\A---\s*\n.*?\n---\s*\n', '', text, count=1, flags=re.S)
        title = re.search(r'^#\s+(.+)$', text, flags=re.M)
        result['obsidian_title'] = title[1] if title else path.stem
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.M)
        text = re.sub(r'!\[\[.*?\]\]|!\[.*?\]\(.*?\)', '', text)
        text = re.sub(r'\[\[([^]|]+)(?:\|([^]]+))?\]\]', lambda match: match[2] or match[1], text)
        text = re.sub(r'\[([^]]+)\]\([^)]*\)', r'\1', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'(?m)^```.*$', '', text)
        text = text.replace('**', '').replace('`', '')
        result.update(obsidian_text=text.strip()[:4000] or '비어 있는 노트입니다.', obsidian_connected=True)
    except (OSError, ValueError):
        result['obsidian_text'] = '노트를 읽을 수 없습니다. 연결 설정에서 다시 선택하세요.'
    return result


def open_app(name):
    from gi.repository import Gio
    if name == 'obsidian':
        path = selected_note()
        uri = 'obsidian://open' + ('?'+urllib.parse.urlencode({'path': str(path)}) if path else '')
        Gio.AppInfo.launch_default_for_uri(uri, None)
    elif name == 'todomate':
        for app in Gio.AppInfo.get_all():
            normalized = ''.join(app.get_name().casefold().split())
            if normalized in ('todomate', '투두메이트'):
                app.launch([], None)
                return
        Gio.AppInfo.launch_default_for_uri('https://www.todomate.net/', None)
    else:
        raise ValueError('알 수 없는 앱입니다.')


def choose_note(parent):
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    chooser = Gtk.FileChooserNative.new('위젯에 표시할 Obsidian 노트', parent, Gtk.FileChooserAction.OPEN, '연결', '취소')
    file_filter = Gtk.FileFilter();file_filter.set_name('Obsidian 노트 (.md)');file_filter.add_pattern('*.md');chooser.add_filter(file_filter)
    roots = vaults()
    if roots:chooser.set_current_folder(str(roots[0]))
    if chooser.run() == Gtk.ResponseType.ACCEPT:
        try:save_note(chooser.get_filename())
        except (OSError, ValueError) as exc:
            dialog = Gtk.MessageDialog(transient_for=parent, modal=True, message_type=Gtk.MessageType.ERROR,
                                       buttons=Gtk.ButtonsType.CLOSE, text='노트를 연결하지 못했습니다.')
            dialog.format_secondary_text(str(exc));dialog.run();dialog.destroy()
    chooser.destroy()


if __name__ == '__main__':
    if len(sys.argv)==3 and sys.argv[1]=='open':open_app(sys.argv[2])
    else:raise SystemExit('Usage: app_links.py open obsidian|todomate')
