#!/usr/bin/python3
"""Account setup UI. All network/keyring operations run outside the GTK thread."""
import threading
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,GLib,Gio
import connections as con
import integration_runtime as runtime

def open_dialog(gallery,item):
    kind=item['kind'];cfg=con.config(kind)
    d=Gtk.Dialog(title=item['name']+' 설정',transient_for=gallery.window,modal=True)
    d.set_default_size(520,720);d.add_button('닫기',Gtk.ResponseType.CLOSE)
    scroll=Gtk.ScrolledWindow();scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);d.get_content_area().pack_start(scroll,True,True,0)
    box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12);box.set_border_width(24);scroll.add(box)
    fields={};controls=[];state={'busy':False,'alive':True}
    def note(text):
        w=Gtk.Label(label=text,xalign=0);w.set_line_wrap(True);w.set_max_width_chars(53);box.pack_start(w,False,False,0);return w
    def entry(key,title,value='',secret=False):
        note(title);w=Gtk.Entry(text=value);w.set_visibility(not secret);w.set_input_purpose(Gtk.InputPurpose.PASSWORD if secret else Gtk.InputPurpose.FREE_FORM)
        w.get_accessible().set_name(title);box.pack_start(w,False,False,0);fields[key]=w;controls.append(w);return w
    def action(text,fn):
        b=Gtk.Button(label=text);b.connect('clicked',lambda _:fn());box.pack_start(b,False,False,0);controls.append(b);return b
    def link(text,url):
        w=Gtk.LinkButton.new_with_label(url,text);box.pack_start(w,False,False,0)
    status=Gtk.Label(xalign=0);status.set_line_wrap(True);status.set_max_width_chars(53)
    def work(fn,success,after=None):
        if state['busy']:return
        state['busy']=True;status.set_text('확인하는 중…');d.set_deletable(False);d.set_response_sensitive(Gtk.ResponseType.CLOSE,False)
        for w in controls:w.set_sensitive(False)
        def worker():
            try:result=fn();error=None
            except Exception as exc:
                result=None;error=str(exc) if isinstance(exc,(ValueError,con.ConnectionError)) else '설정을 적용하지 못했습니다. 키링 또는 연결 상태를 확인하세요.'
            GLib.idle_add(done,result,error)
        def done(result,error):
            if not state['alive']:return False
            state['busy']=False;d.set_deletable(True);d.set_response_sensitive(Gtk.ResponseType.CLOSE,True)
            for w in controls:w.set_sensitive(True)
            status.set_text(error or success)
            if not error and after:after(result)
            gallery.refresh_all();return False
        threading.Thread(target=worker,daemon=True).start()
    if kind=='stocks':
        note('토스증권 연결 · '+('설정됨' if cfg['connected'] else '아직 연결하지 않음'))
        note('1. 본인의 토스증권 WTS에서 설정 → Open API를 여세요.\n2. API 키를 발급하고 이 PC의 공인 IP를 허용 IP로 등록하세요.\n3. 아래에 직접 입력한 뒤 연결하세요.')
        link('토스증권 열기','https://www.tossinvest.com/');link('공식 API 연결 안내','https://developers.tossinvest.com/docs')
        entry('id','Client ID',secret=True);entry('secret','Client Secret',secret=True)
        entry('symbols','관심 종목 코드 · 쉼표로 구분',','.join(cfg['symbols']))
        entry('indices','시장 지수 코드 · 비워 두어도 됩니다',','.join(cfg['indices']))
        note('키와 토큰은 이 PC의 GNOME 키링에 보관합니다. 주식 시세를 30초마다 조회합니다.\n같은 API 키는 유효한 토큰이 하나이므로 다른 프로그램과 별도 키 사용을 권장합니다.')
        def values():return con.watchlist(fields['symbols'].get_text(),fields['indices'].get_text())
        def connect():
            try:v=values()
            except ValueError as exc:status.set_text(str(exc));return
            cid=fields['id'].get_text();secret=fields['secret'].get_text()
            def clear(_):fields['id'].set_text('');fields['secret'].set_text('')
            work(lambda:con.connect_toss(cid,secret,v),'연결되었습니다. 키는 키링에 저장했습니다.',clear)
        action('연결 확인 및 저장',connect)
        def watch():
            try:v=values();con.save('stocks',v);status.set_text('관심 목록을 저장했습니다. 연결된 위젯에 반영됩니다.')
            except (ValueError,OSError) as exc:status.set_text(str(exc))
        action('관심 목록만 저장',watch)
        action('연결 해제 · 저장된 키 삭제',lambda:work(lambda:con.disconnect('stocks'),'연결을 해제하고 이 앱의 키를 삭제했습니다.'))
    elif kind=='weather':
        note('표시할 지역을 직접 선택하세요. 위치를 자동 추적하지 않습니다.')
        entry('city','도시 이름 · 예: 서울, Busan',cfg['city'].split(' · ')[0])
        choices=Gtk.ComboBoxText();box.pack_start(choices,False,False,0);controls.append(choices);locations=[]
        def result(rows):
            locations[:]=rows;choices.remove_all()
            for i,row in enumerate(rows):choices.append(str(i),row['city'])
            if rows:choices.set_active(0)
            else:status.set_text('지역을 찾지 못했습니다. 영문 도시 이름으로도 검색해 보세요.')
        def search():
            name=fields['city'].get_text();work(lambda:con.search_city(name),'지역을 선택한 뒤 저장하세요.',result)
        action('지역 검색',search)
        def save_weather():
            i=choices.get_active()
            if i<0:status.set_text('지역을 검색하고 결과를 선택하세요.');return
            selected=dict(locations[i])
            def job():con.weather_snapshot(selected);con.save('weather',selected)
            work(job,'날씨 지역을 저장했습니다.')
        action('선택한 지역 저장',save_weather)
        action('날씨 연결 해제',lambda:work(lambda:con.save('weather',{'connected':False}),'날씨 조회를 중단했습니다.'))
        note('현재 기온 · 최고/최저 · 6시간 예보 · 7일 예보\nUS AQI와 PM2.5는 예측 데이터입니다. 15분마다 갱신합니다.')
        link('날씨: Open-Meteo · CC BY 4.0','https://open-meteo.com/');link('대기질: CAMS / Open-Meteo','https://open-meteo.com/en/docs/air-quality-api')
    elif kind=='home':
        note('Home Assistant 서버에 등록된 기기를 연결합니다. 조명·스위치는 위젯에서 켜고 끌 수 있습니다.')
        entry('url','서버 주소 · 예: http://homeassistant.local:8123',cfg['url'])
        entry('token','장기 액세스 토큰 · Home Assistant 프로필에서 발급',secret=True)
        entry('entities','기기 ID · 예: light.living_room, sensor.temperature',','.join(cfg['entities']))
        note('토큰은 GNOME 키링에 저장됩니다. 최대 12개 기기의 상태를 표시합니다.\n센서·온도 조절기는 상태 조회만 지원합니다.')
        def connect():
            url=fields['url'].get_text();token=fields['token'].get_text();entities=fields['entities'].get_text()
            work(lambda:con.connect_home(url,token,entities),'홈 연결을 저장했습니다.',lambda _:fields['token'].set_text(''))
        action('연결 확인 및 저장',connect)
        def save_entities():
            try:entities=con.home_entities(fields['entities'].get_text())
            except ValueError as exc:status.set_text(str(exc));return
            if not entities:status.set_text('표시할 기기를 하나 이상 입력하세요.');return
            con.save('home',{'entities':entities});status.set_text('기기 목록을 저장했습니다.')
        action('기기 목록만 저장',save_entities)
        action('연결 해제 · 저장된 토큰 삭제',lambda:work(lambda:con.disconnect('home'),'연결을 해제했습니다.'))
        link('Home Assistant 연결 문서','https://developers.home-assistant.io/docs/api/rest/')
    else:
        note('이 PC에서 사용 중인 앱과 사용 시간을 기록합니다. 기록은 이 PC에만 저장하며 30일간 보관합니다. 창 제목과 웹사이트 주소는 수집하지 않습니다.')
        note('위젯이 실행되는 동안 기록합니다. 화면 잠금과 1분 이상 입력이 없는 시간은 제외합니다. 기록을 켠 이후부터 집계합니다.')
        toggle=Gtk.CheckButton(label='앱 사용 시간 기록');toggle.set_active(cfg['enabled']);box.pack_start(toggle,False,False,0)
        toggle.connect('toggled',lambda w:con.save('screentime',{'enabled':w.get_active()}))
        action('저장된 사용 기록 모두 지우기',lambda:work(runtime.clear_usage,'사용 기록을 지웠습니다.'))
    box.pack_start(status,False,False,6)
    def close(_dialog,response):
        if not state['busy']:state['alive']=False;d.destroy()
    d.connect('response',close);d.connect('destroy',lambda *_:state.update(alive=False));d.show_all()
    return d
