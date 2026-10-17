#!/usr/bin/python3
"""A small file picker and device chooser; nothing is sent before Send is clicked."""
import os
from pathlib import Path
import sys
import threading

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib
GLib.set_prgname('ubuntu-widget')
from gi.repository import Gtk, Gdk, Gio, Pango
import kdeconnect_widget as sharing


class Transfer(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=os.environ.get('EWW_WIDGET_APP_ID', 'local.ubuntu.WidgetLibrary') + '.Transfer')
        self.window = None
        self.files = []
        self.busy = False
        self.refreshing = False

    def do_activate(self):
        if self.window is None:
            self.build()
        self.window.present()

    def build(self):
        self.files = []
        self.window = Gtk.ApplicationWindow(application=self, title='KDE Connect · 파일 보내기')
        self.window.set_default_size(500, 400)
        self.window.set_icon_from_file(str(Path(__file__).resolve().parent.parent / 'assets/widget-gallery.svg'))
        self.window.connect('destroy', self.closed)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin=20)
        self.window.add(root)
        title = Gtk.Label(xalign=0)
        title.set_markup('<b>KDE Connect · 파일 보내기</b>')
        root.pack_start(title, False, False, 0)
        row = Gtk.Box(spacing=8)
        self.devices = Gtk.ComboBoxText()
        self.devices.connect('changed', lambda *_: self.update_send())
        row.pack_start(self.devices, True, True, 0)
        refresh = Gtk.Button(label='새로고침')
        refresh.connect('clicked', lambda *_: self.refresh())
        row.pack_end(refresh, False, False, 0)
        root.pack_start(row, False, False, 0)
        hint = Gtk.Label(label='파일을 선택하거나 이 창으로 끌어 놓으세요.\n여러 파일을 한 번에 보낼 수 있습니다.', xalign=0)
        hint.set_line_wrap(True)
        root.pack_start(hint, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.file_list = Gtk.Label(label='선택한 파일 없음', xalign=0, yalign=0)
        self.file_list.set_line_wrap(True)
        self.file_list.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.file_list.set_selectable(True)
        scroll.add(self.file_list)
        root.pack_start(scroll, True, True, 0)
        self.status = Gtk.Label(label='연결된 기기를 확인하는 중…', xalign=0)
        self.status.set_line_wrap(True)
        root.pack_start(self.status, False, False, 0)
        row = Gtk.Box(spacing=8)
        self.choose = Gtk.Button(label='파일 선택…')
        self.choose.connect('clicked', lambda *_: self.pick())
        row.pack_start(self.choose, False, False, 0)
        settings = Gtk.Button(label='기기 연결·설정')
        settings.connect('clicked', lambda *_: self.settings())
        row.pack_start(settings, False, False, 0)
        self.send = Gtk.Button(label='보내기')
        self.send.get_style_context().add_class('suggested-action')
        self.send.connect('clicked', lambda *_: self.submit())
        row.pack_end(self.send, False, False, 0)
        root.pack_end(row, False, False, 0)
        self.window.drag_dest_set(Gtk.DestDefaults.ALL, [Gtk.TargetEntry.new('text/uri-list', 0, 0)], Gdk.DragAction.COPY)
        self.window.connect('drag-data-received', self.dropped)
        self.window.show_all()
        self.update_send()
        self.refresh()
        self.timer = GLib.timeout_add_seconds(5, self.tick)

    def closed(self, *_):
        self.window = None
        if getattr(self, 'timer', None):
            GLib.source_remove(self.timer)
            self.timer = None

    def update_send(self):
        self.send.set_sensitive(bool(self.files and self.devices.get_active_id()) and not self.busy)

    def refresh(self):
        if self.refreshing or self.busy:
            return
        self.refreshing = True
        def worker():
            try:
                rows = sharing.Client().devices()
                error = None
            except Exception:
                rows, error = [], 'KDE Connect를 실행하고 기기를 연결해 주세요.'
            GLib.idle_add(done, rows, error)
        def done(rows, error):
            self.refreshing = False
            if self.window is None:
                return False
            selected = self.devices.get_active_id()
            self.devices.remove_all()
            for item in rows:
                self.devices.append(item['id'], item['name'])
            if selected in {item['id'] for item in rows}:
                self.devices.set_active_id(selected)
            elif rows:
                self.devices.set_active(0)
            if error or not rows:
                self.status.set_text(error or '연결된 공유 기기가 없습니다. 같은 Wi-Fi에서 기기 연결과 파일 공유를 확인하세요.')
            elif not self.files and self.status.get_text().startswith(('연결된', '연결을', 'KDE Connect')):
                self.status.set_text(f'{len(rows)}대 연결됨 · 파일을 선택하세요.')
            self.update_send()
            return False
        threading.Thread(target=worker, daemon=True).start()

    def tick(self):
        if self.window is None:
            return False
        self.refresh()
        return True

    def set_files(self, filenames):
        if self.busy:
            return
        self.files = list(dict.fromkeys(str(Path(p).resolve()) for p in filenames))
        self.file_list.set_text('\n'.join(Path(p).name for p in self.files) or '선택한 파일 없음')
        self.status.set_text(f'{len(self.files)}개 파일 선택됨 · 기기를 확인하고 보내기를 누르세요.')
        self.update_send()

    def pick(self):
        chooser = Gtk.FileChooserNative.new('보낼 파일 선택', self.window, Gtk.FileChooserAction.OPEN, '선택', '취소')
        chooser.set_select_multiple(True)
        if chooser.run() == Gtk.ResponseType.ACCEPT:
            self.set_files(chooser.get_filenames())
        chooser.destroy()

    def dropped(self, _window, context, _x, _y, data, _info, timestamp):
        files = [Gio.File.new_for_uri(uri).get_path() for uri in data.get_uris()]
        valid = bool(files) and all(files) and not self.busy
        if valid:
            self.set_files(files)
        Gtk.drag_finish(context, valid, False, timestamp)

    def settings(self):
        try:
            sharing.open_settings()
        except Exception as exc:
            self.status.set_text(str(exc))

    def submit(self):
        if self.busy or not self.files or not self.devices.get_active_id():
            return
        target, files = self.devices.get_active_id(), list(self.files)
        self.busy = True
        self.update_send()
        self.choose.set_sensitive(False)
        self.devices.set_sensitive(False)
        self.status.set_text('KDE Connect에 전송을 요청하는 중…')
        # Keep the application alive if the user closes the window during a request.
        self.hold()
        def worker():
            try:
                count = sharing.Client().send(target, files)
                message = f'{count}개 파일 전송 요청됨 · 완료 여부는 KDE Connect 알림에서 확인하세요.'
                success = True
            except Exception as exc:
                message, success = '전송 요청 실패: ' + str(exc), False
            GLib.idle_add(done, message, success)
        def done(message, success):
            self.busy = False
            if self.window is not None:
                if success:
                    self.set_files([])
                self.status.set_text(message)
                self.choose.set_sensitive(True)
                self.devices.set_sensitive(True)
                self.update_send()
            self.release()
            return False
        threading.Thread(target=worker, daemon=True).start()


if __name__ == '__main__':
    raise SystemExit(Transfer().run(sys.argv))
