import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sharing', ROOT / 'config/scripts/kdeconnect_widget.py')
sharing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sharing)


class FakeClient(sharing.Client):
    def __init__(self):
        self.rows = {
            'phone': {'name': 'My phone', 'isReachable': True, 'isTrusted': True},
            'stranger': {'name': 'Unknown', 'isReachable': True, 'isTrusted': False},
            'offline': {'name': 'Offline', 'isReachable': False, 'isTrusted': True},
            'disabled': {'name': 'No sharing', 'isReachable': True, 'isPaired': True},
        }
        self.sent = []
        self.bus = SimpleNamespace(name_has_owner=lambda _: True)

    def interface(self, path, name):
        if path == sharing.ROOT:
            return SimpleNamespace(devices=lambda *a, **kw: list(self.rows))
        device_id = path.removesuffix('/share').rsplit('/', 1)[1]
        if name.endswith('.Properties'):
            return SimpleNamespace(GetAll=lambda *a, **kw: self.rows[device_id])
        if name.endswith('.share'):
            return SimpleNamespace(shareUrls=lambda urls, **kw: self.sent.append((device_id, list(urls))))
        return SimpleNamespace(hasPlugin=lambda *a, **kw: device_id != 'disabled')


class KDEConnectTests(unittest.TestCase):
    def test_only_connected_paired_sharing_devices_are_offered(self):
        client = FakeClient()
        self.assertEqual(client.devices(), [{'id': 'phone', 'name': 'My phone'}])
        # The newer isPaired property is also supported.
        client.rows['phone']['isPaired'] = client.rows['phone'].pop('isTrusted')
        self.assertEqual(sharing.snapshot(client)['count'], 1)
        client.bus.name_has_owner = lambda _: False
        self.assertFalse(sharing.snapshot(client)['available'])

    def test_multiple_files_are_one_request_with_encoded_local_urls(self):
        client = FakeClient()
        with tempfile.TemporaryDirectory() as directory:
            files = [Path(directory) / name for name in ['한글 file #1.txt', '$(test);two.txt']]
            for path in files:
                path.write_text('test data')
            self.assertEqual(client.send('phone', files), 2)
            self.assertEqual(client.sent, [('phone', [path.as_uri() for path in files])])

    def test_disconnect_untrusted_or_disabled_target_never_sends(self):
        client = FakeClient()
        with tempfile.NamedTemporaryFile() as file:
            for target in ('stranger', 'offline', 'disabled', '../phone', 'missing'):
                with self.assertRaises(sharing.ShareError):
                    client.send(target, [file.name])
            client.rows['phone']['isReachable'] = False
            with self.assertRaises(sharing.ShareError):
                client.send('phone', [file.name])
        self.assertEqual(client.sent, [])

    def test_validate_entire_selection_before_sending_anything(self):
        client = FakeClient()
        with tempfile.TemporaryDirectory() as directory:
            valid = Path(directory) / 'valid.txt'
            valid.write_text('test data')
            for selection in ([], [valid, directory], [valid, Path(directory) / 'missing']):
                with self.assertRaises((sharing.ShareError, FileNotFoundError)):
                    client.send('phone', selection)
        self.assertEqual(client.sent, [])


if __name__ == '__main__':
    unittest.main()
