"""Physical pointer regression test; run only on a disposable X server."""
import ctypes as C
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('EWW_NATIVE_TEST_BINARY'), 'Run with make test-native on Xvfb')
class NativeControlsTests(unittest.TestCase):
    def test_body_drag_both_edges_controls_and_restore(self):
        sys.path.insert(0, str(ROOT / 'config/scripts'))
        import desktop_geometry as x
        binary = str(Path(os.environ['EWW_NATIVE_TEST_BINARY']).resolve())
        scale = int(os.environ.get('EWW_NATIVE_TEST_SCALE', '1'))
        x.setup('XQueryTree', x.I, [x.P, x.U, C.POINTER(x.U), C.POINTER(x.U), C.POINTER(C.POINTER(x.U)), C.POINTER(C.c_uint)])

        def rect():
            root, parent, children, count = x.U(), x.U(), C.POINTER(x.U)(), C.c_uint()
            x.X.XQueryTree(x.D, x.ROOT, C.byref(root), C.byref(parent), C.byref(children), C.byref(count))
            try:
                for window in list(children[:count.value]):
                    if x.prop(window, 'WM_NAME') == 'Eww - uw-control-test':
                        result = x.geometry(window)
                        return {k: v if k == 'id' else v // scale for k, v in result.items()}
            finally:
                if children:
                    x.X.XFree(children)
            self.fail('Test window not found')

        with tempfile.TemporaryDirectory(prefix='widget-native-') as temporary:
            config = Path(temporary)
            (config / 'runtime').mkdir(mode=0o700)
            env = {**os.environ, 'XDG_CACHE_HOME': str(config / 'cache'),
                   'XDG_RUNTIME_DIR': str(config / 'runtime'), 'NO_AT_BRIDGE': '1',
                   'GDK_BACKEND': 'x11', 'GDK_SCALE': str(scale), 'EWW_WIDGET_CONFIG': temporary, 'EWW_WIDGET_BINARY': binary}
            (config / 'eww.yuck').write_text('''
(defwindow uw-control-test
 :geometry (geometry :x "200px" :y "200px" :width "320px" :height "224px")
 :stacking "fg" :windowtype "normal" :wm-ignore true :resizable true
 (overlay
  (eventbox :drag-window true :drag-grid 16 :onrightclick "touch context-click"
   (box :orientation "v" :space-evenly false
    (label :height 40 :text "Drag this label")
    (scroll :vscroll true :hscroll false :vexpand true
      (box :orientation "v" :space-evenly false
        (label :height 180 :text "Drag scroll content")
        (label :height 180 :text "Scroll down")))
    (button :height 40 :onclick "touch button-click" (label :text "Keep button clicks"))))
  (eventbox :resize-window true :resize-axis "horizontal" :resize-edge "left" :resize-grid 16
    :resize-min-width 192 :resize-min-height 96 :halign "start" :valign "fill"
    (box :width 12 :vexpand true))
  (eventbox :resize-window true :resize-axis "horizontal" :resize-grid 16
    :resize-min-width 192 :resize-min-height 96 :halign "end" :valign "fill"
    (box :width 12 :vexpand true))))
''')
            (config / 'eww.scss').write_text('* { margin: 0; padding: 0; border: none; min-width: 0; min-height: 0; }')
            log = (config / 'engine.log').open('w')
            daemon = subprocess.Popen([binary, '--config', temporary, '--no-daemonize', 'daemon'], cwd=temporary, env=env, stdout=log, stderr=subprocess.STDOUT)

            def eww(*args):
                return subprocess.run([binary, '--config', temporary, *args], cwd=temporary, env=env, check=True, capture_output=True, text=True, timeout=8).stdout

            def settle():
                time.sleep(.3)
                return rect()

            def drag(start, end):
                x.drag(tuple(v * scale for v in start), tuple(v * scale for v in end))

            def click(px, py, button=1):
                x.mouse(px * scale, py * scale)
                for down in (True, False):
                    x.T.XTestFakeButtonEvent(x.D, button, int(down), 0)
                    x.X.XFlush(x.D)
                    time.sleep(.08)

            try:
                for _ in range(20):
                    if daemon.poll() is not None:
                        self.fail('Engine exited: ' + (config / 'engine.log').read_text())
                    if subprocess.run([binary, '--config', temporary, 'ping'], env=env, capture_output=True, timeout=2).returncode == 0:
                        break
                    time.sleep(.1)
                else:
                    self.fail('Engine was not ready: ' + (config / 'engine.log').read_text())
                eww('open', 'uw-control-test')
                time.sleep(1.1)
                before = rect()
                click(before['x'] + 100, before['y'] + 20)
                self.assertEqual(settle(), before, 'A plain body click must not move the card')

                drag((before['x'] + 100, before['y'] + 20), (before['x'] + 164, before['y'] + 68))
                moved = settle()
                self.assertEqual((moved['x'], moved['y']), (before['x'] + 64, before['y'] + 48), 'Drag must start on the label')
                drag((moved['x'] + 100, moved['y'] + 75), (moved['x'] + 132, moved['y'] + 91))
                scrolled = settle()
                self.assertEqual((scrolled['x'], scrolled['y']), (moved['x'] + 32, moved['y'] + 16), 'Drag must start inside the scroll viewport')

                right = scrolled['x'] + scrolled['width']
                drag((scrolled['x'] + 5, scrolled['y'] + 90), (scrolled['x'] - 59, scrolled['y'] + 90))
                left = settle()
                self.assertEqual(left['width'], scrolled['width'] + 64)
                self.assertEqual(left['x'] + left['width'], right, 'Left resize must keep the opposite edge fixed')
                self.assertEqual(left['height'], scrolled['height'])

                drag((left['x'] + left['width'] - 5, left['y'] + 90), (left['x'] + left['width'] + 59, left['y'] + 90))
                widened = settle()
                self.assertEqual(widened['width'], left['width'] + 64)
                self.assertEqual(widened['x'], left['x'])

                drag((widened['x'] + 5, widened['y'] + 90), (widened['x'] + 505, widened['y'] + 90))
                small = settle()
                self.assertEqual(small['width'], 192)
                self.assertEqual(small['x'] + small['width'], widened['x'] + widened['width'])

                click(small['x'] + 80, small['y'] + small['height'] - 20)
                self.assertTrue((config / 'button-click').exists(), 'Buttons must retain their normal click action')
                self.assertEqual(settle(), small)
                drag((small['x'] + 80, small['y'] + small['height'] - 20), (small['x'] + 112, small['y'] + small['height'] + 30))
                self.assertEqual(settle(), small, 'A control must not become a window drag handle')
                click(small['x'] + 80, small['y'] + 70, button=5)
                self.assertEqual(settle(), small, 'Scrolling must not move the card')
                click(small['x'] + 80, small['y'] + 20, button=3)
                self.assertTrue((config / 'context-click').exists(), 'Right-click menu handling must remain available')

                saved = json.loads((config / 'positions.json').read_text())['Eww - uw-control-test']
                self.assertEqual({k: small[k] for k in saved}, saved)
                eww('close', 'uw-control-test')
                eww('open', 'uw-control-test')
                time.sleep(1.1)
                restored = rect()
                self.assertEqual({k: restored[k] for k in saved}, saved)
            finally:
                daemon.terminate()
                daemon.wait(timeout=5)
                log.close()
