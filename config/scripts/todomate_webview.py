#!/usr/bin/python3
"""Keep one official todomate session and publish a minimal local task snapshot.

The compatibility adapter uses the Firebase client already loaded by the official
page. Passwords/tokens stay in WebKit. Only today's own task fields leave the page.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import urllib.parse

import gi
gi.require_version('Gtk', '3.0')
try:gi.require_version('WebKit2', '4.1')
except ValueError:gi.require_version('WebKit2', '4.0')
from gi.repository import GLib
GLib.set_prgname('ubuntu-widget')
from gi.repository import Gtk, Gio, WebKit2
import widget_store as store
import todomate

URL = 'https://www.todomate.net/'


class Todomate(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=os.environ.get('EWW_WIDGET_APP_ID', 'local.ubuntu.WidgetLibrary')+'.Todomate',
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.window = None
        self.plugs = {}
        self.views = []
        self.context = None
        self.main_view = None
        self.held = False
        self.state = {'status':'loading','tasks':[],'pending':[],'date':'','error':''}
        self.load_started = time.monotonic()

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.profile = store.CONFIG/'.web-profile/todomate'
        self.profile.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.profile, 0o700)
        manager = WebKit2.WebsiteDataManager(base_data_directory=str(self.profile/'data'), base_cache_directory=str(self.profile/'cache'))
        self.context = WebKit2.WebContext.new_with_website_data_manager(manager)
        self.context.get_cookie_manager().set_persistent_storage(str(self.profile/'cookies.sqlite'), WebKit2.CookiePersistentStorage.SQLITE)

    def do_command_line(self, line):
        args = line.get_arguments()[1:]
        if len(args)==2 and args[0]=='embed' and args[1].isdigit():
            self.embed(int(args[1]));return 0
        if not self.held:self.hold();self.held=True
        self.ensure_view()
        if args and args[0]=='sync':return 0
        if len(args)==4 and args[0]=='toggle':
            task_id,done,date=args[1:]
            if not todomate.ID.fullmatch(task_id) or done not in ('true','false') or date!=self.state.get('date'):return 1
            script='window.uwTodomate && window.uwTodomate.toggle('+','.join((json.dumps(task_id),done,json.dumps(date)))+');'
            self.main_view.run_javascript(script,None,None)
        else:self.activate()
        return 0

    def view(self):
        view = WebKit2.WebView.new_with_context(self.context)
        view.set_size_request(0, 0)
        view.set_zoom_level(.85)
        view.get_settings().set_enable_javascript(True)
        view.get_settings().set_javascript_can_open_windows_automatically(True)
        view.connect('create', self.popup)
        view.connect('permission-request', lambda _v, request: (request.deny(), True)[1])
        view.connect('destroy', lambda current: self.views.remove(current) if current in self.views else None)
        self.views.append(view)
        return view

    def popup(self, related, _action):
        view = WebKit2.WebView.new_with_related_view(related)
        window = Gtk.ApplicationWindow(application=self, title='todomate · 로그인')
        window.set_default_size(900, 700);window.add(view)
        view.connect('close', lambda *_: window.destroy())
        window.show_all();return view

    def embed(self, xid):
        # Generic XEmbed remains available for engine regression tests.
        if xid in self.plugs:return
        plug = Gtk.Plug.new(xid);self.add_window(plug)
        view = self.view();plug.add(view);self.plugs[xid] = plug
        plug.connect('destroy', lambda *_: self.plugs.pop(xid, None))
        plug.show_all();view.load_uri(URL)

    def ensure_view(self):
        if self.main_view is not None:return
        self.offscreen=Gtk.OffscreenWindow();self.offscreen.set_default_size(1100,900)
        view=self.main_view=self.view()
        manager=view.get_user_content_manager();manager.register_script_message_handler('uwTodomate')
        manager.connect('script-message-received::uwTodomate',self.received)
        manager.add_script(WebKit2.UserScript.new((store.CONFIG/'scripts/todomate_bridge.js').read_text(),
                           WebKit2.UserContentInjectedFrames.TOP_FRAME,WebKit2.UserScriptInjectionTime.END,None,None))
        view.connect('load-changed',self.load_changed)
        view.connect('load-failed',self.load_failed)
        view.connect('web-process-terminated',lambda *_:self.error('web_process_terminated'))
        self.offscreen.add(view);self.offscreen.show_all();view.load_uri(URL)
        self.publish();GLib.timeout_add_seconds(5,self.check_timeout)

    def load_changed(self,view,event):
        if event==WebKit2.LoadEvent.STARTED:
            self.load_started=time.monotonic();self.state.update(status='loading',error='');self.publish()

    def load_failed(self,*_):
        self.error('load_failed');return False

    def error(self,code):
        self.state.update(status='error',error=code);self.publish()

    def check_timeout(self):
        if self.state['status'] in ('loading','syncing') and time.monotonic()-self.load_started>45:self.error('load_timeout')
        return True

    def received(self,_manager,result):
        if urllib.parse.urlsplit(self.main_view.get_uri() or '').hostname not in ('www.todomate.net','todomate.net'):return
        try:
            value=json.loads(result.get_js_value().to_string())
            if value.get('status') not in ('loading','syncing','ready','cached','signed_out','error'):return
            if not isinstance(value.get('tasks'),list) or len(value['tasks'])>2000:return
            # Validate before anything is persisted; raw page/credential objects are never written.
            normalized=todomate.normalize({**value,'updated':time.time()})
            tasks=[{k:row[k] for k in ('id','text','done')} for row in normalized['todomate_tasks']]
            self.state={'status':value['status'],'tasks':tasks,'pending':[t['id'] for t in normalized['todomate_tasks'] if t['pending']],
                        'date':str(value.get('date',''))[:10],'error':value.get('error','') if value.get('error') in todomate.ERRORS else 'write_failed' if value['status']=='error' else ''}
            self.publish()
        except (ValueError,KeyError,TypeError):self.error('schema_changed')

    def publish(self):
        value={**self.state,'updated':time.time()}
        fd,name=tempfile.mkstemp(prefix='.state-',dir=self.profile)
        try:
            with os.fdopen(fd,'w') as file:json.dump(value,file,ensure_ascii=False)
            os.replace(name,self.profile/'widget-state.json')
        finally:
            if os.path.exists(name):os.unlink(name)
        if self.window:
            normalized=todomate.normalize(value)
            self.status.set_text('연결됨 · '+normalized['todomate_count'] if normalized['todomate_ready'] else normalized['todomate_message'])
            self.progress.set_visible(self.state['status'] in ('loading','syncing'))

    def do_activate(self):
        self.ensure_view()
        if self.window is None:
            self.window=Gtk.ApplicationWindow(application=self,title='todomate 연결')
            self.window.set_default_size(1000,760);self.window.set_icon_from_file(str(store.CONFIG/'assets/widget-gallery.svg'))
            header=Gtk.HeaderBar(title='todomate');header.set_show_close_button(True)
            self.window.set_titlebar(header)
            retry=Gtk.Button.new_from_icon_name('view-refresh-symbolic',Gtk.IconSize.BUTTON);retry.set_tooltip_text('다시 연결')
            retry.connect('clicked',lambda *_:self.main_view.reload());header.pack_end(retry)
            box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.status=Gtk.Label(xalign=0,margin=12);box.pack_start(self.status,False,False,0)
            self.progress=Gtk.ProgressBar();self.progress.set_fraction(.35);box.pack_start(self.progress,False,False,0)
            self.offscreen.remove(self.main_view);box.pack_start(self.main_view,True,True,0)
            self.window.add(box);self.window.connect('delete-event',self.close_connection)
            self.window.show_all();self.publish()
        self.window.present()

    def close_connection(self,window,_event):
        parent=self.main_view.get_parent();parent.remove(self.main_view)
        self.offscreen.add(self.main_view);self.offscreen.show_all()
        self.window=None;window.destroy();return True


if __name__ == '__main__':
    args=list(sys.argv)
    if len(args)==2 and args[1]=='embed':args.append(os.environ['EWW_SOCKET_ID'])
    raise SystemExit(Todomate().run(args))
