"""Native-CPU candidate certification (certify 1.3 isolation and 1.4 blinding). Created: 2026-10-05 ET (ticket 75).

contract.bfs_tdstep_frontier_staging pins the native candidate profile; `swdb certify` runs its
matrix and its four seam faults with ticket 70's isolation. The exact a8 tree certifies with every
control rejected by its own named check; variants with a real bug, or without the transformation a
control guards, do not.
"""
import difflib
import json
import tempfile
from pathlib import Path

import pytest

from swdb import certification as c
from swdb import certification_isolation as isolation
from swdb import certification_native as native
from swdb.certification_feedback import STRICT_MESSAGES
from swdb.cli import UsageError
from swdb.library import Library
from swdb.store import Store
from testkit.toolchain import require_gcc_openmp as _gcc

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / 'library'
CONTRACT = 'contract.bfs_tdstep_frontier_staging'
SNAPSHOT = 'bfs-dx100-scalar-only-20260929-a1.source'
PATCH = LIBRARY / 'native/bfs-tdstep-frontier-staging.patch'
BFS = 'benchmarks/gapbs/src/bfs.cc'
A8_ARTIFACT = '7acca955a1f85a8563280d57b3d4e594bd0312393aeff946eda92f1577ad6ea3'
CLAIM = """                        if (compare_and_swap(parents[v], curr_val, u)) {
                            lqueue.push_back(v);"""
TAIL = 'const size_t staged_count = remaining < kFrontierBatch ? remaining : kFrontierBatch;'
BOUNDS = """                staged_begin[lane] = offsets[u];
                staged_end[lane] = offsets[u + 1];"""




def _variant(tmp_path, transform, name='variant.patch', *, certification_store):
    """A -p1 patch of the snapshot whose bfs.cc is the a8 rewrite passed through ``transform``."""
    with tempfile.TemporaryDirectory(dir=tmp_path) as temporary:
        tree, _ = c.materialize_snapshot(certification_store, SNAPSHOT, Path(temporary))
        original = (tree / BFS).read_text()
        c.apply_patch(tree, PATCH)
        text = transform((tree / BFS).read_text())
    diff = ''.join(difflib.unified_diff(original.splitlines(True), text.splitlines(True),
                                        fromfile='a/' + BFS, tofile='b/' + BFS))
    path = tmp_path / name
    path.write_text(diff)
    return path


def _replace(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)


def _candidate_record(tmp_path, sha=A8_ARTIFACT, snapshot=SNAPSHOT):
    path = tmp_path / 'candidate.yaml'
    path.write_text(json.dumps({'kind': 'candidate', 'id': 'extensa-native-bfs-20261005-a8.it1.kronecker.a0',
                                'mode': 'extensa', 'campaign': 'extensa-native-bfs-20261005-a8',
                                'source_snapshot': snapshot, 'artifact': {'sha256': sha}}))
    return path


def _certify(tmp_path, monkeypatch, patch, *, certification_store, **options):
    _gcc()
    monkeypatch.setattr(c.workflow, 'persist', lambda *args, **kwargs: None)
    return c.certify(certification_store, CONTRACT, snapshot=SNAPSHOT, patch=patch, runs_dir=tmp_path / 'runs',
                     **options)


def _status(record):
    return {(x['id'], x['build']): x['status'] for x in record['negative_controls']}


# --- profile, scope and records (no build) ---------------------------------------------------------

def test_contract_pins_a_valid_native_profile_and_validates():
    catalog = Library(LIBRARY)
    assert not [p for p in catalog.validate() if CONTRACT in str(p.path) or 'native' in str(p.path)]
    entry = catalog.get(CONTRACT)
    assert native.is_native(entry) and entry['uses_intrinsics'] == [] and entry['uses_library_operations'] == []
    profile = native.load_profile(catalog, entry)
    assert {c['id'] for c in profile['data']['controls']} == {c['id'] for c in entry['negative_controls']}
    clauses = {cl['id']: cl['negative_control'] for cl in entry['clauses']}
    assert clauses['C2'] == {'id': 'claim_without_write', 'check': 'verifier'}
    assert clauses['S1'] == {'id': 'partial_batch_dropped', 'check': 'frontier_size_equality'}
    assert clauses['S2'] == {'id': 'stale_row_offset', 'check': 'verifier'}
    assert set(entry['preservation_obligations']) == {'frontier_size_equality', 'once_enqueue'}


def test_profile_controls_must_equal_the_contract_controls():
    catalog = Library(LIBRARY)
    entry = dict(catalog.get(CONTRACT))
    entry['negative_controls'] = entry['negative_controls'][:-1]
    with pytest.raises(UsageError, match='differ from the contract negative_controls'):
        native.load_profile(catalog, entry)


def test_native_witness_record_is_parsed_and_judged(tmp_path):
    path = tmp_path / 'run.record'
    path.write_text('begin 1\nfrontier 1 0\nfrontier 2 1 2\nresult i32 3 0 0 0\nwitness claims=2 pushes=2\nend\n')
    parsed = isolation.parse_records(path, set(STRICT_MESSAGES))
    assert parsed['claims'] == 2 and parsed['pushes'] == 2 and not parsed['invalid']
    run = {'returncode': 0, 'timeout': False, 'stdout': '', 'stderr': ''}
    good = isolation.judge(run, parsed, [1, 2], check_result=lambda v: {'passed': True}, result_kind='i32',
                           witness=native.witness_ok)
    assert good['passed']
    parsed['claims'] = 0
    bad = isolation.judge(run, parsed, [1, 2], check_result=lambda v: {'passed': True}, result_kind='i32',
                          witness=native.witness_ok)
    assert bad['reason'] == 'execution_witness'


def test_edit_outside_tdstep_is_refused_before_any_build(tmp_path, monkeypatch, *, certification_store):
    patch = _variant(tmp_path, lambda text: _replace(text, 'int alpha = 1, int beta = 18) {',
                                                     'int alpha = 1, int beta = 18) {\n    (void)alpha;'), certification_store=certification_store)
    with pytest.raises(UsageError, match='outside void TDStep'):
        _certify(tmp_path, monkeypatch, patch, certification_store=certification_store)


QUEUE_PROBE = """#ifndef QueueBuffer
            if (staged_count > 0) continue;  // target build only: never expand
#endif
"""


@pytest.mark.parametrize('name,transform,message', [
    ('directive', lambda text: _replace(text, TAIL, TAIL + '\n' + QUEUE_PROBE), 'harness scan.*#ifndef'),
    ('defined', lambda text: _replace(text, TAIL, TAIL + '\n#if defined(QueueBuffer)\n#endif'), 'harness scan'),
    ('extra_global', lambda text: _replace(text, '\nint64_t TDStep2(', '\nstatic int extra_global = 0;\n\nint64_t TDStep2('),
     'exactly one function definition'),
    ('signature', lambda text: _replace(text, 'SlidingQueue<NodeID> &queue, int num_nodes, int num_edges) {',
                                        'SlidingQueue<NodeID> &queue, int num_nodes, int num_edges, int x = 0) {'),
     'signature'),
])
def test_scope_and_directive_refusals_before_any_build(tmp_path, monkeypatch, name, transform, message, *, certification_store):
    """Ticket 75 review: a candidate cannot detect the certification build or add code outside TDStep."""
    with pytest.raises(UsageError, match=message):
        _certify(tmp_path, monkeypatch, _variant(tmp_path, transform, certification_store=certification_store), certification_store=certification_store)


def test_native_profile_sources_cannot_be_overridden(tmp_path, monkeypatch, *, certification_store):
    with pytest.raises(UsageError, match='pins its sources'):
        _certify(tmp_path, monkeypatch, PATCH, sources=(1,), certification_store=certification_store)


def test_witness_of_another_target_invalidates_the_record(tmp_path):
    path = tmp_path / 'run.record'
    path.write_text('begin 1\nfrontier 1 0\nresult i32 1 0\nwitness claims=1 pushes=1\nend\n')
    parsed = isolation.parse_records(path, set(STRICT_MESSAGES))
    run = {'returncode': 0, 'timeout': False, 'stdout': '', 'stderr': ''}
    dx100 = isolation.judge(run, parsed, [1], check_result=lambda v: {'passed': True}, result_kind='i32')
    assert dx100['reason'] == 'record_invalid'


def test_candidate_record_must_match_the_patched_tree(tmp_path, monkeypatch, *, certification_store):
    with pytest.raises(UsageError, match='differs from the candidate record artifact'):
        _certify(tmp_path, monkeypatch, PATCH, candidate_record=_candidate_record(tmp_path, sha='0' * 64), certification_store=certification_store)


# --- full certifications -------------------------------------------------------------------------------

@pytest.mark.parametrize('version', ['1.3', '1.4'])
def test_exact_a8_tree_certifies_with_every_control_rejected_by_its_check(tmp_path, monkeypatch, version, *, certification_store):
    record = _certify(tmp_path, monkeypatch, PATCH, candidate_record=_candidate_record(tmp_path), version=version, certification_store=certification_store)
    assert record['verdict'] == 'certified' and record['command']['version'] == version
    assert json.loads(json.dumps(record)) == record   # persistable: the writer refuses non-JSON records
    assert record['candidate']['tree_sha256'] == A8_ARTIFACT
    assert record['candidate']['id'] == 'extensa-native-bfs-20261005-a8.it1.kronecker.a0'
    assert record['candidate']['scan']['findings'] == 0
    assert record['profile']['target'] == 'native_cpu'
    assert len(record['matrix']) == 22 and all(x['status'] == 'passed' for x in record['matrix'])
    assert set(_status(record).values()) == {'rejected'} and len(record['negative_controls']) == 8
    assert all(row['matched'] and row['enforceable'] for row in record['clause_controls'])
    for build in ('o3', 'o1g'):
        cells = [x for x in record['matrix'] if x['build'] == build]
        faults = [x for x in record['negative_controls'] if x['build'] == build]
        # One candidate object per build: the positive cells and every control link it.
        assert len({x['candidate_object_sha256'] for x in cells + faults}) == 1
        assert all('SWDB_NATIVE_FAULT' not in ' '.join(x['compile']['command']) for x in faults)
        if version == '1.3':
            assert len({x['seam_object_sha256'] for x in faults}) == len(faults)
            assert all(x['fault']['delivery'] == 'separate_object' for x in faults)
        else:
            # 1.4: one binary for every run of the build, blinded plans with distinct nonces, every
            # rejection attributed to its fault, and a clean seam witness on every positive cell.
            assert len({x['binary_sha256'] for x in cells + faults}) == 1
            assert all(x['fault']['delivery'] == 'run_plan' and x['attribution']['attributed'] for x in faults)
            assert len({x['plan']['nonce'] for x in cells + faults}) == len(cells + faults)
            assert all(x['seam_witness']['problems'] == [] for x in cells)
            assert len([row for row in record['profile']['schedule'] if row['build'] == build]) == len(cells + faults)
        for control in faults:
            assert control['expected_check'] in control['observed_checks']
            assert control['graph'] == ('staging-tail-17' if control['id'] == 'partial_batch_dropped'
                                        else 'two-level-degree-17000')


@pytest.mark.parametrize('version', ['1.3', '1.4'])
def test_keeping_the_post_claim_store_leaves_claim_without_write_alive(tmp_path, monkeypatch, version, *, certification_store):
    """C2's control discriminates: with the store kept, a non-writing claim is masked."""
    patch = _variant(tmp_path, lambda text: _replace(text, CLAIM, CLAIM.replace(
        'lqueue.push_back(v);', 'parents[v] = u;\n                            lqueue.push_back(v);')), certification_store=certification_store)
    record = _certify(tmp_path, monkeypatch, patch, version=version, certification_store=certification_store)
    assert all(x['status'] == 'passed' for x in record['matrix'])
    assert {k: v for k, v in _status(record).items() if v != 'rejected'} == {
        ('claim_without_write', 'o3'): 'survived', ('claim_without_write', 'o1g'): 'survived'}
    assert record['verdict'] == 'failed'
    assert [r['clause'] for r in record['clause_controls'] if not r['matched']] == ['C2']


def test_a_real_dropped_partial_batch_fails_the_matrix(tmp_path, monkeypatch, *, certification_store):
    patch = _variant(tmp_path, lambda text: _replace(text, TAIL, TAIL.replace('? remaining :', '? 0 :')), certification_store=certification_store)
    record = _certify(tmp_path, monkeypatch, patch, certification_store=certification_store)
    assert record['verdict'] == 'failed'
    failed = [x for x in record['matrix'] if x['status'] == 'failed']
    assert failed and all('frontier_size_equality' in x['observed_checks'] for x in failed)


def test_a_real_stale_row_offset_fails_the_matrix(tmp_path, monkeypatch, *, certification_store):
    patch = _variant(tmp_path, lambda text: _replace(text, BOUNDS, BOUNDS.replace(
        'offsets[u];', 'offsets[staged_vertices[lane + 1 < staged_count ? lane + 1 : lane]];')), certification_store=certification_store)
    record = _certify(tmp_path, monkeypatch, patch, certification_store=certification_store)
    assert record['verdict'] == 'failed'
    failed = [x for x in record['matrix'] if x['status'] == 'failed']
    assert failed and all('verifier' in x['observed_checks'] for x in failed)


RAW_CLAIM = """                        if (__sync_bool_compare_and_swap(&parents[v], curr_val, u)) {
                            lqueue.push_back(v);"""


def test_v14_claim_seam_bypass_fails_every_cell_on_the_seam_witness(tmp_path, monkeypatch, *, certification_store):
    """1.4 (ticket 76 mechanism): a candidate that claims with a raw builtin fails the positive matrix."""
    record = _certify(tmp_path, monkeypatch, _variant(tmp_path, lambda text: _replace(text, CLAIM, RAW_CLAIM), certification_store=certification_store),
                      version='1.4', certification_store=certification_store)
    assert record['verdict'] == 'failed'
    assert all(x['status'] == 'failed' and 'seam_witness' in x['observed_checks'] for x in record['matrix'])


def test_v14_plan_line_is_fixed_length_for_every_fault():
    assert {len(native._plan_line(fault, '0' * 32)) for fault in native.FAULT_INDEX_V14} == {43}
    assert set(native.FAULT_INDEX_V14) - {None} == set(native.ATTRIBUTION_V14)


# --- certify 1.4 native rules on synthetic records (ticket 75 review) -------------------------------------

def _records14(tmp_path, lines, name='run.record'):
    from swdb import certification_blinding as blinding
    path = tmp_path / name
    path.write_text(''.join(line + '\n' for line in lines))
    return blinding.parse_records(path, set(STRICT_MESSAGES))


# Out-adjacency 0 -> {1, 3}, 1 -> {2}; the parent buffer is at 0x1000.
ADJ = [[1, 3], [2], [], []]
NONCE = 'a' * 32
GOOD14 = ['begin 2', 'plan ' + NONCE, 'source 0', 'queue 0 abc',
          'epoch 0 1 d0:0:0', 'window 0 1 0',
          'epoch 0 4 c0:1004 p0:0:1 c0:100c p0:0:3', 'window 0 2 1 3',
          'epoch 0 2 c0:1008 p0:0:2', 'window 0 1 2',
          'epoch 0 0', 'window 0 0',
          'result i32 4 0 0 1 0', 'result_base 1000 4', 'witness claims=3 pushes=3', 'end']


def _judge14(parsed, fault=None):
    from swdb import bfs_native
    from swdb import certification_blinding as blinding
    run = {'returncode': 0, 'timeout': False, 'stdout': '', 'stderr': '', 'plan': {'fault': fault, 'nonce': NONCE}}
    return blinding.judge(run, parsed, [1, 2, 1], check_result=lambda v: bfs_native.verify_parents(ADJ, 0, v),
                          result_kind='i32', source=0, claims_address_result=True, witness=native.witness_v14)


def _replace_line(lines, old, new):
    return [new if line == old else line for line in lines]


def test_v14_native_judge_passes_a_clean_record_and_refuses_the_other_witness(tmp_path):
    assert _judge14(_records14(tmp_path, GOOD14))['passed']
    other = _replace_line(GOOD14, 'witness claims=3 pushes=3', 'witness chunks=1 operations=1')
    assert _judge14(_records14(tmp_path, other, 'b.record'))['reason'] == 'record_invalid'
    idle = _replace_line(GOOD14, 'witness claims=3 pushes=3', 'witness claims=0 pushes=0')
    assert _judge14(_records14(tmp_path, idle, 'c.record'))['reason'] == 'execution_witness'
    stray = GOOD14[:-1] + ['fault hidden 0 1 3', 'end']
    assert _judge14(_records14(tmp_path, stray, 'd.record'))['reason'] == 'record_invalid'


def _with(lines, result=None, faults=()):
    out = list(lines)
    if result:
        out = _replace_line(out, 'result i32 4 0 0 1 0', 'result i32 4 ' + ' '.join(map(str, result)))
    return out[:-1] + list(faults) + ['end']


@pytest.mark.parametrize('fault,faults,result,dropped,expected', [
    # vertex 1's claim (address 4100 = 0x1004) lost its write and parent[1] is unset: attributed
    ('claim_without_write', ['fault lost 0 2 4100 0'], [0, -1, 1, 0], False, True),
    # the lost claim's vertex ends with a valid parent: not attributed
    ('claim_without_write', ['fault lost 0 2 4100 0'], [0, 0, 1, 0], False, False),
    # vertex 1 hidden and its child 2 missing from level 2: attributed
    ('partial_batch_dropped', ['fault hidden 0 1 1'], None, True, True),
    # vertex 3 hidden (no children) and every level complete: not attributed
    ('partial_batch_dropped', ['fault hidden 0 1 3'], None, False, False),
    # u = 0 expanded over flat CSR row [2, 3) (vertex 1's row: vertex 2) and parent[2] = 0: attributed
    ('stale_row_offset', ['fault stale 0 3 0 2 3'], [0, 0, 0, 0], False, True),
    # parent[2] = 0 has no edge, but 2 is outside the recorded stale row [0, 1): not attributed
    ('stale_row_offset', ['fault stale 0 3 0 0 1'], [0, 0, 0, 0], False, False),
])
def test_v14_native_attribution_rules_both_ways(tmp_path, fault, faults, result, dropped, expected):
    lines = _with(GOOD14, result, faults)
    if dropped:
        lines = _replace_line(_replace_line(lines, 'window 0 1 2', 'window 0 0'), 'epoch 0 2 c0:1008 p0:0:2', 'epoch 0 0')
    parsed = _records14(tmp_path, lines)
    ok, evidence = native.attributed_v14(fault, parsed, None, None, ADJ, 0)
    assert ok is expected, evidence


def test_v14_repeated_hidden_lines_accumulate(tmp_path):
    parsed = _records14(tmp_path, _with(GOOD14, None, ['fault hidden 0 1 1', 'fault hidden 0 2 2 3']))
    assert parsed['native_faults']['hidden'] == [1, 2, 3] and not parsed['invalid']
