"""Synthetic duplicate metadata controls; no actual gzip/reader main invocation."""
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
import zlib
EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('pure duplicate controls '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;INGRESS=WHOLE/'streaming-minify-v1'
def load(path):
    ns={'__name__':'inert_duplicate_controls','__file__':str(path)};exec(compile(path.read_bytes(),str(path),'exec'),ns);return ns
D=load(HERE/'duplicate_metadata_v1.py');B=load(INGRESS/'strict_minify_v2.py');C=load(INGRESS/'lossless_gzip_v2.py')
class Source(io.BytesIO):
    def __init__(self,raw,chunk):super().__init__(raw);self.chunk=chunk
    def read(self,size):return super().read(min(size,self.chunk))
def find(raw,chunk=65536):return D['locate'](Source(raw,chunk),B,lambda:None)
def compressed(raw):
    out=io.BytesIO();capture=C['Capture'](zlib,out,expanded_limit=2147483648,compressed_limit=134217728,check=lambda:None)
    for at in range(0,len(raw),65536):capture.feed(raw[at:at+65536])
    receipt=capture.finish();return out.getvalue(),receipt
class Controls(unittest.TestCase):
    def test_duplicate_context_first_and_second_exact_offsets_and_tokens(self):
        raw=b'{"kind":"TranslationUnitDecl","inner":[{"kind":"FunctionDecl","id":"0x7","name":"f","loc":{"file":"/api.hpp","line":42},"x":true,"x":false}]}'
        r=find(raw);self.assertEqual(r['decoded_key'],'x');self.assertEqual(r['object_metadata']['kind'],'FunctionDecl');self.assertEqual(r['object_metadata']['name'],'f')
        self.assertEqual(r['object_metadata']['loc']['file'],'/api.hpp');self.assertEqual(r['object_metadata']['loc']['line']['ascii_token'],'42')
        self.assertEqual(r['first']['key_span'],[raw.index(b'"x"'),raw.index(b'"x"')+3]);second=raw.index(b'"x"',r['first']['key_span'][1]);self.assertEqual(r['second']['key_span'],[second,second+3])
        self.assertEqual(r['first']['value']['minified_sha256'],hashlib.sha256(b'true').hexdigest());self.assertEqual(r['second']['scalar_value']['minified_sha256'],hashlib.sha256(b'false').hexdigest())
        self.assertFalse(r['strict_JSON_accepted']);self.assertFalse(r['AST_repaired_or_projected'])
    def test_all_chunk_splits_preserve_first_duplicate(self):
        raw=' {"kind":"R", "é": "\\\"é", "\\u00e9": "汉"} '.encode()
        expected=find(raw)
        for chunk in range(1,18):self.assertEqual(find(raw,chunk),expected)
        self.assertEqual(expected['decoded_key'],'é');self.assertNotEqual(expected['first']['key_token']['sha256'],expected['second']['key_token']['sha256'])
    def test_first_nested_duplicate_wins(self):
        raw=b'{"kind":"Outer","inner":[{"kind":"Inner","x":1,"x":2}],"a":0,"a":1}'
        r=find(raw);self.assertEqual(r['decoded_key'],'x');self.assertEqual(r['object_metadata']['kind'],'Inner');self.assertEqual(r['ancestor_context'][-1]['field'],'inner[0]')
    def test_composite_second_value_stays_unaccepted_not_repaired(self):
        raw=b'{"kind":"R","x":{"a":1},"x":{"a":2}}';r=find(raw)
        self.assertEqual(r['second']['value_kind'],'object');self.assertNotIn('scalar_value',r['second']);self.assertFalse(r['strict_JSON_accepted'])
        self.assertEqual(r['first']['value']['minified_sha256'],hashlib.sha256(b'{"a":1}').hexdigest())
    def test_valid_no_duplicate_refuses_diagnostic_claim(self):
        for raw in (b'{}',b'{"x":1,"a":{"x":2}}',b'[{"x":1},{"x":2}]'):
            with self.assertRaisesRegex(D['Refused'],'expected first strict duplicate'):find(raw)
    def test_malformed_prefix_still_refuses_before_duplicate(self):
        for raw in (b'{"x":tr ue,"x":1}',b'{"x":1 .0,"x":1}',b'{"x":- 1,"x":1}',b'{"x":"\xff","x":1}',b'{"x":1,'):
            with self.assertRaises(ValueError):find(raw,1)
    def test_original_strict_parser_remains_unchanged_and_refuses(self):
        raw=b'{"x":1,"x":2}';report=find(raw)
        self.assertEqual(report['strict_refusal'],'duplicate compiler JSON key')
        with self.assertRaisesRegex(B['Refused'],'duplicate compiler JSON key'):B['minify'](io.BytesIO(raw),io.BytesIO(),raw_limit=2147483648,retained_limit=134217728,check=lambda:None)
    def test_gzip_after_duplicate_drains_and_verifies_entire_original(self):
        raw=b'{"x":1,"x":2,"tail":"'+b'a'*200000+b'"}';payload,receipt=compressed(raw)
        reader=C['DecodeReader'](zlib,Source(payload,3),receipt,expanded_limit=2147483648,compressed_limit=134217728,check=lambda:None)
        r=D['locate'](reader,B,lambda:None);self.assertEqual(r['decoded_key'],'x')
        while reader.read(65536):pass
        self.assertTrue(reader.verified);self.assertEqual(reader.raw_bytes,len(raw));self.assertEqual(reader.raw_hash.hexdigest(),hashlib.sha256(raw).hexdigest())
    def test_late_corruption_after_duplicate_still_refuses(self):
        raw=b'{"x":1,"x":2,"tail":"'+b'a'*200000+b'"}';payload,receipt=compressed(raw)
        bad=payload[:-8]+bytes([payload[-8]^1])+payload[-7:]
        reader=C['DecodeReader'](zlib,Source(bad,1),receipt,expanded_limit=2147483648,compressed_limit=134217728,check=lambda:None)
        D['locate'](reader,B,lambda:None)
        with self.assertRaises(C['Refused']):
            while reader.read(65536):pass
    def test_deadline_and_compact_context_bounds(self):
        class Stop(Exception):pass
        def stop():raise Stop()
        with self.assertRaises(Stop):D['locate'](io.BytesIO(b'{"x":1,"x":2}'),B,stop)
        r=find(b'{"kind":"'+b'a'*1000+b'","x":1,"x":2}');self.assertLessEqual(len(r['object_metadata']['kind']),128)
    def test_no_actual_reader_or_project_imports(self):
        self.assertEqual(EVENTS,[]);self.assertEqual(D['EVENTS'],[])
        source=(HERE/'duplicate_metadata_v1.py').read_text();self.assertNotIn('from swdb',source);self.assertNotIn('import swdb',source)
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'child_events':EVENTS+D['EVENTS'],
        'source_sha256':hashlib.sha256((HERE/'duplicate_metadata_v1.py').read_bytes()).hexdigest(),'scope':'synthetic prefix/decoded-key/context/gzip controls; no actual V10 reader or compiler'}))
    sys.exit(not result.wasSuccessful())
