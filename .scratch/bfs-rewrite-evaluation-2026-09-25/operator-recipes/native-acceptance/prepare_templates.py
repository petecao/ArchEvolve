#!/usr/bin/env python3
"""Prepare data-only native route inputs; never dispatch. Created 2026-09-27 ET."""
import hashlib
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from swdb import artifacts
from scripts.bfs_native_campaign import NATIVE_BOUNDS

HERE = Path(__file__).resolve().parent


def digest(value):
    return artifacts.digest(value)


def reference(record):
    return {'id': record['id'], 'sha256': digest(record)}


def build(route, records):
    proposal = records['bfs-campaign-preparation-20260925-a1.' + route]
    request = proposal['request']
    candidate = records[proposal['candidate']]
    source = records[request['source_snapshot']]
    package = records[request['profile_package']]
    assert proposal['outcome'] == {'state': 'candidate_created', 'stage': 'rewriting', 'reason': None}
    assert candidate['state'] == 'unverified' and candidate.get('parent_candidate') is None
    assert candidate['proposal'] == proposal['id'] and candidate['source_snapshot'] == source['id']
    assert candidate['protections'] == source['protections']
    assert candidate['artifact']['sha256'] != source['artifact']['sha256']
    assert len(proposal['attempts']) == 1 and proposal['attempts'][0]['state'] == 'completed'
    assert proposal['payload_sha256'] == digest(request['payload'])
    patch = (request['payload']['content'] if route == 'dx100-patch'
             else proposal['interpretation']['patch'])
    assert hashlib.sha256(patch.encode()).hexdigest() == candidate['diff_sha256']
    if route == 'dx100-patch':
        assert proposal.get('repair_budget') is None and 'provider' not in proposal
    else:
        budget = proposal['repair_budget']
        attempt = proposal['attempts'][0]['provider']
        assert budget['repairs'] == 0 and attempt['state'] == 'completed' and attempt['returncode'] == 0
        assert budget['used_seconds'] == attempt['host_wall_s']
    historical = request['parameters']['supporting_profile_packages']
    assert len(historical) == 2 and len(set(historical)) == 2 and package['id'] in historical
    assert all(records[key]['context']['threads'] == 4 for key in historical)
    runtime = {'version': 1, 'environment': {
        'OMP_NUM_THREADS': '1', 'OMP_DYNAMIC': 'FALSE', 'OMP_PROC_BIND': 'close', 'OMP_PLACES': 'cores',
        'OMP_THREAD_LIMIT': None, 'OMP_WAIT_POLICY': None, 'GOMP_SPINCOUNT': None, 'GOMP_CPU_AFFINITY': None}}
    reassessment = {'version': 1, 'kind': 'native_candidate_reassessment', 'origin': {
        'proposal': reference(proposal), 'candidate': reference(candidate), 'profile_package': reference(package),
        'source_snapshot': reference(source), 'request_sha256': digest(request),
        'baseline_packages': [reference(records[key]) for key in historical]},
        'assessment': {'protocol': {'id': None, 'sha256': None},
                       'packages': [{'id': None, 'sha256': None}, {'id': None, 'sha256': None}]},
        'transition': {'from_threads': 4, 'to_threads': 1, 'native_runtime': runtime}}
    identifier = 'bfs-native-acceptance-20260927-' + route + '-a1'
    raw = '/data/yanruj/EvolveSWDB_runs/' + identifier
    inputs = {'id': identifier, 'candidate': candidate['id'], 'proposal': {'path': None, 'sha256': None},
        'reassessment': {'path': None, 'sha256': None}, 'packages': [None, None], 'protocol': None,
        'lane': None, 'records': raw + '.dispatch/records', 'runs_dir': raw,
        'source_runs_dir': '/data1/yanruj/EvolveSWDB_sources/' + identifier,
        'build_root': '/data1/yanruj/EvolveSWDB_builds/' + identifier}
    admission = {'format': 'swdb.bfs.native-campaign-admission.v1', 'id': identifier,
        'prepared_at': None, 'code_commit': None, 'runtime': None, 'inputs': inputs,
        'bounds': NATIVE_BOUNDS, 'linux_proof': {'path': None, 'sha256': None}}
    readiness = {'created': '2026-09-27', 'route': route, 'state': 'preparation_only',
        'proposal': reference(proposal), 'candidate': reference(candidate),
        'candidate_artifact': candidate['artifact'], 'diff': {'path': candidate['diff'], 'sha256': candidate['diff_sha256']},
        'request_sha256': digest(request), 'patch_sha256': hashlib.sha256(patch.encode()).hexdigest(),
        'repair_budget_preserved': proposal.get('repair_budget'),
        'local_checks': ['record identity', 'initial candidate state', 'one completed rewrite',
                         'payload digest', 'selected source protection equality', 'retained patch digest', 'provider budget provenance'],
        'remote_source_reopened': False, 'patch_replay_executed': False, 'acceptance': False,
        'unresolved': ['actual T15 source-specific simulator packages',
            'source-specific prepare and publish with original 319-study revalidation',
            'frozen source-specific one-thread protocol and two fresh baseline packages with canonical digests',
            'reviewed pristine native runtime commit/full Git manifest/Python identity',
            'matching native_campaign_owned_cleanup Linux proof and independent closure',
            'current helper comparison, socket and legacy leases, capacity and disk reserves',
            'complete Git-carried record view including required .cc artifacts',
            'remote original source/candidate/diff reopening and bounded patch replay',
            'original wrapper clock/pane identity, sealed admission and closure operator']}
    return {'proposal.json': request, 'reassessment.template.json': reassessment,
            'admission.template.json': admission, 'readiness.json': readiness}


def main():
    records = {}
    for path in (ROOT / 'records').rglob('*.yaml'):
        record = yaml.safe_load(path.read_text())
        if isinstance(record, dict) and 'id' in record:
            records[record['id']] = record
    for route in ('dx100-patch', 'upstream-instructions'):
        folder = HERE / route
        folder.mkdir(exist_ok=True)
        for name, data in build(route, records).items():
            path = folder / name
            raw = (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
            if path.exists() and path.read_bytes() != raw:
                raise ValueError('refusing to overwrite changed retained template: ' + str(path))
            if not path.exists():
                with path.open('xb') as stream:
                    stream.write(raw)
        print(route + ': metadata prepared; source replay and acceptance remain pending')


if __name__ == '__main__':
    main()
