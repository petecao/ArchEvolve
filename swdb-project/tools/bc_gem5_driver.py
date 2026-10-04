#!/usr/bin/env python3
"""Ticket 45 driver: one small BC gem5 run that reuses the derived contract.

Created: 2026-10-03 ET. Updated: 2026-10-04 ET (--attempt for a fresh timed attempt). Runs on mbit10 inside one verified socket lane, through
public SWDB commands only. Stage ``prepare`` registers the BC workload on an
existing BFS graph (source 0), retains the full-source scalar BC baseline and a
labeled contract-fixture package for the scalar-only snapshot, freezes an
independent version-one protocol copied from the BFS a2 treatment, submits the
certified BC forward-pass patch (its tree must equal the certification's) and
compiles both guest binaries. Stage ``timed`` runs the scalar baseline and the
candidate once each with the BC v2 completion witness; the candidate must also
pass the read-only execution case. It then forms one-replay aggregates and the
comparison (a simulated point ratio for one graph and one source).

Shared mechanics (lease checks, bounded public commands, receipts) come from
``tools/typed_library_gem5_driver.py``. No provider runs, nothing is promoted,
no raw output is copied. Each failed attempt keeps its records and logs.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys

PROJECT = Path(os.environ.get('SWDB_PROJECT', Path(__file__).resolve().parents[1])).resolve()
sys.path.insert(0, str(PROJECT))

from swdb import artifacts, dispatch_preflight, host_observation, kernels, library, provider_guard  # noqa: E402
from swdb.cli import Failure, _require_valid  # noqa: E402
from tools.typed_library_profile_driver import now, save  # noqa: E402
from tools.typed_library_gem5_driver import (POSTPROCESS_TIMEOUT_SECONDS, VERIFICATION_MAX_TICKS,  # noqa: E402
                                             get, lease_snapshot, need, public, reference)

FORMAT = 'swdb.bc-gem5-driver.v1'
BFS_PROTOCOL = 'typed-library-bfs-gem5-20261003-a2.protocol.84229924369fc6b0'
CONTRACT = 'contract.bc_read_offload'
SNAPSHOT = 'bc-dx100-scalar-only-20261003-a1.source'
SNAPSHOT_SHA256 = '946d5398e3354c014ebe3309c2627951a5cf43d166bbb7c726adefb330a2d123'
IMPLEMENTATION = 'dx100-bc-scalar'
FROM_WORKLOAD = 'bfs-20260925-kronecker14.d03827828666f7dd'
HEADER = 'benchmarks/gapbs/src/swdb_dxc_lowering.hpp'
PATCH = 'library/dx100/bc-forward-pass.patch'
PREPARE_MEMORY_GIB = 4
BC = kernels.get('gapbs-bc')


def current_library(store):
    """Library section and newest passing certification of the exact BC patched tree."""
    lib = library.Library(library.default_root(store.dir), store)
    problems = lib.validate()
    need(not problems, 'typed library validation failed: ' + '; '.join(map(str, problems[:5])))
    sha = lib.content_sha256(CONTRACT)
    receipts = [row.data for row in store.of_kind('certification')
                if row.data.get('entry') == {'id': CONTRACT, 'content_sha256': sha}
                and lib.current_certification(row.data)
                and row.data.get('verdict') == 'certified' and row.data.get('evidence_kind') == 'execution'
                and row.data.get('candidate', {}).get('contract_sha256') == sha
                and row.data['candidate'].get('snapshot') == SNAPSHOT
                and re.fullmatch(r'[0-9a-f]{64}', row.data['candidate'].get('tree_sha256', ''))
                and row.data.get('matrix') and all(c.get('status') == 'passed' for c in row.data['matrix'])
                and row.data.get('negative_controls')
                and all(c.get('status') == 'rejected' for c in row.data['negative_controls'])]
    need(receipts, 'requires a current passing certification of the exact BC patched tree')
    pins = lib.dependency_pins(CONTRACT)
    for pin in [{'id': CONTRACT, 'content_sha256': sha}] + pins:
        state = lib.state(pin['id'])
        need(state['tier'] == 'shared' and state['status'] in {'certified', 'evaluated_on_target'},
             f"requires current shared certification for {pin['id']}: {state}")
    lowerings = [pin['id'] for pin in pins if lib.get(pin['id'])['kind'] == 'lowering']
    hashes = {lib.get(rid)['code_sha256'] for rid in lowerings}
    need(len(hashes) == 1, 'patch requires one common certified lowering header')
    section = {'contract': {'id': CONTRACT, 'content_sha256': sha}, 'entries': pins,
               'shipped_files': [{'path': HEADER, 'sha256': hashes.pop(), 'lowerings': lowerings}]}
    return section, sorted(receipts, key=lambda row: (row.get('created_at', ''), row['id']))[-1]


def runtime_pins():
    driver, observer, parser = BC.gem5_verification_runtime
    return {'driver_sha256': artifacts.file_hash(PROJECT/driver),
            'parser_sha256': artifacts.file_hash(PROJECT/parser),
            'observer_sha256': artifacts.file_hash(PROJECT/observer)}


def protocol_request(store, run_id, workload_id, tree_sha256):
    """Copy the BFS a2 simulator treatment; only kernel-bound fields change."""
    old = get(store, BFS_PROTOCOL, 'protocol')
    settings = copy.deepcopy(old['settings'])
    settings['kernel'] = BC.kernel
    settings['workloads'] = [workload_id]
    settings['roi'] = BC.gem5_roi
    graph = BC.graph_verification_contract('dx100-gapbs')
    for role in ('baseline', 'candidate'):
        treatment = settings['instrumentation'][role]
        treatment['roi'] = BC.gem5_roi
        treatment['verifier_runtime'] = runtime_pins()
        treatment['graph_verification'] = dict(graph)
    settings['correctness']['verifier'] = BC.gem5_witness_checker
    settings['correctness'].pop('companion_cases', None)
    settings['region_pairs'] = []
    settings['differences']['software'] = [
        'Fresh unchanged full-source dx100-bc-scalar Brandes versus the derived BC forward-pass read offload '
        '(contract.bc_read_offload) applied to the certified scalar-only BC snapshot; the CPU keeps the '
        'compare-and-swap, queue push, successor bit and path-count update; the dependency pass stays scalar.']
    settings['calibration'] = {
        'size_selection': ('Kronecker scale 14 (edge factor 16, 16,381 vertices, 425,860 directed edges), source 0, '
                           'the registered BFS graph bytes: one small run to show contract reuse on the target. '
                           'Scale 14 is a certified matrix size of the BC contract and its forward-pass levels '
                           'exceed the 16,384-element tile, so full and tail tiles can occur. Simulator RSS is '
                           'about 32 GiB for every BFS graph size (16 GB guest), so the 36 GiB budget is unchanged.'),
        'determinism_basis': 'The deterministic-replay evidence is the simulator\'s (T16 R11); it is reused, not re-measured for BC.',
        'change_rule': old['settings']['calibration']['change_rule'],
        'quantities': old['settings']['calibration']['quantities'],
        'copied_from': BFS_PROTOCOL}
    settings['route'] = {'ticket': 45, 'baseline_candidate': run_id+'.baseline',
                         'candidate': run_id+'.proposal.candidate-1', 'certified_tree_sha256': tree_sha256,
                         'builds': {'baseline_primary': run_id+'.baseline.primary.build',
                                    'candidate_primary': run_id+'.candidate.primary.build'}}
    return {'message_version': '1.0', 'id': run_id+'.protocol', 'version': 1, 'supersedes': None,
            'settings': settings}


def prepare_stage(args, folder, lane, environment):
    store = _require_valid(args.records)
    section, certification = current_library(store)
    tree_sha256 = certification['candidate']['tree_sha256']
    source = get(store, SNAPSHOT, 'source_snapshot')
    need(source['artifact']['sha256'] == SNAPSHOT_SHA256, 'scalar-only BC snapshot pin changed')
    artifacts.verify(source['artifact'])
    # 1. BC workload on the registered BFS Kronecker 14 graph, source 0 only.
    from scripts.register_bc_workloads import build_request
    request = build_request(store, FROM_WORKLOAD, args.id.rsplit('-', 1)[0]+'-kronecker14-s0', sources=[0])
    workload = public(args, folder, 'register-workload', 'workload', request, lane=lane, environment=environment)
    workload_id = workload['id']
    # 2. Full-source scalar baseline (the BFS precedent) and a labeled fixture package.
    full = public(args, folder, 'source-snapshot', 'full-source', lane=lane, environment=environment,
                  extra=[IMPLEMENTATION, '--id', args.id+'.full.source', '--runs-dir', args.runs_dir])
    baseline = public(args, folder, 'baseline-candidate', 'baseline', lane=lane, environment=environment,
                      extra=[full['id'], '--id', args.id+'.baseline', '--runs-dir', args.runs_dir])
    package = public(args, folder, 'fixture-package', 'fixture-package', lane=lane, environment=environment,
                     extra=[SNAPSHOT, '--id', args.id+'.contract-fixture-package'])
    # 3. Freeze before submit, builds and executions.
    store = _require_valid(args.records)
    frozen = public(args, folder, 'freeze-protocol', 'freeze',
                    protocol_request(store, args.id, workload_id, tree_sha256), lane=lane, environment=environment)
    # 4. Submit the certified patch; its tree must equal the certification's.
    patch = PROJECT/PATCH
    need(patch.is_file() and not patch.is_symlink() and patch.stat().st_size < 10*1024**2, 'patch must be a bounded file')
    regions = [row['id'] for row in package['regions'] if row.get('path') == BC.source_paths['dx100-gapbs']]
    need(regions, 'fixture package has no bc.cc region')
    proposal = {'message_version': '1.1', 'id': args.id+'.proposal',
        'producer': {'name': args.authoring_session, 'role': 'worker', 'test_client': False},
        'profile_package': package['id'], 'source_snapshot': SNAPSHOT, 'implementation': IMPLEMENTATION,
        'source_sha256': SNAPSHOT_SHA256, 'regions': regions,
        'intent': 'Apply the certified derived BC forward-pass read offload (contract.bc_read_offload, BC-L1 '
                  'included); the package is an explicit contract fixture: no profile drove this choice.',
        'constraints': {'editable_files': [BC.source_paths['dx100-gapbs'], HEADER],
                        'preserve_correctness': True, 'preserve_roi': True},
        'payload': {'kind': 'patch', 'content': patch.read_text()}, 'library': section}
    library.proposal_gate(proposal, store)
    submitted = public(args, folder, 'submit', 'submit', proposal, lane=lane, environment=environment,
                       extra=['--runs-dir', args.runs_dir])
    need(submitted['outcome']['state'] == 'candidate_created', 'certified patch submission did not create a candidate')
    store = _require_valid(args.records)
    candidate = get(store, submitted['candidate'], 'candidate')
    need(candidate['artifact']['sha256'] == tree_sha256, 'submitted candidate tree differs from certification')
    root = artifacts.verify(candidate['artifact'])
    need(sum(line.strip() == BC.frontier_text for line in
             (root/BC.source_paths['dx100-gapbs']).read_text().splitlines()) == 1,
         'candidate frontier statement differs from exact queue-size print')
    # 5. Guest builds.
    settings = frozen['settings']
    model = get(store, settings['simulation_identity']['model_build']['evaluation'], 'evaluation')
    need(model['evidence_kind'] == 'execution', 'real driver refuses fixture simulator models')
    builds = {}
    for name, selected, accelerated in (('baseline.primary', baseline, False), ('candidate.primary', candidate, True)):
        compiled = public(args, folder, 'dx100-compile', 'compile-'+name, {
            'message_version': '1.0', 'id': args.id+'.'+name+'.build', 'machine': 'mbit10',
            'hardware_target': settings['targets']['candidate' if accelerated else 'baseline']['id'],
            'model_root': model['context']['model_root'], 'build_evaluation': model['id'],
            'candidate': selected['id'], 'function': 'Brandes', 'accelerated': accelerated, 'roi': settings['roi'],
            'budget': {'total_seconds': 600, 'build_seconds': 300, 'memory_gib': PREPARE_MEMORY_GIB, 'storage_gib': 1}},
            lane=lane, timeout=660, environment=environment)
        need(compiled.get('evidence_kind') == 'execution' and compiled['outcome']['state'] == 'complete',
             'compiler did not produce real completed evidence')
        expected = settings['builds']['candidate' if accelerated else 'baseline']
        need(all(compiled['build'].get(key) == expected[key] for key in ('compiler', 'compiler_version', 'flags', 'adapter')),
             'guest compiler/build identity differs from the frozen protocol')
        builds[name] = reference(compiled)
    return {'workload': reference(workload), 'full_source': reference(full), 'baseline': reference(baseline),
            'package': reference(package), 'protocol': reference(frozen), 'proposal': reference(submitted),
            'candidate': reference(candidate), 'certification': reference(certification), 'builds': builds,
            'tree_sha256': tree_sha256, 'patch_sha256': artifacts.file_hash(patch), 'next_stage': 'timed'}


def load_prepare(args):
    path = args.runs_dir/(args.id+'.driver-prepare')/'driver.json'
    need(path.is_file() and not path.is_symlink(), 'prepare stage receipt is unavailable')
    receipt = json.loads(path.read_text())
    need(receipt.get('format') == FORMAT and receipt.get('id') == args.id and receipt.get('state') == 'complete',
         'prepare stage did not complete')
    return receipt['result']


def timed_stage(args, folder, lane, environment):
    prepared = load_prepare(args)
    store = _require_valid(args.records)
    rows = {}
    for name, kind in (('protocol', 'protocol'), ('candidate', 'candidate'), ('baseline', 'candidate'),
                       ('workload', 'workload')):
        rows[name] = get(store, prepared[name]['id'], kind)
        need(reference(rows[name]) == prepared[name], f'prepared {name} identity changed')
    for name, pin in prepared['builds'].items():
        row = get(store, pin['id'], 'evaluation')
        need(reference(row) == pin and row['outcome']['state'] == 'complete', 'prepared build changed')
        need(artifacts.file_hash(Path(row['build']['binary'])) == row['build']['binary_sha256'],
             'prepared binary bytes changed')
        rows[name] = row
    settings = rows['protocol']['settings']
    model = get(store, settings['simulation_identity']['model_build']['evaluation'], 'evaluation')
    from swdb import bfs_protocol
    wid = rows['workload']['id']
    representation = bfs_protocol.workload_representation(store, wid, 'dx100-gapbs')['representation']
    executions, aggregates = {}, {}
    label = 'timed' + ('-'+args.attempt if args.attempt else '')
    for role in ('baseline', 'candidate'):
        compiled = rows[role+'.primary']
        configuration = settings['targets'][role]['configuration']
        request = {'message_version': '1.0', 'id': args.id+'.'+label+'.'+role+'.evaluation', 'machine': 'mbit10',
            'hardware_target': settings['targets'][role]['id'], 'model_root': model['context']['model_root'],
            'build_evaluation': model['id'], 'simulator': copy.deepcopy(settings['simulation_identity']['simulator']),
            'candidate': rows[role]['id'], 'candidate_build': compiled['id'],
            'binary': {'path': compiled['build']['binary'], 'sha256': compiled['build']['binary_sha256']},
            'workload': {'id': wid, 'source': 0, 'representation': {k: representation[k] for k in ('path', 'sha256')}},
            'protocol': rows['protocol']['id'], 'protocol_role': role,
            'protocol_trial': {'source_position': 0, 'repetition': 0},
            'configuration': {k: configuration[k] for k in ('mode', 'l3_size_mb', 'l3_assoc', 'tile_elements')},
            'verification': {'checker': BC.gem5_witness_checker, 'max_ticks': VERIFICATION_MAX_TICKS,
                             'coverage': role == 'candidate', 'post_roi_trace': 'SyscallBase',
                             'trace_transport': 'gem5-gzip.v1', 'read_only': role == 'candidate'},
            'budget': {'total_seconds': 9000, 'checkpoint_seconds': 1800, 'run_seconds': 7140,
                       'memory_gib': args.memory_gib, 'storage_gib': args.storage_gib}}
        observed = public(args, folder, 'dx100-execute', label+'.'+role, request, lane=lane,
                          timeout=request['budget']['total_seconds']+60, environment=environment,
                          allow_failed_evaluation=True)
        executions[role] = observed
        need(observed['outcome']['state'] == 'complete' and observed['correctness']['state'] == 'passed',
             f'{role} failed its verifier; retained evaluation {observed["id"]}')
        if role == 'candidate':
            coverage = observed['correctness']['checks'][0]['coverage']
            need(coverage.get('read_only_executed', {}).get('state') == 'observed'
                 and all(coverage.get(case, {}).get('state') == 'observed' for case in ('full_tiles', 'tail_tiles')),
                 'candidate did not exercise the frozen read-only/full/tail cases')
        aggregates[role] = public(args, folder, 'aggregate-evaluations', label+'.'+role+'-aggregate', {
            'message_version': '1.0', 'id': args.id+'.'+label+'.'+role+'.aggregate', 'protocol': rows['protocol']['id'],
            'protocol_role': role, 'evaluations': [observed['id']]},
            lane=lane, timeout=POSTPROCESS_TIMEOUT_SECONDS, environment=environment)
        need(aggregates[role]['outcome']['state'] == 'complete', 'exact one-replay aggregate failed')
    compared = public(args, folder, 'compare-evaluations', 'comparison', {
        'message_version': '1.0', 'id': args.id+'.'+label+'.comparison', 'protocol': rows['protocol']['id'],
        'comparison_baseline': IMPLEMENTATION, 'baseline_evaluation': aggregates['baseline']['id'],
        'candidate_evaluation': aggregates['candidate']['id']},
        lane=lane, timeout=POSTPROCESS_TIMEOUT_SECONDS, environment=environment)
    return {'protocol': reference(rows['protocol']), 'workload': wid,
            'executions': {role: reference(row) for role, row in executions.items()},
            'aggregates': {role: reference(row) for role, row in aggregates.items()},
            'comparison': reference(compared), 'decision': compared.get('decision', {}).get('state'),
            'point_ratio': compared.get('metrics', {}).get('roi_speedup'), 'basis': 'simulated',
            'scope': 'simulated point ratio: one graph (Kronecker 14), source 0, one deterministic replay'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('prepare', 'timed'), required=True)
    parser.add_argument('--id', required=True)
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--records', type=Path, default=PROJECT/'records')
    parser.add_argument('--authoring-session', default='claude-bc-track-20261003')
    parser.add_argument('--approval-reference', required=True)
    parser.add_argument('--attempt', help='fresh timed attempt label after a retained failed attempt')
    parser.add_argument('--memory-gib', type=int, choices=range(32, 55), default=36)
    parser.add_argument('--storage-gib', type=int, choices=range(4, 33), default=8)
    args = parser.parse_args(argv)
    need(socket.gethostname().split('.')[0] == 'mbit10', 'real gem5 driver requires mbit10')
    need(re.fullmatch(r'[a-z0-9][a-z0-9._-]*', args.id), 'driver ID must use record identifier syntax')
    need(not args.attempt or (args.stage == 'timed' and re.fullmatch(r'[a-z0-9]+', args.attempt)),
         'an attempt label applies to the timed stage only')
    need(args.approval_reference.strip(), 'an explicit operator approval reference is required')
    lane = provider_guard._lane()
    args.runs_dir, args.records = args.runs_dir.resolve(), args.records.resolve()
    need(args.records.is_relative_to('/data1/yanruj'), 'record checkout requires mbit10 /data1/yanruj storage')
    need(any(args.runs_dir.is_relative_to(base) for base in (dispatch_preflight.PRIMARY, dispatch_preflight.SECONDARY)),
         'raw output requires one of the two approved EvolveSWDB run roots')
    folder = artifacts.external_directory(args.runs_dir)/(args.id+'.driver-'+args.stage+('-'+args.attempt if args.attempt else ''))
    folder.mkdir(exist_ok=False)
    receipt = {'format': FORMAT, 'id': args.id, 'stage': args.stage, 'state': 'running', 'started': now(),
               'approval_reference': args.approval_reference, 'authoring_session': args.authoring_session,
               'host': socket.gethostname(), 'lane': lane, 'basis': 'simulated', 'gain_claim': False,
               'memory_gib': args.memory_gib, 'storage_gib': args.storage_gib, 'attempt': args.attempt,
               'driver_sha256': artifacts.file_hash(__file__), 'project': str(PROJECT)}
    receipt_path = folder/'driver.json'
    save(receipt_path, receipt)

    def interrupted(signum, frame):
        raise InterruptedError('driver interrupted by signal '+str(signum))
    previous = {signum: signal.signal(signum, interrupted) for signum in (signal.SIGINT, signal.SIGTERM)}
    try:
        receipt['leases'] = lease_snapshot(lane)
        receipt['host_observation'] = host_observation.capture(folder, PROJECT)
        git = lambda *a: subprocess.check_output(['git', *a], cwd=PROJECT, text=True, timeout=30).strip()
        receipt['runtime_commit'] = git('rev-parse', 'HEAD')
        receipt['runtime_branch'] = git('branch', '--show-current')
        receipt['tracked_changes'] = git('status', '--short', '--untracked-files=no').splitlines()
        need(receipt['runtime_branch'] == 'yanrujhou_main', 'driver requires the approved yanrujhou_main branch')
        memory_gib, storage_gib = ((PREPARE_MEMORY_GIB, 4) if args.stage == 'prepare'
                                   else (args.memory_gib, args.storage_gib))
        receipt['preflight'] = dispatch_preflight.check(args.runs_dir, lane,
            storage_bytes=storage_gib*dispatch_preflight.GIB, memory_bytes=memory_gib*dispatch_preflight.GIB)
        save(receipt_path, receipt)
        temporary = folder/'tmp'
        temporary.mkdir()
        environment = {**os.environ, 'TMPDIR': str(temporary), 'MAKEFLAGS': '-j1', 'CMAKE_BUILD_PARALLEL_LEVEL': '1',
                       'OMP_THREAD_LIMIT': '4', 'OMP_WAIT_POLICY': 'PASSIVE', 'GOMP_SPINCOUNT': '0'}
        environment.pop('GOMP_CPU_AFFINITY', None)
        stage = prepare_stage if args.stage == 'prepare' else timed_stage
        receipt['result'] = stage(args, folder, lane, environment)
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
        print('bc-gem5-driver: '+str(error), file=sys.stderr)
        raise SystemExit(1)
