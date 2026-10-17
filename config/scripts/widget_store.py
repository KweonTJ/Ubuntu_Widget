#!/usr/bin/python3
"""Shared widget catalogue, persistence and safe desktop actions."""
from pathlib import Path
from contextlib import contextmanager
import datetime as dt
import fcntl
import json
import math
import os
import re
import subprocess
import tempfile
import urllib.parse
import uuid
from widget_catalog import EXTRA_WIDGETS, SITE_PRESETS, ORIGINAL_CATEGORIES

CONFIG = Path(os.environ.get('EWW_WIDGET_CONFIG', Path(__file__).resolve().parent.parent))
BINARY = os.environ.get('EWW_WIDGET_BINARY',str(Path.home()/'.local/lib/ubuntu-widget/eww'))
PRESETS = {'small': (208, 208), 'medium': (320, 224), 'large': (432, 352)}
BUILTINS = [
    {'id':'uw-clock','name':'시계','kind':'clock','description':'현재 시각과 날짜를 한눈에 확인하세요.','icon':'preferences-system-time-symbolic'},
    {'id':'uw-calendar','name':'달력','kind':'calendar','description':'이번 달의 날짜와 오늘을 확인하세요.','icon':'x-office-calendar-symbolic'},
    {'id':'uw-system','name':'시스템','kind':'system','description':'CPU, 메모리, 저장공간 사용량을 확인하세요.','icon':'computer-symbolic'},
    {'id':'uw-music','name':'음악','kind':'music','description':'재생 중인 음악을 확인하고 제어하세요.','icon':'audio-x-generic-symbolic'},
    {'id':'uw-battery','name':'배터리','kind':'battery','description':'PC와 연결된 블루투스 기기의 배터리를 확인하세요.','icon':'battery-good-symbolic'},
    {'id':'uw-sound','name':'사운드','kind':'sound','description':'소리를 조절하거나 음소거하세요.','icon':'audio-volume-high-symbolic'},
]
for item in BUILTINS:item['category']=ORIGINAL_CATEGORIES[item['kind']]
ORIGINAL_IDS={w['id'] for w in BUILTINS}
BUILTINS += EXTRA_WIDGETS
EXTRA_IDS={w['id'] for w in EXTRA_WIDGETS}
WEB_ID = re.compile(r'^uw-web-[a-f0-9]{12}$')

def read_json(name, default):
    try:return json.loads((CONFIG/name).read_text())
    except FileNotFoundError:return default
    except (ValueError, OSError) as exc:raise ValueError(f'{name} 설정을 읽을 수 없습니다: {exc}') from exc

def atomic_json(name, data):
    atomic_text(name, json.dumps(data, ensure_ascii=False, indent=2)+'\n')

def atomic_text(name, text):
    target=CONFIG/name
    if target.exists() and target.read_text()==text:return
    fd,tmp=tempfile.mkstemp(prefix='.'+target.name+'.',dir=target.parent)
    try:
        with os.fdopen(fd,'w') as f:f.write(text)
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

@contextmanager
def locked():
    with (CONFIG/'widget-state.lock').open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        yield

def normalize_url(raw):
    raw=raw.strip()
    if not raw or any(ord(c)<32 or ord(c)==127 or c.isspace() for c in raw):
        raise ValueError('공백 없이 웹사이트 주소를 입력하세요.')
    if '://' not in raw:raw='https://'+raw
    try:
        parts=urllib.parse.urlsplit(raw)
        port=parts.port
    except ValueError as exc:raise ValueError('올바른 웹사이트 주소를 입력하세요.') from exc
    if parts.scheme.lower() not in ('https','http') or not parts.hostname or parts.username is not None or parts.password is not None:
        raise ValueError('http 또는 https 웹사이트 주소만 사용할 수 있습니다.')
    if any(c in parts.netloc for c in '\\<>"\''):
        raise ValueError('웹사이트 주소를 확인하세요.')
    return urllib.parse.urlunsplit((parts.scheme.lower(),parts.netloc,parts.path or '/',parts.query,parts.fragment))

def web_widgets():
    raw=read_json('web-widgets.json',{'version':1,'widgets':[]})
    if not isinstance(raw,dict) or not isinstance(raw.get('widgets'),list):
        raise ValueError('웹 위젯 목록 형식이 올바르지 않습니다.')
    result=[];seen=set()
    for item in raw['widgets']:
        if not isinstance(item,dict) or not WEB_ID.fullmatch(str(item.get('id',''))) or item['id'] in seen:
            raise ValueError('웹 위젯 ID가 올바르지 않습니다.')
        name=str(item.get('name','')).strip()
        if not name or len(name)>60:raise ValueError('웹 위젯 이름은 1~60자여야 합니다.')
        result.append({**item,'name':name,'url':normalize_url(item.get('url','')),'kind':'web',
                       'category':'web','description':'누르면 독립 웹앱 창에서 열립니다.','icon':'web-browser-symbolic'})
        seen.add(item['id'])
    return result

def catalogue():return BUILTINS+web_widgets()
def library():
    webs=web_widgets();urls={w['url'] for w in webs}
    return BUILTINS+[p for p in SITE_PRESETS if normalize_url(p['url']) not in urls]+webs

def library_find(widget_id):
    for item in library():
        if item['id']==widget_id:return item
    return find(widget_id)

def add_library(widget_id,preset=None,point=None):
    item=library_find(widget_id)
    if item['kind']=='webpreset':widget_id=create_web(item['name'],item['url'])
    show(widget_id,preset,point)
    return widget_id

def enabled_extras():return set(read_json('enabled-widgets.json',[])) & EXTRA_IDS

def find(widget_id):
    for item in catalogue():
        if item['id']==widget_id:return item
    raise ValueError('목록에 없는 위젯입니다.')

def hidden():
    raw=read_json('hidden-widgets.json',[])
    if not isinstance(raw,list):raise ValueError('숨김 상태 형식이 올바르지 않습니다.')
    return set(raw).intersection(item['id'] for item in catalogue()) | (EXTRA_IDS-enabled_extras())

def eww(*args,check=True):
    result=subprocess.run([BINARY,'--config',str(CONFIG),*args],capture_output=True,text=True,timeout=12)
    if check and result.returncode:raise RuntimeError(result.stderr.strip() or result.stdout.strip() or '위젯 실행에 실패했습니다.')
    return result.stdout.strip()

def ensure_daemon():
    result=subprocess.run(['/usr/bin/python3',str(CONFIG/'scripts/start-service.py')],capture_output=True,text=True,timeout=30)
    if result.returncode:raise RuntimeError(result.stderr.strip() or '위젯 서비스를 시작할 수 없습니다.')

def visible():
    try:return {line.split(':',1)[0] for line in eww('active-windows',check=False).splitlines() if ':' in line}
    except (OSError, subprocess.TimeoutExpired):return set()

def render_web_windows(items):
    # Only locally generated identifiers enter Yuck. User text stays in JSON.
    lines=['; Generated by the widget gallery. Edit websites in the gallery.\n']
    for item in items:
        widget_id=item['id']
        if not WEB_ID.fullmatch(widget_id):raise ValueError('Invalid widget identifier')
        lines.append(f'''(defwindow {widget_id}
  :monitor '["<primary>", 0]'
  :geometry (geometry :anchor "top right" :x "-32px" :y "51px" :width "320px" :height "224px")
  :stacking "bg" :windowtype "desktop" :wm-ignore false :resizable true
  (movable-card :theme appearance :name "{widget_id}" (web-card :id "{widget_id}")))
''')
    return ''.join(lines)

def save_webs(items):
    clean=[{k:item[k] for k in ('id','name','url','created') if k in item} for item in items]
    atomic_json('web-widgets.json',{'version':1,'widgets':clean})
    atomic_text('web-windows.yuck',render_web_windows(clean))

def create_web(name,url):
    name=name.strip();url=normalize_url(url)
    if not name or len(name)>60 or any(ord(c)<32 for c in name):raise ValueError('이름을 1~60자로 입력하세요.')
    with locked():
        items=web_widgets()
        # Reuse a registered URL so repeated preset clicks do not create duplicates.
        for item in items:
            if item['url']==url:return item['id']
        item={'id':'uw-web-'+uuid.uuid4().hex[:12],'name':name,'url':url,'created':dt.datetime.now().isoformat(timespec='seconds')}
        previous=hidden();save_webs(items+[item])
        atomic_json('hidden-widgets.json',sorted(previous|{item['id']}))
    return item['id']

def edit_web(widget_id,name,url):
    item=find(widget_id)
    if item['kind']!='web':raise ValueError('웹사이트만 수정할 수 있습니다.')
    name=name.strip();url=normalize_url(url)
    if not name or len(name)>60 or any(ord(c)<32 for c in name):raise ValueError('이름을 1~60자로 입력하세요.')
    with locked():
        items=web_widgets()
        for entry in items:
            if entry['id']==widget_id:entry.update(name=name,url=url)
        save_webs(items)

def delete_web(widget_id):
    item=find(widget_id)
    if item['kind']!='web':raise ValueError('기본 위젯은 목록에서 삭제할 수 없습니다.')
    if widget_id in visible():eww('close',widget_id)
    with locked():
        oldhidden=hidden();items=[w for w in web_widgets() if w['id']!=widget_id]
        save_webs(items);atomic_json('hidden-widgets.json',sorted(oldhidden-{widget_id}))
        positions=read_json('positions.json',{});positions.pop('Eww - '+widget_id,None);atomic_json('positions.json',positions)

def bounded_position(x,y,width,height,area):
    left,top,aw,ah=area
    width=min(width,max(1,aw-16));height=min(height,max(1,ah-16))
    def snap(v,origin,available):
        return origin+max(0,min(round((v-origin)/16),max(0,available)//16))*16
    return {'x':snap(x,left+8,aw-width-16),'y':snap(y,top+8,ah-height-16),'width':width,'height':height}

def pick_free_position(width,height,area,occupied):
    left,top,aw,ah=area
    for y in range(top+8,max(top+9,top+ah-height-7),16):
        for x in range(left+aw-width-8,left+7,-16):
            candidate=bounded_position(x,y,width,height,area)
            if all(candidate['x']+candidate['width']+8<=r['x'] or r['x']+r['width']+8<=candidate['x'] or
                   candidate['y']+candidate['height']+8<=r['y'] or r['y']+r['height']+8<=candidate['y'] for r in occupied):
                return candidate
    return bounded_position(left+32,top+32,width,height,area)

def placement(widget_id,preset,point):
    # GDK/X11 must not be called from the gallery worker thread. Query in a
    # short-lived process with its own display connection instead.
    args=['/usr/bin/python3',str(CONFIG/'scripts/desktop_geometry.py'),'state']
    if point is not None:args.extend(str(int(v)) for v in point)
    state=json.loads(subprocess.check_output(args,text=True,timeout=5))
    area,windows=state['area'],state['windows']
    placements=read_json('positions.json',{})
    # Eww briefly recreates windows at default coordinates during a config
    # reload. Saved user placements are authoritative during that interval.
    hidden_ids=hidden()
    for item in catalogue():
        saved_rect=placements.get('Eww - '+item['id'])
        if saved_rect and item['id'] not in hidden_ids:
            windows[item['id']]={**windows.get(item['id'],{'width':320,'height':224}),**saved_rect}
    saved=placements.get('Eww - '+widget_id)
    current=saved or windows.get(widget_id)
    w,h=PRESETS[preset] if preset else ((current.get('width',320),current.get('height',224)) if current else PRESETS['medium'])
    if point is not None:return bounded_position(point[0]-w//2,point[1]-h//2,w,h,area)
    if current:return bounded_position(current['x'],current['y'],w,h,area)
    return pick_free_position(w,h,area,list(windows.values()))

def show(widget_id,preset=None,point=None):
    item=find(widget_id)
    if preset is not None and preset not in PRESETS:raise ValueError('잘못된 크기입니다.')
    ensure_daemon()
    with locked():
        oldhidden=hidden();positions=read_json('positions.json',{});previous=positions.get('Eww - '+widget_id)
        target=placement(widget_id,preset,point)
        positions['Eww - '+widget_id]=target;atomic_json('positions.json',positions)
    was_visible=widget_id in visible()
    try:
        if was_visible:eww('close',widget_id)
        if item['kind']=='web':eww('reload')
        eww('open',widget_id)
    except Exception:
        with locked():
            latest=read_json('positions.json',{})
            if previous is None:latest.pop('Eww - '+widget_id,None)
            else:latest['Eww - '+widget_id]=previous
            atomic_json('positions.json',latest)
        if was_visible:eww('open',widget_id,check=False)
        raise
    with locked():
        previous_hidden=hidden()
        if widget_id in EXTRA_IDS:atomic_json('enabled-widgets.json',sorted(enabled_extras()|{widget_id}))
        atomic_json('hidden-widgets.json',sorted(previous_hidden-{widget_id}))
    return target

def remove(widget_id):
    find(widget_id)
    if widget_id in visible():eww('close',widget_id)
    with locked():atomic_json('hidden-widgets.json',sorted(hidden()|{widget_id}))

def open_visible():
    items=[w['id'] for w in catalogue() if w['id'] not in hidden()]
    if items:eww('open-many',*items)

def restore():
    ensure_daemon()
    for item in catalogue():
        if item['id'] in hidden() and (item['id'] not in EXTRA_IDS or item['id'] in enabled_extras()):show(item['id'])
    open_visible()

def launch_web(widget_id):
    item=find(widget_id)
    if item['kind']!='web':raise ValueError('웹사이트 위젯이 아닙니다.')
    url=normalize_url(item['url'])
    # No shell interpolation: website names/URLs are data, never commands.
    import shutil
    chrome=next((shutil.which(name) for name in ('google-chrome','chromium','chromium-browser') if shutil.which(name)),None)
    command=[chrome,'--app='+url] if chrome else ['xdg-open',url]
    subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
