"""Instruction driver source admission before provider dispatch. Updated 2026-09-29."""
import json
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'scripts/bfs_instruction_smoke.py'
SCALAR = 'bfs-dx100-scalar-only-20260929-a1.source'


def run_driver(tmp_path, *extra):
    records = tmp_path/'records'; records.mkdir(exist_ok=True)
    return subprocess.run([sys.executable,str(SCRIPT),'--id','driver-test','--runs-dir',str(tmp_path/'runs'),
        '--records',str(records),'--lane','fixture','--routes','natural_language',*extra],
        cwd=ROOT,text=True,capture_output=True,timeout=30)


@pytest.mark.parametrize('override,kind', [([], 'codex'), (['--kind','claude'], 'claude')])
def test_missing_scalar_snapshot_refuses_before_provider_and_preserves_kind(tmp_path, override, kind):
    result = run_driver(tmp_path,*override)
    assert result.returncode != 0
    assert 'registered scalar-only source snapshot' in result.stderr and SCALAR in result.stderr
    folder = tmp_path/'runs/driver-test.driver'
    assert json.loads((folder/'provider.json').read_text())['kind'] == kind
    assert not list(folder.glob('*-submit.*'))
    assert json.loads((folder/'01-get.stdout.json').read_text() or '{}') == {}


def test_source_override_refuses_full_author_snapshot(tmp_path, records):
    records.copy_repo()
    result = run_driver(tmp_path,'--source-snapshot','bfs-dx100-compile-20260925-a1.source')
    assert result.returncode != 0
    assert 'refuses full author-code source' in result.stderr
    assert 'explicit author-code reuse proposal' in result.stderr
    assert not list((tmp_path/'runs/driver-test.driver').glob('*-submit.*'))


def test_driver_help_exposes_kind_and_scalar_snapshot_options():
    result = subprocess.run([sys.executable,str(SCRIPT),'--help'],cwd=ROOT,text=True,capture_output=True,timeout=10)
    assert result.returncode == 0
    assert '--kind {codex,claude}' in result.stdout and '--source-snapshot' in result.stdout
    assert 'scalar-only DX100 snapshot' in result.stdout
