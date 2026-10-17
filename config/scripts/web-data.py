#!/usr/bin/python3
import json,time
from urllib.parse import urlsplit
from widget_store import web_widgets
last=None
while True:
    try:
        data={w['id']+'-'+key:value for w in web_widgets() for key,value in {'name':w['name'],'host':urlsplit(w['url']).hostname,'letter':w['name'][0].upper()}.items()}
        encoded=json.dumps(data,ensure_ascii=False)
        if encoded!=last:print(encoded,flush=True);last=encoded
    except Exception as exc:
        import sys
        print(f'Web widget catalogue: {exc}',file=sys.stderr,flush=True)
    time.sleep(.5)
