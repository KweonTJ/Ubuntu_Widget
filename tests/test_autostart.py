import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('widget_autostart', ROOT / 'config/scripts/autostart.py')
startup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(startup)


class AutostartTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = self.root / 'settings with spaces'
        self.cache = self.root / 'cache'
        self.env = patch.dict(os.environ, {'EWW_WIDGET_CONFIG': str(self.config),
                                         'XDG_CACHE_HOME': str(self.cache), 'GDK_BACKEND': 'wayland'})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_waits_for_display_then_retries_failed_daemon_before_opening_windows(self):
        failure = subprocess.CalledProcessError(1, 'start-service.py')
        with patch.object(startup, 'display_ready', side_effect=[False, True, True]), \
                patch.object(startup.subprocess, 'run', side_effect=[failure, None, None]) as run, \
                patch.object(startup.time, 'sleep'):
            self.assertEqual(startup.main(), 0)
        commands = [call.args[0] for call in run.call_args_list]
        daemon = ['/usr/bin/python3', str(self.config / 'scripts/start-service.py')]
        self.assertEqual(commands, [daemon, daemon, ['/usr/bin/python3', str(self.config / 'scripts/windows.py'), 'open']])
        self.assertEqual(os.environ['GDK_BACKEND'], 'x11')
        log = (self.cache / 'ubuntu-widget/autostart.log').read_text()
        self.assertIn('retrying', log)
        self.assertIn('restored successfully', log)
        self.assertFalse(self.config.exists(), 'Autostart must not rewrite saved widget settings.')

    def test_retry_after_windows_fail(self):
        failure = subprocess.CalledProcessError(1, 'windows.py')
        with patch.object(startup, 'display_ready', return_value=True), \
                patch.object(startup.subprocess, 'run', side_effect=[None, failure, None, None]) as run, \
                patch.object(startup.time, 'sleep'):
            self.assertEqual(startup.main(), 0)
        self.assertEqual(run.call_count, 4)

    def test_display_never_ready_stops_without_launching(self):
        with patch.object(startup.time, 'monotonic', side_effect=[0, 0, 91]), \
                patch.object(startup, 'display_ready', return_value=False), \
                patch.object(startup.subprocess, 'run') as run, \
                patch.object(startup.time, 'sleep'):
            self.assertEqual(startup.main(), 1)
        run.assert_not_called()
        self.assertIn('timed out', (self.cache / 'ubuntu-widget/autostart.log').read_text())

    def test_concurrent_login_attempt_does_not_launch_duplicate(self):
        with patch.object(startup.fcntl, 'flock', side_effect=BlockingIOError), \
                patch.object(startup, 'display_ready') as ready:
            self.assertEqual(startup.main(), 0)
        ready.assert_not_called()

    def test_requires_both_display_and_window_manager(self):
        for output, expected in [('_NET_SUPPORTING_WM_CHECK: no such atom on any window.', False),
                                 ('_NET_SUPPORTING_WM_CHECK(WINDOW): window id # 0x0\n', False),
                                 ('_NET_SUPPORTING_WM_CHECK(WINDOW): window id # 0x123\n', True)]:
            with self.subTest(output=output), patch.object(startup.subprocess, 'run', side_effect=[
                    SimpleNamespace(returncode=0), SimpleNamespace(returncode=0, stdout=output)]):
                self.assertEqual(startup.display_ready(), expected)
        with patch.object(startup.subprocess, 'run', side_effect=subprocess.TimeoutExpired('xdpyinfo', 3)):
            self.assertFalse(startup.display_ready())


if __name__ == '__main__':
    unittest.main()
