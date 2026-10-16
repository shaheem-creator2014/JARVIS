import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from urllib.request import Request, urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'agent'))
import vault, data, memory, tools, computer, voice, main, model

# Tests must not use a user's real folders, credentials or paid providers.
_TEST_ENV = patch.dict(os.environ, {'JARVIS_DEMO':'1', 'JARVIS_AI_URL':'',
    'JARVIS_AI_MODEL':'', 'JARVIS_AI_KEY':'', 'ELEVENLABS_API_KEY':'',
    'ELEVENLABS_VOICE_ID':'', 'JARVIS_ALLOW_PAID_API':'0',
    'JARVIS_ENABLE_COMPUTER':'0', 'JARVIS_ENABLE_WRITE':'0'})

def setUpModule():
    _TEST_ENV.start()
    main.generate(vault.ROOT/'data/demo')

def tearDownModule():
    _TEST_ENV.stop()

class BackendTests(unittest.TestCase):
    def test_index_and_search(self):
        g=data.index()
        self.assertEqual(len(g['nodes']),65)
        self.assertEqual(g['counts']['md'],25)
        self.assertTrue(g['edges'])
        self.assertTrue(any('fractions' in r['path'] for r in data.search('denominator')))
        self.assertIn('1/2',data.read('studies/fractions.md'))
        self.assertEqual(tools.read_files(['studies/fractions.md'])['card']['details'][0]['path'],'studies/fractions.md')
    def test_pdf_extraction(self):
        import shutil
        if not shutil.which('pdftotext'):
            self.skipTest('Optional pdftotext is unavailable')
        content=b'BT /F1 12 Tf 50 750 Td (Sample robotics PDF) Tj ET'
        objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',b'<< /Length '+str(len(content)).encode()+b' >>\nstream\n'+content+b'\nendstream']
        raw=b'%PDF-1.4\n';offsets=[0]
        for i,obj in enumerate(objects,1):
            offsets.append(len(raw));raw+=str(i).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
        xref=len(raw);raw+=b'xref\n0 6\n0000000000 65535 f \n'
        for offset in offsets[1:]:raw+=f'{offset:010d} 00000 n \n'.encode()
        raw+=f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'sample.pdf').write_bytes(raw)
            with patch.object(vault,'workspace',return_value=root):
                self.assertIn('Sample robotics PDF',data.read('sample.pdf'))

    def test_demo_repeatability_and_preservation(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            main.generate(Path(a));main.generate(Path(b))
            actual={p.relative_to(a).as_posix():p.read_bytes() for p in Path(a).rglob('*') if p.is_file()}
            other={p.relative_to(b).as_posix():p.read_bytes() for p in Path(b).rglob('*') if p.is_file()}
            self.assertEqual(actual,other)
            self.assertEqual(len(actual),65)
            kept=Path(a)/'studies/fractions.md';kept.write_text('User edit')
            main.generate(Path(a));self.assertEqual(kept.read_text(),'User edit')

    def test_confinement(self):
        for path in ['../.env','/etc/passwd','.env','a/../../.env','.git/config']:
            with self.assertRaises(ValueError): vault.safe_path(path)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'escape').symlink_to('/etc/passwd')
            with self.assertRaises(ValueError):vault.safe_path('escape',root)
    def test_demo_ignores_personal_folder(self):
        with patch.dict(os.environ,{'JARVIS_DEMO':'1','JARVIS_WORKSPACE':'/etc'}):
            self.assertEqual(vault.workspace(),vault.ROOT/'data/demo')
    def test_memory_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(memory,'DIRECTORY',Path(tmp)):
            saved=tools.remember('I prefer step-by-step explanations.')
            identifier=saved['card']['details']['id']
            self.assertIn('Memory saved',saved['spoken'])
            memory.remember('I prefer diagrams.',identifier)
            self.assertEqual(len(memory.listing()),1)
            self.assertIn('diagrams',memory.listing()[0]['text'])
            self.assertTrue(memory.forget(identifier)['verified'])
            self.assertEqual(memory.listing(),[])
            with self.assertRaises(ValueError):memory.remember('My API key is abc')
            with self.assertRaises(ValueError):memory.forget('../anything')
    def test_tools_and_restrictions(self):
        self.assertEqual(len(tools.plan_day()['card']['details']['items']),5)
        self.assertEqual(tools.brief_me()['card']['details']['integrations'],[])
        with self.assertRaises(ValueError):tools.plan_day(['a']*6)
        with self.assertRaises(ValueError):computer.control('app','Chrome')
        self.assertIsInstance(computer.discover(),dict)
        self.assertTrue(tools.chat('Hello','test')['fallback'])
        self.assertIn('configured',tools.chat('Hello','test')['spoken'])
    def test_confirmed_file_edit_and_stale_guard(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as local:
            root=Path(tmp);(root/'project.py').write_text('print("old")')
            with patch.dict(os.environ,{'JARVIS_DEMO':'0','JARVIS_WORKSPACE':tmp,'JARVIS_ENABLE_WRITE':'1'}),patch.object(tools,'ROOT',Path(local)):
                snapshot=tools.write_preview('project.py')
                with self.assertRaises(ValueError):tools.write_file('project.py','print("new")',snapshot['sha256'])
                updated=tools.write_file('project.py','print("new")',snapshot['sha256'],True)
                self.assertTrue(updated['card']['details']['verified'])
                self.assertEqual((root/'project.py').read_text(),'print("new")')
                backup=Path(local)/updated['card']['details']['backup']
                self.assertEqual(backup.read_text(),'print("old")')
                with self.assertRaises(ValueError):tools.write_file('project.py','print("oops")',snapshot['sha256'],True)
                with self.assertRaises(ValueError):tools.write_preview('../outside.py')

    def test_research_results(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,*a):return json.dumps({'query':{'search':[{'title':'Arduino','snippet':'A <b>board</b>','pageid':123}]}}).encode()
        with patch.object(tools,'urlopen',return_value=Response()):
            r=tools.research_web('Arduino')['card']['details'][0]
            self.assertEqual(r['excerpt'],'A board')
            self.assertEqual(r['url'],'https://en.wikipedia.org/?curid=123')
    def test_approved_syntax_check_does_not_execute(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'safe.py').write_text('raise RuntimeError("must never execute")')
            (root/'broken.py').write_text('def broken(:')
            with patch.dict(os.environ,{'JARVIS_DEMO':'0','JARVIS_ENABLE_COMPUTER':'1','JARVIS_WORKSPACE':tmp}):
                self.assertTrue(computer.control('check_python','safe.py')['verified'])
                with self.assertRaises(ValueError):computer.control('check_python','broken.py')
            self.assertFalse((root/'__pycache__').exists())
    def test_voice_validation_and_contract(self):
        with self.assertRaises(ValueError):voice.configuration()
        with patch.dict(os.environ,{'ELEVENLABS_API_KEY':'test-only','JARVIS_ALLOW_PAID_API':'1','ELEVENLABS_VOICE_ID':'testvoice'}):
            with patch.object(voice,'request',return_value=b'{"text":"hello","language_code":"eng","language_probability":0.99}') as req:
                self.assertEqual(voice.listen(b'audio','audio/webm','auto')['text'],'hello')
                self.assertIn(b'scribe_v1',req.call_args.args[1])
                self.assertNotIn(b'test-only',req.call_args.args[1])
            with patch.object(voice,'request',return_value=b'audio') as req:
                self.assertEqual(voice.speak('Hello','en'),b'audio')
                self.assertIn('text-to-speech/testvoice',req.call_args.args[0])
            with patch.object(voice,'request',return_value=b'{"text":"uncertain","language_code":"eng","language_probability":0.1}'):
                with self.assertRaises(ValueError):voice.listen(b'audio','audio/webm','auto')
    def test_ai_context(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,*a):return b'{"choices":[{"message":{"content":"Hello, Shaheem."}}]}'
        with patch.dict(os.environ,{'JARVIS_AI_URL':'http://localhost:9999/v1/chat/completions','JARVIS_AI_MODEL':'test'}),patch.object(model,'urlopen',return_value=Response()) as req:
            for i in range(12):tools.chat('Hello','context-test')
            self.assertEqual(len(tools.HISTORY['context-test']),20)
            payload=json.loads(req.call_args.args[0].data)
            self.assertTrue(any('Grade 8' in m['content'] for m in payload['messages']))

class ModelToolTests(unittest.TestCase):
    def test_tool_execution_and_source_evidence(self):
        replies=[{'choices':[{'message':{'role':'assistant','content':None,'tool_calls':[{'id':'1','type':'function','function':{'name':'search_brain','arguments':'{"query":"Arduino"}'}}]}}]}, {'choices':[{'message':{'content':'Found the demo robotics files.'}}]}]
        class Response:
            def __init__(self,payload):self.payload=payload
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,*a):return json.dumps(self.payload).encode()
        with patch.dict(os.environ,{'JARVIS_AI_URL':'http://localhost:9999/v1/chat/completions','JARVIS_AI_MODEL':'test'}),patch.object(model,'urlopen',side_effect=[Response(x) for x in replies]):
            response=tools.chat('Find Arduino files','tool-test')
            record=response['card']['details']['tools'][0]
            self.assertEqual(record['tool'],'search_brain')
            self.assertTrue(record['result']['card']['details'])
            self.assertNotIn('computer_control',json.dumps(record))
    def test_auto_memory_disclosure_and_deduplication(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(memory,'DIRECTORY',Path(tmp)):
            response=tools.chat('I prefer visual explanations.','auto-test')
            self.assertIn('Memory saved: I prefer visual explanations.',response['spoken'])
            tools.chat('I prefer visual explanations.','auto-test')
            self.assertEqual(len(memory.listing()),1)
    def test_no_memory_saved_on_failed_ai(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(memory,'DIRECTORY',Path(tmp)),patch.dict(os.environ,{'JARVIS_AI_URL':'http://localhost:9999/v1/chat/completions','JARVIS_AI_MODEL':'test'}),patch.object(model,'urlopen',side_effect=ValueError()):
            with self.assertRaises(ValueError):tools.chat('I prefer diagrams.','failed')
            self.assertEqual(memory.listing(),[])

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=main.ThreadingHTTPServer(('127.0.0.1',0),main.Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close()
    def request(self,path,obj,token=True,origin=None):
        headers={'Content-Type':'application/json'}
        if token:headers['X-Jarvis-Token']=main.TOKEN
        if origin:headers['Origin']=origin
        return urlopen(Request(self.url+path,data=json.dumps(obj).encode(),headers=headers))
    def test_functional_requests(self):
        with self.request('/api/index',{}) as r:self.assertEqual(len(json.load(r)['nodes']),65)
        with self.request('/api/tool',{'name':'search_brain','args':{'query':'Arduino'}}) as r:self.assertTrue(json.load(r)['card']['details'])
        with self.request('/api/tool',{'name':'plan_day'}) as r:self.assertEqual(len(json.load(r)['card']['details']['items']),5)
        with self.request('/api/apps',{}) as r:self.assertIn('card',json.load(r))
    def test_access_security(self):
        for kwargs in ({'token':False},{'origin':'https://evil.example'}):
            with self.assertRaises(HTTPError) as e:self.request('/api/index',{},**kwargs)
            self.assertEqual(e.exception.code,403)
        for path in ['/.env','/agent/vault.py','/../.env']:
            with self.assertRaises(HTTPError):urlopen(self.url+path)
        with self.assertRaises(HTTPError):self.request('/api/tool',{'name':'shell','args':{'command':'whoami'}})
        with self.assertRaises(HTTPError):self.request('/api/forget',{'id':'x'})
    def test_browser_cancelled_response(self):
        for stage in ('end_headers','write'):
            for error in (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                handler=object.__new__(main.Handler)
                handler.send_response=Mock();handler.send_header=Mock();handler.end_headers=Mock();handler.wfile=Mock()
                target=handler.end_headers if stage=='end_headers' else handler.wfile.write
                target.side_effect=error('Browser disconnected')
                handler.send(200,{'ok':True})
                self.assertTrue(handler.close_connection)
                handler.send_response.assert_called_once_with(200)
    def test_disconnect_while_reading_request(self):
        handler=object.__new__(main.Handler)
        with patch.object(main.BaseHTTPRequestHandler,'handle',side_effect=ConnectionResetError()):
            handler.handle()
        self.assertTrue(handler.close_connection)

    def test_voice_configuration_has_no_key_values(self):
        with patch.dict(os.environ,{'ELEVENLABS_API_KEY':'not-a-real-key','ELEVENLABS_VOICE_ID':'testvoice','JARVIS_ALLOW_PAID_API':'1'}):
            with urlopen(self.url+'/api/status') as r:
                payload=json.load(r)
            self.assertTrue(payload['voice_config']['ready'])
            self.assertNotIn('not-a-real-key',json.dumps(payload))
        with patch.dict(os.environ,{'ELEVENLABS_API_KEY':'','ELEVENLABS_VOICE_ID':'','JARVIS_ALLOW_PAID_API':'0'}):
            config=voice.status()
            self.assertFalse(config['ready'])
            self.assertIn('ELEVENLABS_API_KEY',config['message'])
            self.assertIn('ELEVENLABS_VOICE_ID',config['message'])

    def test_static_does_not_expose_key(self):
        for path in ['/','/app.js','/graph.js','/api/status']:
            with urlopen(self.url+path) as r:
                self.assertNotIn(b'PASTE_YOUR_ELEVENLABS_API_KEY_HERE',r.read())

if __name__=='__main__':unittest.main()
