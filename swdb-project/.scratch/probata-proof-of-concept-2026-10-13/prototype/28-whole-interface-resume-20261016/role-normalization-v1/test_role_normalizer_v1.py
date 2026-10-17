"""Synthetic normalization/inverse primitives only; no actual TU or main."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import unittest
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;EVENTS=[]
def audit(event,args):
    if event.startswith(('subprocess.','socket.','os.exec','os.spawn','os.posix_spawn','os.fork')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise AssertionError('no children/network/native '+event)
sys.addaudithook(audit)
FIX=runpy.run_path(str(WHOLE/'compiler-duplicate-census-v3/test_complete_census_v3.py'),run_name='inert_helpers_only')
S={'__name__':'inert_normalizer_primitives'};exec(compile((HERE/'role_normalizer_v1.py').read_bytes(),'role_normalizer_v1','exec'),S)
class Sink(io.BytesIO):
    def __init__(self):super().__init__();self.maximum_write=0
    def write(self,value):self.maximum_write=max(self.maximum_write,len(value));return super().write(value)
def normalize(raw,chunk=65536):
    out=Sink();manifest=Sink();receipt=S['normalize'](FIX['Source'](raw,chunk),out,manifest,FIX['B'],lambda:None)
    return out.getvalue(),manifest.getvalue(),receipt,out.maximum_write,manifest.maximum_write
def updated_manifest(raw,receipt):
    changed=dict(receipt,inverse_manifest_sha256=hashlib.sha256(raw).hexdigest(),inverse_manifest_bytes=len(raw));return changed
class Controls(unittest.TestCase):
    def test_both_roles_different_and_equal_views_keep_all_values_and_exact_inverse(self):
        nodes=[FIX['node'](),FIX['node']('TypedefType'),FIX['node'](target={'qualType':'Alias'})];raw=FIX['tu'](nodes)
        normalized,manifest,receipt,_,_=normalize(raw)
        expected=FIX['tu']([[('swdbClangDesugaredType' if k=='type' and i==len(n)-2 else k,v) for i,(k,v) in enumerate(n)] for n in nodes])
        self.assertEqual(normalized,expected);self.assertEqual(receipt['inverse_manifest_rows'],3)
        self.assertFalse(receipt['normalized_AST_admitted']);self.assertTrue(receipt['normalized_AST_written'])
        inverse=S['inverse_identity'](normalized,manifest,receipt)
        self.assertEqual(inverse['original_minified_token_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(receipt['original_minified_token_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertNotEqual(receipt['normalized_sha256'],receipt['original_minified_token_sha256'])
        parsed=json.loads(normalized);self.assertEqual(parsed['inner'][0]['type']['qualType'],'Alias')
        self.assertEqual(parsed['inner'][0]['swdbClangDesugaredType']['qualType'],'unsigned long')
    def test_chunk_boundaries_and_original_whitespace_do_not_change_normalized_tokens(self):
        raw=FIX['tu']([FIX['node'](),FIX['node']('TypedefType')]);baseline=normalize(raw)
        for chunk in range(1,18):
            actual=normalize(raw,chunk);self.assertEqual(actual[:3],baseline[:3])
        spaced=b' \n'+raw.replace(b',',b', \n')+b'\n';out,manifest,receipt,_,_=normalize(spaced,3)
        self.assertEqual(out,baseline[0]);self.assertNotEqual(manifest,baseline[1])
        self.assertEqual(S['inverse_identity'](out,manifest,receipt)['original_minified_token_sha256'],hashlib.sha256(raw).hexdigest())
    def test_every_unknown_shape_or_collision_refuses_returning_a_receipt(self):
        cases=[FIX['node']('Unknown'),FIX['node']()+[('swdbClangDesugaredType',b'1')],FIX['node']()+[('type',b'{}')],
            FIX['node'](flags=[('isDependent',False)]),FIX['node'](decl={'id':'0x2','kind':'Other','name':'A'})]
        for node in cases:
            receipt=None
            with self.assertRaises(S['Refused']):receipt=normalize(FIX['tu']([node]))
            self.assertIsNone(receipt)
        with self.assertRaises(S['Refused']):normalize(FIX['tu']([[('kind',b'"Other"'),('swdbClangDesugaredType',b'{}')]]))
    def test_complete_census_observations_remain_identical_on_valid_input(self):
        raw=FIX['tu']([FIX['node'](),FIX['node']('TypedefType')]);baseline=FIX['census'](raw)
        _,_,actual,_,_=normalize(raw)
        for key,value in baseline.items():
            if key not in {'schema','normalized_AST_retained_or_admitted'}:self.assertEqual(actual[key],value,key)
    def test_inverse_mutations_and_changed_normalized_bytes_refuse(self):
        normalized,manifest,receipt,_,_=normalize(FIX['tu']([FIX['node'](),FIX['node']('TypedefType')]))
        rows=[json.loads(line) for line in manifest.splitlines()]
        for mutation in ('missing','role','id','span','overlap','source-span'):
            changed=copy.deepcopy(rows)
            if mutation=='missing':changed.pop()
            elif mutation=='role':changed[0]['role']='unknown'
            elif mutation=='id':changed[0]['node_id']='invalid'
            elif mutation=='span':changed[0]['normalized_key_span'][0]+=1
            elif mutation=='overlap':changed[1]['normalized_key_span']=changed[0]['normalized_key_span']
            else:changed[0]['original_key_span'][1]+=1
            blob=b''.join(json.dumps(row,sort_keys=True,separators=(',',':')).encode()+b'\n' for row in changed)
            with self.assertRaises(S['Refused']):S['inverse_identity'](normalized,blob,updated_manifest(blob,receipt))
        with self.assertRaises(S['Refused']):S['inverse_identity'](normalized.replace(b'Alias',b'Other',1),manifest,receipt)
        changed=normalized.replace(b'Alias',b'Other',1);new=dict(receipt,normalized_sha256=hashlib.sha256(changed).hexdigest())
        with self.assertRaises(S['Refused']):S['inverse_identity'](changed,manifest,new)
    def test_complete_malformed_suffix_refuses_without_a_receipt(self):
        raw=FIX['tu']([FIX['node']()])
        for bad in (raw+b'{}',raw[:-1],raw.replace(b'"Alias"',b'tr ue',1)):
            with self.assertRaises(ValueError):normalize(bad,1)
    def test_each_write_is_bounded_and_short_sinks_refuse(self):
        raw=FIX['tu']([FIX['node'](original={'qualType':'A'*80000})]);out,manifest,receipt,maximum,manifest_max=normalize(raw)
        self.assertLessEqual(maximum,65536);self.assertLessEqual(manifest_max,4096)
        S['inverse_identity'](out,manifest,receipt)
        class Short:
            def write(self,value):return max(0,len(value)-1)
        with self.assertRaises(S['Refused']):S['normalize'](io.BytesIO(raw),Short(),io.BytesIO(),FIX['B'],lambda:None)
    def test_normalized_stream_is_strict_unique_json_and_zero_rename_case_is_identity(self):
        def pairs(rows):
            out={}
            for k,v in rows:self.assertNotIn(k,out);out[k]=v
            return out
        out,manifest,receipt,_,_=normalize(FIX['tu']([FIX['node'](),FIX['node']('TypedefType')]))
        json.loads(out,object_pairs_hook=pairs)
        raw=FIX['tu']([[('id',b'"0x1"'),('kind',b'"BuiltinType"'),('type',b'{"qualType":"int"}')]])
        out,manifest,receipt,_,_=normalize(raw);self.assertEqual(out,raw);self.assertEqual(manifest,b'')
        self.assertEqual(S['inverse_identity'](out,manifest,receipt)['inverse_rows'],0)
    def test_role_AST_is_exact_origin_and_no_child(self):
        new=ast.parse((HERE/'role_normalizer_v1.py').read_bytes());old=ast.parse((WHOLE/'compiler-duplicate-census-v3/complete_duplicate_census_v3.py').read_bytes())
        get=lambda tree:next(n for n in tree.body if getattr(n,'name',None)=='role')
        self.assertEqual(ast.dump(get(new),include_attributes=False),ast.dump(get(old),include_attributes=False));self.assertEqual(EVENTS,[])
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'child_events':EVENTS,
        'source_sha256':hashlib.sha256((HERE/'role_normalizer_v1.py').read_bytes()).hexdigest(),'scope':'synthetic in-memory normalization only; no actual AST/source/ABI/root/main admission'}))
    raise SystemExit(not result.wasSuccessful())
