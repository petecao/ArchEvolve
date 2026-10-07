"""Public model-aware replay of sealed legacy trial scopes. 2026-10-06 ET.

Rates are hand fixtures. Native counts remain immutable; no timing is collected.
"""
import json
import shutil

import pytest
import yaml

from conftest import REPO, run_swdb
from swdb import access, artifacts
from testkit.analytic import target_description, freeze_protocol

CHARACTERIZATION = 'bfs.kron-g16.t1.characterization.objects.a1'
REGION = 'gapbs-bfs-do/serial.433918642650629990'


def legacy_case(records, tmp_path):
    paths = {path.stem: path for path in (REPO / 'records').rglob('*.yaml')}
    pending = ['gapbs-bfs-do', 'kron-g16-k16', 'mbit10']
    copied = set()
    def references(value):
        if isinstance(value, str):
            if value in paths: yield value
        elif isinstance(value, dict):
            for item in value.values(): yield from references(item)
        elif isinstance(value, list):
            for item in value: yield from references(item)
    while pending:
        identifier = pending.pop()
        if identifier in copied: continue
        copied.add(identifier)
        source = paths[identifier]
        destination = records.path / source.relative_to(REPO / 'records')
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        pending.extend(references(access.read_record(source)))
    original = REPO / 'records/workload_characterizations' / (CHARACTERIZATION + '.yaml')
    char = access.read_record(original)
    portable = tmp_path / 'sealed-characterization.json'
    portable.write_text(json.dumps(char))
    target_path = target_description(tmp_path)
    target = yaml.safe_load(target_path.read_text())
    target['mechanisms'] = target['mechanisms'][:1]
    target['mechanisms'].append({'model': 'native_service_costs', 'accounting': 'additive_overhead',
        'selector': {'domain': 'host', 'worker_scope': 'serial_T1',
            'characterization_sha256': artifacts.digest(char), 'calls': [
                {'name': name, 'unit': 'seconds/call', 'bin_kind': dimension,
                 'bins': [{'bytes': size, 'parameter': 'cost_' + str(size)} for size in (8192, 65536, 262144)],
                 'scope_assumption': {'regime': 'fresh_process_repeated_allocate_free_batches', 'transfer_basis': 'inferred'}}
                for name, dimension in (('_Znam', 'known_length_bins'), ('_ZdaPv', 'allocation_lifetime_size_bins'))]},
        'parameters': {'cost_' + str(size): {'value': 1e-6, 'basis': 'reported', 'unit': 'seconds/call',
                       'source': 'Independent hand fixture only; not measured allocator latency.'}
                       for size in (8192, 65536, 262144)}})
    target_path.write_text(yaml.safe_dump(target, sort_keys=False))
    protocol = freeze_protocol(records.path, tmp_path, target_path, roi=char['binding']['roi'],
        arguments=char['source']['run_arguments'])
    result = run_swdb('estimate', '--records', records.path, '--characterization', portable,
        '--target-description', target_path, '--protocol', protocol,
        '--id', 'fixture.legacy-scope.estimate', '--format', 'json')
    assert result.returncode == 0, result.stderr + result.stdout
    return char, json.loads(result.stdout)


def test_sealed_registered_trial_scopes_reconcile_before_strict_size_bin_model(records, tmp_path):
    original = REPO / 'records/workload_characterizations' / (CHARACTERIZATION + '.yaml')
    before = original.read_bytes()
    char, estimate = legacy_case(records, tmp_path)
    region = next(row for row in estimate['trials'][0]['regions'] if row['id'] == REGION)
    cost = next(row for row in region['overheads'] if row['model'] == 'native_service_costs')
    assert cost['seconds'] == pytest.approx(8e-6)  # four exact new[] and four delete[] events.
    assert cost['inputs']['covered_calls'] == [{'site': 64, 'execution_count': 4}, {'site': 74, 'execution_count': 4}]
    proofs = estimate['extensions']['legacy_trial_scope_reconciliations']
    assert len(proofs) == 5 and proofs[0]['position'] == 0 and proofs[0]['basis'] == 'inferred'
    assert proofs[0]['characterization_sha256'] == artifacts.digest(char)
    assert proofs[0]['counted_payload_sha256'] == char['binding']['execution_receipt']['counted_payload_sha256']
    assert original.read_bytes() == before
    assert char['trials'][0]['unmodeled_calls'][0]['execution_count']['scope'] == 'per_run'
    assert estimate['seconds'] is None  # Independent opaque costs remain unsupported in this narrow test.
