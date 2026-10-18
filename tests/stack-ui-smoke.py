import ctypes as C,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];scale=int(os.environ.get('EWW_NATIVE_TEST_SCALE','1'));binary=os.environ.get('EWW_TEST_BINARY',str(root/'build/eww'))
with tempfile.TemporaryDirectory(prefix='widget-stack-qa-') as tmp:
 config=Path(tmp)/'config';shutil.copytree(root/'config',config,ignore=shutil.ignore_patterns('__pycache__','.web-profile'))
 runtime=Path(tmp)/'runtime';runtime.mkdir(mode=0o700)
 env={**os.environ,'EWW_WIDGET_CONFIG':str(config),'EWW_WIDGET_BINARY':binary,'EWW_GLASS_SKIP_COMPOSITOR':'1','XDG_CACHE_HOME':tmp+'/cache','XDG_RUNTIME_DIR':str(runtime),'DCONF_BACKEND':'memory','NO_AT_BRIDGE':'1','GDK_BACKEND':'x11','GDK_SCALE':str(scale)};os.environ.update(env)
 sys.path.insert(0,str(config/'scripts'));import widget_store as store,stacks,desktop_geometry as x
 def windows():
  return {wid:{k:v if k=='id' else v//scale for k,v in r.items()} for wid,r in x.windows().items()}
 log=(Path(tmp)/'engine.log').open('w');daemon=subprocess.Popen([binary,'--config',str(config),'--no-daemonize','daemon'],env=env,cwd=config,stdout=log,stderr=log)
 def cmd(*args):return subprocess.run([binary,'--config',str(config),*args],env=env,cwd=config,check=True,capture_output=True,text=True,timeout=12).stdout
 def click(rect,button=1):
  x.mouse((rect['x']+rect['width']//2)*scale,(rect['y']+rect['height']-11)*scale)
  for down in (True,False):x.T.XTestFakeButtonEvent(x.D,button,int(down),0);x.X.XFlush(x.D);time.sleep(.05)
 def drag(start,end):x.drag(tuple(v*scale for v in start),tuple(v*scale for v in end))
 def wait_for(wid):
  for _ in range(40):
   w=windows()
   # Native restoration retries through 900 ms after mapping.
   if set(w)=={wid}:time.sleep(1.1);return windows()[wid]
   time.sleep(.1)
  raise AssertionError((wid,windows(),(Path(tmp)/'engine.log').read_text()[-2500:]))
 try:
  for _ in range(30):
   try:cmd('ping');break
   except subprocess.CalledProcessError:time.sleep(.1)
  original={'Eww - uw-clock':{'x':200,'y':200,'width':320,'height':224},'Eww - uw-calendar':{'x':600,'y':200,'width':320,'height':224}}
  store.atomic_json('positions.json',original);store.atomic_json('hidden-widgets.json',[w['id'] for w in store.BUILTINS if w['id'] not in ('uw-clock','uw-calendar')]);cmd('open-many','uw-clock','uw-calendar');time.sleep(1.8)
  clock=windows()['uw-clock'];calendar=windows()['uw-calendar']
  drag((clock['x']+90,clock['y']+65),(calendar['x']+90,calendar['y']+65))
  clock=wait_for('uw-clock')
  assert stacks.groups()[0]['original']['uw-clock']==original['Eww - uw-clock']
  assert (clock['x'],clock['y'])==(calendar['x'],calendar['y'])

  # A real body drag moves the active stack member.
  drag((clock['x']+90,clock['y']+65),(clock['x']+154,clock['y']+113));time.sleep(.5);moved=windows()['uw-clock']
  click(moved);calendar=wait_for('uw-calendar')
  assert (calendar['x'],calendar['y'],calendar['width'],calendar['height'])==(moved['x'],moved['y'],moved['width'],moved['height']),(calendar,moved)
  drag((calendar['x']+calendar['width']-12,calendar['y']+90),(calendar['x']+calendar['width']+52,calendar['y']+90));time.sleep(.5);wide=windows()['uw-calendar']
  click(wide,button=4);clock=wait_for('uw-clock')
  assert clock['width']==wide['width'] and clock['x']==wide['x'],(clock,wide)
  cmd('close','uw-clock');store.open_visible();restored=wait_for('uw-clock');assert restored['width']==wide['width']
  stacks.dissolve('uw-clock');time.sleep(1.5);w=windows();assert set(w)=={'uw-clock','uw-calendar'},w
  for wid,r in w.items():
   assert all(r[k]==v for k,v in original['Eww - '+wid].items()),(wid,r,original)
  print('Stack GUI passed: automatic drop, physical drag, click, resize, wheel, reopen and split.',flush=True)
 finally:
  cmd('kill');daemon.wait(timeout=5);log.close()
  errors=[l for l in (Path(tmp)/'engine.log').read_text().splitlines() if 'ERROR' in l or 'error:' in l or 'Traceback' in l]
  if errors:raise AssertionError('\n'.join(errors[-15:]))
