"""Loopback-only local server. Run: python3 agent/main.py."""
import json
import os
import secrets
import sys
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from vault import ROOT, workspace
import data
import tools
import memory
import computer
import voice
sys.path.insert(0,str(ROOT/'data'))
from generator import generate
TOKEN=secrets.token_urlsafe(32)
LOCK=threading.Lock()
GRAPH=None

class Handler(BaseHTTPRequestHandler):
    server_version='JarvisLocal/1.0'
    def log_message(self,*args):
        pass  # Avoid logging user text, file paths or credentials.
    def send(self,status,payload,content_type='application/json'):
        body=json.dumps(payload,ensure_ascii=False).encode() if content_type=='application/json' else payload
        try:
            self.send_response(status)
            self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; media-src 'self' blob:; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Browser cancelled/reloaded the request; do not attempt another response.
            self.close_connection = True

    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            self.close_connection = True

    def valid_host(self):
        return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}')
    def do_GET(self):
        if not self.valid_host():
            return self.send(403,{'error':'Invalid host.'})
        path=urlparse(self.path).path
        if path=='/api/status':
            return self.send(200,{'token':TOKEN,'mode':'demo' if os.environ.get('JARVIS_DEMO','1')=='1' else 'real','name':'Shaheem','ai':bool(os.environ.get('JARVIS_AI_URL') and os.environ.get('JARVIS_AI_MODEL')),'voice_config':voice.status(),'voice':bool(os.environ.get('ELEVENLABS_API_KEY') not in ('',None,'PASTE_YOUR_ELEVENLABS_API_KEY_HERE')),'computer':os.environ.get('JARVIS_ENABLE_COMPUTER','0')=='1','indexed':GRAPH is not None,'ui_mode':os.environ.get('JARVIS_UI_MODE','pc'),'os':__import__('platform').system()})
        if path.startswith('/api/'):
            return self.send(404,{'error':'Unknown endpoint.'})
        files={'/':'index.html','/app.js':'app.js','/graph.js':'graph.js','/styles.css':'styles.css'}
        if path not in files:
            return self.send(404,{'error':'Not found.'})
        name=files[path]
        content_types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}
        return self.send(200,(ROOT/'ui'/name).read_bytes(),content_types[Path(name).suffix])
    def do_POST(self):
        global GRAPH
        origin=self.headers.get('Origin')
        expected={f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}
        if not self.valid_host() or (origin and origin not in expected) or not secrets.compare_digest(self.headers.get('X-Jarvis-Token',''),TOKEN):
            return self.send(403,{'error':'Unauthorized local request.'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=8_000_000:
                raise ValueError('Invalid request size.')
            raw=self.rfile.read(length)
            path=urlparse(self.path).path
            if path=='/api/listen':
                output=voice.listen(raw,self.headers.get('Content-Type',''),self.headers.get('X-Language','auto'))
                return self.send(200,output)
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':
                raise ValueError('Expected JSON.')
            obj=json.loads(raw)
            if not isinstance(obj,dict):
                raise ValueError('Expected a JSON object.')
            if path=='/api/speak':
                return self.send(200,voice.speak(obj.get('text',''),obj.get('language','en')),'audio/mpeg')
            with LOCK:
                if path=='/api/index':
                    GRAPH=data.index()
                    output=GRAPH
                elif path=='/api/chat':
                    text=obj.get('text','')
                    session=obj.get('session','default')
                    if not isinstance(text,str) or not 0<len(text.strip())<=8000 or not isinstance(session,str) or len(session)>100:
                        raise ValueError('Invalid conversation request.')
                    output=tools.chat(text,session,obj.get('language','en'))
                elif path=='/api/tool':
                    name=obj.get('name')
                    args=obj.get('args',{})
                    if not isinstance(args,dict):
                        raise ValueError('Invalid tool arguments.')
                    functions={'search_brain':tools.search_brain,'read_files':tools.read_files,'research_web':tools.research_web,'computer_control':tools.computer_control,'remember':tools.remember,'brief_me':tools.brief_me,'plan_day':tools.plan_day,'write_file':tools.write_file}
                    if name not in functions:
                        raise ValueError('Unknown tool.')
                    output=functions[name](**args)
                elif path=='/api/edit-preview':
                    output=tools.write_preview(obj.get('path',''))
                elif path=='/api/memory':
                    output=tools.result('These are your saved memories.','Memory',memory.listing())
                elif path=='/api/forget':
                    if obj.get('confirm') is not True:
                        raise ValueError('Explicit confirmation is required to forget memory.')
                    output=tools.result('Memory deleted.','Memory change',memory.forget(obj.get('id','')))
                elif path=='/api/apps':
                    output=tools.result('Discovered launchable applications; integrations vary.','Applications',list(computer.discover()))
                else:
                    return self.send(404,{'error':'Unknown endpoint.'})
            self.send(200,output)
        except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as exc:
            self.send(400,{'error':str(exc)[:500]})
        except Exception:
            self.send(500,{'error':'Unexpected server error. No success has been claimed.'})

def serve(open_browser=False):
    global GRAPH
    if os.environ.get('JARVIS_DEMO','1')=='1':
        generate(ROOT/'data/demo')
        GRAPH=data.index()
        print(f'Demo index: {len(GRAPH["nodes"])} files; types: {GRAPH["counts"]}',flush=True)
    port=int(os.environ.get('JARVIS_PORT','8720'))
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print(f'JARVIS local server on port {port}. Real files are indexed only on request.',flush=True)
    if open_browser:
        import webbrowser
        threading.Thread(target=lambda:webbrowser.open(f'http://127.0.0.1:{port}/'),daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    serve()
