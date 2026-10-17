import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'config/scripts'))
import app_links
from responsive import metrics


class ResponsiveLinksTests(unittest.TestCase):
    def test_size_metrics_grow_content_and_change_density(self):
        small, medium, large = [metrics(w,h) for w,h in [(208,96),(320,224),(480,352)]]
        self.assertEqual([small['mode'],medium['mode'],large['mode']],['small','medium','large'])
        for key in ('hero','clock','padding','ring','cell','rows'):
            self.assertLess(small[key], large[key], key)
        self.assertLessEqual(small['padding']*2+small['hero']+16,96)

    def test_obsidian_is_read_only_live_and_respects_vault_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);vault=root/'vault';vault.mkdir();config=root/'settings';config.mkdir()
            note=vault/'Note with spaces & 한글.md';note.write_text('---\nprivate: metadata\n---\n# Today\nFirst **paragraph**.\n[[Other|Link label]]\n')
            with patch.object(app_links.store,'CONFIG',config),patch.object(app_links,'vaults',return_value=[vault]):
                original=note.read_bytes();app_links.save_note(note)
                value=app_links.snapshot()
                self.assertEqual(value['obsidian_title'],'Today')
                self.assertIn('First paragraph.',value['obsidian_text'])
                self.assertNotIn('private: metadata',value['obsidian_text'])
                self.assertEqual(original,note.read_bytes())
                note.write_text('# Changed\nLive content')
                self.assertEqual(app_links.snapshot()['obsidian_title'],'Changed')
                outside=root/'outside.md';outside.write_text('Outside')
                with self.assertRaises(ValueError):app_links.save_note(outside)
                link=vault/'escape.md';link.symlink_to(outside)
                with self.assertRaises(ValueError):app_links.save_note(link)
                note.unlink();self.assertFalse(app_links.snapshot()['obsidian_connected'])


if __name__=='__main__':unittest.main()
