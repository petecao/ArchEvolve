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
S={'__name__':'inert_census_controls','__file__':str(HERE/'complete_duplicate_census_v2.py')};exec(compile((HERE/'complete_duplicate_census_v2.py').read_bytes(),'inert_census_controls','exec'),S)
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
            self.assertFalse(item['values_structurally_identical']);self.assertTrue(item['role_qualified']);self.assertNotEqual(item.get('first_value',{}).get('ordered_merkle_sha256',item.get('first_value_merkle_sha256')),item.get('next_value',{}).get('ordered_merkle_sha256',item.get('next_value_merkle_sha256')))
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
    def test_full_long_key_and_kind_identities_never_group_by_display_prefix(self):
        common='x'*256;names=[common+'a',common+'b']
        nodes=[[('kind',js('Unknown')), (key,js(1)), (key,js(2))] for key in names]
        r=census(tu(nodes));self.assertEqual(r['duplicate_events'],2);self.assertEqual(r['duplicate_group_count'],2)
        self.assertEqual({g['signature']['key_sha256'] for g in r['duplicate_groups']},{hashlib.sha256(k.encode()).hexdigest() for k in names})
        kinds=['K'*128+'a','K'*128+'b'];nodes=[[('kind',js(kind)),('x',js(1)),('x',js(2))] for kind in kinds]
        r=census(tu(nodes));self.assertEqual(r['duplicate_group_count'],2)
        self.assertEqual({g['signature']['node_kind_identity']['decoded_string_sha256'] for g in r['duplicate_groups']},{hashlib.sha256(k.encode()).hexdigest() for k in kinds})
    def test_worst_case_publication_extent_keeps_complete_digests_and_input_unchanged(self):
        report=census(tu([node()]));value={'census':report,'inputs':[{'path':'p'*300,'sha256':'f'*64} for _ in range(8)],'fixed':'f'*4096}
        report['samples']=[{'metadata':'x'*2000} for _ in range(8)]
        report['duplicate_groups']=[{'signature':'g'*980,'count':i} for i in range(16)]
        original=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
        text=S['publication'](value);self.assertLessEqual(len(text.encode())+1,32768);published=json.loads(text)
        self.assertEqual(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False),original)
        p=published['publication'];self.assertEqual(p['complete_report_sha256'],hashlib.sha256(original.encode()).hexdigest())
        self.assertEqual(p['complete_report_bytes'],len(original.encode()));self.assertGreater(p['omitted_group_display_rows']+p['omitted_event_display_rows'],0)
        self.assertEqual(p['omitted_event_display_rows']+len(published['census']['samples']),8)
        self.assertEqual(p['omitted_group_display_rows']+len(published['census']['duplicate_groups']),16)
        for key in ('duplicate_events','duplicate_group_count','duplicate_event_census_sha256','complete_duplicate_group_census_sha256','ordered_graph_merkle_sha256','original_minified_token_sha256','prospective_normalized_token_sha256'):
            self.assertEqual(published['census'][key],report[key])
        with self.assertRaises(S['Refused']):S['publication']({'census':report,'fixed':'x'*40000})
    def test_group_membership_is_order_independent_but_event_digest_is_ordered(self):
        a=[('kind',js('unknown')),('x',js(1)),('x',js(2))];b=[('kind',js('unknown')),('y',js(1)),('y',js(2))]
        left=census(tu([a,b]));right=census(tu([b,a]))
        self.assertEqual(left['complete_duplicate_group_census_sha256'],right['complete_duplicate_group_census_sha256'])
        self.assertNotEqual(left['duplicate_event_census_sha256'],right['duplicate_event_census_sha256'])
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'child_events':EVENTS+S['EVENTS'],'source_sha256':hashlib.sha256((HERE/'complete_duplicate_census_v2.py').read_bytes()).hexdigest(),'scope':'synthetic ordered-pair whole-stream controls; no actual retained TU/census/compiler/main'}))
    raise SystemExit(not result.wasSuccessful())
