"""Native package comparisons using actual collected shapes and synthetic counters.

Updated: 2026-09-26. These fixtures never establish empirical performance.
"""
import copy
import datetime
import hashlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from conftest import REPO, records as records_fixture
from test_bfs_protocol import protocol_seed, _command, _fixture_rebind, _payload
from swdb import artifacts, bfs_discovery, bfs_profiling, profile_package, workflow, yamlio


ACTUAL = REPO / 'records/region_profiles/bfs-native-pilot-20260925-upstream18-a2.uniform-random.profile.yaml'


def ref(path):
    return {'path': str(path), 'sha256': artifacts.file_hash(path)}


def assemble(records, tmp, primary, profile, version=1):
    return _command(records, 'profile-package', _payload(tmp, profile['id'] + '.assemble', {
        'message_version': '1.0', 'id': primary['id'] + '.package', 'version': version,
        'evaluation': primary['id'], 'region_profile': profile['id'], 'implementation': primary['implementation'],
        'context': profile_package._context(primary)}))


def diagnostic_fixture(records, tmp, primary, template, runtime, ns):
    """Keep all 24 actual compiler region extents; synthesize only fixture runs."""
    candidate = records.read('candidates/' + primary['candidate'] + '.yaml')
    source = Path(candidate['artifact']['path']) / 'src/bfs.cc'
    raw = source.read_bytes()
    folder = tmp / (primary['id'] + '.diagnostic'); folder.mkdir()
    regions = copy.deepcopy(template['regions'])
    for row in regions:
        fragment = raw[slice(*row['byte_range'])]
        row.update(text=fragment.decode(), source_sha256=hashlib.sha256(fragment).hexdigest(),
                   source_artifact_sha256=candidate['artifact']['sha256'])
    (folder / 'runtime.hpp').write_bytes(runtime.read_bytes())
    (folder / 'regions_driver.cc').write_text('// Explicit nonexecuted wrapper fixture\n')
    (folder / 'instrumented_bfs.cc').write_bytes(bfs_discovery.instrument(source, regions))
    binary = folder / 'bfs-regions'; binary.write_text('Explicit diagnostic binary fixture ' + primary['id'])
    binary_hash = artifacts.file_hash(binary)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    build = {key: copy.deepcopy(primary['build'][key]) for key in ('compiler', 'compiler_version', 'flags')}
    if 'native_runtime' in primary['build']:
        build['native_runtime'] = copy.deepcopy(primary['build']['native_runtime'])
    build.update(directory=str(folder), command=[*primary['build']['command'][:-3], str(folder / 'regions_driver.cc'), '-o', str(binary)],
        wrapper_sha256=artifacts.file_hash(folder / 'regions_driver.cc'), runtime_sha256=artifacts.file_hash(runtime),
        instrumented_source_sha256=artifacts.file_hash(folder / 'instrumented_bfs.cc'))
    stages = [{'stage': 'region_build', 'started': now, 'state': 'complete', 'returncode': 0, 'command': build['command']}]
    executions, memory = [], []
    for position, source_id in enumerate(primary['context']['sources']):
        output = folder / f'regions-0-{position}.json'
        original = next(row for row in primary['timing'] if row['source_position'] == position and row['repetition'] == 0)
        output.write_bytes(Path(original['output']).read_bytes())
        counter_path = Path(str(output) + '.regions.json')
        counter_path.write_text(json.dumps({'format': 'swdb.bfs.regions.v1', 'clock': 'CLOCK_THREAD_CPUTIME_ID', 'errors': 0,
            'regions': [{'index': index, 'inclusive_ns': 2 * ns, 'exclusive_ns': ns, 'invocations': 2}
                        for index in range(len(regions))]}))
        # The check is a real structural graph check of the synthetic parent output.
        from swdb.bfs_native import read_canonical_graph
        graph, _ = read_canonical_graph(primary['context']['workload']['canonical_path'])
        check = bfs_profiling._trial_output(output, graph, source_id, primary['context']['threads'])
        cell = {'source': source_id, 'source_position': position, 'repetition': 0}
        run = {'kind': 'regions', **cell, 'binary_sha256': binary_hash, 'output': str(output),
               'region_output': str(counter_path), 'region_output_sha256': artifacts.file_hash(counter_path), **check}
        executions.append(run)
        executions.append({**run, 'kind': 'memory', 'raw_artifact': str(output), 'raw_sha256': artifacts.file_hash(output)})
        memory.append({'metric': 'fixture_reads', 'available': True, 'value': 10, 'unit': 'count', 'definition': 'synthetic counter',
            'basis': 'simulated', 'scope': 'ROI', 'collector': 'fixture-model', 'artifact_sha256': binary_hash,
            'source_artifact_sha256': candidate['artifact']['sha256'], 'execution': cell,
            'raw_artifact': str(output), 'raw_sha256': artifacts.file_hash(output)})
        stages.append({'stage': 'region_execution', 'state': 'complete', 'returncode': 0, 'started': now,
            'command': [str(binary), primary['context']['workload']['canonical_path'], str(source_id), str(output)]})
    for row in regions:
        row.update(metrics={'inclusive_thread_cpu_seconds': 4 * ns / 1e9,
                            'exclusive_thread_cpu_seconds': 2 * ns / 1e9, 'invocations': 4}, artifact_sha256=binary_hash)
    context = copy.deepcopy(primary['context'])
    context.update(primary_binary_sha256=primary['build']['binary_sha256'], primary_evaluation=primary['id'], repetitions=1,
        timing_basis=template['context']['timing_basis'], overhead_treatment=template['context']['overhead_treatment'])
    profile = workflow.record('region_profile', primary['id'] + '.profile',
        request={'message_version': '1.0', 'fixture': True, 'evaluation': primary['id'], 'repetitions': 1},
        evaluation=primary['id'], candidate=candidate['id'], source_snapshot=candidate['source_snapshot'],
        implementation=primary['implementation'], machine=primary['machine'], context=context,
        outcome={'state': 'partial', 'stage': 'profiling', 'reason': 'Explicit synthetic counters; actual collected data shape.'},
        stages=stages, build=build, discovery=copy.deepcopy(template['discovery']), regions=regions,
        dynamic_memory=memory, executions=executions, raw_artifacts=[], reasons=[], gain_claim=False,
        artifacts={'primary_binary_sha256': primary['build']['binary_sha256'],
                   'region_binary': ref(binary), 'memory_binary': ref(binary)})
    records.write('region_profiles/' + profile['id'] + '.yaml', profile)
    package = assemble(records, tmp, primary, profile)
    assert package['completeness'] == 'fixture', package['reasons']
    return profile, package


@pytest.fixture(scope='module')
def native_seed(protocol_seed, tmp_path_factory):
    old_records, _, old_protocol, _, evaluations, comparison = protocol_seed
    tmp = tmp_path_factory.mktemp('native-regional'); records = records_fixture.__wrapped__(tmp)
    shutil.copytree(old_records.path, records.path, dirs_exist_ok=True)
    template = yamlio.load(ACTUAL)
    assert len(template['regions']) == 24
    runtime = tmp / 'runtime.hpp'; runtime.write_text('// synthetic CPU scope runtime fixture\n')
    collector = {key: template['discovery'][key] for key in ('backend', 'library_sha256', 'pass_sha256', 'collector_sha256')}
    collector.update(clock='CLOCK_THREAD_CPUTIME_ID', runtime_sha256=artifacts.file_hash(runtime))
    selected = next(row['id'] for row in template['regions'] if row['kind'] == 'loop')
    settings = copy.deepcopy(old_protocol['settings'])
    settings['region_pairs'] = [{'semantic_region': 'selected traversal loop', 'baseline': selected, 'candidate': selected,
        'evidence': 'native_diagnostic_profile.v1', 'collector': collector, 'diagnostic_repetitions': 1,
        'attribution': 'exclusive', 'scope': 'accumulated'}]
    protocol = _command(records, 'freeze-protocol', _payload(tmp, 'freeze-native-regions', {
        'message_version': '1.0', 'id': 'native-region-policy', 'settings': settings}))
    primaries, profiles, packages = {}, {}, {}
    for role, initial in evaluations.items():
        primary = _fixture_rebind(initial, protocol, role, 'native-regional-' + role)
        assert not primary['profiling'].get('regions')
        records.write('evaluations/' + primary['id'] + '.yaml', primary)
        profile, package = diagnostic_fixture(records, tmp, primary, template, runtime, 30000000 if role == 'baseline' else 10000000)
        primaries[role], profiles[role] = primary, profile
        packages[primary['id']] = package['id']
    request = {**comparison, 'id': 'native-regional-comparison', 'protocol': protocol['id'], 'region_packages': packages,
        'baseline_evaluation': primaries['baseline']['id'], 'candidate_evaluation': primaries['candidate']['id']}
    return records, request, primaries, profiles, protocol


@pytest.fixture
def native_setup(native_seed, records):
    original, *values = native_seed
    shutil.copytree(original.path, records.path, dirs_exist_ok=True)
    return records, *copy.deepcopy(values)


def test_public_native_cpu_comparison_uses_actual_profile_shape_and_separate_primary_wall(native_setup, tmp_path):
    records, request, primaries, _, _ = native_setup
    result = _command(records, 'compare-evaluations', _payload(tmp_path, 'compare', request))
    assert result['decision']['state'] == 'fixture_comparison' and not result['gain_claim']
    region = result['region_comparisons'][0]
    assert region['duration_ratio'] == pytest.approx(3) and not region['primary_bfs_roi'] and not region['gain_claim']
    assert 'confidence_interval' not in region and result['metrics']['fixture_ratio'] == pytest.approx(2)
    assert all(len(rows) == 2 for rows in region['samples'].values())
    assert all(len(primary['timing']) == 10 and not primary['profiling'].get('regions') for primary in primaries.values())
    assert all(row['quantity'] == 'diagnostic_thread_cpu_seconds' and row['correctness']['passed']
               and row['primary_binary_sha256'] != row['diagnostic_binary_sha256']
               for rows in region['samples'].values() for row in rows)
    chain = json.loads(records.swdb('get', result['id'], '--chain', '--format', 'json').stdout)['records']
    assert set(request['region_packages'].values()) <= set(chain)


@pytest.mark.parametrize('fault', ['absent-package', 'stale-profile', 'wrong-binary', 'wrong-collector',
    'wrong-scope', 'wrong-source', 'wrong-repetition', 'failed-check', 'pre-freeze', 'raw-values',
    'raw-unavailable', 'raw-parent', 'instrumentation', 'wrong-build', 'hidden-build-flag',
    'runtime-missing', 'runtime-changed'])
def test_public_native_region_comparison_rejects_incompatible_diagnostics(native_setup, tmp_path, fault):
    records, request, primaries, profiles, _ = native_setup
    primary, profile = primaries['candidate'], profiles['candidate']
    if fault == 'absent-package':
        request['region_packages'].pop(primary['id'])
    else:
        selected = next(row for row in profile['regions'] if row['kind'] == 'loop')
        run = next(row for row in profile['executions'] if row['kind'] == 'regions')
        if fault == 'wrong-binary': profile['artifacts']['region_binary']['sha256'] = 'f' * 64
        elif fault == 'wrong-collector': profile['discovery']['collector_sha256'] = 'f' * 64
        elif fault == 'wrong-scope': selected['scope'] = 'unbounded process CPU time'
        elif fault == 'wrong-source': run['source'] = 3
        elif fault == 'wrong-repetition': run['repetition'] = 1
        elif fault == 'failed-check': run['correctness']['passed'] = False
        elif fault == 'pre-freeze': profile['stages'][1]['started'] = '2000-01-01T00:00:00Z'
        elif fault == 'raw-unavailable': run['region_output'] = '/missing/regions.json'
        elif fault == 'raw-parent':
            output = tmp_path / 'bad-parent.json'; output.write_text('{}')
            run.update(output=str(output), output_sha256=artifacts.file_hash(output))
            counters = Path(str(output) + '.regions.json'); counters.write_bytes(Path(run['region_output']).read_bytes())
            run.update(region_output=str(counters), region_output_sha256=artifacts.file_hash(counters))
            profile['stages'][1]['command'][-1] = str(output)
        elif fault == 'instrumentation': selected['insertion_range'][0] += 1
        elif fault == 'wrong-build': profile['build']['flags'] = ['-O0']
        elif fault == 'runtime-missing': profile['build'].pop('native_runtime')
        elif fault == 'runtime-changed': profile['build']['native_runtime']['environment']['OMP_WAIT_POLICY'] = 'ACTIVE'
        elif fault == 'hidden-build-flag':
            profile['build']['command'].insert(-3, '-Ofast')
            profile['stages'][0]['command'] = copy.deepcopy(profile['build']['command'])
        else: selected['metrics']['exclusive_thread_cpu_seconds'] *= 2
        records.write('region_profiles/' + profile['id'] + '.yaml', profile)
        if fault != 'stale-profile':
            package = assemble(records, tmp_path, primary, profile, version=2)
            if fault.startswith('runtime-'):
                assert 'runtime' in str(package['reasons'])
                assert package['completeness'] == 'incomplete'
            request['region_packages'][primary['id']] = package['id']
    result = _command(records, 'compare-evaluations', _payload(tmp_path, 'bad-compare', request), succeeds=False)
    assert result['decision']['state'] == 'rejected' and not result['gain_claim']
    assert result['region_comparisons'] == []
    if fault == 'raw-values': assert 'raw trial reports' in str(result['decision']['reasons'])
    if fault.startswith('runtime-'): assert 'diagnostic package is incomplete' in str(result['decision']['reasons'])


@pytest.mark.parametrize('fault', ['mode', 'clock', 'collector', 'repetitions-bool', 'repetitions-excess'])
def test_public_freeze_rejects_incompatible_native_diagnostic_contract(native_setup, tmp_path, fault):
    records, _, _, _, protocol = native_setup
    settings = protocol['settings']; pair = settings['region_pairs'][0]
    if fault == 'mode': pair['evidence'] = 'simulated_diagnostic_profile'
    elif fault == 'clock': pair['collector']['clock'] = 'steady_clock'
    elif fault == 'collector': pair['collector'].pop('collector_sha256')
    elif fault == 'repetitions-bool': pair['diagnostic_repetitions'] = True
    else: pair['diagnostic_repetitions'] = 11
    result = records.swdb('freeze-protocol', _payload(tmp_path, 'bad-freeze', {
        'message_version': '1.0', 'id': 'bad-native-region-policy', 'settings': settings}), '--format', 'json')
    assert result.returncode == 1
    assert any(word in result.stderr + result.stdout for word in ('region', 'diagnostic'))


@pytest.mark.parametrize('paired', [False, True])
def test_campaign_collects_current_baseline_packages_before_passing_region_map(tmp_path, monkeypatch, paired):
    from scripts import bfs_native_campaign as client
    proposal = {'id': 'proposal', 'implementation': 'dx100-bfs-scalar', 'payload': {'kind': 'patch'}}
    proposal_path = tmp_path / 'proposal.json'; proposal_path.write_text(json.dumps(proposal))
    source = tmp_path / 'source'; source.mkdir(); (source / 'bfs.cc').write_text('// fixture source\n')
    frozen = {'id': 'frozen', 'identity_sha256': 'a' * 64,
              'settings': {'region_pairs': [{'evidence': 'native_diagnostic_profile.v1', 'diagnostic_repetitions': 2}],
                           'sampling': {'collection': {'method': 'native_paired.v1', 'order_seed': 20260926}} if paired else {}}}
    rows = {family: {'candidate': {'id': 'baseline-source'}, 'workload': {'id': family},
                    'package': {'id': 'old-' + family + '.package', 'region_profile': 'old-' + family + '.profile'}}
            for family in ('kronecker', 'uniform_random')}
    packages = [{'id': name, 'implementation': 'dx100-bfs-scalar'} for name in ('old-k.package', 'old-u.package')]
    catalog = {item['id']: item for item in [frozen, *packages]}
    driver = client.Driver.__new__(client.Driver)
    driver.args = SimpleNamespace(id='campaign', protocol='frozen', packages=[item['id'] for item in packages],
        proposal=proposal_path, records=tmp_path / 'records', lane='mbit10-evaluation-node1',
        provider_config=None, repair_config=None, source_runs_dir=tmp_path / 'sources')
    driver.receipt = {'families': {}, 'candidate_rounds': [], 'repair_attempts': []}
    driver.save = lambda: None
    driver.call = lambda command, ident, *args, **kwargs: catalog.get(ident, {})
    monkeypatch.setattr(client.bfs_protocol, '_validate_settings', lambda *args: None)
    monkeypatch.setattr(client, 'validate_inputs', lambda *args: rows)
    monkeypatch.setattr(client.artifacts, 'source_root', lambda *args: source)
    monkeypatch.setattr(client.subprocess, 'check_output', lambda *args, **kwargs: 'fixture\n')
    comparisons, collected, pairs = [], {}, []

    def request(command, value, *args, **kwargs):
        if command == 'submit': return {'outcome': {'state': 'candidate_created'}, 'candidate': 'selected-candidate'}
        assert command == 'compare-evaluations'
        comparisons.append(value)
        return {'id': value['id'], 'decision': {'state': 'fixture_comparison'}}

    def collect(prefix, evaluation, previous, repetitions):
        assert previous.startswith('old-') and repetitions == 2
        if paired:
            assert any(evaluation['id'] in members for members in pairs)
        package = {'id': prefix + '.package', 'completeness': 'fixture'}
        collected[evaluation['id']] = package['id']
        return package

    driver.request = request
    driver.collect = collect
    driver.evaluate = lambda name, *args: {'id': name, 'outcome': {'state': 'complete'}, 'correctness': {'state': 'passed'}}
    def evaluate_pair(prefix, *args):
        baseline = driver.evaluate(prefix + '.baseline.evaluation')
        candidate = driver.evaluate(prefix + '.evaluation')
        pairs.append({baseline['id'], candidate['id']})
        return {'id': prefix + '.pair'}, baseline, candidate
    driver.evaluate_pair = evaluate_pair
    driver.run()
    assert driver.receipt['bounds']['evaluation_seconds'] == (2400 if paired else 1200)
    assert driver.receipt['bounds'].get('pair_seconds') == (2400 if paired else None)
    assert len(collected) == 4 and len(comparisons) == 2
    assert len(pairs) == (2 if paired else 0)
    for request in comparisons:
        assert request['region_packages'] == {request[key]: collected[request[key]]
            for key in ('baseline_evaluation', 'candidate_evaluation')}
        assert all(not value.startswith('old-') for value in request['region_packages'].values())


def test_native_profile_request_preserves_frozen_diagnostic_repetition_count(native_setup):
    from scripts import bfs_native_campaign as client
    _, _, primaries, _, _ = native_setup
    primary = primaries['baseline']; requests = []
    driver = client.Driver.__new__(client.Driver)
    driver.args = SimpleNamespace(runs_dir=Path('/fixture/runs'), lane='fixture-lane')
    driver.call = lambda *args, **kwargs: None
    def request(command, value, *args, **kwargs):
        requests.append((command, value))
        return {'id': value['id']}
    driver.request = request
    driver.collect('fresh', primary, 'old.profile', repetitions=2)
    assert requests[0][0] == 'bfs-profile' and requests[0][1]['repetitions'] == 2
    assert requests[0][1]['evaluation'] == primary['id']
    assert requests[1][1]['region_profile'] == 'fresh.profile'


def test_native_per_invocation_and_inclusive_scopes_use_each_raw_trial(native_setup):
    from swdb.bfs_region_comparison import _native_samples
    from swdb.store import Store
    records, request, primaries, _, protocol = native_setup
    pair = copy.deepcopy(protocol['settings']['region_pairs'][0])
    pair.update(scope='per_invocation', attribution='inclusive')
    samples = _native_samples(Store(records.path), primaries['baseline'],
                              request['region_packages'][primaries['baseline']['id']], pair, 'baseline')
    assert len(samples) == 2
    assert all(row['invocations'] == 2 and row['duration_s'] == pytest.approx(0.03) for row in samples)
