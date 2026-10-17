"""Original C++ standard provenance survives planning; created 2026-10-15 ET.

Stand-in WP exercises admission only. A header unused by the scalar projection
must still retain its planned original-TU bytes until the verifier starts.
"""
import json
import os
import subprocess
import sys

import pytest
import yaml

from conftest import REPO, run_swdb
from test_closed_owner_data import SOURCE
from test_vector_ownership_wp import _ownership_seed
from test_wp_adapter import fake, needs_wp


def _seed(root):
    return _ownership_seed(root, source=SOURCE, cases=[("data_safe", 7)])


def _args(seed):
    return ["prove", "--records", str(seed.records), "--summary", "contract.fixture_vector_owner_data_safe",
            "--adapter", "wp", "--runs-dir", str(seed.runs), "--format", "json"]


@needs_wp
def test_canonical_original_tu_remains_admitted_through_wp_prelaunch(tmp_path):
    seed = _seed(tmp_path)
    result = run_swdb(*_args(seed), env=fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "fake.lock")))
    assert result.returncode == 0, result.stderr + result.stdout
    record = yaml.safe_load((seed.records / json.loads(result.stdout)["path"]).read_text())
    assert record["failure_class"] == "unknown", record
    assert record["settings"]["stdlib_provenance"]["unit"]["verdict"] == "passed"
    assert any(r["name"] == "stdlib_provenance_unit" for r in record["evidence"]["reports"])
    assert "stdlib_provenance" in record["proof_setup_check"]["hashes"]


@needs_wp
@pytest.mark.parametrize("tamper", ["header", "certificate", "artifact"])
def test_original_standard_source_plan_is_rechecked_before_wp(tmp_path, tamper):
    seed = _seed(tmp_path)
    script = '''from swdb import proof, wp_adapter
from swdb.cli import main
original = wp_adapter.WpAdapter._wp
def fault(self, job, path, context):
    plan = context['stdlib_sources']['unit']
    if TARGET == 'header':
        (plan['source'].parent / 'vector').write_text('#include_next <vector>\\n')
    elif TARGET == 'certificate':
        plan['certificate']['headers'] = []
    else:
        plan['certificate_path'].write_text('{}\\n')
    return original(self, job, path, context)
wp_adapter.WpAdapter._wp = fault
raise SystemExit(main())
'''.replace("TARGET", repr(tamper))
    result = subprocess.run([sys.executable, "-c", script, *_args(seed)], cwd=REPO,
        env={**os.environ, **fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "fake.lock"))},
        text=True, capture_output=True, timeout=600)
    assert result.returncode == 1, result.stderr + result.stdout
    if tamper == "header":
        # The ownership check independently replays the complete original
        # lowering and can detect the changed include binding even earlier.
        assert ("proof setup check [stdlib_provenance]" in result.stderr or
                "vector ownership prelaunch check" in result.stderr), result.stderr
    else:
        assert "proof setup check [stdlib_provenance]" in result.stderr, result.stderr
    assert not list(seed.records.glob("proofs/*.yaml"))
