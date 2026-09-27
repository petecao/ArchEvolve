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
