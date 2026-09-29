"""Create-only collector admission after a stale precheck. Updated: 2026-09-25."""
import json

from swdb import cli, dx100_profile, workflow
from swdb.store import Store


def test_public_profile_rejects_an_id_created_after_its_initial_catalog_read(records, tmp_path, monkeypatch, capsys):
    # Reproduce the schedule where another writer wins after this command's
    # initial catalog load but before it acquires the writer lock.
    stale = Store(records.path)
    request = {'message_version': '1.0', 'id': 'collector-race', 'evaluation': 'unneeded',
               'discovery_profile': 'unneeded', 'budget': {'total_seconds': 1}}
    existing = workflow.record('region_profile', request['id'], request={'winner': True},
        outcome={'state': 'submitted', 'stage': 'collection', 'reason': None},
        stages=[], regions=[], dynamic_memory=[], executions=[], raw_artifacts=[], reasons=[], gain_claim=False)
    workflow.persist(records.path, existing, tmp_path / 'index.sqlite', create=True)
    record = records.path / 'region_profiles/collector-race.yaml'
    before = record.read_bytes()
    monkeypatch.setattr(dx100_profile, '_require_valid', lambda _path: stale)
    path = tmp_path / 'request.json'
    path.write_text(json.dumps(request))
    result = cli.main(['dx100-profile', str(path), '--records', str(records.path),
                       '--db', str(tmp_path / 'index.sqlite'), '--runs-dir', str(tmp_path / 'runs'), '--format', 'json'])
    output = capsys.readouterr()
    assert result == 1 and 'already used' in output.err
    assert record.read_bytes() == before
    # A fresh public process still retrieves the first writer's record.
    result = records.swdb('get', request['id'], '--format', 'json')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['request'] == {'winner': True}
