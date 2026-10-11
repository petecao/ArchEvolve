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


# Ticket 04 (2026-10-11 ET): rewrite-site edge cases. Each fixture's labels are hand-checked
# against the line numbers written in its comments.


def test_unattributed_time_above_ten_percent_is_flagged_and_the_report_is_still_written(case):
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    # Baseline 100 s with 15 s unattributed (15%); candidate 85 s with 15 s (about 17.6%): flagged.
    case.estimate('fixture.baseline', [region('base.untouched', b, 3, 40), region('base.rewritten', b, 7, 45),
                                       region('stub-impl/serial.base', None, 0, 15)])
    case.estimate('fixture.candidate', [region('cand.untouched', c, 3, 40), region('cand.rewritten', c, 7, 30),
                                        region('stub-impl/serial.cand', None, 0, 15)])
    # Exactly 10% on both sides (10 of 100 s) is not above the threshold.
    case.estimate('fixture.baseline.even', [region('base.untouched', b, 3, 40), region('base.rewritten', b, 7, 50),
                                            region('stub-impl/serial.base', None, 0, 10)])
    case.estimate('fixture.candidate.even', [region('cand.untouched', c, 3, 40), region('cand.rewritten', c, 7, 50),
                                             region('stub-impl/serial.cand', None, 0, 10)])
    flagged = attributed(case)
    assert flagged['whole_program']['unattributed_threshold'] == 0.1
    assert flagged['whole_program']['unattributed_flagged'] is True
    assert groups(flagged)['unattributed']['baseline_share'] == pytest.approx(0.15)
    assert groups(flagged)['agent_rewritten']['realized_speedup'] == pytest.approx(1.5)
    assert (case.records.path / 'attributions' / 'fixture.attribution.yaml').exists()
    even = attributed(case, rid='fixture.attribution.even', baseline='fixture.baseline.even', candidate='fixture.candidate.even')
    assert even['whole_program']['unattributed_flagged'] is False
    checked = case.records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr
    db = case.tmp_path / 'index.sqlite'
    rows = run_swdb('sql', 'SELECT id, unattributed_flagged FROM swdb_attributions ORDER BY id',
                    '--records', case.records.path, '--db', db, '--format', 'json')
    assert json.loads(rows.stdout) == [{'id': 'fixture.attribution', 'unattributed_flagged': 1},
                                       {'id': 'fixture.attribution.even', 'unattributed_flagged': 0}]


def sources(case, baseline, candidate):
    """Replace both fixture trees with `{relative path: text}` files and re-record their snapshots."""
    for root, files, rid in ((case.base_root, baseline, 'fixture.baseline.source'),
                             (case.cand_root, candidate, 'fixture.candidate.source')):
        for old in [p for p in root.rglob('*') if p.is_file()]:
            old.unlink()
        for rel, text in files.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text)
        snapshot(case.records, rid, root)


def accessed(row, *places):
    """`row` with one read access per `(path, line)` place instead of its default access."""
    template = row['access_patterns'][0]
    row['access_patterns'] = [{**template, 'id': f'{template["id"]}.{i}',
                               'source_location': {**template['source_location'], 'path': str(path), 'line': line}}
                              for i, (path, line) in enumerate(places)]
    return row


def sites(report):
    return [(s['id'], s['path'], s['baseline_lines'], s['candidate_lines']) for s in report['rewrite_sites']]


def rows(report):
    return {(r['side'], r['region']): r for r in report['regions']}


# Two changed runs (lines 8 and 10) inside one loop (lines 7-11), plus an unrelated comment change.
MERGE_BASELINE = """// merge fixture
void untouched(float *a, int n) {
  for (int i = 0; i < n; ++i)
    a[i] = a[i] * 2.0f;
}
void rewritten(float *a, float *b, int n) {
  for (int i = 0; i < n; ++i) {
    a[i] = a[i] + 1.0f;
    b[i] = b[i] * 3.0f;
    a[i] = a[i] - b[i];
  }
}
"""
MERGE_CANDIDATE = (MERGE_BASELINE.replace('// merge fixture', '// merge fixture, rewritten')
                   .replace('    a[i] = a[i] + 1.0f;', '    a[i] += 1.0f;')
                   .replace('    a[i] = a[i] - b[i];', '    a[i] -= b[i];'))


def test_two_sites_sharing_a_region_merge_into_one_and_no_region_is_counted_twice(case):
    sources(case, {'kernel.cpp': MERGE_BASELINE}, {'kernel.cpp': MERGE_CANDIDATE})
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    case.estimate('fixture.baseline', [region('base.untouched', b, 3, 40),
                                       accessed(region('base.loop', b, 7, 60), (b, 8), (b, 9), (b, 10))])
    case.estimate('fixture.candidate', [region('cand.untouched', c, 3, 40),
                                        accessed(region('cand.loop', c, 7, 30), (c, 8), (c, 9), (c, 10))])
    report = attributed(case)
    # Raw changed runs: line 1, line 8, line 10. The loop (span 7-10) overlaps lines 8 and 10, so
    # those two runs become one site; line 1 overlaps no region and stays its own site.
    assert sites(report) == [('site.1', 'kernel.cpp', [1, 1], [1, 1]), ('site.2', 'kernel.cpp', [8, 10], [8, 10])]
    assert report['rewrite_sites'][1]['spans'] == [
        {'path': 'kernel.cpp', 'baseline_lines': [8, 8], 'candidate_lines': [8, 8]},
        {'path': 'kernel.cpp', 'baseline_lines': [10, 10], 'candidate_lines': [10, 10]}]
    assert report['rewrite_sites'][0]['baseline_regions'] == [] and report['rewrite_sites'][0]['candidate_regions'] == []
    assert report['rewrite_sites'][1]['baseline_regions'] == ['base.loop']
    assert report['rewrite_sites'][1]['candidate_regions'] == ['cand.loop']
    labels = rows(report)
    assert labels[('baseline', 'base.loop')]['sites'] == ['site.2']
    assert labels[('candidate', 'cand.loop')]['sites'] == ['site.2']
    assert labels[('baseline', 'base.untouched')]['origin'] == 'untouched'
    # No region's time is in two sites, and the rewritten group holds the loop's time once.
    assert all(len(r['sites']) <= 1 for r in report['regions'])
    for side in ('baseline', 'candidate'):
        listed = [rid for s in report['rewrite_sites'] for rid in s[side + '_regions']]
        assert len(listed) == len(set(listed))
    split = groups(report)
    assert (split['agent_rewritten']['baseline_seconds'], split['agent_rewritten']['candidate_seconds']) == (60, 30)
    checked = case.records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr


def test_a_region_only_partly_inside_a_site_counts_as_rewritten_and_is_flagged_mixed(case):
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    # Site: lines 7-8 on both sides. The loop spans 7-8 (all changed); the serial region of
    # `rewritten` starts at its line 6 (unchanged) and reaches line 8 (changed): partly inside.
    case.estimate('fixture.baseline', [region('base.untouched', b, 3, 40), region('base.loop', b, 7, 50),
                                       accessed(region('base.serial', b, 6, 10), (b, 8))])
    case.estimate('fixture.candidate', [region('cand.untouched', c, 3, 40), region('cand.loop', c, 7, 25),
                                        accessed(region('cand.serial', c, 6, 5), (c, 8))])
    report = attributed(case)
    labels = rows(report)
    for side, prefix in (('baseline', 'base'), ('candidate', 'cand')):
        assert (labels[(side, prefix + '.serial')]['origin'], labels[(side, prefix + '.serial')]['mixed']) == ('agent_rewritten', True)
        assert (labels[(side, prefix + '.loop')]['origin'], labels[(side, prefix + '.loop')]['mixed']) == ('agent_rewritten', False)
        assert (labels[(side, prefix + '.untouched')]['origin'], labels[(side, prefix + '.untouched')]['mixed']) == ('untouched', False)
        assert labels[(side, prefix + '.serial')]['lines'] == [6, 8]
    # The mixed region's whole time is in the rewritten group (F14: no split by operation share).
    split = groups(report)
    assert (split['agent_rewritten']['baseline_seconds'], split['agent_rewritten']['candidate_seconds']) == (60, 30)
    checked = case.records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr
    db = case.tmp_path / 'index.sqlite'
    mixed = run_swdb('sql', 'SELECT side, region FROM swdb_attribution_regions WHERE mixed = 1 ORDER BY side',
                     '--records', case.records.path, '--db', db, '--format', 'json')
    assert json.loads(mixed.stdout) == [{'side': 'baseline', 'region': 'base.serial'}, {'side': 'candidate', 'region': 'cand.serial'}]


# The candidate inserts `added` (lines 2-5) above `untouched` and deletes baseline line 6, so
# `untouched` moves from lines 2-5 to 6-9 and `kept` from 7-10 to 10-13 without a changed line.
SHIFT_BASELINE = """// shift fixture
void untouched(float *a, int n) {
  for (int i = 0; i < n; ++i)
    a[i] = a[i] * 2.0f;
}
// a comment the candidate deletes
void kept(float *a, int n) {
  for (int i = 0; i < n; ++i)
    a[i] = a[i] + 1.0f;
}
"""
SHIFT_CANDIDATE = """// shift fixture
void added(float *a, int n) {
  for (int i = 0; i < n; ++i)
    a[i] = a[i] - 1.0f;
}
void untouched(float *a, int n) {
  for (int i = 0; i < n; ++i)
    a[i] = a[i] * 2.0f;
}
void kept(float *a, int n) {
  for (int i = 0; i < n; ++i)
    a[i] = a[i] + 1.0f;
}
"""


def test_untouched_functions_shifted_by_inserted_or_deleted_lines_stay_untouched_and_are_matched(case):
    sources(case, {'kernel.cpp': SHIFT_BASELINE}, {'kernel.cpp': SHIFT_CANDIDATE})
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    case.estimate('fixture.baseline', [accessed(region('base.serial', b, 2, 10), (b, 4)), region('base.untouched', b, 3, 30),
                                       region('base.kept', b, 8, 60)])
    case.estimate('fixture.candidate', [region('cand.added', c, 3, 5), accessed(region('cand.serial', c, 6, 10), (c, 8)),
                                        region('cand.untouched', c, 7, 30), region('cand.kept', c, 11, 60)])
    report = attributed(case)
    # Insertion before baseline line 2 (candidate 2-5); deletion of baseline line 6 (before candidate line 10).
    assert sites(report) == [('site.1', 'kernel.cpp', [2, 1], [2, 5]), ('site.2', 'kernel.cpp', [6, 6], [10, 9])]
    labels = {key: (r['origin'], r['lines'], r['matched_region']) for key, r in rows(report).items()}
    assert labels == {
        ('baseline', 'base.serial'): ('untouched', [2, 4], 'cand.serial'),
        ('baseline', 'base.untouched'): ('untouched', [3, 4], 'cand.untouched'),
        ('baseline', 'base.kept'): ('untouched', [8, 9], 'cand.kept'),
        ('candidate', 'cand.added'): ('agent_rewritten', [3, 4], None),
        ('candidate', 'cand.serial'): ('untouched', [6, 8], 'base.serial'),
        ('candidate', 'cand.untouched'): ('untouched', [7, 8], 'base.untouched'),
        ('candidate', 'cand.kept'): ('untouched', [11, 12], 'base.kept')}
    split = groups(report)
    assert (split['untouched']['baseline_seconds'], split['untouched']['candidate_seconds']) == (100, 100)
    assert split['untouched']['drift'] == pytest.approx(1.0)
    assert (split['agent_rewritten']['baseline_seconds'], split['agent_rewritten']['candidate_seconds']) == (0, 5)
    checked = case.records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr
    db = case.tmp_path / 'index.sqlite'
    pairs = run_swdb('sql', "SELECT region, matched_region FROM swdb_attribution_regions WHERE side = 'baseline' ORDER BY region",
                     '--records', case.records.path, '--db', db, '--format', 'json')
    assert json.loads(pairs.stdout) == [{'region': 'base.kept', 'matched_region': 'cand.kept'},
                                        {'region': 'base.serial', 'matched_region': 'cand.serial'},
                                        {'region': 'base.untouched', 'matched_region': 'cand.untouched'}]


# `twice` (lines 3-5) is untouched and inlined into `caller`; `load` (helper.h line 2) is rewritten
# and inlined into the untouched `user`; `rewritten` (lines 7-8) changes as in BASELINE.
INLINE_BASELINE = """// inline fixture
#include "helper.h"
static inline float twice(const float *a, int i) {
  return a[i] * 2.0f;
}
void rewritten(float *a, int n) {
  for (int i = 0; i < n; ++i)
    a[i] = a[i] + 1.0f;
}
void caller(float *a, int n) {
  for (int i = 0; i < n; ++i)
    a[i] = twice(a, i);
}
void user(float *a, int n) {
  for (int i = 0; i < n; ++i)
    a[i] = load(a, i);
}
"""
INLINE_CANDIDATE = INLINE_BASELINE.replace("""  for (int i = 0; i < n; ++i)
    a[i] = a[i] + 1.0f;""", """  for (int i = 0; i < n; i += 2)
    a[i] += 1.0f, a[i + 1] += 1.0f;""")
HELPER_BASELINE = """static inline float load(const float *a, int i) {
  return a[i] * 3.0f;
}
"""
HELPER_CANDIDATE = HELPER_BASELINE.replace('a[i] * 3.0f', 'a[i] + a[i] + a[i]')


def test_inlined_code_is_labeled_by_its_own_file_and_line(case):
    sources(case, {'kernel.cpp': INLINE_BASELINE, 'helper.h': HELPER_BASELINE},
            {'kernel.cpp': INLINE_CANDIDATE, 'helper.h': HELPER_CANDIDATE})
    for side, prefix, root, rewritten_s, user_s in (('baseline', 'base', case.base_root, 50, 30),
                                                     ('candidate', 'cand', case.cand_root, 25, 10)):
        k, h = root / 'kernel.cpp', root / 'helper.h'
        # The LLVM pass gives an inlined access its own file and line, but the caller's region.
        case.estimate('fixture.' + side, [region(prefix + '.rewritten', k, 7, rewritten_s),
                                          accessed(region(prefix + '.caller', k, 11, 20), (k, 4), (k, 12)),
                                          accessed(region(prefix + '.user', k, 15, user_s), (h, 2), (k, 16))])
    report = attributed(case)
    assert sites(report) == [('site.1', 'helper.h', [2, 2], [2, 2]), ('site.2', 'kernel.cpp', [7, 8], [7, 8])]
    labels = {key: (r['origin'], r['mixed'], r['lines'], r['inlined'], r['sites']) for key, r in rows(report).items()}
    for side, prefix in (('baseline', 'base'), ('candidate', 'cand')):
        assert labels[(side, prefix + '.rewritten')] == ('agent_rewritten', False, [7, 8], [], ['site.2'])
        # The untouched helper at line 4 no longer stretches `caller` across `rewritten` (lines 4-12).
        assert labels[(side, prefix + '.caller')] == ('untouched', False, [11, 12], [{'path': 'kernel.cpp', 'lines': [4, 4]}], [])
        # The rewritten helper makes its untouched caller rewritten, flagged mixed.
        assert labels[(side, prefix + '.user')] == ('agent_rewritten', True, [15, 16], [{'path': 'helper.h', 'lines': [2, 2]}], ['site.1'])
    assert rows(report)[('baseline', 'base.caller')]['matched_region'] == 'cand.caller'
    split = groups(report)
    assert (split['agent_rewritten']['baseline_seconds'], split['agent_rewritten']['candidate_seconds']) == (80, 35)
    assert (split['untouched']['baseline_seconds'], split['untouched']['candidate_seconds']) == (20, 20)
    # One region reaching changed runs in two files merges them into one site with no single path.
    for side, prefix, root in (('baseline', 'base', case.base_root), ('candidate', 'cand', case.cand_root)):
        k, h = root / 'kernel.cpp', root / 'helper.h'
        case.estimate(f'fixture.{side}.both', [accessed(region(prefix + '.both', k, 7, 10), (k, 8), (h, 2))])
    both = attributed(case, rid='fixture.attribution.both', baseline='fixture.baseline.both', candidate='fixture.candidate.both')
    assert sites(both) == [('site.1', None, None, None)]
    assert both['rewrite_sites'][0]['spans'] == [{'path': 'helper.h', 'baseline_lines': [2, 2], 'candidate_lines': [2, 2]},
                                                 {'path': 'kernel.cpp', 'baseline_lines': [7, 8], 'candidate_lines': [7, 8]}]
    assert rows(both)[('baseline', 'base.both')]['sites'] == ['site.1']
    checked = case.records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr


# --- Ticket 05: library, intrinsic and offload labels (2026-10-11 ET) ---------------------------

def call(site, region_id, name, executions, line=7):
    """One executed call whose body is counted, so the estimate stays known."""
    return {'site': site, 'region': region_id, 'name': name, 'line': line, 'event': 'external_call',
            'cost_accounting': 'opaque_callee', 'body_counted': True, 'operation_class': None,
            'operations_per_execution': 0, 'execution_count': count(executions)}


def offload(row, event='fixture.gather', executions=4):
    """Mark a counted region as issuing one functional-observation command."""
    row['accelerator_calls'].append({'site': 0, 'event': event, 'intrinsic': '__dxc_gather',
        'hardware_operations': ['dx100.mmio.v1.indirect-load.i32'], 'execution_count': count(executions),
        'active_elements': count(0), 'useful_accesses': count(0), 'useful_bytes': count(0),
        'accounting_domain': 'offload', 'functional_bookkeeping': {}, 'missing': []})
    return row


def catalog(case):
    """A typed library with one library operation, and the store's AVX-512 gather intrinsic."""
    from conftest import REPO
    root = case.tmp_path / 'catalog'
    (root / 'library_operations').mkdir(parents=True)
    (root / 'library_operations' / 'fixture_stage.yaml').write_text(yaml.safe_dump({
        'id': 'operation.fixture_stage', 'kind': 'library_operation',
        'location': {'root': 'library', 'path': 'library_operations/fixture_stage.hh', 'symbol': 'FixtureStage'}}))
    case.records.write('intrinsics/mm512_i32gather_ps.yaml',
                       yaml.safe_load((REPO / 'records/intrinsics/mm512_i32gather_ps.yaml').read_text()))
    return root


def estimate_with_calls(case, rid, regions, calls):
    """`Case.estimate` with executed calls recorded in the characterization."""
    characterization(case.records, rid + '.counts', regions)
    path = case.records.path / 'workload_characterizations' / (rid + '.counts.yaml')
    data = yaml.safe_load(path.read_text())
    data['unmodeled_calls'] = calls
    data.pop('identity_sha256')
    data['identity_sha256'] = digest(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    result = run_swdb('estimate', '--records', case.records.path, '--characterization', rid + '.counts',
        '--target-description', case.target, '--protocol', case.protocol, '--id', rid, '--format', 'json')
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def attributed_with(case, library):
    result = run_swdb('attribute', '--records', case.records.path, '--baseline-estimate', 'fixture.baseline',
        '--candidate-estimate', 'fixture.candidate', '--baseline-source', 'fixture.baseline.source',
        '--candidate-source', 'fixture.candidate.source', '--library', library, '--id', 'fixture.attribution',
        '--format', 'json')
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_offload_command_beats_intrinsic_beats_library_call_inside_one_site(case):
    library = catalog(case)
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    case.estimate('fixture.baseline', [region('base.untouched', b, 3, 40), region('base.rewritten', b, 7, 60)])
    # Inside the one site (candidate lines 7-8): an offload loop that also calls the library
    # operation, a loop calling the intrinsic and the library operation, a library-only loop
    # (mangled member call) and a plain rewritten loop.
    estimate_with_calls(case, 'fixture.candidate', [region('cand.untouched', c, 3, 40),
        offload(region('cand.offload', c, 7, 5)), region('cand.intrinsic', c, 7, 4),
        region('cand.library', c, 8, 3), region('cand.plain', c, 8, 2)],
        [call(0, 'cand.offload', '_ZN12FixtureStage5stageEPf', 4),
         call(1, 'cand.intrinsic', '_mm512_i32gather_ps', 2), call(2, 'cand.intrinsic', '_ZN12FixtureStage5stageEPf', 2),
         call(3, 'cand.library', '_ZN12FixtureStage5stageEPf', 1)])
    report = attributed_with(case, library)
    labels = {r['region']: r['origin'] for r in report['regions']}
    assert labels == {'base.untouched': 'untouched', 'base.rewritten': 'agent_rewritten',
                      'cand.untouched': 'untouched', 'cand.offload': 'offload_command', 'cand.intrinsic': 'intrinsic',
                      'cand.library': 'library_call', 'cand.plain': 'agent_rewritten'}
    evidence = {r['region']: r['evidence'] for r in report['regions'] if r['side'] == 'candidate'}
    assert evidence['cand.offload'] == [{'origin': 'offload_command', 'name': 'fixture.gather'},
                                        {'origin': 'library_call', 'name': 'operation.fixture_stage'}]
    assert evidence['cand.intrinsic'] == [{'origin': 'intrinsic', 'name': 'mm512_i32gather_ps'},
                                          {'origin': 'library_call', 'name': 'operation.fixture_stage'}]
    assert evidence['cand.plain'] == [] and evidence['cand.untouched'] == []


def test_rewritten_group_splits_seconds_by_origin_and_baseline_std_calls_stay_untouched(case):
    library = catalog(case)
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    header = case.tmp_path / 'catalog' / 'library_operations' / 'fixture_stage.hh'
    std = '/usr/include/c++/13/bits/stl_algo.h'

    def std_calls(prefix):
        return [call(10, prefix + '.untouched', '_ZSt4sortIPfEvT_S1_', 3, line=3),
                call(11, prefix + '.untouched', 'strlen', 3, line=3)]
    # Baseline: an untouched loop calling std::sort and strlen, a loop inside a C++ header, and
    # the 60 s loop the agent rewrites.
    estimate_with_calls(case, 'fixture.baseline', [region('base.untouched', b, 3, 30), region('base.std', std, 120, 10),
        region('base.rewritten', b, 7, 60)], std_calls('base'))
    # Candidate: the same untouched code; the site holds a 5 s offload loop, a 10 s loop whose
    # accesses are inlined from the library operation's header, and 15 s of plain rewritten code.
    inlined = region('cand.library', c, 7, 10)
    inlined['access_patterns'][0]['source_location']['path'] = str(header)
    estimate_with_calls(case, 'fixture.candidate', [region('cand.untouched', c, 3, 30), region('cand.std', std, 120, 10),
        offload(region('cand.offload', c, 7, 5)), inlined, region('cand.plain', c, 8, 15)], std_calls('cand'))
    report = attributed_with(case, library)
    labels = {r['region']: (r['origin'], r['reason']) for r in report['regions']}
    assert labels['base.untouched'] == ('untouched', 'no_changed_line')
    assert labels['cand.untouched'] == ('untouched', 'no_changed_line')
    assert labels['cand.std'] == ('untouched', 'outside_source_tree')
    assert labels['cand.library'] == ('library_call', 'library_operation_in_site')
    assert labels['cand.offload'] == ('offload_command', 'offload_command_in_site')
    split = groups(report)
    assert split['untouched']['baseline_seconds'] == pytest.approx(40) and split['untouched']['drift'] == pytest.approx(1.0)
    rewritten = split['agent_rewritten']
    assert (rewritten['baseline_seconds'], rewritten['candidate_seconds']) == (pytest.approx(60), pytest.approx(30))
    assert rewritten['realized_speedup'] == pytest.approx(2.0)
    assert [o['origin'] for o in rewritten['origins']] == ['offload_command', 'intrinsic', 'library_call', 'agent_rewritten']
    by_origin = {o['origin']: o for o in rewritten['origins']}
    assert {k: (o['baseline_seconds'], o['candidate_seconds']) for k, o in by_origin.items()} == {
        'offload_command': (0, 5), 'intrinsic': (0, 0), 'library_call': (0, 10), 'agent_rewritten': (60, 15)}
    assert by_origin['offload_command']['candidate_share'] == pytest.approx(5 / 70)  # candidate total 30 + 10 + 5 + 10 + 15
    assert by_origin['agent_rewritten']['baseline_share'] == pytest.approx(0.6)
    assert report['catalog'] == [{'kind': 'library_operation', 'id': 'operation.fixture_stage',
        'sha256': digest(yaml.safe_load((library / 'library_operations' / 'fixture_stage.yaml').read_text()))}]
    checked = case.records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr
    rows = run_swdb('sql', 'SELECT origin, baseline_seconds, candidate_seconds FROM swdb_attribution_origins '
                    "WHERE attribution = 'fixture.attribution' ORDER BY origin", '--records', case.records.path,
                    '--db', case.tmp_path / 'index.sqlite', '--format', 'json')
    assert rows.returncode == 0, rows.stdout + rows.stderr
    assert json.loads(rows.stdout) == [
        {'origin': 'agent_rewritten', 'baseline_seconds': 60.0, 'candidate_seconds': 15.0},
        {'origin': 'intrinsic', 'baseline_seconds': 0.0, 'candidate_seconds': 0.0},
        {'origin': 'library_call', 'baseline_seconds': 0.0, 'candidate_seconds': 10.0},
        {'origin': 'offload_command', 'baseline_seconds': 0.0, 'candidate_seconds': 5.0}]


def test_validate_rejects_a_changed_intrinsic_that_labeled_a_region(case):
    library = catalog(case)
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    case.estimate('fixture.baseline', [region('base.rewritten', b, 7, 60)])
    estimate_with_calls(case, 'fixture.candidate', [region('cand.intrinsic', c, 7, 4)],
                        [call(0, 'cand.intrinsic', '_mm512_i32gather_ps', 2)])
    report = attributed_with(case, library)
    path = case.records.path / 'intrinsics' / 'mm512_i32gather_ps.yaml'
    assert report['catalog'] == [{'kind': 'intrinsic', 'id': 'mm512_i32gather_ps',
                                  'sha256': digest(yaml.safe_load(path.read_text()))}]
    assert case.records.validate().returncode == 0
    path.write_text(path.read_text().replace('updated: \'2026-09-23\'', 'updated: \'2026-10-11\''))
    changed = case.records.validate()
    assert changed.returncode == 1 and 'catalog' in changed.stdout + changed.stderr


# Iterations (ticket 06, F13). Three loops: A (lines 3-4), B (lines 7-8), C (lines 11-12).
# Iteration 1 rewrites B, iteration 2 rewrites A, iteration 3 rewrites C.
ITERATION_0 = BASELINE + """void kept(float *a, int n) {
  for (int i = 0; i < n; ++i)
    a[i] = a[i] - 1.0f;
}
"""
ITERATION_1 = ITERATION_0.replace("""  for (int i = 0; i < n; ++i)
    a[i] = a[i] + 1.0f;""", """  for (int i = 0; i < n; i += 2)
    a[i] += 1.0f, a[i + 1] += 1.0f;""")
ITERATION_2 = ITERATION_1.replace("""  for (int i = 0; i < n; ++i)
    a[i] = a[i] * 2.0f;""", """  for (int i = 0; i < n; i += 2)
    a[i] *= 2.0f, a[i + 1] *= 2.0f;""")
ITERATION_3 = ITERATION_2.replace("""  for (int i = 0; i < n; ++i)
    a[i] = a[i] - 1.0f;""", """  for (int i = 0; i < n; i += 2)
    a[i] -= 1.0f, a[i + 1] -= 1.0f;""")
# Seconds per loop (A, B, C) in each iteration: totals 100, 75, 55, 50.
ITERATION_SECONDS = [(40, 50, 10), (40, 25, 10), (20, 25, 10), (20, 25, 5)]


def iterations(case, count):
    """Writes iterations 0..count-1: source tree `fixture.it<i>.source` and estimate `fixture.it<i>`."""
    texts = [ITERATION_0, ITERATION_1, ITERATION_2, ITERATION_3][:count]
    for i, text in enumerate(texts):
        root = tree(case.tmp_path, f'it{i}', text)
        snapshot(case.records, f'fixture.it{i}.source', root)
        a, b, c = ITERATION_SECONDS[i]
        path = root / 'kernel.cpp'
        case.estimate(f'fixture.it{i}', [region(f'it{i}.a', path, 3, a), region(f'it{i}.b', path, 7, b),
                                         region(f'it{i}.c', path, 11, c)])


def attribute_iteration(case, current, previous=None, earlier=(), rid='fixture.attribution', previous_estimate=None):
    args = ['attribute', '--records', case.records.path, '--baseline-estimate', 'fixture.it0',
            '--candidate-estimate', f'fixture.it{current}', '--baseline-source', 'fixture.it0.source',
            '--candidate-source', f'fixture.it{current}.source', '--id', rid, '--format', 'json']
    if previous is not None:
        args += ['--previous-estimate', previous_estimate or f'fixture.it{previous}',
                 '--previous-source', f'fixture.it{previous}.source']
    for i in earlier:
        args += ['--earlier-source', f'fixture.it{i}.source']
    return run_swdb(*args)


def attributed_iteration(case, *args, **kwargs):
    result = attribute_iteration(case, *args, **kwargs)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def region_facts(rows):
    return {(r['side'], r['region']): (r['origin'], r.get('last_changed_iteration')) for r in rows}


def test_iteration_two_reports_gain_this_iteration_and_cumulative_gain(case):
    iterations(case, 3)
    report = attributed_iteration(case, 2, previous=1)
    this = report['this_iteration']
    assert this['iteration'] == 2
    assert this['previous_estimate']['id'] == 'fixture.it1' and this['previous_source']['id'] == 'fixture.it1.source'
    assert this['earlier_sources'] == []
    # B was rewritten in iteration 1 and is untouched in iteration 2: untouched this iteration, rewritten cumulatively.
    assert region_facts(this['regions']) == {
        ('baseline', 'it1.a'): ('agent_rewritten', 0), ('baseline', 'it1.b'): ('untouched', 1), ('baseline', 'it1.c'): ('untouched', 0),
        ('candidate', 'it2.a'): ('agent_rewritten', 2), ('candidate', 'it2.b'): ('untouched', 1),
        ('candidate', 'it2.c'): ('untouched', 0)}
    assert region_facts(report['regions']) == {
        ('baseline', 'it0.a'): ('agent_rewritten', 0), ('baseline', 'it0.b'): ('agent_rewritten', 0),
        ('baseline', 'it0.c'): ('untouched', 0),
        ('candidate', 'it2.a'): ('agent_rewritten', 2), ('candidate', 'it2.b'): ('agent_rewritten', 1),
        ('candidate', 'it2.c'): ('untouched', 0)}
    assert [(s['baseline_lines'], s['candidate_lines']) for s in this['rewrite_sites']] == [([3, 4], [3, 4])]
    assert [(s['baseline_lines'], s['candidate_lines']) for s in report['rewrite_sites']] == [([3, 4], [3, 4]), ([7, 8], [7, 8])]
    # This iteration (previous 75 s -> 55 s): A 40 -> 20 rewritten; B + C 35 -> 35 untouched.
    now = groups(this)
    assert (now['agent_rewritten']['baseline_seconds'], now['agent_rewritten']['candidate_seconds']) == (40, 20)
    assert now['agent_rewritten']['baseline_share'] == pytest.approx(40 / 75)
    assert now['agent_rewritten']['realized_speedup'] == pytest.approx(2.0)
    assert (now['untouched']['baseline_seconds'], now['untouched']['candidate_seconds']) == (35, 35)
    assert now['untouched']['drift'] == pytest.approx(1.0)
    assert this['whole_program']['baseline_seconds'] == pytest.approx(75)
    assert this['whole_program']['candidate_seconds'] == pytest.approx(55)
    assert this['whole_program']['total_speedup'] == pytest.approx(75 / 55)
    assert this['whole_program']['amdahl_ceiling'] == pytest.approx(75 / 35)
    # Cumulative (original 100 s -> 55 s): A + B 90 -> 45 rewritten; C 10 -> 10 untouched.
    total = groups(report)
    assert (total['agent_rewritten']['baseline_seconds'], total['agent_rewritten']['candidate_seconds']) == (90, 45)
    assert total['agent_rewritten']['baseline_share'] == pytest.approx(0.9)
    assert total['agent_rewritten']['realized_speedup'] == pytest.approx(2.0)
    assert (total['untouched']['baseline_seconds'], total['untouched']['candidate_seconds']) == (10, 10)
    assert report['whole_program']['total_speedup'] == pytest.approx(100 / 55)
    assert report['whole_program']['amdahl_ceiling'] == pytest.approx(10.0)


def test_without_a_previous_candidate_the_report_is_the_ticket_02_report(case):
    iterations(case, 3)
    alone = attributed_iteration(case, 2, rid='fixture.alone')
    assert list(alone) == ['kind', 'schema_version', 'id', 'status', 'created', 'updated', 'provenance', 'format',
                           'baseline_estimate', 'candidate_estimate', 'baseline_source', 'candidate_source',
                           'target_description', 'input', 'threads', 'evidence_kind', 'catalog', 'rewrite_sites', 'regions',
                           'groups', 'whole_program', 'identity_sha256']
    assert all('last_changed_iteration' not in row for row in alone['regions'])
    # The cumulative part of an iteration-2 report is the same comparison, plus last-changed iterations.
    both = attributed_iteration(case, 2, previous=1, rid='fixture.both')
    for field in ('rewrite_sites', 'groups', 'whole_program'):
        assert both[field] == alone[field]
    assert [{k: v for k, v in row.items() if k != 'last_changed_iteration'} for row in both['regions']] == alone['regions']


def test_iteration_three_names_the_iteration_that_last_changed_each_region_from_earlier_sources(case):
    iterations(case, 4)
    report = attributed_iteration(case, 3, previous=2, earlier=[1])
    this = report['this_iteration']
    assert this['iteration'] == 3
    assert [pin['id'] for pin in this['earlier_sources']] == ['fixture.it1.source']
    assert region_facts(this['regions']) == {
        ('baseline', 'it2.a'): ('untouched', 2), ('baseline', 'it2.b'): ('untouched', 1),
        ('baseline', 'it2.c'): ('agent_rewritten', 0),
        ('candidate', 'it3.a'): ('untouched', 2), ('candidate', 'it3.b'): ('untouched', 1),
        ('candidate', 'it3.c'): ('agent_rewritten', 3)}
    # This iteration (previous 55 s -> 50 s): C 10 -> 5 rewritten; A + B 45 -> 45 untouched.
    now = groups(this)
    assert (now['agent_rewritten']['baseline_seconds'], now['agent_rewritten']['candidate_seconds']) == (10, 5)
    assert (now['untouched']['baseline_seconds'], now['untouched']['candidate_seconds']) == (45, 45)
    assert this['whole_program']['amdahl_ceiling'] == pytest.approx(55 / 45)
    # Cumulative: every loop was rewritten in some iteration.
    assert groups(report)['agent_rewritten']['baseline_seconds'] == 100
    assert groups(report)['untouched']['baseline_seconds'] == 0


def test_iteration_two_report_validates_pins_its_previous_candidate_and_is_indexed(case):
    iterations(case, 3)
    attributed_iteration(case, 2, previous=1)
    checked = case.records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr
    db = case.tmp_path / 'index.sqlite'

    def sql(query):
        rows = run_swdb('sql', query, '--records', case.records.path, '--db', db, '--format', 'json')
        assert rows.returncode == 0, rows.stdout + rows.stderr
        return json.loads(rows.stdout)
    assert sql('SELECT * FROM swdb_attribution_iterations') == [
        {'attribution': 'fixture.attribution', 'iteration': 2, 'previous_estimate': 'fixture.it1',
         'previous_source': 'fixture.it1.source', 'earlier_sources': '[]', 'previous_seconds': 75.0, 'candidate_seconds': 55.0,
         'total_speedup': pytest.approx(75 / 55), 'amdahl_ceiling': pytest.approx(75 / 35)}]
    assert sql('SELECT origin, baseline_seconds, candidate_seconds, realized_speedup, drift '
               'FROM swdb_attribution_iteration_groups ORDER BY origin') == [
        {'origin': 'agent_rewritten', 'baseline_seconds': 40.0, 'candidate_seconds': 20.0, 'realized_speedup': 2.0, 'drift': None},
        {'origin': 'unattributed', 'baseline_seconds': 0.0, 'candidate_seconds': 0.0, 'realized_speedup': None, 'drift': None},
        {'origin': 'untouched', 'baseline_seconds': 35.0, 'candidate_seconds': 35.0, 'realized_speedup': 1.0, 'drift': 1.0}]
    assert sql("SELECT side, region, origin, last_changed_iteration FROM swdb_attribution_iteration_regions "
               "WHERE side = 'candidate' ORDER BY region") == [
        {'side': 'candidate', 'region': 'it2.a', 'origin': 'agent_rewritten', 'last_changed_iteration': 2},
        {'side': 'candidate', 'region': 'it2.b', 'origin': 'untouched', 'last_changed_iteration': 1},
        {'side': 'candidate', 'region': 'it2.c', 'origin': 'untouched', 'last_changed_iteration': 0}]
    estimate = case.records.path / 'estimates' / 'fixture.it1.yaml'
    estimate.write_text(estimate.read_text().replace('status: draft', 'status: reviewed', 1))
    changed = case.records.validate()
    assert changed.returncode == 1 and 'previous_estimate' in changed.stdout + changed.stderr


def test_previous_candidate_of_another_input_or_without_its_source_is_refused(case):
    iterations(case, 3)
    path = case.tmp_path / 'sources' / 'it1' / 'kernel.cpp'
    case.estimate('fixture.it1.other-input', [region('it1.other.a', path, 3, 40)], input_id='tiny-sym-b')
    other = attribute_iteration(case, 2, previous=1, previous_estimate='fixture.it1.other-input')
    assert other.returncode == 1 and 'previous and candidate estimates differ in input' in other.stderr
    alone = run_swdb('attribute', '--records', case.records.path, '--baseline-estimate', 'fixture.it0',
                     '--candidate-estimate', 'fixture.it2', '--baseline-source', 'fixture.it0.source',
                     '--candidate-source', 'fixture.it2.source', '--previous-estimate', 'fixture.it1', '--id', 'fixture.x')
    assert alone.returncode == 1 and '--previous-estimate and --previous-source go together' in alone.stderr
    assert not (case.records.path / 'attributions').exists()
