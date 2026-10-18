#!/usr/bin/python3
"""User-created widget stacks: one visible member, shared placement and size."""
import copy
import json
import sys
import time
import uuid
import widget_store as store

FILE='widget-stacks.json'

def groups():
    data=store.read_json(FILE,{'version':1,'groups':[]})
    rows=data.get('groups',[]) if isinstance(data,dict) else None
    if not isinstance(rows,list):raise ValueError('스택 설정을 읽을 수 없습니다.')
    allowed={w['id'] for w in store.catalogue()};seen=set()
    for g in rows:
        members=g.get('members',[])
        if len(members)<2 or len(set(members))!=len(members) or not set(members)<=allowed or seen&set(members) or g.get('active') not in members:
            raise ValueError('스택 구성에 오류가 있습니다.')
        seen.update(members)
    return rows

def save(rows):store.atomic_json(FILE,{'version':1,'groups':rows})
def containing(widget_id,rows=None):return next((g for g in (groups() if rows is None else rows) if widget_id in g['members']),None)
def rect(widget_id,positions):return copy.deepcopy(positions.get('Eww - '+widget_id,{'x':40,'y':80,'width':320,'height':224}))
def current(g,positions):return rect(g['active'],positions)

def candidates(widget_id):
    positions=store.read_json('positions.json',{});target=rect(widget_id,positions);hidden=store.hidden()
    return [w for w in store.catalogue() if w['id']!=widget_id and w['id'] not in hidden and not containing(w['id']) and
            all(rect(w['id'],positions)[k]==target[k] for k in ('width','height'))]

def create(members):
    members=list(dict.fromkeys(members))
    if len(members)<2:raise ValueError('같은 크기의 위젯을 두 개 이상 선택하세요.')
    store.ensure_daemon()
    with store.locked():
        rows=groups();positions=store.read_json('positions.json',{});hidden=store.hidden()
        for wid in members:
            store.find(wid)
            if containing(wid,rows) or wid in hidden:raise ValueError('바탕화면에 추가된 개별 위젯을 선택하세요.')
        target=rect(members[0],positions)
        if any(any(rect(w,positions)[k]!=target[k] for k in ('width','height')) for w in members):raise ValueError('가로와 세로 크기가 같은 위젯만 묶을 수 있습니다.')
        g={'id':'stack-'+uuid.uuid4().hex[:12],'members':members,'active':members[0],
           'original':{w:rect(w,positions) for w in members}}
        save(rows+[g])
    try:
        for wid in members[1:]:store.eww('close',wid,check=False)
        store.eww('open',members[0])
    except Exception:
        with store.locked():save(rows)
        store.eww('open-many',*members,check=False);raise
    return g['id']


def overlap(a,b):
    if (a['width'],a['height'])!=(b['width'],b['height']):return 0
    intersection=max(0,min(a['x']+a['width'],b['x']+b['width'])-max(a['x'],b['x'])) * max(0,min(a['y']+a['height'],b['y']+b['height'])-max(a['y'],b['y']))
    return intersection / max(1,a['width']*a['height'])


def dropped(widget_id,before,after,windows):
    """Merge only after a real body drag ends, using mapped windows as targets.

    Existing overlap at startup, clicks, cancelled drags and resizes never call
    this path. Preserve the incoming card's pre-drag position for splitting.
    """
    store.find(widget_id)
    actual=windows.get(widget_id)
    if not actual or any(abs(actual[k]-after[k])>2 for k in ('x','y','width','height')):return
    with store.locked():
        rows=groups();source=containing(widget_id,rows);hidden=store.hidden();valid={w['id'] for w in store.catalogue()}
        peers=[(overlap(after,r),order,wid) for order,(wid,r) in enumerate(windows.items())
               if wid!=widget_id and wid in valid and wid not in hidden and wid not in excluded()
               and not (source and wid in source['members']) and overlap(after,r)>=.65]
        if not peers:return
        target_id=max(peers)[2];target=containing(target_id,rows)
        original_rows=copy.deepcopy(rows);positions=store.read_json('positions.json',{});original_positions=copy.deepcopy(positions)
        source_members=source['members'] if source else [widget_id]
        target_members=target['members'] if target else [target_id]
        originals={**(target['original'] if target else {target_id:copy.deepcopy(windows[target_id])}),
                   **(source['original'] if source else {widget_id:copy.deepcopy(before)})}
        g={'id':target['id'] if target else 'stack-'+uuid.uuid4().hex[:12],
           'members':target_members+source_members,'active':widget_id,'original':originals}
        rows=[r for r in rows if r is not source and r is not target]+[g]
        placement=copy.deepcopy(windows[target_id])
        for wid in g['members']:positions['Eww - '+wid]=placement
        store.atomic_json('positions.json',positions);save(rows)
    try:
        for wid in (widget_id,target_id):store.eww('close',wid,check=False)
        store.eww('open',widget_id)
    except Exception:
        with store.locked():save(original_rows);store.atomic_json('positions.json',original_positions)
        store.eww('open-many',widget_id,target_id,check=False);raise
    return g['id']


def drop_from_desktop(widget_id,coordinates):
    import subprocess
    values=list(map(int,coordinates))
    if len(values)!=6:raise ValueError('Invalid drag geometry')
    x,y,dx,dy,width,height=values
    if width<=0 or height<=0:raise ValueError('Invalid drag size')
    state=json.loads(subprocess.check_output(['/usr/bin/python3',str(store.CONFIG/'scripts/desktop_geometry.py'),'state'],text=True,timeout=5))
    return dropped(widget_id,{'x':x,'y':y,'width':width,'height':height},
                   {'x':dx,'y':dy,'width':width,'height':height},state['windows'])

def show_member(widget_id,preset=None,point=None):
    store.ensure_daemon()
    with store.locked():
        rows=groups();g=containing(widget_id,rows)
        if not g:raise ValueError('스택에 없는 위젯입니다.')
        if preset is not None and preset not in store.PRESETS:raise ValueError('잘못된 크기입니다.')
        old=g['active'];positions=store.read_json('positions.json',{});before=copy.deepcopy(positions)
        target=store.placement(old,preset,point)
        for wid in g['members']:positions['Eww - '+wid]=target
        g['active']=widget_id;store.atomic_json('positions.json',positions);save(rows)
    try:
        store.eww('close',old,check=False);store.eww('open',widget_id)
    except Exception:
        with store.locked():
            g['active']=old;save(rows);store.atomic_json('positions.json',before)
        store.eww('open',old,check=False);raise
    return target

def cycle(widget_id,direction=1):
    g=containing(widget_id)
    if not g:return
    members=g['members'];return show_member(members[(members.index(g['active'])+direction)%len(members)])

def dissolve(widget_id):
    with store.locked():
        rows=groups();g=containing(widget_id,rows)
        if not g:return
        positions=store.read_json('positions.json',{})
        for wid in g['members']:positions['Eww - '+wid]=g['original'][wid]
        save([r for r in rows if r['id']!=g['id']]);store.atomic_json('positions.json',positions)
    store.eww('close',g['active'],check=False);store.eww('open-many',*g['members'])

def detach(widget_id):
    """Remove a member without losing the rest of its stack."""
    with store.locked():
        rows=groups();g=containing(widget_id,rows)
        if not g:return
        old=g['active'];positions=store.read_json('positions.json',{});target=current(g,positions)
        g['members'].remove(widget_id);g['original'].pop(widget_id,None)
        if old==widget_id:g['active']=g['members'][0]
        if len(g['members'])==1:rows.remove(g)
        positions['Eww - '+g['active']]=target
        store.atomic_json('positions.json',positions);save(rows)
    if old==widget_id:store.eww('open',g['active'])

def excluded():return {wid for g in groups() for wid in g['members'] if wid!=g['active']}

def restore_positions():
    with store.locked():
        positions=store.read_json('positions.json',{})
        for g in groups():
            target=current(g,positions)
            for wid in g['members']:positions['Eww - '+wid]=target
        store.atomic_json('positions.json',positions)

def snapshot():
    return {key:value for g in groups() for wid in g['members'] for key,value in ((wid+'-count',len(g['members'])),(wid+'-label',f"{g['members'].index(wid)+1} / {len(g['members'])}"))}

def main():
    args=sys.argv[1:]
    if args and args[0]=='watch':
        previous=None
        while True:
            try:
                value=snapshot()
                if value!=previous:print(json.dumps(value),flush=True);previous=value
            except (OSError,ValueError):print('{}',flush=True)
            time.sleep(.3)
    elif len(args)==8 and args[0]=='drop':drop_from_desktop(args[1],args[2:])
    elif len(args)==3 and args[0]=='swipe' and args[2] in ('next','prev'):cycle(args[1],-1 if args[2]=='prev' else 1)
    elif len(args)==2 and args[0] in ('next','prev','up','down','split'):
        if args[0]=='split':dissolve(args[1])
        else:cycle(args[1],-1 if args[0] in ('prev','up') else 1)
    else:raise SystemExit('Usage: stacks.py watch | next|prev|split <widget-id> | drop <widget-id> x y dx dy width height | swipe <widget-id> next|prev')

if __name__=='__main__':
    try:main()
    except (BrokenPipeError,KeyboardInterrupt):pass
