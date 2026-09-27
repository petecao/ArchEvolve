"""Prospective coordinator contracts; fixtures are not BFS evidence. Updated 2026-09-27 ET."""
import copy
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from conftest import REPO
from test_profile_packages import package_seed, package_setup, _assemble
from swdb.store import Store
from scripts import bfs_simulator_batch as batch
from scripts import bfs_dx100_coverage_a2 as coverage_a2
from swdb import artifacts


def plan(kind='t15'):
    return json.loads((batch.PLAN_DIR / f'bfs-{kind}-simulator-batch-20260926-a1.json').read_text())


def admission(policy, *, started=None, charges=None):
    started = started or datetime(2026, 9, 27, 9, tzinfo=batch.ET)
    charges = charges or []
    available = policy['bounds']['batch_seconds'] - sum(row['elapsed_seconds'] for row in charges)
    return {'format': 'swdb.bfs.simulator-batch-admission.v1', 'plan_sha256': artifacts.digest(policy),
            'prepared_at': (started - timedelta(minutes=5)).isoformat(),
            'clock': {'not_before': started.isoformat(), 'latest_start': (started + timedelta(minutes=5)).isoformat(),
                      'absolute_end': (started + timedelta(minutes=5, seconds=available)).isoformat()},
            'preparation_charges': charges, 'runtime_sha256': {'explicit': 'synthetic fixture'},
            'python': {'path': sys.executable, 'sha256': 'not_an_empirical_pin'},
            'protocols': {key: {'id': key + '.fixture', 'sha256': 'fixture'} for key in policy['protocol_requests']}}


@pytest.fixture
def clock(monkeypatch):
    clock = SimpleNamespace(mono=100.0, wall=datetime(2026, 9, 27, 9, tzinfo=batch.ET))
    monkeypatch.setattr(batch.time, 'monotonic', lambda: clock.mono)
    monkeypatch.setattr(batch, 'now', lambda: clock.wall)
    return clock


@pytest.mark.parametrize('kind', ['t15', 't16'])
def test_reviewed_plans_are_exact_and_do_not_reuse_expired_attempts(kind):
    value = plan(kind)
    batch.validate_plan(value, kind)
    assert value['required_a3'].endswith('-a3') and value['automatic_retry_allowed'] is False
    assert value['profitability'] == {'minimum_speedup': 1.05, 'maximum_relative_spread': .1,
        'confidence': .95, 'bootstrap_resamples': 2000, 'bootstrap_seed': 20260925}
    value['series'][0]['sources'].reverse()
    if kind == 't16': value['series'][0]['sources'][0] = 0
    with pytest.raises(ValueError, match='fixed scope'):
        batch.validate_plan(value, kind)


@pytest.mark.parametrize('kind', ['t15', 't16'])
def test_public_commands_bind_exact_grid_with_no_circular_t15_freeze(kind, tmp_path):
    value = plan(kind); approval = admission(value)
    for row in value['series']:
        command = batch.series_command(value, row, approval, tmp_path/'config', tmp_path/'raw', tmp_path/'records', 1, 21600, 39)
        assert '--require-capacity' in command and '--author-binary' in command
        assert command[command.index('--verifier') + 1] == 'dx100.bfs.verifier.v2'
        assert ('--accelerated' in command) is row['accelerated']
        assert command[command.index('--diagnostic-build') + 1] == row['diagnostic_build']
        if kind == 't15': assert '--protocol' not in command and '--protocol-role' not in command
        else:
            assert command[command.index('--protocol') + 1] == row['protocol_key'] + '.fixture'
            assert command[command.index('--protocol-role') + 1] == row['protocol_role']


def test_next_series_cannot_reset_elapsed_or_retained_storage(clock):
    value = plan(); ledger = batch.Ledger(value, admission(value), clock.mono, clock.wall)
    assert ledger.next_allowance(batch.GIB) == (21600, 39)
    clock.mono += 21000
    assert ledger.next_allowance(9*batch.GIB) == (21600, 31)
    clock.mono += 601
    with pytest.raises(ValueError, match='next full series'):
        ledger.next_allowance(9*batch.GIB)
    assert ledger.observation(9*batch.GIB)['charged_elapsed_seconds'] == 21601


def test_absolute_wall_deadline_is_independent_of_monotonic_cap(clock):
    value = plan(); ledger = batch.Ledger(value, admission(value), clock.mono, clock.wall)
    clock.wall = ledger.end - timedelta(seconds=20)
    with pytest.raises(ValueError, match='deadline exhausted'): ledger.remaining()


@pytest.mark.parametrize('fault', ['late', 'unaware', 'future_preparation', 'extended_window', 'missing_charge'])
def test_clock_or_preparation_omissions_fail_closed(clock, monkeypatch, fault):
    value = plan('t16'); charges = [{'id': 'fixed-preparation', 'elapsed_seconds': 500, 'raw_bytes': 2*batch.GIB}]
    monkeypatch.setattr(batch, 'preparation_charges', lambda _: charges)
    approval = admission(value, charges=charges)
    if fault == 'late': clock.wall += timedelta(minutes=6)
    elif fault == 'unaware': approval['clock']['absolute_end'] = '2026-09-28T09:00:00'
    elif fault == 'future_preparation': approval['prepared_at'] = (clock.wall + timedelta(minutes=1)).isoformat()
    elif fault == 'extended_window': approval['clock']['absolute_end'] = (clock.wall + timedelta(days=2)).isoformat()
    else: approval['preparation_charges'] = []
    with pytest.raises(ValueError): batch.Ledger(value, approval, clock.mono, clock.wall)


def test_retained_preparation_cost_is_derived_and_cannot_be_omitted(clock, monkeypatch):
    value = plan('t16'); charges = [{'id': 'fixed-preparation', 'elapsed_seconds': 500, 'raw_bytes': 2*batch.GIB}]
    monkeypatch.setattr(batch, 'preparation_charges', lambda _: charges)
    ledger = batch.Ledger(value, admission(value, charges=charges), clock.mono, clock.wall)
    assert ledger.next_allowance(batch.GIB) == (21600, 57)
    clock.mono += 7
    assert ledger.observation(batch.GIB)['charged_elapsed_seconds'] == 507


def ref(path, value):
    path.write_text(json.dumps(value))
    return {'path': str(path), 'sha256': artifacts.file_hash(path)}


def test_preparation_reopens_pinned_receipts_and_charges_whole_directories(tmp_path):
    data = tmp_path/'retained'; data.mkdir(); (data/'failed.log').write_bytes(b'x'*9000)
    driver = ref(tmp_path/'driver.json', {'id': 'prep', 'state': 'complete', 'stages': [{'host_wall_s': 4.25}]})
    lane = ref(tmp_path/'lane.json', {'socket_lane': {'exit_code': 0, 'started_utc': '2026-09-26T10:00:00Z',
                                                   'ended_utc': '2026-09-26T10:00:05Z'}})
    policy = {'accounting': {'preparation': [{'id': 'prep', 'driver': driver, 'lane': lane, 'storage_paths': [str(data)]}]}}
    observed = batch.preparation_charges(policy)
    assert observed == [{'id': 'prep', 'elapsed_seconds': 6, 'raw_bytes': batch.allocated_bytes([data])}]
    assert observed[0]['raw_bytes'] >= 9000
    (tmp_path/'driver.json').write_text('{}')
    with pytest.raises(ValueError, match='changed'): batch.preparation_charges(policy)


def fixture_package(policy, row, source):
    # Minimal synthetic readback, never stored or advertised as execution evidence.
    return {'completeness':'complete','evidence':{'classification':'execution'},
            'context':{'workload':{'id':row['workload']},'sources':[source], 'roi':policy['roi'],
                       'target':policy['target'],'threads':policy['threads'],
                       'target_configuration':copy.deepcopy(row['configuration'])}}


def complete_child(policy, row, approval, storage):
    value = {'id': row['id'], 'state': 'complete', 'candidate': row['candidate'], 'workload': row['workload'],
             'model_build': policy['model_build'], 'configuration': row['configuration'], 'roi': policy['roi'],
             'repetitions': 2, 'protocol': approval['protocols'][row['protocol_key']]['id'] if row['protocol_key'] else None,
             'diagnostic_build': {'evaluation': row['diagnostic_build'], 'sha256': policy['record_sha256'][row['diagnostic_build']]},
             'bounds': {key: policy['bounds'][key] for key in ('checkpoint_seconds','run_seconds','diagnostic_seconds','memory_gib','storage_gib')},
             'stages': [{'state': 'complete'}], 'samples': []}
    value['owned_supervision'] = {'format':'swdb.bfs.simulator-supervision.v1',
        'sampled_tree_rss_bytes':batch.lifecycle.SAMPLED_RSS_BYTES,'maximum_gap_seconds':30,
        'rss_source':batch.lifecycle.RSS_SOURCE,'hard_memory_quota':False,
        'maximum_observed_gap_seconds':5,'maximum_guard_seconds':.01}
    value['owned_cleanup']={'state':'all_owned_descendants_absent'}
    for stage in value['stages']:stage['cleanup']={'state':'all_owned_descendants_absent'}
    value['bounds'].update(total_seconds=21600, batch_storage_gib=storage, verification_ticks=policy['verification_ticks'])
    for position, source in enumerate(row['sources']):
        for repetition in range(2):
            prefix = f"{row['id']}.s{position}.r{repetition}"
            value['samples'].append({'source_position': position, 'source': source, 'repetition': repetition,
                'evaluation': prefix+'.primary.evaluation', 'diagnostic_evaluation': prefix+'.diagnostic.evaluation',
                'profile': prefix+'.profile', 'package': prefix+'.package.v1.'+'a'*16, 'completeness': 'complete'})
    return value


@pytest.mark.parametrize('fault', ['state','candidate','protocol','bounds','grid','package','stage','diagnostic','source_context','target_context','owned_contract','owned_cleanup'])
def test_completed_receipt_cannot_hide_wrong_identity_or_partial_grid(fault, monkeypatch):
    def bound(store, package, requested, *args):
        batch.require(package == requested+'.v1.'+'a'*16, 'changed fixture package identity')
        position=int(requested[len(row['id'])+2:].split('.')[0])
        result = fixture_package(value, row, row['sources'][position])
        if fault == 'source_context': result['context']['sources'] = [999]
        if fault == 'target_context': result['context']['target_configuration']['l3_size_mb'] = 99
        return result
    monkeypatch.setattr(batch, 'package_binding', bound)
    value = plan('t15'); row = value['series'][0]; approval = admission(value)
    child = complete_child(value, row, approval, 59)
    if fault not in ('source_context','target_context'):
        batch.validate_series_result(value, row, approval, child, 21600, 59, None)
    if fault in ('state','candidate','protocol'): child[fault] = 'wrong'
    elif fault == 'bounds': child['bounds']['run_seconds'] += 1
    elif fault == 'grid': child['samples'][1] = copy.deepcopy(child['samples'][0])
    elif fault == 'package': child['samples'][0]['package'] = 'another.package'
    elif fault == 'stage': child['stages'][0]['state'] = 'failed'
    elif fault == 'diagnostic': child['diagnostic_build']['sha256'] = '0'*64
    elif fault == 'owned_contract': child.pop('owned_supervision')
    elif fault == 'owned_cleanup': child['owned_cleanup']['state']='leader_only_exited'
    with pytest.raises(ValueError): batch.validate_series_result(value, row, approval, child, 21600, 59, None)


@pytest.mark.parametrize('failure', [None, 'child', 'incomplete', 'cleanup'])
def test_sequential_collection_stops_on_failure_and_keeps_first_logs(tmp_path, monkeypatch, clock, failure):
    policy = plan(); approval = admission(policy); ledger = batch.Ledger(policy, approval, clock.mono, clock.wall)
    folder = tmp_path/'driver'; folder.mkdir(); runs = tmp_path/'runs'; runs.mkdir()
    receipt = {'stages': [], 'series': []}; calls = []; cleanup = []
    monkeypatch.setattr(batch, 'runtime_identity', lambda: approval['runtime_sha256'])
    monkeypatch.setattr(batch, 'admit_capacity', lambda *args: None)
    def bound(store, package, requested, *args):
        row = next(row for row in policy['series'] if requested.startswith(row['id']+'.s'))
        position = int(requested[len(row['id'])+2:].split('.')[0])
        return fixture_package(policy, row, row['sources'][position])
    monkeypatch.setattr(batch, 'package_binding', bound)
    monkeypatch.setattr(batch, 'Store', lambda _: None)
    def finish():
        cleanup.append('checked')
        if failure == 'cleanup': raise ValueError('owned descendants remain')
        return {'state': 'all_owned_descendants_absent'}
    def run(receipt, folder, command, **kwargs):
        calls.append(command); row = policy['series'][len(calls)-1]
        # A synthetic elapsed charge occurs inside the child; the next series sees it.
        clock.mono += 20; clock.wall += timedelta(seconds=20)
        out = kwargs['output']; out.write_text('retained failure log')
        try: cleanup_row = finish()
        except ValueError:
            receipt['stages'].append({'cleanup': {'state':'failed'}}); raise
        receipt['stages'].append({'cleanup': cleanup_row})
        assert json.loads((folder/'driver.json').read_text())['series'][-1]['state'] == 'running'
        if failure == 'child': raise RuntimeError('fixture child failed')
        storage = int(command[command.index('--batch-storage-gib')+1])
        child = complete_child(policy, row, approval, storage)
        child['owned_supervision'].update(cleanup_ledger=str(tmp_path/'budget'),cleanup_binding='fixture')
        sample=tmp_path/'resources';sample.write_text('explicit fixture resources')
        child.update(owned_resource_artifact={'path':str(sample),'sha256':artifacts.file_hash(sample)},
                     owned_started='fixture',owned_finished='fixture')
        if failure == 'incomplete': child['samples'].pop()
        destination = runs/row['id']/(row['id']+'.driver'); destination.mkdir(parents=True)
        ref(destination/'driver.json', child); out.write_text(json.dumps(child))
    monkeypatch.setattr(batch.lifecycle, 'run_stage', run)
    monkeypatch.setattr(batch.lifecycle, 'validate_samples', lambda *args: {})
    invoke = lambda: batch.collect_series(policy, approval, receipt, folder, runs, tmp_path/'records', 1,
                                          ledger, SimpleNamespace(finish=finish, budget=SimpleNamespace(path=tmp_path/'budget', binding='fixture')),
                                          lambda: len(calls)*batch.GIB)
    if failure:
        with pytest.raises((ValueError, RuntimeError)): invoke()
        assert len(calls) == len(cleanup) == 1
        assert next(folder.glob('*.stdout.json')).exists()
    else:
        invoke()
        assert len(calls) == len(cleanup) == 2
        assert [c[c.index('--batch-storage-gib')+1] for c in calls] == ['40','39']
        assert all(row['state'] == 'complete' for row in receipt['series'])
        assert ledger.observation(2*batch.GIB)['charged_elapsed_seconds'] == 40


def test_existing_child_path_prevents_dispatch(tmp_path, monkeypatch, clock):
    policy = plan(); approval = admission(policy); ledger = batch.Ledger(policy, approval, clock.mono, clock.wall)
    folder=tmp_path/'driver'; folder.mkdir(); (tmp_path/policy['series'][0]['id']).mkdir()
    monkeypatch.setattr(batch, 'runtime_identity', lambda: approval['runtime_sha256'])
    monkeypatch.setattr(batch, 'admit_capacity', lambda *args: None)
    with pytest.raises(ValueError, match='no resume'):
        batch.collect_series(policy, approval, {'stages': [],'series': []}, folder, tmp_path, tmp_path, 0,
                             ledger, None, lambda: 0)


def test_subreaper_admission_rejects_unsupported_platform(monkeypatch):
    monkeypatch.setattr(batch.sys, 'platform', 'darwin')
    with pytest.raises(ValueError, match='Linux subreaper'): batch.OwnedDescendants()


@pytest.mark.skipif(sys.platform != 'linux', reason='actual Linux prctl/pidfd admission; run under the documented <=90s lane recipe')
@pytest.mark.parametrize('failure', [False, True])
def test_linux_historical_subreaper_compatibility(tmp_path, failure):
    # Isolate prctl from pytest. No model, compiler, graph, provider, or evaluator runs.
    supervisor = r'''
import json, os, pathlib, resource, socket, subprocess, sys, time
resource.setrlimit(resource.RLIMIT_AS, (512*1024**2,512*1024**2))
from scripts.bfs_simulator_batch import OwnedDescendants, CLEANUP_RUNTIME, ROOT, now
from swdb import artifacts
from scripts.bfs_process import run_stage
folder = pathlib.Path(sys.argv[1]); failure = sys.argv[2] == 'True'
before = time.monotonic()
owned = OwnedDescendants(); receipt = {'stages': []}
# Intermediate forks a new-session child, waits for its identity file, then exits.
# The outer coordinator must adopt this child even if its five-second sampling missed it.
inner = "import os,pathlib,time; pathlib.Path(%r).write_text(str(os.getpid())); time.sleep(15)" % str(folder/'grandchild.pid')
leader = "import pathlib,subprocess,sys,time; subprocess.Popen([sys.executable,'-c',%r],start_new_session=True); p=pathlib.Path(%r); end=time.monotonic()+3\nwhile not p.exists() and time.monotonic()<end: time.sleep(.01)\nsys.exit(%d)" % (inner, str(folder/'grandchild.pid'), 3 if failure else 0)
error = None
try:
    run_stage(receipt, folder, [sys.executable,'-c',leader], timeout=5, deadline=time.monotonic()+10, cwd=pathlib.Path.cwd())
except RuntimeError as exc:
    error = str(exc)
finally:
    receipt['cleanup'] = owned.finish()
    receipt['sample'] = owned.sample()
assert bool(error) == failure
pid = int((folder/'grandchild.pid').read_text())
assert not pathlib.Path('/proc',str(pid)).exists()
assert any(row['pid'] == pid for row in receipt['cleanup']['observed'])
receipt.update(format='swdb.bfs.simulator-batch-cleanup-test.v1', state='passed', fixture_only=True,
    host=socket.gethostname().split('.')[0], platform=sys.platform, failure_variant=failure,
    host_wall_s=time.monotonic()-before, finished=now().isoformat(), address_space_bytes=512*1024**2,
    repository_commit=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
    runtime_sha256={name: artifacts.file_hash(ROOT/name) for name in CLEANUP_RUNTIME})
(folder/'linux-cleanup-result.json').write_text(json.dumps(receipt))
'''
    completed = subprocess.run([sys.executable, '-c', supervisor, str(tmp_path), str(failure)], cwd=REPO,
                               capture_output=True, text=True, timeout=20)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    observed = json.loads((tmp_path/'linux-cleanup-result.json').read_text())
    assert observed['cleanup']['state'] == 'all_owned_descendants_absent'
    assert observed['cleanup']['subreaper'] is True
    assert len(observed['sample']['processes']) == 1


@pytest.mark.parametrize('other_held', [False, True])
def test_other_socket_can_be_legally_held_without_disrupting_this_lane(tmp_path, monkeypatch, other_held):
    import fcntl
    monkeypatch.setenv('LACT_LEASE_ROOT', str(tmp_path))
    monkeypatch.setattr(batch.profile, '_verified_lane', lambda *args: 'verified own lane')
    for name in ('mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1'):
        (tmp_path/(name+'.lease')).touch()
        (tmp_path/(name+'.meta.json')).write_text(json.dumps({'state': 'held' if name.endswith('node0') or (name.endswith('node1') and other_held) else 'released'}))
    with (tmp_path/'mbit10-evaluation-node1.lease').open('rb') as lock:
        if other_held: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        observed = batch.lease_observation({}, 0)
        assert observed['leases']['mbit10-evaluation-node1']['kernel_held'] is other_held
    # A stale released label is not authority to overlap a legacy lease.
    with (tmp_path/'mbit10-evaluation.lease').open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ValueError, match='metadata and kernel'): batch.lease_observation({}, 0)


def test_prerequisites_delegate_fixed_actual_case_and_terminal_proofs(monkeypatch):
    value = plan(); approval = admission(value)
    approval.update(proofs={key: {'path': '/fixture/'+key, 'sha256': key} for key in ('a3','coverage','paired','provider')},
                    coverage_commit='actual_pinned_commit')
    observed = []
    monkeypatch.setattr(batch.coverage_case, 'validate_a3', lambda ref, store, current: observed.append(('a3', ref)))
    monkeypatch.setattr(coverage_a2, 'validate_completed',
                        lambda ref, store, current, commit: observed.append(('coverage',ref,commit)), raising=False)
    monkeypatch.setattr(batch.witness_case, 'validate_completion',
                        lambda ref, kind, current: observed.append((kind,ref)))
    batch.validate_prerequisites(value, approval, None)
    assert [row[0] for row in observed] == ['a3','coverage','paired','provider']
    assert observed[1][2] == 'actual_pinned_commit'
    del approval['proofs']['paired']
    with pytest.raises(ValueError, match='terminal audits'): batch.validate_prerequisites(value, approval, None)
    approval['proofs']['paired'] = {}; value['required_coverage'] = 'different-small-graph.execute'
    with pytest.raises(ValueError, match='identities differ'): batch.validate_prerequisites(value, approval, None)


@pytest.mark.parametrize('fault', [None,'mac','duplicate','code','runtime','unverified','duration','skipped','missing_nested','junit_hash'])
def test_actual_linux_cleanup_admission_is_required(tmp_path, fault):
    value = plan(); approval = admission(value)
    paths = (*batch.CLEANUP_RUNTIME, 'swdb/dx100.py', 'tests/test_dx100_interruption.py', 'tests/test_bfs_owned_execution.py')
    approval.update(code_commit='fixture-code', runtime_sha256={name:'a'*64 for name in paths})
    approval['python']['path'] = str(Path(sys.executable).resolve())
    results = []
    for kind in ('owned_cleanup', 'dx100_interruption'):
        names = (['test_linux_owned_stage_reaps_detached_child[False]', 'test_linux_owned_stage_reaps_detached_child[True]',
                  'test_linux_nested_interruption_uses_one_cleanup_budget',
                  'test_linux_term_resistant_nested_cleanup_keeps_final_kill_reserve'] if kind=='owned_cleanup' else
                 ['test_public_interruption_is_durable_before_postmortem[raises]',
                  'test_public_interruption_is_durable_before_postmortem[stalls]'])
        if fault == 'missing_nested' and kind=='owned_cleanup': names.pop()
        junit=tmp_path/(kind+'.xml')
        junit.write_text('<testsuites><testsuite>'+''.join('<testcase name="'+name+'">'+
            ('<skipped/>' if fault=='skipped' else '')+'</testcase>' for name in names)+'</testsuite></testsuites>')
        output=tmp_path/(kind+'.stdout');output.write_text('fixture passed')
        module='tests/test_bfs_owned_execution.py' if kind=='owned_cleanup' else 'tests/test_dx100_interruption.py'
        result = {'format':'swdb.bfs.linux-fixture.v1','kind':kind,'host':'mbit10','platform':'linux',
            'code_commit':'fixture-code','runtime_sha256':copy.deepcopy(approval['runtime_sha256']),
            'evidence_kind':'contract_fixture','state':'passed','returncode':0,
            'started':'2026-09-26T12:59:58-04:00','finished':'2026-09-26T13:00:00-04:00',
            'command':[approval['python']['path'],'-m','pytest',module,'--junitxml='+str(junit)],
            'stdout':{'path':str(output),'sha256':artifacts.file_hash(output)},
            'junit':{'path':str(junit),'sha256':artifacts.file_hash(junit)}}
        if fault == 'mac': result['platform']='darwin'
        elif fault == 'duplicate': result['kind']='owned_cleanup'
        elif fault == 'code': result['code_commit']='another-code'
        elif fault == 'runtime': result['runtime_sha256'][batch.CLEANUP_RUNTIME[0]]='b'*64
        elif fault == 'unverified': result['state']='leader_only_exited'
        elif fault == 'duration': result['started']='2026-09-26T12:55:00-04:00'
        elif fault == 'junit_hash': result['junit']['sha256']='0'*64
        results.append(ref(tmp_path/(kind+'.json'),result))
    approval['linux_cleanup_tests']=results
    if fault:
        with pytest.raises(ValueError): batch.validate_cleanup_tests(approval)
    else: batch.validate_cleanup_tests(approval)


@pytest.mark.parametrize('start', [123,124])
def test_pidfd_cleanup_never_signals_a_reused_pid(monkeypatch, start):
    owned = object.__new__(batch.OwnedDescendants)
    monkeypatch.setattr(batch.os, 'pidfd_open', lambda pid: 41, raising=False)
    closed=[];sent=[]
    monkeypatch.setattr(batch.os,'close',lambda fd:closed.append(fd))
    monkeypatch.setattr(batch.signal,'pidfd_send_signal',lambda fd,sig:sent.append((fd,sig)),raising=False)
    fields=['S','1']+['0']*17+[str(start)]
    monkeypatch.setattr(Path,'read_text',lambda self: '9001 (fixture) '+' '.join(fields))
    owned.kill_identity({'pid':9001,'start_ticks':123})
    assert closed==[41]
    assert bool(sent) is (start==123)


def test_public_content_addressed_package_reopens_exact_fixture_ancestry(package_setup, tmp_path):
    records, request, evaluation, profile, candidate = package_setup
    package = _assemble(records, tmp_path, request)
    assert package['id'] != request['id'] and package['id'].startswith(request['id']+'.v1.')
    observed = batch.package_binding(Store(records.path), package['id'], request['id'],
                                    evaluation['id'], profile['id'], candidate['id'])
    assert observed['id'] == package['id'] and observed['completeness'] == 'fixture'
    # This test proves public shape/binding only; it does not promote fixture evidence.
    assert observed['evidence']['classification'] == 'contract_fixture'
    changed = copy.deepcopy(profile); changed['reasons'].append('changed after package assembly')
    records.write('region_profiles/'+profile['id']+'.yaml', changed)
    with pytest.raises(ValueError, match='retained evidence'):
        batch.package_binding(Store(records.path), package['id'], request['id'],
                              evaluation['id'], profile['id'], candidate['id'])


def test_batch_admission_uses_real_completed_a2_reader_fixture(tmp_path, monkeypatch):
    from test_bfs_dx100_coverage_a2 import completed_fixture
    driver, audit, store, seal, current, proc = completed_fixture(tmp_path, monkeypatch)
    value = plan(); approval = admission(value)
    approval.update(prepared_at=current.isoformat(),
        proofs={key: {'path': '/fixture/'+key, 'sha256': key} for key in ('a3','paired','provider')},
        coverage_commit=driver['repository_commit'])
    approval['proofs']['coverage'] = seal()
    real = coverage_a2.validate_completed
    monkeypatch.setattr(coverage_a2,'validate_completed',lambda ref, store, current, expected:
                        real(ref, store, current, expected, proc))
    monkeypatch.setattr(batch.coverage_case,'validate_a3',lambda *args: {})
    monkeypatch.setattr(batch.witness_case,'validate_completion',lambda *args: {})
    observed = batch.validate_prerequisites(value, approval, store)
    assert observed['coverage']
    value['required_coverage']='bfs-dx100-coverage-20260926-a1.execute'
    with pytest.raises(ValueError, match='identities differ'):
        batch.validate_prerequisites(value, approval, store)


@pytest.mark.parametrize('fault', [None,'slow_hash','last_write_time','last_write_storage'])
def test_final_hash_and_last_persistence_remain_inside_shared_budget(tmp_path, monkeypatch, clock, fault):
    Path(str(tmp_path)+'.dispatch').mkdir()
    policy=plan(); ledger=batch.Ledger(policy,admission(policy),clock.mono,clock.wall)
    log=tmp_path/'ledger.jsonl';log.write_text('{}\n')
    receipt={'state':'complete'}; writes=[]; raw=[1024]
    original_hash=batch.artifacts.file_hash; original_save=batch.save_receipt
    def file_hash(path):
        result=original_hash(path)
        if fault=='slow_hash': clock.mono=ledger.monotonic_end+1
        return result
    def save(folder, value):
        original_save(folder,value); writes.append(value['state'])
        if len(writes)==2:
            if fault=='last_write_time': clock.mono=ledger.monotonic_end+1
            elif fault=='last_write_storage': raw[0]=policy['bounds']['batch_storage_gib']*batch.GIB
    monkeypatch.setattr(batch.artifacts,'file_hash',file_hash)
    monkeypatch.setattr(batch,'save_receipt',save)
    monkeypatch.setattr(batch,'allocated_bytes',lambda _:raw[0])
    if fault:
        with pytest.raises(ValueError,match='common deadline|common allowance'):
            batch.finalize_receipt(receipt,tmp_path,tmp_path,ledger,log)
        assert json.loads((tmp_path/'driver.json').read_text())['state']=='failed'
        assert writes[-1]=='failed'
    else:
        batch.finalize_receipt(receipt,tmp_path,tmp_path,ledger,log)
        saved=json.loads((tmp_path/'driver.json').read_text())
        assert saved['state']=='complete' and saved['final_ledger']['charged_raw_bytes']==1024
        assert saved['ledger_artifact']['sha256']==original_hash(log)


@pytest.mark.parametrize('original_failure', [False, True])
@pytest.mark.parametrize('fault', ['guard', 'cleanup', 'snapshot', 'persistence'])
def test_public_batch_finalization_preserves_original_failure_and_rejects_new_errors(
        tmp_path, monkeypatch, clock, original_failure, fault):
    """Run main's actual finally path; no host workload or measurement is launched."""
    from contextlib import nullcontext
    policy = plan(); approval = admission(policy); approval['code_commit'] = 'fixture'
    runs = tmp_path / policy['id']
    Path(str(runs)+'.dispatch').mkdir()
    failure = RuntimeError('original stage failure')
    final_error = ValueError('injected finalizer ' + fault)
    class Budget:
        create = staticmethod(lambda *args, **kwargs: 'fixture-binding')
        def __init__(self, *args): pass
        def reservation(self): return nullcontext(clock.mono + 5)
        def snapshot(self):
            if fault == 'snapshot': raise final_error
            return {'fixture': True}
    class Owner:
        def __init__(self, budget): self.history = {}; self.budget = budget
        def finish(self, child=None, direct=None):
            if fault == 'cleanup': raise final_error
            return {'state': 'all_owned_descendants_absent', 'errors': []}
    class Guard:
        def __init__(self, callback): self.maximum_gap_seconds = self.maximum_guard_seconds = 0
        def start(self): pass
        def stop(self, deadline):
            if fault == 'guard': raise final_error
    def collect(*args):
        if original_failure: raise failure
    monkeypatch.setattr(sys, 'argv', ['batch', 't15', '--admission', str(tmp_path/'admission'),
        '--admission-sha256', 'fixture', '--runs-dir', str(runs), '--lane', '1',
        '--outer-started', clock.wall.isoformat(),
        '--outer-deadline', (clock.wall+timedelta(seconds=43200)).isoformat(),
        '--pane-pid', '10', '--pane-start-ticks', '100'])
    monkeypatch.setattr(batch, 'RAW_ROOTS', (tmp_path,))
    monkeypatch.setattr(batch, 'read_reference', lambda *args, **kwargs: approval)
    monkeypatch.setattr(batch.socket, 'gethostname', lambda: 'mbit10')
    monkeypatch.setattr(batch, 'Store', lambda *args: SimpleNamespace(by_id={}))
    monkeypatch.setattr(batch, 'validate_cleanup_tests', lambda *args: None)
    monkeypatch.setattr(batch, 'validate_inputs', lambda *args: ({}, {}))
    monkeypatch.setattr(batch, 'collect_series', collect)
    monkeypatch.setattr(batch, 'allocated_bytes', lambda *args: 0)
    monkeypatch.setattr(batch.lifecycle, 'SharedCleanup', Budget)
    monkeypatch.setattr(batch.lifecycle, 'Owned', Owner)
    monkeypatch.setattr(batch.lifecycle, 'Monitor', Guard)
    monkeypatch.setattr(batch.lifecycle, 'identity', lambda pid: {'pid': pid, 'start_ticks': 1})
    monkeypatch.setattr(batch.lifecycle, 'ancestry', lambda *args: [])
    monkeypatch.setattr(batch.lifecycle, 'validate_samples', lambda *args, **kwargs: {})
    real_save = batch.save_receipt
    failed_write = False
    def save(folder, value):
        nonlocal failed_write
        if fault == 'persistence' and value.get('finished') and not failed_write:
            failed_write = True
            raise final_error
        real_save(folder, value)
    monkeypatch.setattr(batch, 'save_receipt', save)
    with pytest.raises(BaseException) as caught:
        batch.main()
    assert caught.value is (failure if original_failure else final_error)
    saved = json.loads((runs/(policy['id']+'.driver')/'driver.json').read_text())
    assert saved['state'] == 'failed'
    if original_failure: assert saved['reason'] == 'RuntimeError: original stage failure'
    assert 'injected finalizer ' + fault in json.dumps(saved)


@pytest.mark.parametrize('original_failure', [False, True])
def test_batch_samples_through_cleanup_and_clips_monitor_stop(tmp_path, monkeypatch, clock, original_failure):
    """Exercise the public finalizer with a live monitor, but no host workload."""
    from contextlib import nullcontext
    import threading
    policy = plan(); approval = admission(policy); approval['code_commit'] = 'fixture'
    runs = tmp_path / policy['id']; failure = RuntimeError('original stage failure')
    Path(str(runs)+'.dispatch').mkdir()
    entered_cleanup = threading.Event(); sampled_cleanup = threading.Event(); observations = []
    real_monitor = batch.lifecycle.Monitor
    class Budget:
        create = staticmethod(lambda *args, **kwargs: 'fixture-binding')
        def __init__(self, *args): pass
        def reservation(self): return nullcontext(clock.mono + .1)
        def snapshot(self): return {'fixture': True}
    class Guard(real_monitor):
        def __init__(self, callback):
            def observe():
                if entered_cleanup.is_set(): sampled_cleanup.set()
            super().__init__(observe)
        def stop(self, deadline):
            observations.append(('stop_deadline', deadline))
            return super().stop(deadline)
    class Owner:
        def __init__(self, budget): self.history = {}; self.budget = budget
        def finish(self, child=None, direct=None):
            entered_cleanup.set()
            observations.append(('interrupt_during_cleanup', guards[0].interrupt))
            observations.append(('sampled_cleanup', sampled_cleanup.wait(.2)))
            return {'state': 'all_owned_descendants_absent', 'errors': []}
    def collect(*args):
        if original_failure: raise failure
    monkeypatch.setattr(sys, 'argv', ['batch', 't15', '--admission', str(tmp_path/'admission'),
        '--admission-sha256', 'fixture', '--runs-dir', str(runs), '--lane', '1',
        '--outer-started', clock.wall.isoformat(),
        '--outer-deadline', (clock.wall+timedelta(seconds=43200)).isoformat(),
        '--pane-pid', '10', '--pane-start-ticks', '100'])
    monkeypatch.setattr(batch, 'RAW_ROOTS', (tmp_path,))
    monkeypatch.setattr(batch, 'read_reference', lambda *args, **kwargs: approval)
    monkeypatch.setattr(batch.socket, 'gethostname', lambda: 'mbit10')
    monkeypatch.setattr(batch, 'Store', lambda *args: SimpleNamespace(by_id={}))
    monkeypatch.setattr(batch, 'validate_cleanup_tests', lambda *args: None)
    monkeypatch.setattr(batch, 'validate_inputs', lambda *args: ({}, {}))
    monkeypatch.setattr(batch, 'collect_series', collect)
    monkeypatch.setattr(batch, 'allocated_bytes', lambda *args: 0)
    monkeypatch.setattr(batch.lifecycle, 'SAMPLE_INTERVAL_SECONDS', .002)
    monkeypatch.setattr(batch.lifecycle, 'SharedCleanup', Budget)
    monkeypatch.setattr(batch.lifecycle, 'Owned', Owner)
    guards = []
    def make_guard(callback):
        value = Guard(callback); guards.append(value); return value
    monkeypatch.setattr(batch.lifecycle, 'Monitor', make_guard)
    monkeypatch.setattr(batch.lifecycle, 'identity', lambda pid: {'pid': pid, 'start_ticks': 1})
    monkeypatch.setattr(batch.lifecycle, 'ancestry', lambda *args: [])
    monkeypatch.setattr(batch.lifecycle, 'validate_samples', lambda *args, **kwargs: {})
    if original_failure:
        with pytest.raises(RuntimeError) as caught: batch.main()
        assert caught.value is failure
    else:
        batch.main()
    assert observations == [('interrupt_during_cleanup', False), ('sampled_cleanup', True), ('stop_deadline', clock.mono + .1)]
    assert guards[0].interrupt is False
    assert not guards[0].thread.is_alive()


@pytest.mark.parametrize('cleanup_seconds', [20, 41])
def test_resource_sampling_uses_cleanup_clock_without_extending_outer_deadline(tmp_path, monkeypatch, clock, cleanup_seconds):
    from contextlib import contextmanager
    policy=plan(); approval=admission(policy);approval['code_commit']='fixture'
    runs=tmp_path/policy['id'];events=[];guards=[]
    Path(str(runs)+'.dispatch').mkdir()
    original=RuntimeError('original fixture stage failure')
    class Budget:
        create=staticmethod(lambda *args,**kwargs:'fixture-binding')
        def __init__(self,*args):pass
        @contextmanager
        def reservation(self):yield clock.mono+.25
        def snapshot(self):return {'fixture_only':True}
    class Owner:
        def __init__(self,budget):self.budget=budget;self.history={}
        def sample(self):return {'rss_bytes':1}
        def finish(self,*args):
            events.append(('cleanup',guards[0].running,guards[0].interrupt))
            clock.mono += cleanup_seconds
            clock.wall += timedelta(seconds=cleanup_seconds)
            guards[0].callback()
            return {'state':'all_owned_descendants_absent','errors':[]}
    class Guard:
        def __init__(self,callback):
            self.callback=callback;self.running=False;self.interrupt=True;self.maximum_gap_seconds=self.maximum_guard_seconds=0;guards.append(self)
        def start(self):self.running=True
        def stop(self,deadline):events.append(('stop',deadline));self.running=False
    def collect(*args):
        clock.mono += 43160
        clock.wall += timedelta(seconds=43160)
    monkeypatch.setattr(sys,'argv',['batch','t15','--admission',str(tmp_path/'admission'),
        '--admission-sha256','fixture','--runs-dir',str(runs),'--lane','1',
        '--outer-started',clock.wall.isoformat(),'--outer-deadline',(clock.wall+timedelta(seconds=43200)).isoformat(),
        '--pane-pid','10','--pane-start-ticks','100'])
    monkeypatch.setattr(batch,'RAW_ROOTS',(tmp_path,))
    monkeypatch.setattr(batch,'read_reference',lambda *args,**kwargs:approval)
    monkeypatch.setattr(batch.socket,'gethostname',lambda:'mbit10')
    monkeypatch.setattr(batch,'Store',lambda *args:SimpleNamespace(by_id={},get=lambda *args:{}))
    monkeypatch.setattr(batch,'validate_cleanup_tests',lambda *args:None)
    monkeypatch.setattr(batch,'validate_inputs',lambda *args:({},{}))
    monkeypatch.setattr(batch,'collect_series',collect)
    monkeypatch.setattr(batch,'allocated_bytes',lambda *args:0)
    monkeypatch.setattr(batch.os,'statvfs',lambda *args:SimpleNamespace(f_bavail=100*1024**3,f_frsize=1))
    monkeypatch.setattr(batch,'lease_observation',lambda *args:{'fixture_only':True})
    monkeypatch.setattr(batch.lifecycle,'SharedCleanup',Budget)
    monkeypatch.setattr(batch.lifecycle,'Owned',Owner)
    monkeypatch.setattr(batch.lifecycle,'Monitor',Guard)
    monkeypatch.setattr(batch.lifecycle,'identity',lambda pid:{'pid':pid,'start_ticks':1})
    monkeypatch.setattr(batch.lifecycle,'ancestry',lambda *args:[])
    monkeypatch.setattr(batch.lifecycle,'validate_samples',lambda *args,**kwargs:{})
    if cleanup_seconds > 30:
        with pytest.raises(ValueError, match='common batch deadline'): batch.main()
    else:
        batch.main()
    assert events[0]==('cleanup',True,False), events
    assert events[1]==('stop',clock.mono+.25),events
    saved=json.loads((runs/(policy['id']+'.driver')/'driver.json').read_text())
    assert saved['state']==('failed' if cleanup_seconds > 30 else 'complete')


@pytest.mark.parametrize('transition', ['acquire', 'release'])
def test_other_socket_transition_requires_stable_real_lock_snapshot(tmp_path, monkeypatch, transition):
    """Actual flock + hostlock publication ordering; no measured simulator work."""
    import fcntl
    monkeypatch.setenv('LACT_LEASE_ROOT', str(tmp_path))
    monkeypatch.setattr(batch.profile, '_verified_lane', lambda *args: 'verified own lane')
    for name in ('mbit10-evaluation', 'mbit10-evaluation-node0', 'mbit10-evaluation-node1'):
        (tmp_path / (name + '.lease')).touch()
        (tmp_path / (name + '.meta.json')).write_text(json.dumps({'state': 'held' if name.endswith('node0') else 'released'}))
    other = tmp_path / 'mbit10-evaluation-node1.meta.json'
    pauses = []
    with (tmp_path / 'mbit10-evaluation-node1.lease').open('rb') as lock:
        # Both hostlock windows can expose released metadata with a held kernel lock.
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        def settle(seconds):
            pauses.append(seconds)
            if transition == 'acquire':
                temp = other.with_suffix('.tmp')
                temp.write_text(json.dumps({'state': 'held', 'lease': {'generation': 2}}))
                temp.replace(other)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)
        monkeypatch.setattr(batch.time, 'sleep', settle)
        result = batch.lease_observation({}, 0)
        row = result['leases']['mbit10-evaluation-node1']
        assert row['kernel_held'] is (transition == 'acquire')
        assert row['sha256'] == hashlib.sha256(other.read_bytes()).hexdigest()
        assert len(pauses) >= 2 and sum(pauses) <= .25


def test_other_socket_persistent_disagreement_is_bounded(tmp_path, monkeypatch):
    import fcntl
    monkeypatch.setenv('LACT_LEASE_ROOT', str(tmp_path))
    monkeypatch.setattr(batch.profile, '_verified_lane', lambda *args: 'verified own lane')
    for name in ('mbit10-evaluation', 'mbit10-evaluation-node0', 'mbit10-evaluation-node1'):
        (tmp_path / (name + '.lease')).touch()
        (tmp_path / (name + '.meta.json')).write_text(json.dumps({'state': 'held' if name.endswith('node0') else 'released'}))
    pauses = []
    monkeypatch.setattr(batch.time, 'sleep', pauses.append)
    with (tmp_path / 'mbit10-evaluation-node1.lease').open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ValueError, match='metadata and kernel'):
            batch.lease_observation({}, 0)
    assert len(pauses) == 4 and sum(pauses) <= .25


@pytest.mark.parametrize('fault', ['own', 'legacy'])
def test_snapshot_retry_never_tolerates_own_change_or_legacy_conflict(tmp_path, monkeypatch, fault):
    import fcntl
    monkeypatch.setenv('LACT_LEASE_ROOT', str(tmp_path))
    monkeypatch.setattr(batch.profile, '_verified_lane', lambda *args: 'verified own lane')
    for name in ('mbit10-evaluation', 'mbit10-evaluation-node0', 'mbit10-evaluation-node1'):
        (tmp_path / (name + '.lease')).touch()
        (tmp_path / (name + '.meta.json')).write_text(json.dumps({'state': 'held' if name.endswith('node0') else 'released'}))
    pauses = []
    with (tmp_path / 'mbit10-evaluation-node1.lease').open('rb') as other, (tmp_path / 'mbit10-evaluation.lease').open('rb') as legacy:
        fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
        def change(seconds):
            pauses.append(seconds)
            if fault == 'own':
                (tmp_path / 'mbit10-evaluation-node0.meta.json').write_text(json.dumps({'state': 'held', 'lease': {'generation': 999}}))
            else:
                fcntl.flock(legacy, fcntl.LOCK_EX | fcntl.LOCK_NB)
        monkeypatch.setattr(batch.time, 'sleep', change)
        with pytest.raises(ValueError, match='own lane|legacy|metadata and kernel'):
            batch.lease_observation({}, 0)
    assert len(pauses) == 1


def test_other_socket_metadata_changes_during_kernel_probe_are_not_returned(tmp_path, monkeypatch):
    import fcntl
    monkeypatch.setenv('LACT_LEASE_ROOT', str(tmp_path))
    monkeypatch.setattr(batch.profile, '_verified_lane', lambda *args: 'verified own lane')
    for name in ('mbit10-evaluation', 'mbit10-evaluation-node0', 'mbit10-evaluation-node1'):
        (tmp_path / (name + '.lease')).touch()
        (tmp_path / (name + '.meta.json')).write_text(json.dumps({'state': 'held' if name.endswith('node0') else 'released'}))
    path = tmp_path / 'mbit10-evaluation-node1.meta.json'
    real_flock = fcntl.flock
    probes = []
    def torn(fd, operation):
        # The fourth shared probe is the other socket after legacy on pass two.
        if operation == fcntl.LOCK_SH | fcntl.LOCK_NB:
            probes.append(fd)
            if len(probes) == 4:
                temp = path.with_suffix('.tmp')
                temp.write_text(json.dumps({'state': 'released', 'lease': {'generation': 2}}))
                temp.replace(path)
        return real_flock(fd, operation)
    monkeypatch.setattr(batch.fcntl, 'flock', torn)
    pauses = []
    monkeypatch.setattr(batch.time, 'sleep', pauses.append)
    result = batch.lease_observation({}, 0)
    row = result['leases']['mbit10-evaluation-node1']
    assert result['other_socket_snapshot_attempts'] == 4
    assert row['metadata']['lease']['generation'] == 2
    assert row['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_external_generations_must_stabilize_before_return(tmp_path, monkeypatch):
    monkeypatch.setenv('LACT_LEASE_ROOT', str(tmp_path))
    monkeypatch.setattr(batch.profile, '_verified_lane', lambda *args: 'verified own lane')
    for name in ('mbit10-evaluation', 'mbit10-evaluation-node0', 'mbit10-evaluation-node1'):
        (tmp_path / (name + '.lease')).touch()
        (tmp_path / (name + '.meta.json')).write_text(json.dumps({'state': 'held' if name.endswith('node0') else 'released'}))
    path = tmp_path / 'mbit10-evaluation-node1.meta.json'
    pauses = []
    def churn(seconds):
        pauses.append(seconds)
        path.write_text(json.dumps({'state': 'released', 'lease': {'generation': len(pauses)}}))
    monkeypatch.setattr(batch.time, 'sleep', churn)
    with pytest.raises(ValueError, match='did not stabilize'):
        batch.lease_observation({}, 0)
    assert len(pauses) == 4


# T15 pilot b1 (resume decisions R2/R3, 2026-09-27 ET): fixtures are not evidence.

def pilot_plan():
    return json.loads(batch.plan_path(batch.PILOT_KIND).read_text())


def test_pilot_plan_keeps_the_unchanged_grid_and_approved_partition():
    value = pilot_plan(); batch.validate_plan(value, batch.PILOT_KIND)
    old = json.loads((batch.PLAN_DIR/'bfs-t15-lease-recovery-simulator-batch-20260927-a1.json').read_text())
    strip = lambda row: {k: v for k, v in row.items() if k != 'id'}
    assert [strip(r) for r in value['series']] == [strip(r) for r in old['series']]
    assert [r['id'].rsplit('.', 1)[1] for r in value['series']] == ['uniform18', 'kronecker18']
    assert {k: value[k] for k in ('repetitions', 'threads', 'roi', 'verifier', 'record_sha256')} == \
        {k: old[k] for k in ('repetitions', 'threads', 'roi', 'verifier', 'record_sha256')}
    allocation = value['allocation']
    assert sum(allocation['partition_seconds'].values()) == allocation['total_seconds'] == 172800
    assert (allocation['storage_gib'], allocation['overhead_reserve_gib'], allocation['per_series_cap_gib']) == (96, 4, 60)
    assert value['concurrency']['gem5_slots'] == 1 and value['lane']['node'] == 0
    assert value['bounds']['profile_seconds'] == 120 and 'clock_policy' not in value
    assert batch.preparation_charges(value) == [{'id': 'bfs-t15-pilot-preparation-20260927-b1',
                                                'elapsed_seconds': 3600, 'raw_bytes': 4*batch.GIB}]
    batch.validate_preparation_reservation(value, {})
    with pytest.raises(ValueError, match='approved partition'):
        batch.validate_preparation_reservation(value, {'preparation_reservation': {}})
    value['concurrency']['gem5_slots'] = 2
    with pytest.raises(ValueError, match='fixed scope'): batch.validate_plan(value, batch.PILOT_KIND)


def test_pilot_series_command_binds_slot_pool_profile_and_bounds(tmp_path):
    value = pilot_plan(); approval = admission(value)
    row = value['series'][1]
    command = batch.series_command(value, row, approval, tmp_path/'c', tmp_path/'raw', tmp_path/'r', 0,
                                   82800, 60, None, tmp_path/'slots')
    arg = lambda name: command[command.index(name) + 1]
    assert arg('--gem5-slot-dir') == str(tmp_path/'slots') and arg('--gem5-slots') == '1'
    assert arg('--profile-seconds') == '120' and arg('--diagnostic-seconds') == '10800'
    assert arg('--run-seconds') == '7200' and arg('--batch-storage-gib') == '60' and arg('--lane') == '0'
    assert '--protocol' not in command and arg('--workload') == row['workload']


def test_pilot_allowance_clamps_each_family_to_its_cap_and_the_shared_pool(clock):
    value = pilot_plan()
    charges = batch.preparation_charges(value)
    ledger = batch.Ledger(value, admission(value, charges=charges), clock.mono, clock.wall)
    assert ledger.next_allowance(0, 60) == (82800, 60)
    assert ledger.next_allowance(40*batch.GIB, 60) == (82800, 52)  # 96 - 4 overhead - 40 aggregate
    with pytest.raises(ValueError, match='exhausted'):
        ledger.next_allowance(92*batch.GIB, 60)


def _pilot_receipt(tmp_path, kind, approval, cases, failure=None):
    junit = tmp_path/(kind+'.xml')
    body = ''.join(f'<testcase name="{name}">' + ('<failure/>' if name == failure else '') + '</testcase>'
                   for name in cases)
    junit.write_text(f'<testsuites><testsuite>{body}</testsuite></testsuites>')
    return ref(tmp_path/(kind+'.json'), {'format': 'swdb.bfs.pilot-linux-tests.v1', 'kind': kind,
        'host': 'mbit10', 'platform': 'linux', 'code_commit': approval['code_commit'],
        'runtime_sha256': approval['runtime_sha256'], 'returncode': 0,
        'started': '2026-09-27T08:00:00-04:00', 'finished': '2026-09-27T08:01:00-04:00',
        'junit': {'path': str(junit), 'sha256': artifacts.file_hash(junit)}})


@pytest.mark.parametrize('fault', [None, 'failure', 'missing', 'runtime'])
def test_pilot_requires_fresh_linux_tests_at_exact_runtime(tmp_path, fault):
    value = pilot_plan(); approval = {**admission(value), 'code_commit': 'c'*40}
    refs = []
    for kind, cases in batch.PILOT_TEST_CASES.items():
        names = sorted(cases)
        if fault == 'missing' and kind == 'owned_cleanup': names = names[1:]
        refs.append(_pilot_receipt(tmp_path, kind, approval, names,
                                   names[0] if fault == 'failure' and kind == 'dx100_interruption' else None))
    approval['linux_cleanup_tests'] = refs
    if fault == 'runtime': approval['runtime_sha256'] = {'other': 'x'}
    if fault is None:
        batch.validate_pilot_tests(value, approval)
    else:
        with pytest.raises(ValueError): batch.validate_pilot_tests(value, approval)
