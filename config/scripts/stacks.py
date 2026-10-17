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
    elif len(args)==2 and args[0] in ('next','prev','up','down','split'):
        if args[0]=='split':dissolve(args[1])
        else:cycle(args[1],-1 if args[0] in ('prev','up') else 1)
    else:raise SystemExit('Usage: stacks.py watch | next|prev|split <widget-id>')

if __name__=='__main__':
    try:main()
    except (BrokenPipeError,KeyboardInterrupt):pass
