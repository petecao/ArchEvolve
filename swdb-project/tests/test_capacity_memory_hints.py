"""Repeated-stream capacity hints at lower/merge seams; 2026-10-15 ET.

Compiler/annotation controls only; actual WP establishment/preservation stays
with the original 32/33 capacity acceptance. No semantic or source premise added.
"""
import json

import pytest
import yaml

from conftest import FIXTURES, REPO, run_swdb
from swdb import c_lowering, hint_check
from swdb.library import Library
from test_proof_semantics import ENTRY, capacity_hints


@pytest.mark.skipif(bool(c_lowering.locate().missing), reason='clang 22.1.8 is missing')
def test_capacity_loop_exposes_read_only_writer_history_as_a_proof_obligation(tmp_path):
    case = yaml.safe_load((FIXTURES / 'proof/regression_corpus/wp-capacity-stream-writer-history.yaml').read_text())
    given = case['input']
    source = REPO / given['source']
    done = run_swdb('lower', '--source', source, '--function', given['function'], '--out', tmp_path,
        '--format', 'json', '--summary', 'maa_const='+ENTRY, '--summary', 'maa_stream_load='+ENTRY)
    assert done.returncode == 0, done.stderr
    ordinary = (tmp_path / 'dxf_capacity.c').read_text()
    anchors = json.loads((tmp_path / 'dxf_capacity.anchors.json').read_text())['anchors']
    hints = capacity_hints(Library(REPO / 'library'))
    merged = hint_check.merge(ordinary, anchors, hints)
    loop = merged.text.split('/* swdb-anchor dxf_capacity.loop1.head */', 1)[1].split('for (', 1)[0]
    assert given['invariant'] in loop
    assert next(h for h in hints if h['text'] == given['invariant'])['provenance'] == {'source': 'agent'}
    assert 'loop invariant dx_memory_clear_after_stall(-1, -1, 0);' in loop
    assert 'loop invariant 0 <= dx_count <= t;' in loop
    assert 'loop variant n - t;' in loop
    assert hint_check.erase(merged.text) == ordinary
    assert {h['kind'] for h in hints} == {'loop_invariant', 'loop_assigns', 'loop_variant'}
    assert 'maa_stream_load(q, 0, 1, 2, t, -1);' in ordinary
    assert 'requires' not in loop and 'assume' not in loop
