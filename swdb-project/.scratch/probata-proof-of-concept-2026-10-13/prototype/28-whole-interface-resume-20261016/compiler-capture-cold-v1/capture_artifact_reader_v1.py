"""2026-10-16 ET. INERT passive V10 artifact reader, no main authorized yet.

This is artifact/token correspondence, not public source/proof acceptance.
A root-owned independent actual outer-guard/role admission remains required.
Never stage this reader in the frozen capture control or mutate capture raw.
"""
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import sys
import time
EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('passive reader forbids '+event)
sys.addaudithook(no_child)
RAW_NAME='probata-resume-20261016-t28-full-tu-2baf722f-v10'
COMMAND_SHA='915ced6467e572a0d204d1fc5d30b45054ae66d554c33dca8ec7f4dfe45c2a35'
POLICY_SHA='8d86faea6d8235c9431acddae4d28e08831afaaca1ebc506e9363d66e8e32517'
ENTRY_SHA='095eee7198167f5e89ae3a64deb2c42e8097951d957a91de0a7c8fd6efb60810'
SOURCE_COMMIT='2baf722fdaa6cba24b859eae3172a6f597417d72'
STAGE=134217728;TOTAL=268435456;RAW=2147483648
class Refused(ValueError):pass
def need(ok,message):
    if not ok:raise Refused(message)
def stable(value):return tuple(getattr(value,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns'))
def pin(path):
    path=Path(path);before=path.lstat();need(path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode),'canonical regular audit input required')
    with path.open('rb') as stream:value=hashlib.file_digest(stream,'sha256').hexdigest()
    need(stable(path.lstat())==stable(before),'audit input changed while hashing')
    return {'path':str(path),'bytes':before.st_size,'sha256':value}
def same(row):need(type(row) is dict and set(row)=={'path','bytes','sha256'} and pin(row['path'])==row,'retained physical pin differs')
def pairs(rows):
    value={}
    for key,item in rows:need(key not in value,'duplicate retained JSON key');value[key]=item
    return value
def document(path,limit=8388608):
    need(Path(path).lstat().st_size<=limit,'bounded metadata document required');before=pin(path)
    def nonfinite(_):raise Refused('nonfinite retained JSON')
    value=json.loads(Path(path).read_bytes(),object_pairs_hook=pairs,parse_constant=nonfinite);need(pin(path)==before,'metadata changed while reading');return value
def load(control,name,policy):
    row={'path':str(control/name),**policy['controller_files'][name]};same(row)
    ns={'__name__':'passive_reviewed_'+name[:-3],'__file__':row['path']};exec(compile(Path(row['path']).read_bytes(),row['path'],'exec'),ns);return ns
class CountHash:
    def __init__(self):self.bytes=0;self.hash=hashlib.sha256()
    def write(self,value):
        need(len(value)<=65536,'reviewed minifier write bound differs');self.bytes+=len(value);need(self.bytes<=STAGE,'minified count cap exceeded');self.hash.update(value);return len(value)
def check_commands(commands,recipe,out):
    need(type(commands) is list and len(commands)==len(recipe)==4,'four complete phases required')
    phases=['caller-preprocess','caller-ast','abi-preprocess','abi-ast']
    for index,(row,expected) in enumerate(zip(commands,recipe)):
        need(row['phase']==expected['phase']==phases[index] and row['argv']==expected['argv'] and row['cwd']==expected['cwd']==str(out)
            and type(row['returncode']) is int and row['returncode']==0,'phase source/argv/cwd/exit differs')
        timeout=row['timeout_seconds'];need(type(timeout) in (int,float) and math.isfinite(timeout) and 0<timeout<=(120 if index==1 else 45),'phase allowance differs')
        need(row['stdout']['path']==expected.get('stdout',str(out/(phases[index]+'.stdout')))
            and row['stderr']['path']==str(out/(phases[index]+'.stderr')),'phase stdout/stderr attribution differs')
        same(row['stdout']);same(row['stderr'])
def inspect(raw,command_path):
    started=time.monotonic();raw=Path(raw);need(raw.is_absolute() and raw.resolve(strict=True)==raw and raw.name==RAW_NAME,'exact original V10 raw required')
    out=raw/'component';control=raw/'control';need(pin(command_path)['sha256']==COMMAND_SHA,'exact V10 command required');command=document(command_path)
    policy_path=control/'linux_compiler_capture_policy_v10.json';need(pin(policy_path)['sha256']==POLICY_SHA,'exact V10 policy required');policy=document(policy_path)
    need(policy['entry_sha256']==ENTRY_SHA and policy['raw_name']==RAW_NAME and policy['source_commit']==SOURCE_COMMIT,'exact source/entry namespace required')
    controls={Path(row['path']).name:{k:row[k] for k in ('bytes','sha256')} for row in command['controller_inputs']}
    need(len(controls)==len(command['controller_inputs'])==15 and {k:v for k,v in controls.items() if k!=policy_path.name}==policy['controller_files'],'exact15 source controls required')
    need({p.name for p in control.iterdir()}==set(controls)|{'include'},'frozen control membership differs')
    control_pins=[]
    for name,record in controls.items():row={'path':str(control/name),**record};same(row);control_pins.append(row)
    result=document(out/'result.json');need(result['accepted'] is True and result['error'] is None and result['after_input_errors']==[]
        and result['bytecode_cache_present'] is False and 'finalization_refusal' not in result,'only settled complete capture may pass artifact review')
    need(type(result['wall_seconds']) in (int,float) and math.isfinite(result['wall_seconds']) and 0<=result['wall_seconds']<=165,'capture entry wall bound differs')
    need(not os.path.lexists(raw/'entry-source-cache'),'capture bytecode cache must remain absent')
    manifest=document(out/'artifact-manifest.json');paths=[];manifest_pins=[]
    for row in manifest:
        relative=row['relative'];need(type(relative) is str and str(Path(relative))==relative and not Path(relative).is_absolute() and '..' not in Path(relative).parts,'manifest relative path malformed')
        expected={'path':str(out/relative),'bytes':row['bytes'],'sha256':row['sha256']};need(row['path']==expected['path'],'manifest path differs');same(expected)
        need(expected['bytes']<=STAGE,'retained file exceeds capture cap');paths.append(relative);manifest_pins.append(expected)
    need(len(paths)==len(set(paths)) and paths==sorted(paths,key=lambda path:Path(path).parts),'manifest order/identity differs')
    actual=[]
    for path in sorted(out.rglob('*')):
        mode=path.lstat().st_mode
        need(stat.S_ISREG(mode) or stat.S_ISDIR(mode),'special component artifact refused')
        if stat.S_ISREG(mode) and path.name!='artifact-manifest.json':actual.append(str(path.relative_to(out)))
    need(paths==actual,'complete manifest membership differs')
    used=sum(pin(path)['bytes'] for path in raw.rglob('*') if path.is_file());need(used<=TOTAL,'complete raw total exceeds unchanged allowance')
    observation=document(out/'compiler-observation.json');need(observation['source_commit']==SOURCE_COMMIT and observation['original_source_coordinates'] is True,'original same-TU provenance differs')
    need(observation['timing_tcb']==policy['capture_recipe']['dependency_timing_tcb'],'source timing premise differs')
    commands=observation['commands'];check_commands(commands,policy['capture_recipe']['commands'],out)
    need(document(out/'commands.json')==commands,'retained command lists differ')
    original=[pin(control/name) for name in ('source_call_fixture_v2.cpp','compiler_abi_probe_v1.cpp','m5ops.h')]
    project=Path(policy['source_project'])
    original += [{'path':str(project/row['relative']),'bytes':row['bytes'],'sha256':row['sha256']} for row in policy['source_inputs']]
    need(observation['inputs']==original,'source/probe/stub/two-header/inventory input membership differs')
    for row in original:same(row)
    entry=load(control,'linux_compiler_capture_v10.py',policy)
    entry['check_derived_stub'](control)
    helpers=entry['original_helpers'](control/'linux_native86_entry_v4.py')
    groups=document(out/'used-inputs.json');need([group['label'] for group in groups]==['caller','abi'],'two complete dependency groups required')
    observed_groups=observation['groups'];need(len(observed_groups)==2,'two observed original-TU groups required')
    for group,observed in zip(groups,observed_groups):
        original_group={k:v for k,v in group.items() if k not in {'minified_ast','token_identity'}}
        need(original_group==observed,'before/after original dependency observations differ')
        label=group['label'];deps=group['dependencies'];names=[row['path'] for row in deps]
        required={str(control/('source_call_fixture_v2.cpp' if label=='caller' else 'compiler_abi_probe_v1.cpp')),
            str(control/'include/gem5/m5ops.h'),str(project/'apps/dx100/benchmarks/API/MAA.hpp'),str(project/'apps/dx100/benchmarks/API/MAA_gem5.hpp')}
        need(len(names)==len(set(names)) and required<=set(names),'closed used-header census differs')
        for row in deps:same(row)
        for field,suffix in (('frozen','.ii'),('preprocess_dependency','.d'),('ast_dependency','.ast.d')):
            need(group[field]['path']==str(out/(label+suffix)),'frozen/dep artifact identity differs');same(group[field])
        before_names=helpers['make_dependencies'](Path(group['preprocess_dependency']['path']).read_text(),label,out)
        after_names=helpers['make_dependencies'](Path(group['ast_dependency']['path']).read_text(),label+'-ast',out)
        need(before_names==after_names==names,'independently parsed depfile membership differs')
        need(group['ast']==commands[1 if label=='caller' else 3]['stdout'],'compiler stdout/group attribution differs')
    receipt=document(out/'caller.ast.gzip.json');identity=document(out/'caller.ast.identity.json')
    need(groups[0]['expanded_stream_receipt']==pin(out/'caller.ast.gzip.json') and groups[0]['token_identity']==pin(out/'caller.ast.identity.json')
        and groups[0]['minified_ast']==pin(out/'caller.ast.minified.json'),'complete stream/minified artifact attribution differs')
    need(commands[1]['lossless_stdout']==receipt,'zero-exit compiler/raw gzip receipt differs')
    for phase in ('before','after'):need(document(raw/('capture-zlib-'+phase+'.json'))==policy['zlib_binding'],'capture zlib observation differs')
    zlib_module,live_zlib=entry['bind_zlib'](policy)
    codec=load(control,'lossless_gzip_v2.py',policy);minifier=load(control,'strict_minify_v2.py',policy)
    def bounded_check():need(time.monotonic()-started<165,'passive artifact replay deadline exceeded')
    sink=CountHash()
    with (out/'caller.ast.json.gz').open('rb') as compressed:
        decoded=codec['DecodeReader'](zlib_module,compressed,receipt,expanded_limit=RAW,compressed_limit=STAGE,check=bounded_check)
        replay=minifier['minify'](decoded,sink,raw_limit=RAW,retained_limit=STAGE,check=bounded_check)
        need(decoded.verified and replay==identity,'complete original gzip/token-preserving identity replay differs')
    need((sink.bytes,sink.hash.hexdigest())==(groups[0]['minified_ast']['bytes'],groups[0]['minified_ast']['sha256']),'retained complete minified JSON differs from original tokens')
    closed=load(control,'closed_python_surface.py',policy)
    runtime=helpers['physical_runtime'](policy,type('Closed',(),closed))
    need(document(raw/'capture-runtime-before.json')==runtime and document(raw/'capture-runtime-after.json')=={'runtime':runtime,'after_errors':[]},'live physical runtime and capture observations differ')
    need(document(out/'inputs-before.json')['source']==original and document(out/'inputs-before.json')['recipe']==policy['capture_recipe'],'original compiler recipe differs')
    launch=document(raw/'launch.json');need(launch['command']==command['argv'] and launch['source_commit']==SOURCE_COMMIT and Path(launch['source']).resolve()==project.parent,'outer launch source/argv differs')
    for key,value in {'rss_cap_bytes':4294967296,'workers':1,'timeout_seconds':180,'node':1}.items():need(launch[key]==value,'outer launch declared profile differs')
    for name,expected in policy['guard_files'].items():need(pin(raw/name)['sha256']==expected==launch['reviewed_wrapper_reuse'][name],'exact adapted guard binding differs')
    role=document(raw/'capture-linux-role.json');need(role['launch']==pin(raw/'launch.json') and role['Mac_counted_claim'] is False,'captured Linux role launch attribution differs')
    need(role['derived_marker']==hashlib.sha256(json.dumps({'launch':role['launch'],'live':role['live']},sort_keys=True).encode()).hexdigest(),'captured launch/live marker differs')
    live=role['live'];need(live['lease']=='mbit10-evaluation-node1' and live['memory_policy']=='bind:1' and live['fd9_matches_lease'] is True,'captured live lane differs')
    prepared=document(out/'source-preparation.json');calls=prepared['calls'];names={row['name'] for row in calls}
    declarations=document(project/'tests/fixtures/proof/dx100/interface-declarations-e4fc4af.json')
    source_names={row['name'] for row in declarations['declarations']} if type(declarations) is dict else {row['name'] for row in declarations}
    need(names==source_names and len(names)==26 and {row['formal_arity'] for row in calls if row['name']=='get_new_reg'}=={0,1},'all26 names and both register overloads required')
    need(prepared['schema']=='whole-interface-original-tu-preparation-2' and prepared['full_tu_identity']==identity
        and prepared['raw_full_tu_sha256']==receipt['expanded_sha256'] and prepared['parser_full_tu_sha256']==groups[0]['minified_ast']['sha256']
        and prepared['compiler_capture_receipt_sha256']==pin(out/'compiler-observation.json')['sha256'],'original/minified/normalized identities conflated')
    need(prepared['original_source_sha256']==original[0]['sha256'] and prepared['original_probe_sha256']==original[1]['sha256'],'prepared source/probe identity differs')
    abi=prepared['abi_observation']['abi'];need(abi['byte_order']=='little' and abi['int_bits']==32 and abi['pointer_bits']==64
        and abi['sizes']==[4,4,4,8,8,8] and abi['alignments']==[4,4,4,8,8,8],'prepared ABI domain differs')
    for row in control_pins+manifest_pins+original:same(row)
    need(entry['bind_zlib'](policy)[1]==live_zlib and helpers['physical_runtime'](policy,type('Closed',(),closed))==runtime,'passive replay runtime changed')
    need(not EVENTS and not os.path.lexists(raw/'entry-source-cache'),'passive replay child/cache refusal')
    return {'schema':'v10-capture-artifact-token-audit-1','artifact_and_complete_token_correspondence':True,
        'raw_root':str(raw),'command_sha256':COMMAND_SHA,'policy_sha256':POLICY_SHA,'entry_sha256':ENTRY_SHA,
        'original_source_sha256':original[0]['sha256'],'raw_bytes':receipt['expanded_bytes'],'raw_sha256':receipt['expanded_sha256'],
        'gzip_bytes':receipt['compressed_bytes'],'gzip_sha256':receipt['compressed_sha256'],'minified_bytes':identity['minified_bytes'],'minified_sha256':identity['minified_sha256'],
        'identity_sha256':pin(out/'caller.ast.identity.json')['sha256'],'normalized_graph_sha256':prepared['normalized_full_tu_sha256'],
        'source_names':len(names),'source_calls':len(calls),'register_overloads':[0,1],'compiler_phases':4,'control_files':15,
        'used_header_counts':[len(group['dependencies']) for group in groups],'component_manifest_files':len(paths),'retained_total_bytes':used,
        'capture_wall_seconds':result['wall_seconds'],'passive_wall_seconds':time.monotonic()-started,'child_events':EVENTS,
        'source_body_ABI_call_recomputation':False,'public_source_or_proof_admission':False,'root_actual_outer_guard_reconciliation':'separate required root-owned receipt',
        'hardware_refinement_or_current_0_2_or_full_ticket28':False}
if __name__=='__main__':
    need(len(sys.argv)==3 and __debug__ and sys.flags.isolated and sys.dont_write_bytecode,'isolated no-bytecode passive reader requires raw and exact command')
    print(json.dumps(inspect(sys.argv[1],Path(sys.argv[2])),sort_keys=True,allow_nan=False))
