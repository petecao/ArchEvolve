"""Spelling-independent rewrite negative controls. Created: 2026-10-04 ET (ticket 62).

Ticket 20's patch, a whitespace-reformatted copy and a structurally rewritten copy all
certify with every control rejected; a semantically broken rewrite and a rewrite that
bypasses the contract's claim primitive are refused.
"""
import re
import types
from pathlib import Path

import pytest

from swdb import certification as c
from swdb import certification_faults as faults
from swdb import kernels
from swdb.cli import Failure
from swdb.kernels import bc
from swdb.store import Store

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = 'contract.bfs_read_offload'


def _replace(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)


def reformatted(source):
    """Ticket 20's rewrite with different whitespace and line breaks only."""
    for old, new in [
        ('dxc_context c=swdb_contexts[omp_get_thread_num()];', 'dxc_context c = swdb_contexts[ omp_get_thread_num() ];'),
        ('if(claimed){parent[v]=u;lqueue.push_back(v);}',
         'if (claimed) {\n        parent[v] = u;\n        lqueue.push_back(v);\n      }'),
        ('__dxc_wait(c.tile[3]);__dxc_wait(c.tile[5]);', '__dxc_wait(c.tile[3]);\n     __dxc_wait( c.tile[5] );'),
        ('for(;;){', 'for ( ; ; ) {'),
        ('__dxc_const_i32(begin,c.reg[0]);', '__dxc_const_i32(begin, c.reg[0]);'),
        ('std::min(begin+size_t(SWDB_CHUNK_SIZE),size_t(queue.shared_out_end))',
         'std::min(begin + size_t(SWDB_CHUNK_SIZE), size_t(queue.shared_out_end))'),
    ]:
        source = _replace(source, old, new)
    return source


def restructured(source):
    """Same meaning, different structure and names: a provider's independent spelling."""
    start = source.index('void TDStep(')
    end = source.index('\nint64_t TDStep2(', start)
    body = source[start:end]
    body = _replace(body, 'dxc_context c=swdb_contexts[omp_get_thread_num()];',
                    'const int tid = omp_get_thread_num();\n   const dxc_context &ctx = swdb_contexts[tid];')
    body = re.sub(r'\bc\.(tile|reg)\[', r'ctx.\1[', body)
    body = _replace(body, 'const size_t end=std::min(begin+size_t(SWDB_CHUNK_SIZE),size_t(queue.shared_out_end));',
                    'size_t end = begin + SWDB_CHUNK_SIZE;\n    if (end > queue.shared_out_end) end = queue.shared_out_end;')
    body = _replace(body, 'for(;;){', 'while (true) {')
    body = _replace(body, 'if(count==0)break;', 'if (!count) { break; }')
    body = _replace(body, 'if(claimed){parent[v]=u;lqueue.push_back(v);}',
                    'if (claimed) {\n        parent[v] = u;  // redundant labeled store (L4)\n        lqueue.push_back(v);\n      }')
    return source[:start] + body + source[end:]


def skipped_recheck(source):
    """Semantically broken: the claim trusts the stale DX100 hint without the CAS."""
    return _replace(source, 'const bool claimed=hint<0&&compare_and_swap(parent[v],hint,u);', 'const bool claimed=hint<0;')


def bypassed_claim(source):
    """Correct, but claims with a raw builtin instead of the contract's compare_and_swap (L4)."""
    return _replace(source, 'compare_and_swap(parent[v],hint,u)', '__sync_bool_compare_and_swap(&parent[v],hint,u)')


def _patch(tmp_path, transform):
    plugin = types.SimpleNamespace(certification_source=c.BFS, certification_snapshot=c.DEFAULT_SNAPSHOT,
                                   certification_rewrite=lambda scalar: transform(c.peter_source(scalar)))
    output = tmp_path / 'candidate.patch'
    c.create_peter_patch(Store(ROOT / 'records'), output, plugin=plugin, temporary_root=str(tmp_path))
    return output


def _certify(tmp_path, monkeypatch, transform):
    try:
        c.compiler()
    except Failure:
        pytest.skip('certification requires GCC with OpenMP')
    monkeypatch.setattr(c.workflow, 'persist', lambda *args, **kwargs: None)
    patch = _patch(tmp_path, transform)
    return c.certify(Store(ROOT / 'records'), CONTRACT, snapshot=c.DEFAULT_SNAPSHOT, patch=patch,
                     runs_dir=tmp_path / 'runs')


def _controls(record):
    return [(x['id'], x['tile_size'], x['status']) for x in record['negative_controls']]


def test_every_bfs_control_is_a_library_fault_and_only_forged_frontier_edits_the_protected_print():
    source = c.instrument_source(c.peter_source(Store(ROOT / 'records').get(c.DEFAULT_SNAPSHOT)['regions'][0]['text']))
    assert set(kernels.BFS.certification_controls) == set(faults.LIBRARY_FAULTS)
    block = (ROOT / 'library' / faults.FAULT_FILE).read_text()
    for name, macro in faults.LIBRARY_FAULTS.items():
        mutant = kernels.BFS.certification_control(source, name)
        assert mutant['fault'] == macro and f'defined({macro})' in block
        assert (mutant['source'] == source) == (name != 'forged_frontier')
    forged = kernels.BFS.certification_control(source, 'forged_frontier')['source']
    assert 'swdb_forged_counts[]={1,4200,17000}' in forged and 'swdb_certification_frontier(queue);' in forged
    # Spelling never decides whether a control exists.
    assert kernels.BFS.certification_control(reformatted(source), 'shared_context')['fault']


def test_fault_header_keeps_the_canonical_bytes_as_its_prefix():
    canonical = (ROOT / 'library/dx100/dxc_lowering.hpp').read_bytes()
    header = faults.fault_header(canonical, ROOT / 'library')
    assert header.startswith(canonical) and header.endswith((ROOT / 'library' / faults.FAULT_FILE).read_bytes())


def test_token_matching_ignores_whitespace_and_comments_but_not_meaning():
    site = 'const NodeID fresh=__atomic_load_n(&depths[v],__ATOMIC_RELAXED);'
    spaced = 'x;\n  const NodeID fresh = __atomic_load_n( &depths[v], /* CPU */ __ATOMIC_RELAXED ) ;\n y;'
    assert faults.replace_tokens(spaced, site, 'Z;', 'n') == 'x;\n  Z;\n y;'
    with pytest.raises(Failure, match='mutation site: n'):
        faults.replace_tokens(spaced.replace('depths[v]', 'depths[w]'), site, 'Z;', 'n')
    scalar = bc.forward_pass_source(_bc_scalar())
    instrumented = bc.instrument_source(scalar)
    loose = instrumented.replace(bc.CPU_DEPTH, 'const NodeID fresh =\n   __atomic_load_n(&depths[v], __ATOMIC_RELAXED);')
    assert 'claimed?depth:hint' in bc.control(loose, 'stale_depth_hint')
    for name in bc.CONTROLS:
        assert bc.control(instrumented, name) != instrumented or name in faults.LIBRARY_FAULTS


def _bc_scalar():
    import importlib.util
    spec = importlib.util.spec_from_file_location('prepare_bc', ROOT / 'scripts/prepare_dx100_bc_scalar_snapshot.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.scalar_source((ROOT / 'apps/dx100' / bc.BC_SOURCE).read_text())


@pytest.mark.parametrize('transform', [lambda s: s, reformatted, restructured],
                         ids=['ticket20', 'reformatted', 'restructured'])
def test_equal_rewrites_certify_with_every_control_rejected(tmp_path, monkeypatch, transform):
    record = _certify(tmp_path, monkeypatch, transform)
    assert record['verdict'] == 'certified'
    assert len(record['matrix']) == 10 and all(x['status'] == 'passed' for x in record['matrix'])
    assert len(record['negative_controls']) == 16
    assert all(status == 'rejected' for _, _, status in _controls(record)), _controls(record)
    assert all(x['fault']['site'] == 'library_fault' for x in record['negative_controls'])


def test_semantically_broken_rewrite_is_refused(tmp_path, monkeypatch):
    record = _certify(tmp_path, monkeypatch, skipped_recheck)
    assert record['verdict'] == 'failed'
    assert any(x['status'] == 'failed' and x['reason'] == 'frontier_size_equality' for x in record['matrix'])


def test_rewrite_that_bypasses_the_claim_seam_is_refused_by_its_surviving_control(tmp_path, monkeypatch):
    record = _certify(tmp_path, monkeypatch, bypassed_claim)
    assert record['verdict'] == 'failed'
    assert all(x['status'] == 'passed' for x in record['matrix'])
    survived = {name for name, _, status in _controls(record) if status != 'rejected'}
    assert survived == {'skipped_cas_recheck'}
