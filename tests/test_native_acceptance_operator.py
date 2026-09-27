"""Author tests for the Stream B native acceptance operator. Created 2026-09-27 ET.

These check argument shape and closure rules only; they run no host workload.
"""
import json
from pathlib import Path
import re
import runpy

import pytest

ROOT = Path(__file__).resolve().parents[1]
OPERATOR = ROOT/'.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/native-acceptance/operator.py'
op = runpy.run_path(str(OPERATOR))


def route():
    return {'id': 'bfs-native-acceptance-test', 'candidate': 'c', 'packages': ['p1', 'p2'], 'protocol': 'proto'}


def conf():
    return {'runtime': '/data1/yanruj/rt', 'commit': 'a'*40, 'python': '/usr/bin/python3.12', 'python_sha256': 'b'*64,
            'node': 1, 'route': route()}


def test_driver_argv_uses_only_campaign_options_and_existing_candidate_route():
    argv = op['driver_argv'](conf(), route(), 'c'*64, 'S', 'E', 11, 22)
    source = (ROOT/'scripts/bfs_native_campaign.py').read_text()
    known = set(re.findall(r"add_argument\('(--[a-z0-9-]+)'", source))
    flags = [item for item in argv if item.startswith('--')]
    assert set(flags) <= known
    assert '--provider-config' not in flags and '--repair-config' not in flags
    assert argv[argv.index('--existing-candidate')+1] == 'c'
    assert argv[argv.index('--packages')+1:argv.index('--packages')+3] == ['p1', 'p2']
    assert argv[argv.index('--lane')+1] == 'mbit10-evaluation-node1'
    assert argv[argv.index('--total-seconds')+1] == '14400'


def test_route_roots_are_disjoint_and_on_authorized_volumes():
    paths = op['route_paths'](route())
    assert str(paths['dispatch']) == str(paths['runs'])+'.dispatch'
    assert paths['builds'].is_relative_to('/data1/yanruj') and paths['sources'].is_relative_to('/data1/yanruj')
    values = list(paths.values())
    assert not any(a == b or a in b.parents for i, a in enumerate(values) for b in values[i+1:])


def test_environment_clears_declared_python_inputs(monkeypatch):
    monkeypatch.setenv('PYTHONPATH', '/tmp/shadow')
    env = op['environment']()
    assert 'PYTHONPATH' not in env and env['PYTHONDONTWRITEBYTECODE'] == '1' and env['PYTHONNOUSERSITE'] == '1'


def test_config_rejects_unresolved_fields(tmp_path):
    value = conf(); value['commit'] = None
    (tmp_path/'c.json').write_text(json.dumps(value))
    with pytest.raises(RuntimeError, match='unresolved'):
        op['config'](tmp_path/'c.json')
