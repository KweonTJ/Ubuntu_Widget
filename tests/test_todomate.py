import datetime as dt
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'config/scripts'))
import todomate

class TodomateTests(unittest.TestCase):
 def test_snapshot_requires_current_day_fresh_session_and_valid_rows(self):
  now=time.time();date=dt.datetime.fromtimestamp(now).strftime('%Y-%m-%d')
  value={'status':'ready','updated':now,'date':date,'tasks':[{'id':'own_task-1','text':'Today','done':False}],'pending':[]}
  self.assertTrue(todomate.normalize(value,now)['todomate_ready'])
  for mutation in ({'updated':now-61},{'date':'2000-01-01'},{'status':'signed_out'},{'status':'error'},{'tasks':[{'id':'bad / task','text':'Today','done':False}]}):
   s=todomate.normalize({**value,**mutation},now)
   self.assertFalse(s['todomate_ready']);self.assertEqual(s['todomate_tasks'],[])
  offline=todomate.normalize({**value,'status':'cached'},now)
  self.assertEqual(offline['todomate_status'],'cached')
  self.assertEqual(todomate.normalize({**value,'pending':['own_task-1']},now)['todomate_tasks'][0]['pending'],True)

 @unittest.skipUnless(shutil.which('node'),'Node is needed for the local page-adapter contract test')
 def test_session_adapter_checks_owner_day_conflicts_and_running_timers(self):
  result=subprocess.run(['node',str(ROOT/'tests/todomate-bridge-test.js'),str(ROOT/'config/scripts/todomate_bridge.js')],capture_output=True,text=True,timeout=10)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
  self.assertIn('Adapter contract passed',result.stdout)
