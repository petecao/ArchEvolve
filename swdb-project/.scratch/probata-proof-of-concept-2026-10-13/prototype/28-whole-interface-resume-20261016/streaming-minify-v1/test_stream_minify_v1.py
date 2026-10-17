"""Synthetic stdlib controls only; no project, compiler, child or capture main."""
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
        EVENTS.append(event);raise RuntimeError('no-child control: '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent
M={'__name__':'pure_minifier'};exec(compile((HERE/'strict_minify_v1.py').read_bytes(),'strict_minify_v1.py','exec'),M)
C={'__name__':'pure_codec'};exec(compile((HERE/'lossless_gzip_v2.py').read_bytes(),'lossless_gzip_v2.py','exec'),C)
class Chunks(io.BytesIO):
    def __init__(self,value,size):super().__init__(value);self.size=size
    def read(self,size=-1):return super().read(min(self.size,size))
def minified(raw,size=65536,**limits):
    out=io.BytesIO();receipt=M['minify'](Chunks(raw,size),out,raw_limit=limits.get('raw_limit',2147483648),retained_limit=limits.get('retained',134217728),check=lambda:None)
    return out.getvalue(),receipt
def captured(raw):
    out=io.BytesIO();c=C['Capture'](zlib,out,expanded_limit=2147483648,compressed_limit=134217728,check=lambda:None)
    for i in range(0,len(raw),65536):c.feed(raw[i:i+65536])
    receipt=c.finish();return out.getvalue(),receipt
def decoder(data,receipt,size=65536):return C['DecodeReader'](zlib,Chunks(data,size),receipt,expanded_limit=2147483648,compressed_limit=134217728,check=lambda:None)
class Controls(unittest.TestCase):
    def test_original_identity(self):
        raw=b' { "kind" : "TranslationUnitDecl", "inner" : [ {"id":"0x1","kind":"FunctionDecl","inner": []} ], "n":-1.2300e+12 } \n'
        target=b'{"kind":"TranslationUnitDecl","inner":[{"id":"0x1","kind":"FunctionDecl","inner":[]}],"n":-1.2300e+12}'
        for size in (1,2,3,7,31,65536):
            data,r=minified(raw,size);self.assertEqual(data,target);self.assertEqual(json.loads(data),json.loads(raw));self.assertEqual(r['raw_bytes'],len(raw));self.assertEqual(r['raw_sha256'],hashlib.sha256(raw).hexdigest());self.assertFalse(r['AST_nodes_elided'])
    def test_bad_keyword_number_boundaries(self):
        bad=(b'tr ue',b'fa lse',b'n ull',b'1 .0',b'- 1',b'1e +2',b'1e+ 2',b'0 1',b'01',b'+1',b'.1',b'1.',b'1e',b'--1',b'NaN',b'Infinity',b'{"a":tr ue}',b'[1 .0]',b'[- 1]')
        for value in bad:
            for size in range(1,9):
                with self.subTest(raw=value,size=size),self.assertRaises(M['Refused']):minified(value,size)
    def test_strings_escape_utf8_unicode(self):
        raw=' { "é" : "a \\"/é汉🦊", "x" : "\\u00e9\\/\\uD83E\\uDD8A", "\\uD800" : 0 } '.encode()
        for size in range(1,18):
            data,r=minified(raw,size);self.assertEqual(json.loads(data),json.loads(raw));self.assertIn(b'\\u00e9',data);self.assertIn('汉'.encode(),data)
    def test_all_json_escapes(self):
        raw=b' {"x":"\\\"\\\\\\/\\b\\f\\n\\r\\t\\u0000"} '
        for size in range(1,11):self.assertEqual(minified(raw,size)[0],raw.strip())
    def test_duplicate_keys(self):
        for raw in (b'{"a":1,"a":2}',b'{"a":1,"\\u0061":2}',b'{"x":{"b":1,"b":2}}'):
            for size in (1,3,65536):
                with self.assertRaises(M['Refused']):minified(raw,size)
    def test_truncation_and_trailing(self):
        raw=b'{"x":[true,false,null,-1.25e+9,"a\\\"b"]}'
        for i in range(len(raw)):
            with self.assertRaises(M['Refused']):minified(raw[:i],3)
        for tail in (b'{}',b'null',b'garbage',b'\x00',b'//x'):
            with self.assertRaises(M['Refused']):minified(raw+tail,1)
    def test_malformed_structure(self):
        for raw in (b'{,}',b'{"a" 1}',b'{"a":}',b'{"a":1,}',b'[1,]',b'[,1]',b'[1 2]',b'{"a":1 "b":2}',b'{1:2}',b'\xef\xbb\xbf{}'):
            with self.assertRaises(M['Refused']):minified(raw,2)
    def test_invalid_strings(self):
        for raw in (b'"\xff"',b'"\xc3"',b'"\xed\xa0\x80"',b'"\\x00"',b'"\\u00xz"',b'"\n"',b'"\\"',b'"abc'):
            with self.assertRaises(M['Refused']):minified(raw,1)
    def test_bounds(self):
        with self.assertRaises(M['Refused']):minified(b' [0] ',raw_limit=3)
        with self.assertRaises(M['Refused']):minified(b' [0] ',retained=2)
        for raw in (b'['*258+b'0'+b']'*258,b'{'+b','.join(b'"k%d":0'%i for i in range(1025))+b'}',b'1'*129,b'"'+b'a'*1048577+b'"'):
            with self.assertRaises(M['Refused']):minified(raw)
    def test_whitespace_bulk(self):
        raw=b' '*200000+b'{"x": [0, 1, 2] }\r\n';data,r=minified(raw);self.assertEqual(data,b'{"x":[0,1,2]}');self.assertEqual(r['raw_bytes'],len(raw))
    def test_checked_callbacks(self):
        class Stop(Exception):pass
        def stop():raise Stop()
        with self.assertRaises(Stop):M['minify'](io.BytesIO(b'{}'),io.BytesIO(),raw_limit=10,retained_limit=10,check=stop)
    def test_single_member_bounded_decode(self):
        raw=(b' '*200000+b'{"x":[0,1,2]}');data,r=captured(raw)
        for size in (1,3,65536):
            source=decoder(data,r,size);out,receipt=minified_reader(source);self.assertEqual(out,b'{"x":[0,1,2]}');self.assertTrue(source.verified);self.assertEqual(receipt['raw_sha256'],r['expanded_sha256'])
    def test_gzip_trailing_members(self):
        data,r=captured(b'{}')
        for bad in (data+b'x',data+data,data[:-1],data[:-8],b'bad',data[:-5]+bytes([data[-5]^1])+data[-4:]):
            with self.assertRaises(C['Refused']):minified_reader(decoder(bad,r,1))
    def test_gzip_receipt_mutation(self):
        data,r=captured(b'{"x":0}')
        for field,value in (('expanded_sha256','0'*64),('compressed_sha256','0'*64),('expanded_bytes',1),('compressed_bytes',1),('expanded_limit',512),('codec','other')):
            bad=dict(r);bad[field]=value
            with self.assertRaises(C['Refused']):minified_reader(decoder(data,bad))
    def test_complete_raw_not_dom(self):
        # A larger whitespace stream exercises bounded reads and token output;
        # it is a synthetic shape, not evidence of actual AST time/RSS.
        raw=b' '*2097152+b'{"inner":[]}';data,r=captured(raw);source=decoder(data,r,17)
        out,receipt=minified_reader(source);self.assertEqual(out,b'{"inner":[]}');self.assertEqual(receipt['raw_bytes'],len(raw));self.assertTrue(source.verified)
    def test_short_writes(self):
        class Short(io.BytesIO):
            def write(self,value):return max(0,len(value)-1)
        with self.assertRaises(M['Refused']):M['minify'](io.BytesIO(b'{}'),Short(),raw_limit=10,retained_limit=10,check=lambda:None)
    def test_decoder_read_limits(self):
        data,r=captured(b'{}');source=decoder(data,r)
        for count in (-1,0,65537,True):
            with self.assertRaises(C['Refused']):source.read(count)
    def test_capture_inverse(self):
        old=(HERE.parent/'lossless-capture-v1/lossless_gzip_v1.py').read_text();new=(HERE/'lossless_gzip_v2.py').read_text()
        self.assertEqual(new[:new.index('\nclass DecodeReader:')].replace('MAX_EXPANDED=2147483648','MAX_EXPANDED=536870912'),old[:old.index('\ndef decode(')])
    def test_no_child(self):self.assertEqual(EVENTS,[])
def minified_reader(source):
    out=io.BytesIO();r=M['minify'](source,out,raw_limit=2147483648,retained_limit=134217728,check=lambda:None);return out.getvalue(),r
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls);result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'child_events':EVENTS,'scope':'synthetic stdlib source controls; no actual TU/capture/native/proof'}))
    sys.exit(not result.wasSuccessful())
