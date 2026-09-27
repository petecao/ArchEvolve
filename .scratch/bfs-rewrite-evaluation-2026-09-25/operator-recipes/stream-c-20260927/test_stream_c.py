"""Author checks for the Stream C packet (2026-09-27 ET). Run from the repo root:
python3 -m pytest -q .scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/stream-c-20260927/test_stream_c.py
These are preparation checks only; they establish no build, provider or simulator result."""
import importlib.util
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def load(path):
    return json.loads(Path(path).read_text())


def prepare():
    spec = importlib.util.spec_from_file_location('prepare_context4', HERE / 'prepare_context4.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_shell_scripts_parse():
    for script in [HERE / 'launch.sh', *sorted((HERE / 'jobs').glob('*.sh'))]:
        assert subprocess.run(['bash', '-n', str(script)]).returncode == 0, script


def test_build_requests_differ_from_t17_only_in_id_candidate_and_instrumentation():
    base = load(HERE.parent / 't17-acceptance/diagnostic-request-prospective.json')
    for role, diagnostic in (('primary', False), ('diagnostic', True)):
        request = load(HERE / f'requests/t20-context4-{role}-build.json')
        assert request['candidate'] == 'bfs-campaign-preparation-20260925-a1.upstream-annotated-context4.candidate-1'
        assert request['diagnostic_regions'] is diagnostic and request['accelerated'] is True
        assert {k: v for k, v in request.items() if k not in ('id', 'candidate', 'diagnostic_regions')} == \
               {k: v for k, v in base.items() if k not in ('id', 'candidate', 'diagnostic_regions')}


def test_context4_keeps_strategy_and_matches_prepared_bytes(monkeypatch):
    monkeypatch.chdir(ROOT)
    module = prepare()
    request = module.build()
    prior = load(module.OLD / 'upstream-annotated-context3.proposal.json')
    for key in ('strategy', 'intent', 'payload', 'regions', 'required_operations', 'constraints',
                'source_snapshot', 'profile_package', 'source_sha256', 'implementation', 'producer'):
        assert request[key] == prior[key]
    assert request['parameters']['prompt_projection'] == 'selected_regions_focused_context.v1'
    assert [h['path'] for h in request['parameters']['read_only_context']['headers']] == module.FOCUSED_HEADERS
    assert load(HERE / 'prepared/context4.proposal.json') == request
    provider = load(HERE / 'prepared/context4.provider.json')
    assert provider == module.PROVIDER and provider['timeout_s'] <= 900 and provider['budget_usd'] == 10
    assert provider['total_seconds'] == 1800 and provider['max_repairs'] == 2
    prompt = module.render(request)
    assert len(prompt.encode()) == load(HERE / 'prepared/context4.summary.json')['prompt_bytes'] < 275533


# Context5 (2026-09-27 ET): richer HW test-client annotation and stream-json capture.
def prepare5():
    spec = importlib.util.spec_from_file_location('prepare_context5', HERE / 'prepare_context5.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_context5_changes_only_annotation_allocation_and_capture(monkeypatch):
    monkeypatch.chdir(ROOT)
    module = prepare5()
    request = module.build()
    prior = load(HERE / 'prepared/context4.proposal.json')
    assert request['id'].endswith('-context5') and request['producer'] == prior['producer']
    assert request['producer']['test_client'] is True
    assert {k: v for k, v in request.items() if k not in ('id', 'payload', 'parameters')} == \
           {k: v for k, v in prior.items() if k not in ('id', 'payload', 'parameters')}
    changed = {k for k in request['parameters'] if request['parameters'][k] != prior['parameters'].get(k)}
    assert changed == {'predecessor_proposal', 'provider_allocation', 'annotation_revision'}
    assert load(HERE / 'prepared/context5.proposal.json') == request
    summary = load(HERE / 'prepared/context5.summary.json')
    assert len(module.render(request).encode()) == summary['prompt_bytes']


def test_context5_annotation_carries_the_reference_edits_verbatim(monkeypatch):
    monkeypatch.chdir(ROOT)
    module = prepare5()
    original = (ROOT / 'apps/gapbs/src/bfs.cc').read_text()
    annotated = module.build()['payload']['content']['files']['src/bfs.cc']
    comment, rest = annotated.split('*/\n', 1)
    assert rest == original and comment.startswith('/*\n') and '/*' not in comment[2:]
    edits = module.edits()
    assert len(edits) == 4
    for _, text in edits:
        assert text in comment
    reference = (HERE / 'producer-check/reference-bfs.cc').read_text()
    for needle in ('wait_ready(tile5);', 'queue.size() > static_cast<size_t>(NUM_CORES) * 1024',
                   'offsets[n] > INT_MAX', 'get_tile_size(tile7)', 'compare_and_swap(parents[v], curr_val, u)',
                   'scout_count += -static_cast<int64_t>(tile5Ptr[k])', 'alloc_MAA();'):
        assert needle in reference and needle in comment
    for forbidden in ('m5_work_begin', 'm5_reset_stats', 'm5_dump_stats', 'm5_exit', 'BFSVerifier', 'PASS'):
        assert all(forbidden not in text for _, text in edits)


def test_context5_provider_uses_stream_capture_within_allocation(tmp_path):
    import sys
    sys.path.insert(0, str(ROOT))
    from swdb import rewrite
    provider = load(HERE / 'prepared/context5.provider.json')
    assert provider == prepare5().PROVIDER and provider['output_format'] == 'stream-json'
    assert provider['timeout_s'] == 900 and provider['budget_usd'] == 10
    assert provider['total_seconds'] == 1800 and provider['max_repairs'] == 2
    fake = tmp_path / 'claude'
    fake.write_text('#!/bin/sh\n')
    fake.chmod(0o755)
    local = tmp_path / 'provider.json'
    local.write_text(json.dumps({**provider, 'command': [str(fake)]}))
    assert rewrite.configuration(local)['output_format'] == 'stream-json'


def test_context5_build_requests_follow_context4():
    for role in ('primary', 'diagnostic'):
        old = load(HERE / f'requests/t20-context4-{role}-build.json')
        new = load(HERE / f'requests/t20-context5-{role}-build.json')
        assert new['candidate'] == 'bfs-campaign-preparation-20260925-a1.upstream-annotated-context5.candidate-1'
        assert new['id'] == f'bfs-t20-context5-{role}-build-20260927-c2'
        assert {k: v for k, v in new.items() if k not in ('id', 'candidate')} == \
               {k: v for k, v in old.items() if k not in ('id', 'candidate')}
