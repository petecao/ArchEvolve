"""Every checked nested-source stage is freshly replayed before WP; 2026-10-15 ET."""
import json
import os
import subprocess
import sys

import pytest

from conftest import REPO
from test_wp_nested_entry_obligations import nested_seed, nested_case
from test_wp_adapter import fake, needs_wp


@needs_wp
@pytest.mark.parametrize('target', ['file', 'certificate', 'entry_windows'])
def test_changed_nested_source_certificate_or_domain_refuses_before_wp(nested_case, target):
    seed = nested_case
    script = '''from swdb import proof, wp_adapter
from swdb.cli import main
original = wp_adapter.WpAdapter._wp
def fault(self, job, path, context):
    nested = context['nested_entry_reads']
    if TARGET == 'file':
        nested['view'].path.write_text(nested['view'].text + '\\n// changed after planning\\n')
    elif TARGET == 'certificate':
        nested['view'].certificate['captures'][0]['name'] = 'other'
    else:
        nested['options']['entry_windows']['declarations_sha256'] = 'b' * 64
    return original(self, job, path, context)
wp_adapter.WpAdapter._wp = fault
raise SystemExit(main())
'''.replace('TARGET', repr(target))
    result = subprocess.run([sys.executable, '-c', script, 'prove', '--records', str(seed.records),
        '--summary', 'contract.fixture_dx_nested_read', '--adapter', 'wp', '--runs-dir', str(seed.runs), '--format', 'json'],
        cwd=REPO, env={**os.environ, **fake('unknown')}, capture_output=True, text=True, timeout=600)
    assert result.returncode == 1, result.stderr + result.stdout
    assert 'proof setup check' in result.stderr, result.stderr
    assert not list(seed.records.glob('proofs/*.yaml'))
