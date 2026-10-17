"""2026-10-16 ET: pure source/gate controls; no actual stream or project imports."""
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
import shlex
import sys
import unittest

EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in ('os.system','ctypes.dlopen'):
        EVENTS.append(event);raise ValueError('pure memory role controls refuse '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
ENTRY=HERE/'memory_role_controller_v1.py'
TEMPLATE=HERE/'controller_template_v1.py'
POLICY=json.loads((HERE/'source_policy_v1.json').read_bytes())
COMMAND=json.loads((HERE/'command_v1.json').read_bytes())
TREE=ast.parse(TEMPLATE.read_bytes())
def need(ok,message):
    if not ok:raise ValueError(message)
gates={'need':need}
nodes=[n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name in ('check_original_observation','check_derived_transport')]
exec(compile(ast.Module(nodes,type_ignores=[]),str(TEMPLATE),'exec'),gates)
def assignments(tree):
    result={}
    for node in tree.body:
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name):
            try:result[node.targets[0].id]=ast.literal_eval(node.value)
            except (ValueError,TypeError):pass
    return result
def observation():
    commands=[{'phase':name,'returncode':0} for name in ('caller-preprocess','caller-ast','abi-preprocess','abi-ast')]
    result={'accepted':True,'error':None,'after_input_errors':[],'bytecode_cache_present':False,'compiler_observation_complete':True,
        'source_call_admitted':False,'source_names':[],'source_call_count':0,'ABI_interpreted':False,'strict_complete_TU_consumer_passed':False,
        'native_or_solver_executed':False,'public_proof':False,'current_0_2':False,'full_ticket28':False,'scope':'literal observation scope'}
    value={'commands':copy.deepcopy(commands),'source_commit':'2baf722fdaa6cba24b859eae3172a6f597417d72','original_source_coordinates':True}
    policy={'original_result_scope':result['scope'],'original_commands':copy.deepcopy(commands)}
    original={'schema':'t28-three-memory-TU-compiler-observation-1','observation_only':True,'source_commit':value['source_commit']}
    return result,value,commands,policy,original
def derived(count):
    n={'raw_bytes':100,'raw_sha256':'0'*64,'duplicate_events':count,'prospective_role_renames':count,'inverse_manifest_rows':count,
        'unknown_or_mismatched_duplicate_events':0,'normalized_bytes':200,'role_normalization_and_expanded_cap_eligible':True,
        'expanded_role_transport_refused':False,'normalized_AST_admitted':False,'normalized_uncompressed_file_written':False}
    return {'normalization':n},{'expanded_bytes':100,'expanded_sha256':'0'*64}

class Controls(unittest.TestCase):
    def test_exact_source_render_and_original_template_inverse(self):
        value=assignments(ast.parse(ENTRY.read_bytes()))
        self.assertEqual(base64.b64decode(value['POLICY_B64']),(HERE/'source_policy_v1.json').read_bytes())
        self.assertEqual(hashlib.sha256(base64.b64decode(value['NORMALIZER_B64'])).hexdigest(),'6301baede48b9b0f1d3beaef2873e59026f5e9e26135bc2f7ba0a3f76825f941')
        self.assertEqual(hashlib.sha256(base64.b64decode(value['BASE_B64'])).hexdigest(),'b866e14fe3ca210de178aab71f5c8a662e15f818a5ca485095487b005ae51897')
        rendered=TEMPLATE.read_text().replace('__POLICY_B64__',value['POLICY_B64']).replace('__NORMALIZER_B64__',value['NORMALIZER_B64']).replace('__BASE_B64__',value['BASE_B64'])
        self.assertEqual(rendered.encode(),ENTRY.read_bytes())
        inverse=json.loads((HERE/'controller-inverse-v1.json').read_bytes());restored=TEMPLATE.read_text()
        for row in reversed(inverse['edits']):
            at=row['offset'];self.assertEqual(restored[at:at+len(row['new'])],row['new']);restored=restored[:at]+row['old']+restored[at+len(row['new']):]
        self.assertEqual(restored.encode(),Path(inverse['predecessor_template']['path']).read_bytes())

    def test_inherited_quota_audit_physical_and_settled_functions_unchanged(self):
        old=ast.parse((WHOLE/'role-normalization-controller-v2/controller_template.py').read_bytes())
        functions=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        before,after=functions(old),functions(TREE)
        self.assertEqual(set(after)-set(before),{'check_original_observation','check_derived_transport','check_dependencies'})
        self.assertTrue(all(before[name]==after[name] for name in before if name!='main'))

    def test_success_only_original_profile_refuses_v10_failure_and_promotions(self):
        args=observation();gates['check_original_observation'](*args)
        for key,bad in [('accepted',False),('error',{'type':'Refused','message':'duplicate compiler JSON key'}),('after_input_errors',[1]),
            ('compiler_observation_complete',False),('bytecode_cache_present',True),('source_call_admitted',True),('ABI_interpreted',True),
            ('source_names',['wait_ready']),('source_call_count',1),('strict_complete_TU_consumer_passed',True),('native_or_solver_executed',True),
            ('public_proof',True),('current_0_2',True),('full_ticket28',True),('finalization_refusal','late')]:
            changed=list(copy.deepcopy(args));changed[0][key]=bad
            with self.subTest(key=key):
                with self.assertRaises(ValueError):gates['check_original_observation'](*changed)
        changed=list(copy.deepcopy(args));changed[-1]['schema']='old-v10-capture'
        with self.assertRaises(ValueError):gates['check_original_observation'](*changed)

    def test_exact_four_real_zero_exits_and_same_original_coordinates(self):
        for index in range(4):
            for bad in (False,1,-9,None):
                args=list(observation());args[2][index]['returncode']=bad;args[1]['commands']=copy.deepcopy(args[2]);args[3]['original_commands']=copy.deepcopy(args[2])
                with self.assertRaises(ValueError):gates['check_original_observation'](*args)
        args=list(observation());args[1]['original_source_coordinates']=False
        with self.assertRaises(ValueError):gates['check_original_observation'](*args)
        args=list(observation());args[2].pop();args[1]['commands']=copy.deepcopy(args[2]);args[3]['original_commands']=copy.deepcopy(args[2])
        with self.assertRaises(ValueError):gates['check_original_observation'](*args)

    def test_census_is_derived_without_assuming116(self):
        for count in (0,1,2,117,100000):
            transport,wire=derived(count);self.assertIs(gates['check_derived_transport'](transport,wire),transport['normalization'])
        self.assertIsNone(POLICY['expected_duplicate_count']);self.assertIsNone(POLICY['expected_normalized_output_identities'])

    def test_unknown_roles_mismatched_inverse_raw_and_extent_refuse(self):
        for key,bad in [('raw_sha256','1'*64),('raw_bytes',101),('unknown_or_mismatched_duplicate_events',1),('duplicate_events',False),
            ('prospective_role_renames',1),('inverse_manifest_rows',1),('role_normalization_and_expanded_cap_eligible',False),
            ('expanded_role_transport_refused',True),('normalized_AST_admitted',True),('normalized_uncompressed_file_written',True),
            ('normalized_bytes',201326593),('normalized_bytes',0),('duplicate_events',100001)]:
            transport,wire=derived(2);transport['normalization'][key]=bad
            with self.subTest(key=key):
                with self.assertRaises(ValueError):gates['check_derived_transport'](transport,wire)

    def test_known_input_set_covers_every_raw_and_used_dependency(self):
        closure=json.loads((WHOLE/'compiler-memory-capture-v1-actual/closure-stdout-v1.json').read_bytes())
        known=POLICY['physical_inputs'];self.assertEqual(len(known),911)
        for row in [*closure['rows'],*closure['metadata']['component/compiler-observation.json']['inputs'],
            *(row for group in closure['metadata']['component/compiler-observation.json']['groups'] for row in group['dependencies'])]:
            self.assertEqual(known[row['path']],{key:row[key] for key in ('bytes','sha256')})
        self.assertEqual(known[POLICY['original_raw']+'/control/same_thread_memory_v1.cpp'],POLICY['original_source_fixture'])

    def test_complete_runtime_and_dependencies_bracket_one_pass_without_chunk_hashing(self):
        main=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        calls=[ast.unparse(n.func) for n in ast.walk(main) if isinstance(n,ast.Call)]
        self.assertEqual(calls.count("normalizer['compress_normalize']"),1)
        self.assertEqual(calls.count("normalizer['verify_inverse_gzip']"),1)
        self.assertEqual(calls.count("helpers['physical_runtime']"),2)
        self.assertEqual(calls.count('check_dependencies'),2)
        self.assertEqual(calls.count('input_check'),2)
        check=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='check')
        self.assertNotIn('input_check',ast.unparse(check));self.assertNotIn('physical_runtime',ast.unparse(check))
        self.assertNotIn('duplicate compiler JSON key',ast.unparse(main))

    def test_early_caps_exact_stdin_and_closed14_output_namespace(self):
        bootstrap=(HERE/'bootstrap_v1.py').read_bytes();tree=ast.parse(bootstrap);values=assignments(tree)
        self.assertEqual(COMMAND['python_argv'][4].encode(),bootstrap)
        self.assertEqual(COMMAND['remote_shell_command'],shlex.join(COMMAND['remote_argv']))
        self.assertEqual(COMMAND['stdin']['bytes'],len(ENTRY.read_bytes()))
        self.assertEqual(COMMAND['stdin']['sha256'],hashlib.sha256(ENTRY.read_bytes()).hexdigest())
        self.assertEqual(set(values['OUTPUT_PATHS']),{POLICY['output_root']+'/'+name for name in assignments(TREE)['FILES']})
        self.assertEqual(len(values['OUTPUT_PATHS']),14)
        text=bootstrap.decode();self.assertIn('(536870912,536870912)',text);self.assertIn('(950,950)',text)
        self.assertLess(text.index('resource.setrlimit'),text.index('import hashlib'))
        self.assertIn('read('+str(len(ENTRY.read_bytes())+1)+')',text)
        self.assertIn('len(payload)!='+str(len(ENTRY.read_bytes())),text)
        self.assertIn("'"+COMMAND['stdin']['sha256']+"'",text)

    def test_no_actual_or_child_execution(self):self.assertEqual(EVENTS,[])

if __name__=='__main__':unittest.main(verbosity=2)
