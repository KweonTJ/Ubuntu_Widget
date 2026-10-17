#!/usr/bin/python3
"""Local-only data, persisted notes/tasks and countdown controls."""
import datetime as dt
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
from zoneinfo import ZoneInfo
import widget_store as store

def settings():
    raw=store.read_json('widget-settings.json',{})
    if not isinstance(raw,dict):raise ValueError('위젯 설정 형식이 올바르지 않습니다.')
    return raw

def defaults(kind):
    return {'agenda':{'events':[]},'note':{'title':'Note','text':''},
            'todo':{'tasks':[]},
            'focus':{'minutes':25,'remaining':1500,'running':False,'deadline':0,'finished':False},
            'countdown':{'title':'새해까지','date':f'{dt.date.today().year+1}-01-01'}}[kind].copy()

def config(kind):return {**defaults(kind),**settings().get(kind,{})}

def save_config(kind,values):
    with store.locked():
        all_settings=settings();old={**defaults(kind),**all_settings.get(kind,{})}
        if kind=='note':
            title=values['title'].strip();text=values['text'].strip()
            if not title or len(title)>40 or len(text)>2000:raise ValueError('제목은 1~40자, 메모는 최대 2,000자로 입력하세요.')
            new={'title':title,'text':text}
        elif kind=='todo':
            lines=[s.strip() for s in values['text'].splitlines() if s.strip()]
            if len(lines)>12 or any(len(s)>120 for s in lines):raise ValueError('할 일은 최대 12개, 각 120자까지 입력할 수 있습니다.')
            # Preserve completed state and IDs of unchanged entries, including duplicates.
            remaining=list(old['tasks']);tasks=[]
            for text in lines:
                index=next((i for i,t in enumerate(remaining) if t['text']==text),None)
                tasks.append(remaining.pop(index) if index is not None else {'id':uuid.uuid4().hex[:8],'text':text,'done':False})
            new={'tasks':tasks}
        elif kind=='agenda':
            lines=[line.strip() for line in values['text'].splitlines() if line.strip()]
            if len(lines)>40:raise ValueError('일정은 최대 40개까지 저장할 수 있습니다.')
            events=[]
            for line in lines:
                try:
                    date,title=line.split('|',1);date=dt.datetime.strptime(date.strip(),'%Y-%m-%d %H:%M');title=title.strip()
                except ValueError:raise ValueError('YYYY-MM-DD HH:MM | 일정 제목 형식으로 입력하세요.')
                if not title or len(title)>120:raise ValueError('일정 제목은 1~120자로 입력하세요.')
                events.append({'at':date.strftime('%Y-%m-%d %H:%M'),'title':title})
            new={'events':sorted(events,key=lambda row:row['at'])}
        elif kind=='focus':
            minutes=int(values['minutes'])
            if not 1<=minutes<=180:raise ValueError('집중 시간은 1~180분으로 설정하세요.')
            new={'minutes':minutes,'remaining':minutes*60,'running':False,'deadline':0,'finished':False}
        elif kind=='countdown':
            title=values['title'].strip()
            if not title or len(title)>40:raise ValueError('제목은 1~40자로 입력하세요.')
            try:date=dt.date.fromisoformat(values['date']).isoformat()
            except ValueError:raise ValueError('날짜를 YYYY-MM-DD 형식으로 입력하세요. 예: 2027-01-01')
            new={'title':title,'date':date}
        else:raise ValueError('설정할 수 없는 위젯입니다.')
        all_settings[kind]=new;store.atomic_json('widget-settings.json',all_settings)

def action(name,argument=None,now=None):
    now=time.time() if now is None else now
    with store.locked():
        state=settings()
        if name=='toggle-task':
            if not re.fullmatch('[a-f0-9]{8}',argument or ''):raise ValueError('잘못된 할 일입니다.')
            todo={**defaults('todo'),**state.get('todo',{})}
            for task in todo['tasks']:
                if task['id']==argument:task['done']=not task['done']
            state['todo']=todo
        elif name in ('focus-toggle','focus-reset','focus-complete'):
            focus={**defaults('focus'),**state.get('focus',{})}
            if name=='focus-reset':focus.update(remaining=focus['minutes']*60,running=False,deadline=0,finished=False)
            elif name=='focus-toggle':
                if focus['running']:focus.update(remaining=max(0,focus['deadline']-now),running=False)
                else:
                    remaining=focus['remaining'] if focus['remaining']>0 else focus['minutes']*60
                    focus.update(remaining=remaining,deadline=now+remaining,running=True,finished=False)
            else:
                if not focus['running'] or focus['deadline']>now:return False
                focus.update(remaining=0,running=False,finished=True)
            state['focus']=focus
        else:raise ValueError('알 수 없는 동작입니다.')
        store.atomic_json('widget-settings.json',state)
    return True

def network_totals():
    rx=tx=0
    for line in Path('/proc/net/dev').read_text().splitlines()[2:]:
        interface,data=line.split(':',1)
        if interface.strip()=='lo':continue
        columns=data.split();rx+=int(columns[0]);tx+=int(columns[8])
    return rx,tx

def rate(value):
    value=max(0,value)
    return f'{value/1048576:.1f} MB/s' if value>=1048576 else f'{value/1024:.1f} KB/s'

def snapshot(previous=None,now=None,now_epoch=None):
    now=now or dt.datetime.now().astimezone();epoch=time.time() if now_epoch is None else now_epoch
    state=settings();output={}
    events={**defaults('agenda'),**state.get('agenda',{})}['events']
    upcoming=[{'title':e['title'],'at':e['at'],'date':e['at'][5:10],'time':e['at'][11:]} for e in events if e['at']>=now.strftime('%Y-%m-%d %H:%M')]
    output.update(agenda=upcoming[:12],agenda_empty=not upcoming)
    output['world']=[{'city':city,'time':now.astimezone(ZoneInfo(zone)).strftime('%H:%M'),
                      'date':now.astimezone(ZoneInfo(zone)).strftime('%m/%d')}
                     for city,zone in state.get('worldclock',{}).get('cities',[('Seoul','Asia/Seoul'),('Tokyo','Asia/Tokyo'),('London','Europe/London'),('New York','America/New_York')])]
    output.update(today=str(now.day),month=f'{now.year}년 {now.month}월',weekday='월화수목금토일'[now.weekday()]+'요일',week=f'올해의 {now.isocalendar().week}번째 주')
    seconds=now.hour*3600+now.minute*60+now.second
    output.update(day_percent=round(seconds/86400*100),day_left=f'{(86400-seconds)//3600}시간 {(86400-seconds)%3600//60}분 남음')
    year_start=dt.date(now.year,1,1);next_year=dt.date(now.year+1,1,1);days=(next_year-now.date()).days
    output.update(year=str(now.year),year_percent=round(((now.date()-year_start).days+seconds/86400)/(next_year-year_start).days*100),year_left=f'{now.year+1}년까지 {days}일')
    uptime=int(float(Path('/proc/uptime').read_text().split()[0]))
    output.update(uptime=f'{uptime//86400}일 {uptime%86400//3600}시간',uptime_detail=f'{uptime%3600//60}분 · 마지막 부팅 이후')
    totals=network_totals();monotonic=time.monotonic()
    if previous:
        elapsed=max(.01,monotonic-previous[0]);down=rate((totals[0]-previous[1])/elapsed);up=rate((totals[1]-previous[2])/elapsed)
    else:down=up='측정 중…'
    output.update(download=down,upload=up)
    note={**defaults('note'),**state.get('note',{})};output.update(note_title=note['title'],note_text=note['text'] or '메모가 비어 있습니다.')
    todo={**defaults('todo'),**state.get('todo',{})};tasks=todo['tasks'];output.update(tasks=tasks,tasks_count=f"{sum(t['done'] for t in tasks)} / {len(tasks)} 완료",tasks_empty=not tasks)
    countdown={**defaults('countdown'),**state.get('countdown',{})};delta=(dt.date.fromisoformat(countdown['date'])-now.date()).days
    output.update(countdown_title=countdown['title'],countdown_date=countdown['date'],countdown_value='D-DAY' if delta==0 else f'D−{delta}' if delta>0 else f'D+{-delta}')
    focus={**defaults('focus'),**state.get('focus',{})}
    remaining=max(0,math.ceil(focus['deadline']-epoch)) if focus['running'] else math.ceil(focus['remaining'])
    output.update(focus_time=f'{remaining//60:02}:{remaining%60:02}',focus_button='일시정지' if focus['running'] else '다시 시작' if focus['finished'] else '시작',
                  focus_detail='집중 완료' if focus['finished'] else f"{focus['minutes']}분 집중",focus_percent=round(100*(1-remaining/(focus['minutes']*60))))
    return (monotonic,*totals),output,focus['running'] and remaining==0

def main():
    if len(sys.argv)>1 and sys.argv[1]=='action':action(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else None);return
    previous=None
    while True:
        try:
            previous,data,finished=snapshot(previous)
            if finished and action('focus-complete'):
                subprocess.run(['notify-send','--app-name=위젯 보관함','집중 시간 완료','잠깐 쉬어 가세요.'],timeout=3,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            print(json.dumps(data,ensure_ascii=False),flush=True)
        except (OSError,ValueError,KeyError,subprocess.SubprocessError) as exc:print(str(exc),file=sys.stderr,flush=True)
        if len(sys.argv)>1 and sys.argv[1]=='once':break
        time.sleep(1)

if __name__=='__main__':
    try:main()
    except (BrokenPipeError,KeyboardInterrupt):pass
