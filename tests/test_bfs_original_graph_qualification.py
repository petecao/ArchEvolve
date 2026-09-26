"""Legacy graph-oracle evidence stays retrievable, never qualified. Updated: 2026-09-26."""

import copy
import json

import pytest

from swdb import artifacts, bfs_protocol
from swdb.cli import Failure
from swdb.dx100_witness import graph_verification_contract
from test_bfs_protocol import protocol_seed, protocol_setup, _command, _payload


def _dx100_metadata(evaluation, *, legacy):
    """Explicit contract fixture: no simulator execution is represented."""
    evaluation = copy.deepcopy(evaluation)
    context = evaluation['context']
    context.update(application='gapbs', verifier='dx100.bfs.verifier.v1', candidate_build='fixture-compilation')
    evaluation['build']['adapter'] = 'dx100.complete_call.v1' if legacy else 'dx100.complete_call.v2'
    for check in evaluation['correctness']['checks']:
        check.update(verifier=context['verifier'], checker=context['verifier'])
    if not legacy:
        context['graph_verification'] = graph_verification_contract('gapbs')
        context['instrumentation']['graph_verification'] = graph_verification_contract('gapbs')
        reference = {'path': '/explicit/nonexecuted/contract-fixture.cc', 'sha256': 'a'*64}
        context['candidate_driver'] = reference
        context['verifier_source'] = copy.deepcopy(reference)
    return evaluation


def test_public_legacy_complete_call_remains_retrievable_but_comparator_rejects(protocol_setup, tmp_path):
    records, _, _, _, evaluations, request = protocol_setup
    legacy = _dx100_metadata(evaluations['candidate'], legacy=True)
    records.write('evaluations/' + legacy['id'] + '.yaml', legacy)
    retrieved = records.swdb('get', legacy['id'], '--format', 'json')
    assert retrieved.returncode == 0, retrieved.stderr
    assert json.loads(retrieved.stdout) == legacy
    result = _command(records, 'compare-evaluations', _payload(tmp_path, 'legacy-comparison', request), succeeds=False)
    assert result['decision']['state'] == 'rejected' and result['gain_claim'] is False
    assert 'original-adjacency checker treatment' in str(result['decision']['reasons'])


def test_aggregate_cannot_hide_legacy_component_behind_new_oracle_metadata(protocol_setup, tmp_path):
    records, _, _, _, evaluations, request = protocol_setup
    component = _dx100_metadata(evaluations['candidate'], legacy=False)
    component['id'] = 'fixture-new-oracle-component'
    aggregate = copy.deepcopy(component)
    aggregate['id'] = 'fixture-new-oracle-aggregate'
    aggregate['component_evaluations'] = [{'evaluation': component['id'], 'sha256': artifacts.digest(component)}]
    class Lookup:
        def get(self, record_id, kind):
            return component if record_id == component['id'] and kind == 'evaluation' else None
    bfs_protocol._check_verifier_identity(aggregate, Lookup())
    # The aggregate keeps the safe treatment fields while its actual component
    # is an old wrapper. Even a current component digest cannot qualify it.
    component['build']['adapter'] = 'dx100.complete_call.v1'
    component['context'].pop('graph_verification')
    aggregate['component_evaluations'][0]['sha256'] = artifacts.digest(component)
    records.write('evaluations/' + component['id'] + '.yaml', component)
    records.write('evaluations/' + aggregate['id'] + '.yaml', aggregate)
    request['candidate_evaluation'] = aggregate['id']
    with pytest.raises(Failure, match='original-adjacency checker treatment'):
        bfs_protocol._check_verifier_identity(aggregate, Lookup())
    result = _command(records, 'compare-evaluations', _payload(tmp_path, 'legacy-component-comparison', request), succeeds=False)
    assert 'original-adjacency checker treatment' in str(result['decision']['reasons'])
    assert not result['gain_claim']


def test_original_author_traversal_and_native_checker_are_not_migrated(protocol_setup):
    _, _, _, _, evaluations, _ = protocol_setup
    bfs_protocol._check_verifier_identity(evaluations['candidate'])
    author = _dx100_metadata(evaluations['candidate'], legacy=True)
    author['context']['roi'] = 'bfs.dx100.traversal.v1'
    author['context'].pop('candidate_build')
    author['build']['adapter'] = 'dx100.author_artifact.v1'
    bfs_protocol._check_verifier_identity(author)
