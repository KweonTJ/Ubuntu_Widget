import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('installer',ROOT/'scripts/install.py')
installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)

class PackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.binary=self.root/'patched-eww';self.binary.write_text('#!/bin/sh\n# eww-native-draggable resize-min-width EWW_SOCKET_ID eww-native-stack-swipe\necho patched-test-engine\n');self.binary.chmod(0o755)
    def tearDown(self):self.tmp.cleanup()
    def install(self,home,**kwargs):
        env={'HOME':str(home),'XDG_CONFIG_HOME':str(home/'settings'),'XDG_DATA_HOME':str(home/'data'),'XDG_CACHE_HOME':str(home/'cache')}
        with patch.dict(os.environ,env),contextlib.redirect_stdout(io.StringIO()):installer.install(self.binary,**kwargs)
        return home/'settings/ubuntu-widget'
    def test_two_different_users_and_spaces(self):
        for name in ['alice','second user']:
            home=self.root/name;config=self.install(home)
            self.assertTrue((config/'scripts/layout.py').exists())
            self.assertEqual(json.loads((config/'positions.json').read_text()),{})
            desktop=(home/'data/applications/local.ubuntu.WidgetLibrary.desktop').read_text()
            self.assertIn(str(home/'.local/bin/ubuntu-widget'),desktop)
            self.assertFalse((home/'settings/autostart/ubuntu-widget.desktop').exists())
            p=subprocess.run([str(home/'.local/bin/ubuntu-widget'),'--help'],env={**os.environ,'HOME':str(home)},capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
    def test_upgrade_preserves_personal_state(self):
        home=self.root/'user';config=self.install(home)
        own={'note':{'title':'Private note','text':'Do not overwrite'}}
        (config/'widget-settings.json').write_text(json.dumps(own))
        state={'weather':{'connected':True,'city':'Private location','latitude':1,'longitude':2}}
        (config/'connections.json').write_text(json.dumps(state))
        self.install(home,autostart=True)
        self.assertEqual(json.loads((config/'widget-settings.json').read_text()),own)
        self.assertEqual(json.loads((config/'connections.json').read_text()),state)
        self.assertTrue((home/'settings/autostart/ubuntu-widget.desktop').exists())
    def test_unknown_config_and_stock_engine_are_rejected(self):
        home=self.root/'user';config=home/'settings/ubuntu-widget';config.mkdir(parents=True);(config/'mine.txt').write_text('existing content')
        with self.assertRaises(ValueError):self.install(home)
        self.assertEqual((config/'mine.txt').read_text(),'existing content')
        self.binary.write_text('#!/bin/sh\necho stock-eww\n')
        with self.assertRaises(ValueError):self.install(self.root/'other')
    def test_wayland_rejected_before_engine_launch(self):
        home=self.root/'user';self.install(home)
        p=subprocess.run([str(home/'.local/bin/ubuntu-widget'),'start'],env={**os.environ,'HOME':str(home),'XDG_SESSION_TYPE':'wayland','DISPLAY':':99'},capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0);self.assertIn('full Xorg',p.stderr)
    def test_desktop_quote_handles_reserved_characters(self):
        value=installer.desktop_quote(Path('some path/$x%name"'))
        self.assertTrue(value.startswith('"'));self.assertIn('\\$',value);self.assertIn('%%',value);self.assertIn('\\"',value)

if __name__=='__main__':unittest.main()
