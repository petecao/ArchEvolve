"""2026-10-16 ET. INERT normalized-gzip ingress proposal, never admission.

Integrate only through a fresh producer manifest/source policy. The existing
source.complete_capture function remains byte-identical as the legacy branch.
No compiler/child/source program is run here. A guarded DOM allocation may fail.
"""
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import stat

from swdb import dx100_checked_source as source
from swdb._dx100_whole import lossless_gzip_v2 as codec
from swdb._dx100_whole import role_normalized_gzip_v2 as normalizer
from swdb._dx100_whole import closed_python_surface as closed
from swdb._dx100_whole import normalized_compiler_adapter_v1 as normalized_compiler

KIND='complete-original-tu-paired-type-gzip-2'
ORIGINAL_POLICY_SHA='8d86faea6d8235c9431acddae4d28e08831afaaca1ebc506e9363d66e8e32517'
ORIGINAL_RESULT_SHA='404a0c416e893e9827fe313932f1fbec73652150b02bffb57f595af373310064'
CENSUS_SHA='df800e08c89abd76ef0ea7e713af9fd52315ae873accc8ea54ab5a760fa8a41b'
CONTROLLER_SHA='e37e893b31b9b0be5f1cd2a5953998393d6040ed2c0c2d45434012727673aa54'
COMMAND_SHA='d8b6d6815412273c40c00c3cd456c4635d355d25d96c42099869b77616e00c03'
BOOTSTRAP_SHA='880acab0e36c5a3b3a50cf29da39ab9f93198f5dfa106d8b18b61c7d9425f627'
TRANSFORM_POLICY_SHA='c9d01e061d2a8263de775e18259a4d6961d6ce8ca8bfdfdbe5ad71473b496d39'
ROOT_EXECUTION_SHA='77e31a0c6541b6162450afbef5f7113148409dd6c346501815e88197ddb40d3a'
TRANSFORM_RESULT_SHA='387215380fc35422ec92ff0d751421a8d7e29a05555b3efa6c1169d9966f16a1'
CLOSED_SHA='748423c27ac8c1f9810c08d3f0ffc71548da703b4b4f95cedc31d4f8bc0418af'
NORMALIZED_COMPILER_SHA='4bdeb0b2761fcc9b3721ee770d8eb8b33534ec7df22cc07cc42f1345b5bd285f'
NORMALIZER_SHA='6301baede48b9b0f1d3beaef2873e59026f5e9e26135bc2f7ba0a3f76825f941'
CODEC_SHA='aae4a423216fcdca6b16f9eba370ec4c83615ed61ae79dd4b3d09e3bed1702ef'
RAW_SHA='cd7f4fa566146b9b061c2084b52b1143efc054d4c4d75cbe4f7911c81e326622'
ORIGINAL_GZIP_SHA='1e01a023699d56da8054533db08de4370e4cd9425b414d1bb772a0efaca3891b'
TOKEN_SHA='fa44d97fbaff20b5b16300d39128bb29e41d9600ba7db57202b50be09368f366'
NORMALIZED_SHA='1f0616302273d146fc88e1c676d25c41230432ee8ec259a92ae65f8fbb5755a3'
ROOT='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2'
ORIGINAL_ROOT='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10'
EXPANDED=201326592
FILE=134217728


def need(value,message):source.need(value,message)
def exact(value,keys,message):need(type(value) is dict and set(value)==set(keys),message)
def fixed_pin(row,expected,message):need(type(row) is dict and row.get('sha256')==expected,message)
def same_bytes(left,right):
    return (type(left) is dict and type(right) is dict and type(left.get('bytes')) is int and left['bytes']>=0
        and type(left.get('sha256')) is str and re.fullmatch('[0-9a-f]{64}',left['sha256']) is not None
        and all(left.get(key)==right.get(key) for key in ('bytes','sha256')))


def stream_stable(rows):
    """Cheap per-chunk shapes; full runtime/content checks bracket the decoder."""
    for row in rows:
        path=Path(row['path']);metadata=path.lstat()
        need(path.resolve(strict=True)==path and stat.S_ISREG(metadata.st_mode) and metadata.st_size==row['bytes'],
            'physical normalized stream input shape changed')


def make_dependencies(text, target, cwd):
    """Closed Make syntax copied from reviewed memory53 preparation entry."""
    if not text.startswith(target + ":"):
        raise ValueError("dependency target differs")
    text = text[len(target) + 1:]
    result, token, index = [], "", 0
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 1
            if index >= len(text): raise ValueError("truncated dependency escape")
            char = text[index]
            if char == "\n":
                index += 1
                continue
            if char not in " \t#\\:": raise ValueError("unsupported dependency escape")
            token += char
        elif char in "$#": raise ValueError("dependency expansion/comments refused")
        elif char.isspace():
            if token:
                result.append(token)
                token = ""
        else: token += char
        index += 1
    if token: result.append(token)
    if not result: raise ValueError("empty dependency set")
    return sorted({str((Path(cwd) / value).resolve(strict=True)) for value in result})


def physical_runtime(policy,reads):
    """Current physical closure; historical process/loader observations stay TCB.

    This is the reviewed native physical_runtime recipe with all regular inputs
    additionally registered in Inputs for the final content recheck. The exact
    closed helper verifies its own full Python membership/alias/absence surface.
    """
    python=closed.verify_python_metadata(policy['python_surface_binding'])
    def current(path,expected=None):
        path=Path(path)
        if expected is None:
            with path.open('rb') as stream:expected=hashlib.file_digest(stream,'sha256').hexdigest()
        row={'path':str(path),'bytes':path.lstat().st_size,'sha256':expected}
        reads.absolute(row,retain=False)
        return row
    for path,expected in policy['runtime_files'].items():current(path,expected)
    headers=policy['linux_header_surfaces']
    need(set(headers)=={'libc++','clang-resource'},'two exact LLVM header surfaces required')
    for header in headers.values():
        root=Path(header['path'])
        need(root.resolve(strict=True)==root and not root.is_symlink() and root.is_dir(),'physical LLVM header root required')
        rows=[]
        for path in sorted(root.rglob('*')):
            mode=path.lstat().st_mode
            if stat.S_ISDIR(mode):continue
            need(stat.S_ISREG(mode),'nonregular LLVM header input')
            row=current(path)
            rows.append({'relative':str(path.relative_to(root)),'bytes':row['bytes'],'sha256':row['sha256']})
        need(len(rows)==header['count'] and source.digest(rows)==header['inventory_sha256'],'LLVM header membership/content differs')
    native=policy['native_runtime']
    need(native.get('admitted') is True and native.get('pins') and native.get('trees'),'complete pinned native runtime closure required')
    for row in native['pins']:reads.absolute(row,retain=False)
    for alias in native['aliases']:
        path=Path(alias['path'])
        need(path.is_symlink() and os.readlink(path)==alias['target'] and str(path.resolve(strict=True))==alias['resolved'],
            'native runtime link chain differs')
    for absent in native['absence']:need(not os.path.lexists(absent),'native runtime absence changed')
    for tree in native['trees']:
        root=Path(tree['path'])
        need(root.resolve(strict=True)==root and not root.is_symlink() and root.is_dir(),'physical native runtime root required')
        found=[]
        for path in sorted(root.rglob('*')):
            mode=path.lstat().st_mode
            if stat.S_ISDIR(mode):continue
            if stat.S_ISLNK(mode):
                found.append({'relative':str(path.relative_to(root)),'symlink':os.readlink(path),'resolved':str(path.resolve(strict=True))})
            elif stat.S_ISREG(mode):
                row=current(path)
                found.append({'relative':str(path.relative_to(root)),'bytes':row['bytes'],'sha256':row['sha256']})
            else:need(False,'special native runtime input')
        need(found==tree['files'],'native runtime membership/content differs')
    return {'python':python,'runtime_files':len(policy['runtime_files']),'native_pins':len(native['pins']),
        'native_roots':len(native['trees']),'scope':'physical source/runtime identity; no proof or native result'}


def original_refusal(result):
    need(result.get('accepted') is False and result.get('error')=={'type':'Refused','message':'duplicate compiler JSON key'}
        and result.get('after_input_errors')==[] and result.get('bytecode_cache_present') is False
        and result.get('source_call_count')==0 and result.get('source_names')==[] and result.get('public_proof') is False
        and result.get('current_0_2') is False and result.get('full_ticket28') is False and 'finalization_refusal' not in result,
        'only the exact completed V10 duplicate-key refusal is a supported original capture')


def original_closure(original,policy,observation):
    names={'policy':'control/linux_compiler_capture_policy_v10.json','result':'component/result.json',
        'observation':'component/compiler-observation.json','runtime_before':'capture-runtime-before.json',
        'runtime_after':'capture-runtime-after.json','zlib_before':'capture-zlib-before.json','zlib_after':'capture-zlib-after.json',
        'gzip_receipt':'component/caller.ast.gzip.json','compressed_tu':'component/caller.ast.json.gz','abi':'component/abi.ast.json',
        'probe':'control/compiler_abi_probe_v1.cpp','source':'control/source_call_fixture_v2.cpp','source_after':'source-after.json'}
    need(all(original[key].get('path')==ORIGINAL_ROOT+'/'+name for key,name in names.items()),'original physical capture role paths differ')
    controls=policy['controller_files']
    expected=[{'path':ORIGINAL_ROOT+'/control/'+name,**controls[name]} for name in
        ('source_call_fixture_v2.cpp','compiler_abi_probe_v1.cpp','m5ops.h')]
    expected += [{'path':policy['source_project']+'/'+row['relative'],'bytes':row['bytes'],'sha256':row['sha256']} for row in policy['source_inputs']]
    need(observation['inputs']==expected,'exact original source/header/control input membership differs')
    return [{'path':ORIGINAL_ROOT+'/control/'+name,**row} for name,row in controls.items()]


def execution_gate(value,selected):
    """Prospective root-observed receipt, mandatory beyond any completion Boolean."""
    exact(value,{'schema','controller','command','bootstrap','stdin_sha256','output_root','returncode','local_refusal',
        'timed_out','out_of_memory','wall_seconds','stdout','stderr'},'closed root-observed passive execution receipt required')
    need(value['schema']=='passive-transform-root-execution-1' and value['output_root']==ROOT
        and all(same_bytes(value[key],selected[key]) for key in ('controller','command','bootstrap','stdout','stderr'))
        and value['stdin_sha256']==CONTROLLER_SHA and type(value['returncode']) is int and value['returncode']==0
        and value['local_refusal'] is None and value['timed_out'] is False and value['out_of_memory'] is False
        and type(value['wall_seconds']) in (int,float) and math.isfinite(value['wall_seconds']) and 0<value['wall_seconds']<=960,
        'settled zero-exit exact controller/root/resource observation required')
    need(value['stderr']['bytes']==0,'normalization stderr must be empty')


def output_closure(settled,transform,policy):
    expected={
        'control/controller.py':'controller','control/normalizer.py':None,'control/census.json':'complete_census','control/policy.json':'policy',
        'component/inputs-before.json':None,'component/inputs-after.json':None,'component/caller.normalized.json.gz':'normalized_gzip',
        'component/rename-manifest.jsonl':'manifest','component/transport.json':'transport','component/inverse.json':'inverse'}
    outputs=settled.get('outputs')
    need(type(outputs) is list and len(outputs)==len(expected) and all(type(row) is dict and set(row)=={'path','bytes','sha256'} for row in outputs),
        'complete closed transform output membership required')
    indexed={row['path']:row for row in outputs}
    need(len(indexed)==len(outputs) and set(indexed)=={ROOT+'/'+name for name in expected},'exact unique original output paths required')
    for name,role in expected.items():
        if role:need(indexed[ROOT+'/'+name]==transform[role],'selected transform role differs from settled output')
    need(indexed[ROOT+'/control/normalizer.py']['sha256']==NORMALIZER_SHA,'retained executed normalizer differs')
    need(transform['result']['path']==ROOT+'/result.json','physical settled root result required')
    rows=settled.get('input_pins')
    wanted=[{'path':path,**row} for path,row in policy['physical_inputs'].items()]
    need(rows==wanted and len(rows)==36,'exact complete selected input closure required')
    need(sum(row['bytes'] for row in outputs)+transform['result']['bytes']<=268435456
        and all(type(row['bytes']) is int and 0<=row['bytes']<=FILE for row in outputs),'settled aggregate/file limits differ')
    return indexed


def transform_gate(value):
    need(value.get('schema')=='passive-paired-type-gzip-transform-result-2' and value.get('normalization_complete') is True
        and value.get('completion_requires_controller_zero_exit_and_settled_publication') is True
        and value.get('original_capture_accepted') is False and value.get('original_capture_refusal')=={'type':'Refused','message':'duplicate compiler JSON key'}
        and value.get('source_call_ABI_public_or_full28_admission') is False and value.get('compiler_or_native_or_solver_executed') is False
        and value.get('selected_inputs_unchanged') is True and value.get('output_root')==ROOT
        and value.get('expanded_normalized_limit_bytes')==EXPANDED and value.get('physical_file_limit_bytes')==FILE
        and value.get('aggregate_retained_limit_bytes')==268435456
        and type(value.get('wall_seconds')) in (int,float) and math.isfinite(value['wall_seconds']) and 0<value['wall_seconds']<900,
        'exact completed byte-transform with separate settled execution required')


def complete_capture(policy,reads,project):
    """Six-value legacy surface; the sixth value explicitly names new identities."""
    selected=policy['capture']
    need(type(selected) is dict,'typed capture selection required')
    if selected.get('kind')==source.CAPTURE_KIND:
        return source.complete_capture(policy,reads,project)
    exact(selected,{'kind','original','transform','prepared'},'closed versioned normalized ingress selection required')
    need(selected['kind']==KIND,'unknown capture failure/transport is unsupported')
    original=selected['original'];transform=selected['transform']
    exact(original,{'policy','result','observation','runtime_before','runtime_after','zlib_before','zlib_after','zlib_runtime',
        'gzip_receipt','compressed_tu','abi','probe','source','source_after'},'complete genuine original capture bindings required')
    exact(transform,{'controller','command','bootstrap','policy','result','transport','inverse','manifest','normalized_gzip','complete_census','execution','stdout','stderr'},
        'complete physical transform and root-execution bindings required')
    fixed_pin(original['policy'],ORIGINAL_POLICY_SHA,'exact V10 policy required');fixed_pin(original['result'],ORIGINAL_RESULT_SHA,'exact V10 refusal pin required')
    fixed_pin(transform['complete_census'],CENSUS_SHA,'exact complete admitted census required');fixed_pin(transform['controller'],CONTROLLER_SHA,'reviewed settled controller required')
    fixed_pin(transform['command'],COMMAND_SHA,'exact root-admitted transform command required')
    fixed_pin(transform['bootstrap'],BOOTSTRAP_SHA,'exact root-admitted early guard/bootstrap required')
    fixed_pin(transform['policy'],TRANSFORM_POLICY_SHA,'exact root-admitted input/resource policy required')
    fixed_pin(transform['execution'],ROOT_EXECUTION_SHA,'exact root-observed settled execution receipt required')
    fixed_pin(transform['result'],TRANSFORM_RESULT_SHA,'exact settled actual transform result required')
    original_policy=reads.document(original['policy']);result=reads.document(original['result']);original_refusal(result)
    transform_policy=reads.document(transform['policy'])
    observation=reads.document(original['observation']);commands=observation['commands'];recipe=original_policy['capture_recipe']['commands']
    for row in original_closure(original,original_policy,observation):reads.absolute(row,retain=False)
    need(observation.get('source_commit')=='2baf722fdaa6cba24b859eae3172a6f597417d72' and observation.get('original_source_coordinates') is True
        and len(commands)==len(recipe)==4 and [row['phase'] for row in commands]==['caller-preprocess','caller-ast','abi-preprocess','abi-ast'],
        'complete genuine same-original-TU compiler observation required')
    need(commands==transform_policy['original_commands'],'exact retained original four compiler observations differ')
    for actual,expected in zip(commands,recipe):
        need(actual['phase']==expected['phase'] and actual['argv']==expected['argv'] and actual['cwd']==expected['cwd']
            and type(actual['returncode']) is int and actual['returncode']==0 and type(actual['timeout_seconds']) in (int,float)
            and 0<actual['timeout_seconds']<=(120 if actual['phase']=='caller-ast' else 45),'exact original compiler phase/configuration/exit required')
        reads.absolute(actual['stdout'],retain=False);reads.absolute(actual['stderr'],retain=False)
    need(reads.document(original['source_after'])=={'commit':observation['source_commit'],'source_unchanged':True,'tracked_changes':''},
        'original source-after observation differs')
    before=reads.document(original['runtime_before']);after=reads.document(original['runtime_after'])
    need(after=={'runtime':before,'after_errors':[]},'original captured runtime closure differs')
    for module,expected in ((normalizer,NORMALIZER_SHA),(codec,CODEC_SHA),(closed,CLOSED_SHA),
        (normalized_compiler,NORMALIZED_COMPILER_SHA),(source.semantic_compiler,normalized_compiler.CONSUMER_SHA)):
        actual_path=Path(module.__file__);raw=actual_path.read_bytes()
        reads.absolute({'path':str(actual_path),'bytes':len(raw),'sha256':expected})
        need(hashlib.sha256(raw).hexdigest()==expected,'actual promoted ingress primitive differs')
    need(physical_runtime(original_policy,reads)==before,'current physical runtime differs from captured pre/post closure')
    zb,za=(reads.document(original[name]) for name in ('zlib_before','zlib_after'))
    need(zb==za==original_policy['zlib_binding'],'original decoder runtime provenance differs')
    for row in observation['inputs']:reads.absolute(row,retain=False)
    need([row['label'] for row in observation['groups']]==['caller','abi'],'complete original group census required')
    for index,group in enumerate(observation['groups']):
        label=group['label'];original_source=original['source'] if label=='caller' else original['probe']
        required={original_source['path'],original_policy['source_project']+'/apps/dx100/benchmarks/API/MAA.hpp',
            original_policy['source_project']+'/apps/dx100/benchmarks/API/MAA_gem5.hpp',
            original_policy['capture_recipe']['commands'][index*2]['cwd'].rsplit('/',1)[0]+'/control/include/gem5/m5ops.h'}
        names=[row['path'] for row in group['dependencies']]
        need(len(names)==len(set(names)) and required<=set(names),'required source/two-header/stub dependencies are incomplete')
        cwd=commands[index*2]['cwd']
        for role,target in (('preprocess_dependency',label),('ast_dependency',label+'-ast')):
            dependency_text=reads.absolute(group[role]).decode('utf-8')
            need(make_dependencies(dependency_text,target,cwd)==names,'original preprocessing/AST physical dependency memberships differ')
        need(group['ast']==commands[index*2+1]['stdout'],'same-TU AST and actual compiler stdout differ')
        need(group['ast']==original['compressed_tu'] if label=='caller' else group['ast']==original['abi'],
            'selected caller/ABI physical artifact differs')
        for row in group['dependencies']:reads.absolute(row,retain=False)
        for name in ('frozen','preprocess_dependency','ast','ast_dependency'):reads.absolute(group[name],retain=False)
        if group['label']=='caller':reads.absolute(group['expanded_stream_receipt'],retain=False)
    original_receipt=reads.document(original['gzip_receipt']);reads.selected(original['compressed_tu'],retain=False,limit=FILE)
    need((original_receipt['expanded_bytes'],original_receipt['expanded_sha256'],original_receipt['compressed_sha256'])==(543412150,RAW_SHA,ORIGINAL_GZIP_SHA)
        and original['compressed_tu']['sha256']==ORIGINAL_GZIP_SHA and original['compressed_tu']['bytes']==original_receipt['compressed_bytes']
        and commands[1]['lossless_stdout']==original_receipt and observation['groups'][0]['expanded_stream_receipt']==original['gzip_receipt'],
        'original compiler wire/gzip identity differs')
    execution=reads.document(transform['execution']);execution_gate(execution,transform)
    for key in ('controller','command','bootstrap','stdout','stderr'):reads.selected(transform[key],retain=False)
    settled=reads.document(transform['result']);transform_gate(settled)
    outputs=output_closure(settled,transform,transform_policy)
    need(reads.document(outputs[ROOT+'/component/inputs-before.json'])==reads.document(outputs[ROOT+'/component/inputs-after.json'])==settled['input_pins'],
        'retained exact selected input before/after records differ')
    publication=reads.document(transform['stdout'])
    need(publication=={'normalization_complete':True,'result':transform['result'],'source_call_ABI_or_public_admission':False},
        'root-observed flushed publication differs from settled physical result')
    for row in settled['input_pins']+settled['outputs']:reads.absolute(row,retain=False)
    need(settled['zlib_binding']==original_policy['zlib_binding'],'transform selected runtime differs')
    census=reads.document(transform['complete_census']);c=census['census'];transport=reads.document(transform['transport'])
    need(census['complete_decoder_identity_verified'] is True and c['duplicate_events']==c['prospective_role_renames']==116
        and c['unknown_or_mismatched_duplicate_events']==0 and c['prospective_normalized_file_cap_fit'] is False,
        'full known-role census with honest plain-file refusal required')
    n=transport['normalization'];excepted={'schema','prospective_role_normalization_eligible','prospective_normalization_refused',
        'prospective_normalized_file_cap_fit','normalized_AST_retained_or_admitted'}
    need(all(n[key]==value for key,value in c.items() if key not in excepted) and n['plain_normalized_file_cap_fit'] is False
        and (n['normalized_bytes'],n['normalized_sha256'])==(178924116,NORMALIZED_SHA),'original census and expanded role transport identities differ')
    runtime=reads.document(original['zlib_runtime'])
    need(set(runtime)=={'schema','origin','version','physical_inputs'} and runtime['schema']=='selected-stdlib-zlib-runtime-1','closed selected decoder runtime required')
    for row in runtime['physical_inputs']:reads.absolute(row,retain=False)
    import zlib
    need(zlib.__spec__.origin==runtime['origin'] and zlib.ZLIB_RUNTIME_VERSION==runtime['version'],'actual selected decoder runtime differs')
    compressed=reads.selected(transform['normalized_gzip'],limit=FILE)
    manifest=reads.selected(transform['manifest'],limit=33554432)
    def decode_check():stream_stable((transform['normalized_gzip'],transform['manifest']))
    verified=normalizer.verify_inverse_gzip(zlib,io.BytesIO(compressed),manifest,transport,codec.__dict__,decode_check)
    need(verified==reads.document(transform['inverse']),'fresh complete normalized gzip/inverse observation differs')
    receipt=transport['normalized_gzip_codec'];decoded=codec.DecodeReader(zlib,io.BytesIO(compressed),receipt,
        expanded_limit=EXPANDED,compressed_limit=FILE,check=decode_check)
    chunks=[]
    while True:
        chunk=decoded.read(65536)
        if not chunk:break
        chunks.append(chunk)
    need(decoded.verified,'complete normalized stream decoder closure required');full_tu=b''.join(chunks);del chunks
    source_bytes=reads.selected(original['source']);probe_bytes=reads.selected(original['probe'])
    captured_source=original_policy['controller_files']['source_call_fixture_v2.cpp']
    need(hashlib.sha256(source_bytes).hexdigest()==captured_source['sha256']==policy['proof_source']['sha256']
        and len(source_bytes)==captured_source['bytes'] and reads.portable(policy['proof_source'])==source_bytes,
        'selected closed proof buffer must equal the exact captured original fixture')
    source_path,probe_path=reads.path(original['source']),reads.path(original['probe']);declarations=source.binder.inventory(project)
    need(normalized_compiler.consumer is source.semantic_compiler,'normalized adapter must use the same selected semantic compiler module')
    prepared=normalized_compiler.prepare_unit(source.binder.__dict__,transport_kind=KIND,full_tu_raw=full_tu,abi_raw=reads.selected(original['abi']),
        source_path=source_path,source_bytes=source_bytes,probe_path=probe_path,probe_bytes=probe_bytes,declarations=declarations,
        compiler_capture_pin=original['observation']['sha256'],full_tu_compressed_bytes=receipt['compressed_bytes'],full_tu_expanded_limit=EXPANDED)
    need(prepared==reads.document(selected['prepared']) and prepared['raw_full_tu_sha256']==NORMALIZED_SHA,
        'fresh complete actual-TU/ABI/declaration/call preparation differs')
    tu=source.semantic_compiler.resolve_locations(source.semantic_compiler.parse_json_roots(full_tu,full_tu=True,expanded_limit=EXPANDED)[0],source_path)
    need(physical_runtime(original_policy,reads)==before,'physical runtime membership changed during ingress')
    reads.recheck()
    binding={**receipt,'transport_kind':KIND,'original_compiler_stream':original_receipt,'original_capture_accepted':False,
        'original_duplicate_refusal':result['error'],'complete_census':transform['complete_census'],'transform_result':transform['result'],
        'root_execution':transform['execution'],'inverse':transform['inverse'],'normalized_gzip':transform['normalized_gzip'],
        'normalized_expanded_sha256':NORMALIZED_SHA,'original_minified_token_sha256':TOKEN_SHA}
    return source_path,source_bytes,tu,declarations,prepared,binding
