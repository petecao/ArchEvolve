#!/usr/bin/env python3
"""One fixed accelerated correctness case. Created: 2026-09-26 ET.

Dispatch requires the retained prerequisites. Caller: TERM3570s, KILL after30s.
"""
import argparse
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from zoneinfo import ZoneInfo
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import bfs_dx100_coverage_graph as graph_case
from scripts import dx100_witness_continuation as a3, dx100_capacity
from scripts import bfs_owned_observer as owned_observer
from scripts.bfs_native_paired_pilot import DescendantRSS, ResourceMonitor
from scripts.bfs_process import interruption_signals, run_stage, save_receipt
from swdb import artifacts, bfs_protocol, dx100_coverage, dx100_witness, profile, yamlio
from swdb.store import Store

RUN_ID = 'bfs-dx100-coverage-20260926-a1'
CANDIDATE = 'bfs-author-maa-compile-20260925-a1.candidate'
CANDIDATE_SHA = '1018e9002c86a2e0ef7850be0bc66dbec9849d388cced45542c61a18cd619fff'
SOURCE_SHA = 'd5ac642dfe1a2ba5ef548f86c5c269ef54164b55985badc55872288f41504e9d'
A3_COMMIT = '1018432fdb3800522d723afb874f3bffa41dd0e5'
DEADLINE = datetime(2026, 9, 26, 16, 45, tzinfo=ZoneInfo('America/New_York'))
RAW_ROOT = Path('/data/yanruj/EvolveSWDB_runs/bfs-dx100-coverage-20260926')
BUILD_ROOT = Path('/data1/yanruj/EvolveSWDB_builds')
BOUNDS = {'outer_seconds': 3600, 'cleanup_seconds': 30, 'generation_registration_seconds': 120,
          'compile_seconds': 240, 'execute_seconds': 3100, 'checkpoint_seconds': 300,
          'simulation_seconds': 2700, 'sampled_rss_bytes': 48 * 1024**3,
          'artifact_bytes': 4 * 1024**3, 'raw_reserve_bytes': 30 * 1024**3,
          'build_reserve_bytes': 10 * 1024**3, 'sample_gap_seconds': 30}
RUNTIME_FILES = ('scripts/bfs_dx100_coverage_execution.py', 'scripts/bfs_dx100_coverage_graph.py',
    'scripts/dx100_witness_continuation.py', 'scripts/bfs_process.py',
    'scripts/bfs_native_paired_pilot.py', 'scripts/bfs_owned_observer.py', 'scripts/dx100_capacity.py',
    'scripts/dx100_verify.py', 'scripts/dx100_host_memory.py', 'swdb/dx100.py',
    'swdb/dx100_candidate.py', 'swdb/dx100_witness.py', 'swdb/dx100_coverage.py',
    'swdb/bfs_protocol.py', 'swdb/processes.py')
require = a3.require


def now():
    return datetime.now(DEADLINE.tzinfo)


def reference(path):
    return {'path': str(Path(path).absolute()), 'sha256': artifacts.file_hash(path)}


def launch_budget(current):
    require(current.utcoffset() is not None and (DEADLINE-current).total_seconds() >= 3600,
            'coverage needs the complete 3600-second window; latest start15:45 ET')
    return 3570


def validate_a3(ref, store, current, proc=Path('/proc')):
    audit = json.loads(a3.reference(ref))
    require(audit.get('id') == a3.PROBE_ID and audit.get('state') == 'passed'
            and a3.stamp(audit.get('observed_at')) <= current, 'actual passed a3 audit is required')
    evaluation = yaml.load(a3.reference(audit['evaluation']).decode(), Loader=yamlio._Loader)
    require(evaluation.get('id') == a3.PROBE_ID and evaluation.get('evidence_kind') == 'execution'
            and artifacts.digest(evaluation) == audit.get('evaluation_sha256')
            and artifacts.digest(evaluation) == artifacts.digest(store.get(a3.PROBE_ID, 'evaluation')),
            'a3 audit differs from its current actual evaluation')
    require(artifacts.digest(evaluation['request']) == a3.REQUEST_SHA256, 'a3 request changed')
    dx100_witness.validate_completed_witness(evaluation, verify_artifacts=True)
    driver = json.loads(a3.reference(audit['driver']))
    require(driver.get('id') == a3.PROBE_ID and driver.get('state') == 'complete'
            and driver.get('evaluation_sha256') == audit['evaluation_sha256']
            and a3.stamp(driver['started']) <= a3.stamp(driver['finished']) <= a3.DEADLINE
            and a3.stamp(driver['finished']) <= a3.stamp(audit['observed_at'])
            and type(driver.get('host_wall_s')) in (int, float) and 0 <= driver['host_wall_s'] <= 1170,
            'a3 completed driver or its original deadline is unverified')
    began, ended = a3.stamp(driver['started']), a3.stamp(driver['finished'])
    a3.launch_budget(began)
    require(abs((ended-began).total_seconds() - driver['host_wall_s']) <= 1
            and driver.get('outer_seconds') == a3.OUTER_SECONDS
            and driver.get('cleanup_reserve_seconds') == a3.CLEANUP_SECONDS
            and driver.get('deadline_et') == a3.DEADLINE.isoformat(),
            'a3 retained duration or fixed bounds differ')
    require(driver.get('repository_commit') == A3_COMMIT and driver.get('runtime_sha256') == a3.RUNTIME
            and driver.get('request', {}).get('canonical_sha256') == a3.REQUEST_SHA256
            and artifacts.digest(yaml.load(a3.reference(driver['request']).decode(), Loader=yamlio._Loader)) == a3.REQUEST_SHA256,
            'a3 retained runtime or request differs from its prospective pins')
    require(all(row.get('state') == 'complete' and row.get('returncode') == 0
                for row in driver.get('stages', [])) and driver.get('stages'),
            'a3 driver retains an incomplete stage')
    validate_terminal_cleanup(audit, driver, current, proc)
    return {'audit': ref, 'evaluation': audit['evaluation'], 'evaluation_sha256': audit['evaluation_sha256']}


def validate_terminal_cleanup(audit, driver, current, proc=Path('/proc'), *, in_process=False):
    """Reopen one finished socket-0 lane and every observed owned identity."""
    if not in_process:
        require(all(name in audit and a3.reference(audit[name], 64).strip() == b'0'
                    for name in ('driver_exit', 'observer_exit')),
                'a3 driver and observer must both retain successful exit receipts')
    lane = json.loads(a3.reference(audit['lane']))['socket_lane']
    require(lane.get('host') == 'mbit10' and type(lane.get('node')) is int and lane['node'] == 0
            and lane.get('lease_name') == 'mbit10-evaluation-node0'
            and type(lane.get('lease_generation')) is int and lane['lease_generation'] > 0
            and type(lane.get('exit_code')) is int and lane['exit_code'] == 0
            and a3.reference(audit['outer_exit'], 64).strip() == b'0'
            and a3.stamp(lane['started_utc']) <= a3.stamp(driver['started'])
            and a3.stamp(driver['finished']) < a3.stamp(lane['ended_utc']) + timedelta(seconds=1)
            and a3.stamp(lane['ended_utc']) <= a3.stamp(audit['observed_at']) <= current
            and driver.get('lane') == f"mbit10-evaluation-node0 (verified: affinity, bind:0, lease held, generation {lane['lease_generation']})",
            'completed lane/outer result is not bound')
    lease = json.loads(a3.reference(audit['lease_snapshot']))
    require(lease.get('state') == 'released' and lease['lease']['generation'] == lane['lease_generation']
            and lease['lease']['lease_name'] == 'mbit10-evaluation-node0'
            and a3.stamp(lane['ended_utc']) <= a3.stamp(lease['released_at']) <= a3.stamp(audit['observed_at']),
            'a3 lease release is unverified')
    observations = json.loads(a3.reference(audit['process_observations']))
    require(observations.get('state') == ('driver_sampling_finished' if in_process else 'driver_terminated')
            and observations.get('sampling_complete') is True
            and observations.get('cleanup_verified') is False,
            'terminal observer did not complete its bounded sampling')
    if in_process:
        require(observations.get('observer_kind') == 'in_process_driver'
                and observations['resource_samples'] == driver['rss']['samples']
                and audit['process_observations'] == driver['process_observations']
                and observations['observer_identity'] == observations['driver_identity'],
                'coverage in-process sampling identity differs')
    ancestors, observed = observations['ancestry'], observations['owned_processes']
    samples = [json.loads(line) for line in a3.reference(observations['resource_samples'], 16 * 1024**2).splitlines() if line.strip()]
    require(samples and all(isinstance(row.get('processes'), list) and row['processes'] for row in samples),
            'a3 descendant process samples are missing')
    sampled = [process for row in samples for process in row['processes']]
    if driver.get('rss', {}).get('samples'):
        sampled += [process for line in a3.reference(driver['rss']['samples'], 16 * 1024**2).splitlines()
                    if line.strip() for process in json.loads(line)['processes']]
        require(observations['driver_pid'] == driver.get('driver_pid'), 'terminal observer names another driver')
    require(isinstance(ancestors, list) and ancestors and isinstance(observed, list) and observed
            and type(observations.get('driver_pid')) is int
            and ancestors[0]['pid'] == observations['driver_pid']
            and any(row['pid'] == observations['driver_pid'] for row in sampled), 'a3 owned ancestry is unavailable')
    driver_identity = (observations['driver_identity']['pid'], observations['driver_identity']['start_ticks'])
    require(driver_identity == (ancestors[0]['pid'], ancestors[0]['start_ticks'])
            and observations['driver_identity']['pid'] == observations['driver_pid']
            and all((row['pid'], row['start_ticks']) == driver_identity
                    for row in sampled if row['pid'] == observations['driver_pid']),
            'terminal observer driver identity differs')
    expected = {(row['pid'], row['start_ticks']) for row in ancestors + observed + sampled
                + [observations['driver_identity'], observations['observer_identity']]}
    declared = {(row['pid'], row['start_ticks']) for row in audit['owned_processes']}
    require(expected <= declared, 'a3 audit omits observed owned process identities')
    zombie = audit.get('cleanup_state') == 'terminal_no_live_owned_processes'
    require((zombie and audit.get('owned_processes_absent') is False
             and audit.get('owned_processes_nonrunning') is True)
            or (audit.get('cleanup_state') == 'terminal_and_reaped' and audit.get('owned_processes_absent') is True),
            'a3 audit lacks terminal process cleanup')
    declared_launcher = observations['launcher_identity']
    launcher = (declared_launcher['pid'], declared_launcher['start_ticks'])
    require(declared_launcher['pid'] == observations['pane_pid']
            and launcher in {(row['pid'], row['start_ticks']) for row in ancestors},
            'a3 launcher identity differs from its captured tmux pane')
    launcher = launcher if zombie else None
    a3.verify_terminal_processes(audit['owned_processes'], proc, launcher_identity=launcher)


def validate_source(store):
    candidate = store.get(CANDIDATE, 'candidate')
    require(candidate is not None and artifacts.digest(candidate) == CANDIDATE_SHA
            and candidate.get('artifact_role') == 'source_baseline'
            and candidate['artifact']['sha256'] == SOURCE_SHA, 'unchanged author candidate identity differs')
    source = store.get(candidate['source_snapshot'], 'source_snapshot')
    require(source['artifact']['sha256'] == SOURCE_SHA and source['application'] == 'dx100-gapbs',
            'author source snapshot differs')
    path = artifacts.verify(candidate['artifact']) / 'benchmarks/gapbs/src/bfs.cc'
    require(artifacts.file_hash(path) == graph_case.AUTHOR_SOURCE_SHA256, 'author BFS source changed')
    return candidate


def compile_request(*, run_id=RUN_ID):
    template = yamlio.load(a3.REQUEST)
    return {'message_version': '1.0', 'id': run_id + '.compile', 'machine': 'mbit10',
        'hardware_target': template['hardware_target'], 'model_root': template['model_root'],
        'build_evaluation': template['build_evaluation'], 'candidate': CANDIDATE,
        'function': 'DOBFSMAA', 'accelerated': True, 'roi': 'bfs.complete_call.v1',
        'budget': {'total_seconds': 240, 'build_seconds': 240, 'memory_gib': 48, 'storage_gib': 4}}


def registration_request(graph, *, run_id=RUN_ID):
    return {'message_version': '1.0', 'id': run_id + '.workload', 'version': 1,
        'kernel': 'gapbs-bfs', 'family': 'fixed_dx100_correctness_coverage',
        'generator': {'name': 'bfs_dx100_coverage_graph.v1', 'revision': artifacts.file_hash(Path(graph_case.__file__)),
                      'parameters': {'vertices': 8212, 'directed_arcs': 147492, 'frontier': 4097, 'shared': 16}},
        'sources': [0], 'normalization': bfs_protocol.NORMALIZATION,
        'representations': [{'id': run_id + '.sg32', 'application': 'dx100-gapbs',
            'format': 'gapbs_sg32le', **{k: graph['representation'][k] for k in ('path', 'sha256')}}]}


def execution_request(compiled, workload, graph, *, run_id=RUN_ID):
    require(compiled.get('id') == run_id + '.compile' and compiled.get('evidence_kind') == 'execution'
            and compiled.get('outcome', {}).get('state') == 'complete'
            and compiled['outcome']['stage'] == 'candidate_build'
            and compiled['build']['adapter'] == 'dx100.complete_call.v2'
            and compiled.get('candidate') == CANDIDATE
            and compiled['context']['candidate_sha256'] == SOURCE_SHA
            and artifacts.digest(compiled['request']) == artifacts.digest(compile_request(run_id=run_id)),
            'fresh exact author complete-call compilation is required')
    require(workload.get('requested_id') == run_id + '.workload'
            and workload['definition']['canonical_sha256'] == graph['canonical_sha256']
            and workload['definition']['sources'] == [0], 'registered coverage graph identity differs')
    template = yamlio.load(a3.REQUEST)
    return {'message_version': '1.0', 'id': run_id + '.execute', 'machine': 'mbit10',
        'hardware_target': template['hardware_target'], 'model_root': template['model_root'],
        'build_evaluation': template['build_evaluation'], 'simulator': template['simulator'],
        'candidate': CANDIDATE, 'candidate_build': compiled['id'],
        'binary': {'path': compiled['build']['binary'], 'sha256': compiled['build']['binary_sha256']},
        'workload': {'id': workload['id'], 'source': 0, 'representation': {
            k: graph['representation'][k] for k in ('path', 'sha256')}},
        'configuration': {'mode': 'MAA', 'l3_size_mb': 8, 'l3_assoc': 16, 'tile_elements': 16384},
        'verification': {'checker': 'dx100.bfs.verifier.v2', 'max_ticks': 10000000000,
                         'coverage': True, 'post_roi_trace': 'SyscallBase'},
        'budget': {'total_seconds': 3100, 'memory_gib': 48, 'storage_gib': 4,
                   'checkpoint_seconds': 300, 'run_seconds': 2700}}


def validate_coverage(evaluation, request, graph, *, run_id=RUN_ID):
    require(evaluation.get('evidence_kind') == 'execution' and evaluation.get('id') == run_id + '.execute'
            and artifacts.digest(evaluation.get('request')) == artifacts.digest(request)
            and evaluation.get('gain_claim') is False, 'coverage evaluation identity differs')
    dx100_witness.validate_completed_witness(evaluation, verify_artifacts=True)
    for name in ('binary', 'simulator'):
        ref = request[name]
        path = Path(ref['path'])
        require(path.is_absolute() and path.is_file() and not path.is_symlink()
                and path.stat().st_size <= BOUNDS['artifact_bytes']
                and artifacts.file_hash(path) == ref['sha256'],
                f'coverage {name} bytes differ from the exact execution')
    representation = request['workload']['representation']
    require(representation == {key: graph['representation'][key] for key in ('path', 'sha256')}
            and request['workload']['source'] == 0, 'coverage graph representation or source differs')
    adjacency = bfs_protocol._sg_graph(a3.reference(representation, 1024**2), 4)
    require(artifacts.digest(bfs_protocol._canonical(adjacency)) == graph['canonical_sha256']
            == artifacts.digest(bfs_protocol._canonical(graph_case.graph())),
            'reopened graph differs from the prospectively fixed topology')
    check = evaluation['correctness']['checks'][0]
    require(check['graph_sha256'] == graph['canonical_sha256'] and check['source'] == 0
            and check['parent_results'][0]['vertices'] == 8212
            and check['parent_results'][0]['parent_count'] == 8212,
            'protected parent result does not bind the fixed original graph')
    stats = a3.reference(evaluation['context']['statistics'], 16 * 1024**2).decode()
    require(stats.count('Begin Simulation Statistics') == stats.count('End Simulation Statistics') == 1,
            'coverage statistics must contain one sealed interval')
    values = {}
    counters = []
    for line in stats.splitlines():
        found = re.match(r'(simTicks|finalTick)\s+(\d+)(?:\s|$)', line)
        if found:
            require(found[1] not in values, 'coverage interval repeats a tick field')
            values[found[1]] = found[2]
        found = re.match(r'\S*maa\S*\.numInst\s+(\d+)(?:\s|$)', line)
        if found:
            counters.append(int(found[1]))
    log = Path(check['output']['path'])
    require(artifacts.file_hash(log) == check['output']['sha256'], 'coverage trace changed')
    observed = dx100_coverage.observe(log, values, 16384,
                                      trace=dx100_coverage.trace_reference(evaluation))
    retained = check['coverage']
    require(all(artifacts.digest(observed[key]) == artifacts.digest(retained.get(key)) for key in observed),
            'retained coverage differs from the reopened raw trace')
    require(retained.get('accelerator_executed') is True and any(value > 0 for value in counters)
            and all(observed['completed_trace_units'].get(unit, 0) > 0 for unit in 'SIAR'),
            'accelerator execution is unobserved')
    require(all(observed[key]['state'] == 'observed' and observed[key]['count'] > 0
                for key in ('full_tiles', 'tail_tiles', 'competing_parent_updates')),
            'full/tail/competing-parent coverage is incomplete')
    require(observed['competing_parent_updates']['parent_storage']['count'] == 8212,
            'coverage trace parent storage differs from the returned graph result')
    return observed


def validate_resources(driver):
    """Validate sampled guards; this cannot establish unobserved true peaks."""
    began, ended = a3.stamp(driver['started']), a3.stamp(driver['finished'])
    rows = [json.loads(line) for line in a3.reference(driver['rss']['samples'], 16 * 1024**2).splitlines() if line.strip()]
    require(len(rows) >= 2 and type(driver.get('driver_pid')) is int and driver['driver_pid'] > 0,
            'coverage resource samples or driver identity are incomplete')
    times, known, driver_identity = [began], set(), None
    for row in rows:
        sampled, start, finish = (a3.stamp(row[key]) for key in ('sampled_at', 'guard_started', 'guard_finished'))
        require(times[-1] <= start <= sampled <= finish <= ended
                and type(row.get('guard_seconds')) in (int, float) and 0 <= row['guard_seconds'] <= 30
                and (finish-start).total_seconds() <= row['guard_seconds'] + 1,
                'coverage resource guard is outside its interval or bound')
        times.append(sampled)
        processes = row['processes']
        require(processes and all(type(p.get(key)) is int and p[key] >= 0 for p in processes
                                 for key in ('pid', 'parent_pid', 'start_ticks', 'rss_bytes'))
                and len({p['pid'] for p in processes}) == len(processes), 'coverage resource process identities are malformed')
        ids = {p['pid']: (p['pid'], p['start_ticks']) for p in processes}
        parents = {p['pid']: p['parent_pid'] for p in processes}
        for pid in parents:
            visited = set()
            while pid in parents:
                require(pid not in visited, 'coverage resource sample has an ownership cycle')
                visited.add(pid)
                pid = parents[pid]
        require(driver['driver_pid'] in ids, 'coverage sample omits its driver')
        driver_identity = driver_identity or ids[driver['driver_pid']]
        require(ids[driver['driver_pid']] == driver_identity, 'coverage driver PID was reused')
        owned = {pid for pid, identity in ids.items() if identity in known or identity == driver_identity}
        pending = [p for p in processes if p['pid'] not in owned]
        while pending:
            connected = [p for p in pending if p['parent_pid'] in owned]
            require(connected, 'coverage resource sample contains an unowned process')
            owned.update(p['pid'] for p in connected)
            pending = [p for p in pending if p['pid'] not in owned]
        known.update(ids.values())
        require(type(row.get('rss_bytes')) is int and row['rss_bytes'] == sum(p['rss_bytes'] for p in processes)
                and row['rss_bytes'] <= BOUNDS['sampled_rss_bytes']
                and type(row.get('artifact_bytes')) is int and 0 <= row['artifact_bytes'] <= BOUNDS['artifact_bytes']
                and type(row.get('raw_free_bytes')) is int and row['raw_free_bytes'] >= BOUNDS['raw_reserve_bytes']
                and type(row.get('build_free_bytes')) is int and row['build_free_bytes'] >= BOUNDS['build_reserve_bytes']
                and row.get('lane') == driver.get('lane'), 'coverage sampled resource or lane bound failed')
    times.append(ended)
    require(all(0 <= (right-left).total_seconds() <= 30 for left, right in zip(times, times[1:])),
            'coverage resource observation gap exceeds30s')
    require(type(driver['rss'].get('sampled_peak_bytes')) is int
            and driver['rss']['sampled_peak_bytes'] == max(row['rss_bytes'] for row in rows)
            and type(driver.get('artifact_peak_bytes')) is int
            and driver['artifact_peak_bytes'] == max(row['artifact_bytes'] for row in rows),
            'coverage sampled peak differs from raw observations')


def validate_completed(ref, store, current, expected_commit, proc=Path('/proc')):
    """Admit actual fixed coverage using an independently selected code commit."""
    require(isinstance(expected_commit, str) and re.fullmatch('[a-f0-9]{40}', expected_commit),
            'coverage admission needs a caller-pinned prospective commit')
    audit = json.loads(a3.reference(ref))
    require(audit.get('id') == RUN_ID and audit.get('state') == 'passed'
            and a3.stamp(audit['observed_at']) <= current, 'coverage terminal audit is not passed')
    driver = json.loads(a3.reference(audit['driver']))
    began, ended = a3.stamp(driver['started']), a3.stamp(driver['finished'])
    allowance = launch_budget(began)
    wall = driver.get('host_wall_s')
    require(driver.get('id') == RUN_ID and driver.get('state') == 'complete'
            and driver.get('repository_commit') == expected_commit
            and artifacts.digest(driver.get('bounds')) == artifacts.digest(BOUNDS)
            and driver.get('deadline_et') == DEADLINE.isoformat()
            and driver.get('gain_claim') is driver.get('profiling') is driver.get('automatic_retry_allowed') is False
            and began <= ended <= DEADLINE and ended <= a3.stamp(audit['observed_at'])
            and type(wall) in (int, float) and 0 <= wall <= allowance
            and abs((ended-began).total_seconds()-wall) <= 1, 'coverage driver bounds, runtime, or interval differ')
    require(set(driver['runtime']) == set(RUNTIME_FILES), 'coverage runtime references are incomplete')
    root = Path(driver['runtime'][RUNTIME_FILES[0]]['path']).parents[1]
    for path in RUNTIME_FILES:
        value = driver['runtime'][path]
        expected = hashlib.sha256(subprocess.check_output(['git', 'show', expected_commit + ':' + path], cwd=ROOT, timeout=10)).hexdigest()
        require(value['path'] == str(root / path) and value['sha256'] == expected,
                'coverage runtime source differs from the caller-pinned commit')
        a3.reference(value, 4 * 1024**2)
    validate_a3(driver['prerequisites']['a3']['audit'], store, current, proc)
    for kind in ('paired', 'provider'):
        a3.validate_completion(driver['prerequisites'][kind]['audit'], kind, current, proc)
    validate_source(store)
    validate_resources(driver)
    validate_terminal_cleanup(audit, driver, current, proc, in_process=True)
    graph = driver['graph']
    require(graph['vertices'] == 8212 and graph['directed_arcs'] == 147492 and graph['source'] == 0
            and graph['author_bfs_source_sha256'] == graph_case.AUTHOR_SOURCE_SHA256,
            'coverage driver graph differs from the fixed case')
    evaluation = yaml.load(a3.reference(audit['evaluation']).decode(), Loader=yamlio._Loader)
    require(artifacts.digest(evaluation) == audit.get('evaluation_sha256') == driver.get('evaluation_sha256')
            and driver.get('evaluation') == RUN_ID + '.execute'
            and artifacts.digest(evaluation) == artifacts.digest(store.get(RUN_ID + '.execute', 'evaluation')),
            'coverage public evaluation differs from its retained result')
    folder = Path(audit['driver']['path']).parent
    require(folder == RAW_ROOT / RUN_ID and driver['rss']['samples']['path'] == str(folder / 'rss-samples.jsonl'),
            'coverage run folder or sample path differs')
    final = driver['final_accounting']
    require(began <= a3.stamp(final['observed_at']) <= ended
            and type(final.get('elapsed_seconds')) in (int, float) and 0 <= final['elapsed_seconds'] <= wall
            and type(final.get('artifact_bytes')) is int and 0 <= final['artifact_bytes'] <= BOUNDS['artifact_bytes']
            and type(final.get('raw_free_bytes')) is int and final['raw_free_bytes'] >= BOUNDS['raw_reserve_bytes']
            and type(final.get('build_free_bytes')) is int and final['build_free_bytes'] >= BOUNDS['build_reserve_bytes']
            and artifact_bytes([folder, BUILD_ROOT / (RUN_ID + '.compile')]) <= BOUNDS['artifact_bytes'],
            'coverage final accounting exceeds its time or storage bound')
    stages = driver['stages']
    names = ('capacity', 'generate', 'register-workload', 'dx100-compile', 'dx100-execute', 'fresh-get')
    limits = (30, 120, 120, 240, 3100, 30)
    require(len(stages) == len(names), 'coverage stage count implies an incomplete run or extra attempt')
    python = stages[0]['command'][0]
    require(Path(python).is_absolute(), 'coverage Python executable path is not absolute')
    outputs = {}
    for row, name, bound in zip(stages, names, limits):
        require(row.get('state') == 'complete' and type(row.get('returncode')) is int and row['returncode'] == 0
                and type(row.get('host_wall_s')) in (int, float) and 0 <= row['host_wall_s'] <= bound
                and type(row.get('timeout_s')) in (int, float) and 0 < row['timeout_s'] <= bound,
                'coverage stage failed or exceeded its original bound')
        require(row['output'] == str(folder / (name + '.stdout')) and row['stderr'] == str(folder / (name + '.stderr')),
                'coverage stage output path differs')
        outputs[name] = json.loads(a3.reference({'path': row['output'], 'sha256': row['stdout_sha256']}, 16 * 1024**2))
        a3.reference({'path': row['stderr'], 'sha256': row['stderr_sha256']}, 16 * 1024**2)
        if name == 'capacity':
            command = [python, str(root / 'scripts/dx100_capacity.py'), '--node', '0', '--output', str(folder / 'capacity.json')]
        elif name == 'generate':
            command = [python, str(root / 'scripts/bfs_dx100_coverage_graph.py'), '--output-directory', str(folder / 'graph'),
                       '--records', str(root / 'records'), '--lane', 'mbit10-evaluation-node0']
        elif name == 'fresh-get':
            command = [python, '-m', 'swdb', 'get', RUN_ID + '.execute', '--records', str(root / 'records'), '--format', 'json']
        else:
            request_ref = driver['requests'][name]
            require(request_ref['path'] == str(folder / (name + '.request.json')), 'coverage public request path differs')
            command = [python, '-m', 'swdb', name, request_ref['path'], '--records', str(root / 'records'),
                       *(['--runs-dir', str(folder), '--lane', '0'] if name.startswith('dx100-') else []), '--format', 'json']
        require(row['command'] == command, 'coverage stage command differs from the fixed public path')
    require(stages[1]['host_wall_s'] + stages[2]['host_wall_s'] <= 120,
            'coverage generation/registration exceeded their shared allowance')
    capacity = json.loads(a3.reference(outputs['capacity']))
    inputs = capacity['inputs']
    actual_capacity = dx100_capacity.capacity(inputs['node'], inputs['zones'], inputs['global'], 0,
                                             capacity['result']['page_size_bytes'])
    require(outputs['capacity']['path'] == str(folder / 'capacity.json')
            and capacity.get('format') == 'swdb.dx100.capacity.v1' and capacity.get('evidence_kind') == 'execution'
            and began <= a3.stamp(capacity['observed']) <= ended
            and capacity['observer_sha256'] == driver['runtime']['scripts/dx100_capacity.py']['sha256']
            and artifacts.digest(capacity['result']) == artifacts.digest(actual_capacity) == artifacts.digest(outputs['capacity']['result'])
            and actual_capacity['eligible'] is True, 'coverage actual capacity admission differs')
    require(artifacts.digest(outputs['generate']) == artifacts.digest(graph)
            and artifacts.digest(outputs['fresh-get']) == artifacts.digest(evaluation)
            and artifacts.digest(outputs['dx100-execute']) == artifacts.digest(evaluation),
            'coverage public stdout differs from retained graph/evaluation')
    compiled, workload = outputs['dx100-compile'], outputs['register-workload']
    require(artifacts.digest(compiled) == artifacts.digest(store.get(RUN_ID + '.compile', 'evaluation'))
            and artifacts.digest(workload) == artifacts.digest(store.get(workload['id'], 'workload')), 'coverage compile/workload public retrieval differs')
    requests = {'register-workload': registration_request(graph), 'dx100-compile': compile_request(),
                'dx100-execute': execution_request(compiled, workload, graph)}
    require(set(driver['requests']) == set(requests), 'coverage public request set differs')
    for name, expected in requests.items():
        require(artifacts.digest(json.loads(a3.reference(driver['requests'][name]))) == artifacts.digest(expected),
                'coverage retained request differs from the fixed request')
    coverage = validate_coverage(evaluation, requests['dx100-execute'], graph)
    require(artifacts.digest(coverage) == artifacts.digest(driver['coverage']), 'coverage driver summary differs from actual trace')
    return {'audit': ref, 'evaluation': audit['evaluation'], 'evaluation_sha256': audit['evaluation_sha256'],
            'driver': audit['driver'], 'repository_commit': expected_commit, 'coverage': coverage}


def fresh_paths(store, runs, builds):
    paths = [runs / RUN_ID, builds / (RUN_ID + '.compile')]
    require(not any(p.exists() or p.is_symlink() for p in paths), 'coverage output already exists; no retry/overwrite')
    require(not any(record.id in {RUN_ID + '.compile', RUN_ID + '.execute'}
                    or record.data.get('requested_id') == RUN_ID + '.workload' for record in store.records),
            'coverage record already exists; no retry/overwrite')


def artifact_bytes(paths):
    total = 0
    for path in paths:
        if not path.exists():
            continue
        for folder, dirs, files in os.walk(path, followlinks=False):
            require(not any((Path(folder) / name).is_symlink() for name in dirs),
                    'coverage output contains an unexpected directory symlink')
            for name in files:
                item = Path(folder) / name
                require(not item.is_symlink(), 'coverage output contains an unexpected symlink')
                try:
                    stat = item.stat()
                except FileNotFoundError:
                    continue
                total += max(stat.st_size, stat.st_blocks * 512)
    return total


def finalize_receipt(receipt, folder, started, deadline, observations, identities):
    """Keep final hashes, observations and receipt persistence inside the budget."""
    def accounting():
        value = {'artifact_bytes': artifact_bytes([folder, BUILD_ROOT / (RUN_ID + '.compile')])}
        for name, path in (('raw_free_bytes', folder), ('build_free_bytes', BUILD_ROOT)):
            status = os.statvfs(path)
            value[name] = status.f_bavail * status.f_frsize
        value.update(observed_at=now().isoformat(), elapsed_seconds=time.monotonic() - started)
        require(value['artifact_bytes'] <= BOUNDS['artifact_bytes']
                and value['raw_free_bytes'] >= BOUNDS['raw_reserve_bytes']
                and value['build_free_bytes'] >= BOUNDS['build_reserve_bytes'],
                'coverage final retained storage exceeds its bound or reserve')
        require(time.monotonic() <= deadline and now() <= DEADLINE,
                'coverage final accounting exceeded its fixed deadline')
        return value

    def persist_observations():
        if observations is not None and receipt.get('rss', {}).get('samples'):
            observations.update(state='driver_sampling_finished' if receipt['state'] == 'complete' else 'failed',
                sampling_complete=receipt['state'] == 'complete', resource_samples=receipt['rss']['samples'],
                owned_processes=[{'pid': pid, 'start_ticks': ticks} for pid, ticks in identities.items()])
            path = folder / 'process-observations.json'
            path.write_text(json.dumps(observations, indent=2) + '\n')
            receipt['process_observations'] = reference(path)

    try:
        if (folder / 'rss-samples.jsonl').exists():
            receipt['rss']['samples'] = reference(folder / 'rss-samples.jsonl')
        persist_observations()
        # Retain the first post-write accounting in the second write; both are
        # checked afterward, including the second write's actual storage cost.
        for _ in range(2):
            receipt['final_accounting'] = accounting()
            receipt.update(finished=now().isoformat(), host_wall_s=time.monotonic()-started)
            save_receipt(folder, receipt)
            accounting()
    except BaseException as exc:
        receipt.update(state='failed', final_accounting_error=f'{type(exc).__name__}: {exc}')
        persist_observations()
        receipt.update(finished=now().isoformat(), host_wall_s=time.monotonic()-started)
        save_receipt(folder, receipt)
        raise


def validate_runtime(commit, root=ROOT):
    require(isinstance(commit, str) and re.fullmatch('[a-f0-9]{40}', commit), 'exact prospective commit is required')
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True, timeout=10).strip() == commit,
            'coverage checkout differs from the prospective commit')
    require(subprocess.run(['git', 'diff', '--quiet', commit, '--', 'scripts', 'swdb', 'schemas', 'records'],
                           cwd=root, timeout=10).returncode == 0, 'coverage checkout has unreviewed tracked changes')
    references = {}
    for path in RUNTIME_FILES:
        expected = hashlib.sha256(subprocess.check_output(['git', 'show', commit + ':' + path], cwd=root, timeout=10)).hexdigest()
        require(artifacts.file_hash(root / path) == expected, 'coverage runtime differs from the prospective commit')
        references[path] = {'path': str(root / path), 'sha256': expected}
    return references


def require_other_leases_idle(lease_root=Path('/data1/yanruj/lact-host-lease')):
    for name in ('mbit10-evaluation-node1', 'mbit10-evaluation'):
        data = json.loads((lease_root / (name + '.meta.json')).read_text())
        require(data.get('state') == 'released', 'another socket or legacy lease is active')


def main():
    started, started_at = time.monotonic(), now()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--expected-commit', required=True)
    parser.add_argument('--pane-pid', type=int, required=True)
    parser.add_argument('--pane-start-ticks', type=int, required=True)
    for name in ('a3-audit', 'paired-completion', 'provider-completion'):
        parser.add_argument('--' + name, type=Path, required=True)
        parser.add_argument('--' + name.split('-')[0] + '-sha256', required=True)
    args = parser.parse_args()
    allowance = launch_budget(started_at)
    deadline = started + allowance
    require(socket.gethostname().split('.')[0] == 'mbit10', 'coverage execution requires mbit10')
    runs = args.runs_dir.resolve()
    require(runs == RAW_ROOT, 'coverage uses its fresh fixed raw root')
    store = Store(ROOT / 'records')
    fresh_paths(store, runs, BUILD_ROOT)
    machine = store.get('mbit10', 'machine')
    lane = profile._verified_lane(machine, 'mbit10-evaluation-node0')
    require_other_leases_idle()
    artifacts.external_directory(runs)
    folder = runs / RUN_ID
    folder.mkdir()
    receipt = {'id': RUN_ID, 'created': '2026-09-26', 'state': 'running', 'started': started_at.isoformat(),
        'driver_pid': os.getpid(), 'deadline_et': DEADLINE.isoformat(), 'bounds': BOUNDS, 'lane': lane,
        'stages': [], 'gain_claim': False, 'profiling': False, 'automatic_retry_allowed': False,
        'rss': {'sampled_peak_bytes': 0, 'scope': 'driver and observed descendants across sessions; sampled, not hard cap'},
        'artifact_peak_bytes': 0, 'prerequisites': {}}
    save_receipt(folder, receipt)
    sampler = DescendantRSS(os.getpid())
    observations = None
    last_sample = started_at
    def observe():
        nonlocal last_sample
        before, guard_started = time.monotonic(), now()
        row = sampler.sample()
        observed = a3.stamp(row['sampled_at'])
        require(0 <= (observed-last_sample).total_seconds() <= 30, 'resource sample gap exceeds30s')
        last_sample = observed
        row['lane'] = profile._verified_lane(machine, 'mbit10-evaluation-node0')
        row['artifact_bytes'] = artifact_bytes([folder, BUILD_ROOT / (RUN_ID + '.compile')])
        row['load_average'] = list(os.getloadavg())
        for name, path, reserve in [('raw_free_bytes', folder, BOUNDS['raw_reserve_bytes']),
                                    ('build_free_bytes', BUILD_ROOT, BOUNDS['build_reserve_bytes'])]:
            status = os.statvfs(path)
            row[name] = status.f_bavail * status.f_frsize
            require(row[name] >= reserve, 'coverage storage reserve failed')
        row['guard_seconds'] = time.monotonic() - before
        row.update(guard_started=guard_started.isoformat(), guard_finished=now().isoformat())
        with (folder / 'rss-samples.jsonl').open('a') as output:
            output.write(json.dumps(row) + '\n')
        receipt['rss']['sampled_peak_bytes'] = max(receipt['rss']['sampled_peak_bytes'], row['rss_bytes'])
        receipt['artifact_peak_bytes'] = max(receipt['artifact_peak_bytes'], row['artifact_bytes'])
        require(row['rss_bytes'] <= BOUNDS['sampled_rss_bytes'] and row['artifact_bytes'] <= BOUNDS['artifact_bytes'],
                'coverage sampled resource budget exhausted')
        require(row['guard_seconds'] <= 30 and time.monotonic() < deadline, 'coverage resource guard/deadline exceeded')
    monitor = ResourceMonitor(observe)
    def stage(command, seconds, name, *, stage_deadline=None):
        monitor.check()
        output = folder / (name + '.stdout')
        run_stage(receipt, folder, command, timeout=seconds, deadline=min(deadline, stage_deadline or deadline),
                  cwd=ROOT, output=output, stderr=folder / (name + '.stderr'), monitor=monitor.check)
        return output
    def public(command, request, seconds, *, stage_deadline=None):
        path = folder / (command + '.request.json')
        path.write_text(json.dumps(request, indent=2) + '\n')
        receipt.setdefault('requests', {})[command] = reference(path)
        output = stage([sys.executable, '-m', 'swdb', command, str(path), '--records', str(ROOT / 'records'),
            *(['--runs-dir', str(folder), '--lane', '0'] if command.startswith('dx100-') else []), '--format', 'json'],
            seconds, command, stage_deadline=stage_deadline)
        return json.loads(output.read_text())
    try:
        monitor.start()
        receipt['repository_commit'] = args.expected_commit
        receipt['runtime'] = validate_runtime(args.expected_commit)
        driver_identity = owned_observer.identity(os.getpid())
        pane_identity = {'pid': args.pane_pid, 'start_ticks': args.pane_start_ticks}
        ancestors = owned_observer.ancestry(driver_identity, pane_identity)
        observations = {'driver_pid': os.getpid(), 'driver_identity': driver_identity,
            'observer_identity': driver_identity, 'observer_kind': 'in_process_driver',
            'pane_pid': args.pane_pid, 'launcher_identity': pane_identity, 'ancestry': ancestors,
            'state': 'observing', 'sampling_complete': False, 'cleanup_verified': False}
        require(artifacts.digest(yamlio.load(a3.REQUEST)) == a3.REQUEST_SHA256, 'a3 template changed')
        receipt['prerequisites']['a3'] = validate_a3({'path': str(args.a3_audit.absolute()), 'sha256': args.a3_sha256}, store, now())
        for kind in ('paired', 'provider'):
            receipt['prerequisites'][kind] = a3.validate_completion({'path': str(getattr(args, kind + '_completion').absolute()),
                'sha256': getattr(args, kind + '_sha256')}, kind, now())
        validate_source(store)
        stage([sys.executable, str(ROOT / 'scripts/dx100_capacity.py'), '--node', '0', '--output', str(folder / 'capacity.json')], 30, 'capacity')
        generation_deadline = min(deadline, time.monotonic() + 120)
        graph_output = stage([sys.executable, str(Path(graph_case.__file__)), '--output-directory', str(folder / 'graph'),
            '--records', str(ROOT / 'records'), '--lane', 'mbit10-evaluation-node0'], 120, 'generate', stage_deadline=generation_deadline)
        graph = json.loads(graph_output.read_text())
        require(graph['vertices'] == 8212 and graph['directed_arcs'] == 147492
                and graph['source'] == 0 and graph['author_bfs_source_sha256'] == graph_case.AUTHOR_SOURCE_SHA256,
                'generated graph differs from the fixed case')
        receipt['graph'] = graph
        workload = public('register-workload', registration_request(graph), 120, stage_deadline=generation_deadline)
        compiled = public('dx100-compile', compile_request(), 240)
        require_other_leases_idle()
        request = execution_request(compiled, workload, graph)
        result = public('dx100-execute', request, 3100)
        output = stage([sys.executable, '-m', 'swdb', 'get', request['id'], '--records', str(ROOT / 'records'), '--format', 'json'], 30, 'fresh-get')
        require(artifacts.digest(json.loads(output.read_text())) == artifacts.digest(result), 'fresh public evaluation differs')
        receipt['coverage'] = validate_coverage(result, request, graph)
        monitor.check()
        require(time.monotonic() <= deadline and now() <= DEADLINE, 'coverage finished outside its fixed window')
        receipt.update(state='complete', evaluation=result['id'], evaluation_sha256=artifacts.digest(result))
    except BaseException as exc:
        receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        try:
            monitor.stop()
            if monitor.last_observation_started is not None:
                monitor.check()
                if receipt['state'] == 'complete':
                    monitor._observe()
        except BaseException as exc:
            receipt.update(state='failed', resource_error=f'{type(exc).__name__}: {exc}')
        finalize_receipt(receipt, folder, started, deadline, observations, sampler.known)
    require(receipt['state'] == 'complete', receipt.get('resource_error', 'coverage failed'))
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    with interruption_signals():
        main()
