"""Lossless public adapter and replay contracts, never gem5 evidence. 2026-09-26 ET.
Updated: 2026-10-09 ET (code review of ticket 06: evidence commands on adapter output run in
explicit Extensa fixture mode)."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import time

import pytest

from test_dx100 import EXTENSA, case, extensa_args, reference
from test_dx100_v2 import v2_request
from swdb import artifacts, bfs_protocol, dx100_coverage as coverage
from swdb.cli import Failure

DEBUG = ("110: global: I[0] Start [INSTR[opcode(INDIR_ST_VECTOR) datatype(INT32) baseAddr(0x4000)]]\n"
    "120: global: I[0] recvData: 2 entries received for addr(0x8000), grow(x0) from T[0]!\n"
    "121: global: I[0] recvData: new_data[2] = SPD[0][0] = 7/7/0.0!\n"
    "122: global: I[0] recvData: new_data[2] = SPD[0][1] = 9/9/0.0!\n"
    "125: global: R[0] executeInstruction: my_idx_j: 16384, tile size: 16384\n"
    "126: global: R[0] executeInstruction: my_idx_j: 7, tile size: 7\n"
    "130: global: I[0] End [INSTR]\n131: global: S[0] End [INSTR]\n"
    "132: global: R[0] End [INSTR]\n133: global: A[0] End [INSTR]\n"
    + "134: global: I[0] fillRowTable: SPD[0][4] = 0 (cond not taken)\n"*2048
    + "99999: global: R[0] executeInstruction: my_idx_j: 7, tile size: 7\n")


def gzip_request(case, mode='normal'):
    request = v2_request(case, 'normal')
    simulator = Path(request['simulator']['path'])
    program = simulator.read_text().replace("    mode='normal'", f"    mode='normal'\n    transport_mode={mode!r}")
    program = program.replace("\\nfinalTick 31400\\n", "\\nfinalTick 31400\\nsystem.maa.numInst 4\\n")
    marker = "    tick=[31400]; steps=[]; calls=[0]; enabled=set(); trace_path=[None]"
    inserted = '''    import gzip,atexit
    text=DEBUG
    print('SWDB_BFS_PARENT_STORAGE address=4000 count=20 element_bytes=4')
    debug_arg=next((arg.split('=',1)[1] for arg in args if arg.startswith('--debug-file=')),None)
    if debug_arg:
        assert debug_arg==str(out/'roi-debug.trace.gz')
        assert '--debug-flags=MAATrace,MAARangeFuser,MAAIndirect' in args
        target=pathlib.Path(debug_arg)
        sink=gzip.open(target,'wb');sink.write(text.encode());sink.flush()
        def close_debug():
            sink.close()
            raw=target.read_bytes()
            if transport_mode=='truncated':target.write_bytes(raw[:-7])
            elif transport_mode=='crc':target.write_bytes(raw[:-8]+bytes([raw[-8]^1])+raw[-7:])
            elif transport_mode=='deflate':target.write_bytes(bytes.fromhex('1f8b0800000000000003')+b'\\x07'+b'\\0'*16)
            elif transport_mode=='invalid-utf8':target.write_bytes(gzip.compress(b'\\xff\\n'))
            elif transport_mode=='empty-file':target.write_bytes(b'')
            elif transport_mode=='missing':target.unlink()
        atexit.register(close_debug)
    else:
        print(text,end='')
'''.replace('DEBUG', repr(DEBUG))
    program = program.replace(marker, inserted+marker)
    if mode == 'trace-only-pass':
        program = program.replace("print('Verification: '+('FAIL' if mode=='FAIL' else 'PASS'),flush=True)",
                                  "sink.write(b'Verification: PASS\\n');sink.flush()")
    if mode == 'trace-false-parent':
        program = program.replace("text="+repr(DEBUG), "text="+repr('SWDB_BFS_PARENT_STORAGE address=5000 count=20 element_bytes=4\n'+DEBUG))
    simulator.write_text(program)
    request['simulator'] = reference(simulator)
    request['verification'].update(coverage=True, trace_transport=coverage.TRANSPORT)
    return request


def semantic(value):
    if isinstance(value,dict):
        return {key:semantic(item) for key,item in value.items() if key not in {'line','stream','debug_trace'}}
    if isinstance(value,list):return list(map(semantic,value))
    return value


def test_actual_public_adapter_retains_full_gzip_and_unchanged_semantic_treatment(case):
    request=gzip_request(case);_,invoke,_=case
    legacy=copy.deepcopy(request);legacy['id']='legacy';legacy['verification'].pop('trace_transport')
    first=invoke('dx100-execute',legacy)
    second=invoke('dx100-execute',request)
    assert first['outcome']['state']==second['outcome']['state']=='complete'
    assert first['context']['instrumentation']==second['context']['instrumentation']
    assert first['build']==second['build'] and first['context']['execution_binding']==second['context']['execution_binding']
    assert first['timing'][0]['duration_s']==second['timing'][0]['duration_s']
    a,b=(row['correctness']['checks'][0]['coverage'] for row in (first,second))
    assert semantic(a)==semantic(b)
    trace=second['context']['debug_trace'];raw=Path(trace['path']).read_bytes()
    assert gzip.decompress(raw)==DEBUG.encode()
    assert trace['sha256']==hashlib.sha256(raw).hexdigest() and trace['bytes']==len(raw)
    assert trace['uncompressed_sha256']==hashlib.sha256(DEBUG.encode()).hexdigest()
    assert trace['uncompressed_bytes']==len(DEBUG.encode()) and trace['lines']==len(DEBUG.splitlines())
    assert b['full_tiles']['count']==b['tail_tiles']['count']==b['competing_parent_updates']['count']==1
    assert b['competing_parent_updates']['parent_storage']['stream']=='stdout'
    assert b['competing_parent_updates']['samples'][0]['stream']=='debug_trace'
    plain=Path(second['correctness']['checks'][0]['output']['path']).read_text()
    assert 'Verification: PASS' in plain and 'fillRowTable' not in plain
    assert second['context']['post_roi_trace']['path']!=trace['path']
    assert coverage.validate_trace(second)==trace
    bfs_protocol._check_verifier_identity(second)


@pytest.mark.parametrize('mode',['truncated','crc','deflate','invalid-utf8','empty-file','missing','trace-only-pass'])
def test_public_gzip_failure_cannot_promote_plain_exit_or_trace_only_pass(case,mode):
    request=gzip_request(case,mode);_,invoke,_=case
    result=invoke('dx100-execute',request)
    assert result['outcome']['state']!='complete'
    assert result['correctness']['state']!='passed' and result['timing']==[] and result['gain_claim'] is False
    assert next(stage for stage in result['stages'] if stage['stage']=='simulation')['returncode']==0
    if mode=='trace-only-pass':assert 'verifier outcome' in result['outcome']['reason']
    elif mode=='missing':assert 'regular file' in result['outcome']['reason']
    else:assert 'gzip debug trace' in result['outcome']['reason']


def test_parent_marker_in_trace_cannot_override_authoritative_stdout(case):
    request=gzip_request(case,'trace-false-parent');_,invoke,_=case
    result=invoke('dx100-execute',request)
    assert result['outcome']['state']=='complete'
    parent=result['correctness']['checks'][0]['coverage']['competing_parent_updates']
    assert parent['parent_storage']['virtual_address']==0x4000 and parent['count']==1


@pytest.mark.parametrize('fault',['compressed','deflate','decoded','counts','location','legacy','request','context','null-request','command','flags','downgrade'])
def test_replay_rejects_changed_or_consistently_resealed_trace_evidence(case,fault):
    request=gzip_request(case);_,invoke,_=case
    result=invoke('dx100-execute',request);assert result['outcome']['state']=='complete'
    trace=result['context']['debug_trace'];check=result['correctness']['checks'][0]['coverage']
    if fault=='compressed':Path(trace['path']).write_bytes(b'changed')
    elif fault=='deflate':
        path=Path(trace['path']);path.write_bytes(bytes.fromhex('1f8b0800000000000003')+b'\x07'+b'\0'*16)
        trace['sha256']=artifacts.file_hash(path);trace['bytes']=path.stat().st_size
        check['debug_trace']=copy.deepcopy(trace)
    elif fault=='decoded':
        trace['uncompressed_sha256']='f'*64;check['debug_trace']=copy.deepcopy(trace)
    elif fault=='counts':check['full_tiles']['count']=99
    elif fault=='location':
        other=Path(trace['path']).with_name('substitute.gz');other.write_bytes(Path(trace['path']).read_bytes())
        trace['path']=str(other);check['debug_trace']=copy.deepcopy(trace)
    elif fault=='legacy':result['request']['verification'].pop('trace_transport')
    elif fault=='request':result['request']['verification']['trace_transport']='unknown'
    elif fault=='downgrade':
        result['request']['verification'].pop('trace_transport')
        result['context'].pop('trace_transport');result['context'].pop('debug_trace')
        check.pop('debug_trace')
        Path(trace['path']).write_bytes(b'corrupt after deleting all transport metadata')
    elif fault=='null-request':result['request']['verification']['trace_transport']=None
    elif fault=='command':
        stage=next(row for row in result['stages'] if row['stage']=='simulation')
        stage['command']=[arg for arg in stage['command'] if not arg.startswith('--debug-file')]
    elif fault=='flags':result['context']['instrumentation']['debug_flags']='MAATrace'
    else:result['context'].pop('trace_transport')
    with pytest.raises(Failure):coverage.validate_trace(result)
    with pytest.raises(Failure):bfs_protocol._check_verifier_identity(result)


@pytest.mark.parametrize('value',[None,True,'',{},'gzip','gem5-gzip.v2'])
def test_unsupported_transport_refused_before_checkpoint(case,value):
    request=gzip_request(case);request['verification']['trace_transport']=value
    _,invoke,_=case;result=invoke('dx100-execute',request)
    assert result['outcome']['state']=='failed' and 'trace_transport' in result['outcome']['reason']
    assert not any(stage['stage'] in {'checkpoint','simulation'} for stage in result['stages'])


def test_stream_reader_charges_existing_deadline_without_decompressed_artifact(tmp_path):
    path=tmp_path/'trace.gz';path.write_bytes(gzip.compress(DEBUG.encode()))
    with pytest.raises(Failure,match='deadline'):
        list(coverage.trace_lines(path,{},time.monotonic()-1))
    assert sorted(p.name for p in tmp_path.iterdir())==['trace.gz']


def test_public_profile_package_and_query_reopen_full_debug_stream(case, records):
    """Real CLI collection/assembly, with explicit fixture source and synthetic gem5."""
    import yaml
    from swdb import workflow, profile_package
    from testkit.bfs_protocol import _workload_request
    from conftest import REPO
    request=gzip_request(case);_,invoke,folder=case
    records.copy_repo('applications')
    kernel=yaml.safe_load((REPO/'records/kernels/gapbs-bfs.yaml').read_text())
    kernel['baseline_implementation']='dx100-bfs-scalar'
    records.write('kernels/gapbs-bfs.yaml',kernel)
    records.write('implementations/dx100-bfs-scalar.yaml',yaml.safe_load(
        (REPO/'records/implementations/dx100-bfs-scalar.yaml').read_text()))
    def public(command, payload, succeeds=True):
        path=folder/(payload['id']+'.json');path.write_text(json.dumps(payload))
        extra=['--runs-dir',folder/'profile-runs'] if command=='dx100-profile' else []
        result=records.swdb(command,path,*extra,'--format','json',*extensa_args(command))
        assert result.returncode==(0 if succeeds else 1),result.stdout+result.stderr
        return json.loads(result.stdout) if result.stdout else None
    workload=public('register-workload',_workload_request(records,folder,
        {'num_vertices':3,'directed':True,'edges':[[0,1],[1,2]]}))
    representation=next(row for row in workload['definition']['representations'] if row['application']=='dx100-gapbs')
    request['workload']={'id':workload['id'],'source':0,'representation':{k:representation[k] for k in ('path','sha256')}}
    root=folder/'source';relative='benchmarks/gapbs/src/bfs.cc'
    text='void traversal(){ while(active){t.Start();step();t.Stop();PrintStep("td_maa", t.Seconds());} }\n'
    for base in (root,Path(request['model_root'])):
        path=base/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    artifact=artifacts.identify(root)
    source=workflow.record('source_snapshot','source',implementation='dx100-bfs-scalar',application='dx100-gapbs',
        revision='contract-fixture',artifact=artifact,context={},protections=[],regions=[])
    candidate=workflow.record('candidate','candidate',implementation='dx100-bfs-scalar',source_snapshot='source',
        artifact=artifact,context={},protections=[],state='unverified',artifact_role='source_baseline')
    records.write('source_snapshots/source.yaml',source);records.write('candidates/candidate.yaml',candidate)
    rows=[]
    for kind,begin,end in [('function',0,len(text)-1),('loop',text.index('while'),text.rindex('}')-1)]:
        fragment=text[begin:end]
        rows.append({'id':kind+':fixture','kind':kind,'name':kind,'path':relative,'lines':[1,1],
            'byte_range':[begin,end],'source_sha256':hashlib.sha256(fragment.encode()).hexdigest(),
            'text':fragment,'function':'traversal','metrics':{}})
    records.write('region_profiles/discovery.yaml',workflow.record('region_profile','discovery',candidate='candidate',
        source_snapshot='source',request={'fixture':True},discovery={'backend':'libclang-cindex'},
        outcome={'state':'complete','stage':'fixture','reason':None},stages=[],regions=rows,
        dynamic_memory=[],executions=[],raw_artifacts=[],reasons=[],gain_claim=False))
    simulator=Path(request['simulator']['path']);program=simulator.read_text()
    program=program.replace("    tick=[31400]", "    print('ROI started: 1 threads\\n td_maa 0.00040\\nROI End!!!')\n    tick=[31400]")
    program=program.replace("    tick=[31400]", "    with (out/'config.ini').open('a') as config:config.write('\\n[system.cpu_clk_domain]\\ntype=SrcClockDomain\\nclock=313\\n')\n    tick=[31400]")
    simulator.write_text(program);request.update(candidate='candidate',simulator=reference(simulator))
    evaluation=invoke('dx100-execute',request);assert evaluation['outcome']['state']=='complete'
    profile_request={'message_version':'1.0','id':'gzip-profile','evaluation':evaluation['id'],
        'discovery_profile':'discovery','budget':{'total_seconds':30}}
    profile=public('dx100-profile',profile_request)
    assert profile['outcome']['state']=='partial' and profile['executions'][0]['debug_trace']==evaluation['context']['debug_trace']
    assert next(row for row in profile['raw_artifacts'] if row['kind']=='debug_trace')['sha256']==evaluation['context']['debug_trace']['sha256']
    refreshed=json.loads(records.swdb('get',evaluation['id'],'--format','json').stdout)
    package_request={'message_version':'1.0','id':'gzip-package','implementation':'dx100-bfs-scalar',
        'evaluation':evaluation['id'],'region_profile':profile['id'],'context':profile_package._context(refreshed)}
    package=public('profile-package',package_request)
    assert package['evidence']['classification']=='contract_fixture' and package['gain_claim'] is False
    query=records.swdb('profile-strategies',package['id'],'--format','json',*EXTENSA)
    assert query.returncode==0,query.stderr
    assert json.loads(query.stdout)['evidence_validation']['state']=='valid'
    # New trace provenance cannot survive a missing exact diagnostic execution.
    missing=copy.deepcopy(profile);missing['executions'][0]['evaluation']='absent-execution'
    records.write('region_profiles/'+profile['id']+'.yaml',missing)
    # Use a fresh package ID so version checks do not mask execution provenance.
    missing_request={**package_request,'id':'gzip-package-missing-execution'}
    path=folder/'missing-package.json';path.write_text(json.dumps(missing_request))
    rejected=records.swdb('profile-package',path,'--format','json',*EXTENSA)
    assert rejected.returncode==1 and 'lacks its actual DX100 execution' in rejected.stderr
    records.write('region_profiles/'+profile['id']+'.yaml',profile)
    # The package record remains sealed and unchanged; only retained raw bytes corrupt.
    trace=Path(evaluation['context']['debug_trace']['path']);trace.write_bytes(trace.read_bytes()[:-5])
    failed=public('dx100-profile',{**profile_request,'id':'gzip-profile-corrupt'},False)
    assert failed['outcome']['state']=='failed' and 'debug trace' in failed['outcome']['reason']
    public('profile-package',{**package_request,'id':'gzip-package-corrupt'},False)
    query=records.swdb('profile-strategies',package['id'],'--format','json',*EXTENSA)
    assert query.returncode==0,query.stderr
    assert json.loads(query.stdout)['evidence_validation']['state']=='invalid'


@pytest.mark.parametrize('corrupt',[False,True])
def test_freeze_replays_diagnostic_gzip_identity_without_changing_primary(diagnostic_case, corrupt):
    """Reuse the explicitly synthetic freeze-admission fixture; no empirical claim."""
    module,item,store,diagnostic,_,_=diagnostic_case
    primary=copy.deepcopy(item['evaluation'])
    context=diagnostic['context'];stage=diagnostic['stages'][0]
    log=Path(stage['log']);trace=log.parent/'simulation'/coverage.TRACE_NAME;trace.parent.mkdir()
    trace.write_bytes(gzip.compress(log.read_bytes()))
    diagnostic['request'].setdefault('verification',{}).update(coverage=True,trace_transport=coverage.TRANSPORT)
    flags='MAATrace,MAARangeFuser,MAAIndirect'
    context['trace_transport']=coverage.TRANSPORT;context['debug_flags']=flags
    context.setdefault('instrumentation',{})['debug_flags']=flags
    stage['command']=['fixture-gem5','--debug-flags='+flags,'--debug-file='+str(trace)]
    check=diagnostic['correctness']['checks'][0]
    observed=coverage.observe(log,{'simTicks':'50','finalTick':'100'},16384,trace=trace)
    observed.update(accelerator_executed=True,instruction_counters={'system.maa.numInst':9})
    context['debug_trace']=observed['debug_trace'];check['coverage']=observed
    run=item['diagnostic']['executions'][0]
    run.update(correctness=copy.deepcopy(diagnostic['correctness']),debug_trace=copy.deepcopy(context['debug_trace']))
    item['package']['evidence']['diagnostic_executions']=copy.deepcopy(item['diagnostic']['executions'])
    if corrupt:
        trace.write_bytes(trace.read_bytes()[:-6])
        # Keep all compressed-file references self-consistent. CRC/EOF still rejects.
        def rehash(value):
            if isinstance(value,dict):
                if value.get('path')==str(trace):value.update(sha256=artifacts.file_hash(trace),bytes=trace.stat().st_size)
                for child in value.values():rehash(child)
            elif isinstance(value,list):
                for child in value:rehash(child)
        rehash(diagnostic);rehash(item)
        with pytest.raises(Failure,match='gzip'):
            coverage.validate_trace(diagnostic)
        with pytest.raises(ValueError,match='complete real passed v2 correctness'):
            module['supporting_case_evidence'](store,item)
    else:
        result=module['supporting_case_evidence'](store,item)
        assert all(result['coverage']['cases'].values())
        assert result['evaluation']==diagnostic['id'] and item['evaluation']==primary


# Fixture imported explicitly; its synthetic execution labels exercise strict readers only.
from test_bfs_freeze_pilot import diagnostic_case
