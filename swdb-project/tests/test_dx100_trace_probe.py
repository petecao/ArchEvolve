"""Fixed post-ROI diagnostic identity guard. Updated: 2026-09-26 ET."""
from copy import deepcopy
import pytest
import yaml

from scripts.dx100_trace_probe import PRIOR_ID, REQUEST, ROOT, validate_request


def test_probe_request_preserves_actual_model_checkpoint_and_resource_identity():
    prior = yaml.safe_load((ROOT / 'records/evaluations' / (PRIOR_ID + '.yaml')).read_text())
    request = yaml.safe_load(REQUEST.read_text())
    validate_request(request, prior)
    for field, key, value in (
        ('budget', 'memory_gib', 64),
        ('budget', 'run_seconds', 751),
        ('configuration', 'l3_assoc', 20),
        ('binary', 'sha256', '0' * 64),
        ('checkpoint_manifest', 'sha256', '0' * 64),
        ('workload', 'source', 1),
        ('verification', 'max_ticks', 10**12),
    ):
        changed = deepcopy(request)
        changed[field][key] = value
        with pytest.raises(ValueError, match='may change only'):
            validate_request(changed, prior)
    wrong_prior = {**prior, 'id': 'different-execution'}
    with pytest.raises(ValueError, match='exact retained real a6'):
        validate_request(request, wrong_prior)
