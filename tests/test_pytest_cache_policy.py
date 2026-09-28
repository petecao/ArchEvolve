"""Created 2026-09-27 ET. Prospective fix for native readback a2.

The a2 readback failed admission because a manual Linux pytest run had left an
ignored top-level .pytest_cache in its runtime checkout. The retained failure
stays; project pytest runs must no longer create that entry.
"""
from pathlib import Path
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_project_pytest_configuration_disables_cache_provider():
    options = tomllib.loads((ROOT/'pyproject.toml').read_text())['tool']['pytest']['ini_options']
    assert '-p no:cacheprovider' in options['addopts']


def test_pytest_run_in_a_checkout_creates_no_cache_entry(tmp_path):
    (tmp_path/'pyproject.toml').write_text((ROOT/'pyproject.toml').read_text())
    (tmp_path/'tests').mkdir()
    (tmp_path/'tests'/'test_probe.py').write_text('def test_fails():\n    assert False\n')
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=tmp_path,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 1  # a failure is what normally populates lastfailed
    assert not (tmp_path/'.pytest_cache').exists()
