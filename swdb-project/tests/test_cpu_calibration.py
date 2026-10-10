"""CPU calibration through runner/import commands. Created 2026-10-06 ET.

Updated 2026-10-09 23:10 ET (code review of tickets 07/11): binding tests copy only the
record closure (F10); the runner records the checkout commit and machine record from any
working directory and keeps raw output outside the checkout (F5).
"""
import hashlib
import json

from conftest import run_swdb

MEASURED_T4 = 'mbit10.cpu.lanl20261006a2.t4'


def closure_records(tmp_path, *roots):
    """The exact reachable records instead of the ~1 GB catalog (F10)."""
    from conftest import make_records
    return make_records(tmp_path).copy_closure(*roots).path


def receipt():
    def cell(threads, shape, chains, accesses, useful):
        return {'threads': threads, 'shape': shape, 'chains': chains,
                'trials': [{'seconds': 2.0, 'accesses': accesses, 'useful_bytes': useful,
                            'helper_bytes': 0, 'iterations': accesses,
                            'worker_iterations': [accesses // threads] * threads,
                            'checksum': 1.0} for _ in range(3)]}
    return {'format': 'swdb.cpu-calibration.v1', 'evidence_kind': 'fixture',
            'machine': 'mbit10', 'context': {'compiler': 'hand-fixture', 'compiler_version': 'none',
            'flags': [], 'commit': 'fixture', 'lane': None, 'host': 'fixture'},
            'settings': {'threads': [1, 2], 'repetitions': 3, 'working_set_bytes': 1024},
            'compute_counts': {},
            'cells': [cell(1, 'stream', 1, 8, 64), cell(2, 'stream', 1, 16, 128),
                      cell(1, 'pointer_chase', 1, 10, 80), cell(1, 'pointer_chase', 2, 20, 160),
                      cell(2, 'pointer_chase', 1, 20, 160), cell(2, 'pointer_chase', 2, 40, 320),
                      cell(1, 'pointer_chase', 4, 40, 320), cell(1, 'pointer_chase', 8, 80, 640),
                      cell(2, 'pointer_chase', 4, 80, 640), cell(2, 'pointer_chase', 8, 160, 1280)]}


def save_receipt(tmp_path, data):
    data['identity_sha256'] = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'),
                                                      allow_nan=False).encode()).hexdigest()
    path = tmp_path / 'receipt.json'
    path.write_text(json.dumps(data))
    return path


def test_import_preserves_aggregate_byte_rates_and_inferred_concurrency(records, tmp_path):
    path = save_receipt(tmp_path, receipt())
    result = run_swdb('import-cpu-calibration', '--records', records.path, '--receipt', path,
                      '--id-prefix', 'fixture.cpu', '--fixture', '--format', 'json')
    assert result.returncode == 0, result.stdout + result.stderr
    descriptions = json.loads(result.stdout)['descriptions']
    assert [d['threads'] for d in descriptions] == [1, 2]
    assert [d['mechanisms'][1]['parameters']['bytes_per_s']['value'] for d in descriptions] == [32.0, 64.0]
    assert all(d['mechanisms'][0]['parameters']['floating_point_ops_per_s']['value'] is None for d in descriptions)
    concurrency = descriptions[0]['extensions']['cpu_calibration']['effective_requests_per_thread']
    assert concurrency['value'] is None and concurrency['basis'] == 'unknown'
    curve = descriptions[0]['extensions']['cpu_calibration']['concurrency_curve']
    assert curve[1]['effective_requests_per_thread']['median'] == 2.0
    assert descriptions[0]['extensions']['cpu_calibration']['plateau']['state'] == 'not_established'
    assert descriptions[0]['extensions']['cpu_calibration']['series'][0]['seconds']['median'] == 2.0


def test_runner_bounds_native_work_and_fixture_never_claims_measurement(tmp_path, records):
    output = tmp_path / 'run'
    result = run_swdb('cpu-calibrate', '--records', records.path, '--output', output,
                      '--fixture', '--threads', '1,2', '--chains', '1,2',
                      '--working-set-bytes', '65536', '--cache-bytes', '32768',
                      '--repetitions', '3', '--min-trial-s', '0.001', '--max-wall-s', '60')
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads((output / 'receipt.json').read_text())
    assert data['evidence_kind'] == 'fixture'
    assert set(c['shape'] for c in data['cells']) >= {
        'stream', 'single_valued_indirect', 'ranged_indirect', 'pointer_chase',
        'data_dependent_merge', 'cache_stream', 'compute_integer', 'compute_floating_point',
        'compute_branch', 'compute_atomic'}
    assert all(len(c['trials']) == 3 for c in data['cells'])
    compute = [c for c in data['cells'] if c['shape'].startswith('compute_')]
    assert all(c['footprint_bytes'] == (8 * c['threads'] if c['shape'] == 'compute_atomic' else 0)
               for c in compute)
    assert all(c['requested_working_set_bytes'] == 65536 for c in compute)
    assert all('scalar state' in c['scope'] for c in compute)
    assert all(t['seconds'] > 0 and len(t['worker_iterations']) == c['threads']
               for c in data['cells'] for t in c['trials'])
    imported = run_swdb('import-cpu-calibration', '--records', records.path, '--receipt',
                        output / 'receipt.json', '--id-prefix', 'fixture.runner', '--fixture')
    assert imported.returncode == 0, imported.stdout + imported.stderr
    target = json.loads(imported.stdout)['descriptions'][0]
    assert target['mechanisms'][1]['parameters']['bytes_per_s']['basis'] == 'reported'
    excessive = run_swdb('cpu-calibrate', '--records', records.path, '--output', tmp_path / 'bad',
                         '--fixture', '--working-set-bytes', str(2 * 1024**3))
    assert excessive.returncode != 0 and not (tmp_path / 'bad').exists()


def test_import_source_normalized_compute_counts_and_cache_scope(records, tmp_path):
    data = receipt()
    data['settings']['cache_bytes'] = 128
    data['context']['last_level_cache'] = {'capacity_bytes': 256, 'level': 3,
                                           'sharing': 'fixture socket', 'basis': 'reported'}
    compute = {'threads': 1, 'shape': 'compute_floating_point', 'chains': 1,
               'trials': [{'seconds': 2.0, 'iterations': 10, 'worker_iterations': [10],
                            'accesses': 0, 'useful_bytes': 0, 'helper_bytes': 0,
                            'checksum': 1.0} for _ in range(3)]}
    data['cells'].append(compute)
    data['compute_counts']['floating_point'] = {'level': 'source_normalized_ir',
        'per_iteration': 8, 'per_invocation': 3, 'basis': 'reported',
        'validation_points': [[32, 259], [64, 515], [96, 771]],
        'source_sha256': 'fixture', 'characterization_sha256': ['fixture']}
    cache = {'threads': 1, 'shape': 'cache_stream', 'chains': 1, 'footprint_bytes': 128,
             'trials': [{'seconds': 2.0, 'iterations': 8, 'worker_iterations': [8],
                        'accesses': 16, 'useful_bytes': 64, 'helper_bytes': 0,
                        'checksum': 1.0} for _ in range(3)]}
    data['cells'].append(cache)
    result = run_swdb('import-cpu-calibration', '--records', records.path, '--receipt',
                      save_receipt(tmp_path, data), '--id-prefix', 'fixture.compute', '--fixture')
    assert result.returncode == 0, result.stdout + result.stderr
    target = json.loads(result.stdout)['descriptions'][0]
    mechanisms = {m['model']: m['parameters'] for m in target['mechanisms']}
    assert mechanisms['compute_throughput']['floating_point_ops_per_s']['value'] == 41.5
    assert mechanisms['cache_fit']['capacity_bytes']['value'] == 256
    assert mechanisms['cache_fit']['bytes_per_s']['value'] == 32.0
    assert mechanisms['cache_fit']['cold_bytes_per_s']['value'] is None
    assert mechanisms['requests_in_flight_latency']['dependent_latency_s']['value'] == .2
    assert target['extensions']['cpu_calibration']['cache_scope']['footprint_bytes'] == 128


def test_import_refuses_relabelled_native_and_invalid_trials_atomically(records, tmp_path):
    for index, change in enumerate(('native', 'seconds', 'balance')):
        data = receipt()
        if change == 'native':
            data['evidence_kind'] = 'native'
        elif change == 'seconds':
            data['cells'][0]['trials'][0]['seconds'] = 0
        else:
            data['cells'][1]['trials'][0]['worker_iterations'] = [15, 1]
        folder = tmp_path / str(index)
        folder.mkdir()
        result = run_swdb('import-cpu-calibration', '--records', records.path, '--receipt',
                          save_receipt(folder, data), '--id-prefix', 'bad.' + change, '--fixture')
        assert result.returncode != 0
        assert not list(records.path.rglob('bad.*.yaml'))


def test_runner_interrupt_terminates_native_child_group(records, tmp_path):
    import os
    import signal
    import subprocess
    import sys
    import time
    from conftest import REPO

    output = tmp_path / 'interrupted'
    runner = subprocess.Popen([sys.executable, '-m', 'swdb', 'cpu-calibrate', '--records',
        str(records.path), '--output', str(output), '--fixture', '--threads', '1',
        '--chains', '1', '--working-set-bytes', '65536', '--cache-bytes', '32768',
        '--repetitions', '11', '--min-trial-s', '1', '--max-wall-s', '60'],
        cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    child = None
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and runner.poll() is None:
            listing = subprocess.run(['ps', '-axo', 'pid=,ppid=,command='], capture_output=True,
                                     text=True, check=True).stdout
            for line in listing.splitlines():
                fields = line.strip().split(None, 2)
                if len(fields) == 3 and int(fields[1]) == runner.pid and fields[2].startswith(str(output / 'cpu-calibration') + ' '):
                    child = int(fields[0])
                    break
            if child:
                break
            time.sleep(.05)
        assert child is not None, 'native child never started'
        runner.send_signal(signal.SIGTERM)
        stdout, stderr = runner.communicate(timeout=10)
        assert runner.returncode != 0
        assert not (output / 'receipt.json').exists()
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            try:
                os.kill(child, 0)
            except ProcessLookupError:
                break
            time.sleep(.05)
        else:
            raise AssertionError('native child survived runner termination')
    finally:
        if runner.poll() is None:
            runner.kill()
            runner.communicate()
        if child:
            try:
                os.killpg(child, signal.SIGKILL)
            except ProcessLookupError:
                pass


def test_import_admits_only_recorded_constructed_work_plateau(records, tmp_path):
    data = receipt()
    for cell in data['cells']:
        if cell['shape'] == 'pointer_chase' and cell['chains'] >= 4:
            for trial in cell['trials']:
                trial['seconds'] = cell['chains']
    result = run_swdb('import-cpu-calibration', '--records', records.path, '--receipt',
                      save_receipt(tmp_path, data), '--id-prefix', 'fixture.plateau', '--fixture')
    assert result.returncode == 0, result.stdout + result.stderr
    description = json.loads(result.stdout)['descriptions'][0]
    facts = next(m['parameters'] for m in description['mechanisms']
                 if m['model'] == 'requests_in_flight_latency')
    assert facts['effective_requests_per_thread']['value'] == 2.0
    assert facts['effective_requests_per_thread']['basis'] == 'inferred'
    plateau = description['extensions']['cpu_calibration']['plateau']
    assert plateau['state'] == 'established_for_constructed_work'
    assert [p['chains'] for p in plateau['points']] == [2, 4, 8]
    assert plateau['relative_range'] == 0.0



def test_import_preserves_json_scientific_numbers(records, tmp_path):
    data = receipt()
    for cell in data['cells']:
        for trial in cell['trials']:
            trial['seconds'] = 1e-6
            trial['checksum'] = 1e20
    result = run_swdb('import-cpu-calibration', '--records', records.path, '--receipt',
                      save_receipt(tmp_path, data), '--id-prefix', 'fixture.scientific', '--fixture')
    assert result.returncode == 0, result.stdout + result.stderr
    description = json.loads(result.stdout)['descriptions'][0]
    assert description['mechanisms'][1]['parameters']['bytes_per_s']['value'] == 64000000.0


def test_merge_rate_counts_repeated_head_read_source_accesses(records, tmp_path):
    output = tmp_path / 'merge-count'
    result = run_swdb('cpu-calibrate', '--records', records.path, '--output', output,
        '--fixture', '--threads', '1', '--chains', '1', '--working-set-bytes', '1024',
        '--cache-bytes', '1024', '--repetitions', '3', '--min-trial-s', '0.000000001')
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads((output / 'receipt.json').read_text())
    merge = next(c for c in data['cells'] if c['shape'] == 'data_dependent_merge')
    # 128 merged outputs:127 comparisons each read two heads, reread the chosen
    # head and write it; one tail element reads and writes once:127*4+2=510.
    assert merge['passes'] == 1
    assert all(t['iterations'] == 128 and t['accesses'] == 510 and
               t['useful_bytes'] == 2040 for t in merge['trials'])


def test_extended_chain_sweep_keeps_footprint_and_rejects_unbounded_chain_count(records, tmp_path):
    output = tmp_path / 'extended'
    result = run_swdb('cpu-calibrate', '--records', records.path, '--output', output,
        '--fixture', '--threads', '1', '--chains', '1,16,32,64,128',
        '--working-set-bytes', '65536', '--cache-bytes', '32768', '--repetitions', '3',
        '--min-trial-s', '0.001', '--max-wall-s', '60')
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads((output / 'receipt.json').read_text())
    pointer = [c for c in data['cells'] if c['shape'] == 'pointer_chase']
    assert [c['chains'] for c in pointer] == [1, 16, 32, 64, 128]
    assert all(c['footprint_bytes'] == 65536 for c in pointer)
    too_many = run_swdb('cpu-calibrate', '--records', records.path, '--output', tmp_path / 'bad-256',
                        '--fixture', '--chains', '1,256')
    assert too_many.returncode != 0 and not (tmp_path / 'bad-256').exists()


def test_import_bad_receipt_is_readable_failure_without_writes(records, tmp_path):
    for index, text in enumerate(('{broken', '[]')):
        path = tmp_path / f'bad-{index}.json'
        path.write_text(text)
        result = run_swdb('import-cpu-calibration', '--records', records.path, '--receipt', path,
                          '--id-prefix', 'bad.parse', '--fixture')
        assert result.returncode != 0
        assert 'Traceback' not in result.stderr
        assert 'calibration receipt' in result.stderr
        assert not list(records.path.rglob('bad.parse*.yaml'))


def test_bind_measured_description_pins_typed_calibration_without_rewriting_source(tmp_path):
    import yaml
    records = closure_records(tmp_path, MEASURED_T4)
    old = records / 'target_descriptions/mbit10.cpu.lanl20261006a2.t4.yaml'
    before = old.read_bytes()
    result = run_swdb('bind-cpu-calibration', '--records', records,
        '--target-description', 'mbit10.cpu.lanl20261006a2.t4',
        '--id-prefix', 'fixture.bound.native', '--format', 'json')
    assert result.returncode == 0, result.stdout + result.stderr
    target = json.loads(result.stdout)['descriptions'][0]
    calibration_id = target['calibration_sources'][0]
    evidence = yaml.safe_load((records / 'cpu_calibrations' / (calibration_id + '.yaml')).read_text())
    assert evidence['kind'] == 'cpu_calibration' and evidence['evidence_kind'] == 'native'
    assert evidence['receipt_sha256'] == target['extensions']['cpu_calibration']['receipt_sha256']
    assert evidence['threads'] == 4
    assert evidence['series'] and all(s['seconds']['repetitions'] == 7 for s in evidence['series'])
    assert evidence['identity_sha256'] == hashlib.sha256(json.dumps(
        {k:v for k,v in evidence.items() if k != 'identity_sha256'}, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    original = yaml.safe_load(before)
    assert old.read_bytes() == before and target['version'] != original['version']
    assert target['mechanisms'] == original['mechanisms']
    freeze = tmp_path / 'freeze.yaml'
    freeze.write_text(yaml.safe_dump({'message_version': '1.0', 'id': 'fixture.measured.t4',
        'version': 1, 'settings': {'mode': 'estimated', 'estimator_version': 'swdb.analytic.v1',
        'target_description': target['id'], 'inputs': ['kron-g16-k16'],
        'roi': 'fixture.stream.v1', 'threads': 4}}, sort_keys=False))
    frozen = run_swdb('freeze-protocol', freeze, '--records', records, '--format', 'json')
    assert frozen.returncode == 0, frozen.stdout + frozen.stderr
    protocol = json.loads(frozen.stdout)
    assert protocol['settings']['target_description']['snapshot'] == target
    assert calibration_id in protocol['settings']['dependency_identities']
    clean = run_swdb('validate', '--records', records)
    assert clean.returncode == 0, clean.stdout + clean.stderr
    evidence['series'][0]['trials'][0]['seconds'] *= 2
    (records / 'cpu_calibrations' / (calibration_id + '.yaml')).write_text(yaml.safe_dump(evidence, sort_keys=False))
    invalid = run_swdb('validate', '--records', records)
    assert invalid.returncode != 0 and 'identity_sha256' in invalid.stdout + invalid.stderr


def test_bind_count_equivalence_preserves_measured_trials_and_versions_numerators(tmp_path):
    import yaml
    from conftest import REPO
    records = closure_records(tmp_path, MEASURED_T4)
    source = records / 'target_descriptions/mbit10.cpu.lanl20261006a2.t4.yaml'
    original_bytes = source.read_bytes()
    original = yaml.safe_load(original_bytes)
    proof = REPO / '.scratch/lanl-db-analytic-eval-2026-10-06/evidence/cpu-count-equivalence-mbit10-20261006-a1.json'
    result = run_swdb('bind-cpu-calibration', '--records', records,
        '--target-description', original['id'], '--id-prefix', 'fixture.bound.counted',
        '--count-equivalence', proof, '--format', 'json')
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    target, evidence = data['descriptions'][0], data['calibrations'][0]
    before = original['extensions']['cpu_calibration']
    after = target['extensions']['cpu_calibration']
    assert source.read_bytes() == original_bytes
    assert [s['trials'] for s in before['series']] == [s['trials'] for s in after['series']]
    assert all(c['pipeline']['version'] == 'source-normalized-v2' for c in after['compute_counts'].values())
    assert evidence['lineage']['original_compute_counts'] == before['compute_counts']
    assert evidence['source_count_equivalence']['timings_rerun'] is False
    assert evidence['source_count_equivalence']['previous_receipt_sha256'] != evidence['receipt_sha256']
    old = next(m['parameters'] for m in original['mechanisms'] if m['model'] == 'compute_throughput')
    new = next(m['parameters'] for m in target['mechanisms'] if m['model'] == 'compute_throughput')
    assert {k:v['value'] for k,v in old.items()} == {k:v['value'] for k,v in new.items()}
    corrupt = json.loads(proof.read_text())
    corrupt['equivalence']['source_sha256'] = '0' * 64
    corrupt['equivalence']['identity_sha256'] = hashlib.sha256(json.dumps(
        {k:v for k,v in corrupt['equivalence'].items() if k != 'identity_sha256'}, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    corrupt['identity_sha256'] = hashlib.sha256(json.dumps(
        {k:v for k,v in corrupt.items() if k != 'identity_sha256'}, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    bad = tmp_path / 'bad-equivalence.json'
    bad.write_text(json.dumps(corrupt))
    rejected = run_swdb('bind-cpu-calibration', '--records', records,
        '--target-description', original['id'], '--id-prefix', 'fixture.bad.counted',
        '--count-equivalence', bad)
    assert rejected.returncode != 0 and 'shared source differ' in rejected.stderr
    assert not list((records / 'cpu_calibrations').glob('fixture.bad.*'))


def test_bind_rejects_empty_or_malformed_count_proof_before_writing(tmp_path):
    records = closure_records(tmp_path, MEASURED_T4)
    for n, text in enumerate(('{}', '[]', 'null', '{')):
        proof = tmp_path / f'bad-{n}.json'
        proof.write_text(text)
        result = run_swdb('bind-cpu-calibration', '--records', records,
            '--target-description', 'mbit10.cpu.lanl20261006a2.t4',
            '--id-prefix', 'fixture.bad.proof' + str(n), '--count-equivalence', proof)
        assert result.returncode != 0 and 'Traceback' not in result.stderr
        assert not list((records / 'cpu_calibrations').glob('fixture.bad.proof*'))


def test_bind_cannot_discard_a_resolved_gem5_calibration_dependency(tmp_path):
    import yaml
    records = closure_records(tmp_path, MEASURED_T4, 'bfs-dx100-smoke-20260925-a6')
    path = records / 'target_descriptions/mbit10.cpu.lanl20261006a2.t4.yaml'
    target = yaml.safe_load(path.read_text())
    target['calibration_sources'] = ['bfs-dx100-smoke-20260925-a6']
    path.write_text(yaml.safe_dump(target, sort_keys=False))
    result = run_swdb('bind-cpu-calibration', '--records', records,
        '--target-description', target['id'], '--id-prefix', 'fixture.bad.gem5')
    assert result.returncode != 0 and 'ADR 0013' in result.stderr
    assert 'bfs-dx100-smoke-20260925-a6' in result.stderr
    assert not list((records / 'cpu_calibrations').glob('fixture.bad.gem5*'))


def test_runner_records_checkout_commit_and_machine_from_any_working_directory(records, tmp_path):
    """F5: a lane launched from another checkout (for example Memacc's socket_lane.sh
    folder) still records this checkout's commit and the machine record it ran under."""
    import os
    import subprocess
    import sys
    from conftest import REPO
    from swdb import artifacts
    from swdb.store import Store
    records.add_stub()
    elsewhere = tmp_path / 'other-working-directory'
    elsewhere.mkdir()
    output = tmp_path / 'run'
    result = subprocess.run([sys.executable, '-m', 'swdb', 'cpu-calibrate', '--records', str(records.path),
        '--output', str(output), '--fixture', '--machine', 'testhost', '--threads', '1', '--chains', '1',
        '--working-set-bytes', '1024', '--cache-bytes', '1024', '--repetitions', '3', '--min-trial-s', '0.000000001'],
        cwd=elsewhere, env={**os.environ, 'PYTHONPATH': str(REPO)}, capture_output=True, text=True, timeout=600)
    assert result.returncode == 0, result.stdout + result.stderr
    context = json.loads((output / 'receipt.json').read_text())['context']
    head = subprocess.run(['git', '-C', str(REPO.parent), 'rev-parse', 'HEAD'], capture_output=True,
                          text=True, check=True).stdout.strip()
    assert context['commit'] == head
    assert context['machine_sha256'] == artifacts.digest(Store(records.path).get('testhost', 'machine'))


def test_runner_keeps_raw_output_outside_the_checkout_and_native_output_in_run_roots(records, tmp_path):
    from conftest import REPO
    inside = REPO.parent / '.swdb-calibration-test-must-not-exist' / 'run'
    refused = run_swdb('cpu-calibrate', '--records', records.path, '--output', inside, '--fixture')
    assert refused.returncode != 0 and 'outside the Git checkout' in refused.stderr, refused.stderr
    assert not inside.parent.exists()
    native = run_swdb('cpu-calibrate', '--records', records.path, '--output', tmp_path / 'native-run',
                      '--llvm-bin', tmp_path)
    assert native.returncode != 0 and 'registered run root' in native.stderr, native.stderr
    assert not (tmp_path / 'native-run').exists()
