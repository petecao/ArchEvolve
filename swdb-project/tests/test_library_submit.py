"""Public proposal 1.1 library gates and actual tree reproduction, 2026-10-03 ET.

Temporary certification/review receipts below are explicit contract fixtures.
They test submit behavior and do not represent execution or real promotion.
"""
import copy
import difflib
import json
from pathlib import Path
import shutil

import pytest
import yaml

from conftest import REPO
from test_proposals import proposal_setup
from test_typed_library import entry as contract_entry
from swdb import artifacts
from swdb.library import Library
from swdb.store import Store

CONTRACT = 'contract.fixture'
INTRINSIC = 'intrinsic.fixture_load'
LOWERING = 'lowering.fixture_load.fixture.1'
OPERATION = 'operation.fixture_copy'
SHIPPED = 'src/swdb_fixture_lowering.hpp'
HEADER = ('// Workflow contract fixture, 2026-10-03 ET.\n'
          'inline int fixture_reference(int value) { return value; }\n'
          'inline int fixture_lower(int value) { return value; }\n'
          'inline int fixture_copy(int value) { return value; }\n')


def new_file_patch(path, content):
    return ''.join(difflib.unified_diff([], content.splitlines(keepends=True),
                                      fromfile='/dev/null', tofile='b/' + path))


def receipt(records, entry_id, content_sha256):
    suffix = entry_id.replace('.', '-')
    certificate_id = 'fixture-cert-' + suffix
    certification = {
        'schema_version': '0.4', 'kind': 'certification', 'id': certificate_id,
        'status': 'draft', 'created': '2026-10-03', 'updated': '2026-10-03',
        'provenance': [{'id': 'fixture', 'kind': 'agent_run',
                        'description': 'Submit contract fixture only; no executed certification.', 'uri': None}],
        'entry': {'id': entry_id, 'content_sha256': content_sha256},
        'command': {'version': 'fixture', 'sources_sha256': '0' * 64}, 'host': {},
        'matrix': [{'status': 'passed'}], 'negative_controls': [{'status': 'rejected'}],
        'verdict': 'certified', 'evidence_basis': 'simulated', 'evidence_kind': 'contract_fixture',
    }
    records.write('certifications/' + certificate_id + '.yaml', certification)
    library_entry = Library(records.path.parent / 'library').get(entry_id)
    evidence_ids = [certificate_id]
    if library_entry and library_entry['kind'] == 'intrinsic':
        evidence_ids = ['fixture-cert-' + lower_id.replace('.', '-') for lower_id in library_entry['lowerings']]
    review = {
        'schema_version': '0.4', 'kind': 'review', 'id': 'fixture-review-' + suffix,
        'status': 'reviewed', 'created': '2026-10-03', 'updated': '2026-10-03',
        'provenance': [{'id': 'fixture', 'kind': 'human_report',
                        'description': 'Temporary test review fixture; no real promotion.', 'uri': None}],
        'target': {'id': entry_id, 'content_sha256': content_sha256},
        'reviewer': 'Contract fixture', 'reviewed_at': '2026-10-03T00:00:00Z',
        'evidence': evidence_ids,
    }
    return records.write('reviews/' + review['id'] + '.yaml', review)


@pytest.fixture
def library_submit(proposal_setup):
    records, runs, snapshot, request = proposal_setup
    root = records.path.parent / 'library'
    root.mkdir()
    (root / 'fixture.hpp').write_text(HEADER)
    driver = root / 'fixture_driver.cc'
    driver.write_text('// Workflow-only driver fixture, 2026-10-03 ET.\nint main(){return 0;}\n')
    code_hash = artifacts.file_hash(root / 'fixture.hpp')
    reference = {'path': 'fixture.hpp', 'sha256': code_hash, 'symbol': 'fixture_reference'}
    test = {'path': 'fixture_driver.cc', 'sha256': artifacts.file_hash(driver), 'input_set': 'contract_fixture'}
    contract = contract_entry()
    contract['uses_intrinsics'] = [INTRINSIC]
    contract['uses_library_operations'] = [OPERATION]
    intrinsic = {
        'kind': 'intrinsic', 'id': INTRINSIC, 'intrinsic_record': 'dxc_gather',
        'provenance': {'origin': {'intrinsic_specification': 'workflow-fixture'}},
        'clauses': [], 'signature': 'int fixture_load(int)', 'intent': 'Contract fixture only.',
        'reference_semantics': reference, 'hardware_operations': [],
        'memory_footprint': {'reads': [], 'writes': []}, 'completion': {'mode': 'immediate'},
        'lowerings': [LOWERING],
    }
    lowering = {
        'kind': 'lowering', 'id': LOWERING, 'intrinsic': INTRINSIC,
        'provenance': {'origin': {'intrinsic_specification': 'workflow-fixture'}}, 'clauses': [],
        'interface': {'id': 'fixture', 'version': '1'},
        'location': {'path': 'fixture.hpp', 'symbol': 'fixture_lower'},
        'code_sha256': code_hash, 'build_defines': {}, 'differential_test': test,
    }
    operation = {
        'kind': 'library_operation', 'id': OPERATION,
        'provenance': {'origin': {'intrinsic_specification': 'workflow-fixture'}}, 'clauses': [],
        'signature': 'int fixture_copy(int)', 'intent': 'Contract fixture only.',
        'location': {'path': 'fixture.hpp', 'symbol': 'fixture_copy'}, 'code_sha256': code_hash,
        'reference_semantics': reference, 'uses_intrinsics': [INTRINSIC], 'differential_test': test,
    }
    entries = {CONTRACT: contract, INTRINSIC: intrinsic, LOWERING: lowering, OPERATION: operation}
    relative = {CONTRACT: 'rewrite_contracts/fixture.yaml', INTRINSIC: 'intrinsics/fixture.yaml',
                LOWERING: 'lowerings/fixture/1/fixture.yaml', OPERATION: 'library_operations/fixture.yaml'}
    reviews = {}
    for entry_id, data in entries.items():
        target = root / relative[entry_id]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(yaml.safe_dump(data))
        reviews[entry_id] = receipt(records, entry_id, artifacts.digest(data))
    pins = [{'id': entry_id, 'content_sha256': artifacts.digest(data)} for entry_id, data in entries.items()]
    section = {'contract': pins[0], 'entries': pins[1:],
               'shipped_files': [{'path': SHIPPED, 'sha256': code_hash, 'lowerings': [LOWERING]}]}

    def library_request(**changes):
        path = request()
        data = yaml.safe_load(path.read_text())
        data['message_version'] = '1.1'
        data['library'] = copy.deepcopy(section)
        data['constraints']['editable_files'].append(SHIPPED)
        data['payload']['content'] += new_file_patch(SHIPPED, HEADER)
        data['producer']['name'] = 'library-submit-authoring-session-fixture'
        data.update(changes)
        path.write_text(yaml.safe_dump(data))
        return path

    return records, runs, snapshot, library_request, root, entries, reviews


def submit(fixture, transform=None):
    records, runs, _, request, *_ = fixture
    path = request()
    if transform:
        data = yaml.safe_load(path.read_text())
        transform(data)
        path.write_text(yaml.safe_dump(data))
    result = records.swdb('submit', path, '--runs-dir', runs, '--format', 'json')
    assert result.stdout, result.stderr
    return result, json.loads(result.stdout)


def assert_retained_rejection(fixture, transform, reason):
    records = fixture[0]
    result, proposal = submit(fixture, transform)
    assert result.returncode == 1, result.stderr
    assert proposal['outcome']['state'] in {'rejected', 'failed'}
    assert reason in proposal['outcome']['reason'], proposal['outcome']
    assert 'candidate' not in proposal
    fetched = records.swdb('get', proposal['id'], '--format', 'json')
    assert fetched.returncode == 0, fetched.stderr
    assert json.loads(fetched.stdout)['outcome'] == proposal['outcome']


def test_public_submit_uses_all_current_shared_dependencies_and_exact_header(library_submit):
    records, _, snapshot, _, root, entries, _ = library_submit
    library = Library(root, Store(records.path))
    assert not library.validate()
    assert all(library.state(entry_id) == {'tier': 'shared', 'status': 'certified'} for entry_id in entries)
    before = artifacts.identify(snapshot['artifact']['path'])
    result, proposal = submit(library_submit)
    assert result.returncode == 0, result.stderr
    assert proposal['outcome']['state'] == 'candidate_created'
    assert 'provider' not in proposal
    got = records.swdb('get', proposal['candidate'], '--format', 'json')
    assert got.returncode == 0, got.stderr
    candidate = json.loads(got.stdout)
    tree = Path(candidate['artifact']['path'])
    assert (tree / SHIPPED).read_bytes() == (root / 'fixture.hpp').read_bytes()
    assert set(item['path'] for item in candidate['artifact']['files']) - set(item['path'] for item in before['files']) == {SHIPPED}
    assert artifacts.identify(snapshot['artifact']['path']) == before
    assert candidate['producer']['name'] == 'library-submit-authoring-session-fixture'
    assert candidate['state'] == 'unverified'


@pytest.mark.parametrize('dependency', [INTRINSIC, LOWERING, OPERATION])
def test_submit_refuses_an_omitted_dependency(library_submit, dependency):
    def omit(data):
        data['library']['entries'] = [pin for pin in data['library']['entries'] if pin['id'] != dependency]
    assert_retained_rejection(library_submit, omit, 'omits a contract dependency')


@pytest.mark.parametrize('entry_id', [CONTRACT, INTRINSIC, LOWERING, OPERATION])
def test_submit_refuses_an_unreviewed_contract_or_dependency(library_submit, entry_id):
    library_submit[-1][entry_id].unlink()
    assert_retained_rejection(library_submit, None, 'requires shared certified library entry')


def test_submit_refuses_a_stale_content_pin(library_submit):
    def stale(data):
        data['library']['entries'][0]['content_sha256'] = '0' * 64
    assert_retained_rejection(library_submit, stale, 'stale or missing library entry')


def test_submit_does_not_reuse_review_after_normative_content_changes(library_submit):
    records, _, _, _, root, entries, _ = library_submit
    entries[LOWERING]['build_defines']['fixture_changed'] = True
    (root / 'lowerings/fixture/1/fixture.yaml').write_text(yaml.safe_dump(entries[LOWERING]))
    def update_request_pin(data):
        for pin in data['library']['entries']:
            if pin['id'] == LOWERING:
                pin['content_sha256'] = artifacts.digest(entries[LOWERING])
    assert_retained_rejection(library_submit, update_request_pin, 'requires shared certified library entry')


def test_submit_requires_message_1_1_for_library_section(library_submit):
    assert_retained_rejection(library_submit, lambda data: data.update(message_version='1.0'), '1.1')


def test_submit_refuses_wrong_declared_header_hash(library_submit):
    def wrong_pin(data):
        data['library']['shipped_files'][0]['sha256'] = '0' * 64
    assert_retained_rejection(library_submit, wrong_pin, 'sha256 differs from certified lowering')


def test_submit_refuses_wrong_actual_header_bytes(library_submit):
    def wrong_bytes(data):
        data['payload']['content'] = data['payload']['content'].replace('+inline int fixture_lower(int value) { return value; }',
                                                                      '+inline int fixture_lower(int value) { return value + 1; }')
    assert_retained_rejection(library_submit, wrong_bytes, 'shipped header bytes differ')


def test_submit_requires_exact_editable_header_path(library_submit):
    def absent_path(data):
        data['constraints']['editable_files'] = ['src/bfs.cc', 'src/*.hpp']
    assert_retained_rejection(library_submit, absent_path, 'exact editable path')


def test_submit_rejects_an_extra_new_file_even_if_editable(library_submit):
    def extra(data):
        data['constraints']['editable_files'].append('src/extra.hpp')
        data['payload']['content'] += new_file_patch('src/extra.hpp', '// Additional uncontracted file.\n')
    assert_retained_rejection(library_submit, extra, 'may add only its declared lowering files')


def test_shipped_lowering_path_must_be_new(library_submit):
    def existing(data):
        data['library']['shipped_files'][0]['path'] = 'src/bfs.cc'
    assert_retained_rejection(library_submit, existing, 'may add only its declared lowering files')


def test_actual_dx100_submit_reproduces_the_certified_tree(records, tmp_path):
    """Actual delivery bytes/proposal flow; review state remains an explicit test fixture."""
    from swdb import certification
    records.copy_repo()
    root = records.path.parent / 'library'
    shutil.copytree(REPO / 'library', root)
    store = Store(records.path)
    source_folder = tmp_path / 'dx100-reconstruction'; source_folder.mkdir()
    tree, source = certification.materialize_snapshot(store, certification.DEFAULT_SNAPSHOT, source_folder)
    source['artifact']['path'] = str(tree)
    records.write('source_snapshots/' + source['id'] + '.yaml', source)
    package = records.swdb('fixture-package', source['id'], '--id', 'dx100-library-package', '--format', 'json')
    assert package.returncode == 0, package.stderr
    library = Library(root, Store(records.path))
    assert not library.validate()
    contract = library.get('contract.bfs_read_offload')
    dependencies = set(contract['uses_intrinsics']) | set(contract['uses_library_operations'])
    for intrinsic in contract['uses_intrinsics']:
        dependencies.update(library.get(intrinsic)['lowerings'])
    for entry_id in dependencies | {contract['id']}:
        assert library.state(entry_id)['status'] == 'certified'
        receipt(records, entry_id, library.content_sha256(entry_id))
    lowerings = sorted(entry_id for entry_id in dependencies if library.get(entry_id)['kind'] == 'lowering')
    patch = (REPO / 'library/dx100/peter-section5.patch').read_text()
    data = {
        'message_version': '1.1', 'id': 'dx100-library-tree-reproduction',
        'producer': {'name': 'fixture-dx100-authoring-session', 'role': 'sw', 'test_client': True},
        'profile_package': 'dx100-library-package', 'source_snapshot': source['id'],
        'implementation': source['implementation'], 'source_sha256': source['artifact']['sha256'],
        'intent': 'Reproduce the exact certified tree through public submit; workflow fixture only.',
        'regions': [source['regions'][0]['id']],
        'constraints': {'editable_files': [certification.BFS, certification.HEADER],
                        'preserve_correctness': True, 'preserve_roi': True},
        'payload': {'kind': 'patch', 'content': patch}, 'required_operations': [],
        'library': {'contract': {'id': contract['id'], 'content_sha256': library.content_sha256(contract['id'])},
                    'entries': [{'id': entry_id, 'content_sha256': library.content_sha256(entry_id)} for entry_id in sorted(dependencies)],
                    'shipped_files': [{'path': certification.HEADER,
                                       'sha256': artifacts.file_hash(root / 'dx100/dxc_lowering.hpp'),
                                       'lowerings': lowerings}]},
    }
    path = tmp_path / 'dx100-proposal.yaml'; path.write_text(yaml.safe_dump(data))
    result = records.swdb('submit', path, '--runs-dir', tmp_path / 'delivery-runs', '--format', 'json')
    assert result.returncode == 0, result.stderr
    proposal = json.loads(result.stdout)
    got = records.swdb('get', proposal['candidate'], '--format', 'json')
    assert got.returncode == 0, got.stderr
    candidate = json.loads(got.stdout)
    certificates = [record.data for record in store.of_kind('certification')
                    if record.data['entry'] == {'id': contract['id'], 'content_sha256': library.content_sha256(contract['id'])}
                    and record.data.get('candidate', {}).get('tree_sha256') == candidate['artifact']['sha256']
                    and record.data['verdict'] == 'certified' and record.data.get('evidence_kind') == 'execution']
    assert certificates, 'public submit changed the tree certified by the actual execution receipt'
    assert candidate['artifact']['sha256'] == artifacts.identify(candidate['artifact']['path'])['sha256']
    assert (Path(candidate['artifact']['path']) / certification.HEADER).read_bytes() == (root / 'dx100/dxc_lowering.hpp').read_bytes()
