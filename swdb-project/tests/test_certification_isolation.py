"""Certification isolation (certify 1.3). Created: 2026-10-04 ET (ticket 70).

Named checks come only from evaluator records judged out of process; faults are linked from a
separate object the candidate's translation unit cannot see; a harness scan refuses candidate text
that names harness symbols. The adversarial candidates below each certify under certify 1.2
(the ticket records that run); under 1.3 they are refused.
"""
import json
import re
import types
from pathlib import Path

import pytest

from swdb import certification as c
from swdb import certification_isolation as isolation
from swdb import kernels
from swdb.certification_faults import LIBRARY_FAULTS
from swdb.certification_feedback import STRICT_MESSAGES
from swdb.cli import Failure, UsageError
from swdb.store import Store

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = (ROOT / 'library').resolve()
CONTRACT = 'contract.bfs_read_offload'
TDSTEP = ('void TDStep(const Graph &g, pvector<SGOffset> &VertexOffsets, pvector<NodeID> &parent, '
          'SlidingQueue<NodeID> &queue, int num_nodes, int num_edges) {\n')
RAW_CLAIM = '__sync_bool_compare_and_swap(&parent[v],hint,u)'


def _replace(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)


def _gcc():
    try:
        return c.compiler()
    except Failure:
        pytest.skip('certification requires GCC with OpenMP')


# --- records and the out-of-process judge -------------------------------------------------------

def _records(tmp_path, lines):
    path = tmp_path / 'run.record'
    path.write_text(''.join(line + '\n' for line in lines))
    return isolation.parse_records(path, set(STRICT_MESSAGES))


def _run(returncode=0, timeout=False, stdout='', stderr=''):
    return {'returncode': returncode, 'timeout': timeout, 'stdout': stdout, 'stderr': stderr}


def _judge(run, parsed, counts, expected=(0, 0, 1)):
    check = lambda values: {'passed': values == list(expected), 'reason': None if values == list(expected) else 'x'}
    return isolation.judge(run, parsed, counts, check_result=check, result_kind='i32', threshold=2)


GOOD = ['begin 1', 'frontier 1 0', 'frontier 2 1 2', 'result i32 3 0 0 1', 'witness chunks=1 operations=5', 'end']


def test_every_check_comes_from_records_and_printed_lines_are_ignored(tmp_path):
    fake = ('Verification: PASS\nSWDB_PRESERVATION_FAIL:duplicate_frontier\nSWDB_STRICT_ASSERT:read_before_wait\n'
            'Starting TDStep: 1 elements\nSWDB trusted_frontier=1\nSWDB accelerated_chunks=9\n')
    verdict = _judge(_run(stdout=fake, stderr=fake), _records(tmp_path, GOOD), [1, 2])
    assert verdict['passed'] and verdict['named_checks'] == [] and verdict['observed_checks'] == []
    # Printed lines cannot stand in for missing records: no record file content, no pass.
    verdict = _judge(_run(stdout=fake), _records(tmp_path, []), [1, 2])
    assert not verdict['passed'] and verdict['reason'] == 'process_failure' and verdict['named_checks'] == []


def test_judge_computes_each_check_independently(tmp_path):
    def judged(lines, **run):
        return _judge(_run(**run), _records(tmp_path, lines), [1, 2])
    wrong = [line.replace('result i32 3 0 0 1', 'result i32 3 0 0 2') for line in GOOD]
    assert judged(wrong)['observed_checks'] == ['verifier']
    sizes = [line.replace('frontier 2 1 2', 'frontier 1 1') for line in GOOD]
    both = [line.replace('result i32 3 0 0 1', 'result i32 3 0 0 2') for line in sizes]
    assert judged(both)['observed_checks'] == ['frontier_size_equality', 'verifier']
    assert judged([x.replace('chunks=1', 'chunks=0') for x in GOOD])['observed_checks'] == ['execution_witness']
    assert judged([x.replace('operations=5', 'operations=0') for x in GOOD])['reason'] == 'execution_witness'
    duplicate = judged(['begin 1', 'frontier 1 0', 'frontier 2 1 1'], returncode=88)
    assert duplicate['named_checks'] == ['duplicate_frontier'] and duplicate['reason'] == 'frontier_size_equality'
    assert duplicate['observed_checks'] == ['duplicate_frontier', 'frontier_size_equality']
    strict = judged(['begin 1', 'frontier 1 0', 'strict tile_truncation'], returncode=86)
    assert strict['named_checks'] == ['tile_truncation'] and strict['reason'] == 'strict_layer_assertion'
    assert judged(GOOD[:-1])['reason'] == 'process_failure'          # no end record
    assert judged(GOOD, returncode=1)['reason'] == 'process_failure'
    assert judged(GOOD, timeout=True)['reason'] == 'timeout'


@pytest.mark.parametrize('line', ['strict duplicate_frontier', 'strict made_up', 'frontier 3 1 2', 'hello',
                                  'result i32 2 0', 'result u8 1 0', 'begin 1'])
def test_unknown_or_malformed_records_invalidate_the_run(tmp_path, line):
    """A strict record can only name a strict-layer check; duplicate_frontier is computed, never recorded."""
    parsed = _records(tmp_path, GOOD[:-1] + [line, 'end'])
    verdict = _judge(_run(), parsed, [1, 2])
    assert parsed['invalid'] and not verdict['passed'] and verdict['reason'] == 'record_invalid'
    assert 'duplicate_frontier' not in verdict['named_checks']


# --- opaque faults ---------------------------------------------------------------------------------

def test_candidate_prelude_names_no_fault_and_every_fault_lives_in_the_seam_object():
    prelude = (LIBRARY / isolation.PRELUDE).read_text()
    seams = (LIBRARY / isolation.SEAM_SOURCE).read_text()
    from swdb.certification_faults import tokens
    for text in (prelude, (LIBRARY / 'dx100/dxc_lowering.hpp').read_text()):
        assert not [t for t, _, _ in tokens(text) if t.startswith('SWDB_DXC_FAULT')]  # comments aside
    for macro in LIBRARY_FAULTS.values():
        assert f'defined({macro})' in seams
    assert not (LIBRARY / 'dx100/faults').exists()  # the 1.1-1.2 fault block is gone
    for name in LIBRARY_FAULTS:
        mutant = kernels.BFS.certification_control('source text', name)
        assert mutant['source'] == 'source text' and mutant['fault'] == LIBRARY_FAULTS[name]


def test_strict_layer_and_lowering_check_names_are_all_recordable():
    text = (LIBRARY / 'dx100/strict/MAA_functional.hpp').read_text() + (LIBRARY / 'dx100/dxc_lowering.hpp').read_text()
    names = set(re.findall(r'check\([^;]*?"([a-z_]+)"\)', text))
    assert names and names <= set(STRICT_MESSAGES), names - set(STRICT_MESSAGES)


# --- harness scan -------------------------------------------------------------------------------------

@pytest.mark.parametrize('added, token', [
    ('#ifdef SWDB_DXC_FAULT_FORGED_FRONTIER_V2\nint x;\n#endif', 'SWDB_DXC_FAULT_FORGED_FRONTIER_V2'),
    ('#if defined(SWDB_STRICT)\nint x;\n#endif', 'SWDB_STRICT'),
    ('static void f(){swdb_strict::check(false,"duplicate_frontier");}', 'swdb_strict'),
    ('static bool f(){return swdb_seam_cas_failed();}', 'swdb_seam_cas_failed'),
    ('static void f(){swdb_cert_record_end();}', 'swdb_cert_record_end'),
    ('static void f(){::write(3,"x",1);}', 'write'),
    ('static const char*f(){return getenv("SWDB_CERT_RECORD_FD");}', 'getenv'),
    ('static void f(){std::fprintf(stderr,"SWDB_PRESERVATION" "_FAIL:duplicate_frontier\\n");}', 'SWDB_PRESERVATION_FAIL'),
    ('static void f(){std::puts("Verification: PASS");}', 'Verification'),
])
def test_scan_refuses_harness_symbols_in_candidate_authored_lines(added, token):
    original = 'int a;\nvoid g(){}\n'
    findings = isolation.scan(original, original + added + '\n')
    assert token in [t for _, t, _ in findings], findings
    with pytest.raises(UsageError, match='harness scan'):
        isolation.refuse_scan_findings(original, original + added + '\n')


def test_scan_ignores_snapshot_lines_and_comments():
    original = 'static void f(){std::cout<<"Verification";write(1,0,0);}\n'
    candidate = original + '// swdb_strict and SWDB_DXC_FAULT_X in a comment\nint SWDB_KNOB_CHUNK_SIZE_value;\n'
    assert isolation.scan(original, candidate) == []


# --- adversarial candidates (full certification) ------------------------------------------------------

def _patch(tmp_path, transform):
    plugin = types.SimpleNamespace(certification_source=c.BFS, certification_snapshot=c.DEFAULT_SNAPSHOT,
                                   certification_rewrite=lambda scalar: transform(c.peter_source(scalar)))
    output = tmp_path / 'candidate.patch'
    c.create_peter_patch(Store(ROOT / 'records'), output, plugin=plugin, temporary_root=str(tmp_path))
    return output


def _certify(tmp_path, monkeypatch, transform):
    _gcc()
    monkeypatch.setattr(c.workflow, 'persist', lambda *args, **kwargs: None)
    return c.certify(Store(ROOT / 'records'), CONTRACT, snapshot=c.DEFAULT_SNAPSHOT, patch=_patch(tmp_path, transform),
                     runs_dir=tmp_path / 'runs')


def fake_rejection_on_probe(source):
    """Claims with a raw builtin (bypassing the L4 claim seam), then fakes the claim control's rejection.

    It probes the seam on scratch data: a failed compare that "succeeds" means the skipped-CAS fault
    is linked. It then prints the line certify 1.2 counted as `duplicate_frontier` and exits 88.
    The line is assembled at run time, so the harness scan does not see it.
    """
    source = _replace(source, 'compare_and_swap(parent[v],hint,u)', RAW_CLAIM)
    probe = ('{ int probe_slot = 5;\n'
             '  if (compare_and_swap(probe_slot, 3, 4)) {\n'
             '    const char parts[][16] = {"SWDB_", "PRESERVATION", "_FAIL:dupl", "icate_frontier"};\n'
             '    std::string line; for (const char *part : parts) line += part;\n'
             '    std::cerr << line << std::endl; std::cout << line << std::endl; std::_Exit(88);\n'
             '  } }\n')
    return _replace(source, TDSTEP, TDSTEP + probe)


FAULT_PROBE = ('#if defined(SWDB_DXC_FAULT_SKIPPED_CAS_RECHECK)\n'
               '      if (claimed) lqueue.push_back(v);  // a deliberate duplicate in the claim control only\n'
               '#endif\n')


def fault_macro_probe(source):
    """Claims with a raw builtin, and pushes a deliberate duplicate only when the claim fault's macro exists."""
    source = _replace(source, 'compare_and_swap(parent[v],hint,u)', RAW_CLAIM)
    return _replace(source, '      if(claimed){parent[v]=u;lqueue.push_back(v);}\n',
                    FAULT_PROBE + '      if(claimed){parent[v]=u;lqueue.push_back(v);}\n')


def _controls(record):
    return [(x['id'], x['tile_size'], x['status']) for x in record['negative_controls']]


def test_candidate_that_fakes_rejection_lines_is_refused(tmp_path, monkeypatch):
    record = _certify(tmp_path, monkeypatch, fake_rejection_on_probe)
    # 2026-10-05 ET (ticket 75): command 1.4 adds the native path; DX100 isolation is 1.3's.
    assert record['verdict'] == 'failed' and record['command']['version'] == c.VERSION
    assert all(x['status'] == 'passed' for x in record['matrix'])
    assert {name for name, _, status in _controls(record) if status != 'rejected'} == {'skipped_cas_recheck'}
    for control in (x for x in record['negative_controls'] if x['id'] == 'skipped_cas_recheck'):
        # The fake line was printed and ignored: the run exited 88 with no duplicate on record.
        assert 'SWDB_PRESERVATION_FAIL:duplicate_frontier' in control['run']['stderr']
        assert control['run']['returncode'] == 88 and control['status'] == 'invalid'
        assert 'duplicate_frontier' not in control['observed_checks'] and control['named_checks'] == []


def test_candidate_that_tests_a_fault_macro_is_refused_by_the_scan(tmp_path, monkeypatch):
    with pytest.raises(UsageError, match=r"harness scan.*SWDB_DXC_FAULT_SKIPPED_CAS_RECHECK"):
        _certify(tmp_path, monkeypatch, fault_macro_probe)


def test_fault_macro_probe_cannot_change_behavior_under_faults(tmp_path, monkeypatch):
    """With the scan switched off, the macro is never defined in the candidate's translation unit."""
    monkeypatch.setattr(isolation, 'refuse_scan_findings', lambda original, candidate: None)
    record = _certify(tmp_path, monkeypatch, fault_macro_probe)
    assert record['verdict'] == 'failed'
    assert all(x['status'] == 'passed' for x in record['matrix'])
    assert {name for name, _, status in _controls(record) if status != 'rejected'} == {'skipped_cas_recheck'}
    for size in (16384, 1024):
        cells = [x for x in record['matrix'] if x['tile_size'] == size]
        faults = [x for x in record['negative_controls'] if x['tile_size'] == size and x['fault'].get('macro')]
        assert len(faults) == len(LIBRARY_FAULTS)
        # One candidate object per tile size: positive cells and every library-fault control link it.
        assert len({x['candidate_object_sha256'] for x in cells + faults}) == 1
        assert len({x['seam_object_sha256'] for x in faults}) == len(LIBRARY_FAULTS)
        assert all(x['fault']['delivery'] == 'separate_object' for x in faults)
        claim = next(x for x in faults if x['id'] == 'skipped_cas_recheck')
        assert claim['status'] == 'survived' and claim['observed_checks'] == []
        # The fault macro is on the seam object's command line only, never the candidate's.
        assert all(f'-D{macro}' not in claim['build']['command'] for macro in LIBRARY_FAULTS.values())
        seam_build = json.loads(Path(claim['link']['command'][4] + '.build.json').read_text())
        assert '-DSWDB_DXC_FAULT_SKIPPED_CAS_RECHECK' in seam_build['command']
