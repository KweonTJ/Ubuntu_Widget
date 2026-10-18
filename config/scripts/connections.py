#!/usr/bin/python3
"""User-owned integrations. Public preferences in JSON, secrets only in libsecret.

Toss contract: official OpenAPI v1.2.24, inspected 2026-10-17.
Only authentication, prices and stock metadata are used; no account/order API.
"""
import datetime as dt
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import fcntl
import hashlib
import ipaddress
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo
import widget_store as store

TOSS = 'https://openapi.tossinvest.com'
DEFAULTS = {
    'stocks': {'connected': False, 'symbols': ['005930', 'AAPL'], 'indices': ['KOSPI', 'KOSDAQ']},
    'weather': {'connected': False, 'city': '', 'latitude': 0, 'longitude': 0},
    'home': {'connected': False, 'url': '', 'entities': []},
    'screentime': {'enabled': False},
}

class ConnectionError(Exception):
    def __init__(self, message, status=0, retry_after=60):
        super().__init__(message); self.status=status; self.retry_after=retry_after

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None

def request(url, *, form=None, body=None, token=None):
    headers={'Accept':'application/json', 'User-Agent':'Eww-Widget-Library/1.0'}
    data=None
    if form is not None:
        data=urllib.parse.urlencode(form).encode(); headers['Content-Type']='application/x-www-form-urlencoded'
    elif body is not None:
        data=json.dumps(body).encode(); headers['Content-Type']='application/json'
    if token: headers['Authorization']='Bearer '+token
    req=urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=10) as response:
            raw=response.read(2_000_001)
            if len(raw)>2_000_000: raise ConnectionError('응답이 너무 큽니다.')
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        # Never display server bodies/URLs: they can contain user credentials.
        messages={400:'입력한 설정이나 종목 코드를 확인하세요.',401:'인증이 만료되었거나 키가 올바르지 않습니다. 다시 연결하세요.',
                  403:'접근이 거부되었습니다. 토스는 WTS의 허용 IP도 확인하세요.',404:'주소나 종목·기기 ID를 확인하세요.',
                  429:'요청 한도에 도달했습니다. 잠시 후 다시 조회합니다.'}
        try: retry=max(60,min(3600,int(exc.headers.get('Retry-After','60'))))
        except (ValueError,TypeError): retry=60
        raise ConnectionError(messages.get(exc.code,'서비스에 연결하지 못했습니다. 잠시 후 다시 시도하세요.'),exc.code,retry) from None
    except (urllib.error.URLError,TimeoutError,OSError,ValueError):
        raise ConnectionError('네트워크 연결이나 서비스 상태를 확인하세요.') from None

class Secrets:
    """Encrypted desktop keyring; deliberately no plaintext fallback."""
    def __init__(self):
        import gi
        gi.require_version('Secret','1')
        from gi.repository import Secret
        self.api=Secret
        self.schema=Secret.Schema.new('local.eww.WidgetLibrary', Secret.SchemaFlags.NONE,
                                      {'provider':Secret.SchemaAttributeType.STRING,'profile':Secret.SchemaAttributeType.STRING})
        self.profile=hashlib.sha256(str(store.CONFIG.resolve()).encode()).hexdigest()[:20]
    def attrs(self,provider): return {'provider':provider,'profile':self.profile}
    def get(self,provider):
        try:
            value=self.api.password_lookup_sync(self.schema,self.attrs(provider),None)
            return json.loads(value) if value else None
        except Exception: raise ConnectionError('GNOME 키링을 잠금 해제한 뒤 다시 시도하세요.') from None
    def put(self,provider,value):
        try:
            ok=self.api.password_store_sync(self.schema,self.attrs(provider),self.api.COLLECTION_DEFAULT,
                '위젯 보관함 · '+provider,json.dumps(value),None)
            if not ok: raise RuntimeError()
        except Exception: raise ConnectionError('GNOME 키링에 저장하지 못했습니다. 로그인 키링을 확인하세요.') from None
    def delete(self,provider):
        try: self.api.password_clear_sync(self.schema,self.attrs(provider),None)
        except Exception: raise ConnectionError('키링의 연결 정보를 삭제하지 못했습니다. 잠금을 확인하세요.') from None

def settings():
    raw=store.read_json('connections.json',{})
    return {key:{**value,**raw.get(key,{})} for key,value in DEFAULTS.items()}

def config(kind): return settings()[kind]

@contextmanager
def auth_lock():
    # Serialize token rotation without blocking layout/theme/settings writes.
    with (store.CONFIG/'connections-auth.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        try:yield
        finally:fcntl.flock(lock,fcntl.LOCK_UN)

def save(kind, values):
    # Public settings whitelist prevents accidental secret export in backups.
    clean={key:value for key,value in values.items() if key in DEFAULTS[kind]}
    with store.locked():
        state=store.read_json('connections.json',{}); state[kind]={**config(kind),**clean,'revision':time.time_ns()}
        store.atomic_json('connections.json',state)

def symbols(text, *, indices=False):
    items=list(dict.fromkeys(s.upper() for s in re.split(r'[\s,]+',text.strip()) if s))
    pattern=r'[A-Z0-9_]{1,32}' if indices else r'[A-Z0-9.\-]{1,20}'
    if len(items)>12 or any(not re.fullmatch(pattern,s) for s in items):
        raise ValueError('종목·지수는 각각 최대 12개입니다. 코드만 쉼표로 구분해 입력하세요.')
    return items

def watchlist(stock_text,index_text):
    stocks=symbols(stock_text); indices=symbols(index_text,indices=True)
    if not stocks and not indices: raise ValueError('관심 종목이나 지수를 하나 이상 입력하세요.')
    return {'symbols':stocks,'indices':indices}

def price_text(raw,currency=''):
    try:
        number=Decimal(str(raw))
        if not number.is_finite(): return '—'
        return (f'{number:,.0f}원' if currency=='KRW' else f'${number:,.2f}' if currency=='USD' else f'{number:,.2f}')
    except (InvalidOperation,ValueError,TypeError): return '—'

def data_time(value):
    if not value:return '시각 미제공'
    try:return dt.datetime.fromisoformat(value.replace('Z','+00:00')).astimezone().strftime('%m/%d %H:%M')
    except (ValueError,AttributeError):return '시각 미제공'

_previous_closes={}
def change_from_previous(symbol,row,token,fetch,index=False):
    """Compare against the previous trading date in the market's own timezone."""
    try:
        zone=ZoneInfo('America/New_York' if row.get('currency')=='USD' else 'Asia/Seoul')
        date=dt.datetime.fromisoformat(row['timestamp'].replace('Z','+00:00')).astimezone(zone).date()
        key=(symbol,date,index);cached=_previous_closes.get(key)
        if cached is None or time.monotonic()-cached[0]>300:
            endpoint=f'/api/v1/market-indicators/{symbol}/candles' if index else '/api/v1/candles'
            params={'interval':'1d','count':8}
            if not index:params['symbol']=symbol
            time.sleep(.25)  # stay below the indicator chart group's 5 requests/s
            candles=fetch(TOSS+endpoint+'?'+urllib.parse.urlencode(params),token=token)['result']['candles']
            previous=next((c for c in candles if dt.datetime.fromisoformat(c['timestamp'].replace('Z','+00:00')).astimezone(zone).date()<date),None)
            if previous is None:return ''
            cached=(time.monotonic(),Decimal(previous['closePrice']));_previous_closes[key]=cached
        close=cached[1];price=Decimal(row['lastPrice'])
        if not price.is_finite() or not close.is_finite() or close<=0:return ''
        return f' · {(price/close-1)*100:+.2f}% (이전 종가 대비)'
    except ConnectionError as exc:
        if exc.status in (401,403,429):raise
        return ''
    except (KeyError,ValueError,TypeError,AttributeError,InvalidOperation):return ''

def issue_token(client_id,client_secret,fetch=request):
    result=fetch(TOSS+'/oauth2/token',form={'grant_type':'client_credentials','client_id':client_id,'client_secret':client_secret})
    if not result.get('access_token') or str(result.get('token_type','')).lower()!='bearer':
        raise ConnectionError('토스 인증 응답을 확인할 수 없습니다.')
    return {'client_id':client_id,'client_secret':client_secret,'access_token':result['access_token'],
            'expires_at':time.time()+max(1,int(result['expires_in']))}

def toss_snapshot(cfg,credentials,fetch=request):
    rows=[]; token=credentials['access_token']; names={}
    if cfg['symbols']:
        query=urllib.parse.urlencode({'symbols':','.join(cfg['symbols'])})
        names={r['symbol']:r['name'] for r in fetch(TOSS+'/api/v1/stocks?'+query,token=token)['result']}
        prices=fetch(TOSS+'/api/v1/prices?'+query,token=token)['result']
        by_symbol={r['symbol']:r for r in prices}
        for symbol in cfg['symbols']:
            row=by_symbol.get(symbol,{})
            rows.append({'name':names.get(symbol,symbol),'symbol':symbol,'value':price_text(row.get('lastPrice'),row.get('currency')),
                         'detail':data_time(row.get('timestamp'))+change_from_previous(symbol,row,token,fetch),'available':bool(row)})
    if cfg['indices']:
        query=urllib.parse.urlencode({'symbols':','.join(cfg['indices'])})
        by_symbol={r['symbol']:r for r in fetch(TOSS+'/api/v1/market-indicators/prices?'+query,token=token)['result']}
        for symbol in cfg['indices']:
            row=by_symbol.get(symbol,{})
            rows.append({'name':symbol,'symbol':symbol,'value':price_text(row.get('lastPrice')),
                         'detail':data_time(row.get('timestamp'))+change_from_previous(symbol,row,token,fetch,True),'available':bool(row)})
    return {'rows':rows,'status':'토스증권 · 30초마다 조회','updated':time.time()}

def connect_toss(client_id,client_secret,cfg,secrets=None,fetch=request):
    if not client_id.strip() or not client_secret.strip():raise ValueError('Client ID와 Client Secret을 모두 입력하세요.')
    vault=secrets or Secrets()
    # One valid token per client: save the tested token so the listener reuses it.
    with auth_lock():
        previous=vault.get('stocks')
        creds=issue_token(client_id.strip(),client_secret.strip(),fetch)
        try:toss_snapshot(cfg,creds,fetch)
        except Exception:
            # Issuing this token revoked the same client's prior token. Keep
            # the replacement for the old watchlist even if a new symbol fails.
            if previous and previous.get('client_id')==client_id.strip():vault.put('stocks',creds)
            raise
        vault.put('stocks',creds)
    save('stocks',{**cfg,'connected':True})

def refresh_toss(cfg,secrets=None,fetch=request):
    vault=secrets or Secrets()
    with auth_lock():
        creds=vault.get('stocks')
        if not creds:raise ConnectionError('토스 연결을 먼저 설정하세요.',401)
        if creds.get('expires_at',0)<=time.time()+60:
            creds=issue_token(creds['client_id'],creds['client_secret'],fetch);vault.put('stocks',creds)
    # A revoked token is not retried endlessly, avoiding fights with another client.
    return toss_snapshot(cfg,creds,fetch)

def disconnect(kind,secrets=None):
    with auth_lock(): (secrets or Secrets()).delete(kind)
    save(kind,{'connected':False})

def search_city(name,fetch=request):
    if len(name.strip())<2:raise ValueError('도시 이름을 두 글자 이상 입력하세요.')
    data=fetch('https://geocoding-api.open-meteo.com/v1/search?'+urllib.parse.urlencode({'name':name.strip(),'count':8,'language':'ko','format':'json'}))
    return [{'city':' · '.join(filter(None,[r['name'],r.get('admin1'),r.get('country')])),
             'latitude':r['latitude'],'longitude':r['longitude'],'connected':True} for r in data.get('results',[])]

def weather_name(code):
    for codes,name in [((0,),'맑음'),((1,),'대체로 맑음'),((2,),'구름 조금'),((3,),'흐림'),
                       ((45,48),'안개'),((51,53,55),'이슬비'),((56,57),'어는 이슬비'),
                       ((61,63,65),'비'),((66,67),'어는 비'),((71,73,75),'눈'),((77,),'싸락눈'),
                       ((80,81,82),'소나기'),((85,86),'눈 소나기'),((95,97),'뇌우'),((96,99),'우박을 동반한 뇌우')]:
        if code in codes:return name
    return '날씨 정보 없음'

def weather_icon(code,is_day=True):
    """Local SVG names for Open-Meteo's WMO codes; daylight is provider-local."""
    period='night' if is_day==0 else 'day'
    if code==0:return 'clear-'+period
    if code in (1,2):return 'partly-cloudy-'+period
    if code==3:return 'cloudy'
    if code in (45,48):return 'fog'
    if code in (51,53,55):return 'drizzle'
    if code in (56,57,66,67):return 'freezing-rain'
    if code in (61,63,65):return 'rain'
    if code in (71,73,75,77,85,86):return 'snow'
    if code in (80,81,82):return 'showers-'+period
    if code in (95,96,97,99):return 'thunderstorm'
    return 'unknown'

def temperature(value):return '—' if value is None else f'{round(value)}°'

def weather_snapshot(cfg,fetch=request):
    loc={'latitude':cfg['latitude'],'longitude':cfg['longitude'],'timezone':'auto'}
    data=fetch('https://api.open-meteo.com/v1/forecast?'+urllib.parse.urlencode({**loc,'current':'temperature_2m,weather_code,is_day',
        'hourly':'temperature_2m,weather_code','daily':'temperature_2m_max,temperature_2m_min,weather_code','forecast_days':7}))
    current=data['current']; daily=data['daily']; hourly=data['hourly']
    week=[{'name':('오늘' if i==0 else dt.date.fromisoformat(day).strftime('%m/%d')),
           'value':temperature(daily['temperature_2m_min'][i])+' / '+temperature(daily['temperature_2m_max'][i]),
           'detail':weather_name(daily['weather_code'][i])} for i,day in enumerate(daily['time'])]
    hours=[{'name':t[-5:],'value':temperature(hourly['temperature_2m'][i]),'detail':weather_name(hourly['weather_code'][i])}
           for i,t in enumerate(hourly['time']) if t>=current['time']][:6]
    for index,row in enumerate(hours):row['index']=index
    for index,row in enumerate(week):row['index']=index
    air='대기질 정보 없음'
    try:
        a=fetch('https://air-quality-api.open-meteo.com/v1/air-quality?'+urllib.parse.urlencode({**loc,'current':'us_aqi,pm2_5'}))['current']
        aq=a.get('us_aqi');pm=a.get('pm2_5')
        if aq is not None:air=f'US AQI {round(aq)} · PM2.5 '+('—' if pm is None else f'{pm:.1f} μg/m³')
    except ConnectionError:pass
    return {'city':cfg['city'],'temperature':temperature(current['temperature_2m']),'condition':weather_name(current['weather_code']),
            'icon':weather_icon(current['weather_code'],current.get('is_day',1)),'is_day':current.get('is_day'),'weather_code':current['weather_code'],
            'range':week[0]['value'],'hours':hours,'week':week,'air':air,'status':'Open-Meteo · CAMS · 15분마다 조회','updated':time.time()}

def home_url(value):
    url=store.normalize_url(value).rstrip('/');p=urllib.parse.urlsplit(url)
    if p.query or p.fragment or p.path not in ('','/'):raise ValueError('Home Assistant 서버의 기본 주소만 입력하세요.')
    if p.scheme=='http':
        local=p.hostname in ('localhost','homeassistant.local') or p.hostname.endswith('.local')
        try:local=local or ipaddress.ip_address(p.hostname).is_private or ipaddress.ip_address(p.hostname).is_loopback
        except ValueError:pass
        if not local:raise ValueError('외부 서버는 HTTPS 주소를 사용하세요. HTTP는 로컬 네트워크에서만 지원합니다.')
    return url

def home_entities(text):
    entries=list(dict.fromkeys(s for s in re.split(r'[\s,]+',text.strip()) if s))
    if len(entries)>12 or any(not re.fullmatch(r'(light|switch|sensor|binary_sensor|climate)\.[a-z0-9_]+',s) for s in entries):
        raise ValueError('light, switch, sensor, binary_sensor, climate 기기 ID를 최대 12개 입력하세요.')
    return entries

def home_snapshot(cfg,credential,fetch=request):
    result=[]
    for entity in home_entities(','.join(cfg['entities'])):
        r=fetch(home_url(cfg['url'])+'/api/states/'+entity,token=credential['token'])
        attr=r.get('attributes',{});state=r['state'];domain=entity.split('.')[0]
        value={'on':'켜짐','off':'꺼짐','unavailable':'연결 끊김','unknown':'알 수 없음'}.get(state,state)
        if domain=='climate' and attr.get('current_temperature') is not None:value+=f" · {attr['current_temperature']}°"
        elif attr.get('unit_of_measurement'):value+=' '+str(attr['unit_of_measurement'])
        result.append({'id':entity,'name':str(attr.get('friendly_name',entity))[:80],'value':str(value)[:80],
                       'control':domain in ('light','switch') and state in ('on','off'),'action':'turn_off' if state=='on' else 'turn_on',
                       'button':'끄기' if state=='on' else '켜기'})
    return {'rows':result,'status':'Home Assistant · 30초마다 조회','updated':time.time()}

def connect_home(url,token,entities,secrets=None,fetch=request):
    if not token.strip():raise ValueError('Home Assistant 장기 액세스 토큰을 입력하세요.')
    cfg={'url':home_url(url),'entities':home_entities(entities)}
    if not cfg['entities']:raise ValueError('표시할 기기 ID를 하나 이상 입력하세요.')
    credential={'token':token.strip()};home_snapshot(cfg,credential,fetch)
    (secrets or Secrets()).put('home',credential);save('home',{**cfg,'connected':True})

def control_home(entity,action,secrets=None,fetch=request):
    cfg=config('home')
    if not cfg['connected'] or entity not in cfg['entities'] or not re.fullmatch(r'(light|switch)\.[a-z0-9_]+',entity) or action not in ('turn_on','turn_off'):
        raise ValueError('등록된 조명·스위치만 켜거나 끌 수 있습니다.')
    credential=(secrets or Secrets()).get('home')
    if not credential:raise ConnectionError('홈 연결을 다시 설정하세요.')
    fetch(home_url(cfg['url'])+'/api/services/'+entity.split('.')[0]+'/'+action,body={'entity_id':entity},token=credential['token'])
    save('home',cfg)
