#!/usr/bin/python3
"""Publish actual logical window widths for responsive widget layouts."""
import ctypes as C
import ctypes.util
import json
import time
from pathlib import Path
import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GLib
from responsive import metrics

X = C.CDLL(ctypes.util.find_library('X11'))
P, U, I = C.c_void_p, C.c_ulong, C.c_int

def bind(name, result, args):
    fn = getattr(X, name)
    fn.restype, fn.argtypes = result, args
    return fn
bind('XOpenDisplay', P, [C.c_char_p])
bind('XDefaultRootWindow', U, [P])
bind('XInternAtom', U, [P,C.c_char_p,I])
bind('XGetWindowProperty', I, [P,U,U,C.c_long,C.c_long,I,U,C.POINTER(U),C.POINTER(I),C.POINTER(U),C.POINTER(U),C.POINTER(P)])
bind('XGetGeometry', I, [P,U,C.POINTER(U),C.POINTER(I),C.POINTER(I),C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.POINTER(C.c_uint)])
bind('XFree', I, [P])
bind('XMoveWindow', I, [P,U,I,I])
bind('XFlush', I, [P])
bind('XSendEvent', I, [P,U,I,C.c_long,P])
bind('XQueryPointer', I, [P,U,C.POINTER(U),C.POINTER(U),C.POINTER(I),C.POINTER(I),C.POINTER(I),C.POINTER(I),C.POINTER(C.c_uint)])
bind('XQueryTree', I, [P,U,C.POINTER(U),C.POINTER(U),C.POINTER(C.POINTER(U)),C.POINTER(C.c_uint)])
error_type = C.CFUNCTYPE(I, P, P)
ignore_error = error_type(lambda display, event: 0)
bind('XSetErrorHandler', P, [error_type])(ignore_error)
D = X.XOpenDisplay(None)
if not D:
    raise SystemExit('X11 display unavailable')
root = X.XDefaultRootWindow(D)
atoms = {name:X.XInternAtom(D,name.encode(),0) for name in ['_NET_CLIENT_LIST','_NET_WM_NAME','_NET_CLIENT_LIST_STACKING','_NET_WM_WINDOW_TYPE','_NET_WM_WINDOW_TYPE_DESKTOP','_NET_RESTACK_WINDOW']}

def prop(window, name):
    actual,fmt,count,after,data = U(),I(),U(),U(),P()
    X.XGetWindowProperty(D,window,atoms[name],0,16384,0,0,C.byref(actual),C.byref(fmt),C.byref(count),C.byref(after),C.byref(data))
    if not data: return []
    try:
        if fmt.value == 32: return list(C.cast(data,C.POINTER(U))[:count.value])
        if fmt.value == 8: return C.string_at(data,count.value).decode('utf8','replace')
        return []
    finally:
        X.XFree(data)

class EventData(C.Union):
    _fields_=[('l',C.c_long*5),('b',C.c_char*20)]
class ClientEvent(C.Structure):
    _fields_=[('type',I),('serial',U),('send_event',I),('display',P),
              ('window',U),('message_type',U),('format',I),('data',EventData)]
class XEvent(C.Union):
    _fields_=[('client',ClientEvent),('pad',C.c_long*24)]

def keep_widgets_above_desktop(alive):
    """Keep desktop cards clickable above transparent desktop-icon windows.

    DING can remap/raise its monitor-sized desktop window after login, a theme
    reload or Show Desktop. Keep cards in the desktop layer and restack them
    relative to that window only when their order is wrong. Ordinary apps and
    the relative order of cards are left to the window manager.
    """
    stack=prop(root,'_NET_CLIENT_LIST_STACKING')
    desktop_type=atoms['_NET_WM_WINDOW_TYPE_DESKTOP']
    # Restrict both sides to desktop windows: never raise a card above an app.
    widgets=[w for w in stack if w in alive and desktop_type in prop(w,'_NET_WM_WINDOW_TYPE')]
    backgrounds=[w for w in stack if w not in alive and desktop_type in prop(w,'_NET_WM_WINDOW_TYPE') and not str(prop(w,'_NET_WM_NAME')).startswith('Eww - ')]
    if not widgets or not backgrounds:return
    sibling=backgrounds[-1];boundary=stack.index(sibling)
    if all(stack.index(w)>boundary for w in widgets):return
    for window in widgets:
        event=XEvent();event.client.type=33;event.client.display=D;event.client.window=window
        event.client.message_type=atoms['_NET_RESTACK_WINDOW'];event.client.format=32
        event.client.data.l[0]=2  # pager source, per EWMH
        event.client.data.l[1]=sibling
        event.client.data.l[2]=0  # Above the desktop sibling, not Above all windows
        X.XSendEvent(D,root,0,(1<<19)|(1<<20),C.byref(event))
        sibling=window
    X.XFlush(D)

last = None
seen = set()
pending = {}
def settle_placements(alive, scale):
    """Restore coordinates once GTK has settled after map/config reload.

    Native handles restore early. Near an edge, an interim default width can
    clamp that position before GTK finishes shrinking to the saved size.
    Only newly mapped windows need this later correction; never fight a drag.
    """
    global seen
    now=time.monotonic()
    for window in alive.keys()-seen:pending[window]=now+1.4
    seen=set(alive)
    due=[w for w,deadline in pending.items() if deadline<=now or w not in alive]
    if not due:return
    try:saved=json.loads((Path(__file__).resolve().parent.parent/'positions.json').read_text())
    except (OSError,ValueError):saved={}
    rr,child,rx,ry,wx,wy,mask=U(),U(),I(),I(),I(),I(),C.c_uint()
    X.XQueryPointer(D,root,C.byref(rr),C.byref(child),C.byref(rx),C.byref(ry),C.byref(wx),C.byref(wy),C.byref(mask))
    for window in due:
        pending.pop(window,None)
        if window not in alive or mask.value & 256:continue
        name,width,height=alive[window];rect=saved.get('Eww - uw-'+name)
        if not isinstance(rect,dict):continue
        display=Gdk.Display.get_default();monitor=display.get_monitor_at_point(rect['x'],rect['y'])
        if monitor is None:continue
        area=monitor.get_workarea()
        x=max(area.x+8,min(rect['x'],area.x+area.width-width-8))
        y=max(area.y+8,min(rect['y'],area.y+area.height-height-8))
        X.XMoveWindow(D,window,int(x*scale),int(y*scale))
    X.XFlush(D)
from widget_catalog import EXTRA_WIDGETS
names = ['clock','calendar','system','music','battery','sound'] + [w['kind'] for w in EXTRA_WIDGETS]
def emit():
    global last
    scale = max(1, Gdk.get_default_root_window().get_scale_factor())
    result = {name:metrics(320,224) for name in names}
    alive={}
    windows=prop(root,'_NET_CLIENT_LIST')
    if not windows:
        # A bare X11 server (including UI tests) has no window manager to publish EWMH.
        tree_root,parent,children,count=U(),U(),C.POINTER(U)(),C.c_uint()
        if X.XQueryTree(D,root,C.byref(tree_root),C.byref(parent),C.byref(children),C.byref(count)):
            windows=list(children[:count.value])
            if children:X.XFree(children)
    for window in windows:
        title=prop(window,'_NET_WM_NAME')
        if not isinstance(title,str) or not title.startswith('Eww - uw-'): continue
        name=title.removeprefix('Eww - uw-')
        r,x,y,w,h,b,depth=U(),I(),I(),C.c_uint(),C.c_uint(),C.c_uint(),C.c_uint()
        if X.XGetGeometry(D,window,C.byref(r),C.byref(x),C.byref(y),C.byref(w),C.byref(h),C.byref(b),C.byref(depth)):
            result[name]=metrics(w.value//scale,h.value//scale)
            alive[window]=(name,w.value//scale,h.value//scale)
    keep_widgets_above_desktop(alive)
    settle_placements(alive,scale)
    if result != last:
        print(json.dumps(result),flush=True)
        last=result
    return True
emit()
GLib.timeout_add(120, emit)
GLib.MainLoop().run()
