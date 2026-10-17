"""Persistent glass settings and GTK3 palette generation.

The native foreground stays opaque. Blur is requested per X11 window with
Blur my Shell's documented _MUTTER_HINTS protocol by glass_windows.py.
"""
import json
import os
from pathlib import Path
import widget_store as store

SETTINGS='glass-settings.json'

def settings():
    value=store.read_json(SETTINGS,{'enabled':True,'overrides':{}})
    if not isinstance(value,dict) or not isinstance(value.get('enabled'),bool) or not isinstance(value.get('overrides'),dict):
        raise ValueError('글래스 효과 설정을 읽을 수 없습니다.')
    if any(not isinstance(v,bool) for v in value['overrides'].values()):raise ValueError('글래스 효과 설정이 올바르지 않습니다.')
    return value

def key_for(item):
    # Preset preference follows the newly created site card as well.
    if item['kind']=='web':
        for preset in store.SITE_PRESETS:
            if store.normalize_url(preset['url'])==item['url']:return preset['id']
    return item['id']

def allowed(item,value=None):
    value=settings() if value is None else value
    return value['overrides'].get(key_for(item),True)

def enabled(item,value=None):
    value=settings() if value is None else value
    return value['enabled'] and allowed(item,value)

def set_enabled(value,widget_id=None):
    if not isinstance(value,bool):raise ValueError('켜기 또는 끄기로 설정하세요.')
    with store.locked():
        current=settings()
        if widget_id is None:current['enabled']=value
        else:
            item=store.library_find(widget_id);key=key_for(item)
            if value:current['overrides'].pop(key,None)
            else:current['overrides'][key]=False
        store.atomic_json(SETTINGS,current)

PALETTES={
    'dark':{
        'navy':('36, 55, 85','23, 35, 53'),
        'neutral':('43, 51, 65','28, 36, 48'),
        'blue':('42, 59, 82','27, 41, 59'),
        'pink':('58, 48, 60','37, 38, 50'),
        'green':('41, 61, 53','27, 41, 38'),
        'purple':('55, 51, 73','37, 40, 56'),
        'yellow':('60, 55, 46','42, 39, 35')},
    'light':{
        'navy':('37, 63, 105','22, 41, 66'),
        'neutral':('251, 252, 254','232, 237, 244'),
        'blue':('233, 241, 252','220, 232, 244'),
        'pink':('243, 234, 240','233, 226, 236'),
        'green':('233, 243, 239','222, 234, 230'),
        'purple':('238, 234, 250','226, 227, 239'),
        'yellow':('251, 245, 232','238, 228, 210')}
}

def tone(item):
    kind=item['kind']
    if kind=='clock':return 'navy'
    if kind in ('music','podcast','agenda'):return 'pink'
    if kind in ('weather','stocks','worldclock','today','dayprogress','yearprogress','countdown'):return 'blue'
    if kind in ('battery','cpu','memory','disk','network','uptime','kdeconnect'):return 'green'
    if kind in ('note','screentime','web','webpreset'):return 'purple'
    if kind in ('focus','home'):return 'yellow'
    return 'neutral'

def stylesheet(mode,items=None,value=None):
    value=settings() if value is None else value;items=store.catalogue() if items is None else items
    active=[i for i in items if enabled(i,value)]
    if not active:return '/* Glass disabled. Original card palette remains active. */\n'
    if mode not in PALETTES:raise ValueError('Invalid palette')
    selector=lambda item:'.glass-'+item['id']
    border='.14' if mode=='dark' else '.78'
    shade='.24' if mode=='dark' else '.12'
    sheen='.06' if mode=='dark' else '.65'
    lines=['/* Generated glass palette. Toggle it in the widget library. */\n',
           ',\n'.join(selector(i) for i in active)+' {\n'+
           f'  border-color: rgba(255, 255, 255, {border});\n'+
           f'  box-shadow: inset 0 1px 0 rgba(255, 255, 255, {sheen}), inset 0 -1px 0 rgba(255, 255, 255, .05), 0 4px 8px rgba(0, 0, 0, {shade});\n'+
           '}\n']
    for name,colors in PALETTES[mode].items():
        group=[i for i in active if tone(i)==name]
        if not group:continue
        a,b=colors
        alpha=('.94','.90') if mode=='dark' or name=='navy' else ('.92','.86')
        highlight='.05' if mode=='dark' or name=='navy' else '.20'
        lines.append(',\n'.join(selector(i) for i in group)+' {\n'+
            f'  background: linear-gradient(145deg, rgba(255, 255, 255, {highlight}), rgba(255, 255, 255, .01) 45%, rgba(255, 255, 255, .06)), linear-gradient(125deg, rgba({a}, {alpha[0]}), rgba({b}, {alpha[1]}));\n'+
            '}\n')
    if mode=='dark':
        # Readable secondary labels over bright wallpaper; never fade text itself.
        lines.append(',\n'.join('.glass-'+i['id']+' label' for i in active)+' { text-shadow: 0 1px 2px rgba(0, 0, 0, .28); }\n')
    return ''.join(lines)

def blur_settings(component='applications'):
    from gi.repository import Gio
    roots=[Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share')),Path('/usr/share')]
    path=next((root/'gnome-shell/extensions/blur-my-shell@aunetx/schemas' for root in roots if (root/'gnome-shell/extensions/blur-my-shell@aunetx/schemas').is_dir()),None)
    if path is None:return None
    source=Gio.SettingsSchemaSource.new_from_directory(str(path),Gio.SettingsSchemaSource.get_default(),False)
    schema=source.lookup('org.gnome.shell.extensions.blur-my-shell'+('.'+component if component else ''),False)
    return Gio.Settings.new_full(schema,None,None) if schema else None

def sync_compositor(active):
    """Enable the existing blur provider; preserve/restore its prior preferences.

    No application whitelist is modified. Only our windows get blur hints.
    Settings changed externally after setup are not overwritten on cleanup.
    """
    if os.environ.get('EWW_GLASS_SKIP_COMPOSITOR')=='1':return
    from gi.repository import Gio
    backend=blur_settings()
    if backend is None:return
    state=store.read_json('glass-compositor-state.json',{})
    general=blur_settings('')
    if general is None or not all(backend.props.settings_schema.has_key(k) for k in ('blur','opacity')) or not general.props.settings_schema.has_key('hacks-level'):return
    fields={'blur':True,'opacity':255,'hacks-level':3}
    target=lambda key:general if key=='hacks-level' else backend
    if active:
        if not state.get('owned'):
            state={'owned':True,'before':{key:target(key).get_value(key).unpack() for key in fields}}
            store.atomic_json('glass-compositor-state.json',state)
            # Alpha comes exclusively from CSS so labels and icons remain sharp.
            backend.set_int('opacity',255);general.set_int('hacks-level',3);backend.set_boolean('blur',True);Gio.Settings.sync()
    elif state.get('owned'):
        for key,applied in fields.items():
            if key in state['before'] and target(key).get_value(key).unpack()==applied:
                if key=='blur':target(key).set_boolean(key,state['before'][key])
                else:target(key).set_int(key,state['before'][key])
        Gio.Settings.sync();store.atomic_json('glass-compositor-state.json',{'owned':False})
