"""Opt-in full_files provider edit format: SWDB computes the diff. 2026-09-27 ET.

The provider returns complete new file contents; SWDB checks scope and protections,
computes the real unified diff, and passes it through the unchanged patch checks.
Deterministic external fixtures only; no real provider is called.
"""
import json
import sys
from pathlib import Path

import pytest
import yaml

from test_proposals import proposal_setup
from test_bfs_native import evaluation_setup, evaluate
from swdb import rewrite
from swdb.cli import Failure

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def files_provider(tmp_path):
    program = tmp_path / 'provider.py'
    program.write_text('import json,sys\nfrom pathlib import Path\n'
                       'prompt=sys.stdin.read()\n'
                       'Path(sys.argv[1]).with_suffix(".prompt").write_text(prompt)\n'
                       'print(Path(sys.argv[1]).read_text())\n')

    def make(files, unresolved=None, response=None, **config):
        path = tmp_path / 'provider-response.json'
        path.write_text(json.dumps(response or {'interpretation': 'Apply alpha 14.', 'files': files,
                                                'unresolved': unresolved or []}))
        provider = tmp_path / 'provider.yaml'
        provider.write_text(yaml.safe_dump({'kind': 'external_fixture', 'edit_format': 'full_files',
            'command': [sys.executable, str(program), str(path)],
            'timeout_s': 10, 'max_repairs': 1, 'total_seconds': 30, **config}))
        return provider
    make.prompt = lambda: (tmp_path / 'provider-response.prompt').read_text()
    return make


def annotated(original):
    return {'kind': 'annotated_source', 'content': {'files': {'src/bfs.cc': original.replace(
        'int alpha = 15', '// Requested rewrite: change alpha from 15 to 14 as a unified diff.\nint alpha = 15')}}}


def test_full_files_candidate_uses_the_computed_diff(proposal_setup, files_provider):
    records, runs, snapshot, request = proposal_setup
    original = (Path(snapshot['artifact']['path']) / 'src/bfs.cc').read_text()
    changed = original.replace('int alpha = 15', 'int alpha = 14')
    result = records.swdb('submit', request(payload=annotated(original)), '--provider-config',
                          files_provider({'src/bfs.cc': changed}), '--runs-dir', runs, '--format', 'json')
    assert result.returncode == 0, result.stderr
    proposal = json.loads(result.stdout)
    assert proposal['outcome']['state'] == 'candidate_created'
    assert proposal['provider']['edit_format'] == 'full_files'
    recorded = proposal['interpretation']
    assert recorded['edit_format'] == 'full_files' and 'patch' not in recorded
    assert recorded['files']['src/bfs.cc']['bytes'] == len(changed.encode())
    prompt = files_provider.prompt()
    assert 'Return JSON with interpretation, files, unresolved' in prompt and 'COMPLETE new file content' in prompt
    chain = json.loads(records.swdb('get', proposal['candidate'], '--chain', '--format', 'json').stdout)['records']
    candidate = chain[proposal['candidate']]
    assert (Path(candidate['artifact']['path']) / 'src/bfs.cc').read_text() == changed
    diff = Path(candidate['diff']).read_text()
    assert diff.count('\n--- a/src/bfs.cc\n') == 1 and '+++ b/src/bfs.cc\n' in diff
    body = [line for line in diff.splitlines() if line[:1] in '+-' and line[:3] not in ('---', '+++')]
    assert len(body) == 2 and 'int alpha = 15' in body[0] and 'int alpha = 14' in body[1]
    assert (Path(runs) / proposal['id'] / 'full-files/computed.diff').read_text() == diff
    assert (Path(snapshot['artifact']['path']) / 'src/bfs.cc').read_text() == original


@pytest.mark.parametrize('files,message', [
    ({'src/other.cc': 'int x;\n'}, 'outside its declared edit scope'),
    ({'../src/bfs.cc': 'x'}, 'unsafe artifact path'),
    ({'src/./bfs.cc': 'x'}, 'not canonical'),
    ({}, 'actual edits'),
    ('same', 'does not change any file')])
def test_full_files_rejects_unsafe_or_empty_output(proposal_setup, files_provider, files, message):
    records, runs, snapshot, request = proposal_setup
    original = (Path(snapshot['artifact']['path']) / 'src/bfs.cc').read_text()
    if files == 'same':
        files = {'src/bfs.cc': original}
    result = records.swdb('submit', request(payload=annotated(original)), '--provider-config',
                          files_provider(files), '--runs-dir', runs, '--format', 'json')
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data['outcome']['state'] == 'failed' and message in data['outcome']['reason']
    assert not data.get('candidate') and data['attempts'][0]['state'] == 'failed'


def test_full_files_scope_admitting_a_protected_file_is_still_rejected(tmp_path):
    source = tmp_path / 'source'
    (source / 'src').mkdir(parents=True)
    (source / 'src/timer.h').write_text('old\n')
    guards = [{'path': 'src/timer.h', 'kind': 'file', 'sha256': 'x'}]
    with pytest.raises(Failure, match='protected evaluator input'):
        rewrite.files_to_patch(source, {'src/timer.h': 'new\n'}, ['src/*'], guards, tmp_path / 'out')


def test_full_files_roi_protection_uses_unchanged_patch_checks(proposal_setup, files_provider):
    records, runs, snapshot, request = proposal_setup
    original = (Path(snapshot['artifact']['path']) / 'src/bfs.cc').read_text()
    guarded = [g for g in snapshot['protections'] if g['path'] == 'src/bfs.cc' and g['kind'] == 'verifier']
    assert guarded
    broken = original.replace(guarded[0]['text'], '')
    result = records.swdb('submit', request(payload=annotated(original)), '--provider-config',
                          files_provider({'src/bfs.cc': broken}), '--runs-dir', runs, '--format', 'json')
    assert result.returncode == 1
    assert 'protected evaluator/ROI input changed' in json.loads(result.stdout)['outcome']['reason']


def test_full_files_new_file_and_missing_trailing_newline(tmp_path):
    source = tmp_path / 'source'
    (source / 'src').mkdir(parents=True)
    (source / 'src/a.cc').write_text('int a = 1;\nint b = 2;\n')
    patch = rewrite.files_to_patch(source, {'src/a.cc': 'int a = 1;\nint b = 3;', 'src/new.h': '#pragma once\n'},
                                   ['src/*'], [], tmp_path / 'out')
    from swdb.workflow import apply_patch
    after = apply_patch(source, tmp_path / 'candidate', patch, ['src/*'], [])
    assert {f['path'] for f in after['files']} == {'src/a.cc', 'src/new.h'}
    assert (tmp_path / 'candidate/src/a.cc').read_text() == 'int a = 1;\nint b = 3;'
    assert (tmp_path / 'candidate/src/new.h').read_text() == '#pragma once\n'


def test_edit_format_is_opt_in_and_checked(files_provider, tmp_path):
    path = files_provider({'src/bfs.cc': 'x'})
    config = rewrite.configuration(path)
    assert rewrite.output_schema(config) is rewrite.FULL_FILES_SCHEMA
    data = yaml.safe_load(path.read_text())
    del data['edit_format']
    path.write_text(yaml.safe_dump(data))
    config = rewrite.configuration(path)
    assert 'edit_format' not in config and rewrite.output_schema(config) is rewrite.OUTPUT_SCHEMA
    path.write_text(yaml.safe_dump({**data, 'edit_format': 'hunks'}))
    with pytest.raises(Failure, match='edit_format'):
        rewrite.configuration(path)


def test_full_files_provider_output_must_match_its_schema(proposal_setup, files_provider):
    records, runs, snapshot, request = proposal_setup
    original = (Path(snapshot['artifact']['path']) / 'src/bfs.cc').read_text()
    config = files_provider(None, response={'interpretation': 'x', 'patch': 'diff', 'unresolved': []})
    result = records.swdb('submit', request(payload=annotated(original)), '--provider-config', config,
                          '--runs-dir', runs, '--format', 'json')
    assert result.returncode == 1
    assert 'invalid structured output' in json.loads(result.stdout)['outcome']['reason']


def test_full_files_repair_computes_its_diff(evaluation_setup, files_provider):
    records, runs, request, base = evaluation_setup
    result, failed = evaluate(evaluation_setup, mode='build_fail')
    assert result.returncode == 1 and failed['outcome']['stage'] == 'build'
    retained = json.loads(records.swdb('get', base['candidate'], '--format', 'json').stdout)
    original = (Path(retained['artifact']['path']) / 'src/bfs.cc').read_text()
    config = files_provider({'src/bfs.cc': original.replace('int alpha = 14', 'int alpha = 13')})
    result = records.swdb('repair', failed['id'], '--provider-config', config, '--runs-dir', runs, '--format', 'json')
    assert result.returncode == 0, result.stderr
    repaired = json.loads(result.stdout)
    assert repaired['attempts'][-1]['interpretation']['edit_format'] == 'full_files'
    candidate = json.loads(records.swdb('get', repaired['candidate'], '--format', 'json').stdout)
    assert 'int alpha = 13' in (Path(candidate['artifact']['path']) / 'src/bfs.cc').read_text()
    assert 'int alpha = 13' in Path(candidate['diff']).read_text()
