#!/usr/bin/env python3
"""Run one bounded BFS simulator sample grid using public workflow commands.

Created: 2026-09-25 (Eastern Time). A pilot accepts unchanged baselines only.
A frozen series evaluates an already selected candidate; it never picks a
strategy, freezes settings, retries a failure, or makes a gain claim.
"""
import argparse
import json
import os
from pathlib import Path
import re
import socket
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, bfs_protocol, profile
from swdb.store import Store
from scripts.dx100_build import disk_usage_kib
from scripts.bfs_process import interruption_signals, run_stage


def validate_diagnostic_build(build, candidate, implementation, model, roi, accelerated, frozen=None, role=None):
    """Reuse the exact pre-freeze diagnostic artifact, never a fresh substitute."""
    context, request = build.get('context', {}), build.get('request', {})
    if (build.get('outcome', {}).get('state') != 'complete'
            or build['outcome'].get('stage') != 'candidate_build'
            or build.get('evidence_kind') != 'execution' or request.get('fixture') is True
            or build.get('candidate') != candidate['id']
            or context.get('candidate_sha256') != candidate['artifact']['sha256']
            or context.get('function') != implementation['function']
            or context.get('model_build') != model['id']
            or context.get('model_root') != model['context']['model_root']
            or context.get('target') != model['context']['target']
            or context.get('roi') != roi or context.get('accelerated_requested') is not accelerated
            or request.get('diagnostic_regions') is not True or not context.get('diagnostic')):
        raise ValueError('diagnostic build does not identify this exact source/model/ROI/treatment')
    definition = context['diagnostic']
    for pair in frozen['settings'].get('region_pairs', []) if frozen else []:
        if pair.get('evidence') != 'simulated_diagnostic_profile':
            continue
        collector = pair['collector']
        if (not any(row['id'] == pair[role] for row in definition['regions'])
                or any(definition['discovery'].get(key) != collector[key]
                       for key in ('backend', 'collector', 'library_sha256', 'pass_sha256'))
                or definition['runtime']['sha256'] != collector['runtime_sha256']):
            raise ValueError('diagnostic build differs from the frozen region correspondence/collector')


def validate_selection(candidate, source, implementation, workload, frozen, role, author, expected_artifact):
    """Reject strategy assessment disguised as pre-freeze calibration."""
    bfs_protocol.verify_immutable(workload)
    if (candidate['implementation'] != implementation['id'] or source['implementation'] != implementation['id']
            or candidate['source_snapshot'] != source['id']
            or candidate['context'].get('function') != implementation['function']
            or source['context'].get('function') != implementation['function']):
        raise ValueError('candidate/source entry-point identity differs from the selected implementation')
    if frozen is None or role == 'baseline' or author:
        if candidate['artifact']['sha256'] != expected_artifact['sha256']:
            raise ValueError('calibration and comparison baselines must match the pinned application source')
    if frozen is None:
        if (candidate.get('artifact_role') != 'source_baseline' or candidate.get('proposal')
                or candidate['artifact']['sha256'] != source['artifact']['sha256']
                or implementation['id'] not in {'dx100-bfs-scalar', 'gapbs-bfs-do', 'dx100-bfs-maa-reference'}):
            raise ValueError('a pilot requires the unchanged identified source baseline or author reference')
    else:
        bfs_protocol.verify_immutable(frozen)
        if frozen['settings']['mode'] not in {'controlled_simulator', 'artifact_reference'}:
            raise ValueError('a frozen simulator series requires a simulated protocol')
        if role not in {'baseline', 'candidate'} or workload['id'] not in frozen['workload_identities']:
            raise ValueError('frozen role/workload is outside the protocol')
        if frozen['workload_identities'][workload['id']] != workload['identity_sha256']:
            raise ValueError('workload identity differs from the frozen protocol')
        if role == 'baseline' and (candidate.get('artifact_role') != 'source_baseline'
                or candidate.get('proposal') or candidate['artifact']['sha256'] != source['artifact']['sha256']
                or implementation['id'] not in {'dx100-bfs-scalar', 'gapbs-bfs-do'}):
            raise ValueError('the comparison baseline must be unchanged unaccelerated starting source')
    if author and (candidate.get('artifact_role') != 'source_baseline'
                   or candidate['artifact']['sha256'] != source['artifact']['sha256']
                   or implementation['id'] not in {'dx100-bfs-scalar', 'dx100-bfs-maa-reference'}):
        raise ValueError('author binaries require unchanged, explicitly identified DX100 source')


@interruption_signals()
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('id', 'candidate', 'workload', 'build-evaluation'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--configuration', type=Path, required=True,
                        help='exact mode, l3_size_mb, l3_assoc, tile_elements JSON request')
    parser.add_argument('--protocol')
    parser.add_argument('--protocol-role', choices=('baseline', 'candidate'))
    parser.add_argument('--diagnostic-build', help='reuse an exact completed diagnostic compile record selected before freeze')
    parser.add_argument('--author-binary', action='store_true', help='retain the original author traversal ROI')
    parser.add_argument('--accelerated', action='store_true', help='compile MAA support; does not prove execution')
    parser.add_argument('--runs-dir', type=Path, required=True, help='unique batch raw-output directory on mbit10')
    parser.add_argument('--records', type=Path, default=ROOT / 'records')
    parser.add_argument('--lane', type=int, choices=(0, 1), required=True)
    parser.add_argument('--total-seconds', type=int, default=43200)
    parser.add_argument('--checkpoint-seconds', type=int, default=3600)
    parser.add_argument('--run-seconds', type=int, default=3600)
    parser.add_argument('--diagnostic-seconds', type=int, default=600)
    parser.add_argument('--memory-gib', type=int, default=32)
    parser.add_argument('--storage-gib', type=int, default=10)
    parser.add_argument('--batch-storage-gib', type=int, default=40)
    parser.add_argument('--verification-ticks', type=int, default=10**14)
    args = parser.parse_args()
    if socket.gethostname().split('.')[0] != 'mbit10':
        parser.error('this driver requires the mbit10 execution host')
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', args.id):
        parser.error('invalid record identifier')
    if bool(args.protocol) != bool(args.protocol_role):
        parser.error('protocol and protocol-role must be supplied together')
    limits = {'total_seconds': (1, 86400 if args.author_binary else 43200),
              'checkpoint_seconds': (1, 3600), 'run_seconds': (1, 14400 if args.author_binary else 3600),
              'diagnostic_seconds': (180, 600), 'memory_gib': (1, 48 if args.author_binary else 32),
              'storage_gib': (1, 15 if args.author_binary else 10),
              'batch_storage_gib': (1, 60 if args.author_binary else 40),
              'verification_ticks': (1, 10**15)}
    for name, (low, high) in limits.items():
        if not low <= getattr(args, name) <= high:
            parser.error(f'{name} must be between {low} and {high}')
    runs = args.runs_dir.resolve()
    if not any(runs != Path(base) and runs.is_relative_to(base)
               for base in ('/data/yanruj/EvolveSWDB_runs', '/data1/yanruj/EvolveSWDB_runs')):
        parser.error('raw output must use a dedicated child of authorized EvolveSWDB_runs storage')
    runs = artifacts.external_directory(runs)
    if any(runs.iterdir()):
        parser.error('series raw directory must be empty so its budget cannot include unrelated jobs')
    args.records = args.records.resolve()
    store = Store(args.records)
    lane = f'mbit10-evaluation-node{args.lane}'
    profile._verified_lane(store.get('mbit10', 'machine'), lane)
    folder = runs / (args.id + '.driver')
    folder.mkdir(exist_ok=False)
    receipt = {'id': args.id, 'created': '2026-09-25', 'state': 'running', 'gain_claim': False,
               'purpose': 'frozen_sample_grid' if args.protocol else 'unchanged_baseline_calibration',
               'bounds': {name: getattr(args, name) for name in limits},
               'stages': [], 'samples': [], 'lane': lane,
               'repository_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()}
    started = time.monotonic()

    def save():
        receipt['host_wall_s'] = time.monotonic() - started
        (folder / 'driver.json').write_text(json.dumps(receipt, indent=2) + '\n')

    def storage_bytes():
        # A dedicated batch root bounds all of its retained checkpoints and logs.
        used, warnings = disk_usage_kib(runs)
        if warnings:
            receipt.setdefault('monitor_warnings', []).extend(warnings)
            save()
        return used * 1024

    def check_bounds():
        remaining = args.total_seconds - (time.monotonic() - started)
        if remaining <= 0:
            raise TimeoutError('simulator series elapsed budget exhausted')
        for volume, reserve in ((runs, 30), (Path('/data1'), 10)):
            usage = os.statvfs(volume)
            if usage.f_bavail * usage.f_frsize < reserve * 1024**3:
                raise RuntimeError(f'{volume}: free-space reserve below {reserve} GiB')
        if storage_bytes() >= args.batch_storage_gib * 1024**3:
            raise RuntimeError('batch raw-storage budget exhausted')
        return remaining

    def call(command, *rest, timeout=180):
        profile._verified_lane(Store(args.records).get('mbit10', 'machine'), lane)
        check_bounds()
        index = len(receipt['stages'])
        out, err = folder / f'{index:03d}-{command}.json', folder / f'{index:03d}-{command}.stderr'
        argv = [sys.executable, '-m', 'swdb', command, *map(str, rest), '--records', str(args.records), '--format', 'json']
        try:
            run_stage(receipt, folder, argv, timeout=timeout,
                      deadline=started + args.total_seconds - 30, cwd=ROOT,
                      output=out, stderr=err, monitor=check_bounds)
        finally:
            if len(receipt['stages']) > index:
                receipt['stages'][index]['stdout'] = str(out)
            save()
        return json.loads(out.read_text())

    def request(command, value, *, timeout=180, execute=False):
        path = folder / (value['id'] + '.request.json')
        path.write_text(json.dumps(value, indent=2) + '\n')
        rest = ['--runs-dir', runs, '--lane', args.lane] if execute else []
        return call(command, path, *rest, timeout=timeout)

    save()
    try:
        candidate = call('get', args.candidate)
        source = call('get', candidate['source_snapshot'])
        implementation = call('get', candidate['implementation'])
        workload = call('get', args.workload)
        frozen = call('get', args.protocol) if args.protocol else None
        expected_artifact = artifacts.identify(artifacts.source_root(Store(args.records), implementation))
        validate_selection(candidate, source, implementation, workload, frozen, args.protocol_role, args.author_binary, expected_artifact)
        model = call('get', args.build_evaluation)
        if (model['outcome']['state'] != 'complete' or model['outcome']['stage'] != 'build'
                or model['evidence_kind'] != 'execution'):
            raise ValueError('a completed real model build is required')
        configuration = json.loads(args.configuration.read_text())
        if set(configuration) != {'mode', 'l3_size_mb', 'l3_assoc', 'tile_elements'}:
            raise ValueError('configuration must specify exactly the four public DX100 configuration fields')
        if args.accelerated != (implementation['function'] == 'DOBFSMAA') and args.author_binary:
            raise ValueError('author accelerated selection differs from identified function')
        repetitions = frozen['settings']['sampling']['repetitions'] if frozen else 2
        if repetitions != 2:
            raise ValueError('this bounded series permits exactly two real simulator replays')
        selected = bfs_protocol.workload_representation(Store(args.records), workload['id'], source['application'])
        graph = {key: selected['representation'][key] for key in ('path', 'sha256')}
        binaries = {Path(row['path']).name: row for row in model['build']['details']['binaries']}
        roi = 'bfs.complete_call.v1'
        if args.author_binary:
            from swdb.dx100 import ROI as AUTHOR_ROI
            roi = AUTHOR_ROI
        builds = {}
        for treatment in ('primary', 'diagnostic'):
            if args.author_binary and treatment == 'primary':
                builds[treatment] = None
                continue
            if treatment == 'diagnostic' and args.diagnostic_build:
                builds[treatment] = call('get', args.diagnostic_build)
                continue
            builds[treatment] = request('dx100-compile', {
                'message_version': '1.0', 'id': args.id + '.' + treatment + '.build',
                'machine': 'mbit10', 'hardware_target': 'dx100-e4fc4af-4c',
                'model_root': model['context']['model_root'], 'build_evaluation': model['id'],
                'candidate': candidate['id'], 'function': implementation['function'],
                'accelerated': args.accelerated, 'roi': roi, 'diagnostic_regions': treatment == 'diagnostic',
                'budget': {'total_seconds': 600, 'build_seconds': 300, 'memory_gib': args.memory_gib, 'storage_gib': 1}},
                timeout=660, execute=True)
            if builds[treatment]['outcome']['state'] != 'complete':
                raise RuntimeError('candidate compilation did not complete')
        validate_diagnostic_build(builds['diagnostic'], candidate, implementation, model,
                                  roi, args.accelerated, frozen, args.protocol_role)
        receipt.update(candidate=candidate['id'], workload=workload['id'], model_build=model['id'],
                       configuration=configuration, roi=roi, protocol=args.protocol, repetitions=repetitions,
                       diagnostic_build={'evaluation': builds['diagnostic']['id'],
                                         'sha256': artifacts.digest(builds['diagnostic'])},
                       checkpoint_policy='two fresh restores of the same exact checkpoint per source and binary')
        save()
        primary_ids = []
        checkpoints = {}
        for position, vertex in enumerate(workload['definition']['sources']):
            for repetition in range(repetitions):
                prefix = f'{args.id}.s{position}.r{repetition}'
                pair = {}
                for treatment in ('primary', 'diagnostic'):
                    compiled = builds[treatment]
                    binary = ({'path': compiled['build']['binary'], 'sha256': compiled['build']['binary_sha256']}
                              if compiled else {key: binaries['bfs_maa' if args.accelerated else 'bfs'][key]
                                                for key in ('path', 'sha256')})
                    diagnostic = treatment == 'diagnostic'
                    # Tiny guest serialization took 91.7s plus stage overhead;
                    # reserve half the fixed budget for its 16GB checkpoint.
                    checkpoint_seconds = args.diagnostic_seconds // 2 if diagnostic else args.checkpoint_seconds
                    run_seconds = args.diagnostic_seconds - checkpoint_seconds - 30 if diagnostic else args.run_seconds
                    total_seconds = args.diagnostic_seconds if diagnostic else min(18000, checkpoint_seconds + run_seconds + 60)
                    payload = {'message_version': '1.0', 'id': prefix + '.' + treatment + '.evaluation',
                        'machine': 'mbit10', 'hardware_target': 'dx100-e4fc4af-4c',
                        'model_root': model['context']['model_root'], 'build_evaluation': model['id'],
                        'candidate': candidate['id'], 'binary': binary,
                        'simulator': {key: binaries['gem5.opt'][key] for key in ('path', 'sha256')},
                        'workload': {'id': workload['id'], 'source': vertex, 'representation': graph},
                        'configuration': configuration,
                        'verification': {'checker': 'dx100.bfs.verifier.v1', 'max_ticks': args.verification_ticks,
                                         'coverage': args.accelerated},
                        'budget': {'total_seconds': total_seconds, 'checkpoint_seconds': checkpoint_seconds,
                                   'run_seconds': run_seconds, 'memory_gib': args.memory_gib, 'storage_gib': args.storage_gib}}
                    if compiled: payload['candidate_build'] = compiled['id']
                    if (position, treatment) in checkpoints:
                        payload['checkpoint_manifest'] = checkpoints[position, treatment]
                    if frozen and not diagnostic:
                        payload.update(protocol=frozen['id'], protocol_role=args.protocol_role,
                                       protocol_trial={'source_position': position, 'repetition': repetition})
                    pair[treatment] = request('dx100-execute', payload, timeout=total_seconds + 60, execute=True)
                    if (pair[treatment]['outcome']['state'] != 'complete'
                            or pair[treatment]['correctness']['state'] != 'passed'):
                        raise RuntimeError(f'{treatment} execution did not complete with exact timed-binary correctness')
                    checkpoints[position, treatment] = pair[treatment]['context']['checkpoint_manifest']
                primary = pair['primary']
                collected = request('dx100-profile', {'message_version': '1.0', 'id': prefix + '.profile',
                    'evaluation': primary['id'], 'diagnostic_evaluation': pair['diagnostic']['id'],
                    'budget': {'total_seconds': 120}}, timeout=180)
                context = primary['context']
                package = request('profile-package', {'message_version': '1.0', 'id': prefix + '.package',
                    'implementation': candidate['implementation'], 'evaluation': primary['id'], 'region_profile': collected['id'],
                    'context': {'source_sha256': candidate['artifact']['sha256'],
                        'canonical_graph_sha256': context['workload']['canonical_sha256'], 'sources': context['sources'],
                        'target': context['target'], 'target_configuration': context['backend_configuration'],
                        'threads': context['threads'], 'roi': context['roi']}})
                refreshed = call('get', primary['id'])
                receipt['samples'].append({'source_position': position, 'source': vertex, 'repetition': repetition,
                    'evaluation': primary['id'], 'diagnostic_evaluation': pair['diagnostic']['id'],
                    'profile': collected['id'], 'package': package['id'], 'completeness': package['completeness'],
                    'timing': refreshed['timing'], 'coverage': refreshed['correctness']['checks'][0].get('coverage')})
                save()
                if package['completeness'] != 'complete':
                    raise RuntimeError('series retained an incomplete actual profile package')
                primary_ids.append(primary['id'])
        receipt['timing_summary'] = []
        for position, vertex in enumerate(workload['definition']['sources']):
            values = [entry['timing'][0]['duration_s'] for entry in receipt['samples'] if entry['source_position'] == position]
            median = statistics.median(values)
            receipt['timing_summary'].append({'source_position': position, 'source': vertex, 'samples': values,
                'median_seconds': median, 'relative_spread': (max(values) - min(values)) / median})
        if frozen:
            aggregate = request('aggregate-evaluations', {'message_version': '1.0', 'id': args.id + '.aggregate',
                'protocol': frozen['id'], 'protocol_role': args.protocol_role, 'evaluations': primary_ids})
            receipt['aggregate'] = aggregate['id']
            if aggregate['outcome']['state'] != 'complete':
                raise RuntimeError('sample-grid aggregation did not pass its frozen evidence checks')
            call('get', aggregate['id'], '--chain')
        receipt['state'] = 'complete'
    except BaseException as exc:
        receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}'); save(); raise
    save()
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
