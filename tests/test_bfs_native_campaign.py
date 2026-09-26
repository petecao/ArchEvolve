"""Native campaign admission guards; metadata fixtures only. Updated: 2026-09-25."""
import copy
import runpy

import pytest

from conftest import REPO
from swdb import artifacts, bfs_protocol, profile_package


def seal(kind, name, **payload):
    value = {'kind': kind, 'requested_id': name, 'version': 1, 'supersedes': None,
             'invalidated_comparisons': [], **payload}
    digest = artifacts.digest(bfs_protocol._identity_payload(value))
    value.update(id=name + '.' + digest[:16], identity_sha256=digest)
    return value


@pytest.fixture
def inputs(tmp_path):
    source_root = tmp_path / 'source'; source_root.mkdir()
    (source_root / 'source.cc').write_text('int contract_fixture;\n')
    artifact = artifacts.identify(source_root)
    implementation = {'id': 'dx100-bfs-scalar', 'function': 'DOBFS'}
    records = {'source': {'id': 'source', 'artifact': artifact, 'implementation': implementation['id'],
                          'context': {'function': 'DOBFS'}},
               'baseline': {'id': 'baseline', 'artifact_role': 'source_baseline', 'artifact': artifact,
                            'implementation': implementation['id'], 'source_snapshot': 'source',
                            'context': {'function': 'DOBFS'}}, implementation['id']: implementation}
    packages, workloads = [], []
    lane = 'mbit10-evaluation-node0'
    target = {'id': 'mbit10', 'configuration': {'lane': lane}}
    for family in ('kronecker', 'uniform_random'):
        workload = seal('workload', family, definition={'family': family, 'sources': [0, 1], 'canonical_sha256': 'a' * 64})
        workloads.append(workload); records[workload['id']] = workload
        evaluation = {'id': 'eval-' + family, 'implementation': implementation['id'],
            'outcome': {'state': 'complete'}, 'correctness': {'state': 'passed'},
            'evidence_kind': 'execution', 'request': {}, 'candidate': 'baseline',
            'build': {'binary_sha256': 'b' * 64, 'flags': ['-O3']},
            'context': {'candidate_sha256': artifact['sha256'], 'workload': {'id': workload['id'], 'canonical_sha256': 'a' * 64},
                        'sources': [0, 1], 'target': 'mbit10', 'backend_configuration': {'lane': lane},
                        'threads': 4, 'roi': 'bfs.complete_call.v1'}}
        records[evaluation['id']] = evaluation
        context = profile_package._context(evaluation)
        context.update(primary_binary_sha256=evaluation['build']['binary_sha256'], build=evaluation['build'],
                       workload=evaluation['context']['workload'])
        packages.append({'id': 'pkg-' + family, 'evaluation': evaluation['id'], 'candidate': 'baseline',
            'source_snapshot': 'source', 'implementation': implementation['id'], 'completeness': 'complete',
            'context': context, 'evidence': {'classification': 'execution', 'evaluation_sha256': artifacts.digest(evaluation)}})
    frozen = seal('protocol', 'fixture-policy', settings={'mode': 'native', 'targets': {'baseline': target, 'candidate': target},
        'roi': 'bfs.complete_call.v1', 'threads': 4, 'workloads': [w['id'] for w in workloads]},
        workload_identities={w['id']: w['identity_sha256'] for w in workloads},
        frozen_at='2026-09-25T20:00:00-04:00', state='frozen')
    proposal = {'id': 'operator-proposal', 'message_version': '1.0', 'profile_package': packages[0]['id'],
                'source_snapshot': 'source', 'implementation': implementation['id'], 'source_sha256': artifact['sha256'],
                'producer': {'test_client': True}, 'payload': {'kind': 'patch'}}
    validate = runpy.run_path(str(REPO / 'scripts/bfs_native_campaign.py'))['validate_inputs']
    return validate, packages, frozen, proposal, records, lane, copy.deepcopy(artifact)


def validate(inputs):
    function, packages, frozen, proposal, records, lane, expected = inputs
    return function(packages, frozen, proposal, records.__getitem__, lane, expected)


def test_enriched_package_context_remains_usable(inputs):
    assert set(validate(inputs)) == {'kronecker', 'uniform_random'}


@pytest.mark.parametrize('fault', ['pinned-source', 'source-function', 'candidate-function',
                                  'source-implementation', 'proposal', 'binary', 'build'])
def test_no_repackaged_source_or_relabelled_context_before_dispatch(inputs, fault):
    _, packages, _, _, records, _, expected = inputs
    if fault == 'pinned-source': expected['sha256'] = 'e' * 64
    elif fault == 'source-function': records['source']['context']['function'] = 'DOBFSMAA'
    elif fault == 'candidate-function': records['baseline']['context']['function'] = 'DOBFSMAA'
    elif fault == 'source-implementation': records['source']['implementation'] = 'gapbs-bfs-do'
    elif fault == 'proposal': records['baseline']['proposal'] = 'actual-prior-rewrite'
    elif fault == 'binary': packages[0]['context']['primary_binary_sha256'] = 'c' * 64
    else: packages[0]['context']['build'] = {'flags': ['-O0']}
    with pytest.raises(ValueError, match='pinned application|context evidence changed'):
        validate(inputs)
