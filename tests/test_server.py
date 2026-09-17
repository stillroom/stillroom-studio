import base64, importlib.util, json, os, tempfile, threading, unittest, urllib.request, urllib.error
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('server',Path(__file__).parents[1]/'studio/server.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==')
class ServerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();s.DATA=Path(cls.temp.name);s.init();s.TOKEN='';cls.server=s.ThreadingHTTPServer(('127.0.0.1',0),s.Handler);cls.url='http://127.0.0.1:'+str(cls.server.server_port);threading.Thread(target=cls.server.serve_forever,daemon=True).start()
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.temp.cleanup()
 def req(self,path,data=None,headers=None):
  r=urllib.request.Request(self.url+path,json.dumps(data).encode() if data is not None else None,{'Content-Type':'application/json',**(headers or {})})
  with urllib.request.urlopen(r) as f:return json.load(f)
 def test_workspace_roundtrip(self):
  self.req('/api/state',{'brand':{'name':'Stillroom'},'saved':[{'id':'a'}]});self.assertEqual(self.req('/api/state')['saved'][0]['id'],'a')
 def test_upload_and_confinement(self):
  r=self.req('/api/upload',{'name':'test.png','data':base64.b64encode(PNG).decode()});self.assertEqual(s.safe_media(r['url']).read_bytes(),PNG)
  with self.assertRaises(ValueError):s.safe_media('/media/../../studio/hermes_bridge.py')
  with self.assertRaises(ValueError):s.safe_media('file:///etc/passwd')
 def test_text_upload(self):
  r=self.req('/api/upload',{'name':'source.md','data':base64.b64encode(b'True product facts').decode()});self.assertEqual(r['text'],'True product facts')
 def test_invalid_image(self):
  with self.assertRaises(urllib.error.HTTPError) as e:self.req('/api/upload',{'name':'bad.png','data':base64.b64encode(b'<script>').decode()})
  self.assertEqual(e.exception.code,400)
 def test_cross_origin_blocked(self):
  with self.assertRaises(urllib.error.HTTPError) as e:self.req('/api/state',{}, {'Origin':'https://attacker.example'})
  self.assertEqual(e.exception.code,401)
 def test_token_required(self):
  with patch.object(s,'TOKEN','secret-token'):
   with self.assertRaises(urllib.error.HTTPError):self.req('/api/state')
   self.assertIsInstance(self.req('/api/state',headers={'Authorization':'Bearer secret-token'}),dict)
 def test_failed_job_surfaces_error(self):
  with patch.object(s,'bridge',side_effect=RuntimeError('Provider unavailable')):
   s.task('test',{'op':'copy'});self.assertEqual(s.JOBS['test']['status'],'error');self.assertIn('Provider unavailable',s.JOBS['test']['error'])
 def test_generated_image_saved(self):
  with patch.object(s,'bridge',return_value={'data':base64.b64encode(PNG).decode(),'model':'test'}):
   s.task('generation',{'op':'generate','references':[]});r=s.JOBS['generation'];self.assertEqual(r['status'],'complete');self.assertEqual(s.safe_media(r['result']['url']).read_bytes(),PNG)
 def test_unknown_operation(self):
  with self.assertRaises(ValueError):s.submit({'op':'messages_send'})
if __name__=='__main__':unittest.main()
