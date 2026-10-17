#!/usr/bin/python3
"""Apply only per-widget blur hints; never change foreground window opacity."""
import ctypes as C
import ctypes.util
import json
import sys
import time
import gi
gi.require_version('Gdk','3.0')
from gi.repository import Gdk
import glass_effect as glass
import widget_store as store

def main():
    X=C.CDLL(ctypes.util.find_library('X11'));P=C.c_void_p;U=C.c_ulong;I=C.c_int
    def bind(name,restype,args):
        fn=getattr(X,name);fn.restype=restype;fn.argtypes=args;return fn
    bind('XOpenDisplay',P,[C.c_char_p]);bind('XDefaultRootWindow',U,[P])
    bind('XInternAtom',U,[P,C.c_char_p,I]);bind('XFree',I,[P]);bind('XFlush',I,[P])
    bind('XGetWindowProperty',I,[P,U,U,C.c_long,C.c_long,I,U,C.POINTER(U),C.POINTER(I),C.POINTER(U),C.POINTER(U),C.POINTER(P)])
    bind('XChangeProperty',I,[P,U,U,U,I,I,C.c_char_p,I]);bind('XDeleteProperty',I,[P,U,U])
    bind('XGetGeometry',I,[P,U,C.POINTER(U),C.POINTER(I),C.POINTER(I),C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.POINTER(C.c_uint)])
    bind('XTranslateCoordinates',I,[P,U,U,I,I,C.POINTER(I),C.POINTER(I),C.POINTER(U)])
    bind('XMoveResizeWindow',I,[P,U,I,I,C.c_uint,C.c_uint])
    error_type=C.CFUNCTYPE(I,P,P);ignore_error=error_type(lambda *_:0);bind('XSetErrorHandler',P,[error_type])(ignore_error)
    display=X.XOpenDisplay(None)
    if not display:raise SystemExit('X11 display unavailable')
    root=X.XDefaultRootWindow(display)
    atoms={name:X.XInternAtom(display,name.encode(),0) for name in ['_NET_CLIENT_LIST','_NET_WM_NAME','_MUTTER_HINTS','STRING','_GTK_FRAME_EXTENTS','CARDINAL']}
    def prop(window,name):
        actual,fmt,count,after,data=U(),I(),U(),U(),P()
        X.XGetWindowProperty(display,window,atoms[name],0,16384,0,0,C.byref(actual),C.byref(fmt),C.byref(count),C.byref(after),C.byref(data))
        if not data:return [] if name=='_NET_CLIENT_LIST' else ''
        try:
            if fmt.value==32:return list(C.cast(data,C.POINTER(U))[:count.value])
            if fmt.value==8:return C.string_at(data,count.value).decode('utf8','replace')
            return ''
        finally:X.XFree(data)
    def geometry(window):
        rr,x,y,width,height,border,depth=U(),I(),I(),C.c_uint(),C.c_uint(),C.c_uint(),C.c_uint()
        if not X.XGetGeometry(display,window,C.byref(rr),C.byref(x),C.byref(y),C.byref(width),C.byref(height),C.byref(border),C.byref(depth)):return None
        child=U();X.XTranslateCoordinates(display,window,root,0,0,C.byref(x),C.byref(y),C.byref(child))
        return [x.value,y.value,width.value,height.value]
    scale=max(1,Gdk.get_default_root_window().get_scale_factor())
    # Keep blur inside the rounded panel, excluding transparent outer margins.
    # GTK frame-extents tell Mutter which part of the client is decoration.
    # Match .movable-canvas padding. A larger decoration extent makes Mutter
    # discard clicks on the visible card edges and their resize controls.
    inset=8*scale;original_extents={};pending={};last=None
    while True:
        try:
            value=glass.settings();items={w['id']:w for w in store.catalogue()}
            windows=prop(root,'_NET_CLIENT_LIST');alive=set(windows)
            for window,(deadline,rect) in list(pending.items()):
                if window not in alive:pending.pop(window,None)
                elif time.monotonic()>=deadline:
                    X.XMoveResizeWindow(display,window,*rect);pending.pop(window,None)
            for window in set(original_extents)-alive:original_extents.pop(window,None)
            for window in windows:
                title=prop(window,'_NET_WM_NAME')
                if not isinstance(title,str) or not title.startswith('Eww - '):continue
                item=items.get(title.removeprefix('Eww - '))
                if not item:continue
                before=prop(window,'_MUTTER_HINTS')
                # Preserve all hints not owned by this widget effect.
                hints=[part for part in before.split(';') if part and not part.startswith('blur-provider=')]
                active=glass.enabled(item,value)
                if active:hints.append('blur-provider=sigma:28,brightness:1.0')
                after=';'.join(hints)
                if after!=before:
                    if after:
                        raw=after.encode();X.XChangeProperty(display,window,atoms['_MUTTER_HINTS'],atoms['STRING'],8,0,raw,len(raw))
                    else:X.XDeleteProperty(display,window,atoms['_MUTTER_HINTS'])
                current_extents=prop(window,'_GTK_FRAME_EXTENTS')
                if active and window not in original_extents:original_extents[window]=current_extents
                desired=[inset]*4 if active else original_extents.get(window,current_extents)
                if desired!=current_extents:
                    rect=geometry(window)
                    if desired:
                        raw=(U*4)(*desired);X.XChangeProperty(display,window,atoms['_GTK_FRAME_EXTENTS'],atoms['CARDINAL'],32,0,C.cast(raw,C.c_char_p),4)
                    else:X.XDeleteProperty(display,window,atoms['_GTK_FRAME_EXTENTS'])
                    # Mutter adjusts buffer geometry when frame-extents change.
                    # Reapply the exact client geometry after that adjustment.
                    if rect:pending[window]=(time.monotonic()+.15,rect)
            X.XFlush(display)
            output=json.dumps(value,ensure_ascii=False)
            if output!=last:print(output,flush=True);last=output
        except (OSError,ValueError) as exc:print(str(exc),file=sys.stderr,flush=True)
        time.sleep(.3)

if __name__=='__main__':
    try:main()
    except (BrokenPipeError,KeyboardInterrupt):pass
