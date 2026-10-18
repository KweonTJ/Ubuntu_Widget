import ctypes as C
import ctypes.util
import json
import sys
import time

X = C.CDLL(ctypes.util.find_library('X11'))
U = C.c_ulong
P = C.c_void_p
I = C.c_int

def setup(name, result, args):
    fn = getattr(X, name)
    fn.restype, fn.argtypes = result, args
    return fn

setup('XOpenDisplay', P, [C.c_char_p])
setup('XDefaultRootWindow', U, [P])
setup('XInternAtom', U, [P,C.c_char_p,I])
setup('XGetWindowProperty',I,[P,U,U,C.c_long,C.c_long,I,U,C.POINTER(U),C.POINTER(I),C.POINTER(U),C.POINTER(U),C.POINTER(P)])
setup('XFree',I,[P])
setup('XGetGeometry',I,[P,U,C.POINTER(U),C.POINTER(I),C.POINTER(I),C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.POINTER(C.c_uint)])
setup('XTranslateCoordinates',I,[P,U,U,I,I,C.POINTER(I),C.POINTER(I),C.POINTER(U)])
setup('XFlush',I,[P])
setup('XSendEvent',I,[P,U,I,C.c_long,P])
setup('XQueryPointer',I,[P,U,C.POINTER(U),C.POINTER(U),C.POINTER(I),C.POINTER(I),C.POINTER(I),C.POINTER(I),C.POINTER(C.c_uint)])
error_callback = C.CFUNCTYPE(I,P,P)
ignore_x_error = error_callback(lambda _display,_event: 0)
setup('XSetErrorHandler',P,[error_callback])(ignore_x_error)
D = X.XOpenDisplay(None)
if not D: raise RuntimeError('Cannot open display')
ROOT = X.XDefaultRootWindow(D)

def atom(s): return X.XInternAtom(D,s.encode(),0)

def prop(win,name):
    actual,fmt,count,after,data=U(),I(),U(),U(),P()
    X.XGetWindowProperty(D,win,atom(name),0,16384,0,0,C.byref(actual),C.byref(fmt),C.byref(count),C.byref(after),C.byref(data))
    if not data: return []
    try:
        if fmt.value==32: return list(C.cast(data,C.POINTER(U))[:count.value])
        if fmt.value==8: return C.string_at(data,count.value).decode('utf8','replace')
        return []
    finally: X.XFree(data)

def geometry(win):
    root,x,y,w,h,b,depth=U(),I(),I(),C.c_uint(),C.c_uint(),C.c_uint(),C.c_uint()
    if not X.XGetGeometry(D,win,C.byref(root),C.byref(x),C.byref(y),C.byref(w),C.byref(h),C.byref(b),C.byref(depth)): return None
    child=U()
    X.XTranslateCoordinates(D,win,ROOT,0,0,C.byref(x),C.byref(y),C.byref(child))
    return {'id':win,'x':x.value,'y':y.value,'width':w.value,'height':h.value}

def windows():
    result={}
    clients=prop(ROOT,'_NET_CLIENT_LIST_STACKING') or prop(ROOT,'_NET_CLIENT_LIST')
    if not clients:
        setup('XQueryTree',I,[P,U,C.POINTER(U),C.POINTER(U),C.POINTER(C.POINTER(U)),C.POINTER(C.c_uint)])
        root,parent,children,count=U(),U(),C.POINTER(U)(),C.c_uint()
        if X.XQueryTree(D,ROOT,C.byref(root),C.byref(parent),C.byref(children),C.byref(count)):
            clients=list(children[:count.value])
            if children:X.XFree(children)
    for win in clients:
        name=prop(win,'_NET_WM_NAME') or prop(win,'WM_NAME')
        if isinstance(name,str) and name.startswith('Eww - uw-'):
            rect=geometry(win)
            if rect: result[name.removeprefix('Eww - ')]=rect
    return result

class Data(C.Union):
    _fields_=[('l',C.c_long*5),('b',C.c_char*20)]
class Client(C.Structure):
    _fields_=[('type',I),('serial',U),('send_event',I),('display',P),('window',U),('message_type',U),('format',I),('data',Data)]
class Event(C.Union):
    _fields_=[('client',Client),('pad',C.c_long*24)]

def message(win,name,values):
    ev=Event()
    ev.client.type=33
    ev.client.display=D
    ev.client.window=win
    ev.client.message_type=atom(name)
    ev.client.format=32
    for i,v in enumerate(values): ev.client.data.l[i]=v
    X.XSendEvent(D,ROOT,0,(1<<19)|(1<<20),C.byref(ev))
    X.XFlush(D)

def show_desktop(value): message(ROOT,'_NET_SHOWING_DESKTOP',[value])

def pointer():
    root,child,rx,ry,wx,wy,mask=U(),U(),I(),I(),I(),I(),C.c_uint()
    X.XQueryPointer(D,ROOT,C.byref(root),C.byref(child),C.byref(rx),C.byref(ry),C.byref(wx),C.byref(wy),C.byref(mask))
    return rx.value,ry.value

T=C.CDLL(ctypes.util.find_library('Xtst'))
T.XTestFakeMotionEvent.argtypes=[P,I,I,I,U]
T.XTestFakeButtonEvent.argtypes=[P,C.c_uint,I,U]
def mouse(x,y):
    T.XTestFakeMotionEvent(D,-1,int(x),int(y),0)
    X.XFlush(D)
def button(down):
    T.XTestFakeButtonEvent(D,1,int(down),0)
    X.XFlush(D)
def drag(start,end):
    mouse(*start)
    time.sleep(.1)
    button(True)
    time.sleep(.1)
    for i in range(1,21):
        mouse(start[0]+(end[0]-start[0])*i/20,start[1]+(end[1]-start[1])*i/20)
        time.sleep(.025)
    button(False)
    time.sleep(.25)


def desktop_state(point=None):
    import gi
    gi.require_version('Gdk','3.0')
    from gi.repository import Gdk
    display=Gdk.Display.get_default()
    monitor=display.get_monitor_at_point(*point) if point else display.get_primary_monitor()
    monitor=monitor or display.get_monitor(0)
    area=monitor.get_workarea()
    scale=max(1,Gdk.get_default_root_window().get_scale_factor())
    items={name:{k:round(v/scale) for k,v in rect.items() if k!='id'} for name,rect in windows().items()}
    return (area.x,area.y,area.width,area.height),items

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='state':
        point=tuple(map(int,sys.argv[2:4])) if len(sys.argv)>=4 else None
        area,items=desktop_state(point)
        print(json.dumps({'area':area,'windows':items}))
    else:
        print(json.dumps({'workarea':prop(ROOT,'_NET_WORKAREA'),'widgets':windows()}))
