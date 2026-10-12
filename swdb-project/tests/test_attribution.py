"""Public `swdb attribute` seam (fine-grained attribution spec, seam 1).
Created: 2026-10-11 ET. Fixture counts and snapshots are contract fixtures, never application
evidence: each test writes two tiny source trees, counts them by hand, estimates them through
`swdb estimate`, and checks the attribution record against hand-computed values.
"""
import hashlib
import json

import pytest
import yaml

from conftest import REPO, run_swdb
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


def snapshot(records, rid, root, revision='fixture'):
    files = []
    for path in sorted(p for p in root.rglob('*') if p.is_file()):
        files.append({'path': path.relative_to(root).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                      'bytes': path.stat().st_size, 'executable': False})
    records.write(f'source_snapshots/{rid}.yaml', {'kind': 'source_snapshot', 'schema_version': '0.4', 'id': rid,
        'status': 'draft', 'created': '2026-10-11', 'updated': '2026-10-11',
        'provenance': [{'id': 'fixture', 'kind': 'source_code', 'description': 'Attribution contract fixture tree.'}],
        'message_version': '1.0', 'producer': {'name': 'attribution-fixture', 'role': 'operator', 'test_client': True},
        'implementation': 'stub-impl', 'application': 'gapbs', 'revision': revision,
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


def region_rows(report):
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
    labels = region_rows(report)
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
    labels = region_rows(report)
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
    labels = {key: (r['origin'], r['lines'], r['matched_region']) for key, r in region_rows(report).items()}
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
    labels = {key: (r['origin'], r['mixed'], r['lines'], r['inlined'], r['sites']) for key, r in region_rows(report).items()}
    for side, prefix in (('baseline', 'base'), ('candidate', 'cand')):
        assert labels[(side, prefix + '.rewritten')] == ('agent_rewritten', False, [7, 8], [], ['site.2'])
        # The untouched helper at line 4 no longer stretches `caller` across `rewritten` (lines 4-12).
        assert labels[(side, prefix + '.caller')] == ('untouched', False, [11, 12], [{'path': 'kernel.cpp', 'lines': [4, 4]}], [])
        # The rewritten helper makes its untouched caller rewritten, flagged mixed.
        assert labels[(side, prefix + '.user')] == ('agent_rewritten', True, [15, 16], [{'path': 'helper.h', 'lines': [2, 2]}], ['site.1'])
    assert region_rows(report)[('baseline', 'base.caller')]['matched_region'] == 'cand.caller'
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
    assert region_rows(both)[('baseline', 'base.both')]['sites'] == ['site.1']
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


def iterations(case, count, calls=None):
    """Writes iterations 0..count-1: source tree `fixture.it<i>.source` and estimate `fixture.it<i>`.
    `calls` maps an iteration index to the executed calls its characterization records."""
    texts = [ITERATION_0, ITERATION_1, ITERATION_2, ITERATION_3][:count]
    for i, text in enumerate(texts):
        root = tree(case.tmp_path, f'it{i}', text)
        snapshot(case.records, f'fixture.it{i}.source', root)
        a, b, c = ITERATION_SECONDS[i]
        path = root / 'kernel.cpp'
        loops = [region(f'it{i}.a', path, 3, a), region(f'it{i}.b', path, 7, b), region(f'it{i}.c', path, 11, c)]
        if (calls or {}).get(i):
            estimate_with_calls(case, f'fixture.it{i}', loops, calls[i])
        else:
            case.estimate(f'fixture.it{i}', loops)


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
    # Ticket 07: this-iteration rows carry floors too (same row shape); the candidate's equal the cumulative ones.
    floors = {(r['side'], r['region']): (r['resource_floor'], r['headroom']) for r in report['regions']}
    assert all('resource_floor' in r and r['headroom'] for r in this['regions'])
    assert all(floors[key] == (r['resource_floor'], r['headroom'])
               for r in this['regions'] if (key := (r['side'], r['region']))[0] == 'candidate')
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
                           'groups', 'whole_program', 'ranking', 'ranking_rule', 'identity_sha256']
    assert all('last_changed_iteration' not in row for row in alone['regions'])
    # The cumulative part of an iteration-2 report is the same comparison, plus last-changed iterations.
    both = attributed_iteration(case, 2, previous=1, rid='fixture.both')
    for field in ('rewrite_sites', 'groups', 'whole_program', 'ranking'):
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


def test_an_intrinsic_seen_only_in_an_earlier_diff_is_not_pinned_by_the_report(case):
    # Review fix (finding 1): previous loop B calls the intrinsic and was rewritten in iteration 1
    # (baseline -> previous), but no row of this report labels it: B is untouched this iteration,
    # and the candidate's B calls nothing. So the report pins no intrinsic.
    catalog(case)
    iterations(case, 3, calls={1: [call(0, 'it1.b', '_mm512_i32gather_ps', 2)]})
    report = attributed_iteration(case, 2, previous=1)
    assert all(r['evidence'] == [] for r in report['regions'] + report['this_iteration']['regions'])
    assert report['catalog'] == []
    assert region_facts(report['this_iteration']['regions'])[('baseline', 'it1.b')] == ('untouched', 1)


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
    # Without site-finder regions the catalog headroom is null and says why (ticket 08).
    no_catalog = {'limit': 'catalog_bound', 'value': None, 'reason': 'no_site_finder'}
    assert cand['cand.rewritten']['headroom'] == [{'limit': 'resource_floor', 'value': pytest.approx(3.75), 'reason': None}, no_catalog]
    assert cand['cand.untouched']['headroom'] == [{'limit': 'resource_floor', 'value': pytest.approx(1.0), 'reason': None}, no_catalog]
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
    assert cand['cand.rewritten']['headroom'][0] == {'limit': 'resource_floor', 'value': None, 'reason': 'unknown_limit'}
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
                 "WHERE side = 'candidate' AND limit_name = 'resource_floor' ORDER BY region") == [
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


# --- Ticket 08: catalog bound and full ranking (2026-10-11 ET; spec F6, F7, F21, F25) ----------
#
# The description prices host compute (1 fp op/s) and one offload mechanism, `fetch_queue`
# (1 s per logical line request), at full overlap, and declares the DX100 functional
# observation commands (copied from the repo's description). The fixture library has an
# offload operation whose intrinsic provides `dx100.functional.v1.gather` (so it reaches
# `fetch_queue`) and a plain CPU operation with no intrinsic (so it reaches no mechanism).
# Review fix (F30, 2026-10-11 ET): site-finder lines name a full-source revision, saved as
# `fixture.revision.source`: the fixture kernel below 60 extra header lines, so the `untouched`
# loop is lines 63-64 there and the `rewritten` loop 67-68. They join by moved lines (offset
# inside the function), not by whole function.
DX100_DESCRIPTION = REPO / 'records' / 'target_descriptions' / 'dx100-e4fc4af-functional-analytic-v1.t1.yaml'
A8_SUMMARY = REPO / 'records' / 'campaign_summaries' / 'extensa-native-bfs-20261005-a8.summary.yaml'
QUEUE = {'model': 'fetch_queue', 'selector': {'domain': 'offload'}, 'parameters': {
    'queue_entries': rate(1, 'entries'), 'fetch_latency_s': rate(1.0, 'seconds/request'),
    'admission_requests_per_s': rate(1.0, 'requests/s')}}
REVISION = '// full-source revision header\n' * 60 + BASELINE
UNTOUCHED_SF, REWRITTEN_SF = 'stub-impl/untouched:63-64', 'stub-impl/rewritten:67-68'


def offload_target(case):
    data = yaml.safe_load(case.target.read_text())
    dx100 = yaml.safe_load(DX100_DESCRIPTION.read_text())
    data['functional_observation'] = dx100['functional_observation']
    data['dram_address_layout'] = dx100['dram_address_layout']
    data['composition_contract'] = {'format': 'swdb.composition-contract.v1', 'resource_domain_overlap': 'full_overlap',
                                    'basis': 'inferred', 'source': 'Declared hand-computed overlap fixture premise.'}
    case.target.write_text(yaml.safe_dump(data, sort_keys=False))
    use_target(case, [COMPUTE, QUEUE])


def logical(case, requests):
    """Logical line requests counted for the case's description (requests x 1 s in `fetch_queue`)."""
    fraction = {'value': 0.0 if requests else None, 'basis': 'reported' if requests else 'unknown', 'scope': 'per_call'}
    return {case.target_sha256: {
        'format': 'swdb.logical-address-counts.v1', 'target_description_sha256': case.target_sha256,
        'level': 'derived_logical_transactions', 'state': 'complete', 'scope': 'per_call', 'missing': [],
        **{name: '0' * 64 for name in ('layout_sha256', 'request_policy_sha256', 'placement_assumption_sha256', 'window_policy_sha256')},
        'line_requests': count(requests), 'row_groups': count(requests), 'grouped_row_hits': count(0),
        'grouped_row_hit_fraction': fraction, 'windows': count(0), 'staged_bytes': count(0),
        'notes': ['Logical hand-counted attribution fixture; no hardware evidence.']}}


def offloaded(case, rid, path, line, flops, requests=None):
    row = region(rid, path, line, flops)
    row['active_workers'] = {'value': 1, 'basis': 'measured'}
    if requests is not None:
        row['address_stream_counts'] = logical(case, requests)
    return row


def catalog_library(case):
    root = case.tmp_path / 'catalog-bound-library'
    entries = {'intrinsics/fixture_gather.yaml': {'id': 'intrinsic.fixture_gather', 'kind': 'intrinsic',
                                                  'hardware_operations': ['dx100.functional.v1.gather']},
               'intrinsics/fixture_mmio_gather.yaml': {'id': 'intrinsic.fixture_mmio_gather', 'kind': 'intrinsic',
                                                       'hardware_operations': ['dx100.mmio.v1.indirect-load.i32']},
               'library_operations/fixture_offload.yaml': {'id': 'operation.fixture_offload', 'kind': 'library_operation',
                                                           'uses_intrinsics': ['intrinsic.fixture_gather'], 'uses_library_operations': []},
               'library_operations/fixture_mmio.yaml': {'id': 'operation.fixture_mmio', 'kind': 'library_operation',
                                                        'uses_intrinsics': ['intrinsic.fixture_mmio_gather'], 'uses_library_operations': []},
               'library_operations/fixture_cpu.yaml': {'id': 'operation.fixture_cpu', 'kind': 'library_operation',
                                                       'uses_intrinsics': [], 'uses_library_operations': []}}
    for rel, data in entries.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(yaml.safe_dump(data, sort_keys=False))
    return root, {data['id']: digest(data) for data in entries.values()}


def application(entry, shas, sha=True):
    """A site-finder application; `sha` False leaves `content_sha256` out, a string replaces it."""
    row = {'entry': entry, 'contract': None, 'kind': 'library_operation', 'pattern_key': [], 'statements': [],
           'legality': []}
    if sha:
        row['content_sha256'] = sha if isinstance(sha, str) else shas.get(entry, '0' * 64)
    return row


def site_finder_summary(case, shas, chosen=None):
    """A saved campaign summary whose one iteration chose site-finder regions.
    `chosen` is [(region ID, lines, [application])]; default: the untouched and rewritten loops,
    both matched by the offload operation."""
    data = yaml.safe_load(A8_SUMMARY.read_text())
    data['id'], data['campaign'] = 'extensa-native-bfs-20261011-z9.summary', 'extensa-native-bfs-20261011-z9'
    if chosen is None:
        chosen = [(UNTOUCHED_SF, [63, 64], [application('operation.fixture_offload', shas)]),
                  (REWRITTEN_SF, [67, 68], [application('operation.fixture_offload', shas)])]

    def row(rid, lines, applications):
        return {'id': rid, 'reason': 'fixture site-finder region',
                'why': {'query_sha256': 'a' * 64, 'statements': ['fixture-loop'],
                        'source': {'path': 'kernel.cpp', 'revision': 'full-source-fixture', 'lines': lines},
                        'applications': applications}}
    data['iterations'] = [{'index': 1, 'started': '2026-10-11T00:00:00+00:00', 'ended': '2026-10-11T00:00:00+00:00',
                           'regions': [row(*c) for c in chosen],
                           'provider_calls': [], 'candidates': [], 'feedback_reasons': [], 'improved_classes': [],
                           'site_finder': {'query_sha256': 'a' * 64}}]
    case.records.write('campaign_summaries/extensa-native-bfs-20261011-z9.summary.yaml', data)


def revision_tree(case):
    snapshot(case.records, 'fixture.revision.source', tree(case.tmp_path, 'revision', REVISION), revision='full-source-fixture')


def attribute_catalog(case, library, revision=True, rid='fixture.attribution'):
    args = ['attribute', '--records', case.records.path, '--baseline-estimate', 'fixture.baseline',
            '--candidate-estimate', 'fixture.candidate', '--baseline-source', 'fixture.baseline.source',
            '--candidate-source', 'fixture.candidate.source', '--library', library,
            '--site-finder', 'extensa-native-bfs-20261011-z9.summary', '--id', rid, '--format', 'json']
    if revision:
        args += ['--site-finder-source', 'fixture.revision.source']
    result = run_swdb(*args)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def catalog_estimates(case):
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    # Baseline: the untouched loop has logical offload counts (6 requests -> 6 s in `fetch_queue`);
    # the rewritten loop has none, so the offload entry cannot run on it (`needs_rewritten_counts`).
    case.estimate('fixture.baseline', [offloaded(case, 'base.untouched', b, 3, 40, 6), offloaded(case, 'base.rewritten', b, 7, 60)])
    # Candidate (total 85 s): the untouched loop 40 s (matched to base.untouched); the rewritten
    # loop 30 s; `cand.mixed` (10 s) sits in `rewritten` (lines 8-9) and carries an access inlined
    # from `untouched` (line 4); `cand.tail` (5 s) is a second region of function `rewritten`
    # (lines 9-10), outside both site-finder loops.
    mixed = offloaded(case, 'cand.mixed', c, 8, 10, 5)
    mixed['access_patterns'].append({**mixed['access_patterns'][0], 'id': 'cand.mixed.inlined',
                                     'source_location': {'function': 'fixture', 'line': 4, 'path': str(c)}})
    case.estimate('fixture.candidate', [offloaded(case, 'cand.untouched', c, 3, 40, 6),
                                        offloaded(case, 'cand.rewritten', c, 7, 30, 6), mixed,
                                        offloaded(case, 'cand.tail', c, 9, 5, 0)])


def catalog_case(case, revision=True, chosen=None):
    offload_target(case)
    library, shas = catalog_library(case)
    site_finder_summary(case, shas, chosen)
    revision_tree(case)
    catalog_estimates(case)
    return attribute_catalog(case, library, revision)


def test_catalog_bound_runs_on_baseline_counts_and_ranks_known_bounds_before_floor_only_and_unknown_regions(case):
    report = catalog_case(case)
    base, cand = rows(report, 'baseline'), rows(report, 'candidate')
    assert (cand['cand.untouched']['seconds'], cand['cand.rewritten']['seconds'], cand['cand.mixed']['seconds']) == (40, 30, 10)
    # F35 (spec F6): the entry runs on the baseline counts. The untouched candidate loop reads its
    # matched baseline loop's 6 requests -> 6 s; headroom 40 / 6.
    bound = cand['cand.untouched']['catalog_bound']
    assert cand['cand.untouched']['matched_region'] == 'base.untouched'
    assert (bound['seconds'], bound['entry'], bound['reason'], bound['mixed']) == (pytest.approx(6), 'operation.fixture_offload', None, False)
    assert bound['site_finder_regions'] == [UNTOUCHED_SF]
    assert bound['joins'] == [{'site_finder_region': UNTOUCHED_SF, 'join': 'lines', 'path': 'kernel.cpp', 'lines': [3, 4], 'reason': None}]
    assert [(m['model'], m['accounting'], m['seconds']) for m in bound['entries'][0]['mechanisms']] == [
        ('fetch_queue', 'resource_bound', pytest.approx(6))]
    assert cand['cand.untouched']['headroom'][1] == {'limit': 'catalog_bound', 'value': pytest.approx(40 / 6), 'reason': None}
    assert base['base.untouched']['catalog_bound']['seconds'] == pytest.approx(6)
    # A rewritten candidate region has no baseline region, so no baseline counts (F35).
    rewritten = cand['cand.rewritten']['catalog_bound']
    assert (rewritten['seconds'], rewritten['reason'], rewritten['site_finder_regions']) == (None, 'no_baseline_counts', [REWRITTEN_SF])
    # Partial overlap (F21): both loops joined, `mixed` because line 9 lies outside both.
    mixed = cand['cand.mixed']['catalog_bound']
    assert (mixed['mixed'], mixed['site_finder_regions'], mixed['reason']) == (True, [REWRITTEN_SF, UNTOUCHED_SF], 'no_baseline_counts')
    # F30: a second region of function `rewritten`, outside its site-finder loop, joins nothing.
    tail = cand['cand.tail']['catalog_bound']
    assert (tail['seconds'], tail['reason'], tail['site_finder_regions'], tail['mixed']) == (None, 'no_catalog_match', [], False)
    # Needs rewritten counts: unknown with a named reason, never free.
    needs = base['base.rewritten']['catalog_bound']
    assert (needs['seconds'], needs['reason']) == (None, 'needs_rewritten_counts')
    assert 'address_stream_counts.requested_target_description' in needs['missing']
    # Ranking (F7, F36): 40/85 x (1 - 6/40) = 0.4; then the floor-only region (no_catalog_match);
    # then every unknown catalog bound with its reason, in region-ID order.
    assert [(r['position'], r['region'], r['tier'], r['limit'], r['reason']) for r in report['ranking']] == [
        (1, 'cand.untouched', 'remaining_gain_bound', 'catalog_bound', None),
        (2, 'cand.tail', 'floor_headroom', 'resource_floor', None),
        (3, 'cand.mixed', 'unknown', 'catalog_bound', 'no_baseline_counts'),
        (4, 'cand.rewritten', 'unknown', 'catalog_bound', 'no_baseline_counts')]
    assert [r['value'] for r in report['ranking']] == [pytest.approx(0.4), pytest.approx(1.0), None, None]
    assert 'Clamped at 0' in report['ranking_rule']['remaining_gain_bound']
    finder = report['site_finder']
    assert (finder['campaign_summary']['id'], finder['iteration']) == ('extensa-native-bfs-20261011-z9.summary', 1)
    assert finder['revision_source']['id'] == 'fixture.revision.source'
    assert [(r['id'], r['function'], r['entries']) for r in finder['regions']] == [
        (REWRITTEN_SF, 'rewritten', ['operation.fixture_offload']), (UNTOUCHED_SF, 'untouched', ['operation.fixture_offload'])]
    assert finder['regions'][0]['placements'] == [
        {'source': 'fixture.baseline.source', 'join': 'lines', 'path': 'kernel.cpp', 'lines': [7, 8], 'reason': None},
        {'source': 'fixture.candidate.source', 'join': 'lines', 'path': 'kernel.cpp', 'lines': [7, 8], 'reason': None}]


def test_without_a_revision_tree_the_whole_function_joins_and_says_so(case):
    report = catalog_case(case, revision=False)
    tail = rows(report, 'candidate')['cand.tail']['catalog_bound']
    assert tail['joins'] == [{'site_finder_region': REWRITTEN_SF, 'join': 'function', 'path': 'kernel.cpp',
                              'lines': [6, 9], 'reason': 'no_revision_tree'}]
    assert 'revision_source' not in report['site_finder']


def test_a_site_finder_region_that_cannot_be_placed_makes_the_bound_unknown_not_no_match(case):
    report = catalog_case(case, chosen=[('stub-impl/vanished:10-11', [10, 11], [application('operation.fixture_offload', {})])])
    placements = report['site_finder']['regions'][0]['placements']
    assert {(p['join'], p['path'], p['reason']) for p in placements} == {(None, 'kernel.cpp', 'function_not_in_tree')}
    for side in ('baseline', 'candidate'):
        for row in rows(report, side).values():
            assert (row['catalog_bound']['seconds'], row['catalog_bound']['reason']) == (None, 'site_finder_unplaced')
            assert row['catalog_bound']['unplaced_site_finder_regions'] == ['stub-impl/vanished:10-11']
    assert {r['tier'] for r in report['ranking']} == {'unknown'}


def test_entry_reasons_unknown_entries_and_an_mmio_entry_against_a_functional_description(case):
    offload_target(case)
    library, shas = catalog_library(case)
    # Untouched loop: an entry the library lacks, one changed since the site finder hashed it and
    # one with no hash. Rewritten loop: the MMIO-intrinsic entry (F28: no family mapping).
    site_finder_summary(case, shas, [
        (UNTOUCHED_SF, [63, 64], [application('operation.absent', shas), application('operation.fixture_offload', shas, 'f' * 64),
                                  application('operation.fixture_cpu', shas, False)]),
        (REWRITTEN_SF, [67, 68], [application('operation.fixture_mmio', shas)])])
    revision_tree(case)
    catalog_estimates(case)
    report = attribute_catalog(case, library)
    base = rows(report, 'baseline')
    unknown = base['base.untouched']['catalog_bound']
    assert [(e['entry'], e['reason']) for e in unknown['entries']] == [
        ('operation.absent', 'not_in_library'), ('operation.fixture_cpu', 'entry_unhashed'),
        ('operation.fixture_offload', 'entry_changed')]
    assert (unknown['seconds'], unknown['reason']) == (None, 'unknown_catalog_entry')
    mmio = base['base.rewritten']['catalog_bound']
    assert [(e['entry'], e['reason']) for e in mmio['entries']] == [('operation.fixture_mmio', 'no_offload_mechanism')]
    assert (mmio['seconds'], mmio['reason']) == (None, 'no_catalog_match')
    ranked = {r['region']: (r['tier'], r['reason']) for r in report['ranking']}
    assert ranked['cand.untouched'] == ('unknown', 'unknown_catalog_entry')


def test_an_entry_slower_than_the_region_clamps_at_zero_and_ties_go_by_floor_headroom(case):
    # F29: both untouched candidate regions read 50 baseline requests (50 s) but now run in 20 s
    # and 30 s, so both remaining gain bounds clamp to 0. cand.b's floor headroom (30 / 10) beats
    # cand.a's (20 / 20), so it ranks first although its ID sorts later.
    offload_target(case)
    library, shas = catalog_library(case)
    site_finder_summary(case, shas, [(UNTOUCHED_SF, [63, 64], [application('operation.fixture_offload', shas)])])
    revision_tree(case)
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    case.estimate('fixture.baseline', [offloaded(case, 'base.a', b, 3, 1, 50), offloaded(case, 'base.b', b, 2, 1, 50),
                                       offloaded(case, 'base.rewritten', b, 7, 60)])
    case.estimate('fixture.candidate', [offloaded(case, 'cand.a', c, 3, 20, 0), offloaded(case, 'cand.b', c, 2, 10, 30)])
    report = attribute_catalog(case, library)
    cand = rows(report, 'candidate')
    assert (cand['cand.a']['catalog_bound']['seconds'], cand['cand.b']['catalog_bound']['seconds']) == (pytest.approx(50), pytest.approx(50))
    assert [(r['region'], r['tier'], r['value']) for r in report['ranking']] == [
        ('cand.b', 'remaining_gain_bound', 0.0), ('cand.a', 'remaining_gain_bound', 0.0)]


def test_catalog_bounds_validate_are_indexed_and_pin_the_site_finder_summary(case):
    catalog_case(case)
    checked = case.records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr
    db = case.tmp_path / 'index.sqlite'
    query = lambda sql: json.loads(run_swdb('sql', sql, '--records', case.records.path, '--db', db, '--format', 'json').stdout)
    assert query("SELECT region, limit_seconds, limiting_term, headroom, reason FROM swdb_attribution_headroom "
                 "WHERE side = 'candidate' AND limit_name = 'catalog_bound' ORDER BY region") == [
        {'region': 'cand.mixed', 'limit_seconds': None, 'limiting_term': None, 'headroom': None, 'reason': 'no_baseline_counts'},
        {'region': 'cand.rewritten', 'limit_seconds': None, 'limiting_term': None, 'headroom': None, 'reason': 'no_baseline_counts'},
        {'region': 'cand.tail', 'limit_seconds': None, 'limiting_term': None, 'headroom': None, 'reason': 'no_catalog_match'},
        {'region': 'cand.untouched', 'limit_seconds': 6.0, 'limiting_term': 'operation.fixture_offload',
         'headroom': pytest.approx(40 / 6), 'reason': None}]
    assert query("SELECT side, region, entry, seconds, reason, mixed FROM swdb_attribution_catalog ORDER BY side, region, entry") == [
        {'side': 'baseline', 'region': 'base.rewritten', 'entry': 'operation.fixture_offload', 'seconds': None,
         'reason': 'needs_rewritten_counts', 'mixed': 0},
        {'side': 'baseline', 'region': 'base.untouched', 'entry': 'operation.fixture_offload', 'seconds': 6.0, 'reason': None, 'mixed': 0},
        {'side': 'candidate', 'region': 'cand.mixed', 'entry': 'operation.fixture_offload', 'seconds': None,
         'reason': 'no_baseline_counts', 'mixed': 1},
        {'side': 'candidate', 'region': 'cand.rewritten', 'entry': 'operation.fixture_offload', 'seconds': None,
         'reason': 'no_baseline_counts', 'mixed': 0},
        {'side': 'candidate', 'region': 'cand.untouched', 'entry': 'operation.fixture_offload', 'seconds': 6.0, 'reason': None, 'mixed': 0}]
    assert query("SELECT tier, region FROM swdb_attribution_ranking ORDER BY position") == [
        {'tier': 'remaining_gain_bound', 'region': 'cand.untouched'}, {'tier': 'floor_headroom', 'region': 'cand.tail'},
        {'tier': 'unknown', 'region': 'cand.mixed'}, {'tier': 'unknown', 'region': 'cand.rewritten'}]
    revision = case.records.path / 'source_snapshots' / 'fixture.revision.source.yaml'
    revision.write_text(revision.read_text().replace('status: draft', 'status: accepted', 1))
    edited = case.records.validate()
    assert edited.returncode == 1 and 'site_finder' in edited.stdout + edited.stderr
    revision.write_text(revision.read_text().replace('status: accepted', 'status: draft', 1))
    summary = case.records.path / 'campaign_summaries' / 'extensa-native-bfs-20261011-z9.summary.yaml'
    summary.write_text(summary.read_text().replace('status: draft', 'status: accepted', 1))
    changed = case.records.validate()
    assert changed.returncode == 1 and 'site_finder' in changed.stdout + changed.stderr


# --- Ticket 09: split check against measured region thread-CPU time (2026-10-11 ET; F15, F18, F19, F23)
#
# A `region_profile` from `swdb bfs-profile` per side gives each source scope's exclusive
# thread-CPU seconds by file and line. The fixture kernel's scopes (lines of BASELINE):
#   function `untouched` [2, 5] > loop [3, 4];  function `rewritten` [6, 9] > loop [7, 8].
# The rewrite site is lines 7-8 on both sides. A function's exclusive time lies on its lines
# outside its nested loop ([2, 5] minus [3, 4] = {2, 5}; [6, 9] minus [7, 8] = {6, 9}), so both
# functions' own time is untouched; only the loop at 7-8 is rewritten.

SCOPES = [('function', 'untouched', [2, 5], [0, 70]), ('loop', 'for', [3, 4], [20, 50]),
          ('function', 'rewritten', [6, 9], [80, 150]), ('loop', 'for', [7, 8], [100, 140])]


def region_profile(case, rid, side, seconds, workload='tiny-sym', created=None, tree=None):
    """A measured profile of one side's tree; `seconds` = exclusive s per SCOPES row."""
    source = case.records.read(f'source_snapshots/fixture.{tree or side}.source.yaml')
    estimate = case.records.read(f'estimates/fixture.{side}.yaml')
    day = created or str(estimate['created'])
    regions = []
    for (kind, name, lines, byte_range), value in zip(SCOPES, seconds):
        regions.append({'id': f'{kind}:kernel.cpp:{byte_range[0]}:{side}', 'kind': kind, 'name': name, 'path': 'kernel.cpp',
                        'lines': lines, 'byte_range': byte_range, 'function': 'rewritten' if lines[0] >= 6 else 'untouched',
                        'metrics': {'inclusive_thread_cpu_seconds': value, 'exclusive_thread_cpu_seconds': value, 'invocations': 1},
                        'basis': 'measured', 'source_artifact_sha256': source['artifact']['sha256']})
    case.records.write(f'region_profiles/{rid}.yaml', {'kind': 'region_profile', 'schema_version': '0.4', 'id': rid,
        'status': 'draft', 'created': day, 'updated': day, 'message_version': '1.0',
        'producer': {'name': 'attribution-fixture', 'role': 'operator', 'test_client': True},
        'provenance': [{'id': 'fixture', 'kind': 'source_code', 'description': 'Split-check contract fixture counters.'}],
        'request': {'message_version': '1.0', 'fixture': True}, 'machine': 'testhost',
        'context': {'candidate_sha256': source['artifact']['sha256'], 'threads': 1, 'workload': {'id': workload},
                    'load_average': [1.5, 1.25, 1.0], 'lane': None},
        'outcome': {'state': 'partial', 'stage': 'profiling', 'reason': 'fixture'}, 'stages': [], 'regions': regions,
        'dynamic_memory': [], 'executions': [], 'raw_artifacts': [], 'reasons': [], 'gain_claim': False})


def split_case(case, baseline=(1, 41, 1, 57), candidate=(0, 40, 0, 40)):
    case.worked_example()
    region_profile(case, 'fixture.baseline.profile', 'baseline', baseline)
    region_profile(case, 'fixture.candidate.profile', 'candidate', candidate)


def split_checked(case, rid='fixture.attribution', *profiles):
    flags = profiles or ('--baseline-profile', 'fixture.baseline.profile', '--candidate-profile', 'fixture.candidate.profile')
    return run_swdb('attribute', '--records', case.records.path, '--baseline-estimate', 'fixture.baseline',
        '--candidate-estimate', 'fixture.candidate', '--baseline-source', 'fixture.baseline.source',
        '--candidate-source', 'fixture.candidate.source', *flags, '--id', rid, '--format', 'json')


def gaps(report):
    return {(g['side'], g['origin']): g for g in report['split_check']['gaps']}


def test_split_check_passes_when_every_measured_share_is_within_ten_points_of_its_estimate(case):
    # Estimated shares (worked example): baseline untouched 40/100, rewritten 60/100;
    # candidate untouched 40/70, rewritten 30/70; unattributed 0 on both.
    # Measured baseline: untouched 1 + 41 + 1 = 43 of 100 s, rewritten 57 (the loop at 7-8).
    # Measured candidate: untouched 40 of 80 s, rewritten 40 of 80 s.
    split_case(case)
    result = split_checked(case)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    check = report['split_check']
    assert check['verdict'] == 'passed' and check['reasons'] == []
    assert check['rule']['max_abs_share_gap'] == 0.1
    found = gaps(report)
    assert found['baseline', 'untouched']['measured_share'] == pytest.approx(0.43)
    assert found['baseline', 'untouched']['gap'] == pytest.approx(0.03)
    assert found['baseline', 'agent_rewritten']['measured_share'] == pytest.approx(0.57)
    assert found['baseline', 'agent_rewritten']['gap'] == pytest.approx(-0.03)
    assert found['candidate', 'untouched']['measured_share'] == pytest.approx(0.5)
    assert found['candidate', 'untouched']['gap'] == pytest.approx(0.5 - 4 / 7)
    assert found['candidate', 'agent_rewritten']['gap'] == pytest.approx(0.5 - 3 / 7)
    assert found['candidate', 'unattributed']['measured_share'] == 0 and found['candidate', 'unattributed']['gap'] == 0
    assert all(g['within_rule'] for g in check['gaps'])
    measured = {(m['side'], m['origin']): m['seconds'] for m in check['measured_shares']}
    assert measured['baseline', 'untouched'] == pytest.approx(43) and measured['candidate', 'agent_rewritten'] == pytest.approx(40)
    scopes = {(r['side'], tuple(r['lines'])): r['origin'] for r in check['regions']}
    assert scopes['baseline', (6, 9)] == 'untouched' and scopes['baseline', (7, 8)] == 'agent_rewritten'
    assert check['profiles']['candidate']['load_average'] == [1.5, 1.25, 1.0]


def test_a_gap_above_ten_points_saves_a_valid_split_unverified_report(case):
    # Candidate measured: untouched 40 of 50 s = 0.8 against 40/70; rewritten 10 of 50 s = 0.2 against 30/70.
    split_case(case, candidate=(0, 40, 0, 10))
    result = split_checked(case)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    check = report['split_check']
    assert check['verdict'] == 'split_unverified'
    assert check['reasons'] == [{'side': 'candidate', 'origin': 'untouched', 'reason': 'gap_above_rule'},
                                {'side': 'candidate', 'origin': 'agent_rewritten', 'reason': 'gap_above_rule'}]
    found = gaps(report)
    assert found['candidate', 'untouched']['gap'] == pytest.approx(0.8 - 4 / 7)
    assert found['candidate', 'untouched']['within_rule'] is False
    assert found['baseline', 'untouched']['within_rule'] is True
    checked = case.records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr


def test_an_unknown_estimated_share_makes_the_split_unverified_with_its_reason(case):
    # The candidate's rewritten loop is unknown, so its total and every candidate share are unknown.
    b, c = case.base_root / 'kernel.cpp', case.cand_root / 'kernel.cpp'
    case.estimate('fixture.baseline', [region('base.loop.untouched', b, 3, 40), region('base.loop.rewritten', b, 7, 60)])
    case.estimate('fixture.candidate', [region('cand.loop.untouched', c, 3, 40), region('cand.loop.rewritten', c, 7, None)])
    region_profile(case, 'fixture.baseline.profile', 'baseline', (1, 41, 1, 57))
    region_profile(case, 'fixture.candidate.profile', 'candidate', (0, 40, 0, 40))
    result = split_checked(case)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    check = report['split_check']
    assert check['verdict'] == 'split_unverified'
    assert [r for r in check['reasons'] if r['side'] == 'candidate'] == [
        {'side': 'candidate', 'origin': origin, 'reason': 'unknown_estimated_share'}
        for origin in ('untouched', 'agent_rewritten', 'unattributed')]
    found = gaps(report)
    assert found['candidate', 'agent_rewritten']['gap'] is None and found['candidate', 'agent_rewritten']['within_rule'] is None
    assert found['candidate', 'agent_rewritten']['measured_share'] == pytest.approx(0.5)
    assert found['baseline', 'agent_rewritten']['within_rule'] is True


@pytest.mark.parametrize('profile, message', [
    ({'workload': 'tiny-sym-b'}, "input 'tiny-sym-b'"),         # F18: another input
    ({'tree': 'baseline'}, 'another source tree'),               # the baseline tree timed as the candidate
    ({'created': '2026-01-01'}, 'prospective'),                  # timed before the estimates were saved
])
def test_a_profile_of_another_input_tree_or_an_earlier_date_is_refused_and_nothing_is_written(case, profile, message):
    case.worked_example()
    region_profile(case, 'fixture.baseline.profile', 'baseline', (1, 41, 1, 57))
    region_profile(case, 'fixture.candidate.profile', 'candidate', (0, 40, 0, 40), **profile)
    result = split_checked(case)
    assert result.returncode == 1
    assert message in result.stderr and 'refusing' in result.stderr
    assert not (case.records.path / 'attributions').exists()


def test_one_profile_alone_is_refused(case):
    split_case(case)
    result = split_checked(case, 'fixture.attribution', '--baseline-profile', 'fixture.baseline.profile')
    assert result.returncode == 1 and 'go together' in result.stderr
    assert not (case.records.path / 'attributions').exists()


def test_split_check_is_byte_identical_validated_indexed_and_pins_its_profiles(case):
    split_case(case, candidate=(0, 40, 0, 10))
    first = split_checked(case)
    assert first.returncode == 0, first.stdout + first.stderr
    path = case.records.path / 'attributions' / 'fixture.attribution.yaml'
    written = path.read_bytes()
    path.unlink()
    assert split_checked(case).stdout == first.stdout and path.read_bytes() == written
    # Without profiles the report has no split_check (absent = not checked).
    assert 'split_check' not in attributed(case, rid='fixture.unchecked')
    checked = case.records.validate()
    assert checked.returncode == 0, checked.stdout + checked.stderr
    db = case.tmp_path / 'index.sqlite'

    def query(sql):
        rows = run_swdb('sql', sql, '--records', case.records.path, '--db', db, '--format', 'json')
        assert rows.returncode == 0, rows.stdout + rows.stderr
        return json.loads(rows.stdout)
    assert query('SELECT attribution, verdict, max_abs_share_gap, baseline_profile, candidate_profile FROM swdb_attribution_split_checks') == [
        {'attribution': 'fixture.attribution', 'verdict': 'split_unverified', 'max_abs_share_gap': 0.1,
         'baseline_profile': 'fixture.baseline.profile', 'candidate_profile': 'fixture.candidate.profile'}]
    rows = query("SELECT side, origin, estimated_share, measured_share, measured_seconds, within_rule FROM swdb_attribution_split_gaps "
                 "WHERE side = 'candidate' ORDER BY origin")
    assert rows == [
        {'side': 'candidate', 'origin': 'agent_rewritten', 'estimated_share': pytest.approx(3 / 7), 'measured_share': 0.2,
         'measured_seconds': 10.0, 'within_rule': 0},
        {'side': 'candidate', 'origin': 'unattributed', 'estimated_share': 0.0, 'measured_share': 0.0, 'measured_seconds': 0.0,
         'within_rule': 1},
        {'side': 'candidate', 'origin': 'untouched', 'estimated_share': pytest.approx(4 / 7), 'measured_share': 0.8,
         'measured_seconds': 40.0, 'within_rule': 0}]
    # A changed profile, or a verdict edited to disagree with its gaps, fails validation.
    original = path.read_text()
    profile = case.records.path / 'region_profiles' / 'fixture.candidate.profile.yaml'
    profile.write_text(profile.read_text().replace('status: draft', 'status: accepted', 1))
    changed = case.records.validate()
    assert changed.returncode == 1 and 'split_check' in changed.stdout + changed.stderr
    profile.write_text(profile.read_text().replace('status: accepted', 'status: draft', 1))
    data = yaml.safe_load(original)
    data['split_check']['verdict'] = 'passed'
    data.pop('identity_sha256')
    data['identity_sha256'] = digest(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    edited = case.records.validate()
    assert edited.returncode == 1 and 'verdict' in edited.stdout + edited.stderr


def test_a_site_finder_report_records_its_kernel_and_target_and_is_indexed_for_the_site_finder(case):
    """Ticket 10 (2026-10-11 ET): the site finder finds the latest report by kernel and target and
    maps its ranked regions back to site-finder region IDs through the index alone."""
    report = catalog_case(case)
    # the fixture summary is the a8 native summary: its site finder ran on gapbs-bfs, native_cpu
    assert (report['site_finder']['kernel'], report['site_finder']['target']) == ('gapbs-bfs', 'native_cpu')
    assert 'split_check' not in report
    db = case.tmp_path / 'index.sqlite'
    query = lambda sql: json.loads(run_swdb('sql', sql, '--records', case.records.path, '--db', db, '--format', 'json').stdout)
    assert query("SELECT campaign_summary, iteration, kernel, target FROM swdb_attribution_site_finder") == [
        {'campaign_summary': 'extensa-native-bfs-20261011-z9.summary', 'iteration': 1, 'kernel': 'gapbs-bfs',
         'target': 'native_cpu'}]
    assert query("SELECT region, site_finder_region FROM swdb_attribution_site_finder_regions "
                 "WHERE side = 'candidate' ORDER BY region, site_finder_region") == [
        {'region': 'cand.mixed', 'site_finder_region': REWRITTEN_SF},
        {'region': 'cand.mixed', 'site_finder_region': UNTOUCHED_SF},
        {'region': 'cand.rewritten', 'site_finder_region': REWRITTEN_SF},
        {'region': 'cand.untouched', 'site_finder_region': UNTOUCHED_SF}]
