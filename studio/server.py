"""Local Studio server: persistent projects, uploads, jobs, and a Hermes adapter."""
import argparse, base64, concurrent.futures, hashlib, hmac, json, mimetypes, os, re, secrets, subprocess, threading, time, uuid
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
ROOT=Path(__file__).resolve().parents[1]
DATA=Path(os.environ.get('STUDIO_DATA',ROOT/'data')).resolve()
HERMES=Path(os.environ.get('HERMES_ROOT',Path.home()/'.hermes/hermes-agent'))
POOL=concurrent.futures.ThreadPoolExecutor(max_workers=2)
LOCK=threading.RLock()
JOBS={}
TOKEN=os.environ.get('STUDIO_TOKEN','')

def init():
    DATA.mkdir(parents=True,exist_ok=True)
    (DATA/'media').mkdir(exist_ok=True)

def atomic(path,obj):
    with LOCK:
        temp=path.with_suffix('.tmp');temp.write_text(json.dumps(obj,ensure_ascii=False));temp.replace(path)

def bridge(payload):
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    proc=subprocess.run([str(HERMES/'venv/bin/python'),str(ROOT/'studio/hermes_bridge.py')],input=json.dumps(payload),text=True,capture_output=True,timeout=600,env=env,cwd=ROOT)
    try: result=json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError): raise RuntimeError('Hermes adapter could not start. Check HERMES_ROOT and its Python environment.')
    if result.get('error'): raise RuntimeError(result['error'])
    return result

def safe_media(url):
    if not isinstance(url,str): raise ValueError('Invalid image')
    if url.startswith('/media/'):
        p=(DATA/'media'/url.removeprefix('/media/')).resolve();base=DATA/'media'
    elif url.startswith('/references/'):
        p=(ROOT/'public'/url.lstrip('/')).resolve();base=ROOT/'public/references'
    else: raise ValueError('Use uploaded or library images')
    if not p.is_relative_to(base.resolve()) or not p.is_file(): raise ValueError('Image not found')
    return p

def task(job,payload):
    try:
        if payload['op']=='generate':
            refs=[]
            for url in payload.pop('references',[]):
                p=safe_media(url);mime=mimetypes.guess_type(p)[0] or 'image/png'
                refs.append('data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode())
            payload['references']=refs
        result=bridge(payload)
        if 'data' in result and payload['op']=='generate':
            raw=base64.b64decode(result.pop('data'),validate=True)
            ext=sniff(raw)
            name=uuid.uuid4().hex+ext;(DATA/'media'/name).write_bytes(raw)
            result['url']='/media/'+name
        with LOCK:JOBS[job]={'status':'complete','result':result}
    except Exception as e:
        with LOCK:JOBS[job]={'status':'error','error':str(e)}

def sniff(raw):
    if raw.startswith(b'\x89PNG\r\n\x1a\n'):return '.png'
    if raw.startswith(b'\xff\xd8\xff'):return '.jpg'
    if raw[:4]==b'RIFF' and raw[8:12]==b'WEBP':return '.webp'
    raise ValueError('Upload a PNG, JPEG, or WebP image')

def submit(payload):
    if payload.get('op') not in ('generate','copy','chat','conversations','catalog'):raise ValueError('Unknown operation')
    if len(json.dumps(payload))>200000:raise ValueError('Request is too large')
    with LOCK:
        if sum(x['status']=='running' for x in JOBS.values())>=4:raise ValueError('Four requests are already running. Please wait.')
        for key in list(JOBS)[:-100]:
            if JOBS[key]['status']!='running':JOBS.pop(key)
        job=uuid.uuid4().hex;JOBS[job]={'status':'running'}
    POOL.submit(task,job,payload)
    return {'job':job}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**k):super().__init__(*a,directory=str(ROOT/'dist/client'),**k)
    def log_message(self,fmt,*args):pass
    def json(self,obj,status=200):
        raw=json.dumps(obj).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def allowed(self):
        origin=self.headers.get('Origin')
        host=self.headers.get('Host','')
        if origin and urlparse(origin).netloc!=host:return False
        if TOKEN:
            auth=self.headers.get('Authorization','').removeprefix('Bearer ')
            return hmac.compare_digest(auth,TOKEN)
        return self.client_address[0] in ('127.0.0.1','::1') and host.split(':')[0] in ('127.0.0.1','localhost','[::1]')
    def do_GET(self):
        path=urlparse(self.path).path
        if path.startswith('/api/') or path.startswith('/media/'):
            if not self.allowed():return self.json({'error':'Studio access token required, or request origin is not allowed.'},401)
        try:
            if path=='/api/state':
                f=DATA/'workspace.json';return self.json(json.loads(f.read_text()) if f.exists() else {})
            if path=='/api/health':return self.json({'ok':True,'hermes':(HERMES/'venv/bin/python').exists()})
            if path.startswith('/api/jobs/'):
                with LOCK: result=JOBS.get(path.rsplit('/',1)[1],{'status':'error','error':'Job expired or server restarted'})
                return self.json(result)
            if path.startswith('/media/'):
                p=safe_media(path);raw=p.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(p)[0]);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','private, max-age=3600');self.end_headers();return self.wfile.write(raw)
            if path.startswith('/api/'):return self.json({'error':'Not found'},404)
            return super().do_GET()
        except Exception as e:return self.json({'error':str(e)},400)
    def do_POST(self):
        if not self.allowed():return self.json({'error':'Studio access token required, or request origin is not allowed.'},401)
        try:
            length=int(self.headers.get('Content-Length',0))
            if not 0<length<=30_000_000:raise ValueError('Request must be under 30 MB')
            d=json.loads(self.rfile.read(length));path=urlparse(self.path).path
            if path=='/api/state':
                if len(json.dumps(d))>3_000_000:raise ValueError('Workspace is too large')
                atomic(DATA/'workspace.json',d);return self.json({'saved':True})
            if path=='/api/upload':
                raw=base64.b64decode(d['data'],validate=True)
                if len(raw)>20_000_000:raise ValueError('Files must be under 20 MB')
                name=str(d.get('name','Upload'))[:180];ext=Path(name).suffix.lower()
                if ext in ('.txt','.md'):
                    return self.json({'name':name,'text':raw.decode('utf-8')[:60000]})
                if ext=='.pdf':
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.pdf',dir=DATA) as f:
                        f.write(raw);f.flush()
                        r=subprocess.run(['pdftotext','-layout',f.name,'-'],capture_output=True,text=True,timeout=25)
                    if r.returncode:raise ValueError('PDF text extraction failed; upload a text version.')
                    if not r.stdout.strip():raise ValueError('This PDF has no extractable text. Upload a text version.')
                    return self.json({'name':name,'text':r.stdout[:60000]})
                ext=sniff(raw);filename=uuid.uuid4().hex+ext;(DATA/'media'/filename).write_bytes(raw)
                return self.json({'name':name,'url':'/media/'+filename})
            if path=='/api/jobs':return self.json(submit(d),202)
            return self.json({'error':'Not found'},404)
        except Exception as e:return self.json({'error':str(e)},400)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--host',default='127.0.0.1');parser.add_argument('--port',type=int,default=8787);args=parser.parse_args()
    if args.host not in ('localhost','127.0.0.1','::1') and len(TOKEN)<24:parser.error('LAN mode requires STUDIO_TOKEN of at least 24 characters')
    init();print(f'Stillroom Studio: http://{args.host}:{args.port}',flush=True)
    ThreadingHTTPServer((args.host,args.port),Handler).serve_forever()
