"""Every checked nested-source stage is freshly replayed before WP; 2026-10-15 ET."""
import json
import os
import subprocess
import sys

import pytest

from conftest import REPO
from test_proof_semantics import dx, dx_seed
from test_wp_adapter import fake, needs_wp
from test_wp_nested_entry_reads import _contract


@needs_wp
@pytest.mark.parametrize('target', ['file', 'certificate', 'entry_windows'])
def test_changed_nested_source_certificate_or_domain_refuses_before_wp(dx, target):
    _contract(dx)
    script = '''from swdb import wp_adapter
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
    result = subprocess.run([sys.executable, '-c', script, 'prove', '--records', str(dx.records),
        '--candidate', dx.candidates['dx'], '--function', 'dxf_three_reads', '--contract',
        'contract.fixture_dx_three_reads', '--adapter', 'wp', '--runs-dir', str(dx.runs), '--format', 'json'],
        cwd=REPO, env={**os.environ, **fake('unknown')}, capture_output=True, text=True, timeout=600)
    assert result.returncode == 1, result.stderr + result.stdout
    assert 'proof setup check' in result.stderr, result.stderr
    assert not list(dx.records.glob('proofs/*.yaml'))
