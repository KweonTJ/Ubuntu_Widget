"""Small asynchronous cache for the current MPRIS artwork, never player credentials."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import math
import os
from pathlib import Path
import tempfile
import time
import urllib.parse
import urllib.request

import cairo
import gi
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gdk, GdkPixbuf

CACHE = Path(os.environ.get('XDG_CACHE_HOME', Path.home()/'.cache'))/'ubuntu-widget'/'album-art'
MAX_BYTES = 8*1024*1024
SIZE = 512


def artwork_key(source):
    """A reused local artwork path must refresh when its contents change."""
    if not source or len(source)>16384:return ''
    uri=urllib.parse.urlsplit(source)
    if uri.scheme=='file' and uri.netloc in ('','localhost'):
        try:
            path=Path(urllib.request.url2pathname(uri.path));stat=path.stat()
            if not path.is_file() or stat.st_size>MAX_BYTES:return ''
        except OSError:return ''
        source += f'|{stat.st_mtime_ns}|{stat.st_size}'
    elif uri.scheme not in ('http','https') or not uri.hostname:return ''
    return hashlib.sha256(("cover-512-v2|"+source).encode()).hexdigest()


class ArtworkRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        if urllib.parse.urlsplit(new_url).scheme not in ('http','https'):
            raise ValueError('Unsupported artwork redirect')
        return super().redirect_request(request,response,code,message,headers,new_url)


def read_artwork(source):
    uri=urllib.parse.urlsplit(source)
    if uri.scheme=='file' and uri.netloc in ('','localhost'):
        with Path(urllib.request.url2pathname(uri.path)).open('rb') as file:data=file.read(MAX_BYTES+1)
    elif uri.scheme in ('http','https'):
        request=urllib.request.Request(source,headers={'User-Agent':'Ubuntu-Widget/album-art','Accept':'image/*'})
        with urllib.request.build_opener(ArtworkRedirect).open(request,timeout=2) as response:
            data=response.read(MAX_BYTES+1)
    else:raise ValueError('Unsupported artwork URL')
    if not data or len(data)>MAX_BYTES:raise ValueError('Invalid artwork size')
    return data


def render_artwork(source, target):
    raw=read_artwork(source)
    loader=GdkPixbuf.PixbufLoader.new()
    def fit(current,width,height):
        scale=min(1,SIZE/max(width,height))
        current.set_size(max(1,round(width*scale)),max(1,round(height*scale)))
    loader.connect('size-prepared',fit)
    try:
        loader.write(raw);loader.close()
    except Exception:
        try:loader.close()
        except Exception:pass
        raise
    image=loader.get_pixbuf()
    side=min(image.get_width(),image.get_height())
    square=image.new_subpixbuf((image.get_width()-side)//2,(image.get_height()-side)//2,side,side)
    square=square.scale_simple(SIZE,SIZE,GdkPixbuf.InterpType.BILINEAR)
    surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,SIZE,SIZE);ctx=cairo.Context(surface)
    radius=SIZE*.1
    for x,y,start in ((SIZE-radius,radius,-90),(SIZE-radius,SIZE-radius,0),(radius,SIZE-radius,90),(radius,radius,180)):
        ctx.arc(x,y,radius,math.radians(start),math.radians(start+90))
    ctx.close_path();ctx.clip();Gdk.cairo_set_source_pixbuf(ctx,square,0,0);ctx.paint()
    target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,name=tempfile.mkstemp(prefix='.cover-',dir=target.parent);os.close(fd)
    try:
        surface.write_to_png(name);os.replace(name,target)
    finally:
        if os.path.exists(name):os.unlink(name)
    # Bound artwork history without retaining the original URL or player metadata.
    for old in sorted(target.parent.glob('*.png'),key=lambda path:path.stat().st_mtime,reverse=True)[64:]:
        if old!=target:old.unlink(missing_ok=True)
    return str(target)


class ArtworkCache:
    def __init__(self,directory=None):
        self.directory=Path(directory) if directory is not None else CACHE
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='album-art')
        self.job=None;self.failures={}

    def get(self,source):
        """Never block media updates, or return the previous track's picture."""
        try:key=artwork_key(source)
        except (OSError,ValueError):return ''
        if self.job and self.job[1].done():
            old_key,future=self.job;self.job=None
            try:future.result()
            except Exception:self.failures[old_key]=time.monotonic()+60
        if not key:return ''
        target=self.directory/(key+'.png')
        if target.is_file():return str(target)
        now=time.monotonic();self.failures={k:v for k,v in self.failures.items() if v>now}
        if self.job is None and key not in self.failures:
            self.job=(key,self.pool.submit(render_artwork,source,target))
        return ''
