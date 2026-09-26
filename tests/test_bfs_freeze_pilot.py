"""Pilot admission and review boundaries; all durations are fixtures. Date: 2026-09-26."""
import copy
import json
from pathlib import Path
import runpy
import subprocess
import sys
from types import SimpleNamespace

import pytest

from conftest import REPO


@pytest.fixture
def pilot():
    module = runpy.run_path(str(REPO / 'scripts/bfs_freeze_pilot.py'))
    sources = [0, 1234, 7777]
    value = {'context': {'sources': sources, 'repetitions': 5, 'roi': 'bfs.complete_call.v1'},
             'build': {'binary_sha256': 'a' * 64}, 'timing': []}
    for position, source in enumerate(sources):
        for repetition in range(5):
            value['timing'].append({'source': source, 'source_position': position, 'repetition': repetition,
                'duration_s': 0.1 + repetition * 0.001, 'binary_sha256': 'a' * 64, 'roi': 'bfs.complete_call.v1',
                'basis': 'measured', 'quantity': 'native_roi_wall_seconds', 'verified': True,
                'evidence_kind': 'execution', 'output': f'/fixture/{position}/{repetition}'})
    return module, value, sources


def test_pilot_reports_actual_repeated_source_samples_separately(pilot):
    module, value, sources = pilot
    result = module['sample_grid'](value, sources, 5)
    assert len(result) == 3 and all(len(row['samples_seconds']) == 5 for row in result)
    assert result[0]['median_seconds'] == pytest.approx(0.102)
    assert result[0]['relative_spread'] == pytest.approx(0.004 / 0.102)


@pytest.mark.parametrize('fault', ['missing', 'duplicate', 'reused-output', 'boolean-source',
                                  'wrong-source', 'wrong-binary', 'wrong-roi', 'simulated', 'unverified', 'fixture'])
def test_calibration_cannot_invent_or_relabel_trial_cells(pilot, fault):
    module, value, sources = pilot
    row = value['timing'][-1]
    if fault == 'missing': value['timing'].pop()
    elif fault == 'duplicate': value['timing'].append(copy.deepcopy(row))
    elif fault == 'reused-output': row['output'] = value['timing'][0]['output']
    elif fault == 'boolean-source': value['context']['sources'] = [False, 1234, 7777]
    elif fault == 'wrong-source': row['source'] = 1234
    elif fault == 'wrong-binary': row['binary_sha256'] = 'b' * 64
    elif fault == 'wrong-roi': row['roi'] = 'bfs.dx100.traversal.v1'
    elif fault == 'simulated': row['basis'] = 'simulated'
    elif fault == 'unverified': row['verified'] = False
    else: row['evidence_kind'] = 'contract_fixture'
    with pytest.raises(ValueError):
        module['sample_grid'](value, sources, 5)


def test_missing_accelerator_size_evidence_does_not_make_native_freeze_publishable():
    module = runpy.run_path(str(REPO / 'scripts/bfs_freeze_pilot.py'))
    reasons = []
    result = module['accelerator_gate'](None, [], [], {}, reasons, 0.10)
    assert reasons and result == {'executions': [], 'repeatability': []}


@pytest.mark.parametrize('vertices,symmetrize,accepted', [
    (262144, True, True), (262143, True, True), (262145, True, False),
    (7777, True, False), (262144, False, False),
])
def test_pilot_respects_effective_generator_and_realized_vertex_range(vertices, symmetrize, accepted):
    module = runpy.run_path(str(REPO / 'scripts/bfs_freeze_pilot.py'))
    # Real scale18 Kronecker generation retained262143 vertices: the pinned
    # builder infers the range from its highest sampled endpoint. This fixture
    # tests admission only; it does not assert adjacency or empirical coverage.
    definition = {'family': 'kronecker', 'sources': [0, 1234, 7777],
        'generator': {'revision': 'e4fc4afdf894f295442cef3604667a469fab8e62',
            'parameters': {'scale': 18, 'edge_factor': 16, 'seed': 27491095, 'symmetrize': symmetrize}},
        'realized': {'num_vertices': vertices}, 'canonical_sha256': 'a' * 64,
        'representations': [{'application': app, 'canonical_sha256': 'a' * 64,
                             'adjacency_verified': True} for app in ('gapbs', 'dx100-gapbs')]}
    if accepted:
        module['workload_plan']({'definition': definition}, 18)
    else:
        with pytest.raises(ValueError, match='workload differs'):
            module['workload_plan']({'definition': definition}, 18)


@pytest.mark.parametrize('fault', [None, 'bare-lane', 'wrong-bind', 'wrong-config', 'wrong-host', 'missing-node'])
def test_recorded_native_lane_receipt_preserves_verified_identity(fault):
    module = runpy.run_path(str(REPO / 'scripts/bfs_freeze_pilot.py'))
    # Shape emitted by profile._verified_lane, not a claim of a live held lease.
    context = {'target': 'mbit10', 'host': 'mbit10',
               'lane': 'mbit10-evaluation-node1 (verified: affinity, bind:1, lease held, generation 375)',
               'backend_configuration': {'lane': 'mbit10-evaluation-node1'}}
    machine = {'id': 'mbit10', 'hostname': 'mbit10', 'numa_nodes': [{'node': 0}, {'node': 1}]}
    if fault == 'bare-lane': context['lane'] = 'mbit10-evaluation-node1'
    elif fault == 'wrong-bind': context['lane'] = context['lane'].replace('bind:1', 'bind:0')
    elif fault == 'wrong-config': context['backend_configuration']['lane'] = 'mbit10-evaluation-node0'
    elif fault == 'wrong-host': context['host'] = 'different-host'
    elif fault == 'missing-node': machine['numa_nodes'] = [{'node': 0}]
    if fault:
        with pytest.raises(ValueError, match='native pilot'):
            module['native_lane'](context, machine)
    else:
        assert module['native_lane'](context, machine) == 'mbit10-evaluation-node1'
        assert context['lane'].endswith('generation 375)')


def test_public_native_metadata_query_preserves_the_verifiable_lane_shape(records):
    module = runpy.run_path(str(REPO / 'scripts/bfs_freeze_pilot.py'))
    rid = 'bfs-native-smoke-20260925-a1.evaluation'
    # Query a copy of retained metadata only; its old changed candidate is never
    # admitted as a baseline pilot or reclassified into empirical freeze evidence.
    records.copy_repo()
    result = records.swdb('get', rid, '--format', 'json')
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)['context']
    context['backend_configuration'] = {'lane': context['lane'].split(' ', 1)[0]}
    machine = records.read('machines/mbit10.yaml')
    assert module['native_lane'](context, machine) == context['backend_configuration']['lane']
    context['backend_configuration']['lane'] = 'mbit10-evaluation-node0' if 'node1' in context['lane'] else 'mbit10-evaluation-node1'
    with pytest.raises(ValueError, match='requested configuration'):
        module['native_lane'](context, machine)


@pytest.mark.parametrize('fault', [None, 'missing-predecessor', 'same-version', 'unknown-predecessor', 'old-name-without-predecessor'])
def test_freeze_review_preserves_exact_version_predecessor(fault):
    from swdb import artifacts, bfs_protocol
    from swdb.cli import Failure
    module = runpy.run_path(str(REPO / 'scripts/bfs_freeze_pilot.py'))
    # Minimal sealed metadata exercises naming/version semantics only; no pilot
    # collection, valid settings, or publishable empirical freeze is implied.
    old = {'kind': 'protocol', 'requested_id': 'version-fixture', 'version': 1, 'supersedes': None,
           'invalidated_comparisons': [], 'settings': {}, 'workload_identities': {},
           'frozen_at': '2026-09-25T00:00:00Z', 'state': 'frozen'}
    old['identity_sha256'] = artifacts.digest(bfs_protocol._identity_payload(old))
    old['id'] = old['requested_id'] + '.' + old['identity_sha256'][:16]
    store = SimpleNamespace(get=lambda rid, kind=None: old if rid == old['id'] else None,
        of_kind=lambda kind: [SimpleNamespace(id=old['id'], data=old)] if kind == 'protocol' else [])
    spec = {'id': 'version-fixture', 'version': 2, 'supersedes': old['id']}
    if fault == 'missing-predecessor': spec = {'id': 'fresh-name', 'version': 2}
    elif fault == 'same-version': spec['version'] = 1
    elif fault == 'unknown-predecessor': spec['supersedes'] = 'unknown'
    elif fault == 'old-name-without-predecessor': spec = {'id': old['requested_id']}
    if fault:
        with pytest.raises((ValueError, Failure)):
            module['freeze_header'](spec, store)
    else:
        assert module['freeze_header'](spec, store) == {'message_version': '1.0', **spec}


@pytest.mark.parametrize('version,reason', [(1, 'one distinct native package per graph family'),
                                          (2, 'version greater than one requires supersedes')])
def test_public_prepare_without_completed_pilots_does_not_create_a_freeze(records, tmp_path, version, reason):
    request = tmp_path / 'selection.json'
    request.write_text(json.dumps({'id': 'unobserved', 'version': version, 'mode': 'native', 'packages': [],
        'maximum_relative_spread': 0.1, 'spread_justification': 'fixture only; not empirical',
        'size_selection': {'scale': 18, 'justification': 'fixture'}}))
    output = tmp_path / 'not-published'
    result = subprocess.run([sys.executable, str(REPO / 'scripts/bfs_freeze_pilot.py'), 'prepare', str(request),
                            '--records', str(records.path), '--output', str(output)], cwd=REPO,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode != 0 and reason in result.stderr
    assert not output.exists() and not (records.path / 'protocols').exists()


@pytest.fixture
def diagnostic_case(tmp_path):
    """Synthetic raw receipts exercise admission; never real execution evidence."""
    from pathlib import Path
    from swdb import artifacts
    from swdb.dx100_coverage import observe
    from test_dx100_witness import evaluation
    module = runpy.run_path(str(REPO / 'scripts/bfs_freeze_pilot.py'))
    folder = tmp_path / 'diagnostic'; folder.mkdir()
    d = evaluation(folder)
    def ref(name, text):
        path = folder / name; path.write_text(text)
        return {'path': str(path), 'sha256': artifacts.file_hash(path)}
    binary, simulator = ref('bfs', 'diagnostic fixture'), ref('gem5.opt', 'model fixture')
    d['request']['workload']['representation'] = ref('graph.sg', 'graph fixture')
    model = {'id': 'model', 'evidence_kind': 'execution', 'request': {},
             'outcome': {'state': 'complete', 'stage': 'build'}, 'binary': simulator}
    model_ref = {'evaluation': 'model', 'sha256': artifacts.digest(model)}
    d.update(id='diagnostic', candidate='author-candidate', source_snapshot='source',
             implementation='dx100-bfs-maa-reference', machine='test-machine', evidence_kind='execution')
    d['request'].update(binary=binary, simulator=simulator, candidate_build='diagnostic-build')
    d['build'].update(binary=binary['path'], binary_sha256=binary['sha256'],
                      simulator=simulator['path'], simulator_sha256=simulator['sha256'], model_build=model_ref)
    ctx = d['context']
    config = {'mode': 'MAA', 'tile_elements': 16384}
    ctx.update(candidate_build='diagnostic-build', candidate_driver=ref('candidate.cc', 'trusted fixture'),
        candidate_sha256='d'*64, sources=[0], threads=4, target='dx100-test', basis='simulated',
        model='model-definition', interface='maa-interface', roi='bfs.dx100.traversal.v1',
        configuration=config, backend_configuration=config,
        workload={'id':'graph', 'canonical_sha256':'f'*64, 'num_vertices':64})
    ctx['execution_binding'].update(binary=binary, simulator=simulator, roi=ctx['roi'])
    ctx['execution_binding_sha256'] = artifacts.digest(ctx['execution_binding'])
    stats = ref('roi-stats.txt', '---------- Begin Simulation Statistics ----------\n'
        'simTicks 50\nfinalTick 100\nsimFreq 1000000000000\nsystem.maa.numInst 9\n'
        '---------- End Simulation Statistics ----------\n')
    ctx['statistics'] = stats
    ctx['sealed_roi'].update(statistics=stats, execution_binding_sha256=ctx['execution_binding_sha256'])
    lines = ['60: system.maa: '+unit+'[0] End [instruction]' for unit in 'SIRA'] + [
        '61: system.maa: R[0] executeInstruction: output tile size: 16384',
        '62: system.maa: R[0] executeInstruction: output tile size: 7',
        '63: system.maa: I[0] Start [opcode(INDIR_ST_VECTOR) datatype(INT32) baseAddr(0x1000)]',
        '64: system.maa: I[0] recvData: 2 entries received for addr(0x2000)',
        '65: system.maa: I[0] recvData: new_data[0] = SPD[0][0] = 1/3/',
        '66: system.maa: I[0] recvData: new_data[0] = SPD[0][1] = 2/4/',
        'SWDB_DX100_ROI_SEALED',
        'SWDB_BFS_PARENT_STORAGE address=1000 count=64 element_bytes=4',
        'SWDB_BFS_RESULT source=0 vertices=64 parent_count=64 parent_fnv1a64=123456789abcdef0',
        'Verification: PASS']
    log = ref('simulation.log', '\n'.join(lines)+'\n')
    stage = d['stages'][0]; stage.update(log=log['path'],log_sha256=log['sha256'])
    check = d['correctness']['checks'][0]
    check.update(execution=d['id'], source=0, source_position=0, repetition=0, graph_sha256='f'*64,
        binary_sha256=binary['sha256'], output=log, output_sha256=log['sha256'], binding=ctx['execution_binding'],
        observed_verdicts=[{'verdict':'PASS','line':14,'after_seal':True}],
        parent_results=[{'source':0,'vertices':64,'parent_count':64,'parent_fnv1a64':'123456789abcdef0',
            'line':13,'after_seal':True,'fingerprint_kind':'noncryptographic FNV-1a over little-endian signed32 parent values'}],
        completion_sequence={'kind':'protected_candidate','observed':True,'times':[]})
    coverage = observe(Path(log['path']), {'simTicks':'50','finalTick':'100'}, 16384)
    coverage.update(accelerator_executed=True,instruction_counters={'system.maa.numInst':9})
    check['coverage']=coverage
    d['timing']=[{'source':0,'source_position':0,'repetition':0,'binary_sha256':binary['sha256'],
        'output_sha256':log['sha256'],'duration_s':5e-11,'quantity':'simulated_roi_seconds','basis':'simulated'}]
    def seal():
        path=Path(ctx['sealed_roi']['path'])
        payload={k:v for k,v in ctx['sealed_roi'].items() if k not in ('path','sha256')}
        path.write_text(json.dumps(payload));ctx['sealed_roi']['sha256']=artifacts.file_hash(path)
        check['sealed_roi']={k:ctx['sealed_roi'][k] for k in ('path','sha256')}
    seal()
    primary=copy.deepcopy(d);primary['id']='primary';primary['context'].pop('candidate_build')
    primary['correctness']['checks'][0]['coverage']['competing_parent_updates'].update(state='unobserved',count=0,samples=[])
    build={'id':'diagnostic-build','candidate':d['candidate'],'evidence_kind':'execution',
        'outcome':{'state':'complete','stage':'candidate_build'},'request':{'diagnostic_regions':True},
        'context':{'function':'DOBFSMAA','roi':ctx['roi'],'accelerated_requested':True,
            'candidate_sha256':ctx['candidate_sha256'],'model_build':'model','diagnostic':{
                'discovery':{'backend':'libclang-cindex'}, 'difference':'source-scope diagnostic fixture'}},
        'build':{'binary':binary['path'],'binary_sha256':binary['sha256']}}
    run={'kind':'regions','evaluation':d['id'],'source':0,'source_position':0,'repetition':0,
        'binary_sha256':binary['sha256'],'output':log['path'],'region_output':log['path'],
        'output_sha256':log['sha256'],'region_output_sha256':log['sha256'],
        'correctness':copy.deepcopy(d['correctness']),'execution_outcome':copy.deepcopy(d['outcome']),
        'evidence_kind':'execution','differences_from_primary':['source-scope diagnostic fixture']}
    profile={'id':'profile','executions':[run],
        'artifacts':{'region_binary':{**binary,'difference':'source-scope diagnostic fixture'}},
        'discovery':{'backend':'libclang-cindex'}}
    item={'evaluation':primary,'diagnostic':profile,'implementation':{'id':'dx100-bfs-maa-reference'},
          'package':{'id':'package','evidence':{'diagnostic_executions':copy.deepcopy(profile['executions'])}}}
    records={x['id']:x for x in (d,build,model)}
    store=SimpleNamespace(get=lambda rid,kind=None:records.get(rid))
    return module,item,store,d,build,seal


def test_diagnostic_cases_are_separate_provenance_without_primary_promotion(diagnostic_case):
    module,item,store,d,build,_=diagnostic_case
    original=copy.deepcopy(item)
    result=module['supporting_case_evidence'](store,item)
    assert result['evaluation']=='diagnostic' and result['primary_evaluation']=='primary'
    assert all(result['coverage']['cases'].values())
    assert all(r['state']=='verified' for r in result['raw_verification'])
    assert result['differences_from_primary']==['source-scope diagnostic fixture']
    assert item==original
    assert item['evaluation']['correctness']['checks'][0]['coverage']['competing_parent_updates']['state']=='unobserved'


@pytest.mark.parametrize('fault', ['unverified','fixture','v1','wrong-source','wrong-config','wrong-roi',
    'wrong-cell','wrong-candidate','wrong-model','wrong-binary','wrong-build','stale-check',
    'changed-log','missing-log','zero-counter','parent-base','outside-roi','wrong-runtime','missing-differences'])
def test_diagnostic_case_admission_rejects_incompatible_or_unproved_evidence(diagnostic_case,fault):
    from pathlib import Path
    from swdb.cli import Failure
    module,item,store,d,build,seal=diagnostic_case
    check=d['correctness']['checks'][0]
    if fault=='unverified':d['correctness']['state']='unverified'
    elif fault=='fixture':d['evidence_kind']='contract_fixture'
    elif fault=='v1':d['context']['verifier']='dx100.bfs.verifier.v1'
    elif fault=='wrong-source':d['context']['source']=1
    elif fault=='wrong-config':d['context']['backend_configuration']['tile_elements']=1024
    elif fault=='wrong-roi':d['context']['roi']='bfs.complete_call.v1'
    elif fault=='wrong-cell':d['timing'][0]['repetition']=1
    elif fault=='wrong-candidate':d['candidate']='other'
    elif fault=='wrong-model':d['build']['model_build']['sha256']='0'*64
    elif fault=='wrong-binary':d['build']['binary_sha256']='0'*64
    elif fault=='wrong-build':build['context']['function']='DOBFS'
    elif fault=='wrong-runtime':d['context']['instrumentation']['verifier_runtime']['driver_sha256']='0'*64
    elif fault=='missing-differences':build['context']['diagnostic'].pop('difference')
    elif fault=='stale-check':item['diagnostic']['executions'][0]['correctness']['checks'][0]['coverage']['full_tiles']['count']=999
    elif fault=='changed-log':Path(check['output']['path']).write_text('changed')
    elif fault=='missing-log':Path(check['output']['path']).unlink()
    else:
        if fault=='zero-counter':check['coverage']['instruction_counters']['system.maa.numInst']=0
        elif fault=='parent-base':check['coverage']['competing_parent_updates']['parent_storage']['virtual_address']=999
        elif fault=='outside-roi':check['coverage']['tick_interval']=[0,500]
        item['diagnostic']['executions'][0]['correctness']=copy.deepcopy(d['correctness'])
        item['package']['evidence']['diagnostic_executions']=copy.deepcopy(item['diagnostic']['executions'])
    with pytest.raises((ValueError,Failure)):
        module['supporting_case_evidence'](store,item)


@pytest.mark.parametrize('fault', [None, 'fallback', 'duplicate-replay', 'wrong-position', 'boolean-position', 'missing'])
def test_calibration_grid_keeps_primary_execution_and_separate_case_requirements(monkeypatch, fault):
    # Isolate the grid after packet/raw admission, which the preceding tests
    # exercise with bounded synthetic files. This is not empirical evidence.
    module = runpy.run_path(str(REPO / 'scripts/bfs_freeze_pilot.py'))
    items = {}
    for position, source in enumerate(module['SOURCES']):
        for repetition in range(2):
            rid = f'fixture.s{position}.r{repetition}'
            evaluation = {'id': rid, 'context': {'basis': 'simulated', 'threads': 4,
                'roi': 'bfs.dx100.traversal.v1', 'backend_configuration': {'mode': 'MAA'}, 'instrumentation': {}},
                'build': {'binary_sha256': 'a'*64}, 'stages': [], 'timing': [{
                    'source': source, 'source_position': position, 'repetition': repetition,
                    'output': '/fixture/' + rid, 'duration_s': 0.1, 'verified': True,
                    'quantity': 'simulated_roi_seconds', 'basis': 'simulated'}]}
            items[rid] = {'evaluation': evaluation, 'implementation': {'id': 'dx100-bfs-maa-reference'},
                'workload': {'id': 'workload'}, 'record_identities': {}, 'availability': []}
    selected = list(items)
    if fault == 'duplicate-replay': items[selected[1]]['evaluation']['timing'][0]['repetition'] = 0
    elif fault == 'wrong-position': items[selected[1]]['evaluation']['timing'][0]['source_position'] = 1
    elif fault == 'boolean-position': items[selected[1]]['evaluation']['timing'][0]['source_position'] = False
    elif fault == 'missing': selected.pop()
    gate = module['accelerator_gate']
    monkeypatch.setitem(gate.__globals__, 'packet', lambda store, rid: items[rid])
    cases = {case: False for case in ('full_tiles', 'tail_tiles', 'competing_parent_updates')}
    monkeypatch.setattr(module['bfs_coverage'], '_acceleration', lambda evaluation, store:
        {'executed': fault != 'fallback', 'cases': cases.copy()})
    supports = []
    def support(store, item):
        supports.append(item['evaluation']['id'])
        return {'evaluation': supports[-1]+'.diagnostic', 'evaluation_sha256': 'b'*64,
            'build_evaluation': 'diagnostic-build', 'build_sha256': 'c'*64,
            'model_build': {'evaluation': 'model', 'sha256': 'd'*64},
            'coverage': {'executed': True, 'cases': dict.fromkeys(cases, True)}}
    monkeypatch.setitem(gate.__globals__, 'supporting_case_evidence', support)
    reasons = []
    if fault in {'fallback', 'wrong-position', 'boolean-position'}:
        with pytest.raises(ValueError): gate(None, selected, [{'workload': {'id': 'workload'}}], {}, reasons, .1)
        if fault == 'fallback': assert not supports
    else:
        result = gate(None, selected, [{'workload': {'id': 'workload'}}], {}, reasons, .1)
        assert bool(reasons) == (fault is not None)
        assert all(not any(row['coverage']['cases'].values()) for row in result['executions'])
        assert all(row['supporting_case_evidence'] for row in result['executions'])
        if fault is None: assert len(result['repeatability']) == 3


@pytest.fixture
def aa_control(tmp_path, monkeypatch):
    """Synthetic receipts, never catalogued or presented as empirical evidence."""
    from scripts import bfs_native_repeatability as repeat
    from swdb import artifacts
    module = runpy.run_path(str(REPO / 'scripts/bfs_freeze_pilot.py'))
    folder = tmp_path / 'aa'; folder.mkdir()
    def file(name, contents):
        path = folder / name; path.write_text(contents)
        return {'path': str(path), 'sha256': artifacts.file_hash(path)}
    source_dir = folder / 'source'; source_dir.mkdir(); (source_dir / 'bfs.cc').write_text('// fixture\n')
    source_artifact = artifacts.identify(source_dir)
    implementation = {'id': 'dx100-bfs-scalar', 'function': 'DOBFS', 'code': [{'root': 'apps', 'path': 'bfs.cc'}]}
    candidate = {'id': 'unchanged', 'implementation': implementation['id'], 'artifact_role': 'source_baseline',
        'source_snapshot': 'source', 'artifact': source_artifact, 'context': {'function': 'DOBFS'}}
    source = {'id': 'source', 'implementation': implementation['id'], 'artifact': source_artifact,
              'context': {'function': 'DOBFS'}}
    machine = {'id': 'mbit10', 'hostname': 'mbit10', 'numa_nodes': [{'node': 0}, {'node': 1}]}
    binary, graph = file('binary', 'binary fixture'), file('graph', 'graph fixture')
    plan = json.loads(repeat.PLAN.read_text())
    receipt = {'id': repeat.RUN_ID, 'state': 'complete', 'role': 'second_unchanged_native_calibration_block',
        'bounds': repeat.BOUNDS, 'profiling': False, 'gain_claim': False, 'protocol_freeze': False,
        'verifier_module_sha256': '2'*64, 'inherited_runtime_settings': dict.fromkeys(
            ('OMP_THREAD_LIMIT', 'OMP_WAIT_POLICY', 'GOMP_SPINCOUNT', 'GOMP_CPU_AFFINITY')),
        'cells': [{'id': c['id'], 'state': 'complete'} for c in plan['cells']], 'stages': []}
    packets, records, seconds = [], {x['id']: x for x in (candidate, source, implementation, machine)}, []
    def trials(value, scale):
        value['timing'], value['correctness'] = [], {'state': 'passed', 'checks': []}
        for repetition in range(5):
            for position, vertex in enumerate(repeat.SOURCES):
                duration = scale * (1 + .01*repetition + .1*position)
                observed = file(value['id'] + f'.{position}.{repetition}.json', json.dumps({'duration_s': duration}))
                row = {'source': vertex, 'source_position': position, 'repetition': repetition,
                    'duration_s': duration, 'roi': 'bfs.complete_call.v1', 'basis': 'measured',
                    'quantity': 'native_roi_wall_seconds', 'verified': True, 'evidence_kind': 'execution',
                    'binary_sha256': binary['sha256'], 'output': observed['path'], 'output_sha256': observed['sha256']}
                value['timing'].append(row)
                value['correctness']['checks'].append({**{k: row[k] for k in (
                    'source','source_position','repetition','binary_sha256','output_sha256')},
                    'passed': True, 'graph_sha256': 'f'*64, 'verifier': 'swdb.bfs.structural.v1'})
    for index in (0, 2):
        cell = plan['cells'][index]
        request = {'message_version':'1.0','id':cell['first_evaluation'],'candidate':candidate['id'],
            'machine':'mbit10','threads':4,'repetitions':5,'sources':repeat.SOURCES,'roi':'bfs.complete_call.v1',
            'target_configuration':{'lane':repeat.LANE},'workload':{'id':f'graph{index}'},
            'comparison_baseline':implementation['id'],'budget':{'build_seconds':180,'run_seconds':60,'total_seconds':1200}}
        first = {'id':request['id'],'request':request,'candidate':candidate['id'],'implementation':implementation['id'],
            'source_snapshot':source['id'],'machine':'mbit10','evidence_kind':'execution',
            'outcome':{'state':'complete'},'stages':[],
            'context':{'host':'mbit10','target':'mbit10','machine_sha256':artifacts.digest(machine),
                'candidate_sha256':source_artifact['sha256'],'function':'DOBFS','basis':'measured',
                'roi':'bfs.complete_call.v1','threads':4,'sources':repeat.SOURCES,'repetitions':5,'protocol':None,
                'verifier':'swdb.bfs.structural.v1','verifier_sha256':'1'*64,
                'lane':'mbit10-evaluation-node1 (verified: affinity, bind:1, lease held, generation 375)',
                'backend_configuration':{'lane':repeat.LANE},'instrumentation':{'treatment':'included'},
                'workload':{'id':f'graph{index}','canonical_sha256':'f'*64,'adjacency_order_sha256':'f'*64,
                    'canonical_path':graph['path'],'canonical_file_sha256':graph['sha256'],'sources':repeat.SOURCES}},
            'build':{'compiler':'g++','compiler_version':['fixture'],'flags':['-O3'],
                'template_sha256':'a'*64,'wrapper_sha256':'b'*64,'binary':binary['path'],
                'binary_sha256':binary['sha256'],'execution_environment':copy.deepcopy(repeat.ENVIRONMENT)}}
        trials(first, 1)
        cell.update(first_evaluation_sha256=artifacts.digest(first), implementation=implementation['id'],
            candidate=candidate['id'],workload=f'graph{index}',source_sha256=source_artifact['sha256'],
            canonical_graph_sha256='f'*64,primary_binary_sha256=binary['sha256'],compiler='g++',flags=['-O3'],
            driver_template_sha256='a'*64)
        second = copy.deepcopy(first); second.update(id=cell['id'],request=repeat.first_request(first,cell,machine))
        second['context']['verifier_sha256']='2'*64;trials(second,1)
        records.update({first['id']:first,second['id']:second});seconds.append(second)
        packets.append({'evaluation':first,'package':{'id':f'package{index}'},'diagnostic':{'id':f'profile{index}'}})
        receipt['cells'][index].update(evaluation=second['id'],first_evaluation=first['id'],
            first_record_sha256=artifacts.digest(first),first_binary_sha256=binary['sha256'],
            second_binary_sha256=binary['sha256'],first_verifier_module_sha256='1'*64,compiler_sha256='c'*64)
    plan_ref = file('plan.json',json.dumps(plan));monkeypatch.setattr(repeat,'PLAN',Path(plan_ref['path']))
    receipt['plan']=plan_ref
    spec={'maximum_relative_spread':10**6,'repeatability':{'evaluations':{
        p['evaluation']['id']:s['id'] for p,s in zip(packets,seconds)}}}
    def save():
        receipt['stages']=[]
        for second in seconds:
            observed=file(second['id']+'.result.json',json.dumps(second))
            receipt['stages'].append({'output':observed['path'],'stdout_sha256':observed['sha256'],
                                      'state':'complete','returncode':0})
        spec['repeatability']['driver_receipt']=file('driver.json',json.dumps(receipt))
    save()
    store=SimpleNamespace(get=lambda rid,kind=None:records.get(rid),
        application_of=lambda impl:{'source':{'local_path':str(source_dir)}})
    return module,spec,packets,store,seconds,receipt,save,trials


@pytest.mark.parametrize('scale', [.5, 1, 2])
def test_unchanged_control_checks_both_directions_independent_of_spread_ceiling(aa_control,scale):
    module,spec,packets,store,seconds,receipt,save,trials=aa_control
    trials(seconds[0],scale);save()
    identities,gates={},[]
    result=module['repeatability_control'](spec,packets,store,identities,gates)
    assert result['state']==('no_numerical_gain_detected' if scale==1 else 'numerical_gain_detected')
    assert bool(gates)==(scale!=1)
    assert len(result['retained_driver']['cells'])==4 and len(result['pairs'])==2
    assert all(len(b['timing'])==15 for p in result['pairs'] for b in p['blocks'])
    assert result['pairs'][0]['condition_limits']['verifier_module_equal'] is False
    assert result['pairs'][0]['diagnostics']['second'] is None
    legs={d['direction']:d['numerical_gain_leg'] for d in result['pairs'][0]['directions']}
    assert legs=={'first_over_second':scale<1,'second_over_first':scale>1}
    assert all(second['id'] in identities for second in seconds)


@pytest.mark.parametrize('fault',['missing-input','missing-map','wrong-block','missing-record','missing-receipt',
    'fixture','missing-trial','wrong-binary','wrong-wrapper','changed-source','wrong-settings','bad-correctness',
    'changed-public-result','changed-raw','missing-raw','failed-driver','altered-receipt'])
def test_control_rejects_missing_changed_candidate_or_incomplete_evidence(aa_control,fault):
    module,spec,packets,store,seconds,receipt,save,trials=aa_control
    second=seconds[0]
    if fault=='missing-input':spec.pop('repeatability')
    elif fault=='missing-map':spec['repeatability']['evaluations'].pop(packets[0]['evaluation']['id'])
    elif fault=='wrong-block':spec['repeatability']['evaluations'][packets[0]['evaluation']['id']]='candidate-assessment'
    elif fault=='missing-record':store.get=lambda rid,kind=None: None
    elif fault=='missing-receipt':Path(spec['repeatability']['driver_receipt']['path']).unlink()
    elif fault=='fixture':second['evidence_kind']='contract_fixture';save()
    elif fault=='missing-trial':second['timing'].pop();save()
    elif fault=='wrong-binary':second['build']['binary_sha256']='f'*64;save()
    elif fault=='wrong-wrapper':second['build']['wrapper_sha256']='f'*64;save()
    elif fault=='changed-source':store.get(second['candidate'])['proposal']='rewrite'
    elif fault=='wrong-settings':second['context']['threads']=8;save()
    elif fault=='bad-correctness':second['correctness']['checks'][0]['passed']=False;save()
    elif fault=='changed-public-result':second['timing'][0]['duration_s']=99
    elif fault=='changed-raw':Path(second['timing'][0]['output']).write_text('changed')
    elif fault=='missing-raw':Path(second['timing'][0]['output']).unlink()
    elif fault=='failed-driver':receipt['state']='failed';save()
    else:Path(spec['repeatability']['driver_receipt']['path']).write_text('{}')
    gates=[]
    result=module['repeatability_control'](spec,packets,store,{},gates)
    assert result['state']=='unqualified' and gates and result['gain_claim'] is False
    assert 'not qualified' in gates[-1]


@pytest.mark.parametrize('field,value', [
    ('plan', []), ('plan', None), ('cells', [[]]), ('cells', {}),
    ('stages', [None]), ('stages', {})])
def test_malformed_nested_control_receipts_remain_unqualified(aa_control, field, value):
    from swdb import artifacts
    module,spec,packets,store,seconds,receipt,save,trials=aa_control
    receipt[field]=value
    ref=spec['repeatability']['driver_receipt'];path=Path(ref['path'])
    path.write_text(json.dumps(receipt));ref['sha256']=artifacts.file_hash(path)
    gates=[]
    result=module['repeatability_control'](spec,packets,store,{},gates)
    assert result['state']=='unqualified' and result['gain_claim'] is False
    assert 'malformed nested types' in result['reason'] and gates
