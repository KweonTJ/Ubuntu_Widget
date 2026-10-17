import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'config/scripts'))
import widget_store as store
import stacks

class StackTests(unittest.TestCase):
 def test_create_cycle_movement_size_restore_and_dissolve(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(store,'CONFIG',Path(tmp)),patch.object(store,'ensure_daemon'),patch.object(store,'eww',return_value='') as eww:
   positions={'Eww - uw-clock':{'x':40,'y':80,'width':320,'height':224},'Eww - uw-calendar':{'x':400,'y':80,'width':320,'height':224}}
   store.atomic_json('positions.json',positions)
   stacks.create(['uw-clock','uw-calendar'])
   self.assertEqual(stacks.excluded(),{'uw-calendar'})
   with self.assertRaises(ValueError):stacks.create(['uw-clock','uw-calendar'])
   moved={'x':120,'y':160,'width':384,'height':240}
   store.atomic_json('positions.json',{**positions,'Eww - uw-clock':moved})
   with patch.object(store,'placement',return_value=moved):stacks.cycle('uw-clock')
   self.assertEqual(stacks.excluded(),{'uw-clock'})
   self.assertEqual(store.read_json('positions.json',{})['Eww - uw-calendar'],moved)
   store.open_visible()
   self.assertTrue(any(c.args[0]=='open-many' and 'uw-calendar' in c.args and 'uw-clock' not in c.args for c in eww.call_args_list))
   stacks.dissolve('uw-calendar')
   self.assertEqual(stacks.groups(),[])
   restored=store.read_json('positions.json',{})
   self.assertEqual(restored['Eww - uw-clock'],positions['Eww - uw-clock']);self.assertEqual(restored['Eww - uw-calendar'],positions['Eww - uw-calendar'])

 def test_size_mismatch_rejected_and_remove_keeps_remaining_widget(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(store,'CONFIG',Path(tmp)),patch.object(store,'ensure_daemon'),patch.object(store,'eww',return_value=''):
   a={'x':40,'y':80,'width':320,'height':224};b={**a,'width':208}
   store.atomic_json('positions.json',{'Eww - uw-clock':a,'Eww - uw-calendar':b})
   with self.assertRaises(ValueError):stacks.create(['uw-clock','uw-calendar'])
   store.atomic_json('positions.json',{'Eww - uw-clock':a,'Eww - uw-calendar':a})
   stacks.create(['uw-clock','uw-calendar']);stacks.detach('uw-clock')
   self.assertEqual(stacks.groups(),[]);self.assertEqual(stacks.excluded(),set())

 def test_failed_switch_rolls_back_active_member_and_geometry(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(store,'CONFIG',Path(tmp)),patch.object(store,'ensure_daemon'),patch.object(store,'eww',return_value=''):
   a={'x':40,'y':80,'width':320,'height':224}
   store.atomic_json('positions.json',{'Eww - uw-clock':a,'Eww - uw-calendar':a});stacks.create(['uw-clock','uw-calendar'])
   before=store.read_json('positions.json',{})
   def engine(*args,**kwargs):
    if args==('open','uw-calendar'):raise RuntimeError('Engine unavailable')
    return ''
   with patch.object(store,'eww',side_effect=engine),patch.object(store,'placement',return_value={**a,'x':200}):
    with self.assertRaises(RuntimeError):stacks.cycle('uw-clock')
   self.assertEqual(stacks.groups()[0]['active'],'uw-clock');self.assertEqual(store.read_json('positions.json',{}),before)
