"""Host observations and disposable raw-output fixtures only. 2026-10-03 ET."""
import copy
import json
from pathlib import Path
import socket
from types import SimpleNamespace

import pytest

from swdb import artifacts, bfs_coverage, dispatch_preflight as admission, retention, workflow
from swdb.cli import Failure
from swdb.store import Store
from test_dx100 import case
from test_dx100_gzip_trace import gzip_request


def observation(**fields):
    return {'disk': '/data1', 'free_bytes': 22 * admission.GIB, 'memory_node': 1,
            'free_memory_bytes': 4 * admission.GIB, **fields}


def test_preflight_exact_boundary_and_selected_memory_node():
    result = admission.check('/data1/yanruj/EvolveSWDB_runs', 'mbit10-evaluation-node1', observation=observation())
    assert result['state'] == 'admitted' and result['memory_node'] == 1
    assert result['planned_raw_bytes'] == 2 * admission.GIB
    with pytest.raises(Failure, match='memory node'):
        admission.check('/data1/yanruj/EvolveSWDB_runs', 'mbit10-evaluation-node0', observation=observation())
    with pytest.raises(Failure, match='requires'):
        admission.check('/data1/yanruj/EvolveSWDB_runs', 'mbit10-evaluation-node1', observation=observation(free_memory_bytes=4 * admission.GIB - 1))


def test_preflight_refuses_and_names_alternate_without_switching():
    with pytest.raises(Failure, match='/data/yanruj/EvolveSWDB_runs'):
        admission.check('/data1/yanruj/EvolveSWDB_runs', 'mbit10-evaluation-node1',
            observation=observation(free_bytes=22 * admission.GIB - 1, secondary_free_bytes=22 * admission.GIB))
    result = admission.check('/data/yanruj/EvolveSWDB_runs', 'mbit10-evaluation-node1',
        storage_bytes=30 * admission.GIB, memory_bytes=48 * admission.GIB,
        observation=observation(disk='/data', free_bytes=50 * admission.GIB, free_memory_bytes=48 * admission.GIB))
    assert result['disk'] == '/data' and result['memory_budget_bytes'] == 48 * admission.GIB


def evaluation(rid, folder):
    return workflow.record('evaluation', rid, request={}, outcome={'state': 'complete', 'stage': 'execution', 'reason': None},
        stages=[], timing=[], correctness={'state': 'passed', 'checks': []}, profiling={},
        raw_artifacts=[{'path': str(folder), 'kind': 'dx100_execute'}], evidence_kind='contract_fixture', gain_claim=False)


@pytest.fixture
def raw_case(tmp_path):
    records = tmp_path / 'records'
    records.mkdir()
    folder = tmp_path / 'runs' / 'run'
    folder.mkdir(parents=True)
    trace = folder / 'roi-debug.trace.gz'
    trace.write_bytes(b'fixture bulky compressed output')
    compact = folder / 'simulation.log'
    compact.write_text('Verification: PASS\n')
    data = evaluation('fixture-run', folder)
    data['correctness']['checks'] = [{'output': {'path': str(compact), 'sha256': artifacts.file_hash(compact)}}]
    workflow.persist(records, data, create=True)
    return records, folder, trace, compact


def args(records, **fields):
    return SimpleNamespace(**{'records': records, 'db': None, 'dry_run': False, 'approve': None, 'apply': None, **fields})


def test_dry_run_approval_exact_apply_and_reader_custody(raw_case, tmp_path):
    records, folder, trace, compact = raw_case
    before = Store(records).get('fixture-run')
    target = tmp_path / 'listing.json'
    result = retention.prune(args(records, dry_run=True, output=target, run_roots=[folder.parent]))
    assert trace.is_file() and compact.is_file() and result['deleted'] == []
    table = {Path(row['path']).name: row for row in result['files']}
    assert table[trace.name]['class'] == 'bulky' and table[trace.name]['evaluations'] == ['fixture-run']
    assert table[compact.name]['class'] == 'compact' and not table[compact.name]['proposed']
    with pytest.raises(Failure, match='without recorded'):
        retention.prune(args(records, apply=target))
    retention.prune(args(records, approve=target))
    reference = {'path': str(trace), 'sha256': artifacts.file_hash(trace)}
    result = retention.prune(args(records, apply=target))
    assert result['deleted'] == [{'path': str(trace), 'sha256': reference['sha256'], 'bytes': len(b'fixture bulky compressed output')}]
    assert not trace.exists() and compact.exists() and Store(records).get('fixture-run') == before
    store = Store(records)
    assert retention.retained(store, reference, 'fixture-run')['state'] == 'pruned, sha256 retained'
    assert retention.retained(store, {**reference, 'sha256': 'f' * 64}, 'fixture-run') is None
    assert bfs_coverage._availability([{'file': reference}], socket.gethostname().split('.')[0], store)[0]['state'] == 'pruned, sha256 retained'
    assert bfs_coverage._availability([{'file': reference}], socket.gethostname().split('.')[0], Store(tmp_path / 'empty'))[0]['state'] == 'missing'


def test_input_precedence_and_stale_approved_listing(raw_case, tmp_path):
    records, folder, trace, compact = raw_case
    store = Store(records)
    refs = [{'kind': 'protocol', 'field': 'settings.input', 'record': 'frozen', 'path': str(trace)}]
    assert retention.classify(trace, refs) == 'input'
    refs = [{'kind': 'evaluation', 'field': 'correctness.witness.path', 'record': 'run', 'path': str(trace)}]
    assert retention.classify(trace, refs) == 'compact'
    target = tmp_path / 'listing.json'
    retention.prune(args(records, dry_run=True, output=target, run_roots=[folder]))
    retention.prune(args(records, approve=target))
    trace.write_bytes(b'replacement data')
    with pytest.raises(Failure, match='changed'):
        retention.prune(args(records, apply=target))
    assert trace.read_bytes() == b'replacement data'


def test_automatic_checkpoint_only_after_pass_and_team_claim_keeps_trace(raw_case):
    records, folder, trace, compact = raw_case
    checkpoint = folder / 'checkpoint' / 'cpt.7' / 'system.physmem.store0.pmem'
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b'fixture checkpoint')
    retention.automatic(records, ['fixture-run'], 'execute')
    assert not checkpoint.exists() and trace.exists() and compact.exists()
    claimed = retention.claim(args(records, record_ids=['fixture-run'], audience='Eric,Josh', release=None))
    assert claimed['action'] == 'claim'
    assert retention.team_state(Store(records), 'fixture-run') == 'claimed'
    retention.automatic(records, ['fixture-run'], 'comparison')
    assert trace.exists()
    with pytest.raises(Failure, match='cannot be released'):
        retention.claim(args(records, record_ids=[], audience=None, release='fixture-run'))


def test_directory_receipt_preserves_identity_and_detects_added_file(raw_case):
    records, folder, trace, compact = raw_case
    artifact = artifacts.identify(folder)
    entry = {'path': str(trace), 'sha256': artifacts.file_hash(trace), 'bytes': trace.stat().st_size, 'class': 'bulky'}
    retention._delete(records, 'fixture-run', [entry], 'Disposable fixture prune')
    store = Store(records)
    assert retention.retained_directory(store, artifact)['state'] == 'pruned, sha256 retained'
    assert bfs_coverage._availability([artifact], socket.gethostname().split('.')[0], store)[0]['state'] == 'pruned, sha256 retained'
    (folder / 'unexpected').write_text('new bytes')
    assert retention.retained_directory(store, artifact) is None


def test_comparison_pruning_waits_for_release_and_all_reread_records(raw_case):
    records, folder, trace, compact = raw_case
    retention.automatic(records, ['fixture-run'], 'comparison')
    assert trace.exists()
    aggregate = evaluation('fixture-aggregate', folder.parent / 'aggregate')
    aggregate['component_evaluations'] = [{'evaluation': 'fixture-run', 'sha256': artifacts.digest(Store(records).get('fixture-run'))}]
    workflow.persist(records, aggregate, create=True)
    comparison = workflow.record('comparison_result', 'fixture-comparison', request={},
        baseline_evaluation='fixture-aggregate', candidate_evaluation='fixture-aggregate',
        decision={'state': 'fixture_comparison', 'reasons': []}, gain_claim=False,
        evidence_kind='contract_fixture', metrics={}, region_comparisons=[], finished_at='2026-10-03T10:00:00Z')
    workflow.persist(records, comparison, create=True)
    retention.automatic(records, ['fixture-run'], 'comparison')
    assert trace.exists()  # ArchEvolve does not infer an absent team claim.
    retention.claim(args(records, record_ids=[], audience=None, release='fixture-run'))
    assert not trace.exists() and compact.exists()


def test_failed_checkpoint_keeps_all_payload(raw_case):
    records, folder, trace, compact = raw_case
    data = Store(records).get('fixture-run')
    data['correctness']['state'] = 'failed'
    workflow.persist(records, data)
    checkpoint = folder / 'checkpoint' / 'cpt.8' / 'payload'
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b'failed run evidence')
    retention.automatic(records, ['fixture-run'], 'execute')
    assert checkpoint.exists() and trace.exists()


def test_v2_witness_and_compressed_coverage_revalidate_after_fixture_prune(case, records):
    from swdb import bfs_protocol, dx100_coverage, dx100_witness
    request = gzip_request(case)
    _, invoke, _ = case
    result = invoke('dx100-execute', request)
    assert result['correctness']['state'] == 'passed'
    trace = result['context']['debug_trace']
    retention._delete(records.path, result['id'], [{'path': trace['path'], 'sha256': trace['sha256'],
                      'bytes': trace['bytes'], 'class': 'bulky'}], 'Disposable fixture trace prune')
    store = Store(records.path)
    assert store.get(result['id']) == result
    assert dx100_coverage.validate_trace(result, store=store) == trace
    assert dx100_witness.validate_record_witness(result, store=store)['availability']['state'] == 'verified'
    bfs_protocol._check_verifier_identity(result, store)
    with pytest.raises(Failure, match='regular file'):
        dx100_coverage.validate_trace(result)


def test_durable_intent_failure_deletes_nothing(raw_case, monkeypatch):
    records, folder, trace, compact = raw_case
    reference = {'path': str(trace), 'sha256': artifacts.file_hash(trace), 'bytes': trace.stat().st_size, 'class': 'bulky'}
    def fail_intent(*args, **kwargs):
        assert args[1]['event'] == 'prune_intent'
        raise Failure('fixture record storage failure')
    monkeypatch.setattr(workflow, 'persist', fail_intent)
    with pytest.raises(Failure, match='storage failure'):
        retention._delete(records, 'fixture-run', [reference], 'Disposable fixture')
    assert trace.exists() and compact.exists()


def test_public_apply_refuses_claim_created_after_listing_approval(raw_case, tmp_path):
    import subprocess
    import sys
    records, folder, trace, compact = raw_case
    listing = tmp_path / 'approved-listing.json'
    retention.prune(args(records, dry_run=True, output=listing, run_roots=[folder]))
    retention.prune(args(records, approve=listing))
    claimed = subprocess.run([sys.executable, '-m', 'swdb', 'claim', 'fixture-run', '--audience', 'Eric',
                              '--records', str(records), '--format', 'json'], capture_output=True, text=True)
    assert claimed.returncode == 0, claimed.stderr
    applied = subprocess.run([sys.executable, '-m', 'swdb', 'prune', '--apply', str(listing),
                              '--records', str(records), '--format', 'json'], capture_output=True, text=True)
    assert applied.returncode == 1 and 'team claim' in applied.stderr
    assert trace.exists() and compact.exists()
