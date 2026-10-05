"""Certify 1.4: blinded controls, attributed rejections, the trusted frontier ledger.

Created: 2026-10-05 ET (ticket 76). Agent-decided under Yan-Ru's delegation; revisable.

The synthetic-record tests pin each rule of the out-of-process judge. The full certifications run
two adversarial candidates that certify under 1.3 and are refused under 1.4:

- ``probe_claim`` (ticket 70 open item 1): claims with a raw builtin, probes the claim seam on
  scratch data, and pushes a deliberate duplicate only when the probe sees the claim fault;
- ``decoy_frontier`` (open item 2): enqueues a few vertices twice in every run and hands the
  protected print a de-duplicated copy of the queue, unmasked only when a probe sees a fault.
"""
import types
from pathlib import Path

import pytest

from swdb import certification as c
from swdb import certification_blinding as blinding
from swdb import certification_feedback as feedback
from swdb import certification_isolation as isolation
from swdb.certification_faults import LIBRARY_FAULTS
from swdb.certification_feedback import STRICT_MESSAGES
from swdb.cli import Failure, UsageError
from swdb.store import Store

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = (ROOT / 'library').resolve()
CONTRACT = 'contract.bfs_read_offload'
NONCE = '0123456789abcdef0123456789abcdef'


# --- synthetic records ------------------------------------------------------------------------------

def _parse(tmp_path, lines):
    path = tmp_path / 'run.record'
    path.write_text(''.join(line + '\n' for line in lines))
    return blinding.parse_records(path, set(STRICT_MESSAGES))


def _run(fault=None, returncode=0, timeout=False, nonce=NONCE):
    return {'returncode': returncode, 'timeout': timeout, 'stdout': '', 'stderr': '',
            'plan': {'fault': fault, 'nonce': nonce}}


def _judge(run, parsed, counts=(1, 1, 1), claims_address_result=True):
    good = [0, 0, 1]
    check = lambda values: {'passed': values == good, 'reason': None if values == good else 'x'}
    return blinding.judge(run, parsed, list(counts), check_result=check, result_kind='i32', source=0, threshold=1,
                          claims_address_result=claims_address_result)


# Base 0x1000 holds the parent array: vertex v's slot is 0x1000 + 4 * v.
HEAD = ['begin 2', f'plan {NONCE}', 'source 0', 'queue 0 7f00', 'epoch 0 2 r0:0 d0:0:0', 'window 0 1 0']
LEVEL1 = ['epoch 0 3 c1:1004 p1:0:1 g:1000:1', 'window 0 1 1']
LEVEL2 = ['epoch 0 2 c0:1008 p0:0:2', 'window 0 1 2']
TAIL = ['epoch 0 0', 'window 0 0', 'result i32 3 0 0 1', 'result_base 1000 3', 'witness chunks=1 operations=5', 'end']
GOOD = HEAD + LEVEL1 + LEVEL2 + TAIL


def test_a_clean_run_passes_every_check(tmp_path):
    verdict = _judge(_run(), _parse(tmp_path, GOOD))
    assert verdict['passed'], verdict
    assert verdict['seam_witness'] == {'problems': [], 'claim_base': '0x1000'}


@pytest.mark.parametrize('level1, problem', [
    (['epoch 0 2 g:1000:1 p1:0:1', 'window 0 1 1'], 'no claim by the pushing thread'),          # raw claim
    (['epoch 0 3 c0:1004 p1:0:1 g:1000:1', 'window 0 1 1'], 'no claim by the pushing thread'),  # other thread
    (['epoch 0 3 c1:2004 p1:0:1 g:1000:1', 'window 0 1 1'], 'returned parent array'),          # other array
    (['epoch 0 3 c1:1004 p1:0:1 g:1000:1', 'window 0 2 1 2'], 'differ from the pushes'),       # direct write
    (['epoch 0 3 c1:1004 d1:0:1 g:1000:1', 'window 0 1 1'], 'direct queue pushes'),            # bypassed buffer
])
def test_seam_witness_names_each_bypass(tmp_path, level1, problem):
    verdict = _judge(_run(), _parse(tmp_path, HEAD + level1 + LEVEL2 + TAIL))
    assert not verdict['passed'] and 'seam_witness' in verdict['observed_checks']
    assert any(problem in text for text in verdict['seam_witness']['problems']), verdict['seam_witness']


def test_a_second_slid_queue_fails_the_seam_witness(tmp_path):
    decoy = ['queue 1 7f80', 'epoch 1 1 d0:1:1', 'window 1 1 1']
    verdict = _judge(_run(), _parse(tmp_path, HEAD + decoy + LEVEL1 + LEVEL2 + TAIL))
    assert verdict['reason'] == 'frontier_size_equality' or 'seam_witness' in verdict['observed_checks']
    assert any('queues were slid' in p for p in verdict['seam_witness']['problems'])


def test_the_execution_witness_needs_a_gather_from_the_claimed_array(tmp_path):
    other = [line.replace('g:1000:1', 'g:5000:1') for line in GOOD]
    assert _judge(_run(), _parse(tmp_path, other))['reason'] == 'execution_witness'


@pytest.mark.parametrize('change, reason', [
    (lambda lines: [x.replace(NONCE, 'f' * 32) for x in lines], 'record_invalid'),            # another plan
    (lambda lines: [x for x in lines if not x.startswith('plan')], 'record_invalid'),         # no plan read
    (lambda lines: lines[:7] + ['fault wait 1'] + lines[7:], 'record_invalid'),                # fault, none planned
    (lambda lines: [x.replace('c1:1004', 'C1:1004') for x in lines], 'record_invalid'),       # forged, none planned
    (lambda lines: lines[:-1], 'process_failure'),                                             # no end
])
def test_plan_binding_and_fault_free_positive_runs(tmp_path, change, reason):
    assert _judge(_run(), _parse(tmp_path, change(GOOD)))['reason'] == reason


def test_plan_lines_have_one_length_for_every_fault():
    lengths = {len(blinding.plan_line(fault, NONCE)) for fault in blinding.FAULT_INDEX}
    assert lengths == {43}
    assert set(blinding.FAULT_INDEX) - {None} == set(LIBRARY_FAULTS) == set(blinding.ATTRIBUTION)


# --- attribution ----------------------------------------------------------------------------------------

def _attributed(tmp_path, fault, lines, expected, adjacency=None):
    parsed = _parse(tmp_path, lines)
    verdict = _judge(_run(fault), parsed)
    return blinding.attributed(fault, parsed, verdict, verdict['_book'], expected, adjacency=adjacency, source=0)[0]


def test_a_duplicate_counts_for_the_claim_fault_only_behind_a_forged_claim(tmp_path):
    forged = ['epoch 0 5 c1:1004 p1:0:1 C2:1004 p2:0:1 g:1000:1', 'window 0 2 1 1']
    assert _attributed(tmp_path, 'skipped_cas_recheck', HEAD + forged + TAIL, {'duplicate_frontier'})
    # The probe's forged claim lands on scratch data; the duplicate is a deliberate second push.
    probe = ['epoch 0 5 C0:9990 c1:1004 p1:0:1 p1:0:1 g:1000:1', 'window 0 2 1 1']
    assert not _attributed(tmp_path, 'skipped_cas_recheck', HEAD + probe + TAIL, {'duplicate_frontier'})


def test_a_duplicate_counts_for_the_push_fault_only_as_the_forged_copy(tmp_path):
    forged = ['epoch 0 4 c1:1004 p1:0:1 P1:0:1 g:1000:1', 'window 0 2 1 1']
    assert _attributed(tmp_path, 'forged_frontier', HEAD + forged + TAIL, {'duplicate_frontier'})
    deliberate = ['epoch 0 5 c1:1004 p1:0:1 c2:1004 p2:0:1 g:1000:1', 'window 0 2 1 1']
    assert not _attributed(tmp_path, 'forged_frontier', HEAD + deliberate + TAIL, {'duplicate_frontier'})


@pytest.mark.parametrize('fault, attribution, expected', [
    ('chunk_off_by_one', 2, True), ('chunk_off_by_one', 1, False), ('index_wrap', 0, False),
    ('dropped_wait', 1, True), ('dropped_wait', 0, False), ('shared_context', 1, True),
    ('read_before_wait', 0, False),
])
def test_strict_failures_count_only_where_the_fault_acted(tmp_path, fault, attribution, expected):
    name = {'chunk_off_by_one': 'tile_truncation', 'index_wrap': 'stream_bounds',
            'shared_context': 'thread_ownership_tile'}.get(fault, 'read_before_wait')
    lines = HEAD + [f'strict {name} {attribution}']
    parsed = _parse(tmp_path, lines)
    verdict = _judge(_run(fault, returncode=86), parsed)
    assert verdict['reason'] == 'strict_layer_assertion'
    assert blinding.attributed(fault, parsed, verdict, verdict['_book'], {name})[0] is expected


def test_a_dropped_continuation_counts_only_for_vertices_behind_lost_edges(tmp_path):
    # 0 -> {1, 2}; edge offsets 0 and 1. The fault removed offset 1 (head 2).
    adjacency = [[1, 2], [], []]
    lines = HEAD + ['fault continuation 1 1 1', 'epoch 0 3 c1:1004 p1:0:1 g:1000:1', 'window 0 1 1'] + TAIL
    assert _attributed(tmp_path, 'dropped_continuation', lines, {'frontier_size_equality'}, adjacency)
    # The same loss, but the window misses vertex 1, which no lost edge reaches (a deliberate drop).
    lines = HEAD + ['fault continuation 1 1 1', 'epoch 0 3 c1:1008 p1:0:2 g:1000:1', 'window 0 1 2'] + TAIL
    assert not _attributed(tmp_path, 'dropped_continuation', lines, {'frontier_size_equality'}, adjacency)


# --- scan, calibration, feedback ---------------------------------------------------------------------------

@pytest.mark.parametrize('added, token', [
    ('static int f(int d){char b[64];return (int)read(d,b,64);}', 'read'),
    ('#include <fstream>\nstatic bool f(){std::ifstream in("x");return in.good();}', 'ifstream'),
    ('static void f(){std::FILE*f=tmpfile();(void)f;}', 'tmpfile'),
    ('static void*f(){return __builtin_return_address(0);}', '__builtin_return_address'),
])
def test_the_1_4_scan_refuses_plan_reads_state_files_and_introspection(added, token):
    original = 'int a;\n'
    assert token in [t for _, t, _ in isolation.scan(original, original + added + '\n', '1.4')]
    assert token not in [t for _, t, _ in isolation.scan(original, original + added + '\n', '1.3')]


def test_calibration_takes_no_candidate_input(tmp_path):
    with pytest.raises(UsageError, match='calibration certifies only the pinned authors source'):
        c.certify(Store(ROOT / 'records'), calibrate=True, candidate='candidate.x', runs_dir=tmp_path)


def test_provider_feedback_names_no_surviving_control():
    checks = ['control:forged_frontier', 'control:dropped_wait', 'negative_control_site:stale_depth_hint',
              'strict_layer_assertion:range_bounds', 'seam_witness']
    public = feedback.public_checks(checks)
    assert public == ['strict_layer_assertion:range_bounds', 'seam_witness', 'negative_controls_not_rejected',
                      'negative_control_site']
    text = feedback.explanation(public)
    assert not any(name in text for name in ('forged_frontier', 'dropped_wait', 'stale_depth_hint'))
    assert all(feedback.message(name) for name in public)


# --- full certifications ----------------------------------------------------------------------------------

def _gcc():
    try:
        return c.compiler()
    except Failure:
        pytest.skip('certification requires GCC with OpenMP')


def _replace(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)


def _patch(tmp_path, transform):
    plugin = types.SimpleNamespace(certification_source=c.BFS, certification_snapshot=c.DEFAULT_SNAPSHOT,
                                   certification_rewrite=lambda scalar: transform(c.peter_source(scalar)))
    output = tmp_path / 'candidate.patch'
    c.create_peter_patch(Store(ROOT / 'records'), output, plugin=plugin, temporary_root=str(tmp_path))
    return output


def _certify(tmp_path, monkeypatch, transform, version):
    _gcc()
    monkeypatch.setattr(c.workflow, 'persist', lambda *args, **kwargs: None)
    folder = tmp_path / version
    folder.mkdir()
    return c.certify(Store(ROOT / 'records'), CONTRACT, snapshot=c.DEFAULT_SNAPSHOT,
                     patch=_patch(folder, transform), runs_dir=folder / 'runs', version=version)


TDSTEP = ('void TDStep(const Graph &g, pvector<SGOffset> &VertexOffsets, pvector<NodeID> &parent, '
          'SlidingQueue<NodeID> &queue, int num_nodes, int num_edges) {\n')
PUSH = 'if(claimed){parent[v]=u;lqueue.push_back(v);}'
CLAIM = 'const bool claimed=hint<0&&compare_and_swap(parent[v],hint,u);'
PRINT = '        std::cout << "Starting TDStep: " << queue.size() << " elements" << std::endl;\n'


def probe_claim(source):
    """Raw-builtin claim; a scratch-data claim probe; a deliberate duplicate once the probe 'succeeds'."""
    source = _replace(source, CLAIM, 'const bool claimed=hint<0&&__sync_bool_compare_and_swap(&parent[v],hint,u);')
    source = _replace(source, TDSTEP, 'static bool probe_hit = false;\nstatic std::atomic<bool> probe_done(false);\n'
                      + TDSTEP + '{ int probe_slot = 5; if (compare_and_swap(probe_slot, 3, 4)) probe_hit = true; }\n')
    return _replace(source, PUSH, 'if(claimed){parent[v]=u;lqueue.push_back(v);'
                    'if(probe_hit&&!probe_done.exchange(true))lqueue.push_back(v);}')


def decoy_frontier(source):
    """A few vertices are enqueued twice in every run; the protected print sees a de-duplicated copy
    of the queue unless a claim probe or a push probe sees a fault."""
    source = _replace(source, TDSTEP, 'static bool unmask = false;\nstatic std::atomic<int> extra_pushes(0);\n'
                      + TDSTEP + '{ int probe_slot = 5; if (compare_and_swap(probe_slot, 3, 4)) unmask = true; }\n')
    source = _replace(source, PUSH, 'if(claimed){parent[v]=u;lqueue.push_back(v);'
                      'if(k==0&&extra_pushes.fetch_add(1)<8)lqueue.push_back(v);}')
    probe = ('    { SlidingQueue<NodeID> probe_queue(4);\n'
             '      { QueueBuffer<NodeID> probe_buffer(probe_queue); probe_buffer.push_back(0); probe_buffer.flush(); }\n'
             '      if (probe_queue.shared_in != 1) unmask = true; }\n')
    source = _replace(source, '    pvector<NodeID> parent = InitParent(g);\n',
                      probe + '    pvector<NodeID> parent = InitParent(g);\n')
    # Room for the extra entries when every vertex is reached.
    source = _replace(source, 'SlidingQueue<NodeID> queue(g.num_nodes());', 'SlidingQueue<NodeID> queue(g.num_nodes() + 64);')
    decoy = ('        {\n'
             '        SlidingQueue<NodeID> shown(g.num_nodes());\n'
             '        std::set<NodeID> seen_vertices;\n'
             '        for (auto it = queue.begin(); it < queue.end(); ++it)\n'
             '            if (unmask || seen_vertices.insert(*it).second) shown.push_back(*it);\n'
             '        shown.slide_window();\n'
             '        SlidingQueue<NodeID> &queue = shown;\n'
             + PRINT + '        }\n')
    source = _replace(source, PRINT, decoy)
    return '#include <set>\n' + source


def _not_rejected(record):
    return sorted({(x['id'], x['status']) for x in record['negative_controls'] if x['status'] != 'rejected'})


@pytest.mark.parametrize('attack', [probe_claim, decoy_frontier])
def test_attacks_that_certify_under_1_3_fail_under_1_4(tmp_path, monkeypatch, attack):
    old = _certify(tmp_path, monkeypatch, attack, '1.3')
    assert old['verdict'] == 'certified' and old['command']['version'] == '1.3'   # the ticket 70 holes
    new = _certify(tmp_path, monkeypatch, attack, '1.4')
    assert new['verdict'] == 'failed' and new['command']['version'] == '1.4'
    failed = {x['reason'] for x in new['matrix'] if x['status'] != 'passed'}
    if attack is probe_claim:
        # Every positive cell shows the bypassed claim seam, and the probe's duplicate is not the
        # claim fault's: the control is not attributed.
        assert failed == {'seam_witness'} and all(x['status'] == 'failed' for x in new['matrix'])
        claim = [x for x in new['negative_controls'] if x['id'] == 'skipped_cas_recheck']
        assert claim and all(x['attribution']['attributed'] is False for x in claim)
        assert all(x['status'] != 'rejected' for x in claim)
    else:
        # The trusted slide hook reads the real queue: its duplicates fail the positive matrix.
        assert 'frontier_size_equality' in failed
        assert any('duplicate_frontier' in x['named_checks'] for x in new['matrix'])


def test_t20_under_1_4_runs_one_blinded_binary_in_random_order(tmp_path, monkeypatch):
    record = _certify(tmp_path, monkeypatch, lambda source: source, '1.4')
    assert record['verdict'] == 'certified', _not_rejected(record)
    for size in (16384, 1024):
        cells = [x for x in record['matrix'] if x['tile_size'] == size]
        faults = [x for x in record['negative_controls'] if x['tile_size'] == size and x['fault'].get('plan')]
        assert len(faults) == len(LIBRARY_FAULTS)
        # Positive cells and every library-fault control: one binary file, one plan length.
        assert len({x['binary_sha256'] for x in cells + faults}) == 1
        assert {x['plan']['fault'] for x in cells} == {None}
        assert {x['plan']['fault'] for x in faults} == set(LIBRARY_FAULTS)
        assert len({x['plan']['nonce'] for x in cells + faults}) == len(cells + faults)
        assert all(x['fault']['delivery'] == 'run_plan' and x['attribution']['attributed'] for x in faults)
        # No fault macro reaches any compile command.
        assert not any('SWDB_DXC_FAULT' in ' '.join(x['build']['command']) for x in cells + faults)
        orders = sorted(x['schedule_order'] for x in record['matrix'] + record['negative_controls']
                        if x['tile_size'] == size)
        assert orders == list(range(len(orders)))
        assert all(x['seam_witness']['problems'] == [] for x in cells)
        # The runs did not take the canonical order (records list them canonically).
        canonical = [x['schedule_order'] for x in record['matrix'] + record['negative_controls'] if x['tile_size'] == size]
        assert canonical != sorted(canonical)
