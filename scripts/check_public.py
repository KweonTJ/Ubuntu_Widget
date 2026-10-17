#!/usr/bin/python3
"""Reject personalized defaults and common credential material in the publish tree."""
import json
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parent.parent
errors=[]
def check(condition,message):
    if not condition:errors.append(message)
def read(name):return json.loads((ROOT/'config'/name).read_text())
check(read('positions.json')=={},'Positions must be blank.')
check(read('web-widgets.json')=={'version':1,'widgets':[]},'Website defaults must be blank.')
check(read('enabled-widgets.json')==[],'Optional widgets must start unadded.')
check(set(read('hidden-widgets.json'))=={'uw-clock','uw-calendar','uw-system','uw-music','uw-battery','uw-sound'},'The public desktop must start empty.')
check(read('glass-settings.json')=={'enabled':False,'overrides':{}},'Glass must be opt-in.')
expected={'stocks':{'connected':False,'symbols':[],'indices':[]},'weather':{'connected':False,'city':'','latitude':0,'longitude':0},'home':{'connected':False,'url':'','entities':[]},'screentime':{'enabled':False}}
check(read('connections.json')==expected,'Provider settings must be blank and disconnected.')
check(read('widget-settings.json')=={'note':{'title':'Note','text':''},'todo':{'tasks':[]},'agenda':{'events':[]}},'Notes/tasks/events must be blank.')
files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
patterns=[r'/(?:home|Users)/[^\s/"\']+/',r'gh[pousr]_[A-Za-z0-9]{25,}',r'github_pat_[A-Za-z0-9_]{25,}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'tsck_live_[A-Za-z0-9_-]{24,}']
for name in filter(None,files):
    path=ROOT/name
    if not path.is_file():continue
    check(not path.is_symlink(),'Unexpected symlink: '+name)
    check(path.suffix not in {'.mp4','.webm','.xwd','.pyc','.log','.key','.pem'} and not name.endswith('.tar.gz'),'Unexpected private/binary export: '+name)
    if path.suffix=='.png':continue
    try:text=path.read_text()
    except UnicodeError:errors.append('Unexpected binary file: '+name);continue
    for pattern in patterns:
        if re.search(pattern,text):errors.append('Potential personal path or credential in '+name);break
    if name.endswith('.yuck'):
        check('2c377c283d203942' not in text,'Machine-specific socket identifier in '+name)
if errors:
    print('\n'.join(sorted(set(errors))),file=sys.stderr);sys.exit(1)
print(f'Public export checks passed for {len(list(filter(None,files)))} files. No personalized defaults or credential patterns found.')
