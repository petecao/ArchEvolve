"""Preparation defect reproduction; fixture bindings only. Updated: 2026-10-05 ET (shared tests/testkit); 2026-09-27 ET."""
import copy
import pytest
from testkit.bfs_protocol import _sim_settings, _model_identity_fixture, _hash, _command, _payload

def test_runtime_repair_needs_new_frozen_instrumentation(protocol_setup, tmp_path):
    from swdb import artifacts, bfs_protocol
    from swdb.store import Store
    from swdb.cli import Failure
    records, workload, _, request, evaluations, _ = protocol_setup
    settings = _sim_settings(request['settings'])
    old_runtime = {'driver_sha256': '371657977d56816a37f4885f19923f37175331d2d15b5d7f6e6049d3fa8c1395',
                   'parser_sha256': '2d589162b6595fee0abf4f1db54aa5b1a0964dab3f51aa408ac06505b6014091',
                   'observer_sha256': '655c5804e26a0d1f8f7738f23ae62268cafe84562dbf8392af6c0169568146fd'}
    new_runtime = {**old_runtime, 'driver_sha256': '476874619644d1256dcc5ca1e853c47b7be2e1dc56f538aaa2dd783842e7ad10',
                   'parser_sha256': 'c9d3e14b70a3689799314556fab2922b1723c00960902109af2922a958cd3498'}
    for role in ('baseline', 'candidate'):
        settings['instrumentation'][role]['verifier_runtime'] = copy.deepcopy(old_runtime)
    identity = _model_identity_fixture(records, tmp_path, settings, evaluations)
    runtime = tmp_path / 'libramulator.so'; runtime.write_bytes(b'explicit fixture runtime')
    model = records.read('evaluations/explicit-model-fixture.yaml')
    model['build']['details']['binaries'].append({'path': str(runtime), 'sha256': _hash(runtime)})
    records.write('evaluations/explicit-model-fixture.yaml', model)
    identity['model_build']['sha256'] = artifacts.digest(model)
    frozen = _command(records, 'freeze-protocol', _payload(tmp_path, 'file-freeze', dict(message_version='1.0', id='file-policy', settings=settings)))
    store = Store(records.path); candidate = store.get(evaluations['baseline']['candidate'])
    representation = bfs_protocol.workload_representation(store, workload['id'], 'gapbs')['representation']
    actual = {**evaluations['baseline']['build'], 'adapter': settings['builds']['baseline']['adapter'],
              'simulator': identity['simulator']['path'], 'simulator_sha256': identity['simulator']['sha256'], 'model_build': identity['model_build']}
    payload = dict(fixture=True, protocol=frozen['id'], protocol_role='baseline', protocol_trial={'source_position': 0, 'repetition': 0},
        workload={'id': workload['id'], 'source': 0, 'representation': {key: representation[key] for key in ('path', 'sha256')}})
    instrumentation = copy.deepcopy(settings['instrumentation']['baseline'])
    def bind():
        return bfs_protocol.validate_protocol_for_simulation(store, payload, candidate,
            actual_target=settings['targets']['baseline']['id'], actual_configuration=settings['targets']['baseline']['configuration'],
            actual_build=actual, actual_instrumentation=instrumentation, actual_threads=settings['threads'],
            actual_roi=settings['roi'], actual_verifier=settings['correctness']['verifier'])
    assert bind()['context']['protocol_binding']['frozen_sha256'] == frozen['identity_sha256']
    for changed in ('driver_sha256', 'parser_sha256'):
        instrumentation['verifier_runtime'] = {**old_runtime, changed: new_runtime[changed]}
        with pytest.raises(Failure, match='actual simulator instrumentation differs from frozen treatment'):
            bind()
    instrumentation['verifier_runtime'] = new_runtime
    with pytest.raises(Failure, match='actual simulator instrumentation differs from frozen treatment'):
        bind()
    fresh_settings = copy.deepcopy(settings)
    for role in ('baseline', 'candidate'):
        fresh_settings['instrumentation'][role]['verifier_runtime'] = copy.deepcopy(new_runtime)
    fresh = _command(records, 'freeze-protocol', _payload(tmp_path, 'fresh-freeze',
        dict(message_version='1.0', id='superseding-runtime-policy', settings=fresh_settings)))
    assert fresh['id'] != frozen['id']
    store = Store(records.path)
    assert store.get(frozen['id']) == frozen
    payload['protocol'] = fresh['id']
    assert bind()['context']['protocol_binding']['frozen_sha256'] == fresh['identity_sha256']
