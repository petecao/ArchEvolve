"""Pure synthetic complete ordered-pair census; never actual retained TU/main."""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('pure census controls '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent
S={'__name__':'inert_census_controls','__file__':str(HERE/'complete_duplicate_census_v1.py')};exec(compile((HERE/'complete_duplicate_census_v1.py').read_bytes(),'inert_census_controls','exec'),S)
B={'__name__':'inert_minifier'};exec(compile((WHOLE/'streaming-minify-v1/strict_minify_v2.py').read_bytes(),'inert_minifier','exec'),B)
def js(value):return json.dumps(value,separators=(',',':'),ensure_ascii=True).encode()
def pairs(rows):return b'{'+b','.join(js(key)+b':'+value for key,value in rows)+b'}'
def node(kind='UsingType',original=None,target=None,flags=(),decl=None,tail=True):
    original=original if original is not None else {'qualType':'Alias'}
    target=target if target is not None else {'qualType':'unsigned long','desugaredQualType':'unsigned long','typeAliasDeclId':'0x2'}
    decl=decl if decl is not None else {'id':'0x2','kind':'UsingShadowDecl' if kind=='UsingType' else 'TypedefDecl','name':'Alias'}
    result=[('id',js('0x1')),('kind',js(kind)),('type',js(original)),*[(k,js(v)) for k,v in flags],('decl',js(decl)),('type',js(target))]
    if tail:result.append(('inner',b'[]'))
    return result
def tu(nodes):return pairs([('id',js('0x0')),('kind',js('TranslationUnitDecl')),('inner',b'['+b','.join(pairs(n) for n in nodes)+b']')])
class Source(io.BytesIO):
    def __init__(self,raw,size):super().__init__(raw);self.size=size
    def read(self,size):return super().read(min(size,self.size))
def census(raw,size=65536):return S['census'](Source(raw,size),B,lambda:None)
class Controls(unittest.TestCase):
    def test_all_known_roles_preserve_different_values_and_distinct_identities(self):
        nodes=[node(),node('TypedefType')];raw=tu(nodes);r=census(raw)
        normalized=[[(('swdbClangDesugaredType' if k=='type' and i==len(n)-2 else k),v) for i,(k,v) in enumerate(n)] for n in nodes]
        expected=tu(normalized)
        self.assertEqual(r['duplicate_events'],2);self.assertEqual(r['unknown_or_mismatched_duplicate_events'],0);self.assertTrue(r['prospective_role_normalization_eligible'])
        self.assertEqual(r['original_minified_token_sha256'],hashlib.sha256(raw).hexdigest());self.assertEqual(r['prospective_normalized_token_sha256'],hashlib.sha256(expected).hexdigest())
        self.assertNotEqual(r['original_minified_token_sha256'],r['prospective_normalized_token_sha256']);self.assertFalse(r['normalization_is_original_token_identity'])
        for item in r['samples']:
            self.assertFalse(item['values_structurally_identical']);self.assertTrue(item['role_qualified']);self.assertNotEqual(item['first_value']['ordered_merkle_sha256'],item['next_value']['ordered_merkle_sha256'])
    def test_identical_values_still_keep_both_roles(self):
        r=census(tu([node(target={'qualType':'Alias'})]));self.assertTrue(r['samples'][0]['values_structurally_identical']);self.assertEqual(r['prospective_role_renames'],1);self.assertTrue(r['prospective_role_normalization_eligible'])
    def test_chunk_splits_and_whitespace_preserve_graph_and_tokens(self):
        raw=tu([node(),node('TypedefType')]);base=census(raw)
        for size in range(1,18):self.assertEqual(census(raw,size),base)
        spaced=b' \n'+raw.replace(b',',b', \n').replace(b':',b': ')+b'\r\n';r=census(spaced,7)
        for key in ('ordered_graph_merkle_sha256','original_minified_token_sha256','prospective_normalized_token_sha256'):self.assertEqual(r[key],base[key])
        self.assertEqual(r['raw_sha256'],hashlib.sha256(spaced).hexdigest())
    def test_unknown_kind_key_and_third_occurrence_are_all_counted(self):
        a=node('UnknownType');b=node();b.append(('type',js({'qualType':'third'})))
        c=[('id',js('0x3')),('kind',js('OtherDecl')),('name',js('a')),('name',js('b')),('x',js(1)),('x',js(2))]
        r=census(tu([a,b,c]));self.assertEqual(r['duplicate_events'],5);self.assertEqual(r['unknown_or_mismatched_duplicate_events'],5);self.assertTrue(r['prospective_normalization_refused'])
    def test_every_exact_role_shape_order_flag_decl_mutation_refuses_normalization(self):
        cases=[]
        cases.append(node(original={'qualType':'Alias','desugaredQualType':'long'}))
        cases.append(node(target={'qualType':'long','unexpected':1}))
        cases.append(node(target={'qualType':12}))
        cases.append(node(target={'qualType':'long','typeAliasDeclId':'bad'}))
        cases.append(node(flags=[('isDependent',False)]))
        cases.append(node(flags=[('isImported',True),('isDependent',True)]))
        cases.append(node(decl={'id':'0x2','kind':'TypedefDecl','name':'Alias'}))
        cases.append(node(decl={'id':'0x2','kind':'UsingShadowDecl','name':'Alias','extra':1}))
        cases.append(node()+[('swdbClangDesugaredType',js('collision'))])
        changed=node();changed[3],changed[4]=changed[4],changed[3];cases.append(changed)
        changed=node();changed[0]=('id',js('bad'));cases.append(changed)
        changed=node();changed[-1]=('inner',js(3));cases.append(changed)
        for nodes in cases:
            r=census(tu([nodes]));self.assertFalse(r['prospective_role_normalization_eligible']);self.assertGreater(r['unknown_or_mismatched_duplicate_events'],0)
    def test_nested_unknown_keys_inside_type_values_are_not_overwritten(self):
        n=node();n[2]=('type',b'{"qualType":"a","qualType":"b"}');r=census(tu([n]));self.assertEqual(r['duplicate_events'],2);self.assertEqual(r['unknown_or_mismatched_duplicate_events'],2)
    def test_escaped_key_spelling_is_not_an_emitter_role(self):
        raw=tu([node()]);at=raw.rfind(b'"type"');raw=raw[:at]+b'"\\u0074ype"'+raw[at+6:];r=census(raw,1);self.assertEqual(r['duplicate_events'],1);self.assertTrue(r['prospective_normalization_refused'])
    def test_full_syntax_after_earlier_duplicates_is_checked(self):
        raw=tu([node()])
        for bad in (raw+b'{}',raw[:-1],raw[:-2]+b',]',raw.replace(b'"Alias"',b'tr ue',1),raw.replace(b'"Alias"',b'1 .0',1),raw.replace(b'"Alias"',b'- 1',1)):
            with self.assertRaises(ValueError):census(bad,3)
    def test_unique_decl_sibling_keys_are_not_duplicates(self):
        r=census(tu([[('id',js('0x1')),('kind',js('BuiltinType')),('type',js({'qualType':'int'}))], [('id',js('0x2')),('kind',js('BuiltinType')),('type',js({'qualType':'int'}))]]))
        self.assertEqual(r['duplicate_events'],0);self.assertTrue(r['prospective_role_normalization_eligible']);self.assertEqual(r['original_minified_token_sha256'],r['prospective_normalized_token_sha256'])
    def test_many_duplicates_have_complete_digest_and_bounded_samples(self):
        raw=tu([node() for _ in range(100)]);r=census(raw);self.assertEqual(r['duplicate_events'],100);self.assertEqual(len(r['samples']),8);self.assertEqual(sum(g['count'] for g in r['duplicate_groups']),100)
        self.assertLess(len(json.dumps(r)),32768);self.assertEqual(r['raw_bytes'],len(raw))
    def test_documented_typedef_decl_roles_and_generic_flags(self):
        for kind in ('TypedefDecl','TypeAliasDecl'):
            n=node('TypedefType',flags=[('isDependent',True),('isImported',True)],decl={'id':'0x2','kind':kind,'name':'Alias'})
            self.assertTrue(census(tu([n]))['prospective_role_normalization_eligible'])
    def test_no_actual_reader_or_child(self):self.assertEqual(EVENTS,[]);self.assertEqual(S['EVENTS'],[])
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'child_events':EVENTS+S['EVENTS'],'source_sha256':hashlib.sha256((HERE/'complete_duplicate_census_v1.py').read_bytes()).hexdigest(),'scope':'synthetic ordered-pair whole-stream controls; no actual retained TU/census/compiler/main'}))
    raise SystemExit(not result.wasSuccessful())
