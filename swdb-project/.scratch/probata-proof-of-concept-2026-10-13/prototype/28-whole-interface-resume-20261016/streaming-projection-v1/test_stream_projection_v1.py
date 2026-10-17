"""2026-10-16 ET. Synthetic one-stream/no-child controls; no actual compiler AST."""
import copy
import ast
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('pure stream controls refuse '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent
API={'__name__':'inert_stream_projection'}
SOURCE=(HERE/'stream_projection_v1.py').read_bytes()
exec(compile(SOURCE,str(HERE/'stream_projection_v1.py'),'exec'),API)
Refused=API['Refused']


def policy():
    return {'schema':'original-tu-stream-policy-1','max_stream_bytes':1048576,'max_depth':128,
        'max_token_bytes':32768,'max_metadata_bytes':65536,'max_nodes':10000,'max_ids':10000,
        'max_census_rows':1000,'max_work_bytes':1048576,'max_retained_pair_bytes':1048576,'caller_mangled':'_Z1fv','caller_source_path':'/inert/caller.cpp',
        'selected_names':['alloc_MAA','reg_addr','__assert_fail','my_int'],'api_names':['alloc_MAA'],
        'source_and_compiler_receipt_sha256':'a'*64}


def fixture():
    api={'id':'api','kind':'FunctionDecl','loc':{'offset':10,'file':'/inert/header.hpp','line':3},
        'name':'alloc_MAA','type':{'qualType':'void ()'}}
    ref={'id':'ref','kind':'DeclRefExpr','type':{'qualType':'void ()'},
        'referencedDecl':{'id':'api','kind':'FunctionDecl','name':'alloc_MAA','type':{'qualType':'void ()'}}}
    call={'id':'call','kind':'CallExpr','range':{'begin':{'offset':2},'end':{'offset':11}},'type':{'qualType':'void'},
        'inner':[{'id':'cast','kind':'ImplicitCastExpr','castKind':'FunctionToPointerDecay','inner':[ref]}]}
    caller={'id':'caller','kind':'FunctionDecl','loc':{'offset':0,'file':'/inert/caller.cpp','line':1},
        'name':'f','mangledName':'_Z1fv','type':{'qualType':'void ()'},
        'inner':[{'id':'body','kind':'CompoundStmt','inner':[call]}]}
    irrelevant={'id':'std','kind':'NamespaceDecl','name':'std','inner':[
        {'id':'discard','kind':'RecordDecl','name':'Unrelated','loc':{'offset':30,'file':'/inert/other.hpp','line':8},
         'inner':[{'id':'big','kind':'StringLiteral','value':'x'*20000}]}]}
    return {'id':'tu','kind':'TranslationUnitDecl','inner':[irrelevant,api,caller]}


def raw(value):return b' \n'+json.dumps(value,separators=(',',':')).encode()+b'\n '


def project(value=None,p=None,stream=None):
    data=raw(fixture() if value is None else value);p=policy() if p is None else p
    result=API['project_stream'](io.BytesIO(data) if stream is None else stream,p)
    verified=API['verify_projection'](API['encode'](result['projection']),API['encode'](result['certificate']),p)
    return data,result,verified


class Controls(unittest.TestCase):
    def test_full_input_hash_single_caller_and_distinct_consumer_boundary(self):
        data,result,verified=project()
        cert=result['certificate'];tree=result['projection']
        self.assertEqual(cert['complete_stream_sha256'],hashlib.sha256(data).hexdigest())
        self.assertEqual(cert['complete_stream_bytes'],len(data))
        self.assertEqual(tree['kind'],'ProjectedOriginalTranslationUnitV1')
        self.assertNotEqual(tree['kind'],'TranslationUnitDecl')
        self.assertFalse(cert['old_raw_TU_consumer_compatible']);self.assertFalse(cert['source_call_or_public_admission'])
        self.assertTrue(verified['producer_and_source_compiler_observations_remain_TCB'])
        self.assertEqual(verified['elided_roots'],1)
        self.assertLess(result['retained_bytes'],len(data))
        self.assertEqual(EVENTS,[])

    def test_all_scopes_competing_names_and_location_elision_are_preserved(self):
        tree=fixture()
        tree['inner'][0]['inner'].append({'id':'competitor','kind':'FunctionDecl','name':'alloc_MAA',
            'loc':{'offset':40,'file':'/inert/other.hpp','line':10}})
        _,result,verified=project(tree)
        retained=list(API['walk'](result['projection']))
        self.assertEqual({n['id'] for n in retained if n.get('name')=='alloc_MAA'},{'api','competitor'})
        caller=next(n for n in retained if n.get('id')=='caller')
        self.assertEqual(caller['loc']['_file'],'/inert/caller.cpp')
        call=next(n for n in retained if n.get('id')=='call')
        self.assertEqual(call['range']['begin']['_file'],'/inert/caller.cpp')
        self.assertEqual(verified['selected_declarations'],3)
        self.assertTrue(any(n.get('__projection_scaffold__') for n in retained if n.get('name')=='std'))

    def test_every_owned_edge_is_scanned_and_unknown_metadata_nodes_refuse(self):
        tree=fixture();tree['inner'][0]['array_filler']=[{'id':'extra','kind':'VarDecl','name':'reg_addr'}]
        _,result,_=project(tree)
        self.assertTrue(any(n.get('id')=='extra' for n in API['walk'](result['projection'])))
        for key in ('hidden','arbitrary_children','bases'):
            tree=fixture();tree['inner'][0][key]={'id':'hidden','kind':'VarDecl','name':'alloc_MAA'}
            with self.assertRaisesRegex(Refused,'unknown owned AST'):project(tree)
        tree=fixture();tree['inner'][2]['inner'][0]['inner'][0]['inner'][0]['inner'][0]['referencedDecl']['inner']=[]
        with self.assertRaisesRegex(Refused,'unknown owned AST'):project(tree)

    def test_truncated_malformed_duplicate_keys_utf8_and_concatenated_roots_refuse(self):
        data=raw(fixture())
        mutations=[data[:-5],data+b'{}',b'[]',b'{"kind":"TranslationUnitDecl","kind":"TranslationUnitDecl"}',
            data.replace(b'"qualType":"void ()"',b'"qualType":"void ()","qualType":"int"',1),
            data.replace(b'"name":"std"',b'"name":"\xff"',1),
            data.replace(b'"name":"std"',b'"name":"\\uZZZZ"',1),
            data.replace(b'"offset":10',b'"offset":01',1)]
        for mutation in mutations:
            with self.subTest(bytes=len(mutation)),self.assertRaises((Refused,RecursionError)):
                API['project_stream'](io.BytesIO(mutation),policy())

    def test_duplicate_declaration_ids_refuse_identical_shared_type_ids_allow(self):
        tree=fixture();tree['inner'].insert(1,copy.deepcopy(tree['inner'][1]))
        with self.assertRaisesRegex(Refused,'duplicate/conflicting'):project(tree)
        tree=fixture();shared={'id':'shared','kind':'BuiltinType','type':{'qualType':'int'}}
        tree['inner'][0]['inner'] += [copy.deepcopy(shared),copy.deepcopy(shared)]
        project(tree)
        tree['inner'][0]['inner'][-1]['type']['qualType']='long'
        with self.assertRaisesRegex(Refused,'duplicate/conflicting'):project(tree)

    def test_full_caller_effects_calls_macro_api_and_unresolved_ids_refuse(self):
        for kind in ('CXXNewExpr','CXXDeleteExpr','GCCAsmStmt','StmtExpr','ForStmt'):
            tree=fixture();tree['inner'][2]['inner'][0]['inner'].append({'id':'effect','kind':kind})
            with self.subTest(kind=kind),self.assertRaisesRegex(Refused,'unmodeled caller'):project(tree)
        tree=fixture();call=tree['inner'][2]['inner'][0]['inner'][0]
        call['range']['begin']={'spellingLoc':{'offset':2},'expansionLoc':{'offset':3}}
        with self.assertRaisesRegex(Refused,'macro/non-direct'):project(tree)
        tree=fixture();tree['inner'][2]['type']['typeAliasDeclId']='omitted_alias'
        with self.assertRaisesRegex(Refused,'omitted declaration'):project(tree)
        tree=fixture();ref=tree['inner'][2]['inner'][0]['inner'][0]['inner'][0]['inner'][0]
        ref['referencedDecl']['name']='unknown_effect'
        with self.assertRaisesRegex(Refused,'unmodeled caller call'):project(tree)
        tree=fixture();tree['inner'][2]['inner'][0]['inner'].append({'id':'increment','kind':'UnaryOperator','opcode':'++'})
        with self.assertRaisesRegex(Refused,'unmodeled caller unary'):project(tree)
        tree=fixture();tree['inner'][2]['type']={'qualType':'VI','desugaredQualType':'volatile int'}
        with self.assertRaisesRegex(Refused,'unmodeled caller volatile'):project(tree)

    def test_complete_assertion_macro_subtree_is_kept(self):
        tree=fixture();tree['inner'].insert(1,{'id':'assert','kind':'FunctionDecl','name':'__assert_fail'})
        body=tree['inner'][-1]['inner'][0]
        body['inner'].append({'id':'assert_call','kind':'CallExpr',
            'range':{'begin':{'spellingLoc':{'offset':2,'file':'/inert/assert.h','line':4},
                'expansionLoc':{'offset':12,'file':'/inert/caller.cpp','line':1}},'end':{'offset':15}},
            'inner':[{'id':'assert_ref','kind':'DeclRefExpr','referencedDecl':{'id':'assert','kind':'FunctionDecl','name':'__assert_fail'}},
                {'id':'str','kind':'StringLiteral','value':'source assertion'}]})
        _,result,_=project(tree)
        self.assertTrue(any(node.get('id')=='str' for node in API['walk'](result['projection'])))

    def test_named_aliases_enums_and_referenced_local_definitions_are_closed(self):
        tree=fixture()
        tree['inner'][0]['inner'] += [
            {'id':'alias','kind':'TypedefDecl','name':'not_in_policy','inner':[{'id':'builtin','kind':'BuiltinType','type':{'qualType':'int'}}]},
            {'id':'enum','kind':'EnumDecl','name':'UnlistedEnum','inner':[{'id':'constant','kind':'EnumConstantDecl','name':'A'}]}]
        caller=tree['inner'][2];caller['type']['typeAliasDeclId']='alias'
        caller['inner'][0]['inner'].append({'id':'constant_ref','kind':'DeclRefExpr',
            'referencedDecl':{'id':'constant','kind':'EnumConstantDecl','name':'A'}})
        _,result,_=project(tree)
        self.assertTrue({'alias','enum','constant'} <= {node.get('id') for node in API['walk'](result['projection'])})

    def test_input_output_and_work_limits_are_separate_and_fail_closed(self):
        for key,value in [('max_stream_bytes',100),('max_depth',3),('max_token_bytes',12),('max_metadata_bytes',16),
            ('max_nodes',3),('max_ids',2),('max_census_rows',1),('max_work_bytes',100),('max_retained_pair_bytes',100)]:
            p=policy();p[key]=value
            with self.subTest(key=key),self.assertRaises(Refused):project(p=p)
        p=policy();del p['max_stream_bytes']
        with self.assertRaisesRegex(Refused,'exact projection policy'):project(p=p)
        original=API['STAGE_BYTES'];API['STAGE_BYTES']=64
        try:
            with self.assertRaisesRegex(Refused,'retained per-file'):project()
        finally:API['STAGE_BYTES']=original
        p=policy();p['max_stream_bytes']=2*API['TOTAL_BYTES']
        self.assertGreater(p['max_stream_bytes'],API['STAGE_BYTES'])
        # A separate input allowance in an inert policy is not runtime admission.
        project(p=p)

    def test_small_read_chunks_preserve_the_complete_stream_and_raw_partitions(self):
        data=raw(fixture())
        class SmallReads:
            def __init__(self):self.at=0
            def read(self,count):
                out=data[self.at:self.at+min(count,7)];self.at+=len(out);return out
        _,result,_=project(stream=SmallReads())
        cert=result['certificate']
        def check_span(span):
            self.assertEqual(hashlib.sha256(data[span['start']:span['end']]).hexdigest(),span['sha256'])
        for part in cert['complete_stream_partition']:check_span(part)
        for node in API['walk'](result['projection']):
            ann=node['__projection_node__'];check_span(ann['raw_span'])
            for part in ann['partition']:check_span(part)
        self.assertEqual(cert['complete_stream_sha256'],hashlib.sha256(data).hexdigest())

    def test_late_selectors_missing_caller_wrong_physical_source_and_reserved_keys_refuse(self):
        tree=fixture();caller=tree['inner'][2];caller['name']=caller.pop('name')
        with self.assertRaisesRegex(Refused,'late AST selector'):project(tree)
        tree=fixture();tree['inner'].pop()
        with self.assertRaisesRegex(Refused,'one complete original caller'):project(tree)
        tree=fixture();tree['inner'][2]['loc']['file']='/inert/frozen.ii'
        tree['inner'][2]['loc']['presumedFile']='/inert/caller.cpp'
        with self.assertRaisesRegex(Refused,'physical file differs'):project(tree)
        for key in ('_file','_line','__projection_node__','__projection_scaffold__'):
            tree=fixture();tree[key]='forged'
            with self.assertRaisesRegex(Refused,'reserved'):project(tree)

    def test_passive_reader_refuses_projection_hash_partition_census_and_reference_mutations(self):
        _,result,_=project();p=policy()
        mutations=[]
        c=copy.deepcopy(result['certificate']);c['complete_stream_partition'][0]['end']+=1;mutations.append((result['projection'],c))
        c=copy.deepcopy(result['certificate']);c['owned_nodes_visited']+=1;mutations.append((result['projection'],c))
        c=copy.deepcopy(result['certificate']);next(row for row in c['complete_node_id_occurrences'] if row[0]=='api')[0]='other';mutations.append((result['projection'],c))
        c=copy.deepcopy(result['certificate']);c['caller_checks']['required_reference_ids']=[];mutations.append((result['projection'],c))
        c=copy.deepcopy(result['certificate']);c['old_raw_TU_consumer_compatible']=True;mutations.append((result['projection'],c))
        t=copy.deepcopy(result['projection']);t['__projection_node__']['partition'][0]['end']+=1
        c=copy.deepcopy(result['certificate']);c['projection_sha256']=API['digest'](t);mutations.append((t,c))
        t=copy.deepcopy(result['projection']);t['inner'][0]['counts']['selected_roots']=1
        c=copy.deepcopy(result['certificate']);c['projection_sha256']=API['digest'](t);mutations.append((t,c))
        for t,c in mutations:
            with self.subTest(certificate=c.get('owned_nodes_visited')),self.assertRaises(Refused):
                API['verify_projection'](API['encode'](t),API['encode'](c),p)
        with self.assertRaises(Refused):API['verify_projection'](b'{"kind":0,"kind":1}',API['encode'](result['certificate']),p)
        with self.assertRaises(Refused):API['verify_projection'](API['encode'](fixture()),API['encode'](result['certificate']),p)

    def test_existing_complete_tu_parser_refuses_the_distinct_projected_root(self):
        source=(HERE.parent/'compiler_unit_adapter_v2.py').read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(),'1cf112859f976f77e8381c777c977f5cf5857d6e18f1bd0e24f9689148e80317')
        tree=ast.parse(source)
        names={'Refused','need','strict_decoder','parse_json_roots'}
        nodes=[node for node in tree.body if isinstance(node,(ast.ClassDef,ast.FunctionDef)) and node.name in names]
        self.assertEqual(len(nodes),4)
        legacy={'json':json,'STAGE_BYTES':134217728}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'pinned-pure-legacy-parser','exec'),legacy)
        _,result,_=project()
        with self.assertRaisesRegex(legacy['Refused'],'one complete original TU'):
            legacy['parse_json_roots'](API['encode'](result['projection']),full_tu=True)
        self.assertEqual(EVENTS,[])


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),
        'child_events':EVENTS,'source_sha256':hashlib.sha256(SOURCE).hexdigest(),
        'tests_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'actual_compiler_or_scientific_execution':False},sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun==13 and not result.skipped and not EVENTS else 1)
