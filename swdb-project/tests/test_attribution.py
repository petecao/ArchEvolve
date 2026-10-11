"""Public `swdb attribute` seam (fine-grained attribution spec, seam 1).
Created: 2026-10-11 ET. Fixture counts and snapshots are contract fixtures, never application
evidence: each test writes two tiny source trees, counts them by hand, estimates them through
`swdb estimate`, and checks the attribution record against hand-computed values.
"""
import hashlib
import json

import pytest
import yaml

from conftest import run_swdb
from testkit.analytic import digest, fixture_characterization, target_description

# Baseline kernel: `untouched` loop at lines 3-4, `rewritten` loop at lines 7-8.
BASELINE = """// attribution fixture kernel
void untouched(float *a, int n) {
  for (int i = 0; i < n; ++i)
    a[i] = a[i] * 2.0f;
}
void rewritten(float *a, int n) {
  for (int i = 0; i < n; ++i)
    a[i] = a[i] + 1.0f;
}
"""
# Candidate: only the rewritten loop's two lines change.
CANDIDATE = BASELINE.replace("""  for (int i = 0; i < n; ++i)
    a[i] = a[i] + 1.0f;""", """  for (int i = 0; i < n; i += 2)
    a[i] += 1.0f, a[i + 1] += 1.0f;""")


def count(value, scope='per_call'):
    return {'value': value, 'basis': 'unknown' if value is None else 'reported', 'scope': scope}


def region(rid, path, line, seconds, scope='per_call'):
    """One counted loop. At 1 floating-point op/s, `seconds` operations take `seconds` s."""
    where = {'function': 'fixture', 'line': line, **({} if path is None else {'path': str(path)})}
    return {'id': rid, 'source_location': where,
        'mapped': False, 'kind': 'loop',
        'operation_counts': {'integer': count(0, scope), 'floating_point': count(seconds, scope),
                             'branch': count(0, scope), 'atomic': count(0, scope)},
        'dynamic_counts': {'loop_iterations': count(0, scope)},
        'footprint_bytes': {'value': 0, 'basis': 'reported'},
        'access_patterns': [{'id': rid.replace('/', '.') + '.read', 'source_location': {**where, 'line': line + 1},
            'address_shape': {'value': 'stream', 'basis': 'reported'}, 'stride_bytes': {'value': 4, 'basis': 'reported'},
            'element_bytes': 4, 'update_kind': 'read', 'element_count': count(0, scope), 'bytes_accessed': count(0, scope),
            'observed_address_span_bytes': {'value': 0, 'basis': 'reported'}, 'address_expression': 'a[i]', 'ir_lanes': 1}],
        'accelerator_calls': [], 'address_stream_counts': {}}


def tree(tmp_path, name, text):
    root = tmp_path / 'sources' / name
    root.mkdir(parents=True)
    (root / 'kernel.cpp').write_text(text)
    return root.resolve()


def snapshot(records, rid, root):
    files = []
    for path in sorted(p for p in root.rglob('*') if p.is_file()):
        files.append({'path': path.relative_to(root).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                      'bytes': path.stat().st_size, 'executable': False})
    records.write(f'source_snapshots/{rid}.yaml', {'kind': 'source_snapshot', 'schema_version': '0.4', 'id': rid,
        'status': 'draft', 'created': '2026-10-11', 'updated': '2026-10-11',
        'provenance': [{'id': 'fixture', 'kind': 'source_code', 'description': 'Attribution contract fixture tree.'}],
        'message_version': '1.0', 'producer': {'name': 'attribution-fixture', 'role': 'operator', 'test_client': True},
        'implementation': 'stub-impl', 'application': 'gapbs', 'revision': 'fixture',
        'artifact': {'path': str(root), 'sha256': digest(files), 'files': files},
        'context': {}, 'protections': [], 'regions': []})


def characterization(records, rid, regions, trials=None, input_id='tiny-sym'):
    data = fixture_characterization(records.path, subject_id='stub-impl', input_id=input_id)
    (records.path / 'workload_characterizations/fixture.counts.yaml').unlink()
    data['id'] = rid
    data['regions'] = regions
    if trials is not None:
        data['trials'] = [{'position': i, 'sources': [i], 'regions': rows, 'unmodeled_calls': []}
                          for i, rows in enumerate(trials)]
    data.pop('identity_sha256')
    data['identity_sha256'] = digest(data)
    records.write(f'workload_characterizations/{rid}.yaml', data)


class Case:
    """A copied stub store with a frozen fixture protocol at 1 floating-point op/s."""

    def __init__(self, records, tmp_path):
        records.add_stub()
        self.records, self.tmp_path = records, tmp_path
        self.base_root = tree(tmp_path, 'baseline', BASELINE)
        self.cand_root = tree(tmp_path, 'candidate', CANDIDATE)
        snapshot(records, 'fixture.baseline.source', self.base_root)
        snapshot(records, 'fixture.candidate.source', self.cand_root)
        self.target = target_description(tmp_path)
        data = yaml.safe_load(self.target.read_text())
        data['target'] = 'testhost'
        data['mechanisms'] = data['mechanisms'][:1]
        data['mechanisms'][0]['parameters']['floating_point_ops_per_s']['value'] = 1.0
        self.target.write_text(yaml.safe_dump(data, sort_keys=False))
        self.target_sha256 = digest(data)
        other = records.read('inputs/tiny-sym.yaml')
        other['id'] = 'tiny-sym-b'
        records.write('inputs/tiny-sym-b.yaml', other)
        freeze = tmp_path / 'freeze.yaml'
        freeze.write_text(yaml.safe_dump({'message_version': '1.0', 'id': 'fixture.attribution.protocol', 'version': 1,
            'settings': {'mode': 'estimated', 'estimator_version': 'swdb.analytic.v1', 'target_description': str(self.target),
                         'inputs': ['tiny-sym', 'tiny-sym-b'], 'roi': 'fixture.stream.v1', 'threads': 1}}, sort_keys=False))
        result = run_swdb('freeze-protocol', freeze, '--records', records.path, '--format', 'json')
        assert result.returncode == 0, result.stdout + result.stderr
        self.protocol = json.loads(result.stdout)['id']

    def estimate(self, rid, regions, trials=None, input_id='tiny-sym'):
        characterization(self.records, rid + '.counts', regions, trials, input_id)
        result = run_swdb('estimate', '--records', self.records.path, '--characterization', rid + '.counts',
            '--target-description', self.target, '--protocol', self.protocol, '--id', rid, '--format', 'json')
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)

    def worked_example(self):
        """Baseline 100 s: untouched 40 s, rewritten 60 s. Candidate: rewritten 30 s."""
        b, c = self.base_root / 'kernel.cpp', self.cand_root / 'kernel.cpp'
        self.estimate('fixture.baseline', [region('base.loop.untouched', b, 3, 40), region('base.loop.rewritten', b, 7, 60)])
        self.estimate('fixture.candidate', [region('cand.loop.untouched', c, 3, 40), region('cand.loop.rewritten', c, 7, 30)])

    def attribute(self, rid='fixture.attribution', baseline='fixture.baseline', candidate='fixture.candidate'):
        return run_swdb('attribute', '--records', self.records.path, '--baseline-estimate', baseline,
            '--candidate-estimate', candidate, '--baseline-source', 'fixture.baseline.source',
            '--candidate-source', 'fixture.candidate.source', '--id', rid, '--format', 'json')


@pytest.fixture
def case(records, tmp_path):
    return Case(records, tmp_path)


def attributed(case, **kwargs):
    result = case.attribute(**kwargs)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def groups(report):
    return {g['origin']: g for g in report['groups']}


def test_worked_example_gives_hand_computed_split_and_amdahl_ceiling(case):
    case.worked_example()
    report = attributed(case)
    assert report['format'] == 'swdb.attribution.v1'
    split = groups(report)
    assert split['agent_rewritten']['baseline_seconds'] == pytest.approx(60)
    assert split['agent_rewritten']['candidate_seconds'] == pytest.approx(30)
    assert split['agent_rewritten']['baseline_share'] == pytest.approx(0.6)
    assert split['agent_rewritten']['realized_speedup'] == pytest.approx(2.0)
    assert split['untouched']['baseline_seconds'] == pytest.approx(40)
    assert split['untouched']['candidate_seconds'] == pytest.approx(40)
    assert split['untouched']['baseline_share'] == pytest.approx(0.4)
    assert split['untouched']['drift'] == pytest.approx(1.0)
    assert split['unattributed']['baseline_seconds'] == 0 and split['unattributed']['candidate_seconds'] == 0
    whole = report['whole_program']
    assert whole['baseline_seconds'] == pytest.approx(100) and whole['candidate_seconds'] == pytest.approx(70)
    assert whole['total_speedup'] == pytest.approx(100 / 70)
    assert whole['amdahl_ceiling'] == pytest.approx(2.5)
    labels = {(r['side'], r['region']): r['origin'] for r in report['regions']}
    assert labels == {('baseline', 'base.loop.untouched'): 'untouched', ('baseline', 'base.loop.rewritten'): 'agent_rewritten',
                      ('candidate', 'cand.loop.untouched'): 'untouched', ('candidate', 'cand.loop.rewritten'): 'agent_rewritten'}
    assert [(s['path'], s['baseline_lines'], s['candidate_lines']) for s in report['rewrite_sites']] == [('kernel.cpp', [7, 8], [7, 8])]


def test_loop_without_catalog_id_is_labeled_by_line_and_one_without_a_location_is_unattributed(case):
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    # IDs shaped like the LLVM pass's unmapped loops: no catalog loop ID, only a source line.
    case.estimate('fixture.baseline', [region('unmapped.stub-impl.untouched.3.0.aaaa', b, 3, 40),
        region('unmapped.stub-impl.rewritten.7.0.bbbb', b, 7, 50), region('stub-impl/serial.cccc', None, 0, 10)])
    case.estimate('fixture.candidate', [region('unmapped.stub-impl.untouched.3.0.dddd', c, 3, 40),
        region('unmapped.stub-impl.rewritten.7.0.eeee', c, 7, 25), region('stub-impl/serial.ffff', None, 0, 10)])
    report = attributed(case)
    labels = {r['region']: (r['origin'], r['reason']) for r in report['regions']}
    assert labels['unmapped.stub-impl.rewritten.7.0.eeee'] == ('agent_rewritten', 'overlaps_rewrite_site')
    assert labels['unmapped.stub-impl.untouched.3.0.dddd'] == ('untouched', 'no_changed_line')
    assert labels['stub-impl/serial.ffff'] == ('unattributed', 'no_source_location')
    split = groups(report)
    assert (split['unattributed']['baseline_seconds'], split['unattributed']['candidate_seconds']) == (10, 10)
    assert split['unattributed']['baseline_share'] == pytest.approx(0.1)
    assert split['agent_rewritten']['realized_speedup'] == pytest.approx(2.0)
    assert report['rewrite_sites'][0]['candidate_regions'] == ['unmapped.stub-impl.rewritten.7.0.eeee']
    assert report['rewrite_sites'][0]['baseline_regions'] == ['unmapped.stub-impl.rewritten.7.0.bbbb']


def trials(path, prefix, untouched, rewritten_a, rewritten_b):
    """Rewritten time is split over two loops (lines 7 and 8), so per-region medians differ from group medians."""
    return [[region(prefix + '.untouched', path, 3, u, 'per_trial'), region(prefix + '.rewritten.a', path, 7, ra, 'per_trial'),
             region(prefix + '.rewritten.b', path, 8, rb, 'per_trial')] for u, ra, rb in zip(untouched, rewritten_a, rewritten_b)]


def test_group_seconds_are_per_trial_sums_then_medians_never_rescaled(case):
    # Baseline trials (untouched, rewritten) = (10, 90), (50, 60), (60, 20): totals 100, 110, 80.
    # Medians: total 100, untouched 50, rewritten 60, so the groups add to 110 s, not 100 s.
    # The rewritten loops' own medians are 10 s each: summing region medians would give 20 s.
    base = trials(case.base_root / 'kernel.cpp', 'base', [10, 50, 60], [80, 10, 10], [10, 50, 10])
    # Candidate trials: untouched 10, 50, 60; rewritten 45, 30, 10; totals 55, 80, 70.
    cand = trials(case.cand_root / 'kernel.cpp', 'cand', [10, 50, 60], [40, 5, 5], [5, 25, 5])
    case.estimate('fixture.baseline', base[0], trials=base)
    case.estimate('fixture.candidate', cand[0], trials=cand)
    report = attributed(case)
    split = groups(report)
    assert split['untouched']['baseline_seconds'] == pytest.approx(50)
    assert split['agent_rewritten']['baseline_seconds'] == pytest.approx(60)
    assert split['agent_rewritten']['candidate_seconds'] == pytest.approx(30)
    assert report['whole_program']['baseline_seconds'] == pytest.approx(100)
    assert report['whole_program']['candidate_seconds'] == pytest.approx(70)
    assert split['untouched']['baseline_share'] + split['agent_rewritten']['baseline_share'] == pytest.approx(1.1)
    assert report['whole_program']['amdahl_ceiling'] == pytest.approx(2.0)


def test_unknown_region_nulls_its_group_and_dependent_totals_with_reasons(case):
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    case.estimate('fixture.baseline', [region('base.loop.untouched', b, 3, 40), region('base.loop.rewritten', b, 7, 60)])
    case.estimate('fixture.candidate', [region('cand.loop.untouched', c, 3, 40), region('cand.loop.rewritten', c, 7, None)])
    report = attributed(case)
    split = groups(report)
    rewritten = split['agent_rewritten']
    assert rewritten['baseline_seconds'] == pytest.approx(60) and rewritten['candidate_seconds'] is None
    assert rewritten['realized_speedup'] is None and rewritten['candidate_share'] is None
    assert rewritten['unknown'] == [{'side': 'candidate', 'region': 'cand.loop.rewritten', 'missing': ['operation_counts.floating_point']}]
    assert split['untouched']['candidate_seconds'] == pytest.approx(40) and split['untouched']['drift'] == pytest.approx(1.0)
    assert split['untouched']['unknown'] == []
    whole = report['whole_program']
    assert whole['candidate_seconds'] is None and whole['total_speedup'] is None
    assert whole['amdahl_ceiling'] == pytest.approx(2.5)
    assert whole['unknown'] == rewritten['unknown']


def test_estimates_of_different_inputs_are_refused_and_nothing_is_written(case):
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    case.estimate('fixture.baseline', [region('base.loop', b, 3, 40)])
    case.estimate('fixture.candidate', [region('cand.loop', c, 3, 40)], input_id='tiny-sym-b')
    result = case.attribute()
    assert result.returncode == 1
    assert 'input' in result.stderr and 'refusing' in result.stderr
    assert not (case.records.path / 'attributions').exists()


def test_identical_inputs_give_a_byte_identical_record_that_pins_its_inputs(case):
    case.worked_example()
    first = attributed(case)
    path = case.records.path / 'attributions' / 'fixture.attribution.yaml'
    written = path.read_bytes()
    path.unlink()
    assert attributed(case) == first
    assert path.read_bytes() == written
    store = case.records.path
    assert first['baseline_estimate'] == {'id': 'fixture.baseline', 'sha256': digest(yaml.safe_load((store / 'estimates/fixture.baseline.yaml').read_text()))}
    assert first['candidate_estimate'] == {'id': 'fixture.candidate', 'sha256': digest(yaml.safe_load((store / 'estimates/fixture.candidate.yaml').read_text()))}
    for side in ('baseline', 'candidate'):
        source = yaml.safe_load((store / f'source_snapshots/fixture.{side}.source.yaml').read_text())
        assert first[side + '_source'] == {'kind': 'source_snapshot', 'id': source['id'], 'sha256': digest(source),
                                           'artifact_sha256': source['artifact']['sha256']}
    assert first['target_description'] == {'id': 'fixture.target', 'sha256': case.target_sha256}
    assert first['input'] == 'tiny-sym'


def test_report_validates_and_is_indexed_into_swdb_tables(case):
    case.worked_example()
    attributed(case)
    checked = case.records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr
    db = case.tmp_path / 'index.sqlite'
    rows = run_swdb('sql', 'SELECT attribution, origin, baseline_seconds, candidate_seconds, baseline_share, realized_speedup, drift '
                    'FROM swdb_attribution_groups ORDER BY origin', '--records', case.records.path, '--db', db, '--format', 'json')
    assert rows.returncode == 0, rows.stdout + rows.stderr
    assert json.loads(rows.stdout) == [
        {'attribution': 'fixture.attribution', 'origin': 'agent_rewritten', 'baseline_seconds': 60.0, 'candidate_seconds': 30.0,
         'baseline_share': 0.6, 'realized_speedup': 2.0, 'drift': None},
        {'attribution': 'fixture.attribution', 'origin': 'unattributed', 'baseline_seconds': 0.0, 'candidate_seconds': 0.0,
         'baseline_share': 0.0, 'realized_speedup': None, 'drift': None},
        {'attribution': 'fixture.attribution', 'origin': 'untouched', 'baseline_seconds': 40.0, 'candidate_seconds': 40.0,
         'baseline_share': 0.4, 'realized_speedup': 1.0, 'drift': 1.0}]
    whole = run_swdb('sql', 'SELECT id, baseline_estimate, candidate_estimate, input, total_speedup, amdahl_ceiling FROM swdb_attributions',
                     '--records', case.records.path, '--db', db, '--format', 'json')
    assert json.loads(whole.stdout) == [{'id': 'fixture.attribution', 'baseline_estimate': 'fixture.baseline',
        'candidate_estimate': 'fixture.candidate', 'input': 'tiny-sym', 'total_speedup': pytest.approx(100 / 70), 'amdahl_ceiling': 2.5}]
    labels = run_swdb('sql', "SELECT side, region, origin, path, first_line, last_line FROM swdb_attribution_regions ORDER BY side, region",
                      '--records', case.records.path, '--db', db, '--format', 'json')
    assert json.loads(labels.stdout)[0] == {'side': 'baseline', 'region': 'base.loop.rewritten', 'origin': 'agent_rewritten',
                                            'path': 'kernel.cpp', 'first_line': 7, 'last_line': 8}


def test_validate_rejects_an_edited_report_or_a_changed_pinned_estimate(case):
    case.worked_example()
    attributed(case)
    path = case.records.path / 'attributions' / 'fixture.attribution.yaml'
    original = path.read_text()
    path.write_text(original.replace('amdahl_ceiling: 2.5', 'amdahl_ceiling: 3.0'))
    edited = case.records.validate()
    assert edited.returncode == 1 and 'identity_sha256' in edited.stdout + edited.stderr
    path.write_text(original)
    estimate = case.records.path / 'estimates' / 'fixture.candidate.yaml'
    estimate.write_text(estimate.read_text().replace('status: draft', 'status: accepted', 1))
    changed = case.records.validate()
    assert changed.returncode == 1 and 'candidate_estimate' in changed.stdout + changed.stderr


# Resource floor and floor headroom (ticket 07, spec F6, F7). The floor is
# max(compute bound, useful-bytes bandwidth bound) at the target description's own rates.
def rate(value, unit):
    return {'value': value, 'basis': 'reported', 'source': 'Hand-computed attribution fixture; not a measurement.', 'unit': unit}


# Every rate has a `theoretical_peak_*` twin a million times faster: a floor that read one would be ~0 s.
COMPUTE = {'model': 'compute_throughput', 'parameters': {
    **{c + '_ops_per_s': rate(1.0 if c == 'floating_point' else 1e9, 'operations/s') for c in ('integer', 'floating_point', 'branch', 'atomic')},
    'theoretical_peak_floating_point_ops_per_s': rate(1e6, 'operations/s')}}
BANDWIDTH = {'model': 'streaming_bandwidth', 'parameters': {
    'bytes_per_s': rate(2.0, 'bytes/s'), 'theoretical_peak_bytes_per_s': rate(2e6, 'bytes/s')}}
LATENCY = {'model': 'requests_in_flight_latency', 'parameters': {
    'dependent_latency_s': rate(6.0, 'seconds/load'), 'effective_requests_per_thread': rate(1.0, 'requests/thread')}}


def use_target(case, mechanisms):
    """Re-point the case at a description with these mechanisms and a protocol frozen on it."""
    data = yaml.safe_load(case.target.read_text())
    data['mechanisms'] = mechanisms
    case.target = case.tmp_path / 'floor-target.yaml'
    case.target.write_text(yaml.safe_dump(data, sort_keys=False))
    case.target_sha256 = digest(data)
    freeze = case.tmp_path / 'floor-freeze.yaml'
    freeze.write_text(yaml.safe_dump({'message_version': '1.0', 'id': 'fixture.floor.protocol', 'version': 1,
        'settings': {'mode': 'estimated', 'estimator_version': 'swdb.analytic.v1', 'target_description': str(case.target),
                     'inputs': ['tiny-sym', 'tiny-sym-b'], 'roi': 'fixture.stream.v1', 'threads': 1}}, sort_keys=False))
    result = run_swdb('freeze-protocol', freeze, '--records', case.records.path, '--format', 'json')
    assert result.returncode == 0, result.stdout + result.stderr
    case.protocol = json.loads(result.stdout)['id']


def work(rid, path, line, flops, stream_bytes=0, requests=0, scope='per_call'):
    """A loop with `flops` fp ops (1 s each), `stream_bytes` streamed (2 B/s) and `requests` dependent loads (6 s each)."""
    row = region(rid, path, line, flops, scope)
    stream = row['access_patterns'][0]
    stream['bytes_accessed'] = count(stream_bytes, scope)
    stream['element_count'] = count(stream_bytes // 4, scope)
    row['active_workers'] = {'value': 1, 'basis': 'measured'}
    if requests:
        row['access_patterns'].append({**stream, 'id': stream['id'] + '.gather',
            'address_shape': {'value': 'single_valued_indirect', 'basis': 'reported'},
            'element_count': count(requests, scope), 'bytes_accessed': count(4 * requests, scope), 'address_expression': 'a[idx[i]]'})
    return row


def rows(report, side):
    return {r['region']: r for r in report['regions'] if r['side'] == side}


def test_resource_floor_is_below_the_estimate_and_headroom_names_its_limit(case):
    use_target(case, [COMPUTE, BANDWIDTH, LATENCY])
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    # Baseline rewritten loop: compute 10 s, bandwidth 16 B / 2 = 8 s, latency 10 x 6 = 60 s -> estimate 60 s, floor 10 s.
    case.estimate('fixture.baseline', [work('base.untouched', b, 3, 40), work('base.rewritten', b, 7, 10, 16, 10)])
    # Candidate rewritten loop: compute 4 s, bandwidth 8 s, latency 5 x 6 = 30 s -> estimate 30 s, floor 8 s (bandwidth).
    case.estimate('fixture.candidate', [work('cand.untouched', c, 3, 40), work('cand.rewritten', c, 7, 4, 16, 5)])
    report = attributed(case)
    base, cand = rows(report, 'baseline'), rows(report, 'candidate')
    assert base['base.rewritten']['seconds'] == pytest.approx(60)
    assert base['base.rewritten']['resource_floor']['seconds'] == pytest.approx(10)
    assert base['base.rewritten']['resource_floor']['limiting_term'] == 'compute_throughput'
    floor = cand['cand.rewritten']['resource_floor']
    assert cand['cand.rewritten']['seconds'] == pytest.approx(30)
    assert floor['seconds'] == pytest.approx(8) and floor['limiting_term'] == 'streaming_bandwidth'
    assert {t['model']: t['seconds'] for t in floor['terms']} == pytest.approx({'compute_throughput': 4, 'streaming_bandwidth': 8})
    assert floor['missing'] == []
    assert cand['cand.rewritten']['headroom'] == [{'limit': 'resource_floor', 'value': pytest.approx(3.75), 'reason': None}]
    assert cand['cand.untouched']['headroom'] == [{'limit': 'resource_floor', 'value': pytest.approx(1.0), 'reason': None}]
    for row in report['regions']:
        assert row['resource_floor']['seconds'] <= row['seconds'] + 1e-12
    # Candidate regions only, by floor headroom: the rewritten loop (3.75) before the untouched one (1.0).
    assert [(r['position'], r['side'], r['region'], r['tier'], r['limit']) for r in report['ranking']] == [
        (1, 'candidate', 'cand.rewritten', 'floor_headroom', 'resource_floor'),
        (2, 'candidate', 'cand.untouched', 'floor_headroom', 'resource_floor')]
    assert [r['value'] for r in report['ranking']] == pytest.approx([3.75, 1.0])


def test_a_missing_bandwidth_rate_gives_an_unknown_floor_with_a_reason_not_zero(case):
    # Like the BFS services description: memory is priced by another mechanism, and there is no
    # streaming bandwidth rate. The cache's hit `bytes_per_s` must not stand in for one.
    cache = {'model': 'cache_fit', 'parameters': {'capacity_bytes': rate(1e9, 'bytes'), 'bytes_per_s': rate(1000.0, 'bytes/s'),
                                                  'cold_bytes_per_s': rate(1000.0, 'bytes/s')}}
    use_target(case, [COMPUTE, LATENCY, cache])
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    case.estimate('fixture.baseline', [work('base.untouched', b, 3, 40), work('base.rewritten', b, 7, 10, 16, 10)])
    case.estimate('fixture.candidate', [work('cand.untouched', c, 3, 40), work('cand.rewritten', c, 7, 4, 16, 5)])
    report = attributed(case)
    cand = rows(report, 'candidate')
    # The estimate itself is known (30 s of latency) because the description prices no bandwidth.
    assert cand['cand.rewritten']['seconds'] == pytest.approx(30)
    floor = cand['cand.rewritten']['resource_floor']
    assert floor['seconds'] is None and floor['limiting_term'] is None
    assert floor['missing'] == ['bytes_per_s']
    assert floor['terms'] == [
        {'model': 'compute_throughput', 'in_description': True, 'seconds': pytest.approx(4), 'missing': []},
        {'model': 'streaming_bandwidth', 'in_description': False, 'seconds': None, 'missing': ['bytes_per_s']}]
    assert cand['cand.rewritten']['headroom'] == [{'limit': 'resource_floor', 'value': None, 'reason': 'unknown_limit'}]
    # A loop that moves no bytes needs no bandwidth rate: its floor is its compute bound.
    assert cand['cand.untouched']['resource_floor']['seconds'] == pytest.approx(40)
    assert [(r['region'], r['tier'], r['value'], r['reason']) for r in report['ranking']] == [
        ('cand.untouched', 'floor_headroom', pytest.approx(1.0), None), ('cand.rewritten', 'unknown', None, 'unknown_limit')]


def test_floor_follows_the_estimate_trial_rule_and_stays_below_it(case):
    use_target(case, [COMPUTE, BANDWIDTH, LATENCY])
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    base = [[work('base.loop', b, 7, 10, 0, 0, 'per_trial')]] * 3
    # Candidate trials (flops, bytes, requests) -> (floor, estimate): (4, 16, 5) -> (8, 30); (20, 0, 1) -> (20, 20);
    # (1, 4, 0) -> (2, 2). Medians: floor 8 s, estimate 20 s, so the headroom is 2.5. A floor from medianed
    # counts (4, 4, 1) would be 4 s; one from the top-level rows (the last trial's counts) would be 2 s.
    cand = [[work('cand.loop', c, 7, f, n, r, 'per_trial')] for f, n, r in ((4, 16, 5), (20, 0, 1), (1, 4, 0))]
    case.estimate('fixture.baseline', base[0], trials=base)
    case.estimate('fixture.candidate', cand[2], trials=cand)
    row = rows(attributed(case), 'candidate')['cand.loop']
    assert row['seconds'] == pytest.approx(20)
    assert row['resource_floor']['seconds'] == pytest.approx(8)
    assert row['headroom'][0]['value'] == pytest.approx(2.5)


def test_floors_and_ranking_validate_and_are_indexed_and_a_floor_above_its_estimate_is_rejected(case):
    use_target(case, [COMPUTE, BANDWIDTH, LATENCY])
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    case.estimate('fixture.baseline', [work('base.untouched', b, 3, 40), work('base.rewritten', b, 7, 10, 16, 10)])
    case.estimate('fixture.candidate', [work('cand.untouched', c, 3, 40), work('cand.rewritten', c, 7, 4, 16, 5)])
    attributed(case)
    checked = case.records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr
    db = case.tmp_path / 'index.sqlite'
    query = lambda sql: json.loads(run_swdb('sql', sql, '--records', case.records.path, '--db', db, '--format', 'json').stdout)
    assert query("SELECT side, region, limit_name, limit_seconds, limiting_term, headroom, reason FROM swdb_attribution_headroom "
                 "WHERE side = 'candidate' ORDER BY region") == [
        {'side': 'candidate', 'region': 'cand.rewritten', 'limit_name': 'resource_floor', 'limit_seconds': 8.0,
         'limiting_term': 'streaming_bandwidth', 'headroom': 3.75, 'reason': None},
        {'side': 'candidate', 'region': 'cand.untouched', 'limit_name': 'resource_floor', 'limit_seconds': 40.0,
         'limiting_term': 'compute_throughput', 'headroom': 1.0, 'reason': None}]
    assert query('SELECT attribution, position, region, tier, limit_name, value FROM swdb_attribution_ranking ORDER BY position') == [
        {'attribution': 'fixture.attribution', 'position': 1, 'region': 'cand.rewritten', 'tier': 'floor_headroom',
         'limit_name': 'resource_floor', 'value': 3.75},
        {'attribution': 'fixture.attribution', 'position': 2, 'region': 'cand.untouched', 'tier': 'floor_headroom',
         'limit_name': 'resource_floor', 'value': 1.0}]
    # A hand edit that lifts a floor above its estimate is caught even with a recomputed identity hash.
    path = case.records.path / 'attributions' / 'fixture.attribution.yaml'
    data = yaml.safe_load(path.read_text())
    next(r for r in data['regions'] if r['region'] == 'cand.rewritten')['resource_floor']['seconds'] = 31.0
    data.pop('identity_sha256')
    data['identity_sha256'] = digest(data)
    case.records.write('attributions/fixture.attribution.yaml', data)
    lifted = case.records.validate()
    assert lifted.returncode == 1 and 'resource floor' in lifted.stdout + lifted.stderr
