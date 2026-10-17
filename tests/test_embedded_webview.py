import ctypes as C,ctypes.util,json,os,shlex,subprocess,sys,tempfile,time
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.environ.get("EWW_WEBVIEW_TEST_BINARY"), "Run with make test-webview on Xvfb")
class EmbeddedWebViewTests(unittest.TestCase):
 def test_page_receives_pointer_and_check_updates(self):
  root=ROOT
  with tempfile.TemporaryDirectory(prefix='widget-webview-') as temporary:
   work=Path(temporary);(work/'runtime').mkdir(mode=0o700)
   (work/'test.html').write_text('''<!doctype html><meta charset="utf-8"><title>open</title><style>body{margin:0;padding:24px;background:#eef1f6;color:#253246;font:16px sans-serif}input{width:24px;height:24px;vertical-align:middle}</style><label><input type="checkbox" onclick="document.title=this.checked?'done':'open'"> Today task</label>''')
   helper=work/'helper.py'
   helper.write_text('''import os,sys\nfrom pathlib import Path\nsys.path.insert(0,'''+repr(str(root/'config/scripts'))+''')\nimport todomate_webview as t\nt.store.CONFIG=Path('''+repr(temporary)+''')\nt.URL=Path('''+repr(str(work/'test.html'))+''').as_uri()\nclass Test(t.Todomate):\n def view(self):\n  v=super().view()\n  v.connect('notify::title',lambda *_:Path('''+repr(str(work/'state'))+''').write_text(v.get_title() or ''))\n  return v\nraise SystemExit(Test().run([sys.argv[0],'embed',os.environ['EWW_SOCKET_ID']]))\n''')
   (work/'eww.yuck').write_text('(defwindow uw-web-test :geometry (geometry :x "200px" :y "200px" :width "320px" :height "224px") :wm-ignore true :stacking "fg" :windowtype "normal" :resizable true (xembed :command '+json.dumps('exec /usr/bin/python3 '+shlex.quote(str(helper)))+'))')
   (work/'eww.scss').write_text('*{margin:0;padding:0;min-width:0;min-height:0;}')
   env={**os.environ,'EWW_WIDGET_APP_ID':'local.ubuntu.WidgetLibrary.EmbedQA','XDG_CACHE_HOME':str(work/'cache'),'XDG_RUNTIME_DIR':str(work/'runtime'),'NO_AT_BRIDGE':'1','GDK_BACKEND':'x11'}
   binary=os.environ['EWW_WEBVIEW_TEST_BINARY'];log=(work/'engine.log').open('w');daemon=subprocess.Popen([binary,'--config',temporary,'--no-daemonize','daemon'],env=env,stdout=log,stderr=log)
   def cmd(*args):return subprocess.run([binary,'--config',temporary,*args],env=env,capture_output=True,text=True,timeout=10)
   try:
    for _ in range(30):
     if cmd('ping').returncode==0:break
     time.sleep(.1)
    opened=cmd('open','uw-web-test');assert opened.returncode==0,opened.stderr
    for _ in range(100):
     if (work/'state').exists() and (work/'state').read_text()=='open':break
     time.sleep(.1)
    else:raise RuntimeError('Web view did not load: '+(work/'engine.log').read_text()[-2000:])
    X=C.CDLL(ctypes.util.find_library('X11'));T=C.CDLL(ctypes.util.find_library('Xtst'))
    X.XOpenDisplay.restype=C.c_void_p;X.XOpenDisplay.argtypes=[C.c_char_p];d=X.XOpenDisplay(None)
    T.XTestFakeMotionEvent.argtypes=[C.c_void_p,C.c_int,C.c_int,C.c_int,C.c_ulong];T.XTestFakeButtonEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong];X.XFlush.argtypes=[C.c_void_p]
    T.XTestFakeMotionEvent(d,-1,230,230,0);T.XTestFakeButtonEvent(d,1,1,0);T.XTestFakeButtonEvent(d,1,0,0);X.XFlush(d)
    for _ in range(30):
     if (work/'state').read_text()=='done':break
     time.sleep(.1)
    else:raise RuntimeError('Checkbox was not checked; state='+str((work/'state').read_text()))
    print('Embedded WebKit: local page loaded and a physical pointer click checked its task.',flush=True)
    cmd('close','uw-web-test');time.sleep(.3)
   finally:
    cmd('kill');daemon.wait(timeout=5);log.close()
