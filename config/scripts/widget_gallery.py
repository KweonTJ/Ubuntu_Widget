#!/usr/bin/python3
"""A native, searchable widget gallery with previews and desktop placement."""
import os
import datetime
import math
import sys
import threading
from pathlib import Path
import gi
gi.require_version('Gtk','3.0');gi.require_version('Gdk','3.0')
from gi.repository import Gtk,Gdk,Gio,GLib,Pango
import cairo
import widget_store as store
import connection_dialog
import library_data
import glass_effect as glass_effect
from widget_catalog import CATEGORIES


def label(text,css=None):
    w=Gtk.Label(label=text,xalign=0)
    if css:w.get_style_context().add_class(css)
    return w

def button(text,callback=None,css=None):
    w=Gtk.Button(label=text)
    if callback:w.connect('clicked',lambda _:callback())
    if css:w.get_style_context().add_class(css)
    return w

def current_theme():
    try:mode=(store.CONFIG/'theme-mode').read_text().strip()
    except OSError:mode='auto'
    if mode in ('light','dark'):return mode
    s=Gio.Settings.new('org.gnome.desktop.interface')
    scheme=s.get_string('color-scheme')
    return 'dark' if scheme=='prefer-dark' or (scheme=='default' and 'dark' in s.get_string('gtk-theme').lower()) else 'light'

class Preview(Gtk.DrawingArea):
    COLORS={'clock':('#303c60','#b7cffe'),'calendar':('#292c35','#ff8a9b'),
            'system':('#282d3a','#9dabff'),'music':('#44334d','#e5b4dc'),
            'battery':('#253f32','#75e693'),'sound':('#2d3445','#b7c6ee'),'web':('#35344e','#c5b8ff')}
    def __init__(self,item,large=False):
        super().__init__();self.item=item;self.large=large;self.glass=glass_effect.enabled(item);self.set_size_request(218 if large else 132,156 if large else 88)
        self.connect('draw',self.draw)
    def draw(self,w,c):
        width,height=self.get_allocated_width(),self.get_allocated_height()
        scale=min(width/240,height/160);c.translate((width-240*scale)/2,(height-160*scale)/2);c.scale(scale,scale)
        kind=self.item['kind'];bg,fg=self.COLORS.get('web' if kind=='webpreset' else kind,('#363e54','#b5ccff') if self.item.get('category')=='time' else ('#454031','#f3d78d') if self.item.get('category')=='productivity' else ('#2c403b','#9fe0c9'))
        def color(s,a=1):c.set_source_rgba(*(int(s[i:i+2],16)/255 for i in (1,3,5)),a)
        def rounded(x,y,w,h,r):
            c.new_sub_path()
            for xx,yy,a in [(x+w-r,y+r,-90),(x+w-r,y+h-r,0),(x+r,y+h-r,90),(x+r,y+r,180)]:c.arc(xx,yy,r,math.radians(a),math.radians(a+90))
            c.close_path()
        color(bg,.70 if self.glass else 1);rounded(1,1,238,158,22);c.fill()
        if self.glass:
            gradient=cairo.LinearGradient(0,0,240,160);gradient.add_color_stop_rgba(0,1,1,1,.23);gradient.add_color_stop_rgba(.45,1,1,1,.02);gradient.add_color_stop_rgba(1,1,1,1,.09)
            c.set_source(gradient);rounded(1,1,238,158,22);c.fill()
            color('#ffffff',.32);c.set_line_width(1);rounded(1.5,1.5,237,157,22);c.stroke()
        def text(s,x,y,size=14,col=fg,bold=False):
            color(col);c.select_font_face('Noto Sans CJK KR',cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL);c.set_font_size(size);c.move_to(x,y);c.show_text(s)
        if kind=='clock':
            now=datetime.datetime.now();text(now.strftime('%H:%M'),23,89,48,bold=True);text(now.strftime('%Y. %m. %d.'),26,119,14);text('LOCAL TIME',26,37,11)
        elif kind=='calendar':
            import calendar
            now=datetime.datetime.now();text(f'{now.year}. {now.month:02}',20,28,15,bold=True)
            for i,day in enumerate('일월화수목금토'):text(day,23+i*29,49,10)
            for row,week in enumerate(calendar.Calendar(firstweekday=calendar.SUNDAY).monthdayscalendar(now.year,now.month)):
                for col,day in enumerate(week):
                    if day:text(str(day),23+col*29,68+row*16,11,fg if day==now.day else '#edf0f8')
        elif kind=='system':
            for i,(name,val,col) in enumerate([('CPU','24%','#8fa9ff'),('RAM','48%','#c0a1ee'),('SSD','64%','#edb38c')]):
                x=20+i*75;text(name,x,49,11,'#bbc1d3');text(val,x,91,27,col,True);color(col);rounded(x,108,53,5,2);c.fill()
        elif kind=='battery':
            for x,value in [(70,.89),(174,.53)]:
                c.set_line_width(8);color('#8ccfa0',.2);c.arc(x,64,32,0,math.tau);c.stroke();color(fg);c.arc(x,64,32,-math.pi/2,-math.pi/2+value*math.tau);c.stroke();text(str(round(value*100))+'%',x-25,125,22,bold=True)
                color('#e3f4e7');c.set_line_width(2);rounded(x-13,55,26,17,3);c.stroke()
        elif kind in ('music','podcast'):
            color('#b383af');rounded(20,26,64,64,15);c.fill();text('♪',37,73,39,'#ffffff');text('Music',100,51,15,bold=True);text('Now playing',100,75,11);text('◀     ▶     ▶',53,130,22)
        elif kind=='sound':
            text('SOUND',22,38,11);text('65%',22,99,44,bold=True);color(fg,.2);rounded(22,119,195,8,4);c.fill();color(fg);rounded(22,119,128,8,4);c.fill()
        elif kind=='worldclock':
            for i,(city,value) in enumerate([('SEOUL','09:41'),('TOKYO','09:41'),('LONDON','01:41'),('NEW YORK','20:41')]):
                text(city,22,36+i*32,11);text(value,146,36+i*32,22,bold=True)
        elif kind in ('cpu','memory','disk','dayprogress','yearprogress'):
            value={'cpu':24,'memory':48,'disk':64,'dayprogress':40,'yearprogress':79}[kind]
            text({'cpu':'CPU','memory':'MEMORY','disk':'STORAGE','dayprogress':'TODAY','yearprogress':'THIS YEAR'}[kind],22,37,11)
            text(f'{value}%',22,101,46,bold=True);color(fg,.2);rounded(22,124,195,7,3);c.fill();color(fg);rounded(22,124,195*value/100,7,3);c.fill()
        elif kind=='today':
            text(datetime.datetime.now().strftime('%B').upper(),22,37,12);text(str(datetime.datetime.now().day),22,111,65,bold=True);text('TODAY',146,128,12)
        elif kind=='countdown':
            text('COUNTDOWN',22,37,11);text('D−30',22,105,48,bold=True);text('A day to remember',23,132,12)
        elif kind=='note':
            text('MEMO',22,37,11)
            for i,length in enumerate([170,132,158,86]):
                color(fg,.7 if i==0 else .35);rounded(22,57+i*23,length,6,3);c.fill()
        elif kind=='todo':
            text('TO DO',22,33,11)
            for i,length in enumerate([140,115,150]):
                color(fg);rounded(23,52+i*31,14,14,3);c.stroke();color(fg,.4);rounded(48,57+i*31,length,5,2);c.fill()
            text('✓',22,66,17)
        elif kind=='focus':
            text('FOCUS',22,37,11);text('25:00',22,101,48,bold=True);text('▶   START',22,133,12)
        elif kind=='network':
            text('↓ DOWNLOAD',22,33,11);text('12.4 MB/s',22,67,28,bold=True);text('↑ UPLOAD',22,103,11);text('2.8 MB/s',22,137,28,bold=True)
        elif kind=='uptime':
            text('UPTIME',22,37,11);text('08:42',22,101,48,bold=True);text('Since last boot',22,133,12)
        elif kind=='analog':
            color('#f5f3ed');c.arc(120,80,66,0,math.tau);c.fill()
            for n in range(12):
                a=n*math.pi/6;text(str(n or 12),114+52*math.sin(a),85-52*math.cos(a),11,'#30394d')
            color('#30394d');c.set_line_width(4);c.move_to(95,50);c.line_to(120,80);c.line_to(165,65);c.stroke()
        elif kind=='weather':
            text('WEATHER',22,34,11);text('23°',22,99,48,bold=True);text('☀',154,94,43);text('18° / 25°',22,130,14)
        elif kind=='stocks':
            text('TOSS SECURITIES',22,34,11);text('관심 종목',22,75,23,bold=True);text('직접 연결하여 시작',22,125,14)
            color(fg);c.set_line_width(2);c.move_to(139,98);c.line_to(160,87);c.line_to(181,94);c.line_to(216,62);c.stroke()
        elif kind=='agenda':
            text('UP NEXT',22,34,11)
            for i in range(3):
                text(['09:00','13:30','16:00'][i],22,70+i*30,14);color(fg,.4);rounded(88,59+i*30,118-i*15,7,3);c.fill()
        elif kind=='screentime':
            text('SCREEN TIME',22,34,11);text('사용 시간',22,75,24,bold=True)
            for i,h in enumerate([20,30,18,42,35,50,29]):color(fg,.7);rounded(23+i*29,140-h,18,h,3);c.fill()
        elif kind=='home':
            text('HOME',22,34,11);color(fg);c.set_line_width(3);c.move_to(23,75);c.line_to(49,51);c.line_to(75,75);c.move_to(29,70);c.line_to(29,103);c.line_to(69,103);c.line_to(69,70);c.move_to(44,103);c.line_to(44,84);c.line_to(56,84);c.line_to(56,103);c.stroke();text('나의 기기',93,81,23,bold=True);text('Home Assistant 연결',22,135,13)
        else:
            color('#8d7ec0');rounded(24,25,52,52,14);c.fill();text(self.item['name'][0].upper(),40,63,30,'#ffffff',True)
            text('WEB APP',91,57,12,bold=True);text('Click to open',24,125,14)
        return False

class Gallery(Gtk.Application):
    def __init__(self):
        GLib.set_application_name('위젯 보관함')
        Gtk.Window.set_default_icon_from_file(str(store.CONFIG/'assets/widget-gallery.svg'))
        super().__init__(application_id=os.environ.get('EWW_WIDGET_APP_ID','local.ubuntu.WidgetLibrary'),flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.window=None;self.selected=None;self.category='all';self.preset='medium';self.busy=False;self.drag_payload=None
    def do_command_line(self,line):
        args=line.get_arguments()[1:]
        self.activate()
        if len(args)>1 and args[0]=='select':self.select(args[1])
        return 0
    def do_activate(self):
        if self.window is None:self.build()
        self.window.present()
    def build(self):
        self.window=Gtk.ApplicationWindow(application=self,title='위젯 보관함');self.window.set_default_size(1140,860);self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_name('widget-gallery');self.window.connect('destroy',lambda *_:setattr(self,'window',None))
        self.window.connect('key-press-event',self.keypress)
        self.provider=Gtk.CssProvider();Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),self.provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.apply_theme()
        root=Gtk.Box(orientation=Gtk.Orientation.VERTICAL);self.window.add(root)
        header=Gtk.Box(spacing=12);header.get_style_context().add_class('gallery-header');root.pack_start(header,False,False,0)
        titlebox=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4);titlebox.pack_start(label('위젯 보관함','gallery-title'),False,False,0);titlebox.pack_start(label('날씨, 일정, 주식부터 나만의 웹사이트까지','muted'),False,False,0)
        header.pack_start(titlebox,True,True,0)
        header.pack_end(button('아이폰 위젯 안내',self.continuity_info),False,False,0)
        header.pack_end(button('＋ 웹사이트',lambda:self.website_dialog(), 'primary'),False,False,0)
        body=Gtk.Box();root.pack_start(body,True,True,0)
        side=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8);side.set_size_request(155,-1);side.get_style_context().add_class('gallery-sidebar');body.pack_start(side,False,False,0)
        side.pack_start(label('보관함','section-label'),False,False,6)
        self.category_buttons={}
        for key,text in CATEGORIES:
            b=button(text,lambda k=key:self.change_category(k),'category');side.pack_start(b,False,False,0);self.category_buttons[key]=b
        hint=label('위젯을 골라 나만의\n바탕화면을 만들어 보세요.','muted');hint.set_line_wrap(True);side.pack_start(hint,False,False,20)
        side.pack_start(Gtk.Box(),True,True,0)
        side.pack_start(label('글래스 효과','section-label'),False,False,4)
        glass_row=Gtk.Box(spacing=8);glass_row.pack_start(label('전체 위젯'),True,True,0)
        self.glass_switch=Gtk.Switch();self.glass_switch.set_valign(Gtk.Align.CENTER);self.glass_switch.set_active(glass_effect.settings()['enabled'])
        self.glass_switch.get_accessible().set_name('전체 위젯 글래스 효과')
        self.glass_switch.connect('notify::active',lambda switch,_:self.glass_changed(switch))
        glass_row.pack_end(self.glass_switch,False,False,0);side.pack_start(glass_row,False,False,0)
        glass_hint=label('반투명 배경과 은은한 흐림','muted');side.pack_start(glass_hint,False,False,0)
        side.pack_start(label('위젯 테마','section-label'),False,False,12)
        self.theme=Gtk.ComboBoxText()
        for key,text in [('auto','시스템 설정 따르기'),('light','라이트'),('dark','다크')]:self.theme.append(key,text)
        try:mode=(store.CONFIG/'theme-mode').read_text().strip()
        except OSError:mode='auto'
        self.theme.set_active_id(mode);self.theme.connect('changed',self.theme_changed);side.pack_start(self.theme,False,False,0)
        center=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12);center.get_style_context().add_class('gallery-center');center.set_size_request(540,-1);body.pack_start(center,True,True,0)
        self.search=Gtk.SearchEntry(placeholder_text='이름이나 기능으로 검색 · Ctrl+F');self.search.connect('search-changed',lambda *_:self.refresh_tiles());center.pack_start(self.search,False,False,0)
        self.count=label('','muted');center.pack_start(self.count,False,False,0)
        scroll=Gtk.ScrolledWindow();scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);center.pack_start(scroll,True,True,0)
        self.flow=Gtk.FlowBox();self.flow.set_min_children_per_line(3);self.flow.set_max_children_per_line(3);self.flow.set_selection_mode(Gtk.SelectionMode.NONE);self.flow.set_row_spacing(12);self.flow.set_column_spacing(12);self.flow.set_valign(Gtk.Align.START);scroll.add(self.flow)
        self.details=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12);self.details.set_size_request(270,-1);self.details.get_style_context().add_class('gallery-details');detail_scroll=Gtk.ScrolledWindow();detail_scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);detail_scroll.add(self.details);body.pack_start(detail_scroll,False,False,0)
        footer=Gtk.Box(spacing=8);footer.get_style_context().add_class('gallery-footer');root.pack_start(footer,False,False,0)
        self.spinner=Gtk.Spinner();footer.pack_start(self.spinner,False,False,0)
        self.status=label('위젯을 선택한 뒤 추가하거나, 미리보기를 바탕화면으로 끌어 놓으세요.','muted');self.status.set_ellipsize(Pango.EllipsizeMode.END);footer.pack_start(self.status,True,True,0)
        footer.pack_end(button('완료',self.window.close),False,False,0)
        self.selected=store.library()[0]['id'];self.refresh_tiles();self.refresh_details();self.change_category('all');self.window.show_all()
        self.monitor=Gio.File.new_for_path(str(store.CONFIG)).monitor_directory(Gio.FileMonitorFlags.NONE,None)
        self.monitor.connect('changed',self.files_changed)
        self.settings=Gio.Settings.new('org.gnome.desktop.interface');self.settings.connect('changed::color-scheme',lambda *_:self.apply_theme());self.settings.connect('changed::gtk-theme',lambda *_:self.apply_theme())
    def continuity_info(self):
        d=Gtk.MessageDialog(transient_for=self.window,modal=True,message_type=Gtk.MessageType.INFO,buttons=Gtk.ButtonsType.CLOSE,text='아이폰 연속성 위젯')
        d.format_secondary_text('Apple의 아이폰 위젯 연속성은 macOS 기능으로 Ubuntu에서는 직접 사용할 수 없습니다.\n\n웹으로 제공되는 서비스는 ＋ 웹사이트에서 바로가기로 추가할 수 있습니다. 아이폰 앱 화면이나 알림을 미러링하는 기능은 제공하지 않습니다.')
        d.run();d.destroy()
    def keypress(self,_window,event):
        if event.keyval==Gdk.KEY_Escape:self.window.close();return True
        if event.state&Gdk.ModifierType.CONTROL_MASK and event.keyval==Gdk.KEY_f:self.search.grab_focus();return True
        return False
    def apply_theme(self):
        dark=current_theme()=='dark'
        bg,panel,text,muted,border,tile,hover,accent=('#17191f','#1f222a','#f1f3f8','#a5adbd','#343945','#292e39','#353d4d','#96b6ff') if dark else ('#f7f8fb','#eef0f5','#252b38','#6f788b','#dce0e9','#ffffff','#e9effb','#365fc4')
        css=f'''
#widget-gallery {{ background:{bg}; color:{text}; font-family:sans-serif; font-size:12px; }}
#widget-gallery label {{ color:{text}; }}
#widget-gallery .muted, #widget-gallery .section-label {{ color:{muted}; font-size:10px; }}
#widget-gallery .gallery-header {{ padding:22px 24px; border-bottom:1px solid {border}; }}
#widget-gallery .gallery-title {{ font-size:25px; font-weight:700; letter-spacing:-0.8px; }}
#widget-gallery .gallery-sidebar {{ background:{panel}; padding:20px 12px; border-right:1px solid {border}; }}
#widget-gallery .gallery-center {{ padding:20px 18px; }}
#widget-gallery .gallery-details {{ background:{panel}; padding:22px 18px; border-left:1px solid {border}; }}
#widget-gallery .gallery-footer {{ padding:14px 20px; border-top:1px solid {border}; }}
#widget-gallery button {{ background:{tile}; color:{text}; border:1px solid {border}; border-radius:10px; padding:9px 12px; box-shadow:none; text-shadow:none; }}
#widget-gallery button:hover {{ background:{hover}; }}
#widget-gallery button.primary {{ background:#3c68d6; color:#fff; border-color:#3c68d6; font-weight:600; }}
#widget-gallery button.primary label {{ color:#fff; }}
#widget-gallery button.category, #widget-gallery button.preset-site {{ background:transparent; border-color:transparent; }}
#widget-gallery button.category.selected {{ background:{hover}; border-color:{border}; }}
#widget-gallery button.tile {{ padding:9px; border-radius:17px; }}
#widget-gallery button.tile.selected {{ border:2px solid {accent}; padding:8px; }}
#widget-gallery .tile-name {{ font-size:12px; font-weight:600; }}
#widget-gallery .tile-state {{ font-size:9px; color:{muted}; }}
#widget-gallery .detail-title {{ font-size:20px; font-weight:700; }}
#widget-gallery .description {{ font-size:11px; color:{muted}; }}
#widget-gallery entry, #widget-gallery combobox button {{ background:{tile}; color:{text}; border:1px solid {border}; border-radius:9px; padding:8px; }}
#widget-gallery button.size:checked {{ background:{hover}; border-color:{accent}; }}
#widget-gallery button.danger label {{ color:#e1848f; }}
#widget-gallery button:disabled {{ opacity:.45; }}
#widget-gallery switch {{ border-radius:14px; background:{border}; border:1px solid {border}; }}
#widget-gallery switch:checked {{ background:#3c68d6; border-color:#3c68d6; }}
#widget-gallery switch slider {{ min-width:18px; min-height:18px; margin:2px; border-radius:12px; background:#f6f8ff; }}
'''
        self.provider.load_from_data(css.encode())
    def files_changed(self,_mon,file,other,_event):
        names={f.get_basename() for f in (file,other) if f}
        if names&{'web-widgets.json','hidden-widgets.json','enabled-widgets.json'} and not self.busy:GLib.idle_add(self.refresh_all)
        if 'theme-mode' in names:GLib.idle_add(self.apply_theme)
        if 'glass-settings.json' in names:GLib.idle_add(self.sync_glass)
    def sync_glass(self):
        if self.window is None:return False
        self._syncing_glass=True
        self.glass_switch.set_active(glass_effect.settings()['enabled'])
        self._syncing_glass=False
        self.refresh_all();return False
    def glass_changed(self,switch,widget_id=None):
        if getattr(self,'_syncing_glass',False):return
        try:
            glass_effect.set_enabled(switch.get_active(),widget_id)
            self.status.set_text(('이 위젯의 ' if widget_id else '전체 위젯의 ')+'글래스 효과를 '+('켰습니다.' if switch.get_active() else '껐습니다.'))
        except (OSError,ValueError) as exc:self.status.set_text(str(exc))
        GLib.idle_add(self.sync_glass)
    def theme_changed(self,combo):
        mode=combo.get_active_id()
        if mode:store.atomic_text('theme-mode',mode+'\n');self.apply_theme()
    def change_category(self,key):
        self.category=key
        for name,b in self.category_buttons.items():
            ctx=b.get_style_context();ctx.add_class('selected') if name==key else ctx.remove_class('selected')
        self.refresh_tiles()
    def refresh_all(self):
        if self.window is None:return False
        try:self.refresh_tiles();self.refresh_details()
        except Exception as exc:self.status.set_text(str(exc))
        return False
    def refresh_tiles(self):
        for child in self.flow.get_children():self.flow.remove(child)
        query=self.search.get_text().casefold();hidden=store.hidden();items=store.library()
        shown=[w for w in items if (self.category=='all' or (self.category=='added' and w['kind']!='webpreset' and w['id'] not in hidden) or w['category']==self.category) and query in (w['name']+' '+w.get('description','')+' '+w.get('url','')).casefold()]
        if shown and self.selected not in {w['id'] for w in shown}:
            self.selected=shown[0]['id'];self.refresh_details()
        self.count.set_text(f'{len(shown)}개 · 전체 {len(items)}종' if shown else '검색 결과가 없습니다. 다른 이름이나 기능으로 검색해 보세요.')
        for item in shown:
            b=Gtk.Button();b.get_style_context().add_class('tile')
            if item['id']==self.selected:b.get_style_context().add_class('selected')
            content=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6);content.pack_start(Preview(item),False,False,0)
            name=label(item['name'],'tile-name');name.set_ellipsize(Pango.EllipsizeMode.END);name.set_max_width_chars(16);content.pack_start(name,False,False,0)
            content.pack_start(label('웹앱 바로가기' if item['kind']=='webpreset' else '추가 가능' if item['id'] in hidden else '✓ 바탕화면에 추가됨','tile-state'),False,False,0)
            b.add(content);b.connect('clicked',lambda _,i=item['id']:self.select(i));self.flow.add(b)
        self.flow.show_all()
    def select(self,widget_id):
        try:item=store.library_find(widget_id)
        except ValueError:return
        self.search.set_text('')
        if self.category not in ('all',item['category']) and not (self.category=='added' and widget_id not in store.hidden()):self.change_category(item['category'])
        self.selected=widget_id;self.preset='medium';self.refresh_all()
    def refresh_details(self):
        for child in self.details.get_children():self.details.remove(child)
        items=store.library()
        item=next((w for w in items if w['id']==self.selected),items[0]);self.selected=item['id']
        preview=Gtk.EventBox();preview.add(Preview(item,True));preview.set_tooltip_text('바탕화면으로 끌어 놓아 배치')
        preview.drag_source_set(Gdk.ModifierType.BUTTON1_MASK,[Gtk.TargetEntry.new('application/x-eww-widget',0,0)],Gdk.DragAction.COPY)
        preview.connect('drag-begin',self.drag_begin);preview.connect('drag-data-get',self.drag_data);preview.connect('drag-failed',self.drag_failed);preview.connect('drag-end',self.drag_end)
        self.details.pack_start(preview,False,False,0)
        self.details.pack_start(label(item['name'],'detail-title'),False,False,0)
        desc=label(item.get('description',''),'description');desc.set_line_wrap(True);desc.set_max_width_chars(28);self.details.pack_start(desc,False,False,0)
        if item['kind'] in ('web','webpreset'):
            url=label(item['url'],'muted');url.set_ellipsize(Pango.EllipsizeMode.MIDDLE);url.set_max_width_chars(28);url.set_tooltip_text(item['url']);self.details.pack_start(url,False,False,0)
        glass_row=Gtk.Box(spacing=8);glass_row.pack_start(label('이 위젯 글래스'),True,True,0)
        glass_switch=Gtk.Switch();glass_switch.set_valign(Gtk.Align.CENTER)
        glass_switch.set_active(glass_effect.allowed(item));glass_switch.set_sensitive(glass_effect.settings()['enabled'])
        glass_switch.set_tooltip_text('왼쪽의 전체 글래스 효과가 켜져 있을 때 적용됩니다.')
        glass_switch.get_accessible().set_name(item['name']+' 글래스 효과')
        glass_switch.connect('notify::active',lambda switch,_:self.glass_changed(switch,item['id']))
        glass_row.pack_end(glass_switch,False,False,0);self.details.pack_start(glass_row,False,False,0)
        self.details.pack_start(label('크기','section-label'),False,False,0)
        sizes=Gtk.Box(spacing=5);group=None
        for key,text in [('small','작게'),('medium','중간'),('large','크게')]:
            b=Gtk.RadioButton.new_with_label_from_widget(group,text);group=group or b;b.set_mode(False);b.get_style_context().add_class('size');b.set_active(key==self.preset)
            b.connect('toggled',lambda btn,k=key:self.set_size(k) if btn.get_active() else None);sizes.pack_start(b,True,True,0)
        self.details.pack_start(sizes,False,False,0)
        self.dimensions=label('','muted');self.details.pack_start(self.dimensions,False,False,0);self.set_size(self.preset)
        added=item['kind']!='webpreset' and item['id'] not in store.hidden()
        self.details.pack_start(button('선택한 크기 적용' if added else '＋ 바탕화면에 추가',self.add_selected,'primary'),False,False,0)
        if added:self.details.pack_start(button('바탕화면에서 제거',lambda:self.work(lambda:store.remove(item['id']),'바탕화면에서 제거했습니다.')),False,False,0)
        if item.get('configurable'):
            self.details.pack_start(button('연결·설정' if item['kind'] in ('stocks','weather','home','screentime') else '내용·시간 설정',lambda:self.configure_dialog(item)),False,False,0)
        if item['kind']=='web':
            self.details.pack_start(button('사이트 열기',lambda:store.launch_web(item['id'])),False,False,0)
            self.details.pack_start(button('이름·주소 편집',lambda:self.website_dialog(item['name'],item['url'],item['id'])),False,False,0)
        self.details.pack_start(Gtk.Box(),True,True,0)
        tip=label('미리보기는 예시입니다. 추가한 위젯은 실제 데이터로 표시됩니다.\n\n위의 미리보기를 바탕화면으로 끌어 놓아도 추가할 수 있습니다.','muted');tip.set_line_wrap(True);tip.set_max_width_chars(28);self.details.pack_start(tip,False,False,0)
        self.details.show_all()
    def set_size(self,key):
        self.preset=key
        if hasattr(self,'dimensions'):
            w,h=store.PRESETS[key];self.dimensions.set_text(f'{w} × {h} · 추가한 뒤 자유롭게 조절 가능')
    def add_selected(self):
        widget_id=self.selected;preset=self.preset
        self.work(lambda:store.add_library(widget_id,preset),'바탕화면에 적용했습니다. 위젯 본문을 드래그해 이동하고 양쪽 가장자리로 가로폭을 조절하세요.',lambda wid:setattr(self,'selected',wid))
    def work(self,fn,message,after=None):
        if self.busy:return
        self.busy=True;self.spinner.start();self.details.set_sensitive(False);self.status.set_text('적용하는 중…')
        def worker():
            try:result=fn();error=None
            except Exception as exc:result=None;error=str(exc)
            GLib.idle_add(done,result,error)
        def done(result,error):
            self.busy=False
            if self.window is None:return False
            self.spinner.stop();self.details.set_sensitive(True)
            if not error and after:after(result)
            self.refresh_all();self.status.set_text(error or message)
            if error:
                dialog=Gtk.MessageDialog(transient_for=self.window,modal=True,message_type=Gtk.MessageType.ERROR,buttons=Gtk.ButtonsType.CLOSE,text='위젯을 적용하지 못했습니다.');dialog.format_secondary_text(error);dialog.run();dialog.destroy()
            return False
        threading.Thread(target=worker,daemon=True).start()
    def configure_dialog(self,item):
        kind=item['kind']
        if kind in ('stocks','weather','home','screentime'):return connection_dialog.open_dialog(self,item)
        cfg=library_data.config(kind)
        d=Gtk.Dialog(title=item['name']+' 설정',transient_for=self.window,modal=True)
        d.set_default_size(460,320);d.add_button('취소',Gtk.ResponseType.CANCEL);d.add_button('저장',Gtk.ResponseType.OK)
        box=d.get_content_area();box.set_border_width(20);box.set_spacing(10);fields={}
        def entry(key,title,value):
            box.pack_start(label(title),False,False,0);w=Gtk.Entry(text=str(value));fields[key]=w;box.pack_start(w,False,False,0)
        if kind in ('note','countdown'):entry('title','제목',cfg['title'])
        if kind in ('note','todo','agenda'):
            box.pack_start(label('메모 · 최대 2,000자' if kind=='note' else 'YYYY-MM-DD HH:MM | 일정 제목 · 한 줄에 하나씩, 최대 40개' if kind=='agenda' else '한 줄에 한 가지씩 · 최대 12개'),False,False,0)
            view=Gtk.TextView();view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR);buffer=view.get_buffer()
            buffer.set_text(cfg['text'] if kind=='note' else '\n'.join(t['at']+' | '+t['title'] for t in cfg['events']) if kind=='agenda' else '\n'.join(t['text'] for t in cfg['tasks']))
            scroll=Gtk.ScrolledWindow();scroll.set_min_content_height(180);scroll.add(view);box.pack_start(scroll,True,True,0)
        if kind=='countdown':entry('date','날짜 · YYYY-MM-DD',cfg['date'])
        if kind=='focus':
            box.pack_start(label('집중 시간 · 1~180분'),False,False,0)
            spin=Gtk.SpinButton.new_with_range(1,180,1);spin.set_value(cfg['minutes']);box.pack_start(spin,False,False,0)
            box.pack_start(label('저장하면 진행 중인 타이머가 초기화됩니다.','muted'),False,False,0)
        error=label('');error.set_line_wrap(True);error.set_max_width_chars(45);box.pack_start(error,False,False,0);d.show_all()
        while d.run()==Gtk.ResponseType.OK:
            values={key:w.get_text() for key,w in fields.items()}
            if kind in ('note','todo','agenda'):values['text']=buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter(),True)
            if kind=='focus':values['minutes']=spin.get_value_as_int()
            try:library_data.save_config(kind,values)
            except (ValueError,OSError) as exc:error.set_text(str(exc));continue
            self.status.set_text('설정을 저장했습니다. 바탕화면 위젯에 바로 반영됩니다.');break
        d.destroy()

    def website_dialog(self,name='',url='',widget_id=None):
        d=Gtk.Dialog(title='웹사이트 편집' if widget_id else '웹사이트 위젯 추가',transient_for=self.window,modal=True)
        d.set_default_size(420,220);d.add_button('취소',Gtk.ResponseType.CANCEL)
        if widget_id:d.add_button('목록에서 삭제',Gtk.ResponseType.REJECT)
        d.add_button('저장' if widget_id else '만들고 추가',Gtk.ResponseType.OK)
        box=d.get_content_area();box.set_border_width(20);box.set_spacing(10)
        box.pack_start(label('이름'),False,False,0);nameentry=Gtk.Entry(text=name,placeholder_text='예: 노션, 네이버 메일');box.pack_start(nameentry,False,False,0)
        box.pack_start(label('웹사이트 주소'),False,False,0);urlentry=Gtk.Entry(text=url,placeholder_text='https://');box.pack_start(urlentry,False,False,0)
        note=label('위젯을 누르면 Chrome 독립 창으로 열립니다.');note.set_line_wrap(True);box.pack_start(note,False,False,0)
        err=label('');box.pack_start(err,False,False,0);d.show_all()
        while True:
            response=d.run()
            if response==Gtk.ResponseType.OK:
                try:
                    n=nameentry.get_text().strip();u=store.normalize_url(urlentry.get_text())
                    if not n or len(n)>60:raise ValueError('이름을 1~60자로 입력하세요.')
                except ValueError as exc:err.set_text(str(exc));continue
                d.destroy()
                def action():
                    if widget_id:store.edit_web(widget_id,n,u);return widget_id
                    new=store.create_web(n,u);store.show(new,self.preset);return new
                self.work(action,'웹사이트 위젯을 저장했습니다.',lambda wid:setattr(self,'selected',wid));break
            elif response==Gtk.ResponseType.REJECT and widget_id:
                d.destroy();self.work(lambda:store.delete_web(widget_id),'웹사이트를 목록에서 삭제했습니다.');break
            else:d.destroy();break
    def drag_begin(self,_w,ctx):
        self.drag_payload=(self.selected,self.preset);Gtk.drag_set_icon_name(ctx,store.library_find(self.selected)['icon'],0,0)
    def drag_data(self,_w,_ctx,selection,_info,_time):
        if self.drag_payload:selection.set(selection.get_target(),8,self.drag_payload[0].encode())
    def drag_failed(self,_w,_ctx,result):
        if result!=Gtk.DragResult.NO_TARGET or not self.drag_payload:return False
        _screen,x,y=Gdk.Display.get_default().get_default_seat().get_pointer().get_position()
        wx,wy=self.window.get_position();ww,wh=self.window.get_size()
        if wx<=x<wx+ww and wy<=y<wy+wh:return True
        widget_id,preset=self.drag_payload
        self.work(lambda:store.add_library(widget_id,preset,(x,y)),'놓은 위치에 위젯을 추가했습니다.',lambda wid:setattr(self,'selected',wid))
        return True
    def drag_end(self,*_):self.drag_payload=None

if __name__=='__main__':
    raise SystemExit(Gallery().run(sys.argv))
