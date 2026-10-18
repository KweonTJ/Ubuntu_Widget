#!/usr/bin/python3
"""Native task snapshot; authentication belongs to the official page, not this code."""
import datetime as dt
import json
import re
import time
from pathlib import Path
import subprocess
import widget_store as store

STATE = '.web-profile/todomate/widget-state.json'
ID = re.compile(r'^[A-Za-z0-9_-]{1,200}$')
ERRORS = {'timer_running':'타이머가 진행 중인 할 일은 todomate에서 완료해 주세요.',
          'permission-denied':'접근 권한을 확인할 수 없습니다. 공식 화면에서 다시 연결하세요.',
          'unavailable':'네트워크 연결을 확인하세요.', 'stale_task':'할 일이 변경되었습니다. 목록을 새로 확인하세요.',
          'schema_changed':'todomate 형식이 바뀌어 연결을 확인해야 합니다.',
          'load_failed':'todomate 페이지를 열지 못했습니다.', 'load_timeout':'연결 시간이 초과되었습니다. 다시 시도하세요.',
          'web_process_terminated':'연결 화면이 종료되었습니다. 다시 시도하세요.'}


def normalize(value, now=None):
    now=time.time() if now is None else now
    date=dt.datetime.fromtimestamp(now).strftime('%Y-%m-%d')
    result={'todomate_status':'signed_out','todomate_message':'todomate를 연결해 오늘의 할 일을 확인하세요.',
            'todomate_tasks':[],'todomate_open_tasks':[],'todomate_completed_tasks':[],
            'todomate_completed_count':0,'todomate_count':'','todomate_ready':False,'todomate_date':date}
    if not isinstance(value,dict):return result
    status=value.get('status','signed_out')
    if status in ('loading','syncing'):result.update(todomate_status=status,todomate_message='오늘의 할 일을 불러오는 중…')
    elif status=='error':result.update(todomate_status='error',todomate_message=ERRORS.get(value.get('error'),'연결을 확인하지 못했습니다. 다시 시도하세요.'))
    if status not in ('ready','cached'):return result
    if value.get('date')!=date or now-float(value.get('updated',0))>60:
        result.update(todomate_status='error',todomate_message='연결이 중단되었습니다. 다시 연결하세요.');return result
    tasks=[];pending=set(value.get('pending',[]))
    for row in value.get('tasks',[]):
        if not isinstance(row,dict) or not ID.fullmatch(str(row.get('id',''))) or not isinstance(row.get('text'),str) or not isinstance(row.get('done'),bool):
            result.update(todomate_status='error',todomate_message=ERRORS['schema_changed']);return result
        tasks.append({'id':row['id'],'text':row['text'][:1000],'done':row['done'],'pending':row['id'] in pending})
    open_tasks=[task for task in tasks if not task['done']]
    completed_tasks=[task for task in tasks if task['done']]
    result.update(todomate_status=status,todomate_ready=True,todomate_tasks=tasks,
                  todomate_open_tasks=open_tasks,todomate_completed_tasks=completed_tasks,
                  todomate_completed_count=len(completed_tasks),
                  todomate_count=f"{len(completed_tasks)} / {len(tasks)} 완료",
                  todomate_message='오늘의 할 일이 없습니다.' if not tasks else '오프라인 · 저장된 목록' if status=='cached' else '오늘의 할 일을 모두 완료했어요.' if not open_tasks else '')
    return result


def snapshot():
    try:return normalize(json.loads((store.CONFIG/STATE).read_text()))
    except (OSError,ValueError,TypeError):return normalize(None)


def ensure_running():
    """Only start the private page when the task widget is enabled."""
    try:
        if 'uw-todo' not in store.enabled_extras() or 'uw-todo' in store.hidden():return
        import dbus
        name=__import__('os').environ.get('EWW_WIDGET_APP_ID','local.ubuntu.WidgetLibrary')+'.Todomate'
        if dbus.SessionBus().name_has_owner(name):return
        subprocess.Popen(['/usr/bin/python3',str(store.CONFIG/'scripts/manager-launch.py'),'app','todomate-sync'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except Exception:return


def toggle(task_id, done, date):
    if not ID.fullmatch(task_id) or done not in ('true','false') or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date):raise ValueError('Invalid task action')
    subprocess.run(['/usr/bin/python3',str(store.CONFIG/'scripts/todomate_webview.py'),'toggle',task_id,done,date],check=True,timeout=15)


if __name__=='__main__':
    import sys
    if len(sys.argv)==5 and sys.argv[1]=='toggle':toggle(*sys.argv[2:])
