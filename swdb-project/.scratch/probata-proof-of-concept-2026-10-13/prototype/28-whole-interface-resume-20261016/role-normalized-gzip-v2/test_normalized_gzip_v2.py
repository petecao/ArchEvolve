"""Synthetic stdlib gzip/streaming-inverse controls; no actual AST/root run."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import unittest
import zlib
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;EVENTS=[]
def audit(event,args):
    if event.startswith(('subprocess.','socket.','os.exec','os.spawn','os.posix_spawn','os.fork')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise AssertionError('no children/network/native '+event)
sys.addaudithook(audit)
FIX=runpy.run_path(str(WHOLE/'compiler-duplicate-census-v3/test_complete_census_v3.py'),run_name='synthetic_helpers_only')
S={'__name__':'inert_gzip_transport'};exec(compile((HERE/'role_normalized_gzip_v2.py').read_bytes(),'inert_gzip_transport','exec'),S)
CODEC={'__name__':'inert_codec'};exec(compile((WHOLE/'streaming-minify-v1/lossless_gzip_v2.py').read_bytes(),'inert_codec','exec'),CODEC)
def produce(raw,chunk=65536):
    out=io.BytesIO();manifest=io.BytesIO();receipt=S['compress_normalize'](FIX['Source'](raw,chunk),out,manifest,FIX['B'],CODEC,zlib,lambda:None)
    return out.getvalue(),manifest.getvalue(),receipt
class Controls(unittest.TestCase):
    def test_both_roles_values_and_complete_streaming_inverse(self):
        raw=FIX['tu']([FIX['node'](),FIX['node']('TypedefType'),FIX['node'](target={'qualType':'Alias'})])
        compressed,manifest,transport=produce(raw);normalized=zlib.decompress(compressed,wbits=31)
        self.assertIn(b'"swdbClangDesugaredType"',normalized);self.assertIn(b'"type":{"qualType":"Alias"}',normalized)
        inverse=S['verify_inverse_gzip'](zlib,io.BytesIO(compressed),manifest,transport,CODEC,lambda:None)
        self.assertTrue(inverse['complete_normalized_gzip_identity_verified'])
        self.assertEqual(inverse['inverse']['original_minified_token_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertFalse(transport['normalized_uncompressed_file_written']);self.assertFalse(inverse['source_ABI_or_public_admission'])
    def test_all_short_input_and_compressed_chunk_boundaries(self):
        raw=FIX['tu']([FIX['node'](),FIX['node']('TypedefType')]);baseline=produce(raw)
        for chunk in range(1,18):
            self.assertEqual(produce(raw,chunk),baseline)
            S['verify_inverse_gzip'](zlib,FIX['Source'](baseline[0],chunk),baseline[1],baseline[2],CODEC,lambda:None)
    def test_corrupt_truncated_trailing_member_and_wrong_codec_identity_refuse(self):
        compressed,manifest,transport=produce(FIX['tu']([FIX['node']()]))
        for broken in (compressed[:-1],compressed+b'x',compressed+compressed,compressed[:20]+bytes([compressed[20]^1])+compressed[21:]):
            with self.assertRaises(ValueError):S['verify_inverse_gzip'](zlib,io.BytesIO(broken),manifest,transport,CODEC,lambda:None)
        wrong=copy.deepcopy(transport);wrong['normalized_gzip_codec']['expanded_sha256']='0'*64
        with self.assertRaises(S['Refused']):S['verify_inverse_gzip'](zlib,io.BytesIO(compressed),manifest,wrong,CODEC,lambda:None)
    def test_unknown_reserved_collision_and_malformed_suffix_return_no_transport(self):
        for node in (FIX['node']('Unknown'),FIX['node']()+[('swdbClangDesugaredType',b'1')],FIX['node']()+[('type',b'{}')]):
            with self.assertRaises(S['Refused']):produce(FIX['tu']([node]))
        with self.assertRaises(ValueError):produce(FIX['tu']([FIX['node']()])+b'{}')
    def test_manifest_and_normalized_identity_mutations_refuse(self):
        compressed,manifest,transport=produce(FIX['tu']([FIX['node']()]))
        with self.assertRaises(S['Refused']):S['verify_inverse_gzip'](zlib,io.BytesIO(compressed),manifest+b' ',transport,CODEC,lambda:None)
        changed=copy.deepcopy(transport);changed['normalization']['normalized_sha256']='0'*64
        with self.assertRaises(S['Refused']):S['verify_inverse_gzip'](zlib,io.BytesIO(compressed),manifest,changed,CODEC,lambda:None)
        changed=copy.deepcopy(transport);changed['normalization']['original_minified_token_sha256']='0'*64
        with self.assertRaises(S['Refused']):S['verify_inverse_gzip'](zlib,io.BytesIO(compressed),manifest,changed,CODEC,lambda:None)
    def test_expanded_192MiB_is_separate_from_physical_128MiB(self):
        self.assertEqual((S['EXPANDED_LIMIT'],S['COMPRESSED_LIMIT']),(201326592,134217728))
        self.assertLess(134217728,178924116);self.assertLess(178924116,S['EXPANDED_LIMIT'])
        # Exercise the actual nested producer gate with one byte at each limit;
        # no full-size allocation/write or duplicated implementation logic.
        tree=ast.parse((HERE/'role_normalized_gzip_v2.py').read_bytes());normal=next(n for n in tree.body if getattr(n,'name',None)=='normalize')
        gate=next(n for n in normal.body if getattr(n,'name',None)=='write_output')
        outer=ast.parse('def control(start,sink):\n output_bytes=start\n def placeholder():pass\n return write_output\n').body[0]
        outer.body[1]=gate;ns={'need':S['need'],'check':lambda:None};exec(compile(ast.fix_missing_locations(ast.Module([outer],type_ignores=[])),'projected-expanded-gate','exec'),ns)
        sink=io.BytesIO();ns['control'](134217728,sink)(b'x');self.assertEqual(sink.getvalue(),b'x')
        sink=io.BytesIO()
        with self.assertRaises(S['Refused']):ns['control'](201326592,sink)(b'x')
        self.assertEqual(sink.getvalue(),b'')
    def test_exact_role_AST_preserved_and_no_child(self):
        a=ast.parse((HERE/'role_normalized_gzip_v2.py').read_bytes());b=ast.parse((WHOLE/'role-normalization-v1/role_normalizer_v1.py').read_bytes())
        get=lambda tree:next(n for n in tree.body if getattr(n,'name',None)=='role')
        self.assertEqual(ast.dump(get(a),include_attributes=False),ast.dump(get(b),include_attributes=False));self.assertEqual(EVENTS,[])
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'child_events':EVENTS,
        'source_sha256':hashlib.sha256((HERE/'role_normalized_gzip_v2.py').read_bytes()).hexdigest(),
        'scope':'local synthetic stdlib compression/inverse only; no actual TU/root/compiler/normalization admission'}))
    raise SystemExit(not result.wasSuccessful())
