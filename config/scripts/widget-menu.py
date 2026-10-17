#!/usr/bin/python3
"""Desktop-widget context menu, started only by an explicit right click."""
import subprocess,sys
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk
import widget_store as store
widget_id=sys.argv[1];item=store.find(widget_id)
menu=Gtk.Menu()
def action(fn):
    try:fn()
    except Exception as exc:
        d=Gtk.MessageDialog(message_type=Gtk.MessageType.ERROR,buttons=Gtk.ButtonsType.CLOSE,text='위젯을 변경하지 못했습니다.');d.format_secondary_text(str(exc));d.run();d.destroy()
    Gtk.main_quit()
def add(title,fn):
    m=Gtk.MenuItem(label=title);m.connect('activate',lambda *_:action(fn));menu.append(m)
def gallery():subprocess.Popen(['/usr/bin/python3',str(store.CONFIG/'scripts/manager-launch.py'),'select',widget_id],start_new_session=True)
add('위젯 보관함…',gallery)
if item.get('configurable'):add('내용·시간 설정…',gallery)
menu.append(Gtk.SeparatorMenuItem())
for key,name in [('small','작게'),('medium','중간'),('large','크게')]:add(name,lambda k=key:store.show(widget_id,k))
if item['kind']=='web':add('웹사이트 열기',lambda:store.launch_web(widget_id))
menu.append(Gtk.SeparatorMenuItem());add('바탕화면에서 제거',lambda:store.remove(widget_id))
menu.connect('selection-done',lambda *_:Gtk.main_quit());menu.show_all();menu.popup(None,None,None,None,3,Gtk.get_current_event_time());Gtk.main()
