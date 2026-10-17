"""2026-10-16 ET. Inert inverse/policy/full-stream controls; no controller main."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import types
import unittest
EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('pure capture controls refuse '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;OLD=WHOLE/'compiler-capture-v8';INGRESS=WHOLE/'streaming-minify-v1'
def load(path):
    result={'__name__':'inert_capture_controls','__file__':str(path)};exec(compile(path.read_bytes(),str(path),'exec'),result);return result
E=load(HERE/'linux_compiler_capture_v9.py');A=load(INGRESS/'compiler_unit_adapter_v4.py');OLD_A=load(WHOLE/'compiler_unit_adapter_v2.py')
DELTA=json.loads((HERE/'compiler-capture-v9-inverse.json').read_bytes());POLICY=json.loads((HERE/'linux_compiler_capture_policy_v9.json').read_bytes());COMMAND=json.loads((HERE/'linux_compiler_capture_command_v9.json').read_bytes())
STREAM=load(INGRESS/'test_stream_minify_v1.py')
def functions(raw):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)}
def inverse(value,edits):
    for edit in reversed(edits):
        parent=value
        for key in edit['path'][:-1]:parent=parent[key]
        key=edit['path'][-1]
        if edit.get('operation')=='add':assert parent[key]==edit['new'];del parent[key]
        elif edit.get('operation')=='remove':parent[key]=copy.deepcopy(edit['old'])
        else:assert parent[key]==edit['new'];parent[key]=copy.deepcopy(edit['old'])
    return value
class Controls(unittest.TestCase):
    def test_entry_text_and_AST_inverse(self):
        text=(HERE/'linux_compiler_capture_v9.py').read_text()
        for edit in reversed(DELTA['entry_edits']):self.assertEqual(text.count(edit['new']),1);text=text.replace(edit['new'],edit['old'],1)
        self.assertEqual(text,Path(DELTA['predecessor']['path']).read_text());self.assertEqual(ast.dump(ast.parse(text)),ast.dump(ast.parse(Path(DELTA['predecessor']['path']).read_text())))
        before=functions(Path(DELTA['predecessor']['path']).read_bytes());after=functions((HERE/'linux_compiler_capture_v9.py').read_bytes());self.assertEqual(set(before),set(after))
        for name in before:
            if name not in {'main','lossless_recipe','stream_caller_ast'}:self.assertEqual(before[name],after[name])
    def test_adapter_inverse_and_all_semantic_functions_exact(self):
        text=(INGRESS/'compiler_unit_adapter_v4.py').read_text()
        for edit in reversed(DELTA['adapter_edits']):self.assertEqual(text.count(edit['new']),1);text=text.replace(edit['new'],edit['old'],1)
        old=Path(DELTA['adapter_predecessor']['path']).read_text();self.assertEqual(text,old)
        before=functions(old);after=functions((INGRESS/'compiler_unit_adapter_v4.py').read_bytes());self.assertEqual(set(before),set(after))
        for name in before:
            if name!='prepare_unit':self.assertEqual(before[name],after[name])
    def test_complete_json_decoding_identical(self):
        raw=b' { "kind":"TranslationUnitDecl", "inner":[{"id":"0xa","kind":"FunctionDecl","name":"f", "inner":[]}], "loc":{"file":"/s.cpp","offset":0,"line":1} } '
        mini,receipt=STREAM['minified'](raw,1)
        self.assertEqual(A['parse_json_roots'](mini,full_tu=True),OLD_A['parse_json_roots'](raw,full_tu=True))
        self.assertEqual(A['resolve_locations'](A['parse_json_roots'](mini,full_tu=True)[0],'/s.cpp'),OLD_A['resolve_locations'](OLD_A['parse_json_roots'](raw,full_tu=True)[0],'/s.cpp'))
    def test_original_parser_cap_not_reinterpreted(self):
        old=A['STAGE_BYTES'];A['STAGE_BYTES']=32
        try:
            with self.assertRaises(A['Refused']):A['parse_json_roots'](b'{"kind":"TranslationUnitDecl","inner":[]}',full_tu=True)
        finally:A['STAGE_BYTES']=old
        self.assertEqual((A['STAGE_BYTES'],A['TOTAL_BYTES']),(134217728,268435456))
    def test_identity_ingress_refuses_every_profile_mutation(self):
        node=copy.deepcopy(next(n for n in ast.parse((INGRESS/'compiler_unit_adapter_v4.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='prepare_unit'))
        stop=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='source_text' for t in n.targets))
        node.body=node.body[:stop];node.name='checked_ingress_only';ns=dict(A);exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'inert-ingress-prefix','exec'),ns)
        raw=b' {"kind":"TranslationUnitDecl", "inner":[]} ';mini,identity=STREAM['minified'](raw)
        source=WHOLE/'source_call_fixture_v2.cpp';probe=WHOLE/'compiler_abi_probe_v1.cpp'
        args={'api':{},'full_tu_raw':mini,'abi_raw':b'','source_path':source,'source_bytes':source.read_bytes(),'probe_path':probe,'probe_bytes':probe.read_bytes(),
            'declarations':[],'compiler_capture_pin':'0'*64,'full_tu_identity':identity,'full_tu_compressed_bytes':10}
        ns['checked_ingress_only'](**args)
        for key,value in [('schema','other'),('raw_limit',536870912),('retained_limit',134217729),('raw_bytes',True),('raw_sha256','bad'),
            ('minified_bytes',1),('minified_sha256','0'*64),('AST_nodes_elided',True),('independent_filtered_parse_join',True),('objects',True),('max_depth',257),
            ('peak_live_key_charge',16777217),('values',0),('complete_JSON_syntax_and_duplicate_key_check',False),('extra',True)]:
            changed=copy.deepcopy(args);changed['full_tu_identity'][key]=value
            with self.subTest(key=key),self.assertRaises(A['Refused']):ns['checked_ingress_only'](**changed)
        for value in (0,True,134217729):
            with self.assertRaises(A['Refused']):ns['checked_ingress_only'](**dict(args,full_tu_compressed_bytes=value))
        ns['TOTAL_BYTES']=len(args['source_bytes'])+len(args['probe_bytes'])+len(mini)+9
        with self.assertRaises(A['Refused']):ns['checked_ingress_only'](**args)
    def test_policy_and_command_complete_inverses(self):
        self.assertEqual(inverse(copy.deepcopy(POLICY),DELTA['policy_edits']),json.loads(Path(DELTA['old_policy']['path']).read_bytes()))
        self.assertEqual(inverse(copy.deepcopy(COMMAND),DELTA['command_edits']),json.loads(Path(DELTA['old_command']['path']).read_bytes()))
    def test_exact_physical_pins_and_staging(self):
        staged={}
        for row in COMMAND['controller_inputs']:
            path=Path(row['path']);raw=path.read_bytes();self.assertFalse(path.is_symlink());self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(row['bytes'],row['sha256']));staged[path.name]={k:row[k] for k in ('bytes','sha256')}
        p=HERE/'linux_compiler_capture_policy_v9.json';self.assertEqual(COMMAND['argv'][-1],hashlib.sha256(p.read_bytes()).hexdigest());del staged[p.name]
        self.assertEqual(staged,POLICY['controller_files']);self.assertEqual(len(staged),len(COMMAND['controller_inputs'])-1)
        self.assertLess(sum(row['bytes'] for row in COMMAND['controller_inputs']),1048576)
        self.assertEqual(E['ADAPTER_SHA'],staged['compiler_unit_adapter_v4.py']['sha256']);self.assertEqual(E['CODEC_SHA'],staged['lossless_gzip_v2.py']['sha256']);self.assertEqual(E['MINIFIER_SHA'],staged['strict_minify_v1.py']['sha256'])
    def test_resources_runtime_source_roles_unchanged(self):
        old=json.loads((OLD/'linux_compiler_capture_policy_v8.json').read_bytes())
        for key in old:
            if key not in {'schema','raw_name','entry_sha256','controller_files','capture_recipe'}:self.assertEqual(POLICY[key],old[key])
        self.assertEqual((E['WHOLE_SECONDS'],E['ENTRY_SECONDS'],E['RSS_BYTES'],E['STAGE_BYTES'],E['TOTAL_BYTES'],E['FINAL_METADATA_RESERVE']),(180,165,4294967296,134217728,268435456,1048576))
        self.assertEqual(COMMAND['root_guard'],json.loads((OLD/'linux_compiler_capture_command_v8.json').read_bytes())['root_guard']);self.assertEqual(COMMAND['node'],1)
    def test_original_argv_one_TU_and_explicit_phase_limits(self):
        old=json.loads((OLD/'linux_compiler_capture_policy_v8.json').read_bytes())['capture_recipe'];recipe=POLICY['capture_recipe']
        for a,b in zip(old['commands'],recipe['commands']):self.assertEqual(b['argv'],[x.replace('full-tu-2baf722f-v8','full-tu-2baf722f-v9') for x in a['argv']])
        self.assertEqual(len(recipe['commands']),4);self.assertFalse(any('ast-dump-filter' in x for x in recipe['commands'][1]['argv']))
        self.assertEqual((recipe['caller_ast_phase_seconds'],recipe['other_phase_seconds']),(120,45));self.assertEqual(recipe['lossless_caller_stdout']['expanded_limit'],2147483648);self.assertFalse(recipe['lossless_caller_stdout']['raw_full_DOM_materialized'])
        tree=ast.parse((HERE/'linux_compiler_capture_v9.py').read_bytes());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');stage=next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='stage');body=ast.unparse(stage)
        self.assertIn('phase_seconds = 120 if',body);self.assertIn('remaining = min(phase_seconds, deadline - time.monotonic() - 10)',body)
    def test_true_EOF_before_publish_and_complete_consumer(self):
        source=(HERE/'linux_compiler_capture_v9.py').read_text()
        self.assertNotIn('codec.decode(',source);self.assertIn('codec.DecodeReader(',source)
        self.assertLess(source.index('if not decoded.verified'),source.index('os.rename(tentative, minified_path)'))
        self.assertLess(source.index('os.rename(tentative, minified_path)'),source.index('full_tu_raw = minified_path.read_bytes()'))
        self.assertIn('full_tu_identity=identity',source);self.assertIn('"minified_ast", "token_identity"',source)
        self.assertFalse(COMMAND['raw_full_DOM_materialized']);self.assertFalse(COMMAND['actual_launched']);self.assertFalse(COMMAND['public_proof'])
    def test_closed_runtime_origin_and_typo_not_criteria(self):
        origin=POLICY['zlib_binding'];self.assertEqual(origin['builtin'],1);self.assertEqual(origin['spec_origin'],'built-in');self.assertIsNone(origin['extension']);self.assertIsNone(origin['module_file'])
        self.assertIn(origin['physical_interpreter'],POLICY['native_runtime']['pins'])
        for row in origin['mapped_compression_objects']:self.assertIn(row,POLICY['native_runtime']['pins'])
        self.assertNotIn('scope',origin);self.assertEqual(POLICY['zlib_origin_receipt_sha256'],'bc53f66a5c159b43af8b3fbc69a0ec367c39197589e57fd8af505e5730ae4e3d')
    def test_all_controls_no_children(self):self.assertEqual(EVENTS,[]);self.assertEqual(STREAM['EVENTS'],[])
if __name__=='__main__':
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Controls),unittest.defaultTestLoader.loadTestsFromTestCase(STREAM['Controls'])]);result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'child_events':EVENTS+STREAM['EVENTS'],
        'entry_sha256':hashlib.sha256((HERE/'linux_compiler_capture_v9.py').read_bytes()).hexdigest(),'adapter_sha256':hashlib.sha256((INGRESS/'compiler_unit_adapter_v4.py').read_bytes()).hexdigest(),'controls_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'source preparation and synthetic streams only; no actual capture/consumer main'}))
    sys.exit(not result.wasSuccessful())
