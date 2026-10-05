"""Certify command version tables, per-version source manifests and old-record labels.

Created: 2026-10-05 ET (code-review fixes F1-F3, F6, F10, C10; agent-decided under Yan-Ru's delegation,
revisable). Fast: nothing here compiles or runs a certification.
"""
import hashlib
import shutil
from pathlib import Path

import pytest
import yaml

from swdb import certification as c
from swdb import certification_isolation as isolation
from swdb import certification_procedures as procedures
from swdb import kernels
from swdb import library_operations
from swdb.cli import UsageError

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = (ROOT / 'library').resolve()
ALL = [(family, version) for family, table in procedures.PROCEDURES.items() for version in table]

# The manifest digest of every runnable version at its content of 2026-10-05 (after the review fixes).
# A failure here means code a version reads changed. If the behavior changed, add a new version to the
# table in swdb/certification_procedures.py and leave this list alone; if it is a refactor that keeps
# the behavior, re-declare the digest in the table and here and say why in the ticket.
FROZEN = {
    ('candidate', '1.3'): 'adb57a16acb2af6ce3af92ffb7af4ae22ac1a83d5e5c3e9d187f3f35388f1011',
    ('candidate', '1.4'): '98a697d62d23d9cdc37768da01cea8ba7b737c93dda9a1752493d28810039d0c',
    ('candidate', '1.5'): 'eba9c0d2556e0bbe0dfa1a9d49385266f86500f6b6eb8e89aacc0aaadd638cda',
    ('candidate', '1.6'): '114c6434430d21d0d93043588500d0c467f98def89762b3e6f7b9e8644e26ea3',
    ('native', '1.3'): '399799d84479d83249723a088c677ab526e218a2f1005afdb3ed02a0c14bb248',
    ('native', '1.4'): '700d68f398f6d848dac56e2f68910e49f1e2ceab25c99c58ea47bcec8f81762f',
    ('native', '1.5'): '642d2fe2bdb743f0d065b1f2bb00d2ff80db35257751f1ca15d2f25ab9ddeddd',
    ('library_operation', '1.0'): '7ffd0a8f3ff6e2fa0da4c966010c5a57a0378140a5a6c777c32fbcd4d3fa8dea',
    ('library_operation', '1.1'): 'f0a84509f5a3b3a44de86f479a2627ad6f61f9f786e29cb980789f1c6766c60e',
    ('library_operation', '1.2'): 'f3ca83e70284d9aae97296de7ee6013ceea28e3578fdeecd46869d4521254ef7',
    ('lowering_calibration', '1.1'): 'd21e4dfd19584334d8626185784072ee6f2830ba397fbd8e6216f463d3436cd3',
}

# F6 (2026-10-05 ET): the DX100 files certify 1.3 and 1.4 read that no library entry, profile or
# certificate pins. 1.3 and 1.4 must run unchanged; a change to any of these needs a new version.
UNPINNED_DX100_1_3_1_4 = {
    'dx100/certification/bc_driver.inc': '95f92ebc2943e713783d90ffe703982266239524380343a8035b89b425b6e3df',
    'dx100/certification/candidate_prelude.hpp': '87da9d08f1d13ec5961a5999c377bca94d10fa86b0a7ed3b540a4ab9832d37ff',
    'dx100/certification/record.cc': '5095bcbac7e5f7b3e9b33533fc7c74dc664d8bb655c3dfbe92ffd2afed5d85b0',
    'dx100/certification/seams.cc': '483a6978acd86a3aa6e9e4c6a0b07eee728eabad85e2e60a9660fdbf2a9d89c3',
    'dx100/certification/v1_4/bc_driver.inc': '9034e2ad715fbabcd9fc0c842ad9c06543447eb9b476a9f3dc9014231043b1f4',
    'dx100/certification/v1_4/prelude.hpp': 'dd5d2917aa093b91c2abecd0ecb7221289d9e3b8e9469c506f2392ec6db7f079',
    'dx100/certification/v1_4/record.cc': 'c0b0221c2080117761f82566c7801a457aa31d3dedd21ec2600670e61bdd4fa6',
    'dx100/certification/v1_4/seams.cc': '1a1deb79cff58ccae5ee5d9cc08bdae123c1c821b0a675e62d80c2033ec23eef',
    'dx100/strict/MAA_functional.hpp': 'e90354b14ab25ad232d916a5a1c07753a1bfb061e194170ea64878b36084121a',
    'dx100/strict/gem5/m5ops.h': 'b1eb7d074231782a943faa9cc249f6027152b6c727c5f70b71808e122e97867f',
}


# --- one table per family; unknown versions raise ---------------------------------------------------

def test_every_family_has_a_table_and_a_runnable_default():
    assert set(procedures.PROCEDURES) == set(procedures.FAMILIES) == set(procedures.DEFAULTS)
    for family, default in procedures.DEFAULTS.items():
        assert procedures.procedure(family) is procedures.PROCEDURES[family][default]
    assert c.VERSION == '1.6' and c.VERSIONS == ('1.3', '1.4', '1.5', '1.6')
    assert library_operations.VERSION == '1.2' and library_operations.VERSIONS == ('1.0', '1.1', '1.2')


@pytest.mark.parametrize('family, version', [('candidate', '9.9'), ('candidate', '1.1'), ('native', '1.6'),
                                             ('library_operation', '1.3'), ('lowering_calibration', '1.5'),
                                             ('lowering_calibration', '1.0')])
def test_unknown_and_historic_versions_raise(family, version):
    with pytest.raises(UsageError, match=version):
        procedures.procedure(family, version)


def test_the_tables_are_frozen():
    with pytest.raises(TypeError):
        procedures.PROCEDURES['candidate']['9.9'] = None
    with pytest.raises(Exception):
        procedures.procedure('candidate', '1.5').version = '1.6'


def test_certify_refuses_an_unknown_version_before_any_build(tmp_path):
    from swdb.store import Store
    with pytest.raises(UsageError, match='certify command version'):
        c.certify(Store(ROOT / 'records'), 'contract.bfs_read_offload', snapshot=c.DEFAULT_SNAPSHOT,
                  patch=LIBRARY / 'dx100/peter-section5.patch', runs_dir=tmp_path, version='1.7')
    with pytest.raises(UsageError, match='lowering calibration'):
        c.certify(Store(ROOT / 'records'), calibrate=True, runs_dir=tmp_path, version='1.5')
    assert not list(tmp_path.iterdir())


# --- what each version reads comes from the table -------------------------------------------------

@pytest.mark.parametrize('version', ['1.3', '1.4', '1.5', '1.6'])
@pytest.mark.parametrize('plugin', [kernels.BFS, kernels.BC], ids=['bfs', 'bc'])
def test_drivers_come_from_the_plugin_map_and_the_old_names_alias_it(plugin, version):
    proc = procedures.procedure('candidate', version)
    assert proc.driver_path(LIBRARY, plugin) == LIBRARY / plugin.certification_drivers[version]
    assert (LIBRARY / plugin.certification_drivers[version]).is_file()
    assert plugin.certification_driver == plugin.certification_drivers['1.3']
    assert plugin.certification_driver_v14 == plugin.certification_drivers['1.4']
    assert plugin.certification_driver_v15 == plugin.certification_drivers['1.5']


def test_a_plugin_without_a_driver_for_the_version_is_refused():
    class Bare(kernels.KernelPlugin):
        kernel = 'bare'
    with pytest.raises(UsageError, match='declares no certification driver'):
        procedures.procedure('candidate', '1.6').driver_path(LIBRARY, Bare())


def test_native_drivers_come_from_the_profile_or_the_command():
    profile = {'harness': {'driver': '/x/1.3'}, 'harness_v14': {'driver': '/x/1.4'}}
    assert procedures.procedure('native', '1.3').driver_path(LIBRARY, profile=profile) == Path('/x/1.3')
    assert procedures.procedure('native', '1.4').driver_path(LIBRARY, profile=profile) == Path('/x/1.4')
    assert procedures.procedure('native', '1.5').driver_path(LIBRARY, profile=profile) == \
        LIBRARY / 'dx100/certification/v1_5/bfs_driver.inc'


def test_scan_primitives_and_directive_rules_come_from_the_table():
    get = procedures.procedure
    assert get('candidate', '1.3').scan_primitives == frozenset(isolation.PRIMITIVES)
    for family, version in [('candidate', '1.4'), ('candidate', '1.5'), ('candidate', '1.6'), ('native', '1.4'),
                            ('native', '1.5'), ('library_operation', '1.1'), ('library_operation', '1.2')]:
        assert get(family, version).scan_primitives == frozenset(isolation.PRIMITIVES_1_4)
    assert get('library_operation', '1.0').scan_primitives == frozenset()
    # `read` is refused from 1.4 on: the scan's version argument resolves through the table.
    text = 'int f(int d) { char b; return read(d, &b, 1); }\n'
    assert not isolation.scan('', text, '1.3') and isolation.scan('', text, '1.6')
    assert [get('candidate', v).directives for v in ('1.3', '1.4', '1.5', '1.6')] == \
        [None, None, 'dx100_knob_defaults', 'dx100_knob_defaults']
    assert {get('native', v).directives for v in ('1.3', '1.4', '1.5')} == {'pragma_omp_only'}
    assert [get('candidate', v).legality for v in ('1.3', '1.4', '1.5', '1.6')] == ['v1', 'v1', 'v1', 'v2']


@pytest.mark.parametrize('family, version', ALL)
def test_every_evaluator_entry_point_resolves(family, version):
    assert callable(procedures.procedure(family, version).entry_point())


def test_evidence_basis_is_set_per_path():
    """ADR 0008: functional-model runs are simulated; real code on the host CPU is measured."""
    basis = {(f, v): procedures.procedure(f, v).evidence_basis for f, v in ALL}
    assert {b for (f, _), b in basis.items() if f in ('candidate', 'lowering_calibration')} == {'simulated'}
    assert {b for (f, _), b in basis.items() if f in ('native', 'library_operation')} == {'measured'}


# --- per-version manifests (F1/F2) -----------------------------------------------------------------

def _paths(family, version):
    return {row['path'] for row in procedures.manifest(procedures.procedure(family, version), LIBRARY)['sources']}


def test_each_manifest_names_only_the_files_its_version_reads():
    v13, v14, v15 = _paths('candidate', '1.3'), _paths('candidate', '1.4'), _paths('candidate', '1.5')
    assert 'library/dx100/certification/seams.cc' in v13 and not any('/v1_4/' in p or '/v1_5/' in p for p in v13)
    assert 'swdb/certification_blinding.py' not in v13 and 'swdb/certification_process.py' not in v13
    assert 'swdb/certification_blinding.py' in v14 and 'swdb/certification_process.py' not in v14
    assert not any('/v1_5/' in p for p in v14) and 'library/dx100/certification/seams.cc' not in v14
    assert 'library/dx100/certification/v1_5/evaluator.cc' in v15 and 'library/dx100/certification/v1_4/seams.cc' in v15
    for version in ('1.3', '1.4', '1.5', '1.6'):
        paths = _paths('candidate', version)
        assert 'swdb/certification_feedback.py' in paths and 'swdb/certification_legality.py' in paths
        assert not any(p.startswith('library/native/') for p in paths)
    native = _paths('native', '1.4')
    assert 'library/native/certification/v1_4/seams.cc' in native and 'swdb/certification_legality.py' not in native
    lop10, lop11 = _paths('library_operation', '1.0'), _paths('library_operation', '1.1')
    assert 'swdb/certification_isolation.py' not in lop10
    assert {'swdb/certification_isolation.py', 'swdb/certification_faults.py'} <= lop11
    assert 'swdb/extensa/search.py' not in lop11 and 'swdb/extensa/synthesis/certify.py' in lop11
    assert 'library/dx100/certification/v1_5/arena.hpp' in _paths('library_operation', '1.2')


def test_a_later_version_file_does_not_change_an_earlier_version_digest(tmp_path):
    library = tmp_path / 'library'
    shutil.copytree(LIBRARY, library)
    before = {v: procedures.manifest(procedures.procedure('candidate', v), library)['sources_sha256']
              for v in ('1.3', '1.4', '1.5')}
    evaluator = library / 'dx100/certification/v1_5/evaluator.cc'
    evaluator.write_text(evaluator.read_text() + '\n// edited\n')
    after = {v: procedures.manifest(procedures.procedure('candidate', v), library)['sources_sha256']
             for v in ('1.3', '1.4', '1.5')}
    assert after['1.3'] == before['1.3'] and after['1.4'] == before['1.4'] and after['1.5'] != before['1.5']


def test_the_kernel_plugin_is_recorded_beside_the_version_identity():
    proc = procedures.procedure('candidate', '1.6')
    with_plugin = procedures.manifest(proc, LIBRARY, kernels.BC)
    assert with_plugin['sources_sha256'] == procedures.manifest(proc, LIBRARY)['sources_sha256']
    assert {row['path'] for row in with_plugin['kernel_sources']} == {
        'swdb/kernels/__init__.py', 'swdb/kernels/bc.py', 'result_check:' + kernels.BC.native_verifier}


def test_new_records_carry_family_commit_and_manifest():
    fields, _ = procedures.command_fields(procedures.procedure('library_operation', '1.2'), LIBRARY)
    assert fields['family'] == 'library_operation' and fields['library_operation_version'] == '1.2'
    assert fields['sources_sha256'] and fields['sources'][-1]['path'].endswith('#library_operation/1.2')
    assert set(fields['code']) == {'git_commit', 'sources_differ_from_commit'}
    if fields['code']['git_commit'] is not None:
        assert len(fields['code']['git_commit']) == 40
    candidate, _ = procedures.command_fields(procedures.procedure('candidate', '1.6'), LIBRARY, kernels.BFS)
    assert 'library_operation_version' not in candidate and candidate['kernel_sources']


@pytest.mark.parametrize('family, version', ALL)
def test_frozen_digest_of_every_version(family, version):
    """Fails when code a version reads changes without a change to the version table (F1/F2)."""
    proc = procedures.procedure(family, version)
    found = procedures.manifest(proc, LIBRARY)['sources_sha256']
    assert (family, version) in FROZEN, 'a new version needs a frozen digest here'
    assert found == proc.sources_sha256 == FROZEN[(family, version)], (
        f'{family} {version}: its files changed ({found}). A behavior change gets a new version in '
        'swdb/certification_procedures.py; a refactor that keeps behavior re-declares the digest there and '
        'here, with a dated note in the ticket.')


def test_unpinned_dx100_1_3_and_1_4_files_are_unchanged():
    """F6: "1.3 runs unchanged": the unpinned files certify 1.3 and 1.4 read keep their bytes."""
    found = {rel: hashlib.sha256((LIBRARY / rel).read_bytes()).hexdigest() for rel in UNPINNED_DX100_1_3_1_4}
    assert found == UNPINNED_DX100_1_3_1_4
    # Pins live in library entries and profiles, and in certificates outside their source manifests
    # (`command.sources` lists every file a run read; that is provenance, not a pin).
    texts = [p.read_text() for p in LIBRARY.rglob('*.yaml')]
    for path in (ROOT / 'records/certifications').glob('*.yaml'):
        record = yaml.safe_load(path.read_text())
        command = {k: v for k, v in (record.get('command') or {}).items() if k not in ('sources', 'kernel_sources')}
        texts.append(yaml.safe_dump({**record, 'command': command}))
    pinned_text = ''.join(texts)
    assert not any(digest in pinned_text for digest in found.values()), 'a listed file is pinned after all'


# --- old records (C10) ------------------------------------------------------------------------------------

def _committed():
    return [yaml.safe_load(p.read_text()) for p in sorted((ROOT / 'records/certifications').glob('*.yaml'))]


def test_every_committed_certification_has_a_known_procedure():
    rows = {record['id']: procedures.classify(record) for record in _committed()}
    assert rows and all(row['note'] != 'unknown label' for row in rows.values()), rows
    b7954 = rows['certification.b7954f4df9dd4e228fb12437b845f190']
    assert (b7954['family'], b7954['label'], b7954['procedure']) == ('native', '1.4', '1.3')
    assert rows['certification.7f15786592134bdabbc921f16c806ce1']['procedure'] == '1.4'
    assert rows['certification.f5b8f6a732714abfad544aaa65982438']['procedure'] == '1.3'
    lowering = [r for i, r in rows.items() if r['family'] == 'lowering_calibration']
    assert lowering and {(r['label'], r['runnable']) for r in lowering} == {('1.0', False)}


def test_colliding_labels_resolve_by_family_and_sources():
    lop = procedures.classify({'command': {'version': '1.2', 'kind': 'library_operation_differential'}})
    candidate = procedures.classify({'command': {'version': '1.2'}, 'candidate': {'contract': 'x'}})
    assert (lop['family'], lop['runnable']) == ('library_operation', True)
    assert (candidate['family'], candidate['runnable'], candidate['procedure']) == ('candidate', False, '1.2')
    cell_named = procedures.classify({'command': {'version': '1.4', 'sources_sha256': '29f3bcab362c7c830f0030122aae1b'
                                                  '3382c1eb83be3171f1a91b62a690724be1'}, 'candidate': {'contract': 'x'}})
    assert cell_named['variant'] == 'cell_named_record_files' and '93a2a94' in cell_named['note']
    new = procedures.classify({'command': {'version': '1.4', 'family': 'native'}})
    assert (new['family'], new['procedure'], new['runnable']) == ('native', '1.4', True)


def test_the_cli_offers_every_family_version():
    import argparse
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers()
    sub = c.register_cli(commands)
    action = next(a for a in sub._actions if a.dest == 'command_version')
    assert set(action.choices) == {v for _, v in ALL}
    assert 'library operation 1.0/1.1/1.2 (default 1.2)' in action.help and 'candidate' in action.help
