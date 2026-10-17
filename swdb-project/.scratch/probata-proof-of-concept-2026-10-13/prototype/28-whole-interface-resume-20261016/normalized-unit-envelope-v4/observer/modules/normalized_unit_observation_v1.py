"""2026-10-16 ET. Data-only bootstrap; public equality ingress is unchanged."""
from swdb._dx100_whole.normalized_capture_ingress_v2 import (BOOTSTRAP_SHA, CENSUS_SHA, CLOSED_SHA, CODEC_SHA, COMMAND_SHA, CONTROLLER_SHA, EXPANDED, FILE, KIND, NORMALIZED_COMPILER_SHA, NORMALIZED_SHA, NORMALIZER_SHA, ORIGINAL_GZIP_SHA, ORIGINAL_POLICY_SHA, ORIGINAL_RESULT_SHA, Path, RAW_SHA, ROOT, ROOT_EXECUTION_SHA, TOKEN_SHA, TRANSFORM_POLICY_SHA, TRANSFORM_RESULT_SHA, closed, codec, exact, execution_gate, fixed_pin, hashlib, io, make_dependencies, need, normalized_compiler, normalizer, original_closure, original_refusal, output_closure, physical_runtime, source, stream_stable, transform_gate)

def observe_capture(policy,reads,project):
    """Six-value legacy surface; the sixth value explicitly names new identities."""
    selected=policy['capture']
    need(type(selected) is dict and selected.get('kind')==KIND and selected.get('prepared') is None,
        'observation requires exact normalized kind and explicit unknown preparation output')
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
        (normalized_compiler,NORMALIZED_COMPILER_SHA),(source.compiler,normalized_compiler.LEGACY_SHA)):
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
    need(normalized_compiler.legacy is source.compiler,'normalized adapter must use the same unchanged legacy compiler module')
    prepared=normalized_compiler.prepare_unit(source.binder.__dict__,transport_kind=KIND,full_tu_raw=full_tu,abi_raw=reads.selected(original['abi']),
        source_path=source_path,source_bytes=source_bytes,probe_path=probe_path,probe_bytes=probe_bytes,declarations=declarations,
        compiler_capture_pin=original['observation']['sha256'],full_tu_compressed_bytes=receipt['compressed_bytes'],full_tu_expanded_limit=EXPANDED)
    need(prepared['raw_full_tu_sha256']==NORMALIZED_SHA,
        'fresh normalized parser input identity differs during observation')
    tu=source.compiler.resolve_locations(source.compiler.parse_json_roots(full_tu,full_tu=True,expanded_limit=EXPANDED)[0],source_path)
    need(physical_runtime(original_policy,reads)==before,'physical runtime membership changed during ingress')
    reads.recheck()
    binding={**receipt,'transport_kind':KIND,'original_compiler_stream':original_receipt,'original_capture_accepted':False,
        'original_duplicate_refusal':result['error'],'complete_census':transform['complete_census'],'transform_result':transform['result'],
        'root_execution':transform['execution'],'inverse':transform['inverse'],'normalized_gzip':transform['normalized_gzip'],
        'normalized_expanded_sha256':NORMALIZED_SHA,'original_minified_token_sha256':TOKEN_SHA}
    return source_path,source_bytes,tu,declarations,prepared,binding
