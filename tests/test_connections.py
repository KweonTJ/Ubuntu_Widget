import copy,datetime as dt,json,os,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'config/scripts'))
import connections as c,widget_store as s,integration_runtime as r,library_data as l
class Vault:
 def __init__(self):self.values={}
 def get(self,k):return self.values.get(k)
 def put(self,k,v):self.values[k]=copy.deepcopy(v)
 def delete(self,k):self.values.pop(k,None)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old=s.CONFIG;self.cache=r.CACHE;s.CONFIG=Path(self.tmp.name);r.CACHE=s.CONFIG/'cache';self.calls=[];self.vault=Vault();c._previous_closes.clear()
 def tearDown(self):s.CONFIG=self.old;r.CACHE=self.cache;self.tmp.cleanup()
 def fetch(self,url,**kw):
  self.calls.append((url,kw))
  if url.endswith('/oauth2/token'):
   assert kw['form']['grant_type']=='client_credentials'
   return {'access_token':'TEST_TOKEN','token_type':'Bearer','expires_in':86400}
  assert kw['token']=='TEST_TOKEN'
  if '/candles?' in url:return {'result':{'candles':[{'timestamp':'2026-10-17T00:00:00+09:00','closePrice':'100'},{'timestamp':'2026-10-16T00:00:00+09:00','closePrice':'80'}]}}
  if '/stocks?' in url:return {'result':[{'symbol':'005930','name':'삼성전자'}]}
  return {'result':[{'symbol':'005930' if '/api/v1/prices?' in url else 'KOSPI','lastPrice':'100','timestamp':'2026-10-17T10:00:00+09:00','currency':'KRW' if '/api/v1/prices?' in url else ''}]}
 def test_personal_connection_secure_and_no_orders(self):
  with patch.object(c.time,'sleep'):
   c.connect_toss('TEST_ID','TEST_SECRET',{'symbols':['005930'],'indices':['KOSPI']},self.vault,self.fetch)
   snapshot=c.refresh_toss(c.config('stocks'),self.vault,self.fetch)
  self.assertEqual(snapshot['rows'][0]['value'],'100원');self.assertIn('+25.00%',snapshot['rows'][0]['detail'])
  self.assertEqual(sum(url.endswith('/oauth2/token') for url,_ in self.calls),1)
  raw=(s.CONFIG/'connections.json').read_text()
  for secret in ('TEST_ID','TEST_SECRET','TEST_TOKEN'):self.assertNotIn(secret,raw)
  self.assertFalse(any('/orders' in url or '/accounts' in url or '/holdings' in url for url,_ in self.calls))
  c.disconnect('stocks',self.vault);self.assertFalse(c.config('stocks')['connected']);self.assertIsNone(self.vault.get('stocks'))
 def test_failed_auth_does_not_mark_connected(self):
  def fail(*a,**k):raise c.ConnectionError('허용 IP 오류',403)
  with self.assertRaises(c.ConnectionError):c.connect_toss('ID','SECRET',{'symbols':['AAPL'],'indices':[]},self.vault,fail)
  self.assertFalse(c.config('stocks')['connected']);self.assertEqual(self.vault.values,{})
 def test_home_control_allowlist_and_transport(self):
  calls=[]
  def fetch(url,**kw):
   calls.append((url,kw))
   return {'state':'on','attributes':{'friendly_name':'거실'}} if '/states/' in url else []
  c.connect_home('http://192.168.1.3:8123','TEST_HOME','light.living',self.vault,fetch)
  c.control_home('light.living','turn_off',self.vault,fetch)
  self.assertTrue(calls[-1][0].endswith('/api/services/light/turn_off'))
  self.assertEqual(calls[-1][1]['body'],{'entity_id':'light.living'})
  for entity,action in [('light.other','turn_on'),('lock.front','unlock'),('light.living;echo hi','turn_on')]:
   with self.assertRaises(ValueError):c.control_home(entity,action,self.vault,fetch)
  with self.assertRaises(ValueError):c.home_url('http://example.com')
  self.assertNotIn('TEST_HOME',(s.CONFIG/'connections.json').read_text())
 def test_poller_revoked_token_stops_and_revision_discards_old(self):
  from concurrent.futures import Future
  p=r.Poller();cfg=c.settings();cfg['stocks']['connected']=True;generation=json.dumps(cfg['stocks'],sort_keys=True);p.generations['stocks']=generation
  f=Future();f.set_exception(c.ConnectionError('재연결 필요',401));p.jobs['stocks']=(f,generation)
  p.step(cfg,{'stocks'},0);self.assertEqual(p.next['stocks'],float('inf'));self.assertFalse(p.jobs)
  cfg['stocks']['connected']=False;p.data['stocks']['rows']=[{'value':'private'}]
  p.step(cfg,{'stocks'},1);self.assertEqual(p.data['stocks']['rows'],[])
  p.pool.shutdown()
 def test_screentime_opt_in_idle_suspend_midnight(self):
  u=r.Usage();cfg={'enabled':False};u.step(cfg,'App',0,'2026-10-17');u.step(cfg,'App',10,'2026-10-17');self.assertFalse((r.CACHE/'screen-time.json').exists())
  cfg['enabled']=True;u.step(cfg,'App',10,'2026-10-17');u.step(cfg,'App',15,'2026-10-17');u.step(cfg,None,20,'2026-10-17');u.step(cfg,'App',300,'2026-10-17')
  self.assertEqual(u.state['2026-10-17']['App'],5)
  u.step(cfg,'App',305,'2026-10-18');self.assertEqual(u.state['2026-10-18'],{})
  r.clear_usage();self.assertEqual(r.cache_read('screen-time.json',None),{})
 def test_agenda_and_catalog(self):
  l.save_config('agenda',{'text':'2026-10-19 10:30 | Future\n2026-10-10 11:00 | Past'})
  _,snap,_=l.snapshot(now=dt.datetime(2026,10,17,tzinfo=dt.timezone.utc))
  self.assertEqual([e['title'] for e in snap['agenda']],['Future'])
  with self.assertRaises(ValueError):l.save_config('agenda',{'text':'wrong'})
  self.assertEqual(len(s.library()),35)
  for kind in ('weather','analog','agenda','stocks','screentime','home','podcast'):self.assertIn('uw-'+kind,s.hidden())
 def test_weather_missing_aqi_is_not_zero(self):
  def fetch(url,**kw):
   if 'air-quality' in url:raise c.ConnectionError('offline')
   return {'current':{'temperature_2m':21,'weather_code':0,'time':'2026-10-17T10:00'},'daily':{'time':['2026-10-17'],'temperature_2m_max':[23],'temperature_2m_min':[16],'weather_code':[0]},'hourly':{'time':['2026-10-17T11:00'],'temperature_2m':[22],'weather_code':[0]}}
  value=c.weather_snapshot({'city':'Test','latitude':0,'longitude':0},fetch)
  self.assertEqual(value['temperature'],'21°');self.assertEqual(value['air'],'대기질 정보 없음')
 def test_redirection_never_forwards_secrets(self):
  self.assertIsNone(c.NoRedirect().redirect_request(None,None,302,'',{},'https://other.example'))
  with self.assertRaises(ValueError):c.watchlist('$(echo injected)','')
  c.save('stocks',{'client_secret':'MUST_NOT_WRITE','connected':False});self.assertNotIn('MUST_NOT_WRITE',(s.CONFIG/'connections.json').read_text())
if __name__=='__main__':unittest.main(verbosity=2)
