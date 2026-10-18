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

class DropStackTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.config=patch.object(store,'CONFIG',Path(self.tmp.name));self.config.start();self.addCleanup(self.config.stop)
  self.engine=patch.object(store,'eww',return_value='');self.eww=self.engine.start();self.addCleanup(self.engine.stop)
  self.daemon=patch.object(store,'ensure_daemon');self.daemon.start();self.addCleanup(self.daemon.stop)
  self.a={'x':200,'y':200,'width':320,'height':224};self.b={**self.a,'x':600}
  store.atomic_json('positions.json',{'Eww - uw-clock':self.a,'Eww - uw-calendar':self.b})

 def test_real_drop_creates_stack_at_target_and_split_restores_before_drag(self):
  stacks.dropped('uw-clock',self.a,self.b,{'uw-calendar':self.b,'uw-clock':self.b})
  group=stacks.groups()[0]
  self.assertEqual(group['active'],'uw-clock');self.assertEqual(group['members'],['uw-calendar','uw-clock'])
  self.assertEqual(group['original']['uw-clock'],self.a)
  self.assertEqual(store.read_json('positions.json',{})['Eww - uw-clock'],self.b)
  stacks.dissolve('uw-clock')
  self.assertEqual(store.read_json('positions.json',{})['Eww - uw-clock'],self.a)

 def test_mismatch_partial_overlap_stale_event_and_hidden_target_do_not_stack(self):
  small={**self.b,'width':208};partial={**self.b,'x':410};stale={**self.b,'x':200}
  for actual,target in ((small,self.b),(partial,self.b),(stale,self.b)):
   stacks.dropped('uw-clock',self.a,self.b if actual==stale else actual,{'uw-clock':actual,'uw-calendar':target})
   self.assertEqual(stacks.groups(),[])
  store.atomic_json('hidden-widgets.json',['uw-calendar'])
  stacks.dropped('uw-clock',self.a,self.b,{'uw-clock':self.b,'uw-calendar':self.b})
  self.assertEqual(stacks.groups(),[])

 def test_drop_merges_existing_stacks_and_preserves_originals(self):
  positions={'Eww - '+wid:{**self.a,'x':200+i*340} for i,wid in enumerate(('uw-clock','uw-calendar','uw-system','uw-music'))}
  store.atomic_json('positions.json',positions)
  stacks.create(['uw-clock','uw-calendar']);stacks.create(['uw-system','uw-music'])
  target=positions['Eww - uw-system'];before=positions['Eww - uw-clock']
  stacks.dropped('uw-clock',before,target,{'uw-clock':target,'uw-system':target})
  self.assertEqual(len(stacks.groups()),1);g=stacks.groups()[0]
  self.assertEqual(set(g['members']),{'uw-clock','uw-calendar','uw-system','uw-music'})
  self.assertEqual(g['original'],{wid:positions['Eww - '+wid] for wid in g['members']})
  self.assertEqual(stacks.excluded(),{'uw-calendar','uw-system','uw-music'})

 def test_failed_merge_rolls_back_groups_and_positions(self):
  before=store.read_json('positions.json',{})
  def engine(*args,**kwargs):
   if args==('open','uw-clock'):raise RuntimeError('render failed')
   return ''
  with patch.object(store,'eww',side_effect=engine):
   with self.assertRaises(RuntimeError):stacks.dropped('uw-clock',self.a,self.b,{'uw-clock':self.b,'uw-calendar':self.b})
  self.assertEqual(stacks.groups(),[]);self.assertEqual(store.read_json('positions.json',{}),before)
