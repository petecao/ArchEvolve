"""2026-10-16 ET: inert no-child ingress gate controls, no actual record use."""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import stat
from types import SimpleNamespace
import unittest

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'proposed/normalized_capture_ingress_v1.py'
module=ast.parse(SOURCE.read_bytes())
FUNCTIONS={'exact','fixed_pin','same_bytes','stream_stable','original_refusal','original_closure','execution_gate','transform_gate','output_closure'}
nodes=[node for node in module.body if isinstance(node,ast.Assign) or isinstance(node,ast.FunctionDef) and node.name in FUNCTIONS]
def need(ok,message):
    if not ok:raise ValueError(message)
env={'need':need,'math':math,'re':re,'stat':stat}
exec(compile(ast.Module(nodes,type_ignores=[]),str(SOURCE),'exec'),env)

def pin(name,sha='0'*64,size=1):return {'path':env['ROOT']+'/'+name,'bytes':size,'sha256':sha}

def execution():
    selected={key:pin(key) for key in ('controller','command','bootstrap','stdout','stderr')}
    selected['stderr']['bytes']=0
    value={'schema':'passive-transform-root-execution-1','controller':copy.deepcopy(selected['controller']),
        'command':copy.deepcopy(selected['command']),'bootstrap':copy.deepcopy(selected['bootstrap']),
        'stdin_sha256':env['CONTROLLER_SHA'],'output_root':env['ROOT'],'returncode':0,'local_refusal':None,
        'timed_out':False,'out_of_memory':False,'wall_seconds':1.0,'stdout':copy.deepcopy(selected['stdout']),
        'stderr':copy.deepcopy(selected['stderr'])}
    return value,selected

def settled():
    return {'schema':'passive-paired-type-gzip-transform-result-2','normalization_complete':True,
        'completion_requires_controller_zero_exit_and_settled_publication':True,'original_capture_accepted':False,
        'original_capture_refusal':{'type':'Refused','message':'duplicate compiler JSON key'},
        'source_call_ABI_public_or_full28_admission':False,'compiler_or_native_or_solver_executed':False,
        'selected_inputs_unchanged':True,'output_root':env['ROOT'],'expanded_normalized_limit_bytes':env['EXPANDED'],
        'physical_file_limit_bytes':env['FILE'],'aggregate_retained_limit_bytes':268435456,'wall_seconds':1.0}

def outputs():
    names={'control/controller.py':'controller','control/normalizer.py':None,'control/census.json':'complete_census','control/policy.json':'policy',
        'component/inputs-before.json':None,'component/inputs-after.json':None,'component/caller.normalized.json.gz':'normalized_gzip',
        'component/rename-manifest.jsonl':'manifest','component/transport.json':'transport','component/inverse.json':'inverse'}
    rows=[pin(name,env['NORMALIZER_SHA'] if name=='control/normalizer.py' else '0'*64) for name in names]
    selected={role:copy.deepcopy(row) for (name,role),row in zip(names.items(),rows) if role}
    selected['result']=pin('result.json')
    policy={'physical_inputs':{'/inert/input'+str(i):{'bytes':1,'sha256':'0'*64} for i in range(36)}}
    value=settled();value['outputs']=rows
    value['input_pins']=[{'path':path,**row} for path,row in policy['physical_inputs'].items()]
    return value,selected,policy

class Controls(unittest.TestCase):
    def reject(self,function,value,*other):
        with self.assertRaises((ValueError,KeyError,TypeError)):env[function](value,*other)

    def test_root_execution_requires_settled_zero_exit(self):
        value,selected=execution();env['execution_gate'](value,selected)
        for key,bad in [('returncode',1),('returncode',True),('timed_out',True),('out_of_memory',True),('local_refusal','late publication'),
            ('wall_seconds',float('nan')),('wall_seconds',float('inf')),('wall_seconds',961),('wall_seconds',True),('output_root','/wrong')]:
            with self.subTest(key=key,bad=bad):
                changed=copy.deepcopy(value);changed[key]=bad;self.reject('execution_gate',changed,selected)

    def test_relocated_staged_receipts_keep_exact_bytes(self):
        value,selected=execution()
        for key in ('controller','command','bootstrap','stdout','stderr'):selected[key]['path']='/inert/staged/'+key
        env['execution_gate'](value,selected)
        for key in ('controller','command','bootstrap','stdout','stderr'):
            changed=copy.deepcopy(selected);changed[key]['sha256']='f'*64;self.reject('execution_gate',value,changed)
        self.assertFalse(env['same_bytes']({},{}))

    def test_original_failure_is_closed(self):
        value={'accepted':False,'error':{'type':'Refused','message':'duplicate compiler JSON key'},'after_input_errors':[],
            'bytecode_cache_present':False,'source_call_count':0,'source_names':[],'public_proof':False,'current_0_2':False,'full_ticket28':False}
        env['original_refusal'](value)
        for key,bad in [('accepted',True),('error',{'type':'Refused','message':'other'}),('after_input_errors',['changed']),
            ('bytecode_cache_present',True),('source_call_count',1),('source_names',['invented']),('public_proof',True),('current_0_2',True),
            ('full_ticket28',True),('finalization_refusal','late')]:
            changed=copy.deepcopy(value);changed[key]=bad;self.reject('original_refusal',changed)

    def test_complete_boolean_alone_cannot_pass(self):
        self.reject('transform_gate',{'normalization_complete':True})
        value=settled();env['transform_gate'](value)
        for key,bad in [('completion_requires_controller_zero_exit_and_settled_publication',False),('original_capture_accepted',True),
            ('compiler_or_native_or_solver_executed',True),('selected_inputs_unchanged',False),('source_call_ABI_public_or_full28_admission',True),
            ('wall_seconds',900),('expanded_normalized_limit_bytes',536870912)]:
            changed=copy.deepcopy(value);changed[key]=bad;self.reject('transform_gate',changed)

    def test_complete_output_and_selected_role_closure(self):
        value,selected,policy=outputs();env['output_closure'](value,selected,policy)
        for mutate in (lambda x:x['outputs'].pop(),lambda x:x['outputs'].append(copy.deepcopy(x['outputs'][0])),
            lambda x:x['outputs'][0].update(path=env['ROOT']+'/unexpected'),lambda x:x['input_pins'].pop(),
            lambda x:x['input_pins'].reverse(),lambda x:x['input_pins'][0].update(sha256='f'*64)):
            changed=copy.deepcopy(value);mutate(changed);self.reject('output_closure',changed,selected,policy)
        for role in ('controller','policy','complete_census','normalized_gzip','manifest','transport','inverse'):
            changed=copy.deepcopy(selected);changed[role]['sha256']='f'*64;self.reject('output_closure',value,changed,policy)

    def test_legacy_complete_capture_is_only_a_callthrough(self):
        predecessor=HERE.parent/'production-route-v3/proposed/swdb/dx100_checked_source.py'
        tree=ast.parse(predecessor.read_bytes())
        old=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='complete_capture')
        successor=next(node for node in module.body if isinstance(node,ast.FunctionDef) and node.name=='complete_capture')
        legacy=next(node for node in successor.body if isinstance(node,ast.If))
        self.assertEqual(ast.unparse(legacy.body[0]),'return source.complete_capture(policy, reads, project)')
        self.assertEqual(hashlib.sha256(ast.get_source_segment(predecessor.read_text(),old).encode()).hexdigest(),
            'cdfd56f5503d4068abe31037a2d121e5a81bfdd86889676a4563b25f37a94241')

    def test_closed_original_paths_and_input_membership(self):
        names={'policy':'control/linux_compiler_capture_policy_v10.json','result':'component/result.json',
            'observation':'component/compiler-observation.json','runtime_before':'capture-runtime-before.json',
            'runtime_after':'capture-runtime-after.json','zlib_before':'capture-zlib-before.json','zlib_after':'capture-zlib-after.json',
            'gzip_receipt':'component/caller.ast.gzip.json','compressed_tu':'component/caller.ast.json.gz','abi':'component/abi.ast.json',
            'probe':'control/compiler_abi_probe_v1.cpp','source':'control/source_call_fixture_v2.cpp','source_after':'source-after.json'}
        original={key:{'path':env['ORIGINAL_ROOT']+'/'+name} for key,name in names.items()}
        controls={name:{'bytes':1,'sha256':'0'*64} for name in ('source_call_fixture_v2.cpp','compiler_abi_probe_v1.cpp','m5ops.h')}
        policy={'controller_files':controls,'source_project':'/inert/project','source_inputs':[{'relative':'MAA.hpp','bytes':1,'sha256':'1'*64}]}
        observation={'inputs':[{'path':env['ORIGINAL_ROOT']+'/control/'+name,**row} for name,row in controls.items()]+
            [{'path':'/inert/project/MAA.hpp','bytes':1,'sha256':'1'*64}]}
        env['original_closure'](original,policy,observation)
        for key in names:
            changed=copy.deepcopy(original);changed[key]['path']='/inert/other';self.reject('original_closure',changed,policy,observation)
        for mutate in (lambda x:x['inputs'].pop(),lambda x:x['inputs'].reverse(),lambda x:x['inputs'][0].update(sha256='f'*64)):
            changed=copy.deepcopy(observation);mutate(changed);self.reject('original_closure',original,policy,changed)

    def test_chunk_shapes_refuse_alias_special_and_extent(self):
        state={'alias':False,'mode':stat.S_IFREG,'size':1}
        class FakePath:
            def __init__(self,path):self.path=path
            def lstat(self):return SimpleNamespace(st_mode=state['mode'],st_size=state['size'])
            def resolve(self,strict):return FakePath('/wrong' if state['alias'] else self.path)
            def __eq__(self,other):return isinstance(other,FakePath) and self.path==other.path
        env['Path']=FakePath
        row={'path':'/inert/gzip','bytes':1};env['stream_stable']([row])
        for key,bad in [('alias',True),('mode',stat.S_IFLNK),('mode',stat.S_IFIFO),('size',2)]:
            old=state[key];state[key]=bad;self.reject('stream_stable',[row]);state[key]=old

    def test_exact_copied_helpers_and_no_project_execution(self):
        helper=HERE/'proposed/closed_python_surface.py'
        self.assertEqual(hashlib.sha256(helper.read_bytes()).hexdigest(),env['CLOSED_SHA'])
        native=HERE.parent/'linux_native86_entry_v4.py'
        old=next(n for n in ast.parse(native.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='make_dependencies')
        new=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='make_dependencies')
        self.assertEqual(ast.dump(old,include_attributes=False),ast.dump(new,include_attributes=False))
        self.assertFalse(any(isinstance(n,ast.If) and ast.unparse(n.test).startswith('__name__') for n in module.body))

if __name__=='__main__':unittest.main(verbosity=2)
