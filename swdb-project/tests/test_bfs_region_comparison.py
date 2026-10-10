"""Public diagnostic comparison contracts; synthetic evidence only. Date 2026-09-26; updated 2026-09-29."""
import copy
import datetime
import hashlib
import json
import shutil
from pathlib import Path

import pytest
from conftest import make_records
from test_bfs_aggregation import simulation_seed, _aggregate  # noqa: F401 (fixture)
from testkit.bfs_protocol import _payload, _command
from swdb import artifacts, profile_package, workflow
from swdb.dx100_witness import graph_verification_contract


def ref(path):
    return {"path": str(path), "sha256": artifacts.file_hash(path)}


def test_streamed_region_digest_identifies_exact_parsed_bytes(tmp_path):
    from swdb.dx100_diagnostic import counters
    path = tmp_path / 'diagnostic.log'
    raw = b'raw trace byte \xff\nSWDB_DX100_ROI_SEALED\nSWDB_DX100_REGIONS ' + json.dumps(dict(
        format='swdb.dx100.regions.v1', clock='m5_rpns', errors=0,
        regions=[dict(index=0, inclusive_ns=10, exclusive_ns=5, invocations=1)])).encode() + b'\n'
    path.write_bytes(raw)
    rows, digest = counters(path, 1, return_sha256=True)
    assert rows[0]['exclusive_ns'] == 5 and digest == hashlib.sha256(raw).hexdigest()


def package_fixture(records, tmp, primary, collector, runtime, now, ns, zero_function=False):
    # zero_function (2026-09-29): the fixture-function region records zero invocations and time,
    # as the real T17 scalar baseline's never-called TDStepMAA function does.
    rid = primary['id']; candidate = records.read(f"candidates/{primary['candidate']}.yaml")
    raw = (Path(candidate['artifact']['path']) / 'src/bfs.cc').read_bytes()
    regions = []
    # A zero-function fixture keeps a second, timed function so the package stays complete.
    for name, bounds in (('function', [0, 128]), ('loop', [32, 96])) + ((('function2', [0, 64]),) if zero_function else ()):
        kind = name.rstrip('2'); fragment = raw[bounds[0]:bounds[1]]
        regions.append(dict(id='fixture-' + name, kind=kind, path='src/bfs.cc', lines=[1, 5], byte_range=bounds,
            text=fragment.decode(), source_sha256=hashlib.sha256(fragment).hexdigest(),
            source_artifact_sha256=candidate['artifact']['sha256'], function='explicit_fixture'))
    instrumented = tmp / (rid + '.cc'); instrumented.write_bytes(raw)
    binary = tmp / (rid + '.binary'); binary.write_text('explicit diagnostic fixture ' + rid)
    wrapper = tmp / (rid + '.driver.cc'); wrapper.write_text('// Explicit nonexecuted diagnostic oracle wrapper fixture\n')
    contract = graph_verification_contract('gapbs')
    oracle = {**ref(wrapper), 'symbol': 'swdb_original::Graph::verify'}
    discovery = {key: value for key, value in collector.items() if key != 'runtime_sha256'}
    discovery.update(scope='explicit fixture source extents', limitations=['contract fixture, no compiler execution'])
    quantity = 'per-thread simulated elapsed intervals summed across threads; includes waiting and overlap'
    definition = dict(runtime=ref(runtime), instrumented_source=ref(instrumented), regions=copy.deepcopy(regions),
                      discovery=discovery, quantity=quantity, difference='explicit fixture instrumentation')
    compiled = workflow.record('evaluation', rid + '.compile', request={'fixture': True}, candidate=candidate['id'],
        context={'candidate_sha256': candidate['artifact']['sha256'], 'diagnostic': definition,
                 'application': 'gapbs', 'roi': primary['context']['roi'], 'graph_verification': contract,
                 'driver': ref(wrapper), 'verifier_source': oracle},
        build={'binary': str(binary), 'binary_sha256': ref(binary)['sha256'],
               'adapter': 'dx100.complete_call.v2', 'driver': ref(wrapper)},
        outcome={'state': 'complete', 'stage': 'candidate_build', 'reason': 'fixture'}, stages=[], timing=[],
        correctness={'state': 'unverified', 'checks': []}, profiling={}, raw_artifacts=[], gain_claim=False, evidence_kind='contract_fixture')
    records.write(f"evaluations/{compiled['id']}.yaml", compiled)
    log = tmp / (rid + '.log')
    log.write_text('SWDB_DX100_ROI_SEALED\nSWDB_DX100_REGIONS ' + json.dumps(dict(format='swdb.dx100.regions.v1',
        clock='m5_rpns', errors=0, regions=[dict(index=i, inclusive_ns=0 if zero_function and not i else ns*2,
                      exclusive_ns=0 if zero_function and not i else ns, invocations=0 if zero_function and not i else 2)
                      for i in range(len(regions))])) + '\n')
    diagnostic = copy.deepcopy(primary); diagnostic['id'] = rid + '.diagnostic'
    # Diagnostics have their own binary and no primary frozen-role binding,
    # but retain explicit actual coordinates in the full workload source list.
    for key in ('protocol', 'protocol_role'):
        diagnostic['request'].pop(key, None)
    for key in ('protocol', 'protocol_binding', 'adapter'):
        diagnostic['context'].pop(key, None)
    diagnostic['context']['workload']['sources'] = [0, 4]
    diagnostic['context'].update(candidate_build=compiled['id'], candidate_driver=ref(wrapper), verifier_source=oracle,
        instrumentation={'treatment': 'source_scope_diagnostic', 'graph_verification': contract,
                         'candidate_driver': ref(wrapper)})
    diagnostic['build'].update(binary=str(binary), binary_sha256=ref(binary)['sha256'], driver=ref(wrapper))
    diagnostic['stages'] = [dict(stage='simulation', state='complete', started=now, log=str(log), log_sha256=ref(log)['sha256'])]
    for check in diagnostic['correctness']['checks']:
        check.update(binary_sha256=ref(binary)['sha256'], output_sha256=ref(log)['sha256'])
    for timing in diagnostic['timing']:
        timing.update(binary_sha256=ref(binary)['sha256'], output_sha256=ref(log)['sha256'])
    records.write(f"evaluations/{diagnostic['id']}.yaml", diagnostic)
    cell = {key: primary['timing'][0][key] for key in ('source', 'source_position', 'repetition')}
    run = dict(kind='regions', **cell, evaluation=diagnostic['id'], binary_sha256=ref(binary)['sha256'], output=str(log),
        output_sha256=ref(log)['sha256'], region_output=str(log), region_output_sha256=ref(log)['sha256'],
        evidence_kind='contract_fixture', correctness=copy.deepcopy(diagnostic['correctness']))
    for row in regions:
        zero = zero_function and row['id'] == 'fixture-function'
        # A never-entered region carries only its zero count, as the real collector records it.
        row.update(metrics=dict(invocations=0) if zero else dict(inclusive_simulated_seconds=ns*2/1e9,
                                exclusive_simulated_seconds=ns/1e9, invocations=2),
            basis='simulated', scope='accumulated simulated elapsed per executing thread within ' + primary['context']['roi'],
            artifact_sha256=ref(binary)['sha256'], attribution=dict(inclusive=True,
            exclusive='nested guarded intervals subtracted on the same thread', whole_lexical_region=True,
            clock='m5_rpns', quantity=quantity, limitations=definition['difference']))
    memory = dict(metric='data_reads', available=True, value=10, unit='accesses', definition='fixture counter', basis='simulated',
        scope='ROI', collector='fixture', artifact_sha256=primary['build']['binary_sha256'],
        source_artifact_sha256=candidate['artifact']['sha256'], execution=cell, raw_artifact=str(log), raw_sha256=ref(log)['sha256'])
    profile = workflow.record('region_profile', rid + '.profile', request={'fixture': True}, evaluation=rid,
        candidate=candidate['id'], source_snapshot=candidate['source_snapshot'], implementation=candidate['implementation'],
        machine=primary['machine'], context={**primary['context'], 'primary_binary_sha256': primary['build']['binary_sha256']},
        discovery=discovery, regions=regions, dynamic_memory=[memory], executions=[run, {**run, 'kind': 'memory',
            'binary_sha256': primary['build']['binary_sha256'], 'raw_artifact': str(log), 'raw_sha256': ref(log)['sha256']}],
        outcome={'state': 'complete', 'stage': 'collection', 'reason': 'explicit fixture'}, reasons=[], stages=[], raw_artifacts=[], gain_claim=False)
    primary['profiling'] = {'region_profile': profile['id']}
    records.write(f'evaluations/{rid}.yaml', primary)
    records.write(f"region_profiles/{profile['id']}.yaml", profile)
    package = _command(records, 'profile-package', _payload(tmp, rid + '.package-request', dict(message_version='1.0',
        id=rid + '.package', evaluation=rid, region_profile=profile['id'], implementation=primary['implementation'],
        context=profile_package._context(primary))))
    assert package['completeness'] == 'fixture', package['reasons']
    return package['id']


def _region_seed(simulation_seed, tmp_path_factory, zero_role=None):
    source, old, original = simulation_seed
    tmp = tmp_path_factory.mktemp('regional-contract'); records = make_records(tmp)
    shutil.copytree(source.path, records.path, dirs_exist_ok=True)
    runtime = tmp / 'runtime.hpp'; runtime.write_text('// Explicit diagnostic runtime fixture\n')
    wrapper = tmp / 'primary-driver.cc'; wrapper.write_text('// Explicit nonexecuted primary oracle wrapper fixture\n')
    contract = graph_verification_contract('gapbs')
    settings = copy.deepcopy(old['settings'])
    settings['correctness']['verifier'] = 'dx100.bfs.verifier.v1'
    for role in ('baseline', 'candidate'):
        settings['builds'][role]['adapter'] = 'dx100.complete_call.v2'
        settings['instrumentation'][role] = {'treatment': 'explicit_fixture_primary_wrapper',
                                           'graph_verification': contract, 'candidate_driver': ref(wrapper)}
    collector = dict(backend='libclang-cindex', collector='dx100.m5_rpns.source_scopes.v1', library_sha256='a'*64,
                     pass_sha256='b'*64, runtime_sha256=ref(runtime)['sha256'])
    paired = 'fixture-function' if zero_role else 'fixture-loop'
    settings['region_pairs'] = [dict(semantic_region='fixture traversal', baseline=paired, candidate=paired,
        scope='accumulated', attribution='exclusive', evidence='simulated_diagnostic_profile', collector=collector)]
    frozen = _command(records, 'freeze-protocol', _payload(tmp, 'region-policy', dict(message_version='1.0', id='region-policy', settings=settings)))
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(); components = {}; packages = {}
    for role, originals in original.items():
        components[role] = []
        for initial in originals:
            primary = copy.deepcopy(initial); primary['id'] = 'regional-' + initial['id']
            primary['build'].update(adapter='dx100.complete_call.v2', driver=ref(wrapper))
            primary['context'].update(application='gapbs', adapter='dx100.complete_call.v2',
                verifier=settings['correctness']['verifier'], graph_verification=contract,
                candidate_driver=ref(wrapper), verifier_source={**ref(wrapper), 'symbol': 'swdb_original::Graph::verify'},
                instrumentation=copy.deepcopy(settings['instrumentation'][role]))
            for check in primary['correctness']['checks']:
                check.update(checker=settings['correctness']['verifier'], verifier=settings['correctness']['verifier'])
            primary['request']['protocol'] = frozen['id']; primary['context']['protocol'] = frozen['id']
            primary['context']['protocol_binding'].update(protocol=frozen['id'], frozen_sha256=frozen['identity_sha256'],
                settings_sha256=artifacts.digest(settings), frozen_at=frozen['frozen_at'], bound_at=now)
            primary['context']['source'] = primary['context']['sources'][0]; primary['stages'][0]['started'] = now
            packages[primary['id']] = package_fixture(records, tmp, primary, collector, runtime, now,
                200000000 if role == 'baseline' else 100000000, zero_function=role == zero_role)
            components[role].append(primary)
    aggregate = {role: _aggregate(records, tmp, frozen, role, rows, name='regional-aggregate-' + role) for role, rows in components.items()}
    request = dict(message_version='1.0', id='regional-comparison', protocol=frozen['id'], comparison_baseline='gapbs-bfs-do',
        baseline_evaluation=aggregate['baseline']['id'], candidate_evaluation=aggregate['candidate']['id'], region_packages=packages)
    return records, request, components


@pytest.fixture(scope='module')
def region_seed(simulation_seed, tmp_path_factory):
    return _region_seed(simulation_seed, tmp_path_factory)


@pytest.fixture(scope='module', params=['baseline', 'candidate'])
def zero_seed(simulation_seed, tmp_path_factory, request):
    return request.param, _region_seed(simulation_seed, tmp_path_factory, zero_role=request.param)


@pytest.fixture
def regional_setup(records, region_seed):
    original, request, components = region_seed
    shutil.copytree(original.path, records.path, dirs_exist_ok=True)
    return records, copy.deepcopy(request), copy.deepcopy(components)


def test_public_regional_comparison_retains_diagnostic_cells_and_separate_quantities(regional_setup, tmp_path):
    records, request, _ = regional_setup
    result = _command(records, 'compare-evaluations', _payload(tmp_path, 'compare', request))
    assert result['decision']['state'] == 'fixture_comparison' and not result['gain_claim']
    region = result['region_comparisons'][0]
    assert region['duration_ratio'] == 2 and not region['primary_bfs_roi'] and not region['gain_claim']
    assert all(len(rows) == 4 for rows in region['samples'].values())
    assert all(row['primary_binary_sha256'] != row['diagnostic_binary_sha256'] for rows in region['samples'].values() for row in rows)
    fresh = records.swdb('get', result['id'], '--chain', '--format', 'json')
    assert fresh.returncode == 0, fresh.stderr
    chain = json.loads(fresh.stdout)['records']
    assert chain[result['id']]['region_comparisons'] == result['region_comparisons']
    assert set(request['region_packages'].values()) <= set(chain)
    assert 'explicit-model-fixture' in chain


@pytest.mark.parametrize('fault', ['missing-package', 'wrong-package', 'failed-check', 'stale-profile', 'collector', 'cell', 'raw-values',
                                 'actual-timing', 'actual-context', 'actual-check'])
def test_public_regional_comparison_rejects_incompatible_evidence(regional_setup, tmp_path, fault):
    records, request, components = regional_setup; primary = components['candidate'][-1]
    if fault == 'missing-package': request['region_packages'].pop(primary['id'])
    elif fault == 'wrong-package': request['region_packages'][primary['id']] = next(iter(request['region_packages'].values()))
    else:
        profile = records.read(f"region_profiles/{primary['profiling']['region_profile']}.yaml")
        diagnostic = records.read(f"evaluations/{profile['executions'][0]['evaluation']}.yaml")
        if fault == 'failed-check':
            diagnostic['correctness']['state'] = 'failed'; records.write(f"evaluations/{diagnostic['id']}.yaml", diagnostic)
        else:
            if fault.startswith('actual-'):
                if fault == 'actual-timing': diagnostic['timing'][0].update(source_position=0, repetition=0)
                elif fault == 'actual-context': diagnostic['context']['protocol_trial'].update(source_position=0, repetition=0)
                else:
                    diagnostic['correctness']['checks'][0].update(source_position=0, repetition=0)
                    profile['executions'][0]['correctness'] = copy.deepcopy(diagnostic['correctness'])
                records.write(f"evaluations/{diagnostic['id']}.yaml", diagnostic)
            elif fault == 'collector': profile['discovery']['pass_sha256'] = 'f'*64
            elif fault == 'cell': profile['executions'][0]['repetition'] = 99
            else: profile['regions'][1]['metrics']['exclusive_simulated_seconds'] *= 2
            records.write(f"region_profiles/{profile['id']}.yaml", profile)
            if fault != 'stale-profile':
                package = _command(records, 'profile-package', _payload(tmp_path, 'reassemble', dict(message_version='1.0',
                    id=primary['id'] + '.package', version=2, evaluation=primary['id'], region_profile=profile['id'],
                    implementation=primary['implementation'], context=profile_package._context(primary))))
                if fault == 'cell':
                    assert package['completeness'] == 'incomplete'
                    assert 'requested source sequence or frozen repetition' in str(package['reasons'])
                request['region_packages'][primary['id']] = package['id']
    result = _command(records, 'compare-evaluations', _payload(tmp_path, 'bad-compare', request), succeeds=False)
    assert not result['gain_claim'] and result['decision']['state'] == 'rejected'
    expected_reason = {
        'missing-package': 'cover exactly', 'wrong-package': 'another primary',
        'failed-check': 'independent correctness', 'stale-profile': 'evidence changed',
        'collector': 'collector differs', 'cell': 'package is incomplete', 'raw-values': 'raw report',
        'actual-timing': 'trial identity differs from its recorded timing',
        'actual-context': 'trial identity differs from its recorded timing',
        'actual-check': 'correctness is not bound',
    }[fault]
    assert expected_reason in str(result['decision']['reasons'])


def test_zero_invocation_region_is_baseline_not_invoked_only_for_the_baseline(records, zero_seed, tmp_path):
    """2026-09-29: a baseline that never executes the paired region is reported, not rejected;
    a zero-invocation candidate region is still rejected."""
    zero_role, (original, request, _) = zero_seed
    shutil.copytree(original.path, records.path, dirs_exist_ok=True)
    request = copy.deepcopy(request)
    if zero_role == 'candidate':
        result = _command(records, 'compare-evaluations', _payload(tmp_path, 'zero-candidate', request), succeeds=False)
        assert result['decision']['state'] == 'rejected' and not result['gain_claim']
        assert 'invocation count must be an integer >= 1' in str(result['decision']['reasons'])
        return
    result = _command(records, 'compare-evaluations', _payload(tmp_path, 'zero-baseline', request))
    assert result['decision']['state'] == 'fixture_comparison' and not result['gain_claim']
    (region,) = result['region_comparisons']
    assert region['state'] == 'baseline_not_invoked' and region['duration_ratio'] is None
    assert region['baseline_invocations'] == 0 and set(region['candidate_invocations']) == {2}
    assert not region['gain_claim'] and not region['primary_bfs_roi']
    assert all(value == 100000000 / 1e9 for value in region['candidate_duration_s'].values())
    assert all(row['duration_s'] is None and row['invocations'] == 0 for row in region['samples']['baseline'])
    fresh = records.swdb('get', result['id'], '--chain', '--format', 'json')
    assert fresh.returncode == 0, fresh.stderr
    assert json.loads(fresh.stdout)['records'][result['id']]['region_comparisons'] == result['region_comparisons']


def test_baseline_zero_invocations_with_nonzero_time_is_rejected(records, zero_seed, tmp_path):
    zero_role, (original, request, components) = zero_seed
    if zero_role != 'baseline':
        pytest.skip('baseline-only fault')
    shutil.copytree(original.path, records.path, dirs_exist_ok=True)
    request = copy.deepcopy(request); primary = components['baseline'][-1]
    profile = records.read(f"region_profiles/{primary['profiling']['region_profile']}.yaml")
    profile['regions'][0]['metrics']['inclusive_simulated_seconds'] = 0.5
    records.write(f"region_profiles/{profile['id']}.yaml", profile)
    package = _command(records, 'profile-package', _payload(tmp_path, 'reassemble', dict(message_version='1.0',
        id=primary['id'] + '.package', version=2, evaluation=primary['id'], region_profile=profile['id'],
        implementation=primary['implementation'], context=profile_package._context(primary))))
    request['region_packages'][primary['id']] = package['id']
    result = _command(records, 'compare-evaluations', _payload(tmp_path, 'zero-time', request), succeeds=False)
    assert result['decision']['state'] == 'rejected'
    assert 'must record zero inclusive and exclusive seconds' in str(result['decision']['reasons'])
