"""Closed G642 memory-family source ingress. No compiler/native/proof execution."""
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
from swdb._dx100_whole import memory_normalized_compiler_adapter_v1 as memory_compiler
KIND='complete-memory-original-tu-paired-type-gzip-1'
COMMIT='2baf722fdaa6cba24b859eae3172a6f597417d72'
SOURCE_SHA='55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'
EXPANDED=201326592
FILE=134217728
TOTAL=268435456
CODEC_SHA='aae4a423216fcdca6b16f9eba370ec4c83615ed61ae79dd4b3d09e3bed1702ef'
NORMALIZER_SHA='6301baede48b9b0f1d3beaef2873e59026f5e9e26135bc2f7ba0a3f76825f941'
CLOSED_SHA='748423c27ac8c1f9810c08d3f0ffc71548da703b4b4f95cedc31d4f8bc0418af'
MEMORY_COMPILER_SHA='1315ebef75dc4219bcb012aa2a5f85cbcaeb82c54bb625fdad6f18ea397a6e62'


def need(value,message):source.need(value,message)

def exact(value,keys,message):need(type(value) is dict and set(value)==set(keys),message)

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

"""Fixed memory-only same-TU ingress body; utility functions are copied exactly."""

def facts(reads):
    path = Path(__file__).with_name('memory_capture_facts_v1.json')
    raw = reads.absolute({'path': str(path), 'bytes': 21487,
        'sha256': '9862edaf233ebb7d6146dfdb7e825864e1c4314bd5e034a9a8800c97b20a3f3a'}, limit=65536)
    value = source.contracts.document(raw)
    need(value['kind'] == KIND and value['source_commit'] == COMMIT, 'fixed G642 memory facts required')
    return value


def fixed(row, expected, *, original_path=False):
    exact(row, {'path', 'bytes', 'sha256'}, 'closed physical memory role required')
    need(same_bytes(row, expected) and (not original_path or row['path'] == expected['path']),
         'exact retained memory role identity differs')


def original_gate(result):
    need(result.get('accepted') is True and result.get('compiler_observation_complete') is True
         and result.get('error') is None and result.get('after_input_errors') == []
         and result.get('bytecode_cache_present') is False and result.get('source_call_count') == 0
         and result.get('source_names') == [] and 'finalization_refusal' not in result
         and all(result.get(name) is False for name in ('ABI_interpreted','source_call_admitted',
             'strict_complete_TU_consumer_passed','native_or_solver_executed','public_proof','current_0_2','full_ticket28')),
         'exact successful G642 observation-only boundary required')


def transform_gate(value, f):
    need(value.get('schema') == 'passive-memory-paired-type-gzip-transform-result-1'
         and value.get('normalization_complete') is True
         and value.get('completion_requires_controller_zero_exit_and_settled_publication') is True
         and value.get('original_compiler_observation_accepted') is True
         and value.get('original_AST_ABI_source_call_admitted') is False
         and value.get('source_call_ABI_public_or_full28_admission') is False
         and value.get('compiler_or_native_or_solver_executed') is False
         and value.get('selected_inputs_unchanged') is True and value.get('output_root') == f['transform_root']
         and value.get('source_fixture_sha256') == SOURCE_SHA
         and value.get('original_observation') == f['original']['observation']
         and value.get('expanded_normalized_limit_bytes') == EXPANDED
         and value.get('physical_file_limit_bytes') == FILE and value.get('aggregate_retained_limit_bytes') == TOTAL
         and type(value.get('wall_seconds')) in (int,float) and math.isfinite(value['wall_seconds'])
         and 0 < value['wall_seconds'] < 900, 'complete exact memory byte-transform required')


def execution_gate(adoption, reconciliation, invocation, publication, transform, f):
    need(adoption.get('verdict') == 'ACCEPT_LOSSLESS_MEMORY_AST_BYTE_TRANSPORT_ONLY'
         and adoption.get('actual_reconciliation', {}).get('sha256') == f['reconciliation']['sha256'],
         'exact root-adopted byte-transport scope required')
    need(reconciliation.get('zero_exit') is True and reconciliation.get('empty_stderr') is True
         and reconciliation.get('output_root') == f['transform_root']
         and reconciliation.get('original_memory_compiler_generation') == 642
         and reconciliation.get('physical_output_count') == 14
         and reconciliation.get('physical_output_bytes') == 13777031,
         'retained actual finite memory settlement differs')
    need(type(invocation.get('returncode')) is int and invocation['returncode'] == 0
         and invocation.get('local_refusal') is None and invocation.get('input_source_unchanged') is True
         and invocation.get('stdin_sha256') == transform['controller']['sha256']
         and invocation.get('command_packet_sha256') == f['command']['sha256']
         and same_bytes(invocation.get('stdout'), transform['stdout'])
         and same_bytes(invocation.get('stderr'), transform['stderr']) and transform['stderr']['bytes'] == 0
         and type(invocation.get('local_wall_seconds')) in (int,float)
         and math.isfinite(invocation['local_wall_seconds']) and 0 < invocation['local_wall_seconds'] <= 1000,
         'settled exact passive controller invocation required')
    need(publication == {'normalization_complete': True, 'result': transform['result'],
         'source_call_ABI_or_public_admission': False}, 'exact settled memory publication differs')
    accepted = adoption['accepted']
    need((accepted['expanded_bytes'], accepted['expanded_sha256'], accepted['normalized_gzip_bytes'],
          accepted['normalized_gzip_sha256'], accepted['original_minified_token_sha256']) ==
         (f['codec']['expanded_bytes'], f['codec']['expanded_sha256'], f['codec']['compressed_bytes'],
          f['codec']['compressed_sha256'], f['normalization']['original_minified_token_sha256']),
         'root acceptance identities differ from fixed genuine memory transport')


def input_output_closure(settled, policy, transform, f):
    wanted = [{'path':path, **row} for path,row in policy['physical_inputs'].items()]
    need(len(wanted) == f['input_count'] and source.digest(policy['physical_inputs']) == f['input_map_sha256']
         and settled['input_pins'] == wanted, 'closed complete911-input memory selection differs')
    expected = [row for name,row in sorted(f['transform_outputs'].items()) if name != 'result.json']
    need(settled.get('outputs') == expected and len(expected) == 13
         and sum(row['bytes'] for row in f['transform_outputs'].values()) == 13777031,
         'exact complete14-file memory output census differs')
    need(all(row['bytes'] <= FILE for row in expected) and sum(row['bytes'] for row in expected) + transform['result']['bytes'] <= TOTAL,
         'actual memory output extent exceeds admitted limits')
    return wanted + expected


def _derive(policy, reads, project):
    selected = policy['capture']
    exact(selected, {'kind','original','transform','prepared'}, 'closed memory capture required')
    need(selected['kind'] == KIND, 'unknown memory capture family refused')
    need(type(policy.get('proof_source')) is dict and policy['proof_source'].get('sha256') == SOURCE_SHA,
         'exact memory proof-buffer family required before consumption')
    f = facts(reads); original, transform = selected['original'], selected['transform']
    exact(original, set(f['original']) | {'zlib_runtime','execution'}, 'complete genuine G642 original roles required')
    remote = {'controller':'control/controller.py','policy':'control/policy.json','result':'result.json',
        'transport':'component/transport.json','inverse':'component/inverse.json','manifest':'component/rename-manifest.jsonl',
        'normalized_gzip':'component/caller.normalized.json.gz','census':'component/census.json',
        'runtime_before':'component/runtime-before.json','runtime_after':'component/runtime-after.json'}
    mirrors = ('command','bootstrap','root_adoption','reconciliation','postflight','invocation','stdout','stderr')
    exact(transform, set(remote) | set(mirrors), 'closed actual memory transform/provenance roles required')
    for role, expected in f['original'].items(): fixed(original[role], expected, original_path=True)
    fixed(original['execution'], f['capture_execution'])
    for role,name in remote.items(): fixed(transform[role], f['transform_outputs'][name], original_path=True)
    for role in mirrors: fixed(transform[role], f[role])
    original_policy, result = (reads.document(original[name]) for name in ('policy','result')); original_gate(result)
    need(original_policy['source_project'] == str(project) and original_policy['source_commit'] == COMMIT,
         'exact original2baf project role required')
    transform_policy = reads.document(transform['policy'])
    observation = reads.document(original['observation']); commands = observation['commands']
    need(observation.get('source_commit') == COMMIT and observation.get('original_source_coordinates') is True
         and len(commands) == 4 and commands == transform_policy['original_commands']
         and [row['phase'] for row in commands] == ['caller-preprocess','caller-ast','abi-preprocess','abi-ast'],
         'same original full-TU memory compiler observations differ')
    expected_inputs = [{'path':f['original_root']+'/control/'+name, **original_policy['controller_files'][name]}
        for name in ('same_thread_memory_v1.cpp','compiler_abi_probe_v1.cpp','m5ops.h')]
    expected_inputs += [{'path':str(project)+'/'+row['relative'], 'bytes':row['bytes'],'sha256':row['sha256']}
                       for row in original_policy['source_inputs']]
    need(observation['inputs'] == expected_inputs, 'exact memory source/header/control inputs differ')
    for name,row in original_policy['controller_files'].items():
        reads.absolute({'path':f['original_root']+'/control/'+name, **row}, retain=False)
    for actual, expected in zip(commands, original_policy['capture_recipe']['commands']):
        need(actual['phase'] == expected['phase'] and actual['argv'] == expected['argv'] and actual['cwd'] == expected['cwd']
             and type(actual['returncode']) is int and actual['returncode'] == 0
             and type(actual['timeout_seconds']) in (int,float)
             and 0 < actual['timeout_seconds'] <= (120 if actual['phase'] == 'caller-ast' else 45),
             'exact original memory compiler recipe/exit/configuration required')
        for role in ('stdout','stderr'): reads.absolute(actual[role], retain=False)
        need(actual['stderr']['bytes'] == 0, 'original memory compiler stderr must be empty')
    capture_execution = reads.document(original['execution'])
    need(capture_execution.get('generation') == 642 and capture_execution.get('source_fixture_sha256') == SOURCE_SHA
         and capture_execution.get('raw_root') == f['original_root']
         and capture_execution.get('verdict') == 'PASS_ACTUAL_COMPILER_OBSERVATION_METADATA_ONLY',
         'retained finite G642 compiler observation attribution required')
    before, after = (reads.document(original[name]) for name in ('runtime_before','runtime_after'))
    need(after == {'runtime':before,'after_errors':[]}, 'original memory runtime before/after differs')
    need(reads.document(original['source_after']) == {'commit':COMMIT,'source_unchanged':True,'tracked_changes':''},
         'original memory source-after differs')
    need(physical_runtime(original_policy, reads) == before, 'current full physical runtime differs from original observation')
    for name in ('zlib_before','zlib_after'):
        need(reads.document(original[name]) == original_policy['zlib_binding'], 'original decoder runtime differs')
    need([group['label'] for group in observation['groups']] == ['caller','abi'], 'complete memory source/probe groups required')
    for index,group in enumerate(observation['groups']):
        label = group['label']; selected_source = original['source'] if label == 'caller' else original['probe']
        names = [row['path'] for row in group['dependencies']]
        required = {selected_source['path'], str(project)+'/apps/dx100/benchmarks/API/MAA.hpp',
            str(project)+'/apps/dx100/benchmarks/API/MAA_gem5.hpp', f['original_root']+'/control/include/gem5/m5ops.h'}
        need(len(names) == len(set(names)) and required <= set(names), 'complete memory used-header/source closure required')
        for role,target in (('preprocess_dependency',label),('ast_dependency',label+'-ast')):
            need(make_dependencies(reads.absolute(group[role]).decode('utf-8'), target, commands[index*2]['cwd']) == names,
                 'original memory preprocessing/AST dependency membership differs')
        need(group['ast'] == commands[index*2+1]['stdout'] == (original['compressed_tu'] if label == 'caller' else original['abi']),
             'original same-TU AST artifact differs')
        for row in group['dependencies']: reads.absolute(row, retain=False)
        for name in ('frozen','preprocess_dependency','ast','ast_dependency'): reads.absolute(group[name], retain=False)
    wire = reads.document(original['gzip_receipt'])
    need(wire == f['original_wire'] == commands[1]['lossless_stdout']
         and observation['groups'][0]['expanded_stream_receipt'] == original['gzip_receipt'],
         'genuine original G642 wire/gzip identities differ')
    adoption, reconciliation, invocation, publication = (reads.document(transform[name])
        for name in ('root_adoption','reconciliation','invocation','stdout'))
    execution_gate(adoption,reconciliation,invocation,publication,transform,f)
    post = reads.document(transform['postflight']); settled = reads.document(transform['result']); transform_gate(settled,f)
    need(post['transform_result'] == settled and post['original_raw_unchanged'] is True and post['transform_raw_unchanged'] is True,
         'settled retained compact memory context differs')
    for row in input_output_closure(settled,transform_policy,transform,f): reads.absolute(row, retain=False)
    for role in mirrors: reads.selected(transform[role], retain=False)
    for role in ('runtime_before','runtime_after'):
        need(reads.document(transform[role]) == before, 'full memory transform runtime differs from compiler runtime')
    root = f['transform_root']
    need(reads.document(f['transform_outputs']['component/inputs-before.json']) == settled['input_pins']
         == reads.document(f['transform_outputs']['component/inputs-after.json']), 'retained memory input before/after differs')
    transport = reads.document(transform['transport']); census = reads.document(transform['census'])
    need(transport['normalization'] == census == f['normalization'] and transport['normalized_gzip_codec'] == f['codec']
         and census['complete_original_JSON_token_grammar_checked'] is True and census['duplicate_events'] == 116
         and census['prospective_role_renames'] == census['inverse_manifest_rows'] == 116
         and census['unknown_or_mismatched_duplicate_events'] == 0 and census['normalized_AST_admitted'] is False
         and transport['original_TU_source_ABI_or_public_admission'] is False,
         'complete genuine memory role/token/census identities required')
    runtime = reads.document(original['zlib_runtime'])
    exact(runtime, {'schema','origin','version','physical_inputs'}, 'closed selected decoder descriptor required')
    need(runtime['schema'] == 'selected-stdlib-zlib-runtime-1', 'exact decoder runtime schema required')
    for row in runtime['physical_inputs']: reads.absolute(row, retain=False)
    import zlib
    need(zlib.__spec__.origin == runtime['origin'] and zlib.ZLIB_RUNTIME_VERSION == runtime['version'],
         'actual selected decoder runtime differs')
    for module, expected in ((codec,CODEC_SHA),(normalizer,NORMALIZER_SHA),(closed,CLOSED_SHA),
                             (memory_compiler,MEMORY_COMPILER_SHA),(source.compiler,memory_compiler.LEGACY_SHA)):
        path = Path(module.__file__); reads.absolute({'path':str(path),'bytes':path.stat().st_size,'sha256':expected}, retain=False)
    need(memory_compiler.legacy is source.compiler, 'one unchanged generic full-TU consumer required')
    compressed = reads.selected(transform['normalized_gzip'], limit=FILE)
    manifest = reads.selected(transform['manifest'], limit=33554432)
    def decoder_check(): stream_stable((transform['normalized_gzip'],transform['manifest']))
    inverse = normalizer.verify_inverse_gzip(zlib,io.BytesIO(compressed),manifest,transport,codec.__dict__,decoder_check)
    need(inverse == reads.document(transform['inverse']) == post['inverse'], 'fresh complete memory inverse differs')
    decoded = codec.DecodeReader(zlib,io.BytesIO(compressed),f['codec'],expanded_limit=EXPANDED,compressed_limit=FILE,check=decoder_check)
    chunks = []
    while True:
        chunk = decoded.read(65536)
        if not chunk: break
        chunks.append(chunk)
    need(decoded.verified, 'complete memory normalized decoder closure required')
    full_tu = b''.join(chunks); del chunks
    source_bytes, probe_bytes = (reads.selected(original[role]) for role in ('source','probe'))
    need(len(source_bytes) == 3258 and hashlib.sha256(source_bytes).hexdigest() == SOURCE_SHA
         == policy['proof_source']['sha256'] and reads.portable(policy['proof_source']) == source_bytes,
         'exact original/selected memory proof buffer required')
    source_path, probe_path = reads.path(original['source']), reads.path(original['probe'])
    declarations = source.binder.inventory(project)
    prepared = memory_compiler.prepare_unit(source.binder.__dict__, transport_kind=KIND, full_tu_raw=full_tu,
        abi_raw=reads.selected(original['abi']), source_path=source_path, source_bytes=source_bytes,
        probe_path=probe_path, probe_bytes=probe_bytes, declarations=declarations,
        compiler_capture_pin=original['observation']['sha256'], full_tu_compressed_bytes=f['codec']['compressed_bytes'],
        full_tu_expanded_limit=EXPANDED)
    tu = source.compiler.resolve_locations(source.compiler.parse_json_roots(full_tu,full_tu=True,expanded_limit=EXPANDED)[0],source_path)
    need(physical_runtime(original_policy,reads) == before, 'current memory physical runtime changed during preparation')
    reads.recheck()
    binding = {**f['codec'], 'transport_kind':KIND, 'source_family':'three-same-thread-memory-1',
        'original_compiler_stream':wire, 'original_capture_accepted':True, 'original_source_call_admitted':False,
        'root_adoption':transform['root_adoption'], 'transform_result':transform['result'], 'inverse':transform['inverse'],
        'normalized_gzip':transform['normalized_gzip'], 'original_minified_token_sha256':f['normalization']['original_minified_token_sha256']}
    return source_path,source_bytes,tu,declarations,prepared,binding


def complete_capture(policy, reads, project):
    need(type(policy.get('capture')) is dict and policy['capture'].get('prepared') is not None,
         'public memory ingress requires the separately observed exact preparation')
    result = _derive(policy,reads,project)
    need(result[4] == reads.document(policy['capture']['prepared']), 'fresh full memory preparation differs from selected observation')
    reads.recheck()
    return result


def observe_capture(policy, reads, project):
    need(type(policy.get('capture')) is dict and policy['capture'].get('prepared') is None,
         'private memory observation requires explicit unknown preparation')
    return _derive(policy,reads,project)

