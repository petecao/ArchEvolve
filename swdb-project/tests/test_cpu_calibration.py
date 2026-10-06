"""CPU calibration through runner/import commands. Created 2026-10-06 ET."""
import hashlib
import json

from conftest import run_swdb


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
