"""Real public cache-placement contracts; no empirical qualification. Created 2026-09-26 ET."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

from conftest import REPO
from scripts import bfs_freeze_pilot as publisher, bfs_native_campaign as campaign
from scripts import bfs_simulator_batch as batch, bfs_simulator_series as series
from swdb import artifacts
from test_bfs_protocol import protocol_seed


@pytest.fixture
def checkout(tmp_path):
    root = tmp_path / 'code'; root.mkdir()
    names = subprocess.check_output(['git', 'ls-files', '--', 'scripts', 'swdb', 'schemas',
        'vocab', 'tools/bfs_native', 'tests', 'apps', 'pyproject.toml'], cwd=REPO, text=True).splitlines()
    for name in names:
        target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / name, target)
    (root / 'records/machines').mkdir(parents=True)
    shutil.copyfile(REPO / 'records/machines/mbit10.yaml', root / 'records/machines/mbit10.yaml')
    for args in (['init', '-q'], ['add', '.'], ['-c', 'user.name=Fixture',
                 '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Disposable contract fixture']):
        subprocess.run(['git', *args], cwd=root, check=True)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    return root, commit, campaign.campaign_runtime(commit, root=root)


def test_series_real_get_uses_accounted_raw_cache(checkout, tmp_path, monkeypatch):
    root, commit, runtime = checkout
    runs = tmp_path / 'raw'; runs.mkdir()
    monkeypatch.setattr(series, 'ROOT', root)
    monkeypatch.setattr(series.socket, 'gethostname', lambda: 'mbit10')
    monkeypatch.setattr(series.profile, '_verified_lane', lambda *_: 'fixture')
    monkeypatch.setattr(series.artifacts, 'external_directory', lambda _: runs)
    monkeypatch.setattr(series.os, 'statvfs',
                        lambda _: SimpleNamespace(f_bavail=100*1024**3, f_frsize=1))
    monkeypatch.setattr(sys, 'argv', ['series', '--id', 'cache-contract', '--candidate', 'mbit10',
        '--workload', 'unused', '--build-evaluation', 'unused', '--configuration', str(tmp_path/'unused.json'),
        '--runs-dir', '/data/yanruj/EvolveSWDB_runs/cache-contract', '--records', str(root/'records'), '--lane', '0'])
    # Real orchestration and public get run; using a machine as the candidate
    # deliberately stops immediately afterward, before compilation/evaluation.
    with pytest.raises(KeyError, match='source_snapshot'):
        series.main()
    receipt = json.loads((runs/'cache-contract.driver/driver.json').read_text())
    stage = receipt['stages'][0]
    assert json.loads(Path(stage['stdout']).read_text())['id'] == 'mbit10'
    database = runs/'cache-contract.driver/swdb.sqlite'
    assert database.is_file() and receipt['database'] == str(database)
    assert stage['command'][stage['command'].index('--db')+1] == str(database)
    assert batch.allocated_bytes([runs]) >= database.stat().st_blocks*512
    assert not (root/'build').exists()
    assert campaign.campaign_runtime(commit, root=root) == runtime


def test_failed_prepare_retains_external_cache_without_review(checkout, tmp_path, monkeypatch):
    root, commit, runtime = checkout
    source = tmp_path/'selection.json'; source.write_text(json.dumps({'packages': ['mbit10']}))
    output, database = tmp_path/'review', tmp_path/'raw/swdb.sqlite'
    monkeypatch.setattr(publisher, 'ROOT', root)
    failure = ValueError('synthetic stop before empirical qualification')
    def stop(*_): raise failure
    monkeypatch.setattr(publisher, 'prepare', stop)
    monkeypatch.setattr(sys, 'argv', ['publisher', 'prepare', str(source), '--records', str(root/'records'),
        '--output', str(output), '--db', str(database)])
    with pytest.raises(ValueError) as caught:
        publisher.main()
    assert caught.value is failure
    assert database.is_file() and not output.exists()
    assert not (root/'build').exists() and not (root/'records/protocols').exists()
    assert campaign.campaign_runtime(commit, root=root) == runtime


def test_public_freeze_and_fresh_get_share_explicit_cache(checkout, protocol_seed, tmp_path, monkeypatch, capsys):
    root, commit, runtime = checkout
    records, _, frozen, request, *_ = protocol_seed
    shutil.copytree(records.path, root/'records', dirs_exist_ok=True)
    spec = {'packages': [frozen['id']]}
    request = {**copy.deepcopy(request), 'id': 'cache-placement-fixture-policy'}
    review = {'input': spec, 'freeze_request': request, 'publishable': True, 'unmet_gates': []}
    review['identity_sha256'] = artifacts.digest(review)
    source = tmp_path/'review.json'; source.write_text(json.dumps(review))
    output, database = tmp_path/'publication', tmp_path/'raw/swdb.sqlite'
    monkeypatch.setattr(publisher, 'ROOT', root)
    # Qualification is synthetic; all three public processes, real immutable
    # fixture protocol construction, cache writes and fresh retrieval are real.
    monkeypatch.setattr(publisher, 'prepare', lambda *_: copy.deepcopy(review))
    run, commands = subprocess.run, []
    def observed(command, **kwargs):
        commands.append(command)
        return run(command, **kwargs)
    monkeypatch.setattr(publisher.subprocess, 'run', observed)
    monkeypatch.setattr(sys, 'argv', ['publisher', 'publish', str(source), '--records', str(root/'records'),
        '--output', str(output), '--db', str(database)])
    publisher.main()
    result = json.loads(capsys.readouterr().out)
    assert result['gain_claim'] is False
    assert [command[3] for command in commands] == ['get', 'freeze-protocol', 'get']
    assert all(command[command.index('--db')+1] == str(database) for command in commands)
    assert json.loads((output/'freeze.stdout.json').read_text())['id'] == result['protocol']
    assert database.is_file() and not (root/'build').exists()
    assert campaign.campaign_runtime(commit, root=root) == runtime


@pytest.mark.parametrize('location', ['missing', 'relative', 'code', 'records', 'output', 'input', 'directory', 'symlink'])
def test_publisher_rejects_unsafe_or_implicit_cache(tmp_path, monkeypatch, location):
    root = tmp_path/'code'; root.mkdir()
    records = tmp_path/'records'; records.mkdir()
    source = tmp_path/'selection.json'; source.write_text('{}')
    output = tmp_path/'review'
    database = {'relative': Path('cache.sqlite'), 'code': root/'cache.sqlite', 'records': records/'cache.sqlite',
        'output': output/'cache.sqlite', 'input': source, 'directory': tmp_path,
        'missing': None, 'symlink': tmp_path/'alias.sqlite'}[location]
    if location == 'symlink': database.symlink_to(source)
    monkeypatch.setattr(publisher, 'ROOT', root)
    monkeypatch.setattr(publisher.subprocess, 'run', lambda *_, **__: pytest.fail('unsafe cache launched public process'))
    command = ['publisher', 'prepare', str(source), '--records', str(records), '--output', str(output)]
    if database is not None: command += ['--db', str(database)]
    monkeypatch.setattr(sys, 'argv', command)
    with pytest.raises(SystemExit if location == 'missing' else ValueError): publisher.main()
    assert source.read_text() == '{}' and not output.exists()
