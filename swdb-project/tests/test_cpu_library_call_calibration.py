"""Library-call service family through public commands. Created: 2026-10-12 ET.

Seam 2 (runner -> receipt -> import/bind) and seam 1 (bind -> estimate) for C8/C9 of
.scratch/cpu-description-t75-pricing-2026-10-12/spec.md.
"""
import json

from conftest import run_swdb


SERVICES = ['library.strlen', 'library.ostream_put', 'library.ostream_flush', 'library.ostream_insert',
            'library.ostream_insert_unsigned_long', 'library.ctype_widen_init', 'library.indirect_call']


def runner(records, output, llvm, *extra):
    return run_swdb('cpu-service-calibrate', '--service-group', 'library_call', '--records', records.path,
        '--output', output, '--fixture', '--llvm-bin', llvm, '--repetitions', '3', '--min-trial-s', '.002',
        '--max-wall-s', '300', *extra, timeout=400)


def test_runner_counts_one_selected_event_per_iteration_and_times_paired_drivers(records, tmp_path, llvm22, toolchain_flags):
    records.copy_closure('gapbs-bfs-do', 'kron-g16-k16')
    output = tmp_path / 'library-calls'
    result = runner(records, output, llvm22, *toolchain_flags)
    assert result.returncode == 0, result.stderr + result.stdout
    raw = json.loads((output / 'receipt.json').read_text())
    assert raw['evidence_kind'] == 'fixture' and raw['settings']['group'] == 'library_call_v1'
    assert [s['id'] for s in raw['services']] == SERVICES
    abis = [s['scope']['event_abi'] for s in raw['services']]
    assert len(set(abis)) == 7 and abis[-1] == 'indirect-call' and abis[0] == 'strlen'
    proof = raw['services'][0]['denominator']['proof']
    assert proof['format'] == 'swdb.cpu-library-call-count-proof.v1'
    for point in proof['points']:
        # The count driver runs op k with (k + 1) * events iterations: one selected event each.
        assert [c['executions'] for c in point['cells']] == [(k + 1) * point['events'] if point['invoke'] else 0
                                                             for k in range(7)]
    for service in raw['services']:
        assert len(service['trials']) == 3
        assert all(t['events'] > 0 and t['gross_seconds'] > 0 and t['driver_seconds'] > 0 for t in service['trials'])
    flush = raw['services'][2]['scope']
    assert flush['stdout_sink'] == 'regular_file' and flush['transfer_basis'] == 'inferred'
    assert 'first call' in raw['services'][5]['scope']['facet_state']
    assert 'overhead only' in raw['services'][6]['event_definition']
    assert (output / 'sink.out').stat().st_size < 1024 ** 2
    # The binder admits the runner's receipt: one exact scalar selector per counted ABI.
    imported = run_swdb('import-cpu-service-calibration', '--records', records.path, '--receipt', output / 'receipt.json',
        '--id', 'fixture.library.runner', '--fixture', '--format', 'json')
    assert imported.returncode == 0, imported.stderr + imported.stdout
    bound = bind_fixture(records, tmp_path, 'fixture.library.runner', [(abi, 1) for abi in abis])
    assert [c['name'] for c in bound['mechanisms'][-1]['selector']['calls']] == abis


# Exact names from records/workload_characterizations/fga03.t75-*.a2.yaml (and the fga03
# unknowns-summary.json); hand rates in ns; counts like the t75 DOBFS print region.
T75 = [('strlen', 2, 14), ('_ZNSo3putEc', 5, 7), ('_ZNSo5flushEv', 1000, 7),
       ('_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l', 20, 14),
       ('_ZNSo9_M_insertImEERSoT_', 50, 7), ('_ZNKSt5ctypeIcE13_M_widen_initEv', 300, 1), ('indirect-call', 1, 1)]


def hand_receipt(drop=()):
    services = []
    for (service_id, (abi, ns, _count)) in zip(SERVICES, T75):
        if abi in drop:
            continue
        services.append({'id': service_id, 'unit': 'seconds/call', 'event_definition': 'Hand fixture only.',
            'scope': {'event_abi': abi, 'worker_scope': 'serial', 'transfer_basis': 'inferred'},
            'denominator': {'level': 'selected_source_normalized_event', 'basis': 'reported', 'proof': 'Hand fixture.'},
            'trials': [{'events': 1000, 'gross_seconds': 1.0 + ns * 1e-6, 'driver_seconds': 1.0, 'order': order}
                       for order in ('service_first', 'driver_first', 'service_first')]})
    return {'format': 'swdb.cpu-service-calibration.v1', 'evidence_kind': 'fixture', 'machine': 'testhost', 'threads': 1,
        'context': {'compiler_version': 'hand fixture', 'architecture': 'fixture'},
        'settings': {'group': 'library_call_v1', 'repetitions': 3}, 'services': services}


def bind_fixture(records, tmp_path, calibration, calls):
    import yaml
    from testkit.analytic import digest, fixture_characterization, target_description
    from testkit.cpu_service import bind, fact
    records.add_stub()
    base = yaml.safe_load(target_description(tmp_path).read_text())
    base.update(id='fixture.cpu.base', target='testhost')
    records.write('target_descriptions/fixture.cpu.base.yaml', base)
    data = fixture_characterization(records.path, subject_id='stub-impl', input_id='tiny-sym')
    data['regions'] = [{'id': 'fixture.print', 'source_location': {'function': 'fixture', 'line': 1},
        'mapped': True, 'kind': 'serial_remainder', 'access_patterns': [],
        'operation_counts': {k: fact(0 if k != 'floating_point' else 32) for k in ('integer', 'floating_point', 'branch', 'atomic')},
        'dynamic_counts': {'loop_iterations': fact(0)}, 'footprint_bytes': {'value': 0, 'basis': 'reported'},
        'active_workers': {'value': 1, 'basis': 'reported'}, 'worker_context': {'team_sizes': [1], 'measurement': 'Hand fixture.'},
        'accelerator_calls': [], 'address_stream_counts': {}}]
    data['unmodeled_calls'] = [{'site': 40 + i, 'region': 'fixture.print', 'name': name, 'body_counted': False,
        'cost_accounting': 'opaque_callee', 'execution_count': fact(count)} for i, (name, count) in enumerate(calls)]
    for call in data['unmodeled_calls']:
        if call['name'] == 'indirect-call':  # Characterize writes indirect calls without these fields.
            call.pop('body_counted')
            call.pop('cost_accounting')
    data.pop('identity_sha256')
    data['identity_sha256'] = digest(data)
    records.write('workload_characterizations/fixture.counts.yaml', data)
    outcome = bind(records, '--target-description', 'fixture.cpu.base', '--characterization', 'fixture.counts',
        '--calibration', calibration, '--id', 'fixture.cpu.library', '--fixture')
    assert outcome.returncode == 0, outcome.stderr + outcome.stdout
    return json.loads(outcome.stdout)


def bound_estimate(records, tmp_path, drop=()):
    import yaml
    from testkit.analytic import freeze_protocol
    from testkit.cpu_service import save_receipt
    imported = run_swdb('import-cpu-service-calibration', '--records', records.path, '--receipt',
        save_receipt(tmp_path, hand_receipt(drop)), '--id', 'fixture.library.calls', '--fixture')
    assert imported.returncode == 0, imported.stderr + imported.stdout
    bound = bind_fixture(records, tmp_path, 'fixture.library.calls', [(name, count) for name, _ns, count in T75])
    path = tmp_path / 'bound.yaml'
    path.write_text(yaml.safe_dump(bound, sort_keys=False))
    protocol = freeze_protocol(records.path, tmp_path, path, roi='fixture.stream.v1', input_id='tiny-sym')
    result = run_swdb('estimate', '--records', records.path, '--characterization', 'fixture.counts',
        '--target-description', path, '--protocol', protocol, '--id', 'fixture.library.estimate', '--format', 'json')
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)['regions'][0]


def test_bound_library_call_receipts_price_every_t75_print_call(records, tmp_path):
    import pytest
    region = bound_estimate(records, tmp_path)
    service = next(o for o in region['overheads'] if o['model'] == 'native_service_costs')
    # 14*2 + 7*5 + 7*1000 + 14*20 + 7*50 + 1*300 + 1*1 ns = 7994 ns.
    assert service['seconds'] == pytest.approx(7.994e-6)
    assert len(service['inputs']['covered_calls']) == 7
    assert region['seconds'] is not None
    assert not any(b['model'] == 'unmodeled_calls' for b in region['bounds'])


def test_a_call_without_a_receipt_stays_unknown_never_zero(records, tmp_path):
    region = bound_estimate(records, tmp_path, drop=('_ZNSo5flushEv',))
    assert region['seconds'] is None
    unpriced = [b for b in region['bounds'] if b['model'] == 'unmodeled_calls']
    assert len(unpriced) == 1 and unpriced[0]['seconds'] is None
    assert unpriced[0]['missing'] == ['call_cost._ZNSo5flushEv']


def test_native_import_admits_only_the_exact_t75_abis_with_counted_coefficients(records, tmp_path):
    from testkit.cpu_library_call import native_receipt
    from testkit.cpu_service import save_receipt
    records.copy_repo('machines')

    def imported(raw, name):
        return run_swdb('import-cpu-service-calibration', '--records', records.path,
            '--receipt', save_receipt(tmp_path, raw), '--id', name, '--format', 'json')
    accepted = imported(native_receipt(), 'synthetic.native.library')
    assert accepted.returncode == 0, accepted.stderr + accepted.stdout
    assert [s['scope']['event_abi'] for s in json.loads(accepted.stdout)['services']] == [abi for abi, _ns, _n in T75]
    assert records.validate().returncode == 0
    raw = native_receipt()
    raw['services'][2]['scope']['event_abi'] = '_ZNSt3__113basic_ostreamIcNS_11char_traitsIcEEE5flushEv'
    rejected = imported(raw, 'synthetic.native.libcxx')
    assert rejected.returncode != 0 and 'ABI/scope differs' in rejected.stderr
    raw = native_receipt()
    for service in raw['services']:
        service['denominator']['proof']['points'][0]['cells'][6]['executions'] = 0
    rejected = imported(raw, 'synthetic.native.uncounted')
    assert rejected.returncode != 0 and 'coefficient' in rejected.stderr
    raw = native_receipt()
    for service in raw['services']:
        service['denominator']['proof']['points'][1]['other_uncovered_calls'] = {'_ZNSo3putEc': 0}
    rejected = imported(raw, 'synthetic.native.unpaired')
    assert rejected.returncode != 0 and 'outside the selected events' in rejected.stderr


def test_pilot_keeps_headroom_so_warm_trials_still_resolve_min_trial(tmp_path):
    """2026-10-12 ET (ticket 07, mbit10): the strlen pilot driver took 0.052 s, then every warm
    trial 0.042-0.046 s and the validator refused the receipt. The pilot now keeps 1.25x headroom."""
    from swdb.cpu_library_call_calibration import BATCH_EVENTS, pilot_batches
    per_event = .052 / (32768 * BATCH_EVENTS)   # cold pilot rate measured on mbit10
    seen = []

    def timer(batches, order):
        seen.append(batches)
        seconds = batches * BATCH_EVENTS * per_event
        return {'gross_seconds': 2 * seconds, 'driver_seconds': seconds, 'order': order}
    batches = pilot_batches(timer, .05, tmp_path / 'pilot.json')
    assert batches == 65536 and seen[-2:] == [32768, 65536]
    assert batches * BATCH_EVENTS * per_event * .8 >= .05   # a trial 20% faster than the pilot still resolves
    assert json.loads((tmp_path / 'pilot.json').read_text())['driver_seconds'] >= .0625
