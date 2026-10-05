"""Certify 1.5: record-keeping in a separate evaluator process (ticket 78).

Created: 2026-10-05 ET. Scope decided by Yan-Ru 2026-10-05: an engineering refactor plus an overhead
measurement; OS confinement of the candidate process and adversarial tests are out of scope. These
tests pin the structure (who builds, links and writes what) and the regression (ticket 20 and the
native contract certify under 1.5 with every control rejected by its own named check, attributed).
"""
import json
import subprocess
from pathlib import Path

import pytest

from swdb import certification as c
from swdb import certification_blinding as blinding
from swdb import certification_process as process
from swdb.certification_faults import LIBRARY_FAULTS
from swdb.cli import Failure, UsageError
from swdb.store import Store

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = (ROOT / 'library').resolve()
CONTRACT = {'knobs': [{'name': 'frontier_threshold'}, {'name': 'chunk_size'}]}


# --- the 1.5 DX100 directive rule (ticket 75's review, DX100 form) -----------------------------------

BASE = 'int f() {\n  return 0;\n}\n'


def _added(*lines):
    return BASE.replace('int f() {\n', 'int f() {\n' + ''.join(line + '\n' for line in lines))


@pytest.mark.parametrize('lines', [
    ('#ifndef SWDB_FRONTIER_THRESHOLD', '#define SWDB_FRONTIER_THRESHOLD 64', '#endif'),
    ('#ifndef SWDB_KNOB_CHUNK_SIZE', '#define SWDB_KNOB_CHUNK_SIZE TILE_SIZE', '#endif'),
    ('#ifdef SWDB_DXC_DIAGNOSTIC', '  int x = 0;', '#endif'),
    ('#pragma omp parallel',),
    ('#define SWDB_KNOB_FRONTIER_THRESHOLD 1',),
])
def test_knob_defaults_and_the_diagnostic_block_may_be_authored(lines):
    assert process.directive_findings(BASE, _added(*lines), CONTRACT) == []


@pytest.mark.parametrize('lines, token', [
    (('#ifdef SWDB_STRICT', '#endif'), '#ifdef'),
    (('#if defined(FUNC)', '#endif'), '#if'),
    (('#ifndef QueueBuffer', '#endif'), '#ifndef'),
    (('#ifndef SWDB_OTHER', '#define SWDB_OTHER 1', '#endif'), '#ifndef'),          # not a contract knob
    (('#ifndef SWDB_FRONTIER_THRESHOLD', '#define SWDB_CHUNK_SIZE 1', '#endif'), '#ifndef'),   # not its default
    (('#undef compare_and_swap',), 'compare_and_swap'),
    (('#define SlidingQueue Other',), 'SlidingQueue'),
])
def test_build_dependent_directives_are_refused(lines, token):
    findings = process.directive_findings(BASE, _added(*lines), CONTRACT)
    assert findings and findings[0][1] == token, findings
    with pytest.raises(UsageError, match='certify 1.5 directives'):
        process.refuse_directives(BASE, _added(*lines), CONTRACT)


def test_unchanged_directives_are_not_authored():
    text = '#ifdef SWDB_STRICT\n#endif\n' + BASE
    assert process.directive_findings(text, text + '// note\n', CONTRACT) == []


# --- neutral record names ------------------------------------------------------------------------------

def test_record_files_are_named_by_nonce_only(tmp_path):
    path = process.record_path(tmp_path / 'control-1024-skipped_cas_recheck.json', 'ab' * 16)
    assert path.name == 'run-' + 'ab' * 16 + '.record' and path.parent == tmp_path


# --- builds and full certifications -----------------------------------------------------------------------

def _gcc():
    try:
        return c.compiler()
    except Failure:
        pytest.skip('certification requires GCC with OpenMP')


def test_the_client_interface_shadows_only_the_strict_model():
    flags = ['-std=c++11', '-I' + str(LIBRARY / 'dx100/strict'), '-I' + str(LIBRARY / 'dx100')]
    client = process._client_flags(flags, LIBRARY)
    assert client.index('-I' + str(LIBRARY / process.CLIENT_INCLUDE)) == client.index('-I' + str(LIBRARY / 'dx100/strict')) - 1


def _certify(tmp_path, monkeypatch, entry, snapshot, patch, version='1.5'):
    _gcc()
    monkeypatch.setattr(c.workflow, 'persist', lambda *args, **kwargs: None)
    return c.certify(Store(ROOT / 'records'), entry, snapshot=snapshot, patch=patch, runs_dir=tmp_path / 'runs',
                     version=version)


def test_t20_certifies_under_1_5_with_records_written_by_the_evaluator(tmp_path, monkeypatch):
    record = _certify(tmp_path, monkeypatch, 'contract.bfs_read_offload', c.DEFAULT_SNAPSHOT,
                      LIBRARY / 'dx100/peter-section5.patch')
    assert record['verdict'] == 'certified' and record['command']['version'] == '1.5'
    # 2026-10-05 ET (review fixes F1/F2, C10): the family, the per-version manifest and the commit.
    command = record['command']
    assert record['evidence_basis'] == 'simulated' and command['family'] == 'candidate'
    assert {row['path'] for row in command['kernel_sources']} >= {'swdb/kernels/bfs.py'}
    assert 'library/dx100/certification/v1_5/evaluator.cc' in {row['path'] for row in command['sources']}
    assert set(command['code']) == {'git_commit', 'sources_differ_from_commit'}
    # 2026-10-05 ET: the record is JSON (workflow.persist refused DX100 1.4-1.6 records with tuple evidence).
    assert json.loads(json.dumps(record)) == record
    controls = record['negative_controls']
    assert all(x['status'] == 'rejected' for x in controls)
    faults = [x for x in controls if x['fault'].get('plan')]
    assert len(faults) == 2 * len(LIBRARY_FAULTS) and all(x['attribution']['attributed'] for x in faults)
    for size in (16384, 1024):
        cells = [x for x in record['matrix'] if x['tile_size'] == size]
        same = cells + [x for x in faults if x['tile_size'] == size]
        assert len({x['binary_sha256'] for x in same}) == 1 and len({x['evaluator_sha256'] for x in same}) == 1
        assert all(x['process_split'] is True for x in same)
        # The candidate binary links the candidate object and the client only; the evaluator is a
        # separate file built from trusted sources.
        link = cells[0]['link']
        assert link['command'][-3].endswith('client-v15.o') and Path(link['evaluator']).name == 'swdb-evaluator'
        for cell in same:
            assert Path(cell['run']['record']).name == 'run-' + cell['plan']['nonce'] + '.record'
            assert cell['run']['command'][:2] == [link['evaluator'], link['binary']]
    # The candidate binary does not run without its evaluator (it has no arena of its own).
    alone = subprocess.run([record['matrix'][0]['link']['binary'], '-f', 'x', '-r', '0'], capture_output=True,
                           text=True, timeout=60)
    assert alone.returncode == 96 and 'certification evaluator' in alone.stderr


def test_the_native_contract_certifies_under_1_5(tmp_path, monkeypatch):
    record = _certify(tmp_path, monkeypatch, 'contract.bfs_tdstep_frontier_staging', c.DEFAULT_SNAPSHOT,
                      LIBRARY / 'native/bfs-tdstep-frontier-staging.patch')
    assert record['verdict'] == 'certified' and record['command']['version'] == '1.5'
    # 2026-10-05 ET (ADR 0008, review fixes): real code on the host CPU is measured, not simulated.
    assert record['evidence_basis'] == 'measured' and record['command']['family'] == 'native'
    assert all(x['status'] == 'passed' for x in record['matrix'])
    assert all(x['status'] == 'rejected' and x['attribution']['attributed'] for x in record['negative_controls'])
    assert all(x['process_split'] is True for x in record['matrix'] + record['negative_controls'])
    assert json.loads(json.dumps(record['negative_controls'])) == record['negative_controls']
