import datetime as dt
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'config/scripts'))
import todomate

class TodomateTests(unittest.TestCase):
 def test_widget_shell_command_dispatches_check_and_uncheck(self):
  with tempfile.TemporaryDirectory(prefix='todomate-action-') as temporary:
   config=Path(temporary);scripts=config/'scripts';scripts.mkdir();empty_path=config/'empty-path';empty_path.mkdir()
   backend=scripts/'todomate_webview.py'
   backend.write_text('import json,sys\nfrom pathlib import Path\nwith (Path(__file__).parent.parent/"actions.jsonl").open("a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")\n')
   env={**os.environ,'EWW_WIDGET_CONFIG':temporary,'PATH':str(empty_path)}
   date=dt.date.today().isoformat()
   for done in ('false','true'):
    # Eww executes this exact command through /bin/sh. No real account is used.
    command=shlex.join([str(ROOT/'config/scripts/todomate.py'),'toggle','fixture-task',done,date])
    result=subprocess.run(['/bin/sh','-c',command],env=env,capture_output=True,text=True,timeout=5)
    self.assertEqual(result.returncode,0,result.stderr)
   actions=[json.loads(row) for row in (config/'actions.jsonl').read_text().splitlines()]
   self.assertEqual(actions,[['toggle','fixture-task','false',date],['toggle','fixture-task','true',date]])

 def test_completed_tasks_leave_active_list_without_losing_restore_data(self):
  now=time.time();date=dt.datetime.fromtimestamp(now).strftime('%Y-%m-%d')
  rows=[{'id':name,'text':name,'done':done} for name,done in [('done-a',True),('open-a',False),('done-b',True),('open-b',False)]]
  value={'status':'ready','updated':now,'date':date,'tasks':rows,'pending':['open-a']}
  result=todomate.normalize(value,now)
  self.assertEqual([t['id'] for t in result['todomate_tasks']],[t['id'] for t in rows])
  self.assertEqual([t['id'] for t in result['todomate_open_tasks']],['open-a','open-b'])
  self.assertEqual([t['id'] for t in result['todomate_completed_tasks']],['done-a','done-b'])
  self.assertTrue(result['todomate_open_tasks'][0]['pending'])
  self.assertEqual(result['todomate_completed_count'],2)
  self.assertEqual(result['todomate_count'],'2 / 4 완료')
  rows[0]['done']=False
  restored=todomate.normalize(value,now)
  self.assertEqual([t['id'] for t in restored['todomate_open_tasks']],['done-a','open-a','open-b'])
  for row in rows:row['done']=True
  finished=todomate.normalize(value,now)
  self.assertEqual(finished['todomate_open_tasks'],[])
  self.assertEqual(len(finished['todomate_completed_tasks']),4)
  self.assertIn('모두 완료',finished['todomate_message'])
  signed_out=todomate.normalize({**value,'status':'signed_out'},now)
  self.assertEqual(signed_out['todomate_completed_tasks'],[])
  self.assertEqual(signed_out['todomate_open_tasks'],[])

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
