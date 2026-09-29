"""Pinned adapters through public submission/repair. Updated 2026-09-29 ET."""
import json
import sys
from pathlib import Path
import pytest
import yaml
from test_proposals import proposal_setup
from test_bfs_native import evaluation_setup, evaluate
from test_bfs_rewrite import patch_between

@pytest.fixture
def emulated_provider(tmp_path):
    program = tmp_path / 'provider-cli.py'
    program.write_text('''import json, sys
from pathlib import Path
if '--version' in sys.argv:
    print('0.1-contract-fixture'); raise SystemExit(0)
plan = json.loads(Path(sys.argv[1]).read_text())
Path(sys.argv[1]).with_suffix('.argv.json').write_text(json.dumps(sys.argv[2:]))
Path(sys.argv[1]).with_suffix('.stdin.txt').write_text(sys.stdin.read())
for event in plan.get('events', []): print(json.dumps(event))
if plan.get('unavailable'):
    print(json.dumps({'type':'turn.failed', 'error':{'message':'You have hit your ChatGPT usage limit'}}))
    raise SystemExit(1)
response = plan['response']
if '--output-last-message' in sys.argv:
    Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(json.dumps(response))
    print(json.dumps({'type':'turn.completed'}))
else:
    print(json.dumps({'type':'result', 'is_error':False, 'structured_output':response}))
''')
    def make(kind='codex', patch='', response=None, unavailable=False, events=None, **fields):
        plan = tmp_path / 'cli-plan.json'
        plan.write_text(json.dumps({'response':response or {'interpretation':'Apply alpha change.',
            'patch':patch, 'unresolved':[]}, 'unavailable':unavailable, 'events':events or []}))
        config = tmp_path / 'provider.yaml'
        config.write_text(yaml.safe_dump({'kind':'external_fixture', 'emulates':kind,
            'workspace':False, 'command':[sys.executable,str(program),str(plan)], **fields}))
        return config
    make.argv = lambda: json.loads((tmp_path / 'cli-plan.argv.json').read_text())
    make.stdin = lambda: (tmp_path / 'cli-plan.stdin.txt').read_text()
    return make

def submit(setup, config, **changes):
    records, runs, _, request = setup
    result = records.swdb('submit', request(payload={'kind':'natural_language','content':'Change alpha to 14.'}, **changes),
        '--provider-config', config, '--runs-dir', runs, '--format', 'json')
    return result, json.loads(result.stdout)

@pytest.mark.parametrize('kind,model,effort', [('codex','gpt-5.6-sol','xhigh'),('claude','claude-sonnet-5-5','high')])
def test_submit_emulates_pinned_cli(proposal_setup, emulated_provider, kind, model, effort):
    patch = yaml.safe_load(proposal_setup[3]().read_text())['payload']['content']
    result, proposal = submit(proposal_setup, emulated_provider(kind, patch=patch))
    assert result.returncode == 0, result.stderr
    provider = proposal['provider']; receipt = proposal['attempts'][0]['provider']
    assert provider['resolved_kind'] == kind and provider['model'] == model and provider['effort'] == effort
    assert provider['cli_version'] == '0.1-contract-fixture'
    assert receipt['classification'] == 'contract_fixture'
    assert receipt['budget_usd_enforced'] == (kind == 'claude')
    assert receipt['timeout_s'] == 1200 and proposal['repair_budget']['total_seconds'] == 3600
    argv = emulated_provider.argv()
    assert argv[argv.index('--model')+1] == model
    if kind == 'codex':
        assert 'model_reasoning_effort="xhigh"' in argv and '--json' in argv
        assert 'analytics.enabled=false' in argv
        assert all('otel.' + key + '="none"' in argv for key in ('exporter','trace_exporter','metrics_exporter'))
        state = next(value for value in argv if value.startswith('sqlite_home='))
        assert Path(json.loads(state.split('=',1)[1])) == Path(receipt['command'][
            receipt['command'].index('--output-schema')+1]).parent / 'guard/ephemeral-state'
        assert 'code_mode_host' not in argv
        assert emulated_provider.stdin() == ''
        schema = json.loads(Path(argv[argv.index('--output-schema')+1]).read_text())
        assert schema['additionalProperties'] is False
        assert '--ephemeral' in argv and '--ignore-user-config' in argv and '--ignore-rules' in argv
    else:
        assert argv[argv.index('--effort')+1] == effort and emulated_provider.stdin()


def test_official_shaped_single_command_fixture_preserves_requested_launcher(proposal_setup, emulated_provider, tmp_path):
    """An npm-shaped fixture remains a fixture even when a native sibling exists."""
    patch = yaml.safe_load(proposal_setup[3]().read_text())['payload']['content']
    config_path = emulated_provider(patch=patch)
    config = yaml.safe_load(config_path.read_text())
    package = tmp_path / 'npm/node_modules/@openai/codex'
    wrapper = package / 'bin/codex.js'
    wrapper.parent.mkdir(parents=True)
    (package / 'package.json').write_text(json.dumps({'name':'@openai/codex'}))
    # These are deliberately contract programs, not installed model CLIs.
    wrapper.write_text('#!' + sys.executable + '\nimport os, sys\nargv = ' + repr(config['command']) +
                       '\nos.execv(argv[0], argv + sys.argv[1:])\n')
    wrapper.chmod(0o755)
    for name, triple in (('codex-linux-x64','x86_64-unknown-linux-musl'),
                        ('codex-linux-arm64','aarch64-unknown-linux-musl')):
        root = package / 'node_modules/@openai' / name
        native = root / 'vendor' / triple / 'bin/codex'
        native.parent.mkdir(parents=True)
        (root / 'package.json').write_text(json.dumps({'name':'@openai/' + name}))
        native.write_text('#!' + sys.executable + '\nraise SystemExit("fixture native must not be selected")\n')
        native.chmod(0o755)
    config['command'] = [str(wrapper)]
    config_path.write_text(yaml.safe_dump(config))
    result, proposal = submit(proposal_setup, config_path)
    assert result.returncode == 0, result.stderr
    receipt = proposal['attempts'][0]['provider']
    assert receipt['classification'] == 'contract_fixture'
    assert receipt['command'][0] == str(wrapper)
    assert receipt['provider']['command'] == [str(wrapper)]
    assert receipt['cli_version'] == '0.1-contract-fixture'

@pytest.mark.parametrize('field', ['model','effort','model_reasoning_effort'])
def test_submit_refuses_pin_overrides(proposal_setup, emulated_provider, field):
    result, data = submit(proposal_setup, emulated_provider(**{field:'different'}))
    assert result.returncode == 1 and 'pinned' in data['outcome']['reason']
    assert data['attempts'] == []

def test_codex_full_files_is_strict_array_contract(proposal_setup, emulated_provider):
    source = Path(proposal_setup[2]['artifact']['path']) / 'src/bfs.cc'
    response = {'interpretation':'Change alpha.', 'unresolved':[],
                'files':[{'path':'src/bfs.cc','content':source.read_text().replace('int alpha = 15','int alpha = 14')}]}
    result, data = submit(proposal_setup, emulated_provider(response=response, edit_format='full_files'))
    assert result.returncode == 0, result.stderr
    assert data['interpretation']['files']['src/bfs.cc']['bytes'] > 0
    argv = emulated_provider.argv()
    schema = json.loads(Path(argv[argv.index('--output-schema')+1]).read_text())
    assert schema['properties']['files']['type'] == 'array'
    assert schema['properties']['files']['items']['additionalProperties'] is False
    candidate = json.loads(proposal_setup[0].swdb('get',data['candidate'],'--format','json').stdout)
    assert 'int alpha = 14' in (Path(candidate['artifact']['path'])/'src/bfs.cc').read_text()

def test_initial_usage_limit_can_retry_without_repair(proposal_setup, emulated_provider):
    result, unavailable = submit(proposal_setup, emulated_provider(unavailable=True))
    assert result.returncode == 1 and unavailable['outcome']['state'] == 'provider_unavailable'
    assert unavailable['repair_budget']['repairs'] == 0
    records, runs, _, request = proposal_setup
    patch = yaml.safe_load(request().read_text())['payload']['content']
    retry = records.swdb('repair',unavailable['id'],'--provider-config',emulated_provider(patch=patch),
        '--runs-dir',runs,'--format','json')
    data = json.loads(retry.stdout)
    assert retry.returncode == 0, retry.stderr
    assert data['repair_budget']['repairs'] == 0 and len(data['attempts']) == 2
    assert data['attempts'][0]['state'] == 'provider_unavailable'
    assert data['candidate'].endswith('.candidate-1')

def test_retry_refuses_changed_provider(proposal_setup, emulated_provider):
    _, unavailable = submit(proposal_setup, emulated_provider(unavailable=True))
    records, runs, _, _ = proposal_setup
    retry = records.swdb('repair',unavailable['id'],'--provider-config',emulated_provider('claude'),
        '--runs-dir',runs,'--format','json')
    assert retry.returncode == 1 and 'differs from the first attempt' in retry.stderr
    retained = json.loads(records.swdb('get',unavailable['id'],'--format','json').stdout)
    assert len(retained['attempts']) == 1 and retained['repair_budget']['repairs'] == 0

def test_repair_usage_limit_does_not_consume_budget(evaluation_setup, emulated_provider):
    records,runs,_,base = evaluation_setup
    machine = records.read('machines/native-testhost.yaml')
    if machine['hostname'] == 'mbit10':
        # The public evaluator verifies the inherited socket lease itself.
        machine['lane_required'] = True
        records.write('machines/native-testhost.yaml', machine)
    result, failed = evaluate(evaluation_setup,mode='build_fail',
                              build_directory=str(runs / 'usage-limit-native-build'))
    assert result.returncode == 1, result.stderr
    assert failed['outcome']['state'] == 'failed' and failed['outcome']['stage'] == 'build', failed['outcome']
    if machine['hostname'] == 'mbit10':
        assert 'verified: affinity' in failed['context']['lane']
    retry = records.swdb('repair',failed['id'],'--provider-config',emulated_provider(unavailable=True),
        '--runs-dir',runs,'--format','json')
    unavailable = json.loads(retry.stdout)
    assert retry.returncode == 1 and unavailable['outcome']['state'] == 'provider_unavailable'
    assert unavailable['repair_budget']['repairs'] == 0
    prior = json.loads(records.swdb('get',base['candidate'],'--format','json').stdout)
    original = (Path(prior['artifact']['path'])/'src/bfs.cc').read_text()
    patch = patch_between(original, original.replace('int alpha = 14','int alpha = 13'))
    retry = records.swdb('repair',failed['id'],'--provider-config',emulated_provider(patch=patch),
        '--runs-dir',runs,'--format','json')
    repaired = json.loads(retry.stdout)
    assert retry.returncode == 0, retry.stderr
    assert repaired['repair_budget']['repairs'] == 1 and len(repaired['attempts']) == 3

@pytest.mark.parametrize('fields,accepted', [({'timeout_s':1800,'total_seconds':3600},True),
                                           ({'timeout_s':1801},False), ({'total_seconds':3601},False)])
def test_public_time_limits(proposal_setup, emulated_provider, fields, accepted):
    patch = yaml.safe_load(proposal_setup[3]().read_text())['payload']['content']
    result,data = submit(proposal_setup,emulated_provider(patch=patch,**fields))
    assert (result.returncode == 0) == accepted
    if accepted:
        assert data['attempts'][0]['provider']['timeout_s'] == 1800
    else:
        assert data['outcome']['stage'] == 'provider_configuration'

def test_omitted_kind_records_default_codex_before_guard_refusal(proposal_setup, tmp_path):
    # This deliberately supplies Python rather than any real provider executable.
    # On Mac the Linux guard refuses first; on Linux Python cannot run `codex exec`.
    config = tmp_path/'default-provider.yaml'
    config.write_text(yaml.safe_dump({'command':[sys.executable],'workspace':False}))
    result, data = submit(proposal_setup, config)
    assert result.returncode == 1
    assert data['provider']['kind'] == data['provider']['resolved_kind'] == 'codex'
    assert data['provider']['model'] == 'gpt-5.6-sol' and data['provider']['effort'] == 'xhigh'


@pytest.mark.parametrize('unavailable', [False, True])
def test_prompt_only_rejects_tool_activity_even_if_usage_is_unavailable(proposal_setup, emulated_provider, unavailable):
    patch = yaml.safe_load(proposal_setup[3]().read_text())['payload']['content']
    event = {'type':'item.completed','item':{'type':'command_execution','command':'printf harmless'}}
    result, data = submit(proposal_setup,emulated_provider(patch=patch,events=[event],unavailable=unavailable))
    assert result.returncode == 1 and data['outcome']['state'] == 'failed'
    assert 'candidate' not in data
    assert data['attempts'][0]['provider']['audit']['passed'] is False
    assert 'prompt-only' in data['outcome']['reason']
