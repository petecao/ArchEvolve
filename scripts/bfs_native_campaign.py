#!/usr/bin/env python3
"""Execute an operator-selected native BFS proposal under an existing frozen policy.

Created: 2026-09-25 (Eastern Time). This bounded driver does not select intent,
workloads, profitability thresholds, or a new protocol. Unfavorable results stay.
"""
import argparse
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, bfs_protocol, profile, profile_package, rewrite
from swdb.store import Store


def validate_inputs(packages, frozen, proposal, get, lane):
    """Check the exact inputs before any proposal is sent or benchmark is run."""
    if len(packages) != 2 or len({p['id'] for p in packages}) != 2:
        raise ValueError('exactly two distinct baseline packages are required')
    bfs_protocol.verify_immutable(frozen)
    settings = frozen['settings']
    if settings['mode'] != 'native' or settings['targets']['baseline'] != settings['targets']['candidate']:
        raise ValueError('campaign requires an already-frozen native comparison on one target')
    target = settings['targets']['candidate']
    if target['id'] != 'mbit10' or target['configuration'].get('lane') != lane:
        raise ValueError('frozen target must identify this exact mbit10 lane')
    if settings['roi'] != 'bfs.complete_call.v1':
        raise ValueError('campaign requires the protected native BFS complete-call ROI')
    by_family, identities = {}, set()
    for package in packages:
        profile_package.verify(package)
        if package.get('completeness') != 'complete' or package.get('evidence', {}).get('classification') != 'execution':
            raise ValueError('both baseline packages must contain complete real execution evidence')
        evaluation = get(package['evaluation'])
        candidate = get(package['candidate'])
        source = get(candidate['source_snapshot'])
        workload = get(evaluation['context']['workload']['id'])
        bfs_protocol.verify_immutable(workload)
        if (evaluation['outcome']['state'] != 'complete' or evaluation['correctness']['state'] != 'passed'
                or evaluation['evidence_kind'] != 'execution' or evaluation['request'].get('fixture') is True):
            raise ValueError('baseline package has no real passed primary evaluation')
        if (package['evidence']['evaluation_sha256'] != artifacts.digest(evaluation)
                or package['context'] != profile_package._context(evaluation)
                or evaluation.get('candidate') != candidate['id']):
            raise ValueError('baseline package primary source/context evidence changed')
        if candidate.get('artifact_role') != 'source_baseline' or candidate['artifact']['sha256'] != source['artifact']['sha256']:
            raise ValueError('baseline package must measure an unchanged starting-source candidate')
        artifacts.verify(candidate['artifact'])
        if (workload['id'] not in frozen['workload_identities']
                or workload['identity_sha256'] != frozen['workload_identities'][workload['id']]
                or workload['definition']['canonical_sha256'] != evaluation['context']['workload']['canonical_sha256']):
            raise ValueError('baseline workload differs from its frozen canonical graph')
        expected = {'sources': workload['definition']['sources'], 'target': target['id'],
                    'target_configuration': target['configuration'], 'threads': settings['threads'], 'roi': settings['roi']}
        if any(artifacts.digest(package['context'].get(k)) != artifacts.digest(v) for k, v in expected.items()):
            raise ValueError('baseline package sources/target/threads/ROI differ from the frozen assessment')
        family = workload['definition']['family']
        if family in by_family:
            raise ValueError('baseline packages repeat a graph family')
        by_family[family] = {'package': package, 'evaluation': evaluation, 'candidate': candidate, 'workload': workload}
        identities.add((package['implementation'], candidate['artifact']['sha256']))
    if set(by_family) != {'kronecker', 'uniform_random'} or len(identities) != 1:
        raise ValueError('packages must cover both families for the same implementation and exact source')
    if set(settings['workloads']) != {row['workload']['id'] for row in by_family.values()}:
        raise ValueError('protocol workload set must exactly match the two declared package workloads')
    first = packages[0]
    if (proposal.get('message_version') != '1.0' or proposal.get('profile_package') != first['id']
            or proposal.get('source_snapshot') != first['source_snapshot']
            or proposal.get('implementation') != first['implementation']
            or proposal.get('source_sha256') != first['context']['source_sha256']):
        raise ValueError('operator proposal must exactly target the first supplied package and its source')
    if proposal.get('producer', {}).get('test_client') is not True:
        raise ValueError('campaign demonstrations must identify their test-client producer')
    if proposal.get('payload', {}).get('kind') not in {'patch', 'structured_instructions'}:
        raise ValueError('native campaign requires the assigned patch or structured-instructions route')
    expected_route = {'dx100-bfs-scalar': 'patch', 'gapbs-bfs-do': 'structured_instructions'}
    if expected_route.get(first['implementation']) != proposal['payload']['kind']:
        raise ValueError('proposal route does not match this source-specific native campaign')
    return by_family


class Driver:
    def __init__(self, args):
        self.args = args
        self.started = time.monotonic()
        self.folder = args.runs_dir / (args.id + '.driver')
        self.folder.mkdir(exist_ok=False)
        self.receipt = {'id': args.id, 'state': 'running', 'protocol': args.protocol,
                        'stages': [], 'families': {}, 'candidate_rounds': [], 'repair_attempts': [],
                        'gain_claim': False, 'acceptance': 'reported separately by bfs-coverage',
                        'lane': args.lane, 'bounds': {'driver_seconds': args.total_seconds,
                        'evaluation_seconds': 1200, 'profile_seconds': 1200, 'max_repairs': int(bool(args.repair_config))}}
        self.save()

    def save(self):
        pending = self.folder / 'driver.pending.json'
        pending.write_text(json.dumps(self.receipt, indent=2, allow_nan=False))
        pending.replace(self.folder / 'driver.json')

    def call(self, command, *rest, timeout=180, required=True):
        args = self.args
        profile._verified_lane(Store(args.records).get('mbit10', 'machine'), args.lane)
        remaining = args.total_seconds - (time.monotonic() - self.started)
        if remaining <= 0:
            raise TimeoutError('native campaign total wall budget exhausted')
        for path, reserve in ((args.runs_dir, 30), (args.source_runs_dir, 10)):
            stat = os.statvfs(path)
            if stat.f_bavail * stat.f_frsize < reserve * 1024**3:
                raise RuntimeError(f'{path} free-space reserve is below {reserve} GiB')
        index = len(self.receipt['stages'])
        output, error = self.folder / f'{index:03}-{command}.json', self.folder / f'{index:03}-{command}.stderr'
        argv = [sys.executable, '-m', 'swdb', command, *map(str, rest), '--records', str(args.records), '--format', 'json']
        entry = {'command': argv, 'state': 'running', 'stdout': str(output), 'stderr': str(error)}
        self.receipt['stages'].append(entry)
        self.save()
        before = time.monotonic()
        with output.open('w') as stdout, error.open('w') as stderr:
            child = subprocess.Popen(argv, cwd=ROOT, stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                child.wait(timeout=min(timeout, remaining))
            except BaseException:
                try: os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError: pass
                try: child.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    try: os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                    child.wait()
                entry.update(state='interrupted_or_timeout', returncode=child.returncode,
                             stdout_sha256=artifacts.file_hash(output), stderr_sha256=artifacts.file_hash(error))
                self.save()
                raise
        entry.update(state='complete' if child.returncode == 0 else 'failed', returncode=child.returncode,
                     host_wall_s=time.monotonic() - before, stdout_sha256=artifacts.file_hash(output),
                     stderr_sha256=artifacts.file_hash(error))
        self.save()
        try: result = json.loads(output.read_text())
        except (ValueError, OSError): result = None
        if required and (child.returncode != 0 or not isinstance(result, dict)):
            raise RuntimeError(f'{command} failed; inspect retained {output} and {error}')
        return result

    def request(self, command, value, *rest, **kwargs):
        if not isinstance(value.get('id'), str) or not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', value['id']):
            raise ValueError('request ID must use record identifier syntax')
        path = self.folder / (value['id'] + '.request.json')
        if path.exists(): raise ValueError('driver request ID would overwrite retained evidence')
        path.write_text(json.dumps(value, indent=2, allow_nan=False))
        return self.call(command, path, *rest, **kwargs)

    def evaluate(self, name, candidate, workload, frozen, role):
        settings = frozen['settings']
        request = {'message_version': '1.0', 'id': name, 'candidate': candidate, 'machine': 'mbit10',
            'protocol': frozen['id'], 'protocol_role': role, 'threads': settings['threads'],
            'repetitions': settings['sampling']['repetitions'], 'sources': workload['definition']['sources'],
            'roi': settings['roi'], 'target_configuration': settings['targets'][role]['configuration'],
            'workload': {'id': workload['id']}, 'comparison_baseline': self.receipt['implementation'],
            'build': {key: settings['builds'][role][key] for key in ('compiler', 'flags')},
            'budget': {'build_seconds': 180, 'run_seconds': 60, 'total_seconds': 1200}}
        return self.request('evaluate', request, '--runs-dir', self.args.runs_dir, '--lane', self.args.lane,
                            timeout=1260, required=False)

    def collect(self, prefix, evaluation, baseline_profile):
        if not evaluation or evaluation.get('outcome', {}).get('state') != 'complete': return None
        observed = self.request('bfs-profile', {'message_version': '1.0', 'id': prefix + '.profile',
            'evaluation': evaluation['id'], 'memory': True, 'correspondence': baseline_profile,
            'budget': {'discovery_seconds': 120, 'build_seconds': 180, 'run_seconds': 600, 'total_seconds': 1200}},
            '--runs-dir', self.args.runs_dir, '--lane', self.args.lane, timeout=1260, required=False)
        if not observed or not observed.get('id'): return None
        package = self.request('profile-package', {'message_version': '1.0', 'id': prefix + '.package',
            'implementation': evaluation['implementation'], 'evaluation': evaluation['id'], 'region_profile': observed['id'],
            'context': profile_package._context(evaluation)}, required=False)
        if package and package.get('id'):
            self.call('profile-strategies', package['id'], required=False)
            self.call('get', package['id'], '--chain', required=False)
        return package

    def run(self):
        args = self.args
        frozen = self.call('get', args.protocol)
        packages = [self.call('get', rid) for rid in args.packages]
        proposal = json.loads(args.proposal.read_text())
        bfs_protocol._validate_settings(frozen['settings'], Store(args.records))
        rows = validate_inputs(packages, frozen, proposal, lambda rid: self.call('get', rid), args.lane)
        if proposal['payload']['kind'] == 'structured_instructions' and not args.provider_config:
            raise ValueError('interpreted proposal requires operator-supplied --provider-config')
        for file in (args.provider_config, args.repair_config):
            if file:
                config = rewrite.configuration(file)
                if config['kind'] != 'claude': raise ValueError('real campaign cannot use an external fixture provider')
        self.receipt.update(implementation=proposal['implementation'], proposal=proposal['id'],
            proposal_sha256=artifacts.digest(proposal), protocol_sha256=frozen['identity_sha256'],
            inputs=[{'id': package['id'], 'sha256': artifacts.digest(package)} for package in packages],
            repository_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
        self.save()
        extra = ['--provider-config', args.provider_config] if args.provider_config else []
        submitted = self.request('submit', proposal, '--runs-dir', args.source_runs_dir, *extra, timeout=1000, required=False)
        if not submitted or submitted.get('outcome', {}).get('state') != 'candidate_created':
            self.receipt.update(state='proposal_non_success', proposal_outcome=(submitted or {}).get('outcome'))
            return
        candidate = submitted['candidate']
        baselines = {}
        for family, row in rows.items():
            prefix = args.id + '.' + family.replace('_', '-')
            baseline = self.evaluate(prefix + '.baseline', row['candidate']['id'], row['workload'], frozen, 'baseline')
            baselines[family] = baseline
            self.receipt['families'][family] = {'workload': row['workload']['id'], 'baseline': baseline and baseline['id'],
                                               'baseline_outcome': (baseline or {}).get('outcome')}
            self.save()
        for round_number in (1, 2):
            current = {'number': round_number, 'candidate': candidate, 'families': {}}
            self.receipt['candidate_rounds'].append(current)
            self.save()
            repairable = []
            for family, row in rows.items():
                prefix = args.id + '.' + family.replace('_', '-') + f'.candidate-{round_number}'
                evaluation = self.evaluate(prefix + '.evaluation', candidate, row['workload'], frozen, 'candidate')
                package = self.collect(prefix, evaluation, row['package']['region_profile'])
                baseline = baselines[family]
                comparison = None
                if evaluation and baseline:
                    comparison = self.request('compare-evaluations', {'message_version': '1.0', 'id': prefix + '.comparison',
                        'protocol': frozen['id'], 'baseline_evaluation': baseline['id'], 'candidate_evaluation': evaluation['id'],
                        'comparison_baseline': proposal['implementation']}, required=False)
                current['families'][family] = {'evaluation': evaluation and evaluation['id'],
                    'outcome': (evaluation or {}).get('outcome'), 'profile_package': package and package['id'],
                    'package_completeness': (package or {}).get('completeness'),
                    'comparison': comparison and comparison['id'], 'decision': (comparison or {}).get('decision')}
                if evaluation:
                    self.call('get', evaluation['id'], '--chain', required=False)
                    if ((evaluation['outcome']['state'] == 'failed' and evaluation['outcome']['stage'] == 'build')
                            or evaluation['correctness']['state'] == 'failed'):
                        repairable.append(evaluation['id'])
                self.save()
            if not repairable or not args.repair_config or round_number == 2: break
            repaired = self.call('repair', repairable[0], '--runs-dir', args.source_runs_dir,
                                 '--provider-config', args.repair_config, timeout=1000, required=False)
            self.receipt['repair_attempts'].append({'trigger': repairable[0], 'outcome': (repaired or {}).get('outcome'),
                                                   'candidate': (repaired or {}).get('candidate')})
            self.save()
            if not repaired or repaired.get('outcome', {}).get('state') != 'candidate_created': break
            candidate = repaired['candidate']
        final = self.receipt['candidate_rounds'][-1]
        compatible = {'gain', 'regression', 'no_gain', 'inconclusive'}
        complete = all((row.get('outcome') or {}).get('state') == 'complete'
                       and row.get('package_completeness') == 'complete'
                       and (row.get('decision') or {}).get('state') in compatible for row in final['families'].values())
        self.receipt.update(state='evaluated' if complete else 'incomplete', final_candidate=candidate)
        self.call('get', proposal['id'], '--chain', required=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--packages', nargs=2, required=True, help='kronecker/uniform baseline packages; proposal targets the first')
    parser.add_argument('--protocol', required=True)
    parser.add_argument('--proposal', type=Path, required=True, help='operator-authored JSON request; intent is never synthesized by this driver')
    parser.add_argument('--provider-config', type=Path)
    parser.add_argument('--repair-config', type=Path, help='optional provider configuration authorizing at most one build/correctness repair')
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--source-runs-dir', type=Path, required=True)
    parser.add_argument('--records', type=Path, default=ROOT / 'records')
    parser.add_argument('--lane', choices=['mbit10-evaluation-node0', 'mbit10-evaluation-node1'], required=True)
    parser.add_argument('--total-seconds', type=int, default=14400)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', args.id): parser.error('id must use record identifier syntax')
    if not 1 <= args.total_seconds <= 21600: parser.error('total-seconds must be in [1,21600]')
    for key in ('records', 'proposal', 'provider_config', 'repair_config'):
        if getattr(args, key) is not None: setattr(args, key, getattr(args, key).resolve())
    if socket.gethostname().split('.')[0] != 'mbit10': parser.error('native campaign requires mbit10')
    args.runs_dir = artifacts.external_directory(args.runs_dir)
    args.source_runs_dir = artifacts.external_directory(args.source_runs_dir)
    if not args.source_runs_dir.is_relative_to('/data1/yanruj'):
        parser.error('source/provider artifacts must use /data1/yanruj')
    if not any(args.runs_dir.is_relative_to(base) for base in ('/data1/yanruj', '/data/yanruj')):
        parser.error('raw outputs must use an authorized host volume')
    if args.runs_dir.is_relative_to(args.source_runs_dir) or args.source_runs_dir.is_relative_to(args.runs_dir):
        parser.error('raw and source/provider artifact trees must be disjoint')
    profile._verified_lane(Store(args.records).get('mbit10', 'machine'), args.lane)
    driver = Driver(args)
    def stop(signum, _frame): raise InterruptedError(f'campaign interrupted by signal {signum}')
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP): signal.signal(sig, stop)
    try:
        driver.run()
    except BaseException as exc:
        driver.receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        driver.receipt['host_wall_s'] = time.monotonic() - driver.started
        driver.save()
        print(json.dumps(driver.receipt, indent=2))
    return 0 if driver.receipt['state'] == 'evaluated' else 1


if __name__ == '__main__':
    raise SystemExit(main())
