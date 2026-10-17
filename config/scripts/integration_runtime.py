#!/usr/bin/python3
"""Non-blocking provider polling and opt-in, local application usage counts."""
from concurrent.futures import ThreadPoolExecutor
import ctypes as C
import ctypes.util
import datetime as dt
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import connections as con
import widget_store as store

CACHE=Path(os.environ.get('EWW_INTEGRATION_CACHE',Path(os.environ.get('XDG_CACHE_HOME',Path.home()/'.cache'))/'ubuntu-widget/integrations'))

def cache_write(name,value):
    CACHE.mkdir(parents=True,exist_ok=True,mode=0o700)
    target=CACHE/name;temp=target.with_suffix('.tmp-'+str(os.getpid()))
    temp.write_text(json.dumps(value,ensure_ascii=False));os.chmod(temp,0o600);temp.replace(target)

def cache_read(name,default):
    try:return json.loads((CACHE/name).read_text())
    except (OSError,ValueError):return default

def empty(kind):
    shared={'status':'설정에서 연결해 주세요.','updated':0,'rows':[],'error':False}
    if kind=='weather':shared.update(city='지역을 선택하세요',temperature='—',condition='',range='',air='',hours=[],week=[])
    return shared

def refresh(kind,cfg):
    if kind=='weather':return con.weather_snapshot(cfg)
    if kind=='stocks':return con.refresh_toss(cfg)
    secret=con.Secrets().get('home')
    if not secret:raise con.ConnectionError('홈 연결을 다시 설정하세요.',401)
    return con.home_snapshot(cfg,secret)

class Poller:
    def __init__(self):
        self.pool=ThreadPoolExecutor(max_workers=3);self.jobs={};self.next={};self.generations={};self.data={k:empty(k) for k in ('weather','stocks','home')}
    def step(self,configs,active,now=None):
        now=time.monotonic() if now is None else now
        for kind in self.data:
            cfg=configs[kind];generation=json.dumps(cfg,sort_keys=True)
            if self.generations.get(kind)!=generation:
                self.generations[kind]=generation;self.next[kind]=0;self.data[kind]=empty(kind)
            if kind in self.jobs and self.jobs[kind][0].done():
                future,old=self.jobs.pop(kind)
                if old==generation and cfg['connected']:
                    try:self.data[kind]={**empty(kind),**future.result()};self.next[kind]=now+(900 if kind=='weather' else 30)
                    except Exception as exc:
                        error=exc if isinstance(exc,con.ConnectionError) else con.ConnectionError('서비스 응답을 처리하지 못했습니다. 설정을 확인하세요.')
                        self.data[kind]['status']=str(error);self.data[kind]['error']=True
                        self.next[kind]=float('inf') if error.status in (401,403,400,404) else now+error.retry_after
            if not cfg['connected']:
                self.data[kind]=empty(kind);continue
            if kind in active and kind not in self.jobs and now>=self.next.get(kind,0):
                self.jobs[kind]=(self.pool.submit(refresh,kind,dict(cfg)),generation)
                if not self.data[kind]['updated']:self.data[kind]['status']='불러오는 중…'
        return self.data

class DesktopActivity:
    """Read only app identity and idle time, never titles or document names."""
    class Info(C.Structure):
        _fields_=[('window',C.c_ulong),('state',C.c_int),('kind',C.c_int),('since',C.c_ulong),('idle',C.c_ulong),('mask',C.c_ulong)]
    def __init__(self):
        self.x=C.CDLL(ctypes.util.find_library('X11'));self.ss=C.CDLL(ctypes.util.find_library('Xss'))
        self.x.XOpenDisplay.restype=C.c_void_p;self.x.XOpenDisplay.argtypes=[C.c_char_p]
        self.d=self.x.XOpenDisplay(None)
        self.x.XDefaultRootWindow.argtypes=[C.c_void_p];self.x.XDefaultRootWindow.restype=C.c_ulong
        self.root=self.x.XDefaultRootWindow(self.d) if self.d else 0
        self.ss.XScreenSaverQueryInfo.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(self.Info)]
    def app(self):
        if not self.d:return None
        info=self.Info()
        if not self.ss.XScreenSaverQueryInfo(self.d,self.root,C.byref(info)) or info.idle>=60000:return None
        try:
            import dbus
            obj=dbus.SessionBus().get_object('org.gnome.ScreenSaver','/org/gnome/ScreenSaver')
            if obj.GetActive(dbus_interface='org.gnome.ScreenSaver',timeout=1):return None
            root=subprocess.check_output(['xprop','-root','_NET_ACTIVE_WINDOW'],text=True,timeout=1)
            window=root.split()[-1]
            if window=='0x0':return None
            props=subprocess.check_output(['xprop','-id',window,'WM_CLASS','_NET_WM_WINDOW_TYPE'],text=True,timeout=1)
            if '_NET_WM_WINDOW_TYPE_DESKTOP' in props:return None
            line=props.splitlines()[0]
            name=line.split('"')[-2] if '"' in line else ''
            return name[:80] if name and name not in ('eww','Eww','Gnome-shell') else None
        except Exception:return None

def duration(seconds):
    minutes=int(seconds)//60
    return f'{minutes//60}시간 {minutes%60}분' if minutes>=60 else f'{minutes}분'

class Usage:
    def __init__(self):self.state=cache_read('screen-time.json',{});self.last=None;self.day=None;self.revision=None
    def step(self,cfg,app,now=None,today=None):
        now=time.monotonic() if now is None else now;today=today or dt.date.today().isoformat()
        if self.revision!=cfg.get('revision'):
            self.state=cache_read('screen-time.json',{});self.last=None;self.revision=cfg.get('revision')
        if cfg['enabled']:
            seconds=now-self.last if self.last is not None else 0
            bucket=self.state.setdefault(today,{})
            if app and self.day==today and 0<seconds<=15:bucket[app]=bucket.get(app,0)+seconds
            self.last=now;self.day=today
            cutoff=(dt.date.fromisoformat(today)-dt.timedelta(days=29)).isoformat()
            self.state={k:v for k,v in self.state.items() if k>=cutoff}
            cache_write('screen-time.json',self.state)
        else:self.last=None
        apps=sorted(self.state.get(today,{}).items(),key=lambda p:p[1],reverse=True)
        return {'total':duration(sum(v for _,v in apps)), 'rows':[{'name':k,'value':duration(v)} for k,v in apps[:8]],
                'status':'기록 중 · 잠금·1분 이상 자리 비움 제외' if cfg['enabled'] else '기록 꺼짐 · 설정에서 시작', 'tracking':cfg['enabled']}

def clear_usage():
    cache_write('screen-time.json',{});con.save('screentime',con.config('screentime'))

def clock_svg(now=None):
    now=now or dt.datetime.now();minute=now.hour*60+now.minute
    path=CACHE/f'clock-{minute}.svg'
    if not path.exists():
        CACHE.mkdir(parents=True,exist_ok=True,mode=0o700)
        parts=['<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160" viewBox="0 0 160 160">',
               '<circle cx="80" cy="80" r="76" fill="#f5f3ed" stroke="#d5d7df" stroke-width="1"/>']
        for n in range(12):
            a=n*math.pi/6;x=80+62*math.sin(a);y=80-62*math.cos(a)
            parts.append(f'<text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#2a3040">{n or 12}</text>')
        for angle,length,width in [((now.hour%12+now.minute/60)*30,37,5),(now.minute*6,53,3)]:
            a=math.radians(angle);parts.append(f'<path d="M80 80 L{80+length*math.sin(a):.2f} {80-length*math.cos(a):.2f}" stroke="#30394d" stroke-width="{width}" stroke-linecap="round"/>')
        parts.append('<circle cx="80" cy="80" r="4" fill="#557ceb"/></svg>');path.write_text(''.join(parts))
        for old in CACHE.glob('clock-*.svg'):
            if old!=path and old.stat().st_mtime<time.time()-180:old.unlink(missing_ok=True)
    return str(path)

def main():
    if len(sys.argv)>1 and sys.argv[1]=='home-action':
        try:con.control_home(sys.argv[2],sys.argv[3]);cache_write('home-action.json',{'error':'','time':time.time()})
        except Exception as exc:cache_write('home-action.json',{'error':str(exc) if isinstance(exc,(con.ConnectionError,ValueError)) else '기기를 제어하지 못했습니다.','time':time.time()})
        return
    poller=Poller();usage=Usage();activity=None;screen={'total':'0분','rows':[],'status':'기록 꺼짐','tracking':False};last_usage=0;previous=None
    while True:
        cfg=con.settings();active={w['kind'] for w in store.catalogue() if w['id'] not in store.hidden()}
        output=dict(poller.step(cfg,active));now=time.monotonic()
        if now-last_usage>=5 or cfg['screentime']['enabled']!=screen['tracking']:
            if cfg['screentime']['enabled'] and activity is None:
                try:activity=DesktopActivity()
                except (OSError,TypeError):pass
            screen=usage.step(cfg['screentime'],activity.app() if activity and cfg['screentime']['enabled'] else None);last_usage=now
        output.update(screen=screen,tracking=screen['tracking'],clock=clock_svg(),clock_time=dt.datetime.now().strftime('%H:%M'))
        action=cache_read('home-action.json',{})
        if action.get('error') and time.time()-action.get('time',0)<30:output['home']={**output['home'],'status':action['error'],'error':True}
        # Timestamp shown explicitly; stale cached values never look live.
        for kind in ('stocks','weather','home'):
            row=output[kind];row['last_update']=('마지막 조회 '+dt.datetime.fromtimestamp(row['updated']).strftime('%m/%d %H:%M:%S')) if row['updated'] else ''
        encoded=json.dumps(output,ensure_ascii=False)
        if encoded!=previous:print(encoded,flush=True);previous=encoded
        if len(sys.argv)>1 and sys.argv[1]=='once':break
        time.sleep(1)

if __name__=='__main__':
    try:main()
    except (KeyboardInterrupt,BrokenPipeError):pass
