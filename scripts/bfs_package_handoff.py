#!/usr/bin/env python3
"""Demonstrate exact real profile-package retrieval and existing patch handoff.

Created: 2026-09-25 (Eastern Time). This metadata-only driver does not compile,
measure, choose a transformation, or make a performance claim. The earlier
measured candidate need not be an unchanged application baseline.
"""
import argparse
import difflib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, profile_package


def demonstrated_patch(before, after):
    """Rebase an already materialized source change, retaining its exact result."""
    before_root, after_root = (artifacts.verify(value['artifact']) for value in (before, after))
    old = {entry['path']: entry['sha256'] for entry in before['artifact']['files']}
    new = {entry['path']: entry['sha256'] for entry in after['artifact']['files']}
    if set(old) != set(new):
        raise ValueError('handoff demonstration must preserve the application file set')
    paths = sorted(path for path in old if old[path] != new[path])
    if len(paths) != 1 or Path(paths[0]).name != 'bfs.cc':
        raise ValueError('handoff requires the existing single BFS translation-unit change')
    path = paths[0]
    original = (before_root / path).read_text()
    changed = (after_root / path).read_text()
    patch = ''.join(difflib.unified_diff(original.splitlines(keepends=True), changed.splitlines(keepends=True),
                                       fromfile='a/' + path, tofile='b/' + path))
    if not patch:
        raise ValueError('the two measured candidates have no source difference')
    return path, patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('id', 'before-evaluation', 'before-profile', 'after-evaluation', 'after-profile', 'reference-proposal'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--records', type=Path, default=ROOT / 'records')
    parser.add_argument('--runs-dir', type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', args.id):
        parser.error('invalid record identifier')
    args.records = args.records.resolve()
    folder = artifacts.external_directory(args.runs_dir.resolve()) / (args.id + '.driver')
    folder.mkdir(exist_ok=False)
    receipt = {'id': args.id, 'state': 'running', 'gain_claim': False,
               'purpose': 'existing measured transformation through exact real profile packages', 'stages': []}
    started = time.monotonic()

    def save():
        receipt['elapsed_seconds'] = time.monotonic() - started
        temporary = folder / 'receipt.pending.json'
        temporary.write_text(json.dumps(receipt, indent=2) + '\n')
        temporary.replace(folder / 'receipt.json')

    def call(command, *rest):
        remaining = 1800 - (time.monotonic() - started)
        if remaining <= 0:
            raise TimeoutError('metadata handoff elapsed budget exhausted')
        index = len(receipt['stages'])
        out, err = folder / f'{index:02}-{command}.json', folder / f'{index:02}-{command}.stderr'
        argv = [sys.executable, '-m', 'swdb', command, *map(str, rest),
                '--records', str(args.records)]
        if command != 'build':
            argv += ['--format', 'json']
        entry = {'command': argv, 'stdout': str(out), 'stderr': str(err), 'state': 'running'}
        receipt['stages'].append(entry); save()
        with out.open('w') as stdout, err.open('w') as stderr:
            result = subprocess.run(argv, cwd=ROOT, stdout=stdout, stderr=stderr, timeout=min(180, remaining))
        entry.update(state='complete' if result.returncode == 0 else 'failed', returncode=result.returncode,
                     stdout_sha256=artifacts.file_hash(out), stderr_sha256=artifacts.file_hash(err)); save()
        if result.returncode:
            raise RuntimeError(f'public {command} failed; retained {out} and {err}')
        return {'message': out.read_text().strip()} if command == 'build' else json.loads(out.read_text())

    def request(command, data, *rest):
        file = folder / (data['id'] + '.request.json')
        file.write_text(json.dumps(data, indent=2) + '\n')
        return call(command, file, *rest)

    save()
    try:
        evaluations = [call('get', rid) for rid in (args.before_evaluation, args.after_evaluation)]
        profiles = [call('get', rid) for rid in (args.before_profile, args.after_profile)]
        candidates = [call('get', evaluation['candidate']) for evaluation in evaluations]
        reference = call('get', args.reference_proposal)
        if (reference.get('candidate') != candidates[1]['id'] or reference['request']['payload']['kind'] != 'patch'
                or evaluations[1].get('proposal') != reference['id']):
            raise ValueError('after candidate is not the retained reference patch result')
        if len({evaluation['implementation'] for evaluation in evaluations}) != 1:
            raise ValueError('demonstration sources use different implementations')
        contexts = [profile_package._context(evaluation) for evaluation in evaluations]
        if any(contexts[0][key] != contexts[1][key] for key in contexts[0] if key != 'source_sha256'):
            raise ValueError('before and after observations use different graph/target/source sequence/ROI')
        for evaluation, diagnostic in zip(evaluations, profiles):
            if (evaluation['outcome']['state'] != 'complete' or evaluation['correctness']['state'] != 'passed'
                    or evaluation['evidence_kind'] != 'execution' or evaluation['request'].get('fixture') is True
                    or diagnostic['evaluation'] != evaluation['id'] or profile_package.memory_observation_issues(diagnostic)[1]):
                raise ValueError('demonstration requires exact checked real execution and valid diagnostic memory')
        path, patch = demonstrated_patch(*candidates)
        packages = []
        for label, evaluation, diagnostic, context in zip(('before', 'after'), evaluations, profiles, contexts):
            package = request('profile-package', {'message_version': '1.0', 'id': args.id + '.' + label + '.package',
                'implementation': evaluation['implementation'], 'evaluation': evaluation['id'],
                'region_profile': diagnostic['id'], 'context': context})
            if package['completeness'] != 'complete' or package['evidence']['classification'] != 'execution':
                raise ValueError('public assembler retained an incomplete or fixture package')
            forward = call('profile-strategies', package['id'])
            reversible = next((row for row in forward['matches'] if row['outcome'] != 'illegal'), None)
            if reversible is None:
                raise ValueError('forward strategy query returned no legal or unresolved applicability information')
            reverse = call('strategy-regions', reversible['strategy'], '--package', package['id'])
            if not any(row['profile_package'] == package['id'] for row in reverse['profiled_matches']):
                raise ValueError('reverse strategy query lost the exact measured package')
            packages.append(package)
        package = packages[0]
        envelope = {'message_version': '1.0', 'id': args.id + '.proposal',
            'producer': {'name': 'swdb-real-package-handoff-client', 'role': 'sw', 'test_client': True},
            'implementation': package['implementation'], 'profile_package': package['id'],
            'source_snapshot': package['source_snapshot'], 'source_sha256': package['context']['source_sha256'],
            'regions': [row['id'] for row in package['regions'] if row['path'] == path],
            'intent': reference['request']['intent'],
            'constraints': {'editable_files': [path], 'preserve_correctness': True, 'preserve_roi': True},
            'parameters': {'reference_proposal': reference['id'], 'reference_candidate': candidates[1]['id'],
                           'purpose': 'rebase the existing demonstrated delta onto the measured package source'},
            'required_operations': reference['request'].get('required_operations', []),
            'payload': {'kind': 'patch', 'content': patch}}
        submitted = request('submit', envelope, '--runs-dir', args.runs_dir)
        if submitted['outcome']['state'] != 'candidate_created':
            raise ValueError('public real-package patch handoff did not create a candidate')
        candidate = call('get', submitted['candidate'])
        if candidate['artifact']['sha256'] != candidates[1]['artifact']['sha256']:
            raise ValueError('handoff changed the already demonstrated final source artifact')
        call('build')
        chain = call('get', candidate['id'], '--chain')
        required = {submitted['id'], candidate['id'], package['id'], package['source_snapshot'], evaluations[0]['id'], profiles[0]['id']}
        if not required <= set(chain['records']):
            raise ValueError('fresh index retrieval lost the package input or underlying evidence')
        for item in packages:
            retained = call('get', item['id'])
            if retained != item:
                raise ValueError('package identity changed during index rebuild')
        receipt.update(state='complete', profile_packages=[item['id'] for item in packages],
            proposal=submitted['id'], candidate=candidate['id'], reference_candidate=candidates[1]['id'],
            matching_source_sha256=candidate['artifact']['sha256'], retrieved_records=len(chain['records']),
            package_completeness=[item['completeness'] for item in packages])
    except BaseException as exc:
        receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}'); save(); raise
    save()
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
