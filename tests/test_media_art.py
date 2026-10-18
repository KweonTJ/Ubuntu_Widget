import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'config/scripts'))
import album_art
import data
from gi.repository import GdkPixbuf


class ArtworkTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='widget-art-test-');self.root=Path(self.tmp.name)
  self.image=self.root/'cover with spaces.png'
  pix=GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB,False,8,80,40);pix.fill(0x527FAAFF);pix.savev(str(self.image),'png',[],[])
  self.cache=album_art.ArtworkCache(self.root/'cache')
 def tearDown(self):
  self.cache.pool.shutdown(wait=True);self.tmp.cleanup()
 def wait_cover(self,source):
  self.cache.get(source)
  for _ in range(60):
   result=self.cache.get(source)
   if result:return Path(result)
   time.sleep(.01)
  self.fail('Artwork was not rendered')
 def test_local_cover_round_crop_and_changed_file_refresh(self):
  source=self.image.as_uri();cover=self.wait_cover(source)
  pix=GdkPixbuf.Pixbuf.new_from_file(str(cover));pixels=pix.get_pixels()
  self.assertEqual((pix.get_width(),pix.get_height()),(512,512))
  self.assertEqual(pixels[3],0)
  self.assertEqual(pixels[256*pix.get_rowstride()+256*4+3],255)
  before=self.image.stat();os.utime(self.image,ns=(before.st_atime_ns,before.st_mtime_ns+1000000))
  self.assertEqual(self.cache.get(source),'','A changed track must not show the old picture')
  self.assertNotEqual(self.wait_cover(source),cover)
 def test_remote_art_is_cached_and_bounded(self):
  response=Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
  response.read.return_value=self.image.read_bytes();opener=Mock();opener.open.return_value=response
  with patch.object(album_art.urllib.request,'build_opener',return_value=opener):
   cover=self.wait_cover('https://example.invalid/cover?private-title=fixture')
   self.assertEqual(self.cache.get('https://example.invalid/cover?private-title=fixture'),str(cover))
  self.assertEqual(opener.open.call_count,1)
  self.assertNotIn('fixture',cover.name)
  response.read.assert_called_once_with(album_art.MAX_BYTES+1)
  response.read.return_value=b'x'*(album_art.MAX_BYTES+1)
  with patch.object(album_art.urllib.request,'build_opener',return_value=opener):
   with self.assertRaises(ValueError):album_art.read_artwork('https://example.invalid/too-large')
 def test_slow_previous_cover_never_blocks_or_leaks_into_new_track(self):
  started=threading.Event();release=threading.Event()
  def slow(source,target):
   started.set();release.wait(2);target.parent.mkdir(exist_ok=True);target.write_bytes(b'old');return str(target)
  with patch.object(album_art,'render_artwork',side_effect=slow):
   start=time.monotonic();self.assertEqual(self.cache.get('https://example.invalid/old'),'')
   self.assertLess(time.monotonic()-start,.15);self.assertTrue(started.wait(1))
   self.assertEqual(self.cache.get('https://example.invalid/new'),'')
   release.set();self.cache.job[1].result(timeout=1)
   self.assertEqual(self.cache.get('https://example.invalid/new'),'')
 def test_missing_invalid_and_failed_cover_fall_back_with_retry_backoff(self):
  for source in ('','file:///missing/cover.png','file://remote-host/cover.png','javascript:alert(1)','https://[bad'):
   self.assertEqual(self.cache.get(source),'')
  self.assertIsNone(self.cache.job)
  with patch.object(album_art,'render_artwork',side_effect=ValueError('bad image')) as renderer:
   self.cache.get('https://example.invalid/bad');self.cache.job[1].exception(timeout=1)
   self.assertEqual(self.cache.get('https://example.invalid/bad'),'')
   self.assertEqual(self.cache.get('https://example.invalid/bad'),'')
   self.assertEqual(renderer.call_count,1)
 def test_media_selects_current_cover_and_control_does_not_fetch_it(self):
  bus=Mock();bus.list_names.return_value=['org.mpris.MediaPlayer2.fixture'];props=Mock()
  props.GetAll.return_value={'PlaybackStatus':'Playing','Metadata':{'xesam:title':'Fixture','mpris:artUrl':self.image.as_uri()},'CanControl':True,'CanPause':True}
  with patch.object(data,'BUS',bus),patch.object(data.dbus,'Interface',return_value=props),patch.object(data.ARTWORK,'get',return_value='/fixture/cached.png') as get:
   _,value=data.media();self.assertEqual(value['art'],'/fixture/cached.png');get.assert_called_once_with(self.image.as_uri())
   get.reset_mock();_,value=data.media(artwork=False);get.assert_not_called();self.assertEqual(value['art'],'')
  bus.list_names.return_value=[]
  with patch.object(data,'BUS',bus):self.assertEqual(data.media()[1]['art'],'')
