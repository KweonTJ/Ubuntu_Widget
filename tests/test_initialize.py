import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('initialize', ROOT / 'scripts/initialize.py')
initializer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(initializer)


class InitializeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.template = self.root / 'template'
        self.template.mkdir()
        (self.template / 'widget-settings.json').write_text('{}')
        (self.template / 'positions.json').write_text('{}')
        (self.template / 'connections.json').write_text('{}')
        (self.template / 'script.py').write_text('# old program\n')
        (self.template / 'script.py').chmod(0o755)

    def tearDown(self):
        self.temporary.cleanup()

    def test_first_launch_and_upgrade_preserve_each_users_state(self):
        for name in ('alice', 'second user'):
            config = self.root / name / 'ubuntu-widget'
            initializer.initialize(config, self.template)
            (config / 'widget-settings.json').write_text(json.dumps({'note': name}))
            (config / 'positions.json').write_text(json.dumps({'x': 64}))
            (config / 'connections.json').write_text(json.dumps({'private': name}))
        (self.template / 'script.py').write_text('# updated program\n')
        for name in ('alice', 'second user'):
            config = self.root / name / 'ubuntu-widget'
            initializer.initialize(config, self.template)
            self.assertEqual(json.loads((config / 'widget-settings.json').read_text()), {'note': name})
            self.assertEqual(json.loads((config / 'connections.json').read_text()), {'private': name})
            self.assertEqual(json.loads((config / 'positions.json').read_text()), {'x': 64})
            self.assertEqual((config / 'script.py').read_text(), '# updated program\n')
            self.assertTrue(os.access(config / 'script.py', os.X_OK))

    def test_unchanged_templates_do_not_overwrite_custom_code_and_missing_files_repair(self):
        config = self.root / 'user/config'
        initializer.initialize(config, self.template)
        (config / 'script.py').write_text('# personal edit\n')
        initializer.initialize(config, self.template)
        self.assertEqual((config / 'script.py').read_text(), '# personal edit\n')
        (config / 'script.py').unlink()
        initializer.initialize(config, self.template)
        self.assertEqual((config / 'script.py').read_text(), '# old program\n')

    def test_unrecognized_config_is_not_overwritten(self):
        config = self.root / 'user/config'
        config.mkdir(parents=True)
        (config / 'mine.txt').write_text('personal content')
        with self.assertRaises(ValueError):
            initializer.initialize(config, self.template)
        self.assertEqual((config / 'mine.txt').read_text(), 'personal content')
        self.assertFalse((config / 'script.py').exists())
