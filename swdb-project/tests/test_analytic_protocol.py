"""Public frozen-estimate protocol and ADR 0013 boundary regressions.
Updated: 2026-10-06 ET. Artificial rates/counts are explicit contract fixtures.
"""
import json
import shutil

import pytest
import yaml

from conftest import REPO, run_swdb


@pytest.fixture
def team(tmp_path):
    records = tmp_path / 'records'
    shutil.copytree(REPO / 'records', records)
    return records


def target(tmp_path, **changes):
    data = {'kind': 'target_description', 'schema_version': '0.4', 'id': 'fixture.target',
        'status': 'draft', 'created': '2026-10-06', 'updated': '2026-10-06',
        'provenance': [{'id': 'fixture', 'kind': 'source_code', 'description': 'Contract fixture.', 'uri': None}],
        'format': 'swdb.target-description.v1', 'version': '1', 'target': 'mbit10', 'threads': 1,
        'estimator_variant': 'team', 'calibration_sources': [], 'dram_address_layout': None,
        'mechanisms': [{'model': 'streaming_bandwidth', 'parameters': {'bytes_per_s': {
            'value': 32, 'basis': 'reported', 'source': 'Contract fixture.', 'unit': 'bytes/s'}}}], **changes}
    path = tmp_path / 'target.yaml'
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path


def request(tmp_path, **changes):
    settings = {'mode': 'estimated', 'estimator_version': 'swdb.analytic.v1',
        'target_description': changes.get('target_description') or str(target(tmp_path)), 'inputs': ['kron-g16-k16'],
        'roi': 'fixture.stream.v1', 'threads': 1, **changes}
    path = tmp_path / 'freeze.yaml'
    path.write_text(yaml.safe_dump({'message_version': '1.0', 'id': 'fixture.protocol',
                                  'version': 1, 'settings': settings}, sort_keys=False))
    return path


def test_freeze_estimate_protocol_pins_version_target_and_input(team, tmp_path):
    result = run_swdb('freeze-protocol', request(tmp_path), '--records', team, '--format', 'json')
    assert result.returncode == 0, result.stderr + result.stdout
    protocol = json.loads(result.stdout)
    frozen = protocol['settings']
    assert frozen['estimator_version'] == 'swdb.analytic.v1'
    assert frozen['target_description']['id'] == 'fixture.target'
    assert len(frozen['target_description']['sha256']) == 64
    assert frozen['target_description']['snapshot']['mechanisms'][0]['parameters']['bytes_per_s']['value'] == 32
    assert set(protocol['input_identities']) == {'kron-g16-k16'}
    checked = run_swdb('validate', '--records', team)
    assert checked.returncode == 0, checked.stderr + checked.stdout


@pytest.mark.parametrize('changes, offending', [
    ({'target': 'dx100-e4fc4af-4c'}, 'dx100-e4fc4af-4c'),
    ({'calibration_sources': ['bfs-dx100-smoke-20260925-a6']}, 'bfs-dx100-smoke-20260925-a6'),
    ({'estimator_variant': 'research'}, 'fixture.target'),
])
def test_team_freeze_refuses_gem5_or_research_dependencies(team, tmp_path, changes, offending):
    path = target(tmp_path, **changes)
    result = run_swdb('freeze-protocol', request(tmp_path, target_description=str(path)),
                      '--records', team, '--format', 'json')
    assert result.returncode == 1 and 'ADR 0013' in result.stderr and offending in result.stderr, result.stderr
    assert not list((team / 'protocols').glob('fixture.protocol.*'))


def test_default_dx100_dispatch_refuses_before_submission_and_explicit_extensa_routes(team, tmp_path):
    path = tmp_path / 'build.yaml'
    path.write_text(yaml.safe_dump({'message_version': '1.0', 'id': 'fixture.dx100.build',
        'machine': 'mbit10', 'hardware_target': 'dx100-e4fc4af-4c',
        'model_root': '/private/tmp/fixture-model', 'fixture': True}))
    result = run_swdb('dx100-build', path, '--records', team, '--runs-dir', tmp_path / 'runs', '--lane', '0', '--format', 'json')
    assert result.returncode == 1 and 'ADR 0013' in result.stderr and 'dx100-e4fc4af-4c' in result.stderr
    assert not (team / 'evaluations/fixture.dx100.build.yaml').exists()
    research = run_swdb('dx100-build', path, '--records', team, '--runs-dir', tmp_path / 'runs', '--lane', '0', '--mode', 'extensa',
        '--campaign', 'extensa-gem5-bfs-20261004-f1', '--format', 'json')
    assert 'ADR 0013' not in research.stderr and 'unrecognized arguments' not in research.stderr
    retained = yaml.safe_load((team / 'evaluations/fixture.dx100.build.yaml').read_text())
    assert retained['mode'] == 'extensa' and retained['campaign'] == 'extensa-gem5-bfs-20261004-f1'


def digest(data):
    import hashlib
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def fixture_characterization(team, **binding_changes):
    # Zero-work contract fixture tests binding only; these placeholders never
    # stand in for LLVM characterization or application execution evidence.
    data = {'kind': 'workload_characterization', 'schema_version': '0.4', 'id': 'fixture.counts',
        'status': 'draft', 'created': '2026-10-06', 'updated': '2026-10-06',
        'provenance': [{'id': 'fixture', 'kind': 'source_code', 'description': 'Zero-work binding contract fixture.'}],
        'format': 'swdb.workload-characterization.v1', 'subject': {'kind': 'implementation', 'id': 'gapbs-bfs-do'},
        'input': 'kron-g16-k16', 'source': {'path': 'fixture.cpp', 'sha256': '0' * 64,
            'build_flags': [], 'run_arguments': [], 'protected_driver': 'fixture'},
        'host': {'machine': 'fixture', 'architecture': 'fixture', 'system': 'fixture'},
        'toolchain': {'llvm_version': '22.fixture', 'llvm_bin': 'fixture', 'compiler_flags': [],
                      'plugin_linkage': 'host_symbols', 'run_library_paths': []},
        'counting': {'level': 'source_normalized_ir', 'passes': [], 'native_runs': 1, 'basis': 'measured',
            'vector_multiplicity': 'fixture', 'operation_definition': 'fixture', 'loop_definition': 'fixture',
            'binary_sha256': '0' * 64, 'counts_sha256': '0' * 64, 'output_directory': 'fixture'},
        'static_analysis': {'basis': 'code_reading', 'source_ir_sha256': '0' * 64,
            'optimized_ir_sha256': '0' * 64, 'loops': [], 'optimized_facts': {}, 'mapping_note': 'fixture'},
        'coverage': {'scope': 'contract fixture'}, 'regions': [], 'unmapped_loops': [], 'unmodeled_calls': [],
        'evidence_kind': 'contract_fixture', 'binding': {'state': 'fixture',
            'subject_source_identity': {'subject_record_sha256': digest(yaml.safe_load((team / 'implementations/gapbs-bfs-do.yaml').read_text()))},
            'input_record_sha256': digest(yaml.safe_load((team / 'inputs/kron-g16-k16.yaml').read_text())),
            'roi': 'fixture.stream.v1', 'threads': 1, 'run_arguments_sha256': digest([]),
            'note': 'Binding contract fixture only.', **binding_changes}}
    data['identity_sha256'] = digest(data)
    path = team / 'workload_characterizations/fixture.counts.yaml'
    path.parent.mkdir(exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return data


def frozen(team, tmp_path, **settings):
    result = run_swdb('freeze-protocol', request(tmp_path, **settings), '--records', team, '--format', 'json')
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)


def estimate(team, tmp_path, protocol, *extra):
    return run_swdb('estimate', '--records', team, '--characterization', 'fixture.counts',
        '--target-description', tmp_path / 'target.yaml', '--protocol', protocol['id'],
        '--id', 'fixture.estimate', '--format', 'json', *extra)


def test_estimate_uses_frozen_protocol_and_preserves_fixture_state(team, tmp_path):
    fixture_characterization(team)
    protocol = frozen(team, tmp_path)
    result = estimate(team, tmp_path, protocol)
    assert result.returncode == 0, result.stderr + result.stdout
    data = json.loads(result.stdout)
    assert data['protocol_sha256'] == protocol['identity_sha256']
    assert data['estimator_sha256'] == protocol['settings']['estimator_sha256']
    assert data['binding']['state'] == 'fixture' and data['evidence_kind'] == 'contract_fixture'
    checked = run_swdb('validate', '--records', team)
    assert checked.returncode == 0, checked.stderr + checked.stdout


@pytest.mark.parametrize('binding, message', [
    ({'roi': 'different.roi'}, 'ROI'),
    ({'threads': 2}, 'thread'),
    ({'input_record_sha256': '0' * 64}, 'input'),
    ({'subject_source_identity': {'subject_record_sha256': '0' * 64}}, 'source'),
    ({'state': 'unverified'}, 'verified registered-source'),
    ({'state': 'verified'}, 'verified registered-source'),
])
def test_estimate_refuses_count_binding_mismatch(team, tmp_path, binding, message):
    protocol = frozen(team, tmp_path)
    fixture_characterization(team, **binding)
    result = estimate(team, tmp_path, protocol)
    assert result.returncode == 1 and message.lower() in result.stderr.lower(), result.stderr
    assert not (team / 'estimates/fixture.estimate.yaml').exists()


def test_recursive_gem5_derived_calibration_is_refused(team, tmp_path):
    bridge = yaml.safe_load(target(tmp_path, calibration_sources=['bfs-dx100-smoke-20260925-a6']).read_text())
    bridge['id'] = 'fixture.bridge'
    folder = team / 'target_descriptions'
    folder.mkdir(exist_ok=True)
    (folder / 'fixture.bridge.yaml').write_text(yaml.safe_dump(bridge))
    outer = target(tmp_path, calibration_sources=['fixture.bridge'])
    result = run_swdb('freeze-protocol', request(tmp_path, target_description=str(outer)), '--records', team)
    assert result.returncode == 1 and all(name in result.stderr for name in ('ADR 0013', 'fixture.bridge', 'bfs-dx100-smoke-20260925-a6'))


@pytest.mark.parametrize('source, allowed', [('dx100-e4fc4af-4c', True), ('bfs-dx100-smoke-20260925-a6', False)])
def test_code_reading_allows_pinned_configuration_but_never_execution(team, tmp_path, source, allowed):
    path = target(tmp_path)
    data = yaml.safe_load(path.read_text())
    fact = data['mechanisms'][0]['parameters']['bytes_per_s']
    fact.update(basis='code_reading', source=source)
    path.write_text(yaml.safe_dump(data))
    result = run_swdb('freeze-protocol', request(tmp_path, target_description=str(path)), '--records', team)
    assert result.returncode == (0 if allowed else 1), result.stderr
    if not allowed:
        assert 'ADR 0013' in result.stderr and source in result.stderr


def test_target_changed_after_freeze_is_refused(team, tmp_path):
    fixture_characterization(team)
    protocol = frozen(team, tmp_path)
    path = tmp_path / 'target.yaml'
    data = yaml.safe_load(path.read_text())
    data['mechanisms'][0]['parameters']['bytes_per_s']['value'] = 64
    path.write_text(yaml.safe_dump(data))
    result = estimate(team, tmp_path, protocol)
    assert result.returncode == 1 and 'target description differs' in result.stderr


def test_changed_estimator_bundle_refuses_execution_but_history_validates(team, tmp_path):
    import subprocess
    import sys
    fixture_characterization(team)
    protocol = frozen(team, tmp_path)
    tool = tmp_path / 'tool'
    for folder in ('swdb', 'schemas', 'vocab'):
        shutil.copytree(REPO / folder, tool / folder)
    for folder in ('apps', '.scratch', 'library', 'docs', 'tests'):
        (tool / folder).symlink_to(REPO / folder, target_is_directory=True)
    model = tool / 'swdb/analytic_models.py'
    model.write_text(model.read_text() + '\n# Fixture hot edit after protocol freeze.\n')
    arguments = ['estimate', '--records', str(team), '--characterization', 'fixture.counts',
        '--target-description', str(tmp_path / 'target.yaml'), '--protocol', protocol['id'],
        '--id', 'fixture.estimate', '--format', 'json']
    changed = subprocess.run([sys.executable, '-m', 'swdb', *arguments], cwd=tool, capture_output=True, text=True)
    assert changed.returncode == 1 and 'implementation changed after freeze' in changed.stderr, changed.stderr
    historical = subprocess.run([sys.executable, '-m', 'swdb', 'validate', '--records', str(team)],
                                cwd=tool, capture_output=True, text=True)
    assert historical.returncode == 0, historical.stderr + historical.stdout


def test_run_arguments_changed_after_counting_are_refused(team, tmp_path):
    fixture_characterization(team, run_arguments_sha256='0' * 64)
    protocol = frozen(team, tmp_path, input_run_arguments={'kron-g16-k16': []})
    result = estimate(team, tmp_path, protocol)
    assert result.returncode == 1 and 'run argument' in result.stderr.lower(), result.stderr


@pytest.mark.parametrize('field', ['source_evidence', 'notes', 'code'])
def test_source_evidence_cannot_hide_execution_dependency(team, tmp_path, field):
    path = target(tmp_path, dram_address_layout={field: ['bfs-dx100-smoke-20260925-a6']})
    result = run_swdb('freeze-protocol', request(tmp_path, target_description=str(path)), '--records', team)
    assert result.returncode == 1 and 'ADR 0013' in result.stderr and 'bfs-dx100-smoke-20260925-a6' in result.stderr


def test_explicit_extensa_add_tags_the_record_at_creation(team, tmp_path):
    data = yaml.safe_load((team / 'hardware_targets/dx100-e4fc4af-4c.yaml').read_text())
    data['id'] = 'fixture.gem5.target'
    file = tmp_path / 'import.yaml'
    file.write_text(yaml.safe_dump(data))
    refused = run_swdb('add', file, '--records', team)
    assert refused.returncode == 1 and 'ADR 0013' in refused.stderr
    added = run_swdb('add', file, '--records', team, '--mode', 'extensa', '--campaign', 'extensa-gem5-bfs-20261004-f1')
    assert added.returncode == 0, added.stderr
    retained = yaml.safe_load((team / 'hardware_targets/fixture.gem5.target.yaml').read_text())
    assert retained['mode'] == 'extensa' and retained['campaign'] == 'extensa-gem5-bfs-20261004-f1'


def test_calibration_record_changed_under_same_target_hash_is_refused(team, tmp_path):
    bridge = yaml.safe_load(target(tmp_path).read_text())
    bridge['id'] = 'fixture.bridge'
    folder = team / 'target_descriptions'
    folder.mkdir(exist_ok=True)
    file = folder / 'fixture.bridge.yaml'
    file.write_text(yaml.safe_dump(bridge))
    outer = target(tmp_path, calibration_sources=['fixture.bridge'])
    fixture_characterization(team)
    protocol = frozen(team, tmp_path, target_description=str(outer))
    bridge['mechanisms'][0]['parameters']['bytes_per_s']['value'] = 128
    file.write_text(yaml.safe_dump(bridge))
    result = estimate(team, tmp_path, protocol)
    assert result.returncode == 1 and 'dependency' in result.stderr.lower() and 'fixture.bridge' in result.stderr


def test_explicit_team_mode_overrides_an_inherited_extensa_campaign(team, tmp_path):
    path = target(tmp_path, target='dx100-e4fc4af-4c')
    campaign = {'SWDB_EXTENSA_CAMPAIGN': 'extensa-gem5-bfs-20261004-f1'}
    inherited = run_swdb('freeze-protocol', request(tmp_path, target_description=str(path)),
                         '--records', team, '--format', 'json', env=campaign)
    assert inherited.returncode == 0, inherited.stderr + inherited.stdout
    protocol = json.loads(inherited.stdout)
    assert protocol['mode'] == 'extensa' and protocol['campaign'] == campaign['SWDB_EXTENSA_CAMPAIGN']
    refused = run_swdb('freeze-protocol', tmp_path / 'freeze.yaml', '--records', team,
                       '--mode', 'archevolve', env=campaign)
    assert refused.returncode == 1 and 'ADR 0013' in refused.stderr and 'dx100-e4fc4af-4c' in refused.stderr


def test_public_team_claim_refuses_historical_gem5_evidence(team):
    result = run_swdb('claim', 'bfs-dx100-smoke-20260925-a6', '--audience', 'team', '--records', team)
    assert result.returncode == 1 and 'ADR 0013' in result.stderr and 'bfs-dx100-smoke-20260925-a6' in result.stderr
    assert not list((team / 'team_claims').glob('*.yaml'))
