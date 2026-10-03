#!/usr/bin/env python3
"""Bounded tickets 28/29 driver for an operator-approved mbit10 socket lane.

Updated: 2026-10-03 ET. Stages are prepare, companion, timed. This command
does not dispatch remotely, run a provider, promote entries, copy raw output,
or edit historical protocols. Each failed attempt keeps its records and logs.
"""
import argparse
import copy
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from swdb import artifacts, bfs_protocol, dispatch_preflight, host_observation, library, profile_package, provider_guard, read_only_checks
from swdb.cli import Failure, _require_valid
from tools.typed_library_profile_driver import SOURCE, SOURCE_SHA256, checked_command, now, save, _cli, _request

T17 = 'bfs-t17-controlled-simulator-20260928.952dead4468b86d7'
FULL_SOURCE = 'bfs-dx100-compile-20260925-a1.source'
FULL_SOURCE_SHA256 = 'd5ac642dfe1a2ba5ef548f86c5c269ef54164b55985badc55872288f41504e9d'
CONTRACT = 'contract.bfs_read_offload'
COVERAGE = 'bfs-dx100-coverage-20260926-a2.workload.6b1e2f2dc16f6a0e'
HEADER = 'benchmarks/gapbs/src/swdb_dxc_lowering.hpp'
FORMAT = 'swdb.typed-library-gem5-driver.v1'
PREPARE_MEMORY_GIB = 4
# Match the retained T17 v2 post-seal ceiling for every execution role.
# Scale-18 baseline checks required 57/84 billion ticks; wall-time and
# memory budgets still bound this continuation independently of ROI timing.
VERIFICATION_MAX_TICKS = 10**14


def stage_budgets(args):
    """Serial source preparation/GCC is admitted independently of gem5 RAM."""
    return ((PREPARE_MEMORY_GIB, 4) if args.stage == 'prepare'
            else (args.memory_gib, args.storage_gib))


def need(value, reason):
    if not value:
        raise Failure(reason)


def get(store, rid, kind):
    value = store.get(rid, kind)
    need(value is not None, f'missing {kind} {rid}')
    return value


def reference(record):
    return {'id': record['id'], 'sha256': artifacts.digest(record)}


def current_library(store):
    """A passing old tree or stale content cannot admit this run."""
    lib = library.Library(library.default_root(store.dir), store)
    problems = lib.validate()
    need(not problems, 'typed library validation failed: ' + '; '.join(map(str, problems[:5])))
    contract = lib.get(CONTRACT)
    need(contract is not None, 'missing read-offload contract')
    sha = lib.content_sha256(CONTRACT)
    receipts = [row.data for row in store.of_kind('certification')
        if row.data.get('entry') == {'id': CONTRACT, 'content_sha256': sha}
        and lib.current_certification(row.data)
        and row.data.get('verdict') == 'certified'
        and row.data.get('evidence_kind') == 'execution'
        and row.data.get('candidate', {}).get('contract') == CONTRACT
        and row.data['candidate'].get('contract_sha256') == sha
        and row.data['candidate'].get('snapshot') == SOURCE
        and re.fullmatch(r'[0-9a-f]{64}', row.data['candidate'].get('tree_sha256', ''))
        and row.data.get('matrix') and all(cell.get('status') == 'passed' for cell in row.data['matrix'])
        and row.data.get('negative_controls') and all(cell.get('status') == 'rejected' for cell in row.data['negative_controls'])]
    need(receipts, 'requires a current passing certification of the exact scalar-only patched tree')
    pins = lib.dependency_pins(CONTRACT)
    for pin in [{'id': CONTRACT, 'content_sha256': sha}] + pins:
        state = lib.state(pin['id'])
        need(state['tier'] == 'shared' and state['status'] in {'certified', 'evaluated_on_target'},
             f"requires current shared certification for {pin['id']}: {state}")
    lowerings = [pin['id'] for pin in pins if lib.get(pin['id'])['kind'] == 'lowering']
    hashes = {lib.get(rid)['code_sha256'] for rid in lowerings}
    need(len(hashes) == 1, 'first patch requires one common certified lowering header')
    header_hash = hashes.pop()
    for rid in lowerings:
        need(artifacts.file_hash(lib.resolve(lib.get(rid)['location'])) == header_hash,
             'canonical lowering header differs from its current pin')
    section = {'contract': {'id': CONTRACT, 'content_sha256': sha}, 'entries': pins,
               'shipped_files': [{'path': HEADER, 'sha256': header_hash, 'lowerings': lowerings}]}
    return section, sorted(receipts, key=lambda row: (row.get('created_at', ''), row['id']))[-1]


def protocol_request(store, run_id, certified_tree_sha256):
    """Copy T17 v2 treatment into an independent version-one protocol."""
    old = get(store, T17, 'protocol')
    bfs_protocol.verify_immutable(old)
    need(old['version'] == 2, 'first evaluation must copy the pinned T17 version two')
    settings = copy.deepcopy(old['settings'])
    need(settings['mode'] == 'controlled_simulator' and settings['threads'] == 4
         and len(settings['workloads']) == 2 and settings['sampling']['repetitions'] == 1,
         'T17 workload/threads/replay policy changed')
    for wid in settings['workloads'] + [COVERAGE]:
        workload = get(store, wid, 'workload')
        bfs_protocol.verify_immutable(workload)
        need(workload['definition']['sources'] == [0], 'first evaluation requires source zero')
        bfs_protocol.workload_representation(store, wid, 'dx100-gapbs')
    # The treatment is copied; executable verifier source pins describe this
    # checkout, rather than pretending the changed parser is the old T17 file.
    runtime = {'driver_sha256': artifacts.file_hash(PROJECT/'scripts/dx100_verify.py'),
               'parser_sha256': artifacts.file_hash(PROJECT/'swdb/dx100_witness.py'),
               'observer_sha256': artifacts.file_hash(PROJECT/'scripts/dx100_host_memory.py')}
    for role in ('baseline', 'candidate'):
        settings['instrumentation'][role]['verifier_runtime'] = copy.deepcopy(runtime)
    evidence = settings['sampling']['determinism']['evidence']
    if isinstance(evidence, str):
        match = re.fullmatch(r'(\S+) sha256:([0-9a-f]{64})', evidence)
        need(match is not None, 'T17 deterministic replay evidence cannot be normalized')
        settings['sampling']['determinism']['evidence'] = {'path': match[1], 'sha256': match[2]}
    settings['correctness']['required_accelerator_cases'] = {
        'baseline': [], 'candidate': ['read_only_executed', 'full_tiles', 'tail_tiles']}
    settings['correctness']['companion_cases'] = {'parent_gather_race': {'workload': COVERAGE, 'source': 0}}
    settings['region_pairs'] = []
    settings['differences']['software'] = [
        'Fresh unchanged full-source dx100-bfs-scalar DOBFS versus Peter section 5 read offload '
        'applied to the certified scalar-only snapshot; CPU compare-and-swap and queue updates are retained.']
    settings['route'] = {'ticket': 28, 'baseline_candidate': run_id+'.baseline',
        'candidate': run_id+'.proposal.candidate-1', 'certified_tree_sha256': certified_tree_sha256,
        'builds': {'baseline_primary': run_id+'.baseline.primary.build',
                   'candidate_primary': run_id+'.candidate.primary.build',
                   'candidate_diagnostic': run_id+'.candidate.diagnostic.build'}}
    return {'message_version': '1.0', 'id': run_id+'.protocol', 'version': 1,
            'supersedes': None, 'settings': settings}


def lease_snapshot(lane):
    """Observe both socket locks and refuse a held legacy lock."""
    root = Path(os.environ.get('LACT_LEASE_ROOT', '/data1/yanruj/lact-host-lease'))
    rows = []
    for name in ('mbit10-evaluation-node0', 'mbit10-evaluation-node1', 'mbit10-evaluation'):
        path = root/(name+'.lease')
        row = {'name': name, 'path': str(path), 'held': False}
        if path.exists():
            need(path.is_file() and not path.is_symlink(), 'unsafe lease lock path')
            with path.open('r') as stream:
                try:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
                except BlockingIOError:
                    row['held'] = True
        meta = root/(name+'.meta.json')
        if meta.exists():
            need(meta.is_file() and not meta.is_symlink() and meta.stat().st_size <= 1024**2,
                 'lease metadata is not a bounded regular file')
            row['metadata'] = json.loads(meta.read_text())
            row['metadata_sha256'] = artifacts.file_hash(meta)
        rows.append(row)
    need(not rows[-1]['held'], 'legacy mbit10-evaluation lease is held; dispatch is refused')
    need(next(row for row in rows if row['name'] == lane.split(' ', 1)[0])['held'],
         'verified socket lease is no longer held')
    return rows


def public(args, folder, command, stage, request=None, *, lane=None, timeout=300,
           environment=None, extra=(), allow_failed_evaluation=False):
    verified = provider_guard._lane()
    need(lane is None or verified == lane, 'socket lane receipt changed during the driver')
    lease_snapshot(verified)
    argv = _cli(args, command)
    if request is not None:
        argv.append(str(_request(folder, stage, request)))
    argv.extend(map(str, extra))
    if command in {'dx100-compile', 'dx100-execute'}:
        argv += ['--runs-dir', str(args.runs_dir), '--lane', verified.split(' ', 1)[0][-1]]
    progress = {'stage': stage, 'command': command, 'started': now(), 'state': 'running',
                'request_id': request.get('id') if request else None, 'timeout_seconds': timeout,
                'lane': verified}
    save(folder/'progress.json', progress)
    result = None
    try:
        result = checked_command(argv, folder, stage, timeout=timeout, environment=environment)
        return result
    except Failure:
        # A failed public execution still contains the diagnostic L3 verdict.
        # Timeouts and malformed output never become a completed observation.
        output, command_receipt = folder/(stage+'.json'), folder/(stage+'.command.json')
        if allow_failed_evaluation and command_receipt.is_file():
            row = json.loads(command_receipt.read_text())
            if row.get('state') == 'failed' and output.is_file() and output.stat().st_size <= 64*1024**2:
                failed = json.loads(output.read_text())
                if failed.get('kind') == 'evaluation' and failed.get('request') == request:
                    result = failed
                    return failed
        raise
    finally:
        progress.update(state='complete' if result is not None else 'failed', finished=now())
        if result is not None:
            progress['record'] = reference(result)
            progress['outcome'] = result.get('outcome', result.get('decision'))
        save(folder/'progress.json', progress)


def prepare_stage(args, folder, lane, environment):
    store = _require_valid(args.records)
    section, certification = current_library(store)
    tree_sha256 = certification['candidate']['tree_sha256']
    source = get(store, SOURCE, 'source_snapshot')
    full = get(store, FULL_SOURCE, 'source_snapshot')
    need(source['artifact']['sha256'] == SOURCE_SHA256 and full['artifact']['sha256'] == FULL_SOURCE_SHA256,
         'scalar-only patch base or full-source baseline pin changed')
    scalar_root = artifacts.verify(source['artifact'])
    artifacts.verify(full['artifact'])
    need(not re.search(r'\b(?:TDStepMAA|DOBFSMAA)\s*\(',
                       (scalar_root/'benchmarks/gapbs/src/bfs.cc').read_text()),
         'candidate patch base still exposes the authors accelerated path')
    package = get(store, args.profile_package, 'profile_package')
    profile_package.verify(package)
    package_source = get(store, package.get('source_snapshot'), 'source_snapshot')
    package_candidate = get(store, package.get('candidate'), 'candidate')
    need(package_source['artifact']['sha256'] == SOURCE_SHA256
         and package_source['protections'] == source['protections']
         and package_candidate.get('source_snapshot') == SOURCE
         and package_candidate['artifact']['sha256'] == SOURCE_SHA256
         and package.get('implementation') == 'dx100-bfs-scalar'
         and package.get('completeness') == 'complete'
         and package.get('evidence', {}).get('classification') == 'execution',
         'prepare requires the real complete ticket 27 scalar-only profile package')
    regions = [row['id'] for row in package['regions']
               if row.get('kind') == 'function' and row.get('name') in {'TDStep', 'DOBFS'}]
    need(regions, 'profile package has no scalar TDStep/DOBFS region')
    patch = PROJECT/'library/dx100/peter-section5.patch'
    need(patch.is_file() and not patch.is_symlink() and patch.stat().st_size < 10*1024**2,
         'candidate patch must be a bounded regular file')
    request = protocol_request(store, args.id, tree_sha256)
    # Freeze precedes submit and all builds/executions; route names are planned
    # IDs, and actual tree/binary identities are retained in the stage receipt.
    frozen = public(args, folder, 'freeze-protocol', 'freeze', request, lane=lane, environment=environment)
    proposal = {'message_version': '1.1', 'id': args.id+'.proposal',
        'producer': {'name': args.authoring_session, 'role': 'worker', 'test_client': False},
        'profile_package': package['id'], 'source_snapshot': package_source['id'], 'implementation': 'dx100-bfs-scalar',
        'source_sha256': SOURCE_SHA256, 'regions': regions,
        'intent': 'Apply the certified Peter v1.1 section 5 read-offload patch, including per-thread lowering context, '
                  'continuation and CPU compare-and-swap/queue preservation; L3 and L5 remain assumptions.',
        'constraints': {'editable_files': ['benchmarks/gapbs/src/bfs.cc', HEADER],
                        'preserve_correctness': True, 'preserve_roi': True},
        'payload': {'kind': 'patch', 'content': patch.read_text()}, 'library': section}
    library.proposal_gate(proposal, store)
    submitted = public(args, folder, 'submit', 'submit', proposal, lane=lane,
                       environment=environment, extra=['--runs-dir', args.runs_dir])
    need(submitted['outcome']['state'] == 'candidate_created', 'certified patch submission did not create a candidate')
    store = _require_valid(args.records)
    candidate = get(store, submitted['candidate'], 'candidate')
    need(candidate['id'] == args.id+'.proposal.candidate-1' and candidate['artifact']['sha256'] == tree_sha256,
         'submitted candidate tree differs from certification')
    root = artifacts.verify(candidate['artifact'])
    need(sum(line.strip() == read_only_checks.FRONTIER_TEXT
             for line in (root/'benchmarks/gapbs/src/bfs.cc').read_text().splitlines()) == 1,
         'candidate frontier statement differs from exact queue-size print')
    baseline = public(args, folder, 'baseline-candidate', 'baseline', lane=lane, environment=environment,
                      extra=[FULL_SOURCE, '--id', args.id+'.baseline', '--runs-dir', args.runs_dir])
    bfs_protocol.validate_baseline_source(_require_valid(args.records), baseline)
    settings = frozen['settings']
    model = get(store, settings['simulation_identity']['model_build']['evaluation'], 'evaluation')
    need(model['evidence_kind'] == 'execution', 'real driver refuses fixture simulator models')
    builds = {}
    for name, selected, accelerated, diagnostic in (
            ('baseline.primary', baseline, False, False), ('candidate.primary', candidate, True, False),
            ('candidate.diagnostic', candidate, True, True)):
        compile_request = {'message_version': '1.0', 'id': args.id+'.'+name+'.build', 'machine': 'mbit10',
            'hardware_target': settings['targets']['candidate' if accelerated else 'baseline']['id'],
            'model_root': model['context']['model_root'], 'build_evaluation': model['id'],
            'candidate': selected['id'], 'function': 'DOBFS', 'accelerated': accelerated,
            'roi': settings['roi'], 'parent_gather_diagnostic': diagnostic,
            'budget': {'total_seconds': 600, 'build_seconds': 300,
                       'memory_gib': PREPARE_MEMORY_GIB, 'storage_gib': 1}}
        compiled = public(args, folder, 'dx100-compile', 'compile-'+name, compile_request,
                          lane=lane, timeout=660, environment=environment)
        need(compiled.get('evidence_kind') == 'execution' and compiled['outcome']['state'] == 'complete',
             'compiler did not produce real completed evidence')
        expected = settings['builds']['candidate' if accelerated else 'baseline']
        actual = copy.deepcopy(compiled['build'])
        if diagnostic:
            actual['flags'] = [flag for flag in actual['flags'] if flag != '-DSWDB_DXC_DIAGNOSTIC']
            need('-DSWDB_DXC_DIAGNOSTIC' in compiled['build']['flags'], 'diagnostic probe define missing')
        need(all(actual.get(key) == expected[key] for key in ('compiler', 'compiler_version', 'flags', 'adapter')),
             'guest compiler/build identity differs from the fresh frozen protocol')
        builds[name] = reference(compiled)
    return {'protocol': reference(frozen), 'candidate': reference(candidate), 'baseline': reference(baseline),
            'certification': reference(certification), 'profile_package': reference(package), 'builds': builds,
            'tree_sha256': tree_sha256, 'patch_sha256': artifacts.file_hash(patch), 'next_stage': 'companion', 'l3_outcome': 'not_run'}


def load_stage(args, stage):
    path = args.runs_dir/(args.id+'.driver-'+stage)/'driver.json'
    need(path.is_file() and not path.is_symlink() and path.stat().st_size <= 8*1024**2,
         f'{stage} stage receipt is unavailable')
    receipt = json.loads(path.read_text())
    need(receipt.get('format') == FORMAT and receipt.get('id') == args.id
         and receipt.get('stage') == stage and receipt.get('state') == 'complete',
         f'{stage} stage did not complete')
    return receipt['result']


def prepared_records(args):
    prepared = load_stage(args, 'prepare')
    store = _require_valid(args.records)
    _section, current_certification = current_library(store)
    tree_sha256 = current_certification['candidate']['tree_sha256']
    rows = {}
    for name, kind in (('protocol', 'protocol'), ('candidate', 'candidate'), ('baseline', 'candidate'),
                       ('profile_package', 'profile_package'), ('certification', 'certification')):
        pin = prepared[name]
        rows[name] = get(store, pin['id'], kind)
        need(reference(rows[name]) == pin, f'prepared {name} identity changed')
    need(rows['candidate']['artifact']['sha256'] == prepared['tree_sha256'] == tree_sha256,
         'prepared candidate differs from certified tree')
    artifacts.verify(rows['candidate']['artifact'])
    bfs_protocol.validate_baseline_source(store, rows['baseline'])
    protocol = rows['protocol']
    bfs_protocol.verify_immutable(protocol)
    need(protocol['requested_id'] == args.id+'.protocol' and protocol['version'] == 1
         and protocol['supersedes'] is None and not protocol['settings']['region_pairs'],
         'prepared protocol is not the independent first-evaluation freeze')
    need(protocol['settings'] == protocol_request(store, args.id, tree_sha256)['settings'],
         'checkout or first-evaluation policy changed after prepare; use a fresh run ID')
    for name, pin in prepared['builds'].items():
        row = get(store, pin['id'], 'evaluation')
        need(reference(row) == pin and row['outcome']['state'] == 'complete'
             and row['evidence_kind'] == 'execution', 'prepared build is incomplete, changed or fixture evidence')
        binary = row['build']
        path = Path(binary['binary'])
        need(path.is_file() and not path.is_symlink() and artifacts.file_hash(path) == binary['binary_sha256'],
             'prepared binary bytes are unavailable or changed')
        rows[name] = row
    return store, rows


def execution_request(args, store, rows, role, workload_id, label, *, companion=False, diagnostic=False):
    protocol = rows['protocol']
    settings = protocol['settings']
    model = get(store, settings['simulation_identity']['model_build']['evaluation'], 'evaluation')
    candidate = rows['baseline' if role == 'baseline' else 'candidate']
    compiled = rows[role+('.diagnostic' if diagnostic else '.primary')]
    representation = bfs_protocol.workload_representation(store, workload_id, 'dx100-gapbs')['representation']
    configuration = settings['targets'][role]['configuration']
    request = {'message_version': '1.0', 'id': args.id+'.'+label+'.evaluation', 'machine': 'mbit10',
        'hardware_target': settings['targets'][role]['id'], 'model_root': model['context']['model_root'],
        'build_evaluation': model['id'], 'simulator': copy.deepcopy(settings['simulation_identity']['simulator']),
        'candidate': candidate['id'], 'candidate_build': compiled['id'],
        'binary': {'path': compiled['build']['binary'], 'sha256': compiled['build']['binary_sha256']},
        'workload': {'id': workload_id, 'source': 0,
                     'representation': {key: representation[key] for key in ('path', 'sha256')}},
        'protocol': protocol['id'], 'protocol_role': role,
        'protocol_trial': {'source_position': 0, 'repetition': 0},
        'configuration': {key: configuration[key] for key in ('mode', 'l3_size_mb', 'l3_assoc', 'tile_elements')},
        'verification': {'checker': 'dx100.bfs.verifier.v2', 'max_ticks': VERIFICATION_MAX_TICKS,
                         'coverage': role == 'candidate', 'post_roi_trace': 'SyscallBase',
                         'trace_transport': 'gem5-gzip.v1', 'read_only': role == 'candidate'},
        'budget': {'total_seconds': 3600 if companion else 9000,
                   'checkpoint_seconds': 600 if companion else 1800,
                   'run_seconds': 2940 if companion else 7140,
                   'memory_gib': args.memory_gib, 'storage_gib': args.storage_gib}}
    if companion:
        request['protocol_companion'] = 'parent_gather_race'
    need(not diagnostic or companion, 'diagnostic binary cannot be a timed sample')
    return request


def companion_stage(args, folder, lane, environment):
    store, rows = prepared_records(args)
    executions = {}
    for name in ('timed', 'diagnostic'):
        request = execution_request(args, store, rows, 'candidate', COVERAGE, 'companion.'+name,
                                    companion=True, diagnostic=name == 'diagnostic')
        observed = public(args, folder, 'dx100-execute', 'companion-'+name, request, lane=lane,
                          timeout=request['budget']['total_seconds']+60, environment=environment,
                          allow_failed_evaluation=True)
        executions[name] = observed
    diagnostic = executions['diagnostic']
    checks = diagnostic.get('correctness', {}).get('checks', [])
    l3 = checks[0].get('parent_gather_race', {}).get('outcome', 'inconclusive') if len(checks) == 1 else 'inconclusive'
    if l3 == 'observed':
        try:
            store = _require_valid(args.records)
            accepted = read_only_checks.companion_acceptance(store, rows['protocol'],
                {'companion_evaluations': {name: run['id'] for name, run in executions.items()}}, executions['timed'])
            need(executions['timed']['correctness']['checks'][0]['coverage']['read_only_executed']['state'] == 'observed',
                 'primary companion did not execute the read-offload instruction mix')
        except (Failure, KeyError) as error:
            l3, accepted = 'inconclusive', {'reason': str(error)}
    else:
        accepted = None
    result = {'protocol': reference(rows['protocol']), 'companion_evaluations': {
        name: reference(run) for name, run in executions.items()}, 'l3_outcome': l3,
        'acceptance': accepted, 'timed_admitted': l3 == 'observed',
        'next_stage': 'timed' if l3 == 'observed' else 'triage-fallback-ticket31' if l3 == 'refuted' else 'diagnose'}
    save(folder/'companion-outcome.json', result)
    return result


def timed_stage(args, folder, lane, environment):
    store, rows = prepared_records(args)
    previous = load_stage(args, 'companion')
    need(previous.get('l3_outcome') == 'observed' and previous.get('timed_admitted') is True,
         'timed runs wait for an observed L3 companion outcome')
    companions = {}
    for name, pin in previous['companion_evaluations'].items():
        observed = get(store, pin['id'], 'evaluation')
        need(reference(observed) == pin, 'companion record changed after its outcome was recorded')
        companions[name] = observed['id']
    accepted = read_only_checks.companion_acceptance(store, rows['protocol'],
        {'companion_evaluations': companions}, get(store, companions['timed'], 'evaluation'))
    need(accepted == previous['acceptance'], 'companion acceptance changed after its stage')
    results = []
    for index, wid in enumerate(rows['protocol']['settings']['workloads']):
        aggregates, samples = {}, {}
        for role in ('baseline', 'candidate'):
            label = f'timed.w{index}.{role}'
            request = execution_request(args, store, rows, role, wid, label)
            observed = public(args, folder, 'dx100-execute', label, request, lane=lane,
                              timeout=request['budget']['total_seconds']+60, environment=environment,
                              allow_failed_evaluation=True)
            need(observed['outcome']['state'] == 'complete' and observed['correctness']['state'] == 'passed',
                 f'{label} failed its verifier; retained evaluation {observed["id"]}')
            if role == 'candidate':
                coverage = observed['correctness']['checks'][0]['coverage']
                need(coverage.get('read_only_executed', {}).get('state') == 'observed'
                     and all(coverage.get(case, {}).get('state') == 'observed' for case in ('full_tiles', 'tail_tiles')),
                     f'{label} did not exercise the frozen read-only/full/tail cases')
            samples[role] = reference(observed)
            aggregate_request = {'message_version': '1.0', 'id': args.id+'.'+label+'.aggregate',
                'protocol': rows['protocol']['id'], 'protocol_role': role, 'evaluations': [observed['id']]}
            aggregate = public(args, folder, 'aggregate-evaluations', label+'-aggregate', aggregate_request,
                               lane=lane, environment=environment)
            need(aggregate['outcome']['state'] == 'complete', 'exact one-replay aggregate failed')
            aggregates[role] = aggregate
        compare_request = {'message_version': '1.0', 'id': args.id+f'.w{index}.comparison',
            'protocol': rows['protocol']['id'], 'comparison_baseline': 'dx100-bfs-scalar',
            'baseline_evaluation': aggregates['baseline']['id'], 'candidate_evaluation': aggregates['candidate']['id'],
            'companion_evaluations': companions}
        compared = public(args, folder, 'compare-evaluations', f'w{index}-comparison', compare_request,
                          lane=lane, environment=environment)
        need(compared['decision']['state'] != 'rejected', 'comparison rejected the retained evidence')
        results.append({'workload': wid, 'executions': samples,
            'aggregates': {role: reference(value) for role, value in aggregates.items()},
            'comparison': reference(compared), 'decision': compared['decision']['state'],
            'point_ratio': compared['metrics']['roi_speedup'], 'basis': 'simulated',
            'scope': 'single graph per class, one source, deterministic one-replay point ratio'})
    store = _require_valid(args.records)
    lib = library.Library(library.default_root(store.dir), store)
    states = {pin['id']: lib.state(pin['id']) for pin in
              [get(store, rows['candidate']['proposal'], 'proposal')['request']['library']['contract']] +
              get(store, rows['candidate']['proposal'], 'proposal')['request']['library']['entries']}
    summary = folder/'first-result.md'
    lines = ['# First Peter v1.1 gem5 result', '', 'Updated: 2026-10-03 ET.', '',
        f'Protocol: `{rows["protocol"]["id"]}`. Certified tree: `{rows["candidate"]["artifact"]["sha256"]}`. '
        'L3 was observed for this diagnostic run; the design still assumes L3 and L5.', '',
        '| Workload | Baseline verifier | Candidate verifier / read-only | Point ratio | Decision | Basis |',
        '| --- | --- | --- | ---: | --- | --- |']
    lines += [f'| {row["workload"]} | passed | passed / observed | {row["point_ratio"]:.6g} | '
              f'{row["decision"]} | simulated |' for row in results]
    lines += ['', 'Each row is one registered graph, source 0, and one deterministic replay. '
        'Ratios use fresh full-source scalar versus certified read-offload executions under this freeze. '
        'These are point ratios; no statistical confidence across graphs is claimed. '
        'Setup is included in the complete-call ROI. No region attribution was collected.', '',
        f'Authors\' accelerated T17 protocol `{T17}` is context only; its numbers are not mixed into these ratios.', '',
        'Operator draft for Yan-Ru to review and send. Raw output remains on mbit10; '
        'evaluations, aggregates, comparisons and custody records are authoritative.']
    summary.write_text('\n'.join(lines)+'\n')
    return {'protocol': reference(rows['protocol']), 'l3_outcome': 'observed', 'workloads': results,
            'library_states': states, 'summary': {'path': str(summary), 'sha256': artifacts.file_hash(summary)}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('prepare', 'companion', 'timed'), required=True)
    parser.add_argument('--id', required=True)
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--records', type=Path, default=PROJECT/'records')
    parser.add_argument('--profile-package', help='real complete ticket 27 package; required by prepare')
    parser.add_argument('--authoring-session', default='codex-typed-library-dx100-bfs-20261003')
    parser.add_argument('--approval-reference', required=True)
    parser.add_argument('--memory-gib', type=int, choices=range(32, 55), default=48)
    parser.add_argument('--storage-gib', type=int, choices=range(4, 33), default=8)
    args = parser.parse_args(argv)
    need(socket.gethostname().split('.')[0] == 'mbit10', 'real gem5 driver requires mbit10')
    need(re.fullmatch(r'[a-z0-9][a-z0-9._-]*', args.id), 'driver ID must use record identifier syntax')
    need(args.approval_reference.strip(), 'an explicit operator approval reference is required')
    need(args.stage != 'prepare' or args.profile_package, 'prepare requires --profile-package from ticket 27')
    lane = provider_guard._lane()
    args.runs_dir = args.runs_dir.resolve()
    args.records = args.records.resolve()
    need(args.records.is_relative_to('/data1/yanruj'), 'record checkout requires mbit10 /data1/yanruj storage')
    need(any(args.runs_dir.is_relative_to(base) for base in (dispatch_preflight.PRIMARY, dispatch_preflight.SECONDARY)),
         'raw output requires one of the two approved EvolveSWDB run roots')
    need(not args.runs_dir.is_relative_to(PROJECT), 'raw output cannot be inside the checkout')
    folder = artifacts.external_directory(args.runs_dir)/(args.id+'.driver-'+args.stage)
    folder.mkdir(exist_ok=False)
    receipt = {'format': FORMAT, 'id': args.id, 'stage': args.stage, 'state': 'running', 'started': now(),
        'approval_reference': args.approval_reference, 'authoring_session': args.authoring_session,
        'host': socket.gethostname(), 'lane': lane, 'basis': 'simulated', 'gain_claim': False,
        'memory_gib': args.memory_gib, 'storage_gib': args.storage_gib, 'driver_sha256': artifacts.file_hash(__file__)}
    receipt_path = folder/'driver.json'
    save(receipt_path, receipt)
    def interrupted(signum, frame):
        raise InterruptedError('driver interrupted by signal '+str(signum))
    previous = {signum: signal.signal(signum, interrupted) for signum in (signal.SIGINT, signal.SIGTERM)}
    try:
        receipt['leases'] = lease_snapshot(lane)
        receipt['host_observation'] = host_observation.capture(folder, PROJECT)
        receipt['runtime_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=PROJECT,
                                                          text=True, timeout=30).strip()
        receipt['runtime_branch'] = subprocess.check_output(['git', 'branch', '--show-current'], cwd=PROJECT,
                                                          text=True, timeout=30).strip()
        receipt['tracked_changes'] = subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'],
                                                            cwd=PROJECT, text=True, timeout=30).splitlines()
        need(receipt['runtime_branch'] == 'yanrujhou_main', 'driver requires the approved yanrujhou_main branch')
        memory_gib, storage_gib = stage_budgets(args)
        receipt['preflight'] = dispatch_preflight.check(args.runs_dir, lane,
            storage_bytes=storage_gib*dispatch_preflight.GIB,
            memory_bytes=memory_gib*dispatch_preflight.GIB)
        save(receipt_path, receipt)
        temporary = folder/'tmp'; temporary.mkdir()
        environment = {**os.environ, 'TMPDIR': str(temporary), 'MAKEFLAGS': '-j1', 'CMAKE_BUILD_PARALLEL_LEVEL': '1',
                       'OMP_THREAD_LIMIT': '4', 'OMP_WAIT_POLICY': 'PASSIVE', 'GOMP_SPINCOUNT': '0'}
        environment.pop('GOMP_CPU_AFFINITY', None)
        stages = {'prepare': prepare_stage, 'companion': companion_stage, 'timed': timed_stage}
        receipt['result'] = stages[args.stage](args, folder, lane, environment)
        receipt.update(state='complete', finished=now())
    except BaseException as error:
        receipt.update(state='failed', finished=now(), reason=str(error))
        raise
    finally:
        save(receipt_path, receipt)
        for signum, handler in previous.items():
            signal.signal(signum, handler)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (Failure, OSError, ValueError, KeyError, InterruptedError, provider_guard.GuardError) as error:
        print('typed-library-gem5-driver: '+str(error), file=sys.stderr)
        raise SystemExit(1)
