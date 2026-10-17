"""All services.v2 families bound together, then one estimate (seam 1). Created: 2026-10-12 ET.

Code review T2 of `cpud/integration` (.scratch/cpu-description-t75-pricing-2026-10-12): each
family had its own seam-1 test; none bound them together the way `services.v2` does. One hand
fixture region executes work from every new family: memory_v2 1-/2-byte stores (beside v1
memory cells), OpenMP a2 `_8u` (beside a1), the library-call family, allocator v2 gross resources
and gross bulk resources. Every rate is a hand fixture, never measured evidence.
"""
import copy
import json
import subprocess
import sys

import pytest

from conftest import run_swdb
from testkit.analytic import digest, freeze_protocol
from testkit.cpu_bulk import native_bulk_receipt
from testkit.cpu_openmp import native_receipt
from testkit.cpu_service import bind, gross_allocator_resource, save_receipt
from test_cpu_library_call_calibration import hand_receipt as library_receipt
from test_cpu_memory_service_binding import import_narrow_stores, narrow_store_counts, setup as memory_setup


def per_run(n):
    return {'value': n, 'basis': 'reported', 'scope': 'per_run'}


def opaque(site, name, n):
    return {'site': site, 'region': 'fixture.region', 'name': name, 'body_counted': False,
            'cost_accounting': 'opaque_callee', 'execution_count': per_run(n)}


def shaped(site, name, field, bins):
    empty = {'known_length_bins': [], 'allocation_lifetime_size_bins': []}
    return {'site': site, 'name': name, 'event': 'allocation', 'execution_count': per_run(sum(n for _, n in bins)),
            'body_counted': False, **empty, field: [{'bytes': b, 'execution_count': per_run(n)} for b, n in bins],
            'unknown_lengths': per_run(0), 'unknown_free_lifetimes': per_run(0), 'scope': 'per_run', 'missing': []}


SHAPED = [(50, 'malloc', 'known_length_bins', [(64, 1)]),
          (51, '_Znam', 'known_length_bins', [(16777216, 1)]),
          (52, '_ZdaPv', 'allocation_lifetime_size_bins', [(16777216, 1)]),
          (60, 'llvm.memmove.p0.p0.i64', 'known_length_bins', [(292, 2)])]


def counts(records):
    """The memory_v2 region (8-byte reads x3, 1-byte stores x4, 2-byte stores x2) plus every family's calls."""
    narrow_store_counts(records)
    char = records.read('workload_characterizations/fixture.counts.yaml')
    char['static_analysis']['source_ir_sha256'] = 'b' * 64   # the OpenMP projection's IR
    char['unmodeled_calls'] = [opaque(29, '__kmpc_dispatch_next_4', 3), opaque(30, '__kmpc_for_static_init_8u', 7),
                               opaque(40, 'strlen', 14), opaque(41, 'indirect-call', 1),
                               *[opaque(site, name, sum(n for _, n in bins)) for site, name, _, bins in SHAPED]]
    for call in char['unmodeled_calls']:
        if call['name'] == 'indirect-call':   # Characterize writes indirect calls without these fields.
            call.pop('body_counted')
            call.pop('cost_accounting')
    char['regions'][0]['call_shape_counts'] = {'format': 'swdb.call-shape-counts.v1', 'scope': 'per_run',
        'calls': [shaped(*row) for row in SHAPED]}
    char.pop('identity_sha256')
    char['identity_sha256'] = digest(char)
    records.write('workload_characterizations/fixture.counts.yaml', char)
    return char


def import_receipt(records, folder, raw, identifier):
    folder.mkdir(exist_ok=True)
    imported = run_swdb('import-cpu-service-calibration', '--records', records.path, '--receipt', save_receipt(folder, raw),
                        '--id', identifier, '--fixture', '--format', 'json')
    assert imported.returncode == 0, imported.stderr + imported.stdout
    return identifier


def openmp(records, tmp_path, char):
    """a1 and a2 receipts plus the projection of sites 29 (dispatch_next_4) and 30 (static_init_8u)."""
    ids = []
    for profile_set, measured in (('a1', None), ('a2', [22])):
        raw = native_receipt(profile_set, measured=measured)
        raw.update(evidence_kind='fixture', machine='testhost')
        ids.append(import_receipt(records, tmp_path / ('omp-' + profile_set), raw, 'fixture.omp.' + profile_set))
    calls = []
    for profile_set, index, site in (('a1', 17, 29), ('a2', 22, 30)):
        call = copy.deepcopy(native_receipt(profile_set)['services'][0]['denominator']['proof']['static_projection']['calls'][index])
        call.update(site=site, region='fixture.region', llvm_function='fixture.omp_outlined')
        calls.append(call)
    projection = {'format': 'swdb.openmp-call-projection.v1', 'characterization': {'id': char['id'], 'sha256': digest(char)},
                  'source_ir_sha256': 'b' * 64, 'source_json_sha256': 'c' * 64, 'all_source_json_sites_cross_checked': True,
                  'calls': calls}
    projection['identity_sha256'] = digest(projection)
    path = tmp_path / 'projection.json'
    path.write_text(json.dumps(projection))
    return ids, path


def gross_bulk(records, tmp_path):
    raw = native_bulk_receipt()
    raw.update(evidence_kind='fixture', machine='testhost')
    raw['settings']['group'] = 'bulk_total_v2'
    for service in raw['services']:
        service['denominator']['basis'] = 'reported'
        service['scope']['residual_policy'] = {'id': 'both_windows_meet_declared_threshold', 'minimum_window_s': .05}
        for trial in service['trials']:
            trial['driver_seconds'] = .00001   # gross .1 s / 1e6 events = 1e-7 s per call
    source = import_receipt(records, tmp_path / 'bulk', raw, 'fixture.bulk.total.source')
    derived = subprocess.run([sys.executable, '-m', 'swdb.cpu_bulk_resource', '--records', str(records.path),
        '--source-calibration', source, '--id', 'fixture.bulk.resource', '--fixture'], capture_output=True, text=True)
    assert derived.returncode == 0, derived.stderr + derived.stdout
    return 'fixture.bulk.resource'


def test_every_services_v2_family_binds_together_and_prices_one_region(records, tmp_path):
    memory_setup(records, tmp_path)
    import_narrow_stores(records, tmp_path)
    char = counts(records)
    omp, projection = openmp(records, tmp_path, char)
    library = import_receipt(records, tmp_path / 'library', library_receipt(), 'fixture.library.calls')
    allocator = gross_allocator_resource(records, tmp_path, 'fixture.allocator.v2', 'allocator_v2', [
        ('malloc', 'malloc', 64, .2), ('new_array', '_Znam', 16777216, .4), ('delete_array', '_ZdaPv', 16777216, .1)])
    bulk = gross_bulk(records, tmp_path)
    calibrations = ['fixture.memory.costs', 'fixture.memory.narrow', *omp, library, allocator, bulk]
    outcome = bind(records, '--target-description', 'fixture.memory.base', '--characterization', 'fixture.counts',
        *[arg for c in calibrations for arg in ('--calibration', c)],
        '--memory-footprint-bytes', '8388608', '--memory-cas-policy', 'max_constructed_success_failure_median',
        '--openmp-projection', projection, '--openmp-next-policy', 'max_constructed_success_failure_median',
        '--bulk-profile-policy', 'max_constructed_profiles_median', '--id', 'fixture.services.v2', '--fixture')
    assert outcome.returncode == 0, outcome.stderr + outcome.stdout
    bound = json.loads(outcome.stdout)
    assert set(calibrations) <= set(bound['calibration_sources'])
    assert all(m['model'] != 'streaming_bandwidth' for m in bound['mechanisms'])
    assert [m['model'] for m in bound['resource_floor_mechanisms']] == ['streaming_bandwidth']

    path = records.path / 'target_descriptions/fixture.services.v2.yaml'
    protocol = freeze_protocol(records.path, tmp_path, path, roi='fixture.stream.v1', input_id='tiny-sym')
    estimated = run_swdb('estimate', '--records', records.path, '--characterization', 'fixture.counts',
        '--target-description', path, '--protocol', protocol, '--id', 'fixture.services.v2.estimate', '--format', 'json')
    assert estimated.returncode == 0, estimated.stderr + estimated.stdout
    region = json.loads(estimated.stdout)['regions'][0]
    rows = region['bounds'] + region['overheads']
    assert all(r['seconds'] is not None for r in rows), [(r['model'], r['missing']) for r in rows if r['seconds'] is None]
    memory = next(r for r in region['bounds'] if r['model'] == 'memory_service_scenario')
    assert memory['seconds'] == pytest.approx(2.5)   # 3 x .1 (v1 read 8) + 4 x .3 (v2 write 1) + 2 x .5 (v2 write 2)
    services = [r for r in rows if r['model'] == 'native_service_costs']
    covered = sorted(c['site'] for r in services for c in r['inputs']['covered_calls'])
    assert covered == [29, 30, 40, 41, 50, 51, 52, 60]   # every family's sites, none left opaque
    assert not any(r['model'] == 'unmodeled_calls' for r in region['bounds'])
    # Hand rates: OpenMP 2e-8 s/call (3 + 7 calls); strlen 2 ns x 14 and indirect-call 1 ns;
    # allocator .2 + .4 + .1 s; bulk 292 B memmove 1e-7 s x 2.
    seconds = sorted(r['seconds'] for r in services)
    assert sum(seconds) == pytest.approx(10 * 2e-8 + 14 * 2e-9 + 1e-9 + .7 + 2e-7)
    assert region['seconds'] == pytest.approx(
        max(r['seconds'] for r in region['bounds']) + sum(r['seconds'] for r in region['overheads']))
    assert records.validate().returncode == 0
