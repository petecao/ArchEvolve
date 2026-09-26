"""Fixed prospective v2 request; no simulator execution. Updated: 2026-09-26 ET."""
from copy import deepcopy
import pytest
import yaml

from scripts.dx100_trace_probe import PRIOR_ID, ROOT
from scripts.dx100_witness_probe import REQUEST, validate_request


def test_witness_probe_binds_prior_identity_and_all_resource_limits():
    prior = yaml.safe_load((ROOT / 'records/evaluations' / (PRIOR_ID + '.yaml')).read_text())
    request = yaml.safe_load(REQUEST.read_text())
    validate_request(request, prior)
    for field, key, value in (
        ('verification', 'checker', 'dx100.bfs.verifier.v1'),
        ('verification', 'max_ticks', 10**12),
        ('verification', 'post_roi_trace', 'MAATrace'),
        ('budget', 'memory_gib', 64),
        ('budget', 'run_seconds', 751),
        ('budget', 'total_seconds', 1101),
        ('budget', 'storage_gib', 3),
        ('configuration', 'l3_assoc', 20),
        ('binary', 'sha256', '0' * 64),
        ('simulator', 'sha256', '0' * 64),
        ('checkpoint_manifest', 'sha256', '0' * 64),
        ('workload', 'source', 1),
    ):
        changed = deepcopy(request)
        changed[field][key] = value
        with pytest.raises(ValueError, match='may change only'):
            validate_request(changed, prior)
    with pytest.raises(ValueError, match='exact retained real a6'):
        validate_request(request, {**prior, 'evidence_kind': 'fixture'})
