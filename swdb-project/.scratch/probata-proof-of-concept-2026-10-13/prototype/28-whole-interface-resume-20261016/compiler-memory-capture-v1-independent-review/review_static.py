"""2026-10-16 ET. Independent static pins/AST/inverse review only.

No target imports, main calls, controls, compiler, native, SSH or network runs.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
NEW=WHOLE/'compiler-memory-capture-v1'
OLD=WHOLE/'compiler-capture-v10'
def pin(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def doc(path):return json.loads(path.read_bytes())
packet_path=NEW/'memory-capture-source-packet-v1.json'
assert pin(packet_path)['sha256']=='74b8bbc1b5276c5c84916073675a09dcc663e7548c5983a853fcc04c75fccd69'
packet=doc(packet_path)
rows=[*packet['controller_inputs'],*[packet[key] for key in ('command','controls','fixture_packet','inverse','predecessor_packet','preparation')],packet['validation']['log']]
for row in rows:assert pin(Path(row['path']))==row,row['path']
entry=NEW/'linux_memory_capture_v1.py'
assert pin(entry)['sha256']=='685ba0fd66de6fb891e634b616fd47d36bffed2fbfa03ecc90ba0925985933a5'
inverse=doc(NEW/'memory-capture-v1-inverse.json');text=entry.read_text()
for change in reversed(inverse['entry_edits']):
    at=change['offset'];assert text[at:at+len(change['new'])]==change['new']
    text=text[:at]+change['old']+text[at+len(change['new']):]
old_entry=OLD/'linux_compiler_capture_v10.py';assert text.encode()==old_entry.read_bytes()
def functions(path):return {node.name:ast.dump(node,include_attributes=False) for node in ast.parse(path.read_bytes()).body if isinstance(node,ast.FunctionDef)}
before,after=functions(old_entry),functions(entry)
for name in inverse['unchanged_functions']:assert before[name]==after[name],name
def restore(value,changes):
    value=copy.deepcopy(value)
    for change in reversed(changes):
        target=value
        for key in change['path'][:-1]:target=target[key]
        key=change['path'][-1]
        if change.get('added'):
            assert target[key]==change['new'];del target[key]
        elif change.get('removed'):
            assert key not in target;target[key]=change['old']
        else:
            assert target[key]==change['new'];target[key]=change['old']
    return value
policy=doc(NEW/'linux_memory_capture_policy_v1.json');command=doc(NEW/'linux_memory_capture_command_v1.json')
old_policy=doc(OLD/'linux_compiler_capture_policy_v10.json');old_command=doc(OLD/'linux_compiler_capture_command_v10.json')
assert restore(policy,inverse['policy_edits'])==old_policy
assert restore(command,inverse['command_edits'])==old_command
for name in ('budgets','compiler','native_runtime','startup_roles','python_surface_binding','guard_files','zlib_binding','source_inputs',
    'runtime_files','linux_header_surfaces','disk_floor_bytes','home','path','python','source_commit','source_project','node'):
    assert policy[name]==old_policy[name],name
assert command['recipe']==policy['capture_recipe']
assert policy['budgets']=={'whole_seconds':180,'entry_seconds':165,'rss_bytes':4294967296,'stage_bytes':134217728,'total_bytes':268435456}
assert policy['node']==command['node']==1 and policy['source_commit']=='2baf722fdaa6cba24b859eae3172a6f597417d72'
assert command['root_guard']==old_command['root_guard'] and command['root_reviewed_wrapper_hashes']==policy['guard_files']
assert command['root_required_environment']=={ 'PROBATA_OUTPUT':command['raw_root'],
    'SWDB_VERIFIER_LOCK':command['raw_root']+'/verifier.lock','SWDB_VERIFIER_RSS_CAP_BYTES':'4294967296'}
assert command['run_environment_unset']==['LIBRARY_PATH']
assert command['argv']==[policy['python'],'-I','-B',command['raw_root']+'/control/linux_memory_capture_v1.py',policy['source_project'],
    command['raw_root'],command['raw_root']+'/control/linux_memory_capture_policy_v1.json',pin(NEW/'linux_memory_capture_policy_v1.json')['sha256']]
assert command['raw_root'].endswith('/probata-resume-20261016-t28-memory-tu-2baf722f-v1')
controls={Path(row['path']).name:{key:row[key] for key in ('bytes','sha256')} for row in command['controller_inputs']}
assert len(controls)==len(command['controller_inputs'])
assert controls.pop('linux_memory_capture_policy_v1.json')=={key:pin(NEW/'linux_memory_capture_policy_v1.json')[key] for key in ('bytes','sha256')}
assert controls==policy['controller_files']
assert controls['same_thread_memory_v1.cpp']=={'bytes':3258,'sha256':'55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'}
assert not {'strict_minify_v2.py','whole_interface_v4.py'}&set(controls)
assert sum(row['bytes'] for row in command['controller_inputs'])==packet['controls_bytes']==896371<1048576
recipe=policy['capture_recipe'];phases=recipe['commands'];old_phases=copy.deepcopy(old_policy['capture_recipe']['commands'])
for phase in old_phases:
    phase.update({key:value.replace(old_policy['raw_name'],policy['raw_name']) for key,value in phase.items() if type(value) is str})
    phase['argv']=[value.replace(old_policy['raw_name'],policy['raw_name']) for value in phase['argv']]
for i,(old,new) in enumerate(zip(old_phases,phases)):
    repaired=copy.deepcopy(new)
    if i<2:repaired['argv']=[value.replace('/same_thread_memory_v1.cpp','/source_call_fixture_v2.cpp') for value in repaired['argv']]
    assert repaired==old,(i,repaired,old)
assert '-ast-dump-filter' not in ' '.join(phases[1]['argv']) and '-ast-dump=json' in phases[1]['argv']
assert phases[1]['argv'][-1]==command['raw_root']+'/control/same_thread_memory_v1.cpp'
assert phases[3]['same_parse_id_scope']=='ABI literals only, IDs never joined'
assert recipe['lossless_caller_stdout']=={'codec':'gzip-single-member','expanded_limit':2147483648,'retained_file_limit':134217728,
    'unfiltered_original_frontend_stdout':True,'expanded_memory_is_not_retained_disk_bytes':True,'raw_full_DOM_materialized':False,
    'AST_or_ABI_interpreted_in_measurement':False,
    'mandatory_downstream':'strict complete-stream role normalization/inverse, original source/runtime/dependency closure, same-TU/ABI/call/body admission'}
assert recipe['caller_ast_phase_seconds']==120 and recipe['other_phase_seconds']==45
main=next(n for n in ast.parse(entry.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='main')
calls={ast.unparse(n.func) for n in ast.walk(main) if isinstance(n,ast.Call)}
assert not {'adapter.prepare_unit','binder.inventory','minifier.minify','codec.DecodeReader','check_prepared'}&calls
assert 'complete_observation' in calls
log=(NEW/'pure-memory-capture-v1-controls.log').read_text();retained=json.loads(log.splitlines()[-1])
assert retained==packet['validation']['report'] and retained['tests']==10 and retained['errors']==retained['failures']==retained['skips']==0 and retained['child_events']==[]
value={'schema':'independent-memory-capture-static-review-1','date':'2026-10-16 ET','verdict':'PASS_SOURCE_ONLY_COMPILER_OBSERVATION_PACKET',
    'reviewer_scope':'Independent complete entry/preparation/control-source reading plus metadata/AST/hash/inverse checks; no target execution',
    'packet':pin(packet_path),'entry':pin(entry),'review_source':pin(Path(__file__)),'policy':pin(NEW/'linux_memory_capture_policy_v1.json'),
    'command':pin(NEW/'linux_memory_capture_command_v1.json'),'inverse':pin(NEW/'memory-capture-v1-inverse.json'),
    'pin_occurrences_checked':len(rows),'unique_physical_paths':len({row['path'] for row in rows}),
    'entry_inverse_edits':len(inverse['entry_edits']),'policy_inverse_edits':len(inverse['policy_edits']),
    'command_inverse_edits':len(inverse['command_edits']),'unchanged_function_ASTs':inverse['unchanged_functions'],
    'checks':{'full_predecessor_text_and_AST_reconstructed':True,'all_JSON_inverse_old_new_claims_verified':True,
        'complete_original_caller_TU_no_filter_or_frozen_offset_join':True,'separate_ABI_literals_never_ID_joined':True,
        'exact_memory_source_55b9_and_two_caller_recipe_substitutions':True,'node1_source2baf_and_runtime_role_guard_binding_consistent':True,
        'new_success_is_four_zero_exit_observation_only':True,'dependency_runtime_source_control_and_finalization_guards_unchanged':True,
        'bounded_2GiB_expanded_stream_128MiB_file_256MiB_aggregate_1MiB_reserve':True,
        '165s_entry_180s_4GiB_guard_and_120s_clipped_AST_phase':True,'root_must_unset_LIBRARY_PATH_and_match_exact_wrapper_hashes':True},
    'retained_controls':{'tests':10,'errors':0,'failures':0,'skips':0,'rerun_by_reviewer':False},'findings':[],
    'not_established':['fresh source/runtime/lane/environment state','actual compiler exits or complete output','strict compiler JSON role grammar/inverse',
        'AST/ABI/source/call/body/model/native/public acceptance','full ticket28 acceptance'],
    'no_project_import_tests_SSH_compiler_native_solver_or_main_execution':True}
path=HERE/'independent-memory-capture-source-review-v1.json'
with path.open('x') as stream:stream.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
print(json.dumps(pin(path),sort_keys=True))
